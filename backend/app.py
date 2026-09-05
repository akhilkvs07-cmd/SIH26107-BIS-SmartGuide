from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
import re
from rag_engine import LocalRAG

app = Flask(__name__)
CORS(app)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "bis_data.json")
with open(DATA_FILE, "r", encoding="utf-8") as file:
    data = json.load(file)
bis_data = data.get("standards", [])

OFFICIAL_RESOURCES = [
    {"name":"BIS Standards Portal","description":"Search standards and standard-related information.","url":"https://standards.bis.gov.in/"},
    {"name":"Know Your Standard","description":"Access standards, amendments, notifications and related information.","url":"https://www.bis.gov.in/know-your-standard/?lang=en"},
    {"name":"Apply for a BIS Licence","description":"Official guidance for the BIS licensing process.","url":"https://www.bis.gov.in/apply-for-a-license/?lang=en"},
    {"name":"BIS Recognized Laboratories","description":"Official list and laboratory information.","url":"https://www.bis.gov.in/laboratorys/list-of-bis-recognized-lab/?lang=en"},
    {"name":"BIS Laboratory Information","description":"BIS laboratory information management system.","url":"https://lims.bis.gov.in/"}
]
STOP_WORDS={"a","an","and","are","as","at","be","by","for","from","has","have","how","i","in","is","it","of","on","or","that","the","this","to","what","which","with","my","our","can","do","does","about","tell","me","please","product","used","use"}
SYNONYMS={"fan":["fan","ceiling fan","table fan","electric fan"],"charger":["charger","phone charger","mobile charger","adapter"],"iron":["iron","electric iron","clothes iron"],"stove":["stove","gas stove","gas cooker","gas cooking"],"cable":["cable","wire","pvc cable","insulated cable"],"lamp":["lamp","led","led lamp","light"],"kettle":["kettle","electric kettle"],"mixer":["mixer","mixer grinder","grinder"],"microwave":["microwave","microwave oven"],"heater":["heater","water heater","electric heater","immersion heater"],"socket":["socket","electrical socket","power socket"],"switch":["switch","electrical switch"],"refrigerator":["refrigerator","fridge"],"washing":["washing machine","washer"],"air conditioner":["air conditioner","ac","air conditioning"],"toaster":["toaster","electric toaster"],"rice cooker":["rice cooker","cooker"]}

def normalize(text):
    text=str(text or "").lower().strip().replace("-"," ")
    return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9\s]"," ",text)).strip()

def tokenize(text): return [w for w in normalize(text).split() if len(w)>2 and w not in STOP_WORDS]

def searchable(s):
    return normalize(" ".join([s.get("standard_number",""),s.get("product",""),s.get("title",""),s.get("category",""),s.get("description","")," ".join(s.get("requirements",[]))]))

def score_standard(query,standard):
    q=normalize(query)
    if not q:return 0,[]
    product,title,category=normalize(standard.get("product","")),normalize(standard.get("title","")),normalize(standard.get("category",""))
    number,text=normalize(standard.get("standard_number","")),searchable(standard)
    words,score,reasons,matched=tokenize(q),0,[],[]
    if q==product:score+=100;reasons.append("Exact product match")
    elif q in product:score+=65;reasons.append("Product name contains your search")
    if q in title:score+=45;reasons.append("Product matches the standard title")
    if q in category:score+=20;reasons.append("Product matches the category")
    if q==number or q.replace(" ","")==number.replace(" ",""):score+=110;reasons.append("Standard number match")
    for word in words:
        if word in product:score+=22;matched.append(word)
        elif word in title:score+=14;matched.append(word)
        elif word in category:score+=7;matched.append(word)
        elif word in text:score+=4;matched.append(word)
    if matched:reasons.append("Keyword match: "+", ".join(sorted(set(matched))))
    for key,alts in SYNONYMS.items():
        if any(word==key or word in alts for word in words) and any(alt in text for alt in alts):score+=10;reasons.append("Related product terminology detected");break
    return score,reasons

def find_matches(query,limit=5):
    ranked=[]
    for standard in bis_data:
        score,reasons=score_standard(query,standard)
        if score:
            item=dict(standard);item["match_score"]=min(100,score);item["raw_match_score"]=score;item["match_reasons"]=reasons[:5];ranked.append(item)
    ranked.sort(key=lambda x:x["raw_match_score"],reverse=True)
    return ranked[:limit]

def detect_product_entities(description):
    matches=find_matches(description,5);best=matches[0] if matches else None;text=normalize(description);attributes=[]
    for pattern in [r"\b\d+(?:\.\d+)?\s*(?:w|kw|v|kv|a|amp|amps|hz|kg|g|mm|cm|l|litre|liter)\b",r"\b\d+(?:\.\d+)?\s*(?:degree|degrees|c|°c)\b"]:attributes.extend(re.findall(pattern,text))
    for feature in ["temperature control","adjustable temperature","overheating protection","insulation","household use","gas","electric","portable","automatic","digital","stainless steel","plastic","motor","heating element","water protection","voltage protection","pressure protection"]:
        if feature in text:attributes.append(feature)
    return {"input":description,"detected_product":best.get("product") if best else None,"detected_category":best.get("category") if best else None,"attributes":list(dict.fromkeys(attributes)),"recommendations":matches}

def certification_steps(standard=None):
    name=standard.get("standard_number") if standard else "the applicable BIS standard"
    return [f"Identify and confirm {name} as the applicable standard.","Review the latest official BIS requirements, amendments and applicable scheme details.","Check that manufacturing, materials, testing facilities and quality controls can meet the requirements.","Arrange applicable product testing through an appropriate BIS-recognized/empanelled laboratory where required.","Prepare the required technical and manufacturing documents.","Submit the applicable BIS application and complete inspection/assessment requirements.","Maintain continuing conformity, testing and records after certification where applicable."]

rag=LocalRAG(bis_data,OFFICIAL_RESOURCES)

@app.route("/")
def home():return jsonify({"message":"BIS SmartGuide V2 Backend is running","status":"success","version":"2.1-rag"})
@app.route("/health")
def health():return jsonify({"status":"healthy","standards_loaded":len(bis_data),"rag_chunks":len(rag.chunks)})
@app.route("/standards")
def standards():return jsonify({"count":len(bis_data),"standards":bis_data})
@app.route("/search")
def search():
    q=request.args.get("q","").strip()
    if not q:return jsonify({"error":"Please provide a search query"}),400
    r=find_matches(q,10);return jsonify({"query":q,"count":len(r),"results":r})
@app.route("/recommend")
def recommend():
    p=request.args.get("product","").strip()
    if not p:return jsonify({"error":"Please enter a product name or description"}),400
    r=find_matches(p,5)
    if not r:return jsonify({"found":False,"message":"No matching BIS standard found","recommendations":[]})
    return jsonify({"found":True,"standard":r[0],"recommendations":r,"match_score":r[0]["match_score"],"prototype_notice":"Prototype recommendation only. Verify the applicable requirement against current official BIS documentation."})
@app.route("/analyze",methods=["POST"])
def analyze():
    body=request.get_json(silent=True) or {};d=str(body.get("description","")).strip()
    if not d:return jsonify({"error":"Product description is required"}),400
    return jsonify(detect_product_entities(d))
@app.route("/recommendations")
def recommendations():
    q=request.args.get("q","").strip()
    if not q:return jsonify({"error":"Please provide a product description"}),400
    r=find_matches(q,5);return jsonify({"query":q,"recommendations":r,"count":len(r)})
@app.route("/check-compliance")
def check_compliance():
    p=request.args.get("product","").strip()
    if not p:return jsonify({"error":"Please provide a product name"}),400
    r=find_matches(p,1)
    if not r:return jsonify({"found":False,"message":"No matching BIS standard found"})
    return jsonify({"found":True,"standard":r[0],"match_score":r[0]["match_score"]})
@app.route("/check-product",methods=["POST"])
def check_product():
    body=request.get_json(silent=True) or {};product=str(body.get("product","")).strip();checks=body.get("checks",{}) or {}
    if not product:return jsonify({"error":"Product name is required"}),400
    r=find_matches(product,1)
    if not r:return jsonify({"found":False,"message":"No matching BIS standard found"})
    standard=r[0];requirements=standard.get("requirements",[]);passed=[];failed=[];not_checked=[]
    for req in requirements:
        value=checks.get(req)
        if value is True:passed.append(req)
        elif value is False:failed.append(req)
        else:not_checked.append(req)
    total=len(requirements);score=round(len(passed)/total*100) if total else 0;status="Needs Review" if failed else ("Partially Checked" if not_checked else "Compliant")
    actions=[f"Review and correct: {x}." for x in failed]
    if not_checked:actions.append("Complete the remaining unchecked requirements before making a final conformity decision.")
    if not actions:actions.append("Maintain test records and verify the latest official BIS requirements.")
    return jsonify({"found":True,"product":product,"standard":standard,"match_score":standard["match_score"],"score":score,"status":status,"passed":passed,"failed":failed,"not_checked":not_checked,"summary":{"total":total,"passed":len(passed),"failed":len(failed),"not_checked":len(not_checked)},"recommended_actions":actions,"certification_steps":certification_steps(standard),"compliance_text":standard.get("compliance_text","Verify against official BIS documentation."),"prototype_notice":"This is a prototype compliance assessment and does not represent official BIS certification."})
@app.route("/certification-guide")
def certification_guide():
    q=request.args.get("product","").strip();matches=find_matches(q,1) if q else [];standard=matches[0] if matches else None
    return jsonify({"standard":standard,"steps":certification_steps(standard),"official_resources":OFFICIAL_RESOURCES[:3],"notice":"Certification requirements vary by product, applicable standard and scheme. Always verify current BIS instructions."})
@app.route("/labs")
def labs():return jsonify({"message":"Use the official BIS recognized laboratory directory to find current laboratory information.","official_url":OFFICIAL_RESOURCES[3]["url"],"lims_url":OFFICIAL_RESOURCES[4]["url"]})
@app.route("/resources")
def resources():return jsonify({"resources":OFFICIAL_RESOURCES})
@app.route("/rag-search")
def rag_search():
    q=request.args.get("q","").strip()
    if not q:return jsonify({"error":"Please provide a query"}),400
    return jsonify({"query":q,"rag":True,"results":rag.retrieve(q,6)})
@app.route("/chat",methods=["POST"])
def chat():
    body=request.get_json(silent=True) or {};message=str(body.get("message","")).strip()
    if not message:return jsonify({"error":"Message is required"}),400
    lower=normalize(message);matches=find_matches(message,3);rag_result=rag.answer(message,4)
    if any(x in lower for x in ["certification","license","licence","apply"]):intent="certification";reply="For BIS certification, first identify the applicable standard, review current BIS requirements, arrange applicable testing or assessment, prepare documentation, and follow the official BIS application process."
    elif any(x in lower for x in ["lab","laboratory","testing"]):intent="laboratory";reply="For current laboratory information, use the official BIS recognized laboratory directory or BIS LIMS."
    elif matches:
        top=matches[0];intent="standard_search";reply=f"The RAG knowledge base found {top.get('standard_number')} ({top.get('title')}) as the strongest match for your question. {top.get('description','')}"
    else:intent="general";reply=rag_result["answer"]
    return jsonify({"reply":reply,"intent":intent,"recommendations":matches,"rag":True,"retrieved_count":rag_result["retrieved_count"],"sources":rag_result["sources"],"retrieved":rag_result.get("retrieved",[])})

if __name__=="__main__":app.run(host="127.0.0.1",port=5000,debug=False)
