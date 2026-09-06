"""Startup patch for BIS SmartGuide conversation routing.

Keeps greetings and simple social messages out of the standards RAG search.
This is intentionally small and dependency-free.
"""

from bis_agent import BISExpertAgent

_ORIGINAL_RUN = BISExpertAgent.run

GREETING_REPLIES = {
    "en": {
        "greeting": "Hello! 👋 I’m BIS SmartGuide. I can help with BIS standards, certification, compliance, QCOs, testing laboratories and BIS services. What would you like to know?",
        "thanks": "You’re welcome! I’m here whenever you need help with BIS standards or services. 😊",
        "bye": "Goodbye! 👋 Come back anytime for BIS standards, certification or compliance help.",
    },
    "te": {
        "greeting": "నమస్తే! 👋 నేను BIS SmartGuide. BIS ప్రమాణాలు, సర్టిఫికేషన్, కంప్లయన్స్, QCOలు మరియు BIS సేవల గురించి సహాయం చేయగలను. ఏమి తెలుసుకోవాలనుకుంటున్నారు?",
        "thanks": "స్వాగతం! BIS ప్రమాణాలు లేదా సేవలపై సహాయం కావాలంటే ఎప్పుడైనా అడగండి. 😊",
        "bye": "వీడ్కోలు! 👋 BIS ప్రమాణాలు, సర్టిఫికేషన్ లేదా కంప్లయన్స్ సహాయం కోసం మళ్లీ రండి.",
    },
    "hi": {
        "greeting": "नमस्ते! 👋 मैं BIS SmartGuide हूँ। मैं BIS मानकों, प्रमाणन, अनुपालन, QCO और BIS सेवाओं में मदद कर सकता हूँ। आप क्या जानना चाहते हैं?",
        "thanks": "आपका स्वागत है! BIS मानकों या सेवाओं के बारे में मदद चाहिए तो कभी भी पूछें। 😊",
        "bye": "अलविदा! 👋 BIS मानकों, प्रमाणन या अनुपालन सहायता के लिए फिर आएँ।",
    },
    "kn": {
        "greeting": "ನಮಸ್ಕಾರ! 👋 ನಾನು BIS SmartGuide. BIS ಮಾನದಂಡಗಳು, ಪ್ರಮಾಣೀಕರಣ, ಅನುಸರಣೆ, QCOಗಳು ಮತ್ತು BIS ಸೇವೆಗಳ ಬಗ್ಗೆ ಸಹಾಯ ಮಾಡಬಹುದು. ಏನು ತಿಳಿದುಕೊಳ್ಳಲು ಬಯಸುತ್ತೀರಿ?",
        "thanks": "ಸ್ವಾಗತ! BIS ಮಾನದಂಡಗಳು ಅಥವಾ ಸೇವೆಗಳ ಬಗ್ಗೆ ಸಹಾಯ ಬೇಕಾದರೆ ಯಾವಾಗ ಬೇಕಾದರೂ ಕೇಳಿ. 😊",
        "bye": "ವಿದಾಯ! 👋 BIS ಮಾನದಂಡಗಳು, ಪ್ರಮಾಣೀಕರಣ ಅಥವಾ ಅನುಸರಣೆ ಸಹಾಯಕ್ಕಾಗಿ ಮತ್ತೆ ಬನ್ನಿ.",
    },
    "ta": {
        "greeting": "வணக்கம்! 👋 நான் BIS SmartGuide. BIS தரநிலைகள், சான்றிதழ், இணக்கம், QCOகள் மற்றும் BIS சேவைகள் குறித்து உதவ முடியும். என்ன தெரிந்துகொள்ள விரும்புகிறீர்கள்?",
        "thanks": "வரவேற்கிறேன்! BIS தரநிலைகள் அல்லது சேவைகள் குறித்து உதவி தேவைப்பட்டால் எப்போது வேண்டுமானாலும் கேளுங்கள். 😊",
        "bye": "விடைபெறுகிறேன்! 👋 BIS தரநிலைகள், சான்றிதழ் அல்லது இணக்க உதவிக்காக மீண்டும் வாருங்கள்.",
    },
}

GREETING_WORDS = {
    "hi", "hello", "hey", "hiya", "namaste", "namaskar",
    "good morning", "good afternoon", "good evening", "good night",
    "నమస్తే", "నమస్కారం", "नमस्ते", "नमस्कार", "ನಮಸ್ಕಾರ", "வணக்கம்",
}
THANKS_WORDS = {"thanks", "thank you", "thankyou", "ధన్యవాదాలు", "धन्यवाद", "ಧನ್ಯವಾದ", "நன்றி"}
BYE_WORDS = {"bye", "goodbye", "good bye", "see you", "వీడ్కోలు", "अलविदा", "ವಿದಾಯ", "விடைபெறுகிறேன்"}


def _social_kind(text):
    normalized = BISExpertAgent._normalize(text)
    if normalized in GREETING_WORDS:
        return "greeting"
    if normalized in THANKS_WORDS:
        return "thanks"
    if normalized in BYE_WORDS:
        return "bye"
    return None


def _social_run(self, message):
    kind = _social_kind(message)
    if not kind:
        return _ORIGINAL_RUN(self, message)

    lang = self.detect_language(message)
    reply = GREETING_REPLIES.get(lang, GREETING_REPLIES["en"])[kind]
    return {
        "reply": reply,
        "intent": "conversation",
        "tool": "Conversation Router",
        "recommendations": [],
        "sources": [],
        "retrieved": [],
        "retrieved_count": 0,
        "confidence": 1.0,
        "support_level": "conversation",
        "agent": self.name,
        "agent_version": self.version,
        "agentic": True,
        "language": lang,
        "language_name": self.LANGUAGES[lang],
        "disclaimer": self._t(lang, "disclaimer"),
    }


BISExpertAgent.version = "2.2"
BISExpertAgent.run = _social_run
