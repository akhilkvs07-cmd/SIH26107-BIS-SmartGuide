"""BIS Standards Intelligence Agent.

A lightweight, dependency-free agentic layer for the SmartGuide chatbot.
It selects the most useful local tool (standards search, RAG, certification,
laboratory guidance, or compliance guidance) and returns a structured answer.
This keeps the prototype functional without requiring an external API key.
"""


class BISExpertAgent:
    name = "BIS Standards Intelligence Agent"
    version = "1.0"

    def __init__(self, find_matches, rag, resources, certification_steps):
        self.find_matches = find_matches
        self.rag = rag
        self.resources = resources
        self.certification_steps = certification_steps

    @staticmethod
    def _normalize(text):
        return " ".join(str(text or "").lower().split())

    def _standard_tool(self, message):
        matches = self.find_matches(message, 3)
        if not matches:
            return None
        top = matches[0]
        requirements = top.get("requirements", [])
        requirement_text = " ".join(f"• {item}" for item in requirements) if requirements else "No prototype requirements are listed."
        reply = (
            f"Based on the SmartGuide knowledge base, the strongest match is "
            f"{top.get('standard_number')} — {top.get('title')}.\n\n"
            f"{top.get('description', '')}\n\n"
            f"Key prototype requirement areas:\n{requirement_text}\n\n"
            f"Scheme: {top.get('scheme', 'Not specified')}\n"
            f"Source: {top.get('official_source', 'Verify on the official BIS website.')}"
        )
        return {
            "reply": reply,
            "intent": "standard_search",
            "tool": "BIS Standard Finder",
            "recommendations": matches,
            "sources": [top.get("official_source")] if top.get("official_source") else [],
        }

    def _certification_tool(self, message):
        matches = self.find_matches(message, 1)
        standard = matches[0] if matches else None
        steps = self.certification_steps(standard)
        standard_name = standard.get("standard_number") if standard else "the applicable BIS standard"
        reply = (
            f"For BIS certification of {standard_name}, use this high-level workflow:\n"
            + "\n".join(f"{i + 1}. {step}" for i, step in enumerate(steps))
            + "\n\nAlways verify the current BIS scheme, notification and applicable requirements before making a certification decision."
        )
        return {
            "reply": reply,
            "intent": "certification",
            "tool": "BIS Certification Guide",
            "recommendations": matches,
            "sources": [self.resources[1]["url"], self.resources[2]["url"]],
        }

    def _laboratory_tool(self, message):
        reply = (
            "For current product testing laboratories, use the official BIS recognized laboratory directory "
            "and BIS LIMS. SmartGuide does not invent laboratory availability or accreditation status.\n\n"
            f"Recognized laboratories: {self.resources[3]['url']}\n"
            f"BIS LIMS: {self.resources[4]['url']}"
        )
        return {
            "reply": reply,
            "intent": "laboratory",
            "tool": "BIS Laboratory Guide",
            "recommendations": [],
            "sources": [self.resources[3]["url"], self.resources[4]["url"]],
        }

    def _rag_tool(self, message):
        result = self.rag.answer(message, 5)
        reply = result["answer"]
        return {
            "reply": reply,
            "intent": "rag_knowledge",
            "tool": "Local BIS RAG",
            "recommendations": [],
            "sources": result.get("sources", []),
            "retrieved": result.get("retrieved", []),
            "retrieved_count": result.get("retrieved_count", 0),
        }

    def run(self, message):
        text = self._normalize(message)
        if any(x in text for x in ["certification", "certificate", "license", "licence", "apply", "registration"]):
            result = self._certification_tool(message)
        elif any(x in text for x in ["lab", "laboratory", "testing lab", "test lab"]):
            result = self._laboratory_tool(message)
        else:
            result = self._standard_tool(message)
            if result is None:
                result = self._rag_tool(message)

        result["agent"] = self.name
        result["agent_version"] = self.version
        result["agentic"] = True
        result["disclaimer"] = (
            "Prototype AI-agent workflow. Verify current official BIS information, amendments, "
            "schemes and laboratory status before regulatory or certification decisions."
        )
        return result
