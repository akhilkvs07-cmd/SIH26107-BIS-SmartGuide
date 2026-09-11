"""Verified BIS LIMS laboratory router for SmartGuide."""

from urllib.parse import quote_plus
from flask import jsonify, request


def labs_match():
    from app import find_matches
    from labs_directory import OFFICIAL_LIMS_SEARCH, search_laboratories, haversine_km
    from product_guard import anchor, resolve_product
    from recognized_labs import recognized_labs_for_standard
    from bis_lims_live import search_scope

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
    if not standard and product_anchor:
        standard = product_anchor.get("standard_number", "")
    elif not standard and product:
        matches = find_matches(product, 5)
        standard = matches[0].get("standard_number", "") if matches else ""

    # First query the live BIS LIMS Search by IS Number. This is the important
    # upgrade: recognized-lab scope is no longer limited to the small curated
    # SmartGuide list. LIMS currently exposes 431 recognized laboratories.
    live = search_scope(standard, product=product, city=city, limit=50) if standard else {"results": [], "live": False}
    live_rows = live.get("results", [])

    # Keep the local BIS directory as a reliable fallback and source for the
    # 10 BIS-owned laboratories. It also provides routing coordinates.
    directory = search_laboratories(
        query=product or test,
        standard_number=standard,
        domain=domain,
        city=city,
        latitude=latitude,
        longitude=longitude,
    )
    directory_labs = directory.get("laboratories", [])
    origin_lat = directory.get("query", {}).get("latitude")
    origin_lon = directory.get("query", {}).get("longitude")

    results = []
    seen = set()

    # Live recognized-lab scope rows first.
    for row in live_rows:
        key = (row.get("lab_name", "").lower(), row.get("osl_code", "").lower())
        if key in seen:
            continue
        seen.add(key)
        item = dict(row)
        item["name"] = item.get("lab_name")
        item["scope_standard"] = item.get("standard_number") or standard
        item["scope_url"] = item.get("source_url")
        item["maps_url"] = f"https://www.google.com/maps/search/?api=1&query={quote_plus(item.get('lab_name','') + ' ' + city)}"
        item["distance_km"] = None
        item["match_reason"] = "Current BIS LIMS scope record"
        item["ranking_score"] = 100 if item.get("city_match") else 80
        results.append(item)

    # Add known BIS-owned labs as directory candidates. Never mark these as
    # scope-capable unless the live LIMS search actually returned that scope.
    live_names = {str(x.get("lab_name", "")).lower() for x in results}
    for lab in directory_labs:
        key = str(lab.get("name", "")).lower()
        if key in live_names or key in seen:
            continue
        item = dict(lab)
        item["ranking_score"] = 60
        results.append(item)

    # Retain the older curated scope records as a fallback only when live LIMS
    # is unavailable. They are not allowed to override a live LIMS response.
    if not live.get("live"):
        for lab in recognized_labs_for_standard(standard):
            item = dict(lab)
            item["scope_status"] = "LIMS_SCOPE_MATCH_FALLBACK"
            item["verification_status"] = "BIS_LIMS_SCOPE_FALLBACK"
            item["source_status"] = "CURATED_BIS_LIMS_SCOPE_RECORD"
            item["source_url"] = item.get("scope_url")
            item["maps_url"] = f"https://www.google.com/maps/search/?api=1&query={quote_plus(item.get('name','') + ' ' + item.get('city',''))}"
            item["distance_km"] = round(haversine_km(float(origin_lat), float(origin_lon), item["lat"], item["lon"]), 2) if origin_lat is not None and origin_lon is not None else None
            item["ranking_score"] = 90
            results.append(item)

    def rank(item):
        scope = 0 if str(item.get("scope_status", "")).startswith("LIMS_SCOPE_MATCH") or item.get("source_status") == "LIVE_BIS_LIMS_SCOPE_SEARCH" else 1
        city_rank = 0 if item.get("city_match") else 1
        distance = item.get("distance_km")
        return (scope, city_rank, -float(item.get("ranking_score", 0)), distance if distance is not None else 10**9, str(item.get("name", "")))

    results.sort(key=rank)
    limit_raw = request.args.get("limit", "12")
    try:
        limit = max(1, min(int(limit_raw), 50))
    except ValueError:
        limit = 12
    results = results[:limit]

    for item in results:
        item.setdefault("nabl_status", "NOT_ASSERTED_BY_SMARTGUIDE")
        item.setdefault("scope_status", "LIMS_SCOPE_MATCH" if item.get("source_status") == "LIVE_BIS_LIMS_SCOPE_SEARCH" else "VERIFY_CURRENT_SCOPE_IN_BIS_LIMS")
        item.setdefault("verification_status", "BIS_LIMS_SCOPE_FOUND" if item.get("source_status") == "LIVE_BIS_LIMS_SCOPE_SEARCH" else "DIRECTORY_VERIFIED_SCOPE_PENDING")

    lims_scope_search = f"{OFFICIAL_LIMS_SEARCH}?is_number__doc_no={quote_plus(standard)}" if standard else OFFICIAL_LIMS_SEARCH
    live_count = int(live.get("total_found", 0) or 0)
    scope_count = sum(1 for x in results if str(x.get("source_status")) == "LIVE_BIS_LIMS_SCOPE_SEARCH")

    response = {
        "status": "OK",
        "results": results,
        "labs": results,
        "data": {**directory, "laboratories": results, "count": len(results)},
        "resolved_product": normalized_product,
        "resolved_standard": product_anchor or {"standard_number": standard},
        "lims_scope_search": lims_scope_search,
        "lims_live": bool(live.get("live")),
        "lims_total_scope_matches": live_count,
        "scope_matches_returned": scope_count,
        "available_recognized_lab_universe": 431,
        "ranking_mode": "Live BIS LIMS scope first, city relevance, then routing data",
        "confidence": 0.99 if live_count else (0.95 if results else 0.0),
        "evidence": results,
        "source": "BIS LIMS live Search by IS Number + BIS LIMS BIS Labs directory",
        "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "errors": [] if live.get("live") else ["Live BIS LIMS scope lookup unavailable; fallback directory data may be shown."],
        "notice": "Scope-matched records come from the current BIS LIMS search when available. Verify exact test clauses, current validity, capacity and booking availability in BIS LIMS. SmartGuide does not assert NABL accreditation.",
    }
    return jsonify(response)
