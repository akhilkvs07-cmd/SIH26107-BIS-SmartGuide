"""BIS SmartGuide Core Application & REST API Server.

Production-grade, source-grounded standards intelligence platform for SIH26107.
"""

import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from bis_agent import BISExpertAgent
from labs_directory import search_laboratories, OFFICIAL_LIMS_URL, OFFICIAL_LIMS_SEARCH, OFFICIAL_LAB_DIRECTORY
from product_intelligence import ProductIntelligenceEngine, clean_text, correct_spelling, normalize_query, tokenize
from rag_engine import LocalRAG
from role_engine import RoleEngine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
DATA_FILE = os.path.join(BASE_DIR, "bis_data.json")
DOCS_DIR = os.path.join(BASE_DIR, "documents")
os.makedirs(DOCS_DIR, exist_ok=True)

app = Flask(__name__, static_folder=ROOT_DIR, static_url_path="")
CORS(app)

class StripApiPrefixMiddleware:
    """Enables both /endpoint and /api/endpoint for all routes seamlessly."""
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app
    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        if path.startswith("/api/"):
            environ["PATH_INFO"] = path[4:]
        return self.wsgi_app(environ, start_response)

app.wsgi_app = StripApiPrefixMiddleware(app.wsgi_app)

with open(DATA_FILE, "r", encoding="utf-8") as f:
    raw_data = json.load(f)
bis_data: List[Dict[str, Any]] = raw_data.get("standards", []) if isinstance(raw_data, dict) else raw_data

OFFICIAL_RESOURCES = [
    {
        "name": "BIS Standards Portal",
        "description": "Search Indian Standards by number, keyword or product.",
        "url": "https://standards.bis.gov.in/"
    },
    {
        "name": "Know Your Standard (KYS)",
        "description": "Indian Standards, amendments, notifications and licences.",
        "url": "https://www.bis.gov.in/know-your-standard/?lang=en"
    },
    {
        "name": "Apply for a BIS Licence (e-BIS / Manakonline)",
        "description": "Official product certification & licensing portal.",
        "url": "https://www.bis.gov.in/apply-for-a-license/?lang=en"
    },
    {
        "name": "BIS Recognized Laboratories Directory",
        "description": "Directory of recognized central, regional, branch and partner labs.",
        "url": OFFICIAL_LAB_DIRECTORY
    },
    {
        "name": "BIS LIMS (Laboratory Information Management System)",
        "description": "Current laboratory testing scope and IS number search.",
        "url": OFFICIAL_LIMS_SEARCH
    },
    {
        "name": "Compulsory Certification Products & QCOs",
        "description": "Official Compulsory Registration Scheme (CRS) & Gazette QCO lists.",
        "url": "https://www.bis.gov.in/product-certification/products-under-compulsory-certification/?lang=en"
    },
    {
        "name": "BIS Care Mobile App & Portal",
        "description": "Verify ISI Mark CM/L numbers, Hallmarking HUID, and lodge consumer grievances.",
        "url": "https://www.bis.gov.in/bis-apps/?lang=en"
    }
]

def score_standard(query: str, s: Dict[str, Any]) -> tuple[int, List[str]]:
    q_norm = normalize_query(query)
    if not q_norm:
        return 0, []

    q_clean = correct_spelling(query)
    q_tokens = tokenize(q_clean)

    product = normalize_query(s.get("product", ""))
    title = normalize_query(s.get("title", ""))
    cat = normalize_query(s.get("category", ""))
    std_num = normalize_query(s.get("standard_number", "")).replace(" ", "")
    synonyms = [normalize_query(x) for x in s.get("synonyms", [])]
    desc = normalize_query(s.get("description", ""))
    reqs_text = normalize_query(" ".join(s.get("requirements", [])))

    score = 0
    reasons = []
    matched_words = []

    q_no_space = q_norm.replace(" ", "")
    if q_no_space == std_num or q_norm in std_num:
        score += 125
        reasons.append(f"Direct match with Indian Standard number {s.get('standard_number')}")

    if q_norm == product:
        score += 100
        reasons.append(f"Exact product match for '{s.get('product')}'")
    elif q_norm in product or product in q_norm:
        score += 75
        reasons.append("Product name closely matches your search")

    for syn in synonyms:
        if q_norm == syn:
            score += 90
            reasons.append(f"Matched product synonym '{syn}'")
            break
        elif syn in q_norm or q_norm in syn:
            score += 65
            reasons.append(f"Matched related product term '{syn}'")
            break

    if q_norm in title:
        score += 55
        reasons.append("Matched text in the standard's title")
    elif any(t in title for t in q_tokens):
        score += 30

    if q_norm in cat:
        score += 25
        reasons.append(f"Matched category '{s.get('category')}'")

    for token in q_tokens:
        if token in product:
            score += 20
            matched_words.append(token)
        elif any(token in syn for syn in synonyms):
            score += 18
            matched_words.append(token)
        elif token in title:
            score += 12
            matched_words.append(token)
        elif token in desc or token in reqs_text:
            score += 6
            matched_words.append(token)

    if matched_words:
        unique_matches = sorted(set(matched_words))
        reasons.append(f"Keyword evidence matched: {', '.join(unique_matches[:5])}")

    return score, reasons

def find_matches(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    ranked = []
    q_corrected = correct_spelling(query)
    for s in bis_data:
        score, reasons = score_standard(q_corrected, s)
        if score > 0:
            item = dict(s)
            item["match_score"] = min(100, score)
            item["raw_match_score"] = score
            item["match_reasons"] = reasons[:5]
            item["support_level"] = "authoritative_standard"
            ranked.append(item)

    ranked.sort(key=lambda x: x["raw_match_score"], reverse=True)
    return ranked[:limit]

def certification_steps(standard: Optional[Dict[str, Any]] = None) -> List[str]:
    name = standard.get("standard_number") if standard else "the applicable Indian Standard"
    scheme = standard.get("scheme", "Scheme I (ISI Mark Scheme)") if standard else "applicable scheme"
    return [
        f"Step 1: Identify and confirm {name} as the applicable standard for your product scope.",
        f"Step 2: Review the Gazette Quality Control Order (QCO) and statutory scheme ({scheme}).",
        "Step 3: Establish factory manufacturing infrastructure, process controls and in-house testing equipment.",
        "Step 4: Conduct testing per standard clauses through in-house lab or a BIS-recognized/LIMS laboratory.",
        "Step 5: Prepare documentation (Factory Layout, Test Equipment Calibration, Quality Assurance Plan, Raw Material CoAs).",
        "Step 6: Submit application on the official BIS Manakonline / e-BIS portal and pay statutory fees.",
        "Step 7: Complete factory preliminary inspection, independent sampling, and verification by BIS officers.",
        "Step 8: Grant of BIS Licence / Registration and marking authorization with persistent CM/L or R-number."
    ]

def detect_product_entities(description: str) -> Dict[str, Any]:
    text = clean_text(description)
    norm = normalize_query(text)
    matches = find_matches(text, 5)
    best = matches[0] if matches else None

    attrs = []
    patterns = [
        r"\b\d+(?:\.\d+)?\s*(?:w|kw|v|kv|a|amp|amps|hz|kg|g|mm|cm|l|litre|liter|ml|bar|kpa|mpa)\b",
        r"\b\d+(?:\.\d+)?\s*(?:degree|degrees|c|°c|deg\s*c)\b",
        r"\b(?:1|2|3|4|5|6)\s*(?:burner|burners|ply|core|cores|star|stars)\b"
    ]
    for p in patterns:
        attrs.extend(re.findall(p, norm))

    features = [
        "temperature control", "automatic shutoff", "overheating protection", "insulation",
        "household use", "gas", "electric", "portable", "automatic", "digital", "stainless steel",
        "copper", "aluminium", "pvc", "flame retardant", "cordless", "rechargeable", "solar",
        "battery operated", "pressure protection", "leakage protection", "child safety shutter"
    ]
    for feat in features:
        if feat in norm:
            attrs.append(feat)

    intel = product_intel_engine.analyze(text)

    return {
        "input": text,
        "detected_product": intel.get("detected_product") or (best.get("product") if best else None),
        "detected_category": intel.get("likely_category") or (best.get("category") if best else None),
        "classification": intel.get("classification"),
        "confidence": intel.get("confidence"),
        "attributes": list(dict.fromkeys(attrs)),
        "recommendations": matches,
        "top_standard": best,
        "next_actions": intel.get("next_actions", [])
    }

def mandatory_assessment(product: str) -> Dict[str, Any]:
    matches = find_matches(product, 1)
    if not matches:
        return {
            "found": False,
            "status": "UNKNOWN",
            "message": "No matching product found in the available BIS standards corpus. Check the official BIS Compulsory Certification directory.",
            "official_source": OFFICIAL_RESOURCES[5]["url"]
        }
    s = matches[0]
    is_mandatory = s.get("mandatory_status") == "MANDATORY"
    status = "MANDATORY UNDER QUALITY CONTROL ORDER (QCO)" if is_mandatory else "VOLUNTARY / NEEDS GAZETTE CONFIRMATION"
    explanation = (
        f"This product is covered by {s.get('qco_order', 'Statutory QCO')}. "
        f"Standard: {s.get('standard_number')}. Scheme: {s.get('scheme')}."
        if is_mandatory else
        f"The product standard {s.get('standard_number')} is currently voluntary unless mandated by a specific ministry procurement order."
    )
    return {
        "found": True,
        "product": product,
        "standard": s,
        "status": status,
        "mandatory": is_mandatory,
        "qco_order": s.get("qco_order"),
        "effective_date": s.get("effective_date"),
        "scheme": s.get("scheme"),
        "explanation": explanation,
        "official_source": s.get("official_source", OFFICIAL_RESOURCES[5]["url"])
    }

def compliance_result(product: str, checks: Dict[str, Any]) -> Dict[str, Any]:
    matches = find_matches(product, 1)
    if not matches:
        return {"found": False, "message": f"No matching product found for '{product}'."}
    s = matches[0]
    reqs = s.get("requirements", [])
    passed = []
    failed = []
    unchecked = []

    for r in reqs:
        v = checks.get(r)
        if v is True:
            passed.append(r)
        elif v is False:
            failed.append(r)
        else:
            unchecked.append(r)

    total = len(reqs)
    score = round((len(passed) / total * 100)) if total else 0
    status = "Needs Review" if failed else ("Partially Checked" if unchecked else "Compliant")
    risk = "HIGH" if (len(failed) >= 2 or score < 50) else ("MEDIUM" if (failed or unchecked or score < 80) else "LOW")

    actions = [f"Correct and re-test: '{x}'." for x in failed]
    if unchecked:
        actions.append(f"Provide objective test evidence for {len(unchecked)} unchecked requirement(s).")
    if not actions:
        actions.append("Maintain continuing factory quality conformity and periodic surveillance testing.")

    return {
        "found": True,
        "product": product,
        "standard": s,
        "score": score,
        "status": status,
        "risk": risk,
        "passed": passed,
        "failed": failed,
        "not_checked": unchecked,
        "summary": {
            "total": total,
            "passed": len(passed),
            "failed": len(failed),
            "not_checked": len(unchecked)
        },
        "recommended_actions": actions,
        "certification_steps": certification_steps(s),
        "prototype_notice": "AI-assisted screening only. Does not issue, verify, or grant BIS certification."
    }

def agent_compliance(message: str) -> Optional[Dict[str, Any]]:
    m = find_matches(message, 1)
    if not m:
        return None
    top = m[0]
    return {
        "reply": f"Found applicable standard {top.get('standard_number')} ('{top.get('title')}'). Open Compliance Center to run the requirement checklist.",
        "standard": top,
        "source": top.get("official_source") or OFFICIAL_RESOURCES[0]["url"]
    }

product_intel_engine = ProductIntelligenceEngine(bis_data, find_matches)
rag = LocalRAG(bis_data, OFFICIAL_RESOURCES, DOCS_DIR)
agent = BISExpertAgent(find_matches, rag, OFFICIAL_RESOURCES, certification_steps, agent_compliance)

# ==================== REST API ROUTES ====================

@app.route("/")
def index():
    if "text/html" in request.headers.get("Accept", ""):
        return send_from_directory(ROOT_DIR, "index.html")
    return jsonify({
        "platform": "BIS SmartGuide — Standards Intelligence Platform",
        "status": "online",
        "version": "4.0-production",
        "sih_ps": "26107"
    })

@app.route("/<path:filename>")
def static_files(filename):
    safe_path = os.path.normpath(filename)
    if safe_path.startswith("..") or safe_path.startswith("/") or safe_path.startswith("\\"):
        return jsonify({"error": "Invalid file path"}), 400
    if os.path.exists(os.path.join(ROOT_DIR, safe_path)):
        return send_from_directory(ROOT_DIR, safe_path)
    return jsonify({"error": "File not found"}), 404

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "standards_loaded": len(bis_data),
        "rag_chunks": rag.chunk_count,
        "documents_indexed": rag.document_count,
        "agent": agent.name,
        "agentic_chat": True,
        "agent_version": agent.version,
        "platform_version": "4.0",
        "database": "sqlite (smartguide.db)",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.route("/standards")
def get_standards():
    cat = request.args.get("category", "").strip().lower()
    if cat:
        filtered = [s for s in bis_data if cat in s.get("category", "").lower()]
        return jsonify({"count": len(filtered), "category": cat, "standards": filtered})
    return jsonify({"count": len(bis_data), "standards": bis_data})

@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Please provide a search query"}), 400
    results = find_matches(q, 10)
    return jsonify({"query": q, "count": len(results), "results": results})

@app.route("/recommend")
def recommend():
    q = request.args.get("product", "").strip()
    if not q:
        return jsonify({"error": "Please enter a product name or description"}), 400
    results = find_matches(q, 6)
    return jsonify({
        "found": bool(results),
        "message": None if results else "No matching BIS standard found in the catalogue.",
        "standard": results[0] if results else None,
        "recommendations": results,
        "match_score": results[0]["match_score"] if results else 0
    })

@app.route("/recommendations")
def recommendations():
    q = request.args.get("q", "").strip()
    r = find_matches(q, 5) if q else []
    return jsonify({"query": q, "recommendations": r, "count": len(r)})

@app.route("/analyze", methods=["POST"])
def analyze():
    b = request.get_json(silent=True) or {}
    d = str(b.get("description", "")).strip()
    if not d:
        return jsonify({"error": "Product description is required"}), 400
    return jsonify(detect_product_entities(d))

@app.route("/check-compliance")
def check_compliance_route():
    p = request.args.get("product", "").strip()
    if not p:
        return jsonify({"error": "Please provide a product name"}), 400
    return jsonify(compliance_result(p, {}))

@app.route("/check-product", methods=["POST"])
def check_product_route():
    b = request.get_json(silent=True) or {}
    p = str(b.get("product", "")).strip()
    checks = b.get("checks", {}) or {}
    if not p:
        return jsonify({"error": "Product name is required"}), 400
    return jsonify(compliance_result(p, checks))

@app.route("/mandatory-check")
def mandatory_check_route():
    p = request.args.get("product", "").strip()
    if not p:
        return jsonify({"error": "Please provide a product name"}), 400
    return jsonify(mandatory_assessment(p))

@app.route("/certification-guide")
def certification_guide_route():
    q = request.args.get("product", "").strip()
    m = find_matches(q, 1) if q else []
    s = m[0] if m else None
    return jsonify({
        "standard": s,
        "steps": certification_steps(s),
        "official_resources": OFFICIAL_RESOURCES[1:3],
        "notice": "Requirements vary by product, standard, QCO and scheme. Always verify current BIS gazette instructions."
    })

@app.route("/labs")
def labs_route():
    return jsonify({
        "message": "Use the authentic BIS laboratory directory and LIMS for current testing scopes.",
        "official_url": OFFICIAL_LAB_DIRECTORY,
        "lims_url": OFFICIAL_LIMS_URL,
        "lims_search": OFFICIAL_LIMS_SEARCH
    })

@app.route("/resources")
def resources_route():
    return jsonify({"resources": OFFICIAL_RESOURCES})

@app.route("/rag-search")
def rag_search_route():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Please provide a query"}), 400
    return jsonify({"query": q, "rag": True, "results": rag.retrieve(q, 8)})

@app.route("/rag-rebuild", methods=["POST"])
def rag_rebuild_route():
    global rag, agent
    rag = LocalRAG(bis_data, OFFICIAL_RESOURCES, DOCS_DIR)
    agent = BISExpertAgent(find_matches, rag, OFFICIAL_RESOURCES, certification_steps, agent_compliance)
    return jsonify({
        "success": True,
        "message": "RAG index rebuilt",
        "rag_chunks": rag.chunk_count,
        "documents_indexed": rag.document_count,
        "agent_reloaded": True,
        "agent_version": agent.version
    })

@app.route("/chat", methods=["POST"])
@app.route("/agent-chat", methods=["POST"])
def chat_route():
    b = request.get_json(silent=True) or {}
    msg = str(b.get("message", "")).strip()
    lang = b.get("language")
    role = b.get("role", "general")
    if not msg:
        return jsonify({"error": "Message is required"}), 400
    return jsonify(agent.run(msg, role=role, language=lang))

@app.route("/report", methods=["POST"])
def report_route():
    b = request.get_json(silent=True) or {}
    p = str(b.get("product", "")).strip()
    role = str(b.get("role", "general")).strip()
    if not p:
        return jsonify({"error": "Product is required"}), 400
    res = b.get("result") or compliance_result(p, {})
    rep = {
        "title": "BIS SmartGuide Compliance Assessment Report",
        "product": p,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "assessment": res,
        "sources": OFFICIAL_RESOURCES
    }
    adapted = RoleEngine.adapt_report(rep, role)
    return jsonify({"report": adapted, "printable": True})

# ==================== V8 UPGRADED PLATFORM ENDPOINTS ====================

@app.route("/v8/product-intelligence", methods=["POST"])
def v8_product_intelligence():
    b = request.get_json(silent=True) or {}
    q = str(b.get("query") or b.get("description") or b.get("product", "")).strip()
    if not q:
        return jsonify({"error": "Enter a product name or natural language description."}), 400
    return jsonify(product_intel_engine.analyze(q))

@app.route("/v8/roles", methods=["GET"])
def v8_list_roles():
    return jsonify({"roles": RoleEngine.list_roles()})

@app.route("/v8/roles/adapt", methods=["POST"])
def v8_adapt_role():
    b = request.get_json(silent=True) or {}
    role_id = b.get("role", "general")
    product = b.get("product", "")
    matches = find_matches(product, 1) if product else []
    product_info = {"product": product, "standard": matches[0] if matches else None}
    adapted_checklist = RoleEngine.adapt_checklist(product_info, role_id)
    role_cfg = RoleEngine.get_role(role_id)
    return jsonify({
        "role": role_cfg,
        "adapted_checklist": adapted_checklist
    })

@app.route("/v8/labs/search", methods=["GET"])
def v8_labs_search():
    q = request.args.get("q") or request.args.get("query")
    std = request.args.get("standard")
    dom = request.args.get("domain")
    city = request.args.get("city") or request.args.get("state")
    return jsonify(search_laboratories(query=q, standard_number=std, domain=dom, city=city))

@app.route("/v8/qco/search", methods=["GET"])
def v8_qco_search():
    q = request.args.get("q", "").strip().lower()
    matches = []
    for s in bis_data:
        if s.get("mandatory_status") == "MANDATORY":
            blob = f"{s.get('product', '')} {s.get('standard_number', '')} {s.get('title', '')} {s.get('qco_order', '')}".lower()
            if not q or q in blob:
                matches.append({
                    "standard_number": s.get("standard_number"),
                    "title": s.get("title"),
                    "product": s.get("product"),
                    "category": s.get("category"),
                    "scheme": s.get("scheme"),
                    "qco_order": s.get("qco_order"),
                    "effective_date": s.get("effective_date"),
                    "mandatory_status": "MANDATORY",
                    "official_source": s.get("official_source")
                })
    return jsonify({"count": len(matches), "qco_records": matches})

@app.route("/v8/standards/reverse", methods=["GET"])
def v8_standards_reverse():
    std_num = request.args.get("standard", "").strip().upper().replace(" ", "")
    if not std_num:
        return jsonify({"error": "Please provide a standard parameter (e.g. IS4246, IS694)"}), 400
    matched = None
    for s in bis_data:
        if std_num in s.get("standard_number", "").upper().replace(" ", ""):
            matched = s
            break
    if not matched:
        return jsonify({"found": False, "message": f"Standard '{std_num}' not found in the local repository."}), 404
    return jsonify({
        "found": True,
        "standard_number": matched.get("standard_number"),
        "title": matched.get("title"),
        "covered_product": matched.get("product"),
        "synonyms": matched.get("synonyms", []),
        "category": matched.get("category"),
        "scheme": matched.get("scheme"),
        "qco_order": matched.get("qco_order"),
        "requirements": matched.get("requirements", []),
        "testing_parameters": matched.get("testing_parameters", []),
        "related_standards": matched.get("related_standards", []),
        "official_source": matched.get("official_source")
    })

@app.route("/v8/knowledge-graph", methods=["GET"])
def v8_knowledge_graph():
    p = request.args.get("product", "gas stove").strip()
    matches = find_matches(p, 1)
    if not matches:
        return jsonify({"error": "Product not found"}), 404
    s = matches[0]

    nodes = [
        {"id": "prod", "label": s.get("product", p).title(), "type": "product", "color": "#1769e0"},
        {"id": "std", "label": s.get("standard_number", "IS"), "type": "standard", "color": "#0b2b58"},
        {"id": "scheme", "label": s.get("scheme", "Scheme I").split("(")[0].strip(), "type": "scheme", "color": "#14966a"},
        {"id": "qco", "label": "Mandatory QCO" if s.get("mandatory_status") == "MANDATORY" else "Voluntary", "type": "qco", "color": "#bd7411"}
    ]
    edges = [
        {"source": "prod", "target": "std", "label": "Governed by"},
        {"source": "std", "target": "scheme", "label": "Licensing Scheme"},
        {"source": "std", "target": "qco", "label": "Regulatory Mandate"}
    ]

    for i, req in enumerate(s.get("requirements", [])[:3]):
        req_id = f"req_{i}"
        nodes.append({"id": req_id, "label": req[:35] + ("..." if len(req) > 35 else ""), "type": "requirement", "color": "#4b6280"})
        edges.append({"source": "std", "target": req_id, "label": "Specifies"})

    for i, test in enumerate(s.get("testing_parameters", [])[:2]):
        test_id = f"test_{i}"
        nodes.append({"id": test_id, "label": test[:35] + ("..." if len(test) > 35 else ""), "type": "testing", "color": "#8b5cf6"})
        edges.append({"source": "std", "target": test_id, "label": "Prescribes"})

    nodes.append({"id": "lab", "label": "BIS Recognized Labs", "type": "laboratory", "color": "#0284c7"})
    edges.append({"source": "std", "target": "lab", "label": "Tested at"})

    return jsonify({
        "product": s.get("product"),
        "standard_number": s.get("standard_number"),
        "nodes": nodes,
        "edges": edges
    })

@app.route("/api-info")
def api_info():
    return jsonify({
        "platform": "BIS SmartGuide",
        "version": "4.0",
        "standards_count": len(bis_data),
        "supported_roles": [r["id"] for r in RoleEngine.list_roles()],
        "supported_languages": ["en", "hi", "kn", "te", "ta"],
        "endpoints": [
            "/health", "/standards", "/search", "/recommend", "/analyze",
            "/check-product", "/check-compliance", "/mandatory-check",
            "/certification-guide", "/labs", "/resources", "/rag-search",
            "/chat", "/report",
            "/v8/product-intelligence", "/v8/roles", "/v8/roles/adapt",
            "/v8/labs/search", "/v8/qco/search", "/v8/standards/reverse",
            "/v8/knowledge-graph",
            "/v4/assess", "/v4/document", "/v4/assessments", "/v4/passport/<id>",
            "/v4/analytics", "/v4/compare"
        ]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
