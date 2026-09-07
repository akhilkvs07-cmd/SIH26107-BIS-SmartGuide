"""Upgraded Render entrypoint for BIS SmartGuide.

Loads the existing app unchanged, registers the modular V4 compliance layer,
and transparently upgrades the legacy document/compliance endpoints used by
the existing frontend.
"""
import json
import uuid

from flask import jsonify, request

from app import app
from compliance_upgrade import (
    _build_assessment,
    _db,
    _extract_values,
    _get_dependencies,
    _hash_evidence,
    _now,
    _read_document,
    register,
)

register(app)


def _save_assessment(result, product):
    assessment_id = "BIS-" + uuid.uuid4().hex[:10].upper()
    created_at = _now()
    evidence_hash = _hash_evidence(result.get("evidence", {}))
    result["assessment_id"] = assessment_id
    result["created_at"] = created_at
    result["evidence_hash"] = evidence_hash
    with _db() as con:
        con.execute(
            "INSERT INTO assessments VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                assessment_id,
                created_at,
                product,
                result.get("evidence", {}).get("model"),
                result.get("evidence", {}).get("manufacturer"),
                result.get("standard", {}).get("standard_number"),
                int(result.get("score", 0)),
                result.get("risk", "MEDIUM"),
                result.get("status", "REVIEW"),
                result.get("evidence_quality", "LOW"),
                json.dumps(result, ensure_ascii=False),
                evidence_hash,
            ),
        )
        for action in result.get("corrective_actions", []):
            con.execute(
                "INSERT INTO actions VALUES (?,?,?,?,?,?,?)",
                (
                    uuid.uuid4().hex[:12],
                    assessment_id,
                    action["requirement"],
                    action["priority"],
                    action["action"],
                    "OPEN",
                    created_at,
                ),
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

    matches = []
    if text.strip():
        _, _, find_matches = _get_dependencies()
        matches = find_matches(text[:12000], 5)

    extracted = _extract_values(text)
    return jsonify({
        "filename": name,
        "characters": len(text),
        "characters_extracted": len(text),
        "detected_product": matches[0].get("product") if matches else None,
        "recommendations": matches,
        "extracted_fields": extracted,
        "metadata": metadata,
        "missing_data_hints": [
            "Rated voltage/power where applicable",
            "Product scope and model/variant",
            "Applicable test evidence",
            "Manufacturer and factory details",
        ],
        "notice": "AI-assisted prototype document analysis. It does not certify a product.",
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
    result = _build_assessment(product, {}, {}, "")
    return jsonify(result)


# Preserve the existing frontend URLs while upgrading their implementations.
app.view_functions["document_analyze"] = upgraded_document_analyze
app.view_functions["check_product"] = upgraded_check_product
app.view_functions["check_compliance"] = upgraded_check_compliance
