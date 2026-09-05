from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
import re

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "bis_data.json")

with open(DATA_FILE, "r", encoding="utf-8") as file:
    data = json.load(file)

bis_data = data.get("standards", [])

OFFICIAL_RESOURCES = [
    {
        "name": "BIS Standards Portal",
        "description": "Search standards and standard-related information.",
        "url": "https://standards.bis.gov.in/"
    },
    {
        "name": "Know Your Standard",
        "description": "Access standards, amendments, notifications and related information.",
        "url": "https://www.bis.gov.in/know-your-standard/?lang=en"
    },
    {
        "name": "Apply for a BIS Licence",
        "description": "Official guidance for the BIS licensing process.",
        "url": "https://www.bis.gov.in/apply-for-a-license/?lang=en"
    },
    {
        "name": "BIS Recognized Laboratories",
        "description": "Official list and laboratory information.",
        "url": "https://www.bis.gov.in/laboratorys/list-of-bis-recognized-lab/?lang=en"
    },
    {
        "name": "BIS Laboratory Information",
        "description": "BIS laboratory information management system.",
        "url": "https://lims.bis.gov.in/"
    }
]

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "have", "in", "is", "it", "of", "on", "or", "that", "the",
    "this", "to", "with", "my", "our", "used", "use", "product", "made",
    "manufactured", "manufacturing", "type", "model", "item", "device"
}

SYNONYMS = {
    "fan": ["fan", "ceiling fan", "table fan", "electric fan"],
    "charger": ["charger", "phone charger", "mobile charger", "adapter"],
    "iron": ["iron", "electric iron", "clothes iron"],
    "stove": ["stove", "gas stove", "gas cooker", "gas cooking"],
    "cable": ["cable", "wire", "pvc cable", "insulated cable"],
    "lamp": ["lamp", "led", "led lamp", "light"],
    "kettle": ["kettle", "electric kettle"],
    "mixer": ["mixer", "mixer grinder", "grinder"],
    "microwave": ["microwave", "microwave oven"],
    "heater": ["heater", "water heater", "electric heater", "immersion heater"],
    "socket": ["socket", "electrical socket", "power socket"],
    "switch": ["switch", "electrical switch"],
    "refrigerator": ["refrigerator", "fridge"],
    "washing": ["washing machine", "washer"],
    "air conditioner": ["air conditioner", "ac", "air conditioning"],
    "toaster": ["toaster", "electric toaster"],
    "rice cooker": ["rice cooker", "cooker"]
}


def normalize(text):
    text = str(text or "").lower().strip()
    text = text.replace("-", " ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text):
    return [w for w in normalize(text).split() if len(w) > 2 and w not in STOP_WORDS]


def searchable(standard):
    return normalize(" ".join([
        standard.get("standard_number", ""),
        standard.get("product", ""),
        standard.get("title", ""),
        standard.get("category", ""),
        standard.get("description", ""),
        " ".join(standard.get("requirements", []))
    ]))


def score_standard(query, standard):
    q = normalize(query)
    if not q:
        return 0, []

    product = normalize(standard.get("product", ""))
    title = normalize(standard.get("title", ""))
    category = normalize(standard.get("category", ""))
    description = normalize(standard.get("description", ""))
    number = normalize(standard.get("standard_number", ""))
    text = searchable(standard)
    words = tokenize(q)
    score = 0
    reasons = []

    if q == product:
        score += 100
        reasons.append("Exact product match")
    elif q in product:
        score += 65
        reasons.append("Product name contains your search")

    if q in title:
        score += 45
        reasons.append("Product matches the standard title")

    if q in category:
        score += 20
        reasons.append("Product matches the category")

    if q == number or q.replace(" ", "") == number.replace(" ", ""):
        score += 110
        reasons.append("Standard number match")

    matched_words = []
    for word in words:
        if word in product:
            score += 22
            matched_words.append(word)
        elif word in title:
            score += 14
            matched_words.append(word)
        elif word in category:
            score += 7
            matched_words.append(word)
        elif word in text:
            score += 4
            matched_words.append(word)

    if matched_words:
        reasons.append("Keyword match: " + ", ".join(sorted(set(matched_words))))

    for key, alternatives in SYNONYMS.items():
        if any(word == key or word in alternatives for word in words):
            alt_hits = [alt for alt in alternatives if alt in text]
            if alt_hits:
                score += 10
                reasons.append("Related product terminology detected")
                break

    if description and any(word in description for word in words):
        score += 3

    return score, reasons


def find_matches(query, limit=5):
    ranked = []
    for standard in bis_data:
        score, reasons = score_standard(query, standard)
        if score > 0:
            item = dict(standard)
            item["match_score"] = min(100, score)
            item["raw_match_score"] = score
            item["match_reasons"] = reasons[:5]
            ranked.append(item)
    ranked.sort(key=lambda x: x["raw_match_score"], reverse=True)
    return ranked[:limit]


def detect_product_entities(description):
    text = normalize(description)
    matches = find_matches(text, 5)
    best = matches[0] if matches else None
    attributes = []

    patterns = [
        r"\b\d+(?:\.\d+)?\s*(?:w|kw|v|kv|a|amp|amps|hz|kg|g|mm|cm|l|litre|liter)\b",
        r"\b\d+(?:\.\d+)?\s*(?:degree|degrees|c|°c)\b"
    ]
    for pattern in patterns:
        attributes.extend(re.findall(pattern, text))

    feature_words = [
        "temperature control", "adjustable temperature", "overheating protection",
        "insulation", "household use", "gas", "electric", "portable", "automatic",
        "digital", "stainless steel", "plastic", "motor", "heating element",
        "water protection", "voltage protection", "pressure protection"
    ]
    for feature in feature_words:
        if feature in text:
            attributes.append(feature)

    return {
        "input": description,
        "detected_product": best.get("product") if best else None,
        "detected_category": best.get("category") if best else None,
        "attributes": list(dict.fromkeys(attributes)),
        "recommendations": matches
    }


def certification_steps(standard=None):
    standard_name = standard.get("standard_number") if standard else "the applicable BIS standard"
    return [
        f"Identify and confirm {standard_name} as the applicable standard.",
        "Review the latest official BIS requirements, amendments and applicable scheme details.",
        "Check that your manufacturing process, materials, testing facilities and quality controls can meet the requirements.",
        "Arrange applicable product testing through an appropriate BIS-recognized/empanelled laboratory where required.",
        "Prepare the required technical and manufacturing documents.",
        "Submit the applicable BIS application and complete inspection/assessment requirements.",
        "Maintain continuing conformity, testing and records after certification where applicable."
    ]


@app.route("/")
def home():
    return jsonify({
        "message": "BIS SmartGuide V2 Backend is running",
        "status": "success",
        "version": "2.0"
    })


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "standards_loaded": len(bis_data)})


@app.route("/standards")
def standards():
    return jsonify({"count": len(bis_data), "standards": bis_data})


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Please provide a search query"}), 400
    results = find_matches(query, 10)
    return jsonify({
        "query": query,
        "count": len(results),
        "results": results
    })


@app.route("/recommend")
def recommend():
    product = request.args.get("product", "").strip()
    if not product:
        return jsonify({"error": "Please enter a product name or description"}), 400

    results = find_matches(product, 5)
    if not results:
        return jsonify({
            "found": False,
            "message": "No matching BIS standard found",
            "recommendations": []
        })

    return jsonify({
        "found": True,
        "standard": results[0],
        "recommendations": results,
        "match_score": results[0]["match_score"],
        "prototype_notice": "Prototype recommendation only. Verify the applicable requirement against current official BIS documentation."
    })


@app.route("/analyze", methods=["POST"])
def analyze():
    body = request.get_json(silent=True) or {}
    description = str(body.get("description", "")).strip()
    if not description:
        return jsonify({"error": "Product description is required"}), 400
    return jsonify(detect_product_entities(description))


@app.route("/recommendations")
def recommendations():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Please provide a product description"}), 400
    results = find_matches(query, 5)
    return jsonify({
        "query": query,
        "recommendations": results,
        "count": len(results)
    })


@app.route("/check-compliance")
def check_compliance():
    product = request.args.get("product", "").strip()
    if not product:
        return jsonify({"error": "Please provide a product name"}), 400
    results = find_matches(product, 1)
    if not results:
        return jsonify({"found": False, "message": "No matching BIS standard found"})
    return jsonify({"found": True, "standard": results[0], "match_score": results[0]["match_score"]})


@app.route("/check-product", methods=["POST"])
def check_product():
    body = request.get_json(silent=True) or {}
    product = str(body.get("product", "")).strip()
    checks = body.get("checks", {}) or {}

    if not product:
        return jsonify({"error": "Product name is required"}), 400

    results = find_matches(product, 1)
    if not results:
        return jsonify({"found": False, "message": "No matching BIS standard found"})

    matched_standard = results[0]
    requirements = matched_standard.get("requirements", [])
    passed, failed, not_checked = [], [], []

    for requirement in requirements:
        value = checks.get(requirement)
        if value is True:
            passed.append(requirement)
        elif value is False:
            failed.append(requirement)
        else:
            not_checked.append(requirement)

    total = len(requirements)
    score = round((len(passed) / total) * 100) if total else 0

    if failed:
        status = "Needs Review"
    elif not_checked:
        status = "Partially Checked"
    else:
        status = "Compliant"

    actions = []
    for item in failed:
        actions.append(f"Review and correct: {item}.")
    if not_checked:
        actions.append("Complete the remaining unchecked requirements before making a final conformity decision.")
    if not actions:
        actions.append("Maintain test records and verify the latest official BIS requirements.")

    return jsonify({
        "found": True,
        "product": product,
        "standard": matched_standard,
        "match_score": matched_standard["match_score"],
        "score": score,
        "status": status,
        "passed": passed,
        "failed": failed,
        "not_checked": not_checked,
        "summary": {
            "total": total,
            "passed": len(passed),
            "failed": len(failed),
            "not_checked": len(not_checked)
        },
        "recommended_actions": actions,
        "certification_steps": certification_steps(matched_standard),
        "compliance_text": matched_standard.get("compliance_text", "Verify against official BIS documentation."),
        "prototype_notice": "This is a prototype compliance assessment and does not represent official BIS certification."
    })


@app.route("/certification-guide")
def certification_guide():
    query = request.args.get("product", "").strip()
    standard = None
    if query:
        matches = find_matches(query, 1)
        standard = matches[0] if matches else None
    return jsonify({
        "standard": standard,
        "steps": certification_steps(standard),
        "official_resources": OFFICIAL_RESOURCES[:3],
        "notice": "Certification requirements vary by product, applicable standard and scheme. Always verify current BIS instructions."
    })


@app.route("/labs")
def labs():
    return jsonify({
        "message": "Use the official BIS recognized laboratory directory to find current laboratory information.",
        "official_url": "https://www.bis.gov.in/laboratorys/list-of-bis-recognized-lab/?lang=en",
        "lims_url": "https://lims.bis.gov.in/"
    })


@app.route("/resources")
def resources():
    return jsonify({"resources": OFFICIAL_RESOURCES})


@app.route("/chat", methods=["POST"])
def chat():
    body = request.get_json(silent=True) or {}
    message = str(body.get("message", "")).strip()
    if not message:
        return jsonify({"error": "Message is required"}), 400

    lower = normalize(message)
    matches = find_matches(message, 3)

    if any(word in lower for word in ["certification", "license", "licence", "apply"]):
        reply = "For BIS certification, first identify the applicable standard, review current BIS requirements, arrange applicable testing/assessment, prepare documentation, and follow the official BIS application process."
        intent = "certification"
    elif any(word in lower for word in ["lab", "laboratory", "testing"]):
        reply = "For current laboratory information, use the official BIS recognized laboratory directory or BIS LIMS."
        intent = "laboratory"
    elif matches:
        top = matches[0]
        reply = f"I found a likely match: {top.get('standard_number')} — {top.get('title')}. The prototype match score is {top.get('match_score')}%. Please verify applicability against official BIS documentation."
        intent = "standard_search"
    else:
        reply = "I can help find a likely BIS standard, explain the prototype compliance checklist, or guide you to official BIS certification and laboratory resources."
        intent = "general"

    return jsonify({"reply": reply, "intent": intent, "recommendations": matches})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
