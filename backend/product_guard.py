"""Deterministic product-identity guard for the Universal BIS Agent.

Gemini may orchestrate tools, but it must never silently replace the user's
product with a nearby product that happens to share a standard.
"""

import re
from typing import Any, Dict, List

PRODUCT_ALIASES = {
    "keyboard": "keyboard",
    "computer keyboard": "keyboard",
    "pc keyboard": "keyboard",
    "desktop keyboard": "keyboard",
    "wired keyboard": "keyboard",
    "usb keyboard": "keyboard",
    "mechanical keyboard": "keyboard",
    "gaming keyboard": "keyboard",
    "laptop keyboard": "keyboard",
    "wireless keyboard": "wireless keyboard",
    "bluetooth keyboard": "wireless keyboard",
}

# Conservative authoritative mappings for products explicitly present in the
# current BIS CRS schedule. These are identity anchors, not a replacement for
# the local corpus or official BIS evidence.
BIS_PRODUCT_ANCHORS = {
    "keyboard": {
        "product": "Keyboard",
        "standard_number": "IS/IEC 62368: Part 1: 2023",
        "title": "Audio/Video, Information and Communication Technology Equipment – Part 1 Safety Requirements",
        "scheme": "Scheme II (Compulsory Registration Scheme - CRS)",
        "mandatory": True,
        "source": "BIS Scheme-II Registration Scheme",
    },
    "wireless keyboard": {
        "product": "Wireless Keyboards",
        "standard_number": "IS/IEC 62368: Part 1: 2023",
        "title": "Audio/Video, Information and Communication Technology Equipment – Part 1 Safety Requirements",
        "scheme": "Scheme II (Compulsory Registration Scheme - CRS)",
        "mandatory": True,
        "source": "BIS Scheme-II Registration Scheme",
    },
}


def normalize(text: Any) -> str:
    text = str(text or "").lower().replace("-", " ")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", text)).strip()


def resolve_product(query: str) -> str:
    q = normalize(query)
    return PRODUCT_ALIASES.get(q, q)


def anchor(query: str) -> Dict[str, Any] | None:
    item = BIS_PRODUCT_ANCHORS.get(resolve_product(query))
    if not item:
        return None
    result = dict(item)
    result["match_score"] = 100
    result["raw_match_score"] = 1000
    result["support_level"] = "authoritative_product_schedule"
    result["match_reasons"] = [
        f"Exact product identity: {result['product']}",
        f"BIS compulsory-product schedule: {result['scheme']}",
    ]
    return result


def identity_matches(query: str, candidate: Dict[str, Any]) -> bool:
    """Reject candidates that are clearly a different named product."""
    q = resolve_product(query)
    product = normalize(candidate.get("product", ""))
    if q in BIS_PRODUCT_ANCHORS:
        expected = normalize(BIS_PRODUCT_ANCHORS[q]["product"])
        return expected == product
    if not product:
        return True
    q_words = set(q.split())
    p_words = set(product.split())
    # For multi-word descriptions, require meaningful overlap; do not allow a
    # merely shared category such as 'laptop' to answer a 'keyboard' question.
    if q_words and p_words and q_words.intersection(p_words):
        return True
    return q == product


def guarded_results(query: str, results: List[Dict[str, Any]], limit: int = 8) -> List[Dict[str, Any]]:
    exact = anchor(query)
    if exact:
        compatible = [r for r in results if identity_matches(query, r)]
        return [exact] + compatible[: max(0, limit - 1)]
    return [r for r in results if identity_matches(query, r)][:limit]
