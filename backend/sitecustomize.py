"""BIS SmartGuide V3 agent enhancement layer."""
from bis_agent import BISExpertAgent

_ORIGINAL_RUN = BISExpertAgent.run
GREETING_REPLIES = {
    "en": {"greeting":"Hello! 👋 I’m BIS SmartGuide V3. I can help with BIS standards, product compliance, certification, QCOs, testing laboratories and BIS services. What would you like to know?","thanks":"You’re welcome! 😊 I’m here whenever you need help with BIS standards or compliance.","bye":"Goodbye! 👋 Come back anytime for BIS standards, certification or compliance help."},
    "te": {"greeting":"నమస్తే! 👋 నేను BIS SmartGuide V3. BIS ప్రమాణాలు, కంప్లయన్స్, సర్టిఫికేషన్ మరియు QCOలపై సహాయం చేయగలను. ఏమి తెలుసుకోవాలి?","thanks":"స్వాగతం! 😊 BIS గురించి సహాయం కావాలంటే ఎప్పుడైనా అడగండి.","bye":"వీడ్కోలు! 👋 మళ్లీ రండి."},
    "hi": {"greeting":"नमस्ते! 👋 मैं BIS SmartGuide V3 हूँ। मैं BIS मानकों, अनुपालन, प्रमाणन और QCO में मदद कर सकता हूँ।","thanks":"आपका स्वागत है! 😊 BIS के बारे में मदद चाहिए तो पूछें।","bye":"अलविदा! 👋 फिर मिलते हैं।"},
    "kn": {"greeting":"ನಮಸ್ಕಾರ! 👋 ನಾನು BIS SmartGuide V3. BIS ಮಾನದಂಡಗಳು, ಅನುಸರಣೆ ಮತ್ತು ಪ್ರಮಾಣೀಕರಣದಲ್ಲಿ ಸಹಾಯ ಮಾಡಬಹುದು.","thanks":"ಸ್ವಾಗತ! 😊 BIS ಬಗ್ಗೆ ಸಹಾಯ ಬೇಕಾದರೆ ಕೇಳಿ.","bye":"ವಿದಾಯ! 👋 ಮತ್ತೆ ಬನ್ನಿ."},
    "ta": {"greeting":"வணக்கம்! 👋 நான் BIS SmartGuide V3. BIS தரநிலைகள், இணக்கம் மற்றும் சான்றிதழ் குறித்து உதவ முடியும்.","thanks":"வரவேற்கிறேன்! 😊 BIS குறித்து உதவி தேவைப்பட்டால் கேளுங்கள்.","bye":"விடைபெறுகிறேன்! 👋 மீண்டும் வாருங்கள்."},
}
GREETING_WORDS={"hi","hello","hey","hiya","namaste","namaskar","good morning","good afternoon","good evening","good night","నమస్తే","నమస్కారం","नमस्ते","नमस्कार","ನಮಸ್ಕಾರ","வணக்கம்"}
THANKS_WORDS={"thanks","thank you","thankyou","ధన్యవాదాలు","धन्यवाद","ಧನ್ಯವಾದ","நன்றி"}
BYE_WORDS={"bye","goodbye","good bye","see you","వీడ్కోలు","अलविदा","ವಿದಾಯ","விடைபெறுகிறேன்"}

def _social_kind(text):
    normalized=BISExpertAgent._normalize(text)
    if normalized in GREETING_WORDS:return "greeting"
    if normalized in THANKS_WORDS:return "thanks"
    if normalized in BYE_WORDS:return "bye"
    return None

def _intent(text):
    t=BISExpertAgent._normalize(text)
    if any(x in t for x in ("compliance","comply","requirement","checklist","conformity")):return "compliance"
    if any(x in t for x in ("certification","license","licence","apply","registration")):return "certification"
    if any(x in t for x in ("qco","mandatory","compulsory")):return "mandatory_check"
    if any(x in t for x in ("laboratory","lab","testing","test center")):return "laboratory"
    if any(x in t for x in ("standard","is ","bis ","search","find")):return "standards_search"
    return "general_bis"

def _v3_run(self,message,role=None,language=None):
    # Accept role/language from the upgraded /chat endpoint. Older callers can
    # still call run(message) unchanged. Prefer an explicit supported language;
    # otherwise preserve the existing automatic language detection.
    requested_language=str(language or "").strip().lower()
    if requested_language in getattr(self,"LANGUAGES",{}):
        detected_language=requested_language
    else:
        detected_language=self.detect_language(message)
    kind=_social_kind(message)
    lang=detected_language
    if not hasattr(self,"conversation_memory"):self.conversation_memory=[]
    self.conversation_memory.append({"user":str(message)[:1000],"role":role or "user","language":lang}); self.conversation_memory=self.conversation_memory[-8:]
    if kind:
        return {"reply":GREETING_REPLIES.get(lang,GREETING_REPLIES["en"])[kind],"intent":"conversation","tool":"Conversation Router","recommendations":[],"sources":[],"retrieved":[],"retrieved_count":0,"confidence":1.0,"support_level":"conversation","agent":self.name,"agent_version":self.version,"agentic":True,"language":lang,"language_name":self.LANGUAGES[lang],"memory_turns":len(self.conversation_memory),"disclaimer":self._t(lang,"disclaimer")}
    result=_ORIGINAL_RUN(self,message)
    if not isinstance(result,dict):result={"reply":str(result)}
    result["agent_version"]=self.version; result["agentic"]=True; result["intent"]=result.get("intent") or _intent(message); result["memory_turns"]=len(self.conversation_memory)
    if requested_language in getattr(self,"LANGUAGES",{}):
        result["language"]=lang; result["language_name"]=self.LANGUAGES[lang]
    confidence=result.get("confidence")
    if isinstance(confidence,(int,float)) and confidence<0.45:
        result["follow_up"]="Please provide the exact product name, model, or BIS standard number for a stronger match."; result["support_level"]="low-confidence"
    elif "follow_up" not in result:result["follow_up"]="If you give me the product/model, I can narrow this down further."
    return result

BISExpertAgent.version="3.0"
BISExpertAgent.run=_v3_run

# Runtime compatibility patch: the legacy upgraded endpoint originally had
# eleven SQL placeholders for a twelve-column assessment row. The V4 route is
# already correct; this keeps the old /check-product frontend route working.
try:
    import app_upgrade
    from flask import jsonify, request
    from compliance_upgrade import _build_assessment, _db, _hash_evidence, _now
    import json, uuid
    def _fixed_save_assessment(result, product):
        assessment_id="BIS-"+uuid.uuid4().hex[:10].upper(); created_at=_now(); evidence_hash=_hash_evidence(result.get("evidence",{}))
        result.update({"assessment_id":assessment_id,"created_at":created_at,"evidence_hash":evidence_hash})
        with _db() as con:
            con.execute("INSERT INTO assessments VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(assessment_id,created_at,product,result.get("evidence",{}).get("model"),result.get("evidence",{}).get("manufacturer"),result.get("standard",{}).get("standard_number"),int(result.get("score",0)),result.get("risk","MEDIUM"),result.get("status","REVIEW"),result.get("evidence_quality","LOW"),json.dumps(result,ensure_ascii=False),evidence_hash))
            for action in result.get("corrective_actions",[]):
                con.execute("INSERT INTO actions VALUES (?,?,?,?,?,?,?)",(uuid.uuid4().hex[:12],assessment_id,action["requirement"],action["priority"],action["action"],"OPEN",created_at))
        return result
    app_upgrade._save_assessment=_fixed_save_assessment
    def _fixed_check_product():
        body=request.get_json(silent=True) or {}; product=str(body.get("product","")).strip()
        if not product:return jsonify({"error":"Product name is required"}),400
        result=_build_assessment(product,body.get("checks") or {},body.get("evidence") or {},str(body.get("document_text","")))
        if not result.get("standard"):return jsonify(result),404
        return jsonify(_fixed_save_assessment(result,product))
    app_upgrade.app.view_functions["check_product"]=_fixed_check_product
except Exception:
    pass
