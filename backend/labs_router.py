"""Verified BIS LIMS laboratory router for the SmartGuide deployment."""

from urllib.parse import quote_plus
from flask import jsonify, request


def labs_match():
    from app import find_matches
    from labs_directory import OFFICIAL_LIMS_SEARCH, search_laboratories, haversine_km
    from product_guard import anchor, resolve_product
    from recognized_labs import recognized_labs_for_standard

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

    # Product identity has priority over generic corpus ranking.
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

    # Add recognized laboratories only when the requested standard is present
    # in their BIS LIMS scope record. Proximity alone never creates a capability
    # claim.
    scope_labs = recognized_labs_for_standard(standard)
    origin_lat = data.get("query", {}).get("latitude")
    origin_lon = data.get("query", {}).get("longitude")
    existing_ids = {str(x.get("id")) for x in labs}
    for lab in scope_labs:
        if lab["id"] in existing_ids:
            continue
        item = dict(lab)
        item["match_score"] = 100
        item["scope_status"] = "LIMS_SCOPE_MATCH"
        item["verification_status"] = "BIS_LIMS_SCOPE_FOUND"
        item["source_status"] = "BIS_LIMS_RECOGNIZED_SCOPE"
        item["nabl_status"] = "NOT_ASSERTED_BY_SMARTGUIDE"
        item["source_url"] = item["scope_url"]
        item["maps_url"] = f"https://www.google.com/maps/dir/?api=1&destination={item['lat']},{item['lon']}"
        item["distance_km"] = round(haversine_km(float(origin_lat), float(origin_lon), item["lat"], item["lon"]), 2) if origin_lat is not None and origin_lon is not None else None
        labs.append(item)

    # Suitable (scope-matched) laboratories first, then nearby official BIS
    # directory records whose scope still needs verification.
    labs.sort(key=lambda x: (0 if x.get("scope_status") == "LIMS_SCOPE_MATCH" else 1, x.get("distance_km") if x.get("distance_km") is not None else 10**9))
    labs = labs[:12]
    data["laboratories"] = labs
    data["count"] = len(labs)
    data["ranking_mode"] = "LIMS scope match first, then Haversine proximity"

    lims_scope_search = (
        f"{OFFICIAL_LIMS_SEARCH}?is_number__doc_no={quote_plus(standard)}"
        if standard else OFFICIAL_LIMS_SEARCH
    )

    response = {
        "status": "OK",
        "results": labs,
        "labs": labs,
        "data": data,
        "resolved_product": normalized_product,
        "resolved_standard": product_anchor or {"standard_number": standard},
        "lims_scope_search": lims_scope_search,
        "confidence": 0.98 if scope_labs else (0.95 if labs else 0.0),
        "evidence": labs,
        "source": "BIS LIMS BIS Labs directory + BIS LIMS recognized-lab scope records",
        "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "errors": [],
        "notice": "Scope-matched records are based on BIS LIMS scope pages. Verify exact test clauses, current validity, capacity and booking availability in BIS LIMS before sending samples. SmartGuide does not assert NABL accreditation.",
    }
    return jsonify(response)
