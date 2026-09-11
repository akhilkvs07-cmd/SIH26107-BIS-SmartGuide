"""Gemini-powered universal BIS SmartGuide agent.

Uses the Gemini Developer API free tier and keeps BIS-specific truth inside the
existing SmartGuide knowledge/RAG/tool layer. Gemini decides which tools to use;
the returned evidence is then used to produce the final answer.
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Dict, Optional

from google import genai
from google.genai import types


SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "kn": "Kannada",
    "te": "Telugu",
    "ta": "Tamil",
}


class GeminiBISAgent:
    name = "BIS SmartGuide Universal Agent"
    version = "2.0-gemini"

    def __init__(
        self,
        find_matches: Callable[[str, int], list],
        rag_retrieve: Callable[[str, int], list],
        compliance_lookup: Callable[[str], Dict[str, Any]],
        certification_lookup: Callable[[str], Dict[str, Any]],
        lab_lookup: Callable[[str], Dict[str, Any]],
    ) -> None:
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
                name="search_bis_knowledge",
                description="Search the SmartGuide BIS standards corpus for any product or standards question.",
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
                description="Check the supported BIS compliance assessment for a product.",
                parameters=types.Schema(type="OBJECT", properties={
                    "product": types.Schema(type="STRING", description="Physical product description")
                }, required=["product"]),
            ),
            types.FunctionDeclaration(
                name="get_certification_pathway",
                description="Get the SmartGuide certification workflow for a product.",
                parameters=types.Schema(type="OBJECT", properties={
                    "product": types.Schema(type="STRING", description="Physical product description")
                }, required=["product"]),
            ),
            types.FunctionDeclaration(
                name="find_bis_laboratories",
                description="Return the trusted BIS laboratory directory and LIMS handoff for a product.",
                parameters=types.Schema(type="OBJECT", properties={
                    "product": types.Schema(type="STRING", description="Physical product description")
                }, required=["product"]),
            ),
        ]

    def _call_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if name == "search_bis_knowledge":
            q = str(args.get("query", "")).strip()
            return {"query": q, "results": self._find_matches(q, 8)}
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

Understand ANY physical manufactured product, even if it is not hardcoded in the
catalogue. Normalize colloquial product names and investigate using SmartGuide tools.
The tools are the source of truth for BIS-specific claims.
Never invent an IS number, QCO, mandatory status, scheme, test requirement, licence,
laboratory capability, fee, deadline, or certification outcome.
If evidence is insufficient, say so clearly. Distinguish an applicable Indian Standard
from mandatory certification/QCO coverage. Distinguish AI guidance from an official BIS decision.

Use tools deliberately:
- Start with BIS knowledge for product/standard discovery.
- Retrieve RAG evidence when making substantive BIS claims.
- Use compliance for compliance questions.
- Use certification for licensing/certification questions.
- Use laboratory search for testing/lab questions.
- You may call multiple tools before answering.

Return a concise, practical answer with the interpreted product/category, supported
standards/regulatory status, next actions, confidence, and an Evidence Trail.
Preferred language: {language_name}.
User role: {role_name}.
"""

        contents: list[Any] = [str(message).strip()]
        tool = types.Tool(function_declarations=self._tool_declarations())
        evidence_calls = 0
        max_rounds = 4

        for _ in range(max_rounds):
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    tools=[tool],
                    temperature=0.2,
                ),
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
                    "reply": output,
                    "agent": self.name,
                    "agent_version": self.version,
                    "agent_runtime": "gemini-developer-api-free-tier",
                    "model": self.model,
                    "role": role_name,
                    "language": lang or None,
                    "source_grounded": True,
                    "notice": "AI-assisted BIS guidance. Verify current standards, amendments and QCOs against official BIS sources.",
                    "tool_calls": evidence_calls,
                }

            for call in calls:
                evidence_calls += 1
                args = dict(call.args or {})
                result = self._call_tool(call.name, args)
                contents.append(types.Content(
                    role="tool",
                    parts=[types.Part.from_function_response(name=call.name, response={"result": result})],
                ))

        raise RuntimeError("Gemini agent reached its tool-call limit without producing an answer")
