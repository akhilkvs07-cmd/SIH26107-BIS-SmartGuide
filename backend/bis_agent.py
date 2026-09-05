"""BIS SmartGuide intelligence agent.

Dependency-free tool-routing agent for the SIH prototype. It deliberately
prefers grounded local data and official BIS resources over invented answers.
"""

class BISExpertAgent:
    name = "BIS Standards Intelligence Agent"
    version = "2.0"

    def __init__(self, find_matches, rag, resources, certification_steps, compliance_checker=None):
        self.find_matches = find_matches
        self.rag = rag
        self.resources = resources
        self.certification_steps = certification_steps
        self.compliance_checker = compliance_checker

    @staticmethod
    def _normalize(text):
        return " ".join(str(text or "").lower().split())

    def _standard_tool(self, message):
        matches = self.find_matches(message, 5)
        if not matches:
            return None
        top = matches[0]
        requirements = top.get("requirements", [])
        reqs = "\n".join(f"• {x}" for x in requirements) or "No prototype checklist items are listed."
        reply = (f"Best knowledge-base match: {top.get('standard_number')} — {top.get('title')}.\n\n"
                 f"{top.get('description','')}\n\nKey requirement areas:\n{reqs}\n\n"
                 f"Scheme: {top.get('scheme','Not specified in the local record')}\n"
                 "This is a prototype recommendation; verify the current BIS standard, amendments, QCOs and scope.")
        return {"reply": reply, "intent": "standard_search", "tool": "BIS Standard Finder", "recommendations": matches,
                "sources": [top.get("official_source") or self.resources[0]["url"]]}

    def _certification_tool(self, message):
        matches = self.find_matches(message, 1)
        standard = matches[0] if matches else None
        steps = self.certification_steps(standard)
        reply = "High-level BIS certification workflow:\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
        return {"reply": reply, "intent": "certification", "tool": "BIS Certification Guide", "recommendations": matches,
                "sources": [self.resources[1]["url"], self.resources[2]["url"]]}

    def _mandatory_tool(self, message):
        matches = self.find_matches(message, 1)
        standard = matches[0] if matches else None
        if standard and standard.get("scheme"):
            status = "LIKELY WITHIN A COMPULSORY SCHEME"
            explanation = f"The local record identifies {standard['scheme']}. Confirm the current notification and product scope on BIS before relying on this status."
        else:
            status = "NEEDS OFFICIAL VERIFICATION"
            explanation = "The local prototype record does not contain enough verified QCO data to declare the product mandatory or voluntary."
        return {"reply": f"Mandatory-certification assessment: {status}.\n\n{explanation}", "intent": "mandatory_check",
                "tool": "BIS Mandatory Certification Checker", "recommendations": matches,
                "sources": [self.resources[0]["url"], self.resources[1]["url"]]}

    def _laboratory_tool(self, message):
        return {"reply": "For current testing laboratories, use the official BIS recognized laboratory directory and BIS LIMS. SmartGuide does not invent laboratory availability or accreditation status.",
                "intent": "laboratory", "tool": "BIS Laboratory Guide", "recommendations": [],
                "sources": [self.resources[3]["url"], self.resources[4]["url"]]}

    def _compliance_tool(self, message):
        if self.compliance_checker:
            data = self.compliance_checker(message)
            if data:
                return {"reply": data["reply"], "intent": "compliance", "tool": "BIS Compliance Engine", "recommendations": [data["standard"]], "sources": [data.get("source") or self.resources[0]["url"]]}
        return {"reply": "Tell me the product name and I can load its prototype compliance checklist.", "intent": "compliance", "tool": "BIS Compliance Engine", "recommendations": [], "sources": []}

    def _rag_tool(self, message):
        result = self.rag.answer(message, 5)
        return {"reply": result["answer"], "intent": "rag_knowledge", "tool": "Local BIS RAG", "recommendations": [],
                "sources": result.get("sources", []), "retrieved": result.get("retrieved", []), "retrieved_count": result.get("retrieved_count", 0)}

    def run(self, message):
        text = self._normalize(message)
        if any(x in text for x in ["mandatory", "compulsory", "qco", "isi mark required", "is certification required"]):
            result = self._mandatory_tool(message)
        elif any(x in text for x in ["compliance", "compliant", "checklist", "conformity", "requirement status"]):
            result = self._compliance_tool(message)
        elif any(x in text for x in ["certification", "certificate", "license", "licence", "apply", "registration"]):
            result = self._certification_tool(message)
        elif any(x in text for x in ["lab", "laboratory", "testing lab", "test lab"]):
            result = self._laboratory_tool(message)
        else:
            result = self._standard_tool(message) or self._rag_tool(message)
        result.update({"agent": self.name, "agent_version": self.version, "agentic": True,
                       "disclaimer": "Prototype AI-agent workflow. Verify current official BIS information, amendments, QCOs, schemes and laboratory status before regulatory or certification decisions."})
        return result
