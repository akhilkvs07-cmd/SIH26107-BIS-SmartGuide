"""Universal product-intelligence gateway for BIS SmartGuide.

This layer deliberately does not use a hardcoded allow-list. Any physical
manufactured product can be submitted. Known authoritative anchors are used
when available; otherwise the local BIS corpus is searched and only candidates
with real identity evidence are returned. Unrelated standards are never shown
just to make the result look populated.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from product_guard import anchor, resolve_product, guarded_results

BIS_KYS = "https://www.bis.gov.in/know-your-standard/?lang=en"
BIS_STANDARDS = "https://standards.bis.gov.in/"
BIS_QCO = "https://www.bis.gov.in/product-certification/products-under-compulsory-certification/?lang=en"

STOP = {
    "the", "a", "an", "for", "and", "with", "of", "to", "in", "on", "my", "our",
    "product", "device", "item", "unit", "model", "type", "please", "need", "want",
}

DOMAIN_HINTS = {
    "computer / ICT equipment": {
        "terms": {"keyboard", "mouse", "webcam", "monitor", "printer", "scanner", "speaker", "headphone", "earphone", "laptop", "tablet", "computer"},
        "note": "The product appears to be information/communication technology equipment. The exact BIS standard and regulatory category must still be confirmed for the specific product.",
    },
    "electrical appliance": {
        "terms": {"kettle", "iron", "mixer", "grinder", "heater", "fan", "oven", "microwave", "refrigerator", "washer", "toaster", "fryer"},
        "note": "The product appears to be an electrical household appliance. The exact appliance type and applicable part of the Indian Standard must be confirmed.",
    },
    "electrical / wiring product": {
        "terms": {"cable", "wire", "socket", "plug", "switch", "extension", "adapter", "charger"},
        "note": "The product appears to be an electrical/wiring product. Exact construction, rating and applicable standard must be confirmed.",
    },
    "mechanical / industrial product": {
        "terms": {"valve", "pump", "motor", "pipe", "bearing", "bracket", "fastener", "vessel", "tank", "machine"},
        "note": "The product appears to be a mechanical/industrial manufactured product. The applicable Indian Standard depends strongly on its intended use and specifications.",
    },
}


def _tokens(value: str) -> set[str]:
    return {x for x in re.sub(r"[^a-z0-9\s]", " ", str(value or "").lower()).split() if len(x) > 2 and x not in STOP}


def _category(product: str) -> tuple[str, str]:
    tokens = _tokens(product)
    for category, data in DOMAIN_HINTS.items():
        if tokens & data["terms"]:
            return category, data["note"]
    return "General manufactured product", "This is treated as a physical manufactured product, but its exact BIS classification could not be established from the current local evidence."


def _candidate_identity(query: str, candidate: Dict[str, Any]) -> bool:
    q = _tokens(query)
    if not q:
        return False
    fields = [candidate.get("product", ""), candidate.get("title", ""), candidate.get("category", ""), candidate.get("description", "")]
    for syn in candidate.get("synonyms", []) or []:
        fields.append(syn)
    text = _tokens(" ".join(map(str, fields)))
    overlap = q & text
    score = float(candidate.get("match_score", 0) or 0)
    # A candidate must have identity overlap. High numeric score alone is not
    # enough because old corpus ranking can surface an unrelated product.
    return bool(overlap) and (score >= 45 or len(overlap) >= 2)


def analyze_universal(description: str, find_matches) -> Dict[str, Any]:
    raw = str(description or "").strip()
    if not raw:
        raise ValueError("Product description is required")

    resolved = resolve_product(raw)
    exact = anchor(raw)
    category, category_note = _category(resolved)

    if exact:
        return {
            "feature": "Universal Product Intelligence",
            "status": "AUTHORITATIVE_MATCH",
            "classification": "CONFIDENTLY_RECOGNIZED",
            "input": raw,
            "resolved_product": resolved,
            "detected_product": exact.get("product"),
            "likely_category": category,
            "confidence": 0.99,
            "confidence_percentage": 99,
            "ranked_standards": [exact],
            "candidate_standards": [exact],
            "why_matched": exact.get("match_reasons", []),
            "evidence": [exact.get("source", "BIS official product schedule")],
            "next_actions": ["Review the exact standard scope", "Check current mandatory/QCO status", "Find the required testing laboratory"],
            "source": "BIS product schedule anchor",
            "notice": "AI-assisted decision support. Verify current BIS scope, amendments and QCOs before acting.",
        }

    raw_matches = find_matches(resolved, 12)
    matches = [m for m in raw_matches if _candidate_identity(resolved, m)]
    matches = guarded_results(resolved, matches, 8) if matches else []

    top = matches[0] if matches else None
    top_score = float(top.get("match_score", 0) or 0) if top else 0.0

    if top and top_score >= 75:
        confidence = min(0.95, top_score / 100.0)
        status = "CORPUS_MATCH"
        classification = "CONFIDENTLY_RECOGNIZED"
        explanation = f"The product matched the local BIS corpus with identity evidence. Top candidate: {top.get('standard_number')} — {top.get('title')}."
    elif top and top_score >= 50:
        confidence = min(0.82, 0.40 + top_score / 200.0)
        status = "RELATED_PRODUCT_REVIEW"
        classification = "RELATED_PRODUCT"
        explanation = "A related BIS standard was found, but SmartGuide will not treat it as the exact product standard without scope verification."
    else:
        matches = []
        confidence = 0.15
        status = "PHYSICAL_PRODUCT_UNRESOLVED"
        classification = "POSSIBLE_PRODUCT"
        explanation = "This appears to be a physical manufactured product, but the current local corpus does not contain enough product-specific evidence to name an applicable standard safely."

    return {
        "feature": "Universal Product Intelligence",
        "status": status,
        "classification": classification,
        "input": raw,
        "resolved_product": resolved,
        "detected_product": resolved,
        "likely_category": category,
        "confidence": round(confidence, 2),
        "confidence_percentage": int(round(confidence * 100)),
        "ranked_standards": matches,
        "candidate_standards": matches,
        "why_matched": top.get("match_reasons", [])[:5] if top else [],
        "evidence": ["local BIS standards corpus"] if top else [],
        "category_guidance": category_note,
        "explanation": explanation,
        "next_actions": [
            "Add intended use, power/rating, material and model details",
            "Search the official BIS Know Your Standard portal by product keyword",
            "Confirm any applicable QCO/compulsory certification notification",
        ],
        "official_search": BIS_KYS,
        "official_standards_portal": BIS_STANDARDS,
        "official_qco_portal": BIS_QCO,
        "needs_human_review": True,
        "notice": "No unrelated standard is substituted. Lack of a local match is a search limitation, not a certification decision.",
    }
