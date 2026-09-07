"""Upgraded Render entrypoint for BIS SmartGuide.

Loads the existing app unchanged, registers the modular V4 compliance layer,
and transparently upgrades the legacy document endpoint used by the existing
frontend so PDF/image uploads receive the deeper extraction pipeline.
"""
from flask import jsonify, request

from app import app
from compliance_upgrade import _extract_values, _get_dependencies, _read_document, register

register(app)


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


# Preserve the frontend's existing /document-analyze URL while upgrading its
# implementation. This is done before Gunicorn starts serving requests.
app.view_functions["document_analyze"] = upgraded_document_analyze
