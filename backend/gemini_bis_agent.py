"""Gemini-powered universal BIS SmartGuide agent.

Gemini is the reasoning/orchestration layer. SmartGuide's local BIS corpus,
RAG, product guard, compliance data and LIMS handoff remain the evidence layer.
"""
from __future__ import annotations

import json
import os
from typing import Any, Callable, Dict, Optional

from google import genai
from google.genai import types
from product_guard import anchor, guarded_results, resolve_product
from universal_product_v2 import analyze_universal

SUPPORTED_LANGUAGES = {"en": "English", "hi": "Hindi", "kn": "Kannada", "te": "Telugu", "ta": "Tamil"}

FINAL_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "reply": {"type": "STRING"},
        "product": {"type": "STRING"},
        "category": {"type": "STRING"},
        "standards_status": {"type": "STRING"},
        "next_actions": {"type": "ARRAY", "items": {"type": "STRING"}},
        "evidence_trail": {"type": "ARRAY", "items": {"type": "STRING"}},
        "confidence": {"type": "NUMBER"},
        "source_grounded": {"type": "BOOLEAN"},
    },
    "required": ["reply", "product", "category", "standards_status", "next_actions", "evidence_trail", "confidence", "source_grounded"],
}


class GeminiBISAgent:
    name = "BIS SmartGuide Universal Agent"
    version = "3.2-gemini-universal-guarded"

    def __init__(self, find_matches: Callable[[str, int], list], rag_retrieve: Callable[[str, int], list],
                 compliance_lookup: Callable[[str], Dict[str, Any]], certification_lookup: Callable[[str], Dict[str, Any]],
                 lab_lookup: Callable[[str], Dict[str, Any]]) -> None:
        self._find_matches = find_matches
        self._rag_retrieve = rag_retrieve
        self._compliance_lookup = compliance_lookup
        self._certification_lookup = certification_lookup
        self._lab_lookup = lab_lookup
        self.model = os.getenv("GEMINI_AGENT_MODEL", "gemini-3.8-flash")
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.enabled = bool(self.api_key)
        self.client: Optional[genai.Client] = genai.Client(api_key=self.api_key) if self.enabled else None

    @staticmethod
    def _grounding_details(response: Any) -> tuple[bool, list[str]]:
        details: list[str] = []
        grounded = False
        candidates = getattr(response, "candidates", []) or []
        objects = [getattr(response, "grounding_metadata", None)]
        if candidates:
            objects.append(getattr(candidates[0], "grounding_metadata", None))
        for metadata in objects:
            if not metadata:
                continue
            queries = getattr(metadata, "web_search_queries", None) or []
            if queries:
                grounded = True
                details.extend(f"Web search: {q}" for q in queries if q)
            for chunk in getattr(metadata, "grounding_chunks", None) or []:
                web = getattr(chunk, "web", None)
                if web:
                    grounded = True
                    title = getattr(web, "title", None)
                    uri = getattr(web, "uri", None)
                    if title and uri:
                        details.append(f"Web evidence: {title} — {uri}")
                    elif uri:
                        details.append(f"Web evidence: {uri}")
        return grounded, list(dict.fromkeys(details))

    def _tool_declarations(self):
        s = types.Schema
        return [
            types.FunctionDeclaration(name="resolve_product_identity", description="Resolve and lock the exact product. Never substitute a related product.", parameters=s(type="OBJECT", properties={"product": s(type="STRING")}, required=["product"])),
            types.FunctionDeclaration(name="analyze_universal_product", description="Run SmartGuide universal product intelligence before making any product-specific BIS claim.", parameters=s(type="OBJECT", properties={"product": s(type="STRING")}, required=["product"])),
            types.FunctionDeclaration(name="search_bis_knowledge", description="Search the local BIS standards corpus for the locked product or IS-number question.", parameters=s(type="OBJECT", properties={"query": s(type="STRING")}, required=["query"])),
            types.FunctionDeclaration(name="search_bis_evidence", description="Retrieve supporting evidence from the local SmartGuide RAG index.", parameters=s(type="OBJECT", properties={"query": s(type="STRING")}, required=["query"])),
            types.FunctionDeclaration(name="check_product_compliance", description="Check supported compliance evidence for the exact product.", parameters=s(type="OBJECT", properties={"product": s(type="STRING")}, required=["product"])),
            types.FunctionDeclaration(name="get_certification_pathway", description="Get the certification workflow for the exact product.", parameters=s(type="OBJECT", properties={"product": s(type="STRING")}, required=["product"])),
            types.FunctionDeclaration(name="find_bis_laboratories", description="Find trusted BIS laboratory/LIMS evidence for the exact product.", parameters=s(type="OBJECT", properties={"product": s(type="STRING")}, required=["product"])),
        ]

    def _call_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if name == "resolve_product_identity":
            q = str(args.get("product", "")).strip()
            return {"user_product": q, "normalized_product": resolve_product(q), "exact_bis_anchor": anchor(q), "identity_locked": True, "instruction": "Keep this exact product identity. Never replace it with a related product."}
        if name == "analyze_universal_product":
            q = str(args.get("product", "")).strip()
            return analyze_universal(q, self._find_matches)
        if name == "search_bis_knowledge":
            q = str(args.get("query", "")).strip()
            return {"query": q, "results": guarded_results(q, self._find_matches(q, 12), 8)}
        if name == "search_bis_evidence":
            q = str(args.get("query", "")).strip()
            return {"query": q, "results": self._rag_retrieve(q, 10)}
        if name == "check_product_compliance":
            return self._compliance_lookup(str(args.get("product", "")).strip())
        if name == "get_certification_pathway":
            return self._certification_lookup(str(args.get("product", "")).strip())
        if name == "find_bis_laboratories":
            return self._lab_lookup(str(args.get("product", "")).strip())
        return {"error": f"Unknown tool: {name}"}

    def _config(self, system: str, tool: types.Tool):
        return types.GenerateContentConfig(
            system_instruction=system,
            tools=[tool],
            tool_config=types.ToolConfig(include_server_side_tool_invocations=True),
            temperature=0.2,
            max_output_tokens=1800,
            response_mime_type="application/json",
            response_schema=FINAL_SCHEMA,
        )

    @staticmethod
    def _safe_unresolved(preflight: Dict[str, Any], language: str) -> Dict[str, Any]:
        product = preflight.get("resolved_product") or preflight.get("input") or "the requested product"
        category = preflight.get("likely_category", "General manufactured product")
        return {
            "reply": f"I could not establish a product-specific BIS standard for {product} from the available SmartGuide evidence. I will not substitute an unrelated standard. Check the official BIS Know Your Standard portal and confirm the current scope/QCO for this product.",
            "product": product,
            "category": category,
            "standards_status": "Evidence insufficient — official verification required",
            "next_actions": preflight.get("next_actions", []),
            "evidence_trail": preflight.get("evidence", []) + ["SmartGuide universal product gateway: no safe product-specific standard match"],
            "confidence": float(preflight.get("confidence", 0.15) or 0.15),
            "source_grounded": bool(preflight.get("evidence")),
            "agent": "BIS SmartGuide Universal Agent",
            "agent_version": "3.2-gemini-universal-guarded",
            "agent_runtime": "gemini-developer-api-free-tier",
            "model": os.getenv("GEMINI_AGENT_MODEL", "gemini-3.8-flash"),
            "language": language or None,
            "web_grounded": False,
            "web_evidence": [],
            "notice": "AI-assisted BIS guidance. Verify current standards, amendments and QCOs against official BIS sources.",
            "tool_calls": 1,
        }

    def run(self, message: str, role: str = "general", language: Optional[str] = None) -> Dict[str, Any]:
        if not self.enabled or self.client is None:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        msg = str(message or "").strip()
        if not msg:
            raise ValueError("Message is required")
        lang = str(language or "").strip().lower()
        language_name = SUPPORTED_LANGUAGES.get(lang, "match the user's language")
        role_name = str(role or "general").strip() or "general"

        # Deterministic preflight: do not depend on Gemini remembering to call the
        # universal product tool. This prevents a generic corpus hit (for example,
        # an air-conditioner record) from being presented for an unrelated product.
        preflight = analyze_universal(msg, self._find_matches)
        exact_product = preflight.get("resolved_product", msg)
        preflight_json = json.dumps(preflight, ensure_ascii=False, default=str)

        system = f"""
You are BIS SmartGuide Universal Agent for India.
Gemini is the reasoning layer, never the BIS source of truth.

HARD PRODUCT SAFETY RULE:
The locked product is exactly: {exact_product}
The deterministic universal-product preflight is authoritative for local product identity.
Never substitute a different product. If preflight has no ranked_standards, you MUST NOT
present any local corpus standard as applicable to the product. In particular, never turn
computer mouse into laptop, keyboard, monitor, air conditioner, mobile phone or another product.

Use the preflight below as a hard constraint:
{preflight_json}

Workflow:
1. Preserve the exact requested product.
2. Use local BIS knowledge/RAG only when it is identity-compatible.
3. If local evidence is insufficient, use Google Search grounding rather than inventing facts.
4. Prioritize official BIS sources: bis.gov.in, services.bis.gov.in, lims.bis.gov.in and official BIS-hosted pages.
5. Distinguish local SmartGuide evidence from web evidence.
6. A standard existing somewhere does not by itself prove mandatory certification/QCO coverage.
7. If neither local evidence nor authoritative web evidence establishes applicability, explicitly say evidence is insufficient.
8. Never invent IS numbers, QCOs, schemes, licences, tests, labs, fees, deadlines or certification outcomes.
9. Keep the final answer concise and practical.
Preferred language: {language_name}. User role: {role_name}.
"""

        contents: list[Any] = [msg]
        tool = types.Tool(google_search=types.GoogleSearch(), function_declarations=self._tool_declarations())
        evidence_calls = 1
        web_grounded = False
        web_evidence: list[str] = []

        # If local preflight is unresolved, still allow Gemini to investigate the
        # official web, but never allow an ungrounded local result to leak through.
        for _ in range(6):
            response = self.client.models.generate_content(model=self.model, contents=contents, config=self._config(system, tool))
            grounded_now, grounding_details = self._grounding_details(response)
            if grounded_now:
                web_grounded = True
                web_evidence.extend(grounding_details)
                web_evidence = list(dict.fromkeys(web_evidence))
            candidate = response.candidates[0] if response.candidates else None
            if not candidate or not candidate.content:
                raise RuntimeError("Gemini returned no candidate response")
            contents.append(candidate.content)
            calls = [p.function_call for p in candidate.content.parts if getattr(p, "function_call", None)]
            if not calls:
                raw = (response.text or "").strip()
                if not raw:
                    raise RuntimeError("Gemini returned an empty response")
                try:
                    structured = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise RuntimeError(f"Gemini structured output was invalid: {exc}") from exc

                # Final deterministic guard. When no local standard was established and
                # Gemini did not actually use web grounding, discard any unrelated standard
                # claim and return the safe unresolved result.
                if not preflight.get("ranked_standards") and not web_grounded:
                    return self._safe_unresolved(preflight, lang)

                structured.setdefault("reply", raw)
                structured.setdefault("product", exact_product)
                structured.setdefault("category", preflight.get("likely_category", "Unknown"))
                structured.setdefault("standards_status", "Needs verification")
                structured.setdefault("next_actions", preflight.get("next_actions", []))
                structured.setdefault("evidence_trail", [])
                structured.setdefault("confidence", 0)
                if web_evidence:
                    existing = [str(x) for x in structured.get("evidence_trail", [])]
                    structured["evidence_trail"] = existing + [x for x in web_evidence if x not in existing]
                structured["product"] = exact_product
                structured["source_grounded"] = bool(structured.get("source_grounded", True)) or web_grounded
                return {
                    **structured,
                    "agent": self.name,
                    "agent_version": self.version,
                    "agent_runtime": "gemini-developer-api-free-tier",
                    "model": self.model,
                    "role": role_name,
                    "language": lang or None,
                    "web_grounded": web_grounded,
                    "web_evidence": web_evidence,
                    "notice": "AI-assisted BIS guidance. Verify current standards, amendments and QCOs against official BIS sources.",
                    "tool_calls": evidence_calls,
                }

            for call in calls:
                evidence_calls += 1
                args = dict(call.args or {})
                result = self._call_tool(call.name, args)
                contents.append(types.Content(role="tool", parts=[types.Part.from_function_response(name=call.name, response={"result": result}, id=getattr(call, "id", None))]))

        raise RuntimeError("Gemini agent reached its tool-call limit without producing an answer")
