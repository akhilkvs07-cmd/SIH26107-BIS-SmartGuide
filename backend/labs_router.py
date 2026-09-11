"""Verified BIS LIMS laboratory router for the SmartGuide deployment.

This adapter deliberately sits above the older v8 route so the public API can
accept coordinates without rewriting the rest of platform_v8.py.
"""

from urllib.parse import quote_plus

from flask import jsonify, request


def labs_match():
    from app import find_matches
    from labs_directory import OFFICIAL_LIMS_SEARCH, search_laboratories
    from product_guard import anchor, resolve_product

    product = request.args.get("product", "").strip()
    standard = request.args.get("standard", "").strip()
    test = request.args.get("test", "").strip()
    city = request.args.get("city", "").strip()
    domain = request.args.get("domain", "").strip() or test
    lat_raw = request.args.get("lat", "").strip()
    lon_raw = request.args.get("lon", "").strip()

    try:
        latitude = float(lat_raw) if lat_raw else None
        longitude = float(lon_raw) if lon_raw else None
    except ValueError:
        return jsonify({"status": "ERROR", "error": "lat and lon must be numeric."}), 400

    normalized_product = resolve_product(product) if product else ""
    product_anchor = anchor(product) if product else None

    # Product identity has priority over generic corpus ranking. This prevents
    # a query such as "keyboard" from being silently mapped to an unrelated IS.
    if not standard and product_anchor:
        standard = product_anchor.get("standard_number", "")
    elif not standard and product:
        matches = find_matches(product, 5)
        standard = matches[0].get("standard_number", "") if matches else ""

    data = search_laboratories(
        query=product or test,
        standard_number=standard,
        domain=domain,
        city=city,
        latitude=latitude,
        longitude=longitude,
    )
    labs = data.get("laboratories", [])
    lims_scope_search = (
        f"{OFFICIAL_LIMS_SEARCH}?is_number__doc_no={quote_plus(standard)}"
        if standard else OFFICIAL_LIMS_SEARCH
    )

    response = {
        "status": "OK",
        # Keep multiple aliases so older and newer SmartGuide frontends can
        # consume the same trusted result shape.
        "results": labs,
        "labs": labs,
        "data": data,
        "resolved_product": normalized_product,
        "resolved_standard": product_anchor or {"standard_number": standard},
        "lims_scope_search": lims_scope_search,
        "confidence": 0.95 if labs else 0.0,
        "evidence": labs,
        "source": "BIS LIMS BIS Labs directory",
        "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "errors": [],
        "notice": "SmartGuide does not assert NABL accreditation, test capability, capacity or turnaround time without evidence. Confirm the exact IS number/test scope in BIS LIMS before booking.",
    }
    return jsonify(response)
