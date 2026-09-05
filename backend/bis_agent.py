"""BIS SmartGuide multilingual intelligence agent.

Dependency-free tool-routing agent for the SIH prototype. It detects the
script/language of the user's message and localizes the generated response
while keeping BIS standard numbers, product names and official URLs intact.
"""

import re


class BISExpertAgent:
    name = "BIS Standards Intelligence Agent"
    version = "2.1"

    LANGUAGES = {
        "te": "Telugu",
        "hi": "Hindi",
        "kn": "Kannada",
        "ta": "Tamil",
        "en": "English",
    }

    # Fixed UI phrases are translated locally so the agent remains
    # dependency-free and does not require an external translation API/key.
    T = {
        "te": {
            "best": "ఉత్తమ జ్ఞాన-ఆధారిత సరిపోలిక",
            "key": "ముఖ్యమైన అవసరాల విభాగాలు",
            "scheme": "స్కీమ్",
            "prototype": "ఇది ప్రోటోటైప్ సిఫార్సు. ప్రస్తుత BIS ప్రమాణం, సవరణలు, QCOలు మరియు ఉత్పత్తి పరిధిని అధికారిక BIS వనరులో ధృవీకరించండి.",
            "mandatory": "తప్పనిసరి సర్టిఫికేషన్ అంచనా",
            "likely": "తప్పనిసరి స్కీమ్ పరిధిలో ఉండే అవకాశం ఉంది",
            "verify": "అధికారిక ధృవీకరణ అవసరం",
            "confirm": "స్థానిక రికార్డు ఈ స్కీమ్‌ను సూచిస్తోంది. ఈ స్థితిపై ఆధారపడే ముందు ప్రస్తుత BIS నోటిఫికేషన్ మరియు ఉత్పత్తి పరిధిని ధృవీకరించండి.",
            "not_enough": "ఉత్పత్తి తప్పనిసరిగా లేదా స్వచ్ఛందంగా ఉందని ప్రకటించడానికి స్థానిక ప్రోటోటైప్ రికార్డులో తగిన QCO సమాచారం లేదు.",
            "workflow": "BIS సర్టిఫికేషన్ కోసం ఉన్నత-స్థాయి ప్రక్రియ",
            "labs": "ప్రస్తుత పరీక్షా ప్రయోగశాలల కోసం అధికారిక BIS గుర్తింపు పొందిన ప్రయోగశాల డైరెక్టరీ మరియు BIS LIMS ఉపయోగించండి. SmartGuide ప్రయోగశాల లభ్యత లేదా గుర్తింపు స్థితిని ఊహించి చెప్పదు.",
            "compliance_prompt": "ఉత్పత్తి పేరు చెప్పండి; దాని ప్రోటోటైప్ కంప్లయన్స్ చెక్‌లిస్ట్‌ను చూపించగలను.",
            "disclaimer": "ప్రోటోటైప్ AI-ఏజెంట్ వర్క్‌ఫ్లో. నియంత్రణ లేదా సర్టిఫికేషన్ నిర్ణయాలకు ముందు ప్రస్తుత అధికారిక BIS సమాచారం, సవరణలు, QCOలు, స్కీమ్‌లు మరియు ప్రయోగశాల స్థితిని ధృవీకరించండి.",
        },
        "hi": {
            "best": "सर्वोत्तम ज्ञान-आधारित मिलान",
            "key": "मुख्य आवश्यकताएँ",
            "scheme": "स्कीम",
            "prototype": "यह एक प्रोटोटाइप अनुशंसा है। वर्तमान BIS मानक, संशोधन, QCO और उत्पाद का दायरा आधिकारिक BIS स्रोत से सत्यापित करें।",
            "mandatory": "अनिवार्य प्रमाणन आकलन",
            "likely": "अनिवार्य स्कीम के अंतर्गत होने की संभावना",
            "verify": "आधिकारिक सत्यापन आवश्यक",
            "confirm": "स्थानीय रिकॉर्ड इस स्कीम की पहचान करता है। इस स्थिति पर निर्भर करने से पहले वर्तमान BIS अधिसूचना और उत्पाद का दायरा सत्यापित करें।",
            "not_enough": "उत्पाद को अनिवार्य या स्वैच्छिक घोषित करने के लिए स्थानीय प्रोटोटाइप रिकॉर्ड में पर्याप्त QCO जानकारी नहीं है।",
            "workflow": "BIS प्रमाणन की उच्च-स्तरीय प्रक्रिया",
            "labs": "वर्तमान परीक्षण प्रयोगशालाओं के लिए आधिकारिक BIS मान्यता प्राप्त प्रयोगशाला निर्देशिका और BIS LIMS का उपयोग करें। SmartGuide प्रयोगशाला उपलब्धता या मान्यता स्थिति का अनुमान नहीं लगाता।",
            "compliance_prompt": "उत्पाद का नाम बताएं और मैं उसका प्रोटोटाइप अनुपालन चेकलिस्ट दिखा सकता हूँ।",
            "disclaimer": "प्रोटोटाइप AI-एजेंट वर्कफ़्लो। नियामक या प्रमाणन निर्णयों से पहले वर्तमान आधिकारिक BIS जानकारी, संशोधन, QCO, स्कीम और प्रयोगशाला स्थिति सत्यापित करें।",
        },
        "kn": {
            "best": "ಅತ್ಯುತ್ತಮ ಜ್ಞಾನ-ಆಧಾರಿತ ಹೊಂದಾಣಿಕೆ",
            "key": "ಪ್ರಮುಖ ಅವಶ್ಯಕತೆ ವಿಭಾಗಗಳು",
            "scheme": "ಸ್ಕೀಮ್",
            "prototype": "ಇದು ಪ್ರೋಟೋಟೈಪ್ ಶಿಫಾರಸು. ಪ್ರಸ್ತುತ BIS ಮಾನದಂಡ, ತಿದ್ದುಪಡಿಗಳು, QCOಗಳು ಮತ್ತು ಉತ್ಪನ್ನದ ವ್ಯಾಪ್ತಿಯನ್ನು ಅಧಿಕೃತ BIS ಮೂಲದಲ್ಲಿ ಪರಿಶೀಲಿಸಿ.",
            "mandatory": "ಕಡ್ಡಾಯ ಪ್ರಮಾಣೀಕರಣ ಮೌಲ್ಯಮಾಪನ",
            "likely": "ಕಡ್ಡಾಯ ಸ್ಕೀಮ್ ವ್ಯಾಪ್ತಿಯಲ್ಲಿ ಇರುವ ಸಾಧ್ಯತೆ ಇದೆ",
            "verify": "ಅಧಿಕೃತ ಪರಿಶೀಲನೆ ಅಗತ್ಯ",
            "confirm": "ಸ್ಥಳೀಯ ದಾಖಲೆ ಈ ಸ್ಕೀಮ್ ಅನ್ನು ಸೂಚಿಸುತ್ತದೆ. ಇದನ್ನು ಅವಲಂಬಿಸುವ ಮೊದಲು ಪ್ರಸ್ತುತ BIS ಅಧಿಸೂಚನೆ ಮತ್ತು ಉತ್ಪನ್ನದ ವ್ಯಾಪ್ತಿಯನ್ನು ಪರಿಶೀಲಿಸಿ.",
            "not_enough": "ಉತ್ಪನ್ನ ಕಡ್ಡಾಯವೇ ಅಥವಾ ಸ್ವಯಂಪ್ರೇರಿತವೇ ಎಂದು ಘೋಷಿಸಲು ಸ್ಥಳೀಯ ಪ್ರೋಟೋಟೈಪ್ ದಾಖಲೆಯಲ್ಲಿ ಸಾಕಷ್ಟು QCO ಮಾಹಿತಿ ಇಲ್ಲ.",
            "workflow": "BIS ಪ್ರಮಾಣೀಕರಣದ ಉನ್ನತ-ಮಟ್ಟದ ಪ್ರಕ್ರಿಯೆ",
            "labs": "ಪ್ರಸ್ತುತ ಪರೀಕ್ಷಾ ಪ್ರಯೋಗಾಲಯಗಳಿಗಾಗಿ ಅಧಿಕೃತ BIS ಮಾನ್ಯತೆ ಪಡೆದ ಪ್ರಯೋಗಾಲಯ ಡೈರೆಕ್ಟರಿ ಮತ್ತು BIS LIMS ಬಳಸಿ. SmartGuide ಪ್ರಯೋಗಾಲಯ ಲಭ್ಯತೆ ಅಥವಾ ಮಾನ್ಯತೆಯನ್ನು ಊಹಿಸುವುದಿಲ್ಲ.",
            "compliance_prompt": "ಉತ್ಪನ್ನದ ಹೆಸರನ್ನು ತಿಳಿಸಿ; ಅದರ ಪ್ರೋಟೋಟೈಪ್ ಅನುಸರಣೆ ಚೆಕ್‌ಲಿಸ್ಟ್ ಅನ್ನು ತೋರಿಸಬಹುದು.",
            "disclaimer": "ಪ್ರೋಟೋಟೈಪ್ AI-ಏಜೆಂಟ್ ವರ್ಕ್‌ಫ್ಲೋ. ನಿಯಂತ್ರಣ ಅಥವಾ ಪ್ರಮಾಣೀಕರಣ ನಿರ್ಧಾರಗಳ ಮೊದಲು ಪ್ರಸ್ತುತ ಅಧಿಕೃತ BIS ಮಾಹಿತಿ, ತಿದ್ದುಪಡಿಗಳು, QCOಗಳು, ಸ್ಕೀಮ್‌ಗಳು ಮತ್ತು ಪ್ರಯೋಗಾಲಯ ಸ್ಥಿತಿಯನ್ನು ಪರಿಶೀಲಿಸಿ.",
        },
        "ta": {
            "best": "சிறந்த அறிவுத்தள பொருத்தம்",
            "key": "முக்கிய தேவைகள்",
            "scheme": "திட்டம்",
            "prototype": "இது ஒரு முன்மாதிரி பரிந்துரை. தற்போதைய BIS தரநிலை, திருத்தங்கள், QCOகள் மற்றும் தயாரிப்பு வரம்பை அதிகாரப்பூர்வ BIS மூலத்தில் சரிபார்க்கவும்.",
            "mandatory": "கட்டாய சான்றிதழ் மதிப்பீடு",
            "likely": "கட்டாய திட்டத்தின் கீழ் இருக்கக்கூடும்",
            "verify": "அதிகாரப்பூர்வ சரிபார்ப்பு தேவை",
            "confirm": "உள்ளூர் பதிவு இந்த திட்டத்தை குறிப்பிடுகிறது. இதை நம்புவதற்கு முன் தற்போதைய BIS அறிவிப்பு மற்றும் தயாரிப்பு வரம்பை சரிபார்க்கவும்.",
            "not_enough": "தயாரிப்பு கட்டாயமா அல்லது தன்னார்வமா என்பதை அறிவிக்க உள்ளூர் முன்மாதிரி பதிவில் போதுமான QCO தகவல் இல்லை.",
            "workflow": "BIS சான்றிதழுக்கான உயர்நிலை செயல்முறை",
            "labs": "தற்போதைய சோதனை ஆய்வகங்களுக்கு அதிகாரப்பூர்வ BIS அங்கீகரிக்கப்பட்ட ஆய்வக அடைவு மற்றும் BIS LIMS-ஐ பயன்படுத்தவும். SmartGuide ஆய்வக கிடைப்பை அல்லது அங்கீகார நிலையை ஊகிக்காது.",
            "compliance_prompt": "தயாரிப்பு பெயரைச் சொல்லுங்கள்; அதன் முன்மாதிரி இணக்கச் சரிபார்ப்புப் பட்டியலைக் காட்ட முடியும்.",
            "disclaimer": "முன்மாதிரி AI-ஏஜென்ட் பணிப்பாய்வு. ஒழுங்குமுறை அல்லது சான்றிதழ் முடிவுகளுக்கு முன் தற்போதைய அதிகாரப்பூர்வ BIS தகவல், திருத்தங்கள், QCOகள், திட்டங்கள் மற்றும் ஆய்வக நிலையை சரிபார்க்கவும்.",
        },
    }

    def __init__(self, find_matches, rag, resources, certification_steps, compliance_checker=None):
        self.find_matches = find_matches
        self.rag = rag
        self.resources = resources
        self.certification_steps = certification_steps
        self.compliance_checker = compliance_checker

    @staticmethod
    def _normalize(text):
        return " ".join(str(text or "").lower().split())

    @classmethod
    def detect_language(cls, text):
        """Detect supported language primarily from Unicode script ranges."""
        text = str(text or "")
        if re.search(r"[\u0C00-\u0C7F]", text):
            return "te"
        if re.search(r"[\u0900-\u097F]", text):
            return "hi"
        if re.search(r"[\u0C80-\u0CFF]", text):
            return "kn"
        if re.search(r"[\u0B80-\u0BFF]", text):
            return "ta"
        return "en"

    def _t(self, lang, key):
        return self.T.get(lang, {}).get(key, {
            "best": "Best knowledge-base match",
            "key": "Key requirement areas",
            "scheme": "Scheme",
            "prototype": "This is a prototype recommendation; verify the current BIS standard, amendments, QCOs and scope.",
            "mandatory": "Mandatory-certification assessment",
            "likely": "LIKELY WITHIN A COMPULSORY SCHEME",
            "verify": "NEEDS OFFICIAL VERIFICATION",
            "confirm": "The local record identifies this scheme. Confirm the current notification and product scope on BIS before relying on this status.",
            "not_enough": "The local prototype record does not contain enough verified QCO data to declare the product mandatory or voluntary.",
            "workflow": "High-level BIS certification workflow",
            "labs": "For current testing laboratories, use the official BIS recognized laboratory directory and BIS LIMS. SmartGuide does not invent laboratory availability or accreditation status.",
            "compliance_prompt": "Tell me the product name and I can load its prototype compliance checklist.",
            "disclaimer": "Prototype AI-agent workflow. Verify current official BIS information, amendments, QCOs, schemes and laboratory status before regulatory or certification decisions.",
        }[key])

    @staticmethod
    def _translate_requirement(text, lang):
        """Translate common prototype requirement labels; leave unknown technical text intact."""
        maps = {
            "te": {
                "Electrical and safety requirements": "విద్యుత్ మరియు భద్రతా అవసరాలు",
                "Protection against fire hazards": "అగ్ని ప్రమాదాల నుండి రక్షణ",
                "Requirements for external circuits": "బాహ్య సర్క్యూట్ల అవసరాలు",
                "Battery charging safety": "బ్యాటరీ ఛార్జింగ్ భద్రత",
                "Electrical safety": "విద్యుత్ భద్రత",
                "Insulation safety": "ఇన్సులేషన్ భద్రత",
                "Mechanical safety": "యాంత్రిక భద్రత",
                "Temperature safety": "ఉష్ణోగ్రత భద్రత",
            },
            "hi": {
                "Electrical and safety requirements": "विद्युत और सुरक्षा आवश्यकताएँ",
                "Protection against fire hazards": "आग के खतरों से सुरक्षा",
                "Requirements for external circuits": "बाहरी सर्किट की आवश्यकताएँ",
                "Battery charging safety": "बैटरी चार्जिंग सुरक्षा",
                "Electrical safety": "विद्युत सुरक्षा",
                "Insulation safety": "इन्सुलेशन सुरक्षा",
                "Mechanical safety": "यांत्रिक सुरक्षा",
                "Temperature safety": "तापमान सुरक्षा",
            },
            "kn": {
                "Electrical and safety requirements": "ವಿದ್ಯುತ್ ಮತ್ತು ಸುರಕ್ಷತಾ ಅವಶ್ಯಕತೆಗಳು",
                "Protection against fire hazards": "ಅಗ್ನಿ ಅಪಾಯಗಳಿಂದ ರಕ್ಷಣೆ",
                "Requirements for external circuits": "ಬಾಹ್ಯ ಸರ್ಕ್ಯೂಟ್‌ಗಳ ಅವಶ್ಯಕತೆಗಳು",
                "Battery charging safety": "ಬ್ಯಾಟರಿ ಚಾರ್ಜಿಂಗ್ ಸುರಕ್ಷತೆ",
                "Electrical safety": "ವಿದ್ಯುತ್ ಸುರಕ್ಷತೆ",
                "Insulation safety": "ಇನ್ಸುಲೇಷನ್ ಸುರಕ್ಷತೆ",
                "Mechanical safety": "ಯಾಂತ್ರಿಕ ಸುರಕ್ಷತೆ",
                "Temperature safety": "ತಾಪಮಾನ ಸುರಕ್ಷತೆ",
            },
            "ta": {
                "Electrical and safety requirements": "மின்சார மற்றும் பாதுகாப்புத் தேவைகள்",
                "Protection against fire hazards": "தீ அபாயங்களுக்கு எதிரான பாதுகாப்பு",
                "Requirements for external circuits": "வெளிப்புற சுற்றுகளுக்கான தேவைகள்",
                "Battery charging safety": "பேட்டரி சார்ஜிங் பாதுகாப்பு",
                "Electrical safety": "மின்சார பாதுகாப்பு",
                "Insulation safety": "இன்சுலேஷன் பாதுகாப்பு",
                "Mechanical safety": "இயந்திர பாதுகாப்பு",
                "Temperature safety": "வெப்பநிலை பாதுகாப்பு",
            },
        }
        return maps.get(lang, {}).get(text, text)

    def _standard_tool(self, message, lang):
        matches = self.find_matches(message, 5)
        if not matches:
            return None
        top = matches[0]
        requirements = top.get("requirements", [])
        reqs = "\n".join(f"• {self._translate_requirement(x, lang)}" for x in requirements) or "No prototype checklist items are listed."
        if lang == "en":
            reply = (f"Best knowledge-base match: {top.get('standard_number')} — {top.get('title')}.\n\n"
                     f"{top.get('description','')}\n\nKey requirement areas:\n{reqs}\n\n"
                     f"Scheme: {top.get('scheme','Not specified in the local record')}\n{self._t(lang,'prototype')}")
        else:
            reply = (f"{self._t(lang,'best')}: {top.get('standard_number')} — {top.get('title')}.\n\n"
                     f"{top.get('description','')}\n\n{self._t(lang,'key')}:\n{reqs}\n\n"
                     f"{self._t(lang,'scheme')}: {top.get('scheme','Not specified in the local record')}\n{self._t(lang,'prototype')}")
        return {"reply": reply, "intent": "standard_search", "tool": "BIS Standard Finder", "recommendations": matches,
                "sources": [top.get("official_source") or self.resources[0]["url"]]}

    def _certification_tool(self, message, lang):
        matches = self.find_matches(message, 1)
        standard = matches[0] if matches else None
        steps = self.certification_steps(standard)
        if lang == "en":
            reply = "High-level BIS certification workflow:\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
        else:
            # Preserve the precise step content rather than pretending an
            # unverified technical translation is official.
            reply = self._t(lang, "workflow") + ":\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
        return {"reply": reply, "intent": "certification", "tool": "BIS Certification Guide", "recommendations": matches,
                "sources": [self.resources[1]["url"], self.resources[2]["url"]]}

    def _mandatory_tool(self, message, lang):
        matches = self.find_matches(message, 1)
        standard = matches[0] if matches else None
        if standard and standard.get("scheme"):
            status = self._t(lang, "likely")
            explanation = self._t(lang, "confirm")
        else:
            status = self._t(lang, "verify")
            explanation = self._t(lang, "not_enough")
        return {"reply": f"{self._t(lang,'mandatory')}: {status}.\n\n{explanation}", "intent": "mandatory_check",
                "tool": "BIS Mandatory Certification Checker", "recommendations": matches,
                "sources": [self.resources[0]["url"], self.resources[1]["url"]]}

    def _laboratory_tool(self, message, lang):
        return {"reply": self._t(lang, "labs"), "intent": "laboratory", "tool": "BIS Laboratory Guide", "recommendations": [],
                "sources": [self.resources[3]["url"], self.resources[4]["url"]]}

    def _compliance_tool(self, message, lang):
        if self.compliance_checker:
            data = self.compliance_checker(message)
            if data:
                return {"reply": data["reply"], "intent": "compliance", "tool": "BIS Compliance Engine", "recommendations": [data["standard"]], "sources": [data.get("source") or self.resources[0]["url"]]}
        return {"reply": self._t(lang, "compliance_prompt"), "intent": "compliance", "tool": "BIS Compliance Engine", "recommendations": [], "sources": []}

    def _rag_tool(self, message, lang):
        result = self.rag.answer(message, 5)
        reply = result["answer"]
        if lang != "en":
            reply = f"{reply}\n\n{self._t(lang, 'prototype')}"
        return {"reply": reply, "intent": "rag_knowledge", "tool": "Local BIS RAG", "recommendations": [],
                "sources": result.get("sources", []), "retrieved": result.get("retrieved", []), "retrieved_count": result.get("retrieved_count", 0)}

    def run(self, message):
        lang = self.detect_language(message)
        text = self._normalize(message)
        if any(x in text for x in ["mandatory", "compulsory", "qco", "isi mark required", "is certification required", "తప్పనిసరి", "కంపల్సరీ", "अनिवार्य", "कम्पल्सरी", "ಕಡ್ಡಾಯ", "கட்டாய"]):
            result = self._mandatory_tool(message, lang)
        elif any(x in text for x in ["compliance", "compliant", "checklist", "conformity", "requirement status", "కంప్లయన్స్", "अनुपालन", "ಅನುಸರಣೆ", "இணக்கம்"]):
            result = self._compliance_tool(message, lang)
        elif any(x in text for x in ["certification", "certificate", "license", "licence", "apply", "registration", "సర్టిఫికేషన్", "प्रमाणन", "ಪ್ರಮಾಣೀಕರಣ", "சான்றிதழ்"]):
            result = self._certification_tool(message, lang)
        elif any(x in text for x in ["lab", "laboratory", "testing lab", "test lab", "ల్యాబ్", "प्रयोगशाला", "ಲ್ಯಾಬ್", "ஆய்வகம்"]):
            result = self._laboratory_tool(message, lang)
        else:
            result = self._standard_tool(message, lang) or self._rag_tool(message, lang)
        result.update({"agent": self.name, "agent_version": self.version, "agentic": True,
                       "language": lang, "language_name": self.LANGUAGES[lang],
                       "disclaimer": self._t(lang, "disclaimer")})
        return result
