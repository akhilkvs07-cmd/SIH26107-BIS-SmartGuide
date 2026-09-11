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

SUPPORTED_LANGUAGES = {
    "en": "English", "hi": "Hindi", "kn": "Kannada", "te": "Telugu", "ta": "Tamil",
}

FINAL_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "reply": {"type": "STRING", "description": "Concise user-facing BIS guidance."},
        "product": {"type": "STRING", "description": "The exact product requested by the user."},
        "category": {"type": "STRING", "description": "Best supported broad product category."},
        "standards_status": {"type": "STRING", "description": "Supported, unresolved, or needs verification."},
        "next_actions": {"type": "ARRAY", "items": {"type": "STRING"}},
        "evidence_trail": {"type": "ARRAY", "items": {"type": "STRING"}},
        "confidence": {"type": "NUMBER", "description": "Model assessment from 0 to 1 based only on evidence."},
        "source_grounded": {"type": "BOOLEAN"},
    },
    "required": ["reply", "product", "category", "standards_status", "next_actions", "evidence_trail", "confidence", "source_grounded"],
}


class GeminiBISAgent:
    name = "BIS SmartGuide Universal Agent"
    version = "3.0-gemini-universal-orchestrator"

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
    def _json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, default=str)

    def _tool_declarations(self):
        return [
            types.FunctionDeclaration(
                name="resolve_product_identity",
                description="Resolve and lock the exact product. Never substitute a related product.",
                parameters=types.Schema(type="OBJECT", properties={
                    "product": types.Schema(type="STRING", description="Exact product named by the user")
                }, required=["product"]),
            ),
            types.FunctionDeclaration(
                name="analyze_universal_product",
                description="Run SmartGuide's universal product gateway. Use this before making BIS standard, category, QCO, compliance or lab claims.",
                parameters=types.Schema(type="OBJECT", properties={
                    "product": types.Schema(type="STRING", description="The locked physical product description")
                }, required=["product"]),
            ),
            types.FunctionDeclaration(
                name="search_bis_knowledge",
                description="Search the SmartGuide BIS standards corpus for the resolved product or IS-number question.",
                parameters=types.Schema(type="OBJECT", properties={
                    "query": types.Schema(type="STRING", description="Product, category, IS number, or standards question")
                }, required=["query"]),
            ),
            types.FunctionDeclaration(
                name="search_bis_evidence",
                description="Retrieve supporting evidence chunks from the SmartGuide local RAG index.",
                parameters=types.Schema(type="OBJECT", properties={
                    "query": types.Schema(type="STRING", description="Question or product to retrieve evidence for")
                }, required=["query"]),
            ),
            types.FunctionDeclaration(
                name="check_product_compliance",
                description="Check the supported BIS compliance assessment for the exact resolved product.",
                parameters=types.Schema(type="OBJECT", properties={
                    "product": types.Schema(type="STRING", description="Resolved physical product")
                }, required=["product"]),
            ),
            types.FunctionDeclaration(
                name="get_certification_pathway",
                description="Get the SmartGuide certification workflow for the exact resolved product.",
                parameters=types.Schema(type="OBJECT", properties={
                    "product": types.Schema(type="STRING", description="Resolved physical product")
                }, required=["product"]),
            ),
            types.FunctionDeclaration(
                name="find_bis_laboratories",
                description="Find trusted BIS laboratory directory/LIMS evidence for the exact resolved product.",
                parameters=types.Schema(type="OBJECT", properties={
                    "product": types.Schema(type="STRING", description="Resolved physical product")
                }, required=["product"]),
            ),
        ]

    def _call_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if name == "resolve_product_identity":
            q = str(args.get("product", "")).strip()
            exact = anchor(q)
            return {
                "user_product": q,
                "normalized_product": resolve_product(q),
                "exact_bis_anchor": exact,
                "identity_locked": True,
                "instruction": "Keep this exact product identity. Do not replace it with a related product.",
            }
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
            temperature=0.2,
            max_output_tokens=1800,
            response_mime_type="application/json",
            response_schema=FINAL_SCHEMA,
        )

    def run(self, message: str, role: str = "general", language: Optional[str] = None) -> Dict[str, Any]:
        if not self.enabled or self.client is None:
            raise RuntimeError("GEMINI_API_KEY is not configured")

        lang = str(language or "").strip().lower()
        language_name = SUPPORTED_LANGUAGES.get(lang, "match the user's language")
        role_name = str(role or "general").strip() or "general"
        system = f"""
You are BIS SmartGuide Universal Agent for India.

You are the reasoning and orchestration layer, NOT the source of BIS truth.
SmartGuide local corpus, RAG, QCO/compliance data, certification data and BIS LIMS
handoff are evidence sources. Never invent an IS number, QCO, mandatory status, scheme,
test requirement, licence, laboratory capability, fee, deadline or certification outcome.

MANDATORY PRODUCT WORKFLOW:
1. Call resolve_product_identity first and lock the exact user product.
2. Call analyze_universal_product for every product-related request.
3. Use BIS knowledge and RAG tools for supporting evidence.
4. Use compliance/certification/lab tools when the user's question needs them.
5. If local evidence is insufficient, you may use Google Search only to locate current
   authoritative/public information. Prefer official BIS domains and clearly distinguish
   web evidence from the SmartGuide local corpus. Never let a web result silently replace
   the locked product identity.
6. Never substitute a related product. A mouse is not a mobile phone; a keyboard is not a laptop.
7. An unresolved product is still a valid product request. Say that evidence is insufficient
   rather than treating it as NON_PRODUCT or fabricating a standard.

Use reasoning to synthesize the evidence, not to create unsupported facts.
Return JSON matching the supplied schema. The reply should be concise and practical.
Preferred language: {language_name}. User role: {role_name}.
"""

        contents: list[Any] = [str(message).strip()]
        tool = types.Tool(
            google_search=types.GoogleSearch(),
            function_declarations=self._tool_declarations(),
        )
        evidence_calls = 0
        web_grounded = False
        max_rounds = 6

        for _ in range(max_rounds):
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=self._config(system, tool),
            )
            candidate = response.candidates[0] if response.candidates else None
            if not candidate or not candidate.content:
                raise RuntimeError("Gemini returned no candidate response")
            contents.append(candidate.content)

            metadata = getattr(candidate, "grounding_metadata", None)
            if metadata and (getattr(metadata, "web_search_queries", None) or getattr(metadata, "grounding_chunks", None)):
                web_grounded = True

            calls = [p.function_call for p in candidate.content.parts if getattr(p, "function_call", None)]
            if not calls:
                raw = (response.text or "").strip()
                if not raw:
                    raise RuntimeError("Gemini returned an empty response")
                try:
                    structured = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise RuntimeError(f"Gemini structured output was invalid: {exc}") from exc
                structured.setdefault("reply", raw)
                structured.setdefault("product", "")
                structured.setdefault("category", "Unknown")
                structured.setdefault("standards_status", "Needs verification")
                structured.setdefault("next_actions", [])
                structured.setdefault("evidence_trail", [])
                structured.setdefault("confidence", 0)
                structured["source_grounded"] = bool(structured.get("source_grounded", True))
                return {
                    **structured,
                    "agent": self.name,
                    "agent_version": self.version,
                    "agent_runtime": "gemini-developer-api-free-tier",
                    "model": self.model,
                    "role": role_name,
                    "language": lang or None,
                    "source_grounded": bool(structured.get("source_grounded", True)),
                    "web_grounded": web_grounded,
                    "notice": "AI-assisted BIS guidance. Verify current standards, amendments and QCOs against official BIS sources.",
                    "tool_calls": evidence_calls,
                }

            for call in calls:
                evidence_calls += 1
                args = dict(call.args or {})
                result = self._call_tool(call.name, args)
                contents.append(types.Content(
                    role="tool",
                    parts=[types.Part.from_function_response(
                        name=call.name,
                        response={"result": result},
                        id=getattr(call, "id", None),
                    )],
                ))

        raise RuntimeError("Gemini agent reached its tool-call limit without producing an answer")
