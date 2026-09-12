"""Gemini-powered universal BIS SmartGuide agent."""
from __future__ import annotations

import json
import os
import re
from typing import Any, Callable, Dict, Optional

from google import genai
from google.genai import types
from product_guard import anchor, guarded_results, resolve_product
from universal_product_v2 import analyze_universal

SUPPORTED_LANGUAGES = {"en": "English", "hi": "Hindi", "kn": "Kannada", "te": "Telugu", "ta": "Tamil"}

FINAL_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "reply": {"type": "STRING"}, "product": {"type": "STRING"},
        "category": {"type": "STRING"}, "standards_status": {"type": "STRING"},
        "next_actions": {"type": "ARRAY", "items": {"type": "STRING"}},
        "evidence_trail": {"type": "ARRAY", "items": {"type": "STRING"}},
        "confidence": {"type": "NUMBER"}, "source_grounded": {"type": "BOOLEAN"},
    },
    "required": ["reply", "product", "category", "standards_status", "next_actions", "evidence_trail", "confidence", "source_grounded"],
}


class GeminiBISAgent:
    name = "BIS SmartGuide Universal Agent"
    version = "3.3-gemini-universal-guarded"

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
    def _is_casual_message(message: str) -> bool:
        """Keep greetings and basic small talk out of product/BIS resolution."""
        text = re.sub(r"[^a-z\s!?]", " ", str(message or "").lower()).strip()
        text = re.sub(r"\s+", " ", text)
        if not text:
            return False
        greetings = {
            "hi", "hii", "hiii", "hello", "hey", "heyy", "helo", "hai",
            "good morning", "good afternoon", "good evening", "good night",
            "thanks", "thank you", "thankyou", "ok", "okay", "bye", "goodbye",
            "who are you", "what can you do", "help", "namaste",
        }
        return text in greetings or (len(text.split()) <= 3 and any(text.startswith(x) for x in ("hi ", "hello ", "hey ")))

    @staticmethod
    def _casual_response(message: str, language: str) -> Dict[str, Any]:
        return {
            "reply": "Hello! I’m BIS SmartGuide AI. I can help you find Indian Standards, understand BIS certification and QCO requirements, locate laboratories, and answer product-compliance questions. What product or BIS service do you need help with?",
            "product": "",
            "category": "Conversation",
            "standards_status": "Not applicable — casual conversation",
            "next_actions": ["Ask about a product, Indian Standard, BIS certification, QCO, laboratory or consumer service."],
            "evidence_trail": [],
            "confidence": 1.0,
            "source_grounded": False,
            "agent": "BIS SmartGuide Universal Agent",
            "agent_version": "3.3-gemini-universal-guarded",
            "agent_runtime": "gemini-developer-api-free-tier",
            "model": os.getenv("GEMINI_AGENT_MODEL", "gemini-3.8-flash"),
            "language": language or None,
            "web_grounded": False,
            "web_evidence": [],
            "notice": "Ask a product or BIS service question to start evidence-grounded guidance.",
            "tool_calls": 0,
        }

    @staticmethod
    def _grounding_details(response: Any) -> tuple[bool, list[str]]:
        details, grounded = [], False
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
                    title, uri = getattr(web, "title", None), getattr(web, "uri", None)
                    if title and uri: details.append(f"Web evidence: {title} — {uri}")
                    elif uri: details.append(f"Web evidence: {uri}")
        return grounded, list(dict.fromkeys(details))

    def _tool_declarations(self):
        s = types.Schema
        return [
            types.FunctionDeclaration(name="resolve_product_identity", description="Resolve and lock the exact product. Never substitute a related product.", parameters=s(type="OBJECT", properties={"product": s(type="STRING")}, required=["product"])),
            types.FunctionDeclaration(name="analyze_universal_product", description="Run SmartGuide universal product intelligence before product-specific BIS claims.", parameters=s(type="OBJECT", properties={"product": s(type="STRING")}, required=["product"])),
            types.FunctionDeclaration(name="search_bis_knowledge", description="Search the local BIS standards corpus.", parameters=s(type="OBJECT", properties={"query": s(type="STRING")}, required=["query"])),
            types.FunctionDeclaration(name="search_bis_evidence", description="Retrieve supporting evidence from local SmartGuide RAG.", parameters=s(type="OBJECT", properties={"query": s(type="STRING")}, required=["query"])),
            types.FunctionDeclaration(name="check_product_compliance", description="Check compliance evidence for the exact product.", parameters=s(type="OBJECT", properties={"product": s(type="STRING")}, required=["product"])),
            types.FunctionDeclaration(name="get_certification_pathway", description="Get certification workflow for the exact product.", parameters=s(type="OBJECT", properties={"product": s(type="STRING")}, required=["product"])),
            types.FunctionDeclaration(name="find_bis_laboratories", description="Find BIS laboratory/LIMS evidence.", parameters=s(type="OBJECT", properties={"product": s(type="STRING")}, required=["product"])),
        ]

    def _call_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        q = str(args.get("product", args.get("query", ""))).strip()
        if name == "resolve_product_identity":
            return {"user_product": q, "normalized_product": resolve_product(q), "exact_bis_anchor": anchor(q), "identity_locked": True, "instruction": "Keep this exact product identity. Never replace it with a related product."}
        if name == "analyze_universal_product": return analyze_universal(q, self._find_matches)
        if name == "search_bis_knowledge": return {"query": q, "results": guarded_results(q, self._find_matches(q, 12), 8)}
        if name == "search_bis_evidence": return {"query": q, "results": self._rag_retrieve(q, 10)}
        if name == "check_product_compliance": return self._compliance_lookup(q)
        if name == "get_certification_pathway": return self._certification_lookup(q)
        if name == "find_bis_laboratories": return self._lab_lookup(q)
        return {"error": f"Unknown tool: {name}"}

    def _config(self, system: str, tool: types.Tool):
        return types.GenerateContentConfig(system_instruction=system, tools=[tool], tool_config=types.ToolConfig(include_server_side_tool_invocations=True), temperature=0.2, max_output_tokens=1800, response_mime_type="application/json", response_schema=FINAL_SCHEMA)

    @staticmethod
    def _safe_unresolved(preflight: Dict[str, Any], language: str) -> Dict[str, Any]:
        product = preflight.get("resolved_product") or preflight.get("input") or "the requested product"
        return {"reply": f"I could not establish a product-specific BIS standard for {product} from the available SmartGuide evidence. I will not substitute an unrelated standard. Check the official BIS Know Your Standard portal and confirm the current scope/QCO for this product.", "product": product, "category": preflight.get("likely_category", "General manufactured product"), "standards_status": "Evidence insufficient — official verification required", "next_actions": preflight.get("next_actions", []), "evidence_trail": preflight.get("evidence", []) + ["SmartGuide universal product gateway: no safe product-specific standard match"], "confidence": float(preflight.get("confidence", 0.15) or 0.15), "source_grounded": bool(preflight.get("evidence")), "agent": self.name, "agent_version": self.version, "agent_runtime": "gemini-developer-api-free-tier", "model": os.getenv("GEMINI_AGENT_MODEL", "gemini-3.8-flash"), "language": language or None, "web_grounded": False, "web_evidence": [], "notice": "AI-assisted BIS guidance. Verify current standards, amendments and QCOs against official BIS sources.", "tool_calls": 1}

    def run(self, message: str, role: str = "general", language: Optional[str] = None) -> Dict[str, Any]:
        if not self.enabled or self.client is None: raise RuntimeError("GEMINI_API_KEY is not configured")
        msg = str(message or "").strip()
        if not msg: raise ValueError("Message is required")
        lang = str(language or "").strip().lower()
        if self._is_casual_message(msg): return self._casual_response(msg, lang)
        language_name = SUPPORTED_LANGUAGES.get(lang, "match the user's language")
        role_name = str(role or "general").strip() or "general"
        preflight = analyze_universal(msg, self._find_matches)
        exact_product = preflight.get("resolved_product", msg)
        preflight_json = json.dumps(preflight, ensure_ascii=False, default=str)
        system = f"""You are BIS SmartGuide Universal Agent for India. Gemini is the reasoning layer, never the BIS source of truth.\n\nHARD PRODUCT SAFETY RULE: The locked product is exactly: {exact_product}. Never substitute a different product. If preflight has no ranked_standards, do not present a local corpus standard as applicable.\n\nPreflight:\n{preflight_json}\n\nUse local evidence first. If insufficient, use Google Search grounding and prioritize official BIS sources. Distinguish local evidence from web evidence. Never invent IS numbers, QCOs, schemes, licences, tests, labs, fees, deadlines or certification outcomes. Preferred language: {language_name}. User role: {role_name}."""
        contents: list[Any] = [msg]
        tool = types.Tool(google_search=types.GoogleSearch(), function_declarations=self._tool_declarations())
        evidence_calls, web_grounded, web_evidence = 1, False, []
        for _ in range(6):
            response = self.client.models.generate_content(model=self.model, contents=contents, config=self._config(system, tool))
            grounded_now, details = self._grounding_details(response)
            if grounded_now: web_grounded, web_evidence = True, list(dict.fromkeys(web_evidence + details))
            candidate = response.candidates[0] if response.candidates else None
            if not candidate or not candidate.content: raise RuntimeError("Gemini returned no candidate response")
            contents.append(candidate.content)
            calls = [p.function_call for p in candidate.content.parts if getattr(p, "function_call", None)]
            if not calls:
                raw = (response.text or "").strip()
                if not raw: raise RuntimeError("Gemini returned an empty response")
                try: structured = json.loads(raw)
                except json.JSONDecodeError as exc: raise RuntimeError(f"Gemini structured output was invalid: {exc}") from exc
                if not preflight.get("ranked_standards") and not web_grounded: return self._safe_unresolved(preflight, lang)
                structured.setdefault("reply", raw); structured.setdefault("product", exact_product); structured.setdefault("category", preflight.get("likely_category", "Unknown")); structured.setdefault("standards_status", "Needs verification"); structured.setdefault("next_actions", preflight.get("next_actions", [])); structured.setdefault("evidence_trail", []); structured.setdefault("confidence", 0)
                structured["product"] = exact_product
                if web_evidence: structured["evidence_trail"] = list(structured.get("evidence_trail", [])) + [x for x in web_evidence if x not in structured.get("evidence_trail", [])]
                structured["source_grounded"] = bool(structured.get("source_grounded", True)) or web_grounded
                return {**structured, "agent": self.name, "agent_version": self.version, "agent_runtime": "gemini-developer-api-free-tier", "model": self.model, "role": role_name, "language": lang or None, "web_grounded": web_grounded, "web_evidence": web_evidence, "notice": "AI-assisted BIS guidance. Verify current standards, amendments and QCOs against official BIS sources.", "tool_calls": evidence_calls}
            for call in calls:
                evidence_calls += 1
                result = self._call_tool(call.name, dict(call.args or {}))
                contents.append(types.Content(role="tool", parts=[types.Part.from_function_response(name=call.name, response={"result": result}, id=getattr(call, "id", None))]))
        raise RuntimeError("Gemini agent reached its tool-call limit without producing an answer")
