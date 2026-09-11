"""Universal deterministic product-identity guard for BIS SmartGuide.

The guard protects product identity without turning the product catalogue into a
hardcoded allow-list. Explicit BIS schedule anchors are optional boosts; every
other physical product is passed through to the SmartGuide corpus/RAG for
investigation.
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

# These are authoritative anchors for products explicitly present in the
# current BIS CRS schedule. They do NOT limit discovery of other products.
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

# Conversational wrappers are removed so questions such as "what standard
# applies to a pressure cooker" search for the product itself.
_QUERY_WRAPPERS = [
    r"^what\s+(?:bis\s+)?(?:requirements?|standards?)\s+(?:apply|applies)\s+to\s+",
    r"^what\s+(?:bis\s+)?(?:requirements?|standards?)\s+(?:do\s+i\s+need\s+for)\s+",
    r"^what\s+(?:bis\s+)?(?:standard|is)\s+(?:applies\s+to|for)\s+",
    r"^tell\s+me\s+(?:about|the\s+bis\s+requirements\s+for)\s+",
    r"^i\s+(?:want|plan)\s+to\s+(?:manufacture|make|import|sell)\s+",
    r"^i\s+(?:manufacture|make|import|sell)\s+",
]


def normalize(text: Any) -> str:
    text = str(text or "").lower().replace("-", " ")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", text)).strip()


def resolve_product(query: str) -> str:
    q = normalize(query)
    # Repeatedly remove common conversational wrappers, but never require the
    # remaining product to be present in a hardcoded dictionary.
    for _ in range(2):
        changed = False
        for pattern in _QUERY_WRAPPERS:
            new_q = re.sub(pattern, "", q).strip()
            if new_q != q:
                q = new_q
                changed = True
        if not changed:
            break
    q = re.sub(r"\s+(?:please|thanks?)\s*$", "", q).strip()
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


def _candidate_text(candidate: Dict[str, Any]) -> str:
    values = [
        candidate.get("product", ""),
        candidate.get("title", ""),
        candidate.get("category", ""),
        candidate.get("description", ""),
        " ".join(candidate.get("synonyms", []) or []),
    ]
    return normalize(" ".join(str(v) for v in values))


def identity_matches(query: str, candidate: Dict[str, Any]) -> bool:
    """Keep relevant corpus candidates while rejecting obvious product swaps.

    Unknown products are NOT rejected merely because they are not in this file.
    The local BIS corpus remains the discovery source for those products.
    """
    q = resolve_product(query)
    if not q:
        return False

    candidate_product = normalize(candidate.get("product", ""))
    if not candidate_product:
        return True

    # For explicit anchors, prevent a related product from replacing the exact
    # requested product (e.g. laptop replacing keyboard).
    if q in BIS_PRODUCT_ANCHORS:
        expected = normalize(BIS_PRODUCT_ANCHORS[q]["product"])
        if expected == candidate_product:
            return True
        return q in _candidate_text(candidate)

    q_tokens = {t for t in q.split() if len(t) > 2}
    text = _candidate_text(candidate)
    if q == candidate_product or q in candidate_product or candidate_product in q:
        return True

    # Synonym/title/category matches are valid discovery evidence for products
    # that have not been hardcoded in this guard.
    if any(token in text.split() for token in q_tokens):
        return True
    if q_tokens and all(token in text for token in q_tokens):
        return True
    return False


def guarded_results(query: str, results: List[Dict[str, Any]], limit: int = 8) -> List[Dict[str, Any]]:
    exact = anchor(query)
    compatible = [r for r in results if identity_matches(query, r)]
    if exact:
        # Avoid duplicate anchor if the corpus already contains the same record.
        compatible = [r for r in compatible if normalize(r.get("product", "")) != normalize(exact["product"])]
        return [exact] + compatible[: max(0, limit - 1)]
    return compatible[:limit]
