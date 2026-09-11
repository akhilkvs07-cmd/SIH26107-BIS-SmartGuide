"""Universal product context bridge for every SmartGuide advanced feature.

The product-intelligence gateway is the common identity layer. Feature-specific
workflows still perform their own task (mark screening, report parsing, labs,
STL geometry, etc.), but whenever a product is supplied they receive the same
universal product analysis. No feature is allowed to invent a standard merely
because its local workflow has a product-shaped input.
"""
from __future__ import annotations

from typing import Any, Dict
from flask import jsonify, request

from advanced_features import (
    verify_mark,
    label_check,
    test_report,
    lab_match,
    amendment_impact,
    stl_scan,
    procurement,
    issue_report,
)
from universal_product_v2 import analyze_universal


def _context(product: str, find_matches) -> Dict[str, Any]:
    product = str(product or "").strip()
    if not product:
        return {
            "feature": "Universal Product Intelligence",
            "status": "PRODUCT_NOT_PROVIDED",
            "classification": "AWAITING_PRODUCT_CONTEXT",
            "message": "Add the product or component name to connect this workflow to universal product intelligence.",
        }
    analysis = analyze_universal(product, find_matches)
    # Keep the cross-feature payload useful without duplicating the complete
    # workflow response inside every result.
    return {
        "status": analysis.get("status"),
        "classification": analysis.get("classification"),
        "input": analysis.get("input"),
        "resolved_product": analysis.get("resolved_product"),
        "detected_product": analysis.get("detected_product"),
        "likely_category": analysis.get("likely_category"),
        "confidence": analysis.get("confidence"),
        "ranked_standards": analysis.get("ranked_standards", [])[:5],
        "evidence": analysis.get("evidence", []),
        "next_actions": analysis.get("next_actions", []),
        "notice": analysis.get("notice"),
    }


def _attach(result: Dict[str, Any], product: str, find_matches) -> Dict[str, Any]:
    result["universal_product_context"] = _context(product, find_matches)
    result["universal_product_gateway"] = {
        "enabled": True,
        "role": "common product identity and BIS evidence layer",
        "policy": "Any physical manufactured product may be submitted; unsupported products remain unresolved rather than receiving an unrelated standard.",
    }
    return result


def install_universal_feature_bridge(app, find_matches) -> None:
    """Replace v5 feature views with product-aware wrappers after route setup."""

    def wrap_json(view, product_field="product"):
        def wrapped():
            body = request.get_json(silent=True) or {}
            result = view(body)
            return jsonify(_attach(result, body.get(product_field, ""), find_matches))
        return wrapped

    def wrapped_product():
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

    def wrapped_lab():
        args = request.args.to_dict()
        try:
            result = lab_match(args, find_matches)
            return jsonify(_attach(result, args.get("product", ""), find_matches))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception as exc:
            return jsonify({"error": "Workflow failed", "details": str(exc)[:240]}), 500

    def wrapped_stl():
        f = request.files.get("file")
        if not f:
            return jsonify({"error": "Upload an STL file"}), 400
        try:
            body = request.form.to_dict()
            result = stl_scan(f, request.form)
            return jsonify(_attach(result, body.get("product", ""), find_matches))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception as exc:
            return jsonify({"error": "STL scan failed", "details": str(exc)[:240]}), 500

    app.view_functions["v5_product_intelligence"] = wrapped_product
    app.view_functions["v5_verify_mark"] = wrap_json(verify_mark)
    app.view_functions["v5_label_check"] = wrap_json(label_check)
    app.view_functions["v5_test_report"] = wrap_json(test_report)
    app.view_functions["v5_lab_match"] = wrapped_lab
    app.view_functions["v5_amendment_impact"] = wrap_json(amendment_impact)
    app.view_functions["v5_stl_scan"] = wrapped_stl
    app.view_functions["v5_procurement"] = wrap_json(procurement)
    app.view_functions["v5_issue_report"] = wrap_json(issue_report)
