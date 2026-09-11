"""Gemini-powered universal BIS SmartGuide agent with deterministic product grounding."""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Dict, Optional

from google import genai
from google.genai import types
from product_guard import anchor, guarded_results, resolve_product

SUPPORTED_LANGUAGES = {
    "en": "English", "hi": "Hindi", "kn": "Kannada", "te": "Telugu", "ta": "Tamil",
}


class GeminiBISAgent:
    name = "BIS SmartGuide Universal Agent"
    version = "2.1-gemini-product-grounded"

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
                description="Resolve the exact product identity before selecting BIS standards. Never substitute a nearby product.",
                parameters=types.Schema(type="OBJECT", properties={
                    "product": types.Schema(type="STRING", description="The exact product named or described by the user")
                }, required=["product"]),
            ),
            types.FunctionDeclaration(
                name="search_bis_knowledge",
                description="Search the SmartGuide BIS standards corpus for the already-resolved product or standards question.",
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
                description="Check the supported BIS compliance assessment for the resolved product.",
                parameters=types.Schema(type="OBJECT", properties={
                    "product": types.Schema(type="STRING", description="Resolved physical product description")
                }, required=["product"]),
            ),
            types.FunctionDeclaration(
                name="get_certification_pathway",
                description="Get the SmartGuide certification workflow for the resolved product.",
                parameters=types.Schema(type="OBJECT", properties={
                    "product": types.Schema(type="STRING", description="Resolved physical product description")
                }, required=["product"]),
            ),
            types.FunctionDeclaration(
                name="find_bis_laboratories",
                description="Return the trusted BIS laboratory directory and LIMS handoff for the resolved product.",
                parameters=types.Schema(type="OBJECT", properties={
                    "product": types.Schema(type="STRING", description="Resolved physical product description")
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
                "instruction": "Use this product identity. Do not replace it with a related product.",
            }
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

    def run(self, message: str, role: str = "general", language: Optional[str] = None) -> Dict[str, Any]:
        if not self.enabled or self.client is None:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        lang = str(language or "").strip().lower()
        language_name = SUPPORTED_LANGUAGES.get(lang, "match the user's language")
        role_name = str(role or "general").strip() or "general"
        system = f"""
You are BIS SmartGuide Universal Agent for India.

PRODUCT IDENTITY IS LOCKED BEFORE ANSWERING.
Always call resolve_product_identity first. Treat its user_product/normalized_product as the
exact product requested. Never substitute a related product merely because it shares a BIS
standard. Example: keyboard is NOT laptop/notebook/tablet. If the user asks keyboard, the
final answer must say keyboard.

Use SmartGuide tools as the source of BIS-specific truth. Never invent an IS number, QCO,
mandatory status, scheme, test requirement, licence, laboratory capability, fee, deadline,
or certification outcome. Distinguish an applicable Indian Standard from mandatory coverage.
If evidence is insufficient, say so rather than guessing.

Workflow:
1. Resolve and lock product identity.
2. Search BIS knowledge for that exact product.
3. Retrieve RAG evidence for substantive BIS claims.
4. Use compliance/certification/lab tools when relevant.
5. Answer only for the locked product and report uncertainty honestly.

Return a concise practical answer with product, category, standards/regulatory status, next
actions, confidence, and Evidence Trail. Preferred language: {language_name}. User role: {role_name}.
"""
        contents: list[Any] = [str(message).strip()]
        tool = types.Tool(function_declarations=self._tool_declarations())
        evidence_calls = 0
        max_rounds = 5
        for _ in range(max_rounds):
            response = self.client.models.generate_content(
                model=self.model, contents=contents,
                config=types.GenerateContentConfig(system_instruction=system, tools=[tool], temperature=0.2),
            )
            candidate = response.candidates[0] if response.candidates else None
            if not candidate or not candidate.content:
                raise RuntimeError("Gemini returned no candidate response")
            contents.append(candidate.content)
            calls = [p.function_call for p in candidate.content.parts if getattr(p, "function_call", None)]
            if not calls:
                output = (response.text or "").strip()
                if not output:
                    raise RuntimeError("Gemini returned an empty response")
                return {
                    "reply": output, "agent": self.name, "agent_version": self.version,
                    "agent_runtime": "gemini-developer-api-free-tier", "model": self.model,
                    "role": role_name, "language": lang or None, "source_grounded": True,
                    "notice": "AI-assisted BIS guidance. Verify current standards, amendments and QCOs against official BIS sources.",
                    "tool_calls": evidence_calls,
                }
            for call in calls:
                evidence_calls += 1
                args = dict(call.args or {})
                result = self._call_tool(call.name, args)
                contents.append(types.Content(
                    role="tool", parts=[types.Part.from_function_response(name=call.name, response={"result": result})]
                ))
        raise RuntimeError("Gemini agent reached its tool-call limit without producing an answer")
