"""Production upgrade entrypoint for BIS SmartGuide.

Keeps the existing Flask/V6 architecture and layers the V8 source-grounded
intelligence APIs on top. Existing V4/V6/V7 routes remain available.
"""

import json
import uuid
from flask import jsonify, request
from app import app, find_matches, OFFICIAL_RESOURCES
from compliance_upgrade import (
    _build_assessment, _db, _extract_values, _get_dependencies,
    _hash_evidence, _now, _read_document, register as register_compliance
)
from advanced_features import register as register_v6
from v7_platform import register_v7
from platform_v8 import register as register_v8

register_compliance(app)


def _save_assessment(result, product):
    assessment_id = "BIS-" + uuid.uuid4().hex[:10].upper()
    created_at = _now()
    evidence_hash = _hash_evidence(result.get("evidence", {}))
    result["assessment_id"] = assessment_id
    result["created_at"] = created_at
    result["evidence_hash"] = evidence_hash
    with _db() as con:
        con.execute(
            "INSERT INTO assessments VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                assessment_id, created_at, product,
                result.get("evidence", {}).get("model", ""),
                result.get("evidence", {}).get("manufacturer", ""),
                result.get("standard", {}).get("standard_number", ""),
                int(result.get("score", 0)), result.get("risk", "MEDIUM"),
                result.get("status", "REVIEW"), result.get("evidence_quality", "LOW"),
                json.dumps(result, ensure_ascii=False), evidence_hash
            )
        )
        for action in result.get("corrective_actions", []):
            con.execute(
                "INSERT INTO actions VALUES (?,?,?,?,?,?,?)",
                (uuid.uuid4().hex[:12], assessment_id,
                 action.get("requirement", ""), action.get("priority", "MEDIUM"),
                 action.get("action", ""), "OPEN", created_at)
            )
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
    return jsonify({
        "filename": name, "characters": len(text), "characters_extracted": len(text),
        "detected_product": matches[0].get("product") if matches else None,
        "recommendations": matches, "extracted_fields": extracted, "metadata": metadata,
        "missing_data_hints": [
            "Rated voltage/power/current specification",
            "Product scope, model and manufacturer details",
            "Batch test laboratory parameters and measured limits",
            "Markings: ISI / CM/L format or CRS registration R-number"
        ],
        "notice": "AI-assisted document analysis — not official BIS certification."
    })


def upgraded_check_product():
    body = request.get_json(silent=True) or {}
    product = str(body.get("product", "")).strip()
    checks = body.get("checks") or {}
    evidence = body.get("evidence") or {}
    if not product:
        return jsonify({"error": "Product name is required"}), 400
    result = _build_assessment(product, checks, evidence, str(body.get("document_text", "")))
    if not result.get("standard"):
        return jsonify(result), 404
    return jsonify(_save_assessment(result, product))


def upgraded_check_compliance():
    product = request.args.get("product", "").strip()
    if not product:
        return jsonify({"error": "Please provide a product name"}), 400
    return jsonify(_build_assessment(product, {}, {}, ""))


app.view_functions["document_analyze"] = upgraded_document_analyze
app.view_functions["check_product_route"] = upgraded_check_product
app.view_functions["check_compliance_route"] = upgraded_check_compliance

register_v6(app, find_matches)
register_v7(app, find_matches)
register_v8(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
