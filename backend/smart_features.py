"""BIS SmartGuide 2.0 feature helpers.

These helpers are deliberately conservative: they never claim that a local
prototype result is an official BIS certification decision.
"""
import json, math, os, re, struct
from datetime import datetime, timezone

REPORT_FILE = "smartguide_reports.json"


def _utc():
    return datetime.now(timezone.utc).isoformat()


def verify_cm_license(value):
    raw = str(value or "").strip().upper()
    digits = re.sub(r"[^0-9]", "", raw)
    valid_format = len(digits) == 7
    return {
        "input": value,
        "normalized": digits,
        "format_valid": valid_format,
        "status": "FORMAT_VALIDATION_ONLY" if valid_format else "INVALID_FORMAT",
        "message": "The CM/L format looks valid. Confirm the active licence and exact product scope using the official BIS verification service." if valid_format else "Expected a 7-digit CM/L number for this prototype validator.",
        "official_verification": "https://www.bis.gov.in/",
        "authority": "Official BIS source required for licence status"
    }


def save_report(product, assessment, sources=None):
    path = os.path.join(os.path.dirname(__file__), REPORT_FILE)
    try:
        items = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else []
        if not isinstance(items, list): items = []
    except Exception:
        items = []
    report = {"id": f"R-{datetime.now().strftime('%Y%m%d%H%M%S%f')}", "product": product, "created_at": _utc(), "assessment": assessment, "sources": sources or []}
    items.insert(0, report)
    with open(path, "w", encoding="utf-8") as f: json.dump(items[:100], f, ensure_ascii=False, indent=2)
    return report


def load_reports():
    path = os.path.join(os.path.dirname(__file__), REPORT_FILE)
    if not os.path.exists(path): return []
    try:
        data = json.load(open(path, encoding="utf-8")); return data if isinstance(data, list) else []
    except Exception:
        return []


def _stl_vertices(raw):
    # Binary STL: 80-byte header + uint32 triangle count + 50 bytes/triangle.
    if len(raw) >= 84:
        count = struct.unpack_from("<I", raw, 80)[0]
        if 84 + 50 * count <= len(raw) and count > 0:
            for i in range(count):
                off = 84 + i * 50 + 12
                for j in range(3): yield struct.unpack_from("<fff", raw, off + j * 12)
            return
    text = raw.decode("utf-8", "ignore")
    for m in re.finditer(r"vertex\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)", text, re.I):
        yield tuple(float(x) for x in m.groups())


def scan_stl(raw, filename="model.stl"):
    verts = list(_stl_vertices(raw))
    if not verts:
        return {"filename": filename, "success": False, "message": "No STL vertices could be parsed."}
    xs, ys, zs = zip(*verts)
    dims = {"x": round(max(xs)-min(xs), 3), "y": round(max(ys)-min(ys), 3), "z": round(max(zs)-min(zs), 3)}
    volume = round(dims["x"] * dims["y"] * dims["z"], 3)
    standards = {"IS 15652:2006": "Electrical Insulation Mats", "IS 1363:2002": "Hexagon Head Bolts", "IS 4984:2016": "HDPE Pipes"}
    return {"filename": filename, "success": True, "vertex_count": len(verts), "bounding_dimensions": dims, "bounding_box_volume": volume, "candidate_standards": [{"standard_number": k, "scope": v} for k,v in standards.items()], "status": "DIMENSIONAL_SCREENING_ONLY", "notice": "CAD dimensions are a prototype screening aid. Exact conformity requires the applicable BIS standard, tolerances and validated measurement method."}


def update_summary(query, rag_results):
    return {"query": query, "checked_at": _utc(), "live_bis_crawl": False, "status": "SOURCE_CHECK_REQUIRED", "changes_found": [], "evidence": rag_results[:5], "message": "SmartGuide does not invent Gazette amendments. Add verified BIS/Gazette documents to the local knowledge base, then rebuild RAG to compare them."}
