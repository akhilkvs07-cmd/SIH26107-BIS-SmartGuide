"""OpenAI Agents SDK orchestration layer for BIS SmartGuide.

This module deliberately sits above the existing BIS knowledge/RAG layer. The
LLM interprets arbitrary user questions and decides which trusted SmartGuide
tools to call; the tools remain the source of BIS-specific evidence.

If OPENAI_API_KEY is absent, the caller can fall back to the existing
BISExpertAgent so the deployment remains backwards compatible.
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Dict, Optional

from agents import Agent, Runner, function_tool


SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "kn": "Kannada",
    "te": "Telugu",
    "ta": "Tamil",
}


class OpenAIBISAgent:
    """Universal product/compliance orchestrator backed by OpenAI Agents SDK."""

    name = "BIS SmartGuide Universal Agent"
    version = "1.0"

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
        self.model = os.getenv("OPENAI_AGENT_MODEL", "gpt-5-mini")
        self.enabled = bool(os.getenv("OPENAI_API_KEY", "").strip())
        self._agent: Optional[Agent] = None
        if self.enabled:
            self._agent = self._build_agent()

    @staticmethod
    def _json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, default=str)

    def _build_agent(self) -> Agent:
        @function_tool
        def search_bis_knowledge(query: str) -> str:
            """Search the SmartGuide BIS standards corpus for any product or question.

            Use this first for product identification and applicable-standard discovery.
            Returns ranked local knowledge-base matches and their evidence fields.
            """
            matches = self._find_matches(str(query).strip(), 8)
            return self._json({"query": query, "count": len(matches), "results": matches})

        @function_tool
        def search_bis_evidence(query: str) -> str:
            """Retrieve evidence chunks from the SmartGuide local RAG index."""
            results = self._rag_retrieve(str(query).strip(), 10)
            return self._json({"query": query, "count": len(results), "results": results})

        @function_tool
        def check_product_compliance(product: str) -> str:
            """Check the best-supported BIS compliance assessment for a product."""
            return self._json(self._compliance_lookup(str(product).strip()))

        @function_tool
        def get_certification_pathway(product: str) -> str:
            """Get the SmartGuide certification workflow for a product."""
            return self._json(self._certification_lookup(str(product).strip()))

        @function_tool
        def find_bis_laboratories(product: str) -> str:
            """Return the trusted SmartGuide laboratory/LIMS handoff for a product."""
            return self._json(self._lab_lookup(str(product).strip()))

        instructions = """
You are BIS SmartGuide Universal Agent, the orchestration brain of a BIS standards
and compliance assistant for India.

Your job is to understand natural-language questions about ANY physical product,
including products that are not explicitly named in the product catalogue. Never
require the product to be hardcoded. Normalize colloquial descriptions yourself,
then use the SmartGuide tools to investigate.

SOURCE-OF-TRUTH RULES:
- SmartGuide tool results and retrieved evidence are the source of truth for BIS-specific claims.
- Do not invent an IS number, QCO, mandatory status, scheme, test requirement, licence
  requirement, laboratory capability, fee, deadline, or certification outcome.
- If evidence is insufficient, clearly say that applicability is unconfirmed and explain
  what should be verified. Do NOT convert uncertainty into a confident answer.
- Distinguish an applicable Indian Standard from mandatory certification/QCO coverage.
- Distinguish AI guidance from an official BIS decision or certification.
- Prefer official-source fields returned by SmartGuide tools when presenting sources.

AGENT WORKFLOW:
1. Understand the user's intent and product, even when the wording is vague.
2. Search BIS knowledge for the product/question.
3. Retrieve RAG evidence when a substantive BIS claim needs support.
4. Use compliance/certification/lab tools when the question requires them.
5. Synthesize only what the evidence supports.
6. Give practical next actions.

For broad product questions, do not stop after an exact-name miss. Search using the
normalized product/category terminology and related technical terms. If no supported
relationship can be established after investigation, return a useful low-confidence
answer rather than hallucinating.

RESPONSE FORMAT:
- Start with a concise direct answer.
- Identify the interpreted product/category when useful.
- Give applicable standards and regulatory status only when supported.
- Provide an actionable next-step workflow for compliance/certification questions.
- End with an Evidence Trail listing the SmartGuide evidence/tool findings used.
- State confidence as High/Medium/Low when evidence is uncertain.
- Keep answers concise enough for a web chat UI.
"""

        return Agent(
            name=self.name,
            model=self.model,
            instructions=instructions,
            tools=[
                search_bis_knowledge,
                search_bis_evidence,
                check_product_compliance,
                get_certification_pathway,
                find_bis_laboratories,
            ],
        )

    def run(self, message: str, role: str = "general", language: Optional[str] = None) -> Dict[str, Any]:
        if not self.enabled or self._agent is None:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        lang = str(language or "").strip().lower()
        language_name = SUPPORTED_LANGUAGES.get(lang)
        role_name = str(role or "general").strip() or "general"
        prompt = (
            f"User role: {role_name}.\n"
            f"Preferred response language: {language_name or 'match the user language'}.\n"
            f"User question: {str(message).strip()}"
        )
        result = Runner.run_sync(self._agent, prompt)
        output = str(result.final_output).strip()
        return {
            "reply": output,
            "agent": self.name,
            "agent_version": self.version,
            "agent_runtime": "openai-agents-sdk",
            "model": self.model,
            "role": role_name,
            "language": lang or None,
            "source_grounded": True,
            "notice": "AI-assisted BIS guidance. Verify current standards, amendments and QCOs against official BIS sources.",
        }
