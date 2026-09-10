"""BIS SmartGuide Multilingual & Role-Aware Intelligence Agent.

Supports:
- 5 Languages: English (en), Hindi (hi), Telugu (te), Kannada (kn), Tamil (ta)
- 8 User Roles: Manufacturer, Startup, Importer, Procurement, Consumer, Laboratory, Compliance, General
- Grounded evidence trail with confidence scoring and official BIS links
- Strict refusal boundaries when evidence is absent
"""

import re
from typing import Any, Dict, List, Optional
from role_engine import RoleEngine

class BISExpertAgent:
    name = "BIS Standards Intelligence Agent"
    version = "4.0"

    LANGUAGES = {
        "en": "English",
        "hi": "Hindi",
        "kn": "Kannada",
        "te": "Telugu",
        "ta": "Tamil"
    }

    T = {
        "en": {
            "best": "Best Knowledge-Base Match",
            "key": "Key Requirement Areas",
            "scheme": "Scheme",
            "prototype": "This is an AI-assisted recommendation. Verify the current BIS standard, amendments, QCOs and scope against official BIS sources.",
            "mandatory": "Mandatory Certification Assessment",
            "likely": "MANDATORY UNDER QUALITY CONTROL ORDER (QCO)",
            "verify": "NEEDS OFFICIAL GAZETTE VERIFICATION",
            "confirm": "Mandatory Quality Control Order applies to this product under BIS Scheme I / Scheme II.",
            "not_enough": "The local standard record does not contain an active mandatory QCO declaration. Verify current Central Government notifications.",
            "workflow": "High-Level BIS Certification Process",
            "labs": "For accredited testing laboratories, use the official BIS Recognized Laboratory Directory and BIS LIMS. SmartGuide does not invent laboratory availability or test reports.",
            "compliance_prompt": "Provide a product name or standard number to generate its compliance checklist.",
            "disclaimer": "AI-assisted screening only. Does not issue, verify, or grant BIS certification. Confirm all details on standards.bis.gov.in.",
            "refusal": "I could not find sufficient BIS evidence in the available standards repository to answer with certainty. SmartGuide will not invent or guess requirements.",
            "confidence_label": "Confidence",
            "evidence_trail": "Evidence Trail"
        },
        "hi": {
            "best": "सर्वोत्तम मानक मिलान",
            "key": "मुख्य तकनीकी आवश्यकताएँ",
            "scheme": "प्रमाणन स्कीम",
            "prototype": "यह एक AI-सहायक अनुशंसा है। अंतिम निर्णय से पहले आधिकारिक BIS पोर्टल पर वर्तमान मानक, संशोधन और QCO सत्यापित करें।",
            "mandatory": "अनिवार्य प्रमाणन आकलन",
            "likely": "गुणवत्ता नियंत्रण आदेश (QCO) के तहत अनिवार्य",
            "verify": "आधिकारिक राजपत्र सत्यापन आवश्यक",
            "confirm": "यह उत्पाद BIS स्कीम I / II के तहत अनिवार्य प्रमाणन के अंतर्गत आता है।",
            "not_enough": "स्थानीय रिकॉर्ड में अनिवार्य QCO की पुष्टि नहीं है। आधिकारिक BIS अधिसूचना जांचें।",
            "workflow": "BIS प्रमाणन की चरणबद्ध प्रक्रिया",
            "labs": "वर्तमान मान्यता प्राप्त प्रयोगशालाओं के लिए आधिकारिक BIS LIMS पोर्टल का उपयोग करें। SmartGuide प्रयोगशाला उपलब्धता का अनुमान नहीं लगाता।",
            "compliance_prompt": "अनुपालन चेकलिस्ट देखने के लिए उत्पाद का नाम या IS नंबर बताएं।",
            "disclaimer": "प्रोटोटाइप AI-मार्गदर्शन। आधिकारिक BIS प्रमाणन के लिए मानकों और QCO को bis.gov.in पर सत्यापित करें।",
            "refusal": "उपलब्ध BIS डेटाबेस में इस प्रश्न के लिए पर्याप्त प्रामाणिक साक्ष्य नहीं मिले। SmartGuide मनगढ़ंत जानकारी नहीं देता।",
            "confidence_label": "विश्वसनीयता",
            "evidence_trail": "साक्ष्य विवरण"
        },
        "kn": {
            "best": "ಅತ್ಯುತ್ತಮ ಮಾನದಂಡ ಹೊಂದಾಣಿಕೆ",
            "key": "ಪ್ರಮುಖ ತಾಂತ್ರಿಕ ಅವಶ್ಯಕತೆಗಳು",
            "scheme": "ಪ್ರಮಾಣೀಕರಣ ಸ್ಕೀಮ್",
            "prototype": "ಇದು AI-ನೆರವಿನ ಶಿಫಾರಸು. ಅಂತಿಮ ನಿರ್ಧಾರಕ್ಕೂ ಮುನ್ನ ಅಧಿಕೃತ BIS ಮೂಲದಲ್ಲಿ ಪ್ರಸ್ತುತ ಮಾನದಂಡ, ತಿದ್ದುಪಡಿಗಳು ಮತ್ತು QCO ಗಳನ್ನು ಪರಿಶೀಲಿಸಿ.",
            "mandatory": "ಕಡ್ಡಾಯ ಪ್ರಮಾಣೀಕರಣ ಮೌಲ್ಯಮಾಪನ",
            "likely": "ಗುಣಮಟ್ಟ ನಿಯಂತ್ರಣ ಆದೇಶದ (QCO) ಅಡಿಯಲ್ಲಿ ಕಡ್ಡಾಯ",
            "verify": "ಅಧಿಕೃತ ಪರಿಶೀಲನೆ ಅಗತ್ಯವಿದೆ",
            "confirm": "ಈ ಉತ್ಪನ್ನವು BIS ಸ್ಕೀಮ್ I / II ಅಡಿಯಲ್ಲಿ ಕಡ್ಡಾಯ ಪ್ರಮಾಣೀಕರಣಕ್ಕೆ ಒಳಪಟ್ಟಿರುತ್ತದೆ.",
            "not_enough": "ಸ್ಥಳೀಯ ದಾಖಲೆಯಲ್ಲಿ ಸಕ್ರಿಯ ಕಡ್ಡಾಯ QCO ಘೋಷಣೆ ಇಲ್ಲ. ಅಧಿಕೃತ BIS ಅಧಿಸೂಚನೆಗಳನ್ನು ಪರಿಶೀಲಿಸಿ.",
            "workflow": "BIS ಪ್ರಮಾಣೀಕರಣದ ಪ್ರಮುಖ ಪ್ರಕ್ರಿಯೆ",
            "labs": "ಮಾನ್ಯತೆ ಪಡೆದ ಪರೀಕ್ಷಾ ಪ್ರಯೋಗಾಲಯಗಳಿಗಾಗಿ ಅಧಿಕೃತ BIS LIMS ಪೋರ್ಟಲ್ ಬಳಸಿ.",
            "compliance_prompt": "ಅನುಸರಣೆ ಚೆಕ್‌ಲಿಸ್ಟ್ ಪಡೆಯಲು ಉತ್ಪನ್ನದ ಹೆಸರನ್ನು ನಮೂದಿಸಿ.",
            "disclaimer": "AI-ಸಹಾಯದ ಮಾರ್ಗದರ್ಶನ ಮಾತ್ರ. ಇದು ಅಧಿಕೃತ BIS ಪ್ರಮಾಣಪತ್ರವಲ್ಲ.",
            "refusal": "ಲಭ್ಯವಿರುವ BIS ಜ್ಞಾನಕೋಶದಲ್ಲಿ ಸಾಕಷ್ಟು ಪುರಾವೆಗಳು ಲಭ್ಯವಿಲ್ಲ. SmartGuide ಊಹಾಪೋಹದ ಮಾಹಿತಿ ನೀಡುವುದಿಲ್ಲ.",
            "confidence_label": "ವಿಶ್ವಾಸಾರ್ಹತೆ",
            "evidence_trail": "ಪುರಾವೆ ವಿವರ"
        },
        "te": {
            "best": "ఉత్తమ ప్రమాణాల సరిపోలిక",
            "key": "ముఖ్యమైన సాంకేతిక అవసరాలు",
            "scheme": "సర్టిఫికేషన్ స్కీమ్",
            "prototype": "ఇది AI-ఆధారిత సిఫార్సు. అధికారిక BIS పోర్టల్ ద్వారా ప్రస్తుత ప్రమాణం, సవరణలు మరియు QCOలను ధృవీకరించండి.",
            "mandatory": "తప్పనిసరి సర్టిఫికేషన్ అంచనా",
            "likely": "క్వాలిటీ కంట్రోల్ ఆర్డర్ (QCO) కింద తప్పనిసరి",
            "verify": "అధికారిక గెజిట్ ధృవీకరణ అవసరం",
            "confirm": "ఈ ఉత్పత్తి BIS స్కీమ్ I లేదా II కింద తప్పనిసరి సర్టిఫికేషన్ పరిధిలోకి వస్తుంది.",
            "not_enough": "స్థానిక రికార్డులో తగిన QCO సమాచారం లేదు. అధికారిక నోటిఫికేషన్లు చూడండి.",
            "workflow": "BIS సర్టిఫికేషన్ దశల ప్రక్రియ",
            "labs": "పరీక్షా ప్రయోగశాలల వివరాల కోసం అధికారిక BIS LIMS ఉపయోగించండి. SmartGuide సమాచారాన్ని ఊహించదు.",
            "compliance_prompt": "కంప్లయన్స్ చెక్‌లిస్ట్ కోసం ఉత్పత్తి పేరు తెలపండి.",
            "disclaimer": "AI-సహాయక మార్గదర్శకత్వం మాత్రమే. ఇది అధికారిక సర్టిఫికేషన్ కాదు.",
            "refusal": "సరైన BIS ఆధారాలు లభించలేదు. SmartGuide అసంబద్ధమైన సమాధానాలు ఇవ్వదు.",
            "confidence_label": "విశ్వసనీయత",
            "evidence_trail": "ఆధారాల వివరాలు"
        },
        "ta": {
            "best": "சிறந்த தரநிலை பொருத்தம்",
            "key": "முக்கிய தொழில்நுட்ப தேவைகள்",
            "scheme": "சான்றிதழ் திட்டம்",
            "prototype": "இது AI-வழிகாட்டுதல் பரிந்துரை. அதிகாரப்பூர்வ BIS போர்ட்டலில் தற்போதைய தரநிலை மற்றும் QCO விவரங்களை சரிபார்க்கவும்.",
            "mandatory": "கட்டாய சான்றிதழ் மதிப்பீடு",
            "likely": "தரக் கட்டுப்பாட்டு உத்தரவின் (QCO) கீழ் கட்டாயமானது",
            "verify": "அதிகாரப்பூர்வ சரிபார்ப்பு தேவை",
            "confirm": "இந்த தயாரிப்பு BIS திட்டம் I / II இன் கீழ் கட்டாய சான்றிதழிற்கு உட்பட்டது.",
            "not_enough": "உள்ளூர் பதிவில் கட்டாய QCO விவரம் இல்லை. அதிகாரப்பூர்வ அறிவிப்பை சரிபார்க்கவும்.",
            "workflow": "BIS சான்றிதழ் பெறுவதற்கான படிநிலைகள்",
            "labs": "அங்கீகரிக்கப்பட்ட சோதனை ஆய்வகங்களுக்கு அதிகாரப்பூர்வ BIS LIMS போர்ட்டலை பயன்படுத்தவும்.",
            "compliance_prompt": "இணக்கப் பட்டியலைக் காண தயாரிப்பு பெயரை உள்ளிடவும்.",
            "disclaimer": "AI-உதவி வழிகாட்டுதல் மட்டுமே. இது அதிகாரப்பூர்வ BIS சான்றிதழ் அல்ல.",
            "refusal": "போதுமான BIS சான்றுகள் கிடைக்கவில்லை. SmartGuide தவறான தகவல்களை உருவாக்காது.",
            "confidence_label": "நம்பகத்தன்மை",
            "evidence_trail": "சான்றுகள்"
        }
    }

    def __init__(self, find_matches, rag, resources, certification_steps, compliance_checker=None):
        self.find_matches = find_matches
        self.rag = rag
        self.resources = resources
        self.certification_steps = certification_steps
        self.compliance_checker = compliance_checker
        self.conversation_memory = []

    @staticmethod
    def _normalize(text: Any) -> str:
        return " ".join(str(text or "").lower().split())

    @classmethod
    def detect_language(cls, text: str) -> str:
        s = str(text or "")
        if re.search(r"[\u0C00-\u0C7F]", s):
            return "te"
        if re.search(r"[\u0900-\u097F]", s):
            return "hi"
        if re.search(r"[\u0C80-\u0CFF]", s):
            return "kn"
        if re.search(r"[\u0B80-\u0BFF]", s):
            return "ta"
        return "en"

    def _t(self, lang: str, key: str) -> str:
        return self.T.get(lang, self.T["en"]).get(key, self.T["en"].get(key, ""))

    def _role_prefix(self, role_id: str) -> str:
        role = RoleEngine.get_role(role_id)
        return role.get("agent_system_prefix", "")

    def run(self, message: str, role: str = "general", language: Optional[str] = None) -> Dict[str, Any]:
        raw_msg = str(message or "").strip()
        lang = language if language in self.LANGUAGES else self.detect_language(raw_msg)
        text = self._normalize(raw_msg)
        role_cfg = RoleEngine.get_role(role)

        self.conversation_memory.append({"user": raw_msg, "role": role})
        self.conversation_memory = self.conversation_memory[-10:]

        social = self._check_social(text, lang)
        if social:
            return social

        if any(x in text for x in ["mandatory", "compulsory", "qco", "isi mark required", "is certification required", "తప్పనిసరి", "కంపల్సరీ", "अनिवार्य", "कम्पल्सरी", "ಕಡ್ಡಾಯ", "கட்டாய"]):
            result = self._mandatory_tool(raw_msg, lang, role_cfg)
        elif any(x in text for x in ["compliance", "compliant", "checklist", "conformity", "requirement status", "కంప్లయన్స్", "अनुपालन", "ಅನುಸರಣೆ", "இணக்கம்"]):
            result = self._compliance_tool(raw_msg, lang, role_cfg)
        elif any(x in text for x in ["certification", "certificate", "license", "licence", "apply", "registration", "సర్టిఫికేషన్", "प्रमाणन", "ಪ್ರಮಾಣೀಕರಣ", "சான்றிதழ்"]):
            result = self._certification_tool(raw_msg, lang, role_cfg)
        elif any(x in text for x in ["lab", "laboratory", "testing lab", "test lab", "ల్యాబ్", "प्रयोगशाला", "ಲ್ಯಾಬ್", "ஆய்வகம்"]):
            result = self._laboratory_tool(raw_msg, lang, role_cfg)
        else:
            result = self._standard_tool(raw_msg, lang, role_cfg) or self._rag_tool(raw_msg, lang, role_cfg)

        result.update({
            "agent": self.name,
            "agent_version": self.version,
            "agentic": True,
            "language": lang,
            "language_name": self.LANGUAGES[lang],
            "role": role_cfg["id"],
            "role_title": role_cfg["title"],
            "disclaimer": self._t(lang, "disclaimer")
        })
        return result

    def _check_social(self, text: str, lang: str) -> Optional[Dict[str, Any]]:
        greetings = {"hi", "hello", "hey", "namaste", "namaskar", "నమస్తే", "నమస్కారం", "नमस्ते", "नमस्कार", "ನಮಸ್ಕಾರ", "வணக்கம்"}
        thanks = {"thanks", "thank you", "thankyou", "ధన్యవాదాలు", "धन्यवाद", "ಧನ್ಯವಾದ", "நன்றி"}
        byes = {"bye", "goodbye", "good bye", "see you", "వీడ్కోలు", "अलविदा", "ವಿದಾಯ", "விடைபெறுகிறேன்"}

        words = set(text.split())
        is_greeting = bool(words.intersection(greetings)) or text in greetings
        is_thanks = bool(words.intersection(thanks)) or text in thanks
        is_bye = bool(words.intersection(byes)) or text in byes

        if not (is_greeting or is_thanks or is_bye):
            return None

        replies = {
            "en": {
                "greeting": "Hello! 👋 I am the BIS Standards Intelligence Assistant. I can help with Indian Standards, mandatory QCOs, compliance checklists, testing laboratories and certification roadmaps. Which product would you like to evaluate?",
                "thanks": "You’re welcome! I’m here whenever you need verified guidance on Indian Standards and BIS compliance.",
                "bye": "Goodbye! Have a productive and compliant day."
            },
            "hi": {
                "greeting": "नमस्ते! 👋 मैं BIS मानक आसूचना सहायक हूँ। मैं भारतीय मानकों (IS), अनिवार्य QCOs, अनुपालन और प्रयोगशालाओं में आपकी मदद कर सकता हूँ। आप किस उत्पाद की जांच करना चाहते हैं?",
                "thanks": "आपका बहुत धन्यवाद! BIS मानकों पर सहायता के लिए मैं सदैव उपलब्ध हूँ।",
                "bye": "अलविदा! फिर मिलेंगे।"
            },
            "te": {
                "greeting": "నమస్కారం! 👋 నేను BIS స్టాండర్డ్స్ ఇంటెలిజెన్స్ అసిస్టెంట్. BIS ప్రమాణాలు, తప్పనిసరి QCOలు మరియు పరీక్షా ల్యాబ్‌ల సమాచారంలో సహాయపడగలను. మీరు ఏ ఉత్పత్తిని పరీక్షించాలనుకుంటున్నారు?",
                "thanks": "ధన్యవాదాలు! BIS సహాయం కోసం ఎప్పుడైనా అడగండి.",
                "bye": "వీడ్కోలు! మళ్లీ రండి."
            },
            "kn": {
                "greeting": "ನಮಸ್ಕಾರ! 👋 ನಾನು BIS ಸ್ಟ್ಯಾಂಡರ್ಡ್ಸ್ ಇಂಟೆಲಿಜೆನ್ಸ್ ಅಸಿಸ್ಟೆಂಟ್. BIS ಮಾನದಂಡಗಳು, ಕಡ್ಡಾಯ QCOಗಳು ಮತ್ತು ಪ್ರಯೋಗಾಲಯಗಳ ಬಗ್ಗೆ ಮಾಹಿತಿ ನೀಡಬಲ್ಲೆ. ನೀವು ಯಾವ ಉತ್ಪನ್ನವನ್ನು ಪರಿಶೀಲಿಸಲು ಬಯಸುತ್ತೀರಿ?",
                "thanks": "ಧನ್ಯವಾದಗಳು! BIS ಸಹಾಯಕ್ಕಾಗಿ ಯಾವಾಗಲೂ ಸಂಪರ್ಕಿಸಿ.",
                "bye": "ವಿದಾಯ! ಮತ್ತೆ ಭೇಟಿಯಾಗೋಣ."
            },
            "ta": {
                "greeting": "வணக்கம்! 👋 நான் BIS தரநிலைகள் நுண்ணறிவு உதவியாளர். இந்திய தரநிலைகள் (IS), கட்டாய QCOகள் மற்றும் ஆய்வக வழிகாட்டுதலில் உதவ முடியும். எந்த தயாரிப்பை ஆராய விரும்புகிறீர்கள்?",
                "thanks": "நன்றி! BIS தகவல்களுக்கு எப்போதும் கேளுங்கள்.",
                "bye": "விடைபெறுகிறேன்! மீண்டும் வாருங்கள்."
            }
        }
        kind = "greeting" if is_greeting else ("thanks" if is_thanks else "bye")
        return {
            "reply": replies.get(lang, replies["en"])[kind],
            "intent": "conversation",
            "tool": "Conversation Router",
            "recommendations": [],
            "sources": [],
            "confidence": 1.0,
            "support_level": "conversation"
        }

    def _standard_tool(self, message: str, lang: str, role: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        matches = self.find_matches(message, 5)
        if not matches:
            return None
        top = matches[0]
        reqs = top.get("requirements", [])
        bullet = "\n• "
        req_lines = ("• " + bullet.join(reqs[:5])) if reqs else "General safety requirements apply."

        std_num = top.get("standard_number", "")
        title = top.get("title", "")
        scheme = top.get("scheme", "Scheme I (ISI Mark)")
        qco = top.get("qco_order", "Subject to official notification")

        role_note = f"\n\n[{role['title']} Focus]: {role['product_perspective']}"

        reply = (
            f"{self._t(lang, 'best')}: **{std_num}** — *{title}*\n\n"
            f"{top.get('description', '')}\n\n"
            f"**{self._t(lang, 'key')}**:\n{req_lines}\n\n"
            f"**{self._t(lang, 'scheme')}**: {scheme}\n"
            f"**QCO Status**: {top.get('mandatory_status', 'MANDATORY')} ({qco})"
            f"{role_note}\n\n"
            f"{self._t(lang, 'prototype')}"
        )

        sources = [
            {"title": f"{std_num} — {title}", "url": top.get("official_source") or "https://standards.bis.gov.in/", "authority": "BIS Portal Record", "support_level": "authoritative_standard"}
        ]
        return {
            "reply": reply,
            "intent": "standards_search",
            "tool": "BIS Standard Finder",
            "recommendations": matches,
            "confidence": round(min(0.98, top.get("match_score", 85) / 100.0), 2),
            "sources": sources,
            "support_level": "evidence_grounded"
        }

    def _mandatory_tool(self, message: str, lang: str, role: Dict[str, Any]) -> Dict[str, Any]:
        matches = self.find_matches(message, 1)
        top = matches[0] if matches else None
        if top and top.get("mandatory_status") == "MANDATORY":
            status = self._t(lang, "likely")
            order = top.get("qco_order", "Central Government Quality Control Order")
            eff = top.get("effective_date", "In effect")
            reply = (
                f"**{self._t(lang, 'mandatory')}**: {status}\n\n"
                f"**Product**: {top.get('product')}\n"
                f"**Governing Standard**: {top.get('standard_number')}\n"
                f"**Order Reference**: {order}\n"
                f"**Effective Date**: {eff}\n\n"
                f"{self._t(lang, 'confirm')}\n\n"
                f"[{role['title']} Advisory]: Under the BIS Act 2016, manufacturing, importing, stocking or selling goods under mandatory QCO without valid BIS certification or registration attracts statutory penal action."
            )
            confidence = 0.95
        else:
            status = self._t(lang, "verify")
            reply = (
                f"**{self._t(lang, 'mandatory')}**: {status}\n\n"
                f"{self._t(lang, 'not_enough')}\n\n"
                f"[{role['title']} Action]: Consult the official BIS Compulsory Certification Directory before proceeding."
            )
            confidence = 0.60

        return {
            "reply": reply,
            "intent": "mandatory_check",
            "tool": "BIS Mandatory Certification Checker",
            "recommendations": matches,
            "confidence": confidence,
            "sources": [{"title": "BIS Compulsory Certification Directory", "url": "https://www.bis.gov.in/product-certification/products-under-compulsory-certification/?lang=en", "authority": "Official BIS Notification", "support_level": "official_directory"}],
            "support_level": "evidence_grounded"
        }

    def _certification_tool(self, message: str, lang: str, role: Dict[str, Any]) -> Dict[str, Any]:
        matches = self.find_matches(message, 1)
        top = matches[0] if matches else None
        steps = self.certification_steps(top)

        role_steps = [f"{i+1}. {s}" for i, s in enumerate(steps)]
        if role["id"] == "startup":
            role_steps.append("8. Apply for DPIIT 50% fee concession on application and inspection fees.")
        elif role["id"] == "importer":
            role_steps.append("8. Appoint an Authorized Indian Representative (AIR) under FMCS Scheme IV.")
        elif role["id"] == "procurement":
            role_steps.append("8. Request and independently audit the supplier's active CM/L endorsement scope.")

        newline = "\n"
        reply = (
            f"**{self._t(lang, 'workflow')}** for {top.get('product', 'the product') if top else 'general products'}:\n\n"
            f"{newline.join(role_steps)}\n\n"
            f"[{role['title']} Note]: {role['product_perspective']}\n\n"
            f"{self._t(lang, 'prototype')}"
        )
        return {
            "reply": reply,
            "intent": "certification",
            "tool": "BIS Certification Guide",
            "recommendations": matches,
            "confidence": 0.90,
            "sources": [{"title": "BIS Licensing Guidance Portal", "url": "https://www.bis.gov.in/apply-for-a-license/?lang=en", "authority": "BIS Licensing Manual", "support_level": "official_guidance"}],
            "support_level": "evidence_grounded"
        }

    def _laboratory_tool(self, message: str, lang: str, role: Dict[str, Any]) -> Dict[str, Any]:
        matches = self.find_matches(message, 1)
        top = matches[0] if matches else None
        std_str = f" for standard {top.get('standard_number')}" if top else ""
        reply = (
            f"**BIS Laboratory Intelligence**{std_str}:\n\n"
            f"{self._t(lang, 'labs')}\n\n"
            "Key national facilities:\n"
            "• **BIS Central Laboratory (Sahibabad, Delhi NCR)**: comprehensive electrical, gas, and mechanical test benches\n"
            "• **BIS Regional Laboratories (Mumbai, Chennai, Kolkata, Mohali)**\n"
            "• **Empanelled National Labs**: CPRI (Cables/Switchgear), ARAI (Automotive/Helmets), ERTL (Electronics/IT)\n\n"
            "Use the Laboratory Finder in SmartGuide or BIS LIMS to verify current accredited scopes."
        )
        return {
            "reply": reply,
            "intent": "laboratory",
            "tool": "BIS Laboratory Guide",
            "recommendations": matches,
            "confidence": 0.92,
            "sources": [
                {"title": "BIS LIMS Directory", "url": "https://lims.bis.gov.in/", "authority": "BIS LIMS", "support_level": "official_lims"},
                {"title": "BIS Recognized Labs Directory", "url": "https://www.bis.gov.in/laboratorys/list-of-bis-recognized-lab/?lang=en", "authority": "BIS Portal", "support_level": "official_directory"}
            ],
            "support_level": "evidence_grounded"
        }

    def _compliance_tool(self, message: str, lang: str, role: Dict[str, Any]) -> Dict[str, Any]:
        if self.compliance_checker:
            data = self.compliance_checker(message)
            if data:
                return {
                    "reply": f"{data['reply']}\n\n[{role['title']} Focus]: {role['product_perspective']}",
                    "intent": "compliance",
                    "tool": "BIS Compliance Engine",
                    "recommendations": [data["standard"]],
                    "confidence": 0.90,
                    "sources": [{"title": data["standard"].get("standard_number"), "url": data.get("source") or "https://standards.bis.gov.in/", "authority": "BIS Standards Record", "support_level": "authoritative_standard"}],
                    "support_level": "evidence_grounded"
                }
        return {
            "reply": f"{self._t(lang, 'compliance_prompt')}\n\n[{role['title']} Guide]: {role['checklist_intro']}",
            "intent": "compliance",
            "tool": "BIS Compliance Engine",
            "recommendations": [],
            "confidence": 0.70,
            "sources": [],
            "support_level": "general_guidance"
        }

    def _rag_tool(self, message: str, lang: str, role: Dict[str, Any]) -> Dict[str, Any]:
        result = self.rag.answer(message, 5)
        reply = result.get("answer", "")
        if result.get("support_level") == "unsupported":
            reply = f"{self._t(lang, 'refusal')}\n\nQuery: '{message}'\n\n[{role['title']} Advice]: Please specify a physical manufactured product or authentic IS number."
        else:
            reply = f"{reply}\n\n[{role['title']} Analysis]: {role['product_perspective']}\n\n{self._t(lang, 'prototype')}"

        return {
            "reply": reply,
            "intent": "rag_knowledge",
            "tool": "Local BIS RAG",
            "recommendations": [],
            "confidence": result.get("confidence", 0.5),
            "sources": result.get("sources", []),
            "retrieved": result.get("retrieved", []),
            "retrieved_count": result.get("retrieved_count", 0),
            "support_level": result.get("support_level", "rag_retrieved")
        }
