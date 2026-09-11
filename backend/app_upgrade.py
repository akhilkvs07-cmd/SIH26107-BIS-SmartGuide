"""Production upgrade entrypoint for BIS SmartGuide.

Keeps the existing Flask architecture and layers the source-grounded
intelligence APIs on top. The universal agent uses Gemini's free API tier when
configured and falls back to the proven local BIS agent when it is unavailable.
"""

import json
import uuid
from urllib.parse import quote_plus
from flask import jsonify, request
from app import app, find_matches, OFFICIAL_RESOURCES, certification_steps, mandatory_assessment, OFFICIAL_LAB_DIRECTORY, OFFICIAL_LIMS_URL, OFFICIAL_LIMS_SEARCH, rag, agent
from compliance_upgrade import (
    _build_assessment, _db, _extract_values, _get_dependencies,
    _hash_evidence, _now, _read_document, register as register_compliance
)
from advanced_features import register as register_v6
from v7_platform import register_v7
import platform_v8
from platform_v8 import register as register_v8
from gemini_bis_agent import GeminiBISAgent
from labs_router import labs_match as verified_labs_match
from product_guard import anchor, resolve_product
from universal_product_v2 import analyze_universal
from universal_feature_bridge import install_universal_feature_bridge

register_compliance(app)


def _save_assessment(result, product):
    assessment_id = "BIS-" + uuid.uuid4().hex[:10].upper()
    created_at = _now()
    evidence_hash = _hash_evidence(result.get("evidence", {}))
    result["assessment_id"] = assessment_id
    result["created_at"] = created_at
    result["evidence_hash"] = evidence_hash
    with _db() as con:
        con.execute("INSERT INTO assessments VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (assessment_id, created_at, product, result.get("evidence", {}).get("model", ""), result.get("evidence", {}).get("manufacturer", ""), result.get("standard", {}).get("standard_number", ""), int(result.get("score", 0)), result.get("risk", "MEDIUM"), result.get("status", "REVIEW"), result.get("evidence_quality", "LOW"), json.dumps(result, ensure_ascii=False), evidence_hash))
        for action in result.get("corrective_actions", []):
            con.execute("INSERT INTO actions VALUES (?,?,?,?,?,?,?)", (uuid.uuid4().hex[:12], assessment_id, action.get("requirement", ""), action.get("priority", "MEDIUM"), action.get("action", ""), "OPEN", created_at))
    return result


def upgraded_document_analyze():
    file_storage = request.files.get("file")
    if not file_storage:
        return jsonify({"error": "Upload a TXT, MD, JSON, PDF or image file."}), 400
    try:
        name, text, metadata = _read_document(file_storage)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": "Document extraction failed.", "details": str(exc)}), 422
    matches = find_matches(text[:12000], 5) if text.strip() else []
    extracted = _extract_values(text)
    return jsonify({"filename": name, "characters": len(text), "characters_extracted": len(text), "detected_product": matches[0].get("product") if matches else None, "recommendations": matches, "extracted_fields": extracted, "metadata": metadata, "missing_data_hints": ["Rated voltage/power/current specification", "Product scope, model and manufacturer details", "Batch test laboratory parameters and measured limits", "Markings: ISI / CM/L format or CRS registration R-number"], "notice": "AI-assisted document analysis — not official BIS certification."})


def upgraded_check_product():
    body = request.get_json(silent=True) or {}; product = str(body.get("product", "")).strip(); checks = body.get("checks") or {}; evidence = body.get("evidence") or {}
    if not product: return jsonify({"error": "Product name is required"}), 400
    result = _build_assessment(product, checks, evidence, str(body.get("document_text", "")))
    if not result.get("standard"): return jsonify(result), 404
    return jsonify(_save_assessment(result, product))


def upgraded_check_compliance():
    product = request.args.get("product", "").strip()
    if not product: return jsonify({"error": "Please provide a product name"}), 400
    return jsonify(_build_assessment(product, {}, {}, ""))


app.view_functions["document_analyze"] = upgraded_document_analyze
app.view_functions["check_product_route"] = upgraded_check_product
app.view_functions["check_compliance_route"] = upgraded_check_compliance

register_v6(app, find_matches)
register_v7(app, find_matches)
register_v8(app)

app.view_functions["v8_product_intelligence"] = platform_v8.product_intelligence

# Advanced Features product screening uses the same universal identity gateway
# as the rest of SmartGuide. It accepts arbitrary physical products, but never
# fabricates a standard when the local evidence is insufficient.
def universal_v5_product_intelligence():
    body = request.get_json(silent=True) or {}
    description = str(body.get("description") or body.get("product") or body.get("query") or "").strip()
    if not description:
        return jsonify({"error": "Product description is required"}), 400
    try:
        return jsonify(analyze_universal(description, find_matches))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": "Universal product analysis failed", "details": str(exc)[:240]}), 500

app.view_functions["v5_product_intelligence"] = universal_v5_product_intelligence

# Replace the older local-snapshot laboratory view with the verified BIS LIMS
# directory + Haversine router. This keeps all other v8 routes untouched.
app.view_functions["v8_labs_search"] = verified_labs_match

# Every Advanced Feature now shares the same universal product-intelligence
# gateway. Feature-specific logic remains intact, but product identity,
# category, evidence, and safe-standard matching come from one common layer.
install_universal_feature_bridge(app, find_matches)


@app.get("/v8/compliance/passport")
def v8_compliance_passport():
    assessment_id = request.args.get("assessment_id", "").strip()
    if not assessment_id:
        return jsonify({"status": "ERROR", "error": "assessment_id is required", "notice": platform_v8.NOTICE}), 400
    with _db() as con:
        row = con.execute("SELECT * FROM assessments WHERE id=?", (assessment_id,)).fetchone()
        if not row:
            return jsonify({"status": "NOT_FOUND", "error": "Assessment not found", "notice": platform_v8.NOTICE}), 404
        actions = con.execute("SELECT * FROM actions WHERE assessment_id=? ORDER BY created_at", (assessment_id,)).fetchall()
    result = json.loads(row["result_json"])
    return jsonify({"status": "OK", "data": {"passport_id": "PASS-" + assessment_id, "assessment_id": assessment_id, "product": row["product"], "model": row["model"], "manufacturer": row["manufacturer"], "standard_number": row["standard_number"], "status": row["status"], "risk": row["risk"], "score": row["score"], "evidence_hash": row["evidence_hash"], "evidence": result.get("evidence", {}), "corrective_actions": [dict(a) for a in actions], "created_at": row["created_at"]}, "confidence": result.get("confidence", 0), "evidence": result.get("evidence", {}), "source": "SmartGuide assessment history", "timestamp": _now(), "errors": [], "notice": platform_v8.NOTICE})


# ---------------------------------------------------------------------------
# Universal AI Agent layer — Gemini free tier
# ---------------------------------------------------------------------------

def _agent_compliance_lookup(product: str):
    result = _build_assessment(product, {}, {}, "")
    if result.get("standard"):
        return result
    return mandatory_assessment(product)


def _agent_certification_lookup(product: str):
    resolved = resolve_product(product)
    exact = anchor(product)
    matches = [exact] if exact else find_matches(resolved, 1)
    standard = matches[0] if matches else None
    return {
        "product": resolved,
        "standard": standard,
        "steps": certification_steps(standard),
        "official_resources": OFFICIAL_RESOURCES[1:3],
        "notice": "Requirements vary by product, standard, QCO and scheme. Verify current BIS instructions.",
    }


def _agent_lab_lookup(product: str):
    resolved = resolve_product(product)
    exact = anchor(product)
    standard = exact.get("standard_number", "") if exact else ""
    if not standard:
        matches = find_matches(resolved, 1)
        standard = matches[0].get("standard_number", "") if matches else ""
    return {
        "product": resolved,
        "standard": standard,
        "message": "Use the authentic BIS LIMS laboratory directory and IS-specific scope search to confirm current testing scope and availability.",
        "official_url": OFFICIAL_LAB_DIRECTORY,
        "lims_url": OFFICIAL_LIMS_URL,
        "lims_search": f"{OFFICIAL_LIMS_SEARCH}?is_number__doc_no={quote_plus(standard)}" if standard else OFFICIAL_LIMS_SEARCH,
        "trust_boundary": "SmartGuide does not invent laboratory capabilities or test reports. Distance alone does not prove testing scope.",
    }


gemini_bis_agent = GeminiBISAgent(
    find_matches=find_matches,
    rag_retrieve=lambda query, limit=10: rag.retrieve(query, limit),
    compliance_lookup=_agent_compliance_lookup,
    certification_lookup=_agent_certification_lookup,
    lab_lookup=_agent_lab_lookup,
)


def universal_chat_route():
    b = request.get_json(silent=True) or {}
    msg = str(b.get("message", "")).strip()
    lang = b.get("language")
    role = b.get("role", "general")
    if not msg:
        return jsonify({"error": "Message is required"}), 400
    if gemini_bis_agent.enabled:
        try:
            return jsonify(gemini_bis_agent.run(msg, role=role, language=lang))
        except Exception as exc:
            fallback = agent.run(msg, role=role, language=lang)
            fallback["agent_runtime"] = "local-fallback"
            fallback["agent_fallback_reason"] = str(exc)[:240]
            return jsonify(fallback)
    fallback = agent.run(msg, role=role, language=lang)
    fallback["agent_runtime"] = "local-fallback"
    return jsonify(fallback)


app.view_functions["chat_route"] = universal_chat_route
