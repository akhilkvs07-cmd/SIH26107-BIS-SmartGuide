"""Verified BIS LIMS laboratory router for the SmartGuide deployment.

This adapter deliberately sits above the older v8 route so the public API can
accept coordinates without rewriting the rest of platform_v8.py.
"""

from flask import jsonify, request


def labs_match():
    from app import find_matches
    from labs_directory import search_laboratories

    product = request.args.get("product", "").strip()
    standard = request.args.get("standard", "").strip()
    test = request.args.get("test", "").strip()
    city = request.args.get("city", "").strip()
    domain = request.args.get("domain", "").strip()
    lat_raw = request.args.get("lat", "").strip()
    lon_raw = request.args.get("lon", "").strip()

    try:
        latitude = float(lat_raw) if lat_raw else None
        longitude = float(lon_raw) if lon_raw else None
    except ValueError:
        return jsonify({"status": "ERROR", "error": "lat and lon must be numeric."}), 400

    if not standard and product:
        matches = find_matches(product, 1)
        standard = matches[0].get("standard_number", "") if matches else ""

    data = search_laboratories(
        query=test or product,
        standard_number=standard,
        domain=domain,
        city=city,
        latitude=latitude,
        longitude=longitude,
    )
    labs = data.get("laboratories", [])
    return jsonify({
        "status": "OK",
        "data": data,
        "confidence": 0.95 if labs else 0.0,
        "evidence": labs,
        "source": "BIS LIMS BIS Labs directory",
        "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "errors": [],
        "notice": "SmartGuide does not assert NABL accreditation, test capability, capacity or turnaround time without evidence. Confirm the exact IS number/test scope in BIS LIMS before booking.",
    })
