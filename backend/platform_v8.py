from __future__ import annotations

import hashlib
import io
import json
import os
import re
import sqlite3
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Dict, List

from flask import Blueprint, jsonify, request, send_file

bp = Blueprint("platform_v8", __name__, url_prefix="/v8")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "smartguide.db")
MAX_FILE_BYTES = int(os.getenv("SMARTGUIDE_MAX_FILE_BYTES", str(10 * 1024 * 1024)))

NOTICE = "BIS SmartGuide is an information and decision-support platform and does not itself grant BIS certification."
UNVERIFIED = "Live official verification is unavailable in this deployment."

ROLES = {
    "consumer": {"title": "Consumer", "focus": ["mark verification", "product safety", "complaints", "simple guidance"]},
    "manufacturer_msme": {"title": "Manufacturer / MSME", "focus": ["product-to-standard mapping", "QCO", "testing", "documents", "corrective actions"]},
    "startup": {"title": "Startup", "focus": ["prototype safety", "standard discovery", "testing roadmap", "market-entry checks"]},
    "importer": {"title": "Importer", "focus": ["product scope", "QCO", "foreign manufacturer route", "documentation"]},
    "procurement": {"title": "Procurement", "focus": ["vendor due diligence", "CM/L screening", "test evidence", "purchase controls"]},
    "compliance_pro": {"title": "Compliance Professional", "focus": ["evidence trail", "QCO", "amendments", "audit history"]},
    "laboratory": {"title": "Testing Laboratory", "focus": ["test parameters", "clauses", "measurements", "scope lookup"]},
    "general": {"title": "General User", "focus": ["standards discovery", "product intelligence", "public BIS resources"]},
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS sg_alerts (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, severity TEXT NOT NULL,
            alert_date TEXT NOT NULL, source TEXT, product TEXT,
            action TEXT, status TEXT NOT NULL DEFAULT 'OPEN', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sg_evidence (
            id TEXT PRIMARY KEY, evidence_type TEXT NOT NULL, payload_json TEXT NOT NULL,
            source TEXT, verification_status TEXT NOT NULL, created_at TEXT NOT NULL
        );
        """)


def deps():
    from app import bis_data, find_matches, product_intel_engine, rag, OFFICIAL_RESOURCES
    from labs_directory import search_laboratories
    return bis_data, find_matches, product_intel_engine, rag, OFFICIAL_RESOURCES, search_laboratories


def response(status: str, data: Any, confidence: float = 0.0, evidence=None, source=None, errors=None):
    return jsonify({
        "status": status,
        "data": data,
        "confidence": confidence,
        "evidence": evidence or [],
        "source": source,
        "timestamp": now(),
        "errors": errors or [],
        "notice": NOTICE,
    })


def extract_standard_number(text: str):
    m = re.search(r"\b(?:IS(?:/IEC)?|IS/IEC)\s*[A-Z]?\s*\d{3,6}(?:\s*\([^)]*\))?(?::\s*\d{4})?", text or "", re.I)
    return m.group(0).strip() if m else None


def extract_markers(text: str) -> Dict[str, List[str]]:
    text = str(text or "")
    cml = re.findall(r"\b(?:CM/?L|CML|LICENCE|LICENSE)\s*[:#-]?\s*(\d{5,10})\b", text, re.I)
    rnums = re.findall(r"\bR[-\s]?\d{6,12}\b", text, re.I)
    huid = re.findall(r"\bHUID\s*[:#-]?\s*([A-Z0-9]{4,12})\b", text, re.I)
    return {"cm_l_candidates": cml, "r_number_candidates": rnums, "huid_candidates": huid}


def validate_file(f):
    name = os.path.basename(f.filename or "")
    ext = os.path.splitext(name)[1].lower()
    allowed = {".pdf", ".txt", ".md", ".json", ".doc", ".docx", ".png", ".jpg", ".jpeg", ".webp"}
    if ext not in allowed:
        raise ValueError("Unsupported file type. Supported: PDF, TXT, MD, JSON, DOC/DOCX, PNG, JPG/JPEG, WEBP.")
    raw = f.read(MAX_FILE_BYTES + 1)
    if len(raw) > MAX_FILE_BYTES:
        raise ValueError(f"File exceeds the {MAX_FILE_BYTES // (1024*1024)} MB limit.")
    if not raw:
        raise ValueError("Uploaded file is empty.")
    return name, ext, raw


def detect_clauses(text: str) -> List[Dict[str, Any]]:
    out = []
    for line_no, line in enumerate(str(text or "").splitlines(), 1):
        line = line.strip()
        m = re.match(r"^(\d+(?:\.\d+){1,4})\s+(.{2,180})$", line)
        if m:
            out.append({"clause_number": m.group(1), "clause_title": m.group(2).strip(), "line": line_no})
    return out[:300]


def read_document(name: str, ext: str, raw: bytes):
    metadata = {"filename": name, "extension": ext, "bytes": len(raw), "document_hash": sha256_bytes(raw)}
    pages = []
    text = ""
    if ext in {".txt", ".md", ".json"}:
        text = raw.decode("utf-8", "ignore")
        if ext == ".json":
            try:
                text = json.dumps(json.loads(text), ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                pass
        pages = [{"page": 1, "text": text}]
    elif ext == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(raw))
            for i, page in enumerate(reader.pages, 1):
                pages.append({"page": i, "text": page.extract_text() or ""})
            text = "\n\n".join(p["text"] for p in pages)
            metadata["pages"] = len(pages)
        except Exception as exc:
            metadata["extraction_error"] = str(exc)
    elif ext in {".doc", ".docx"}:
        if ext == ".docx":
            try:
                from docx import Document
                doc = Document(io.BytesIO(raw))
                text = "\n".join(p.text for p in doc.paragraphs)
                pages = [{"page": 1, "text": text}]
            except Exception as exc:
                metadata["extraction_error"] = str(exc)
        else:
            metadata["extraction_error"] = "Legacy .doc extraction is not available in this deployment."
    else:
        try:
            from PIL import Image
            image = Image.open(io.BytesIO(raw))
            metadata.update({"width": image.width, "height": image.height, "format": image.format})
            try:
                import pytesseract
                text = pytesseract.image_to_string(image)
                metadata["ocr"] = True
            except Exception as exc:
                metadata["ocr"] = False
                metadata["ocr_error"] = str(exc)
                metadata["ocr_notice"] = "OCR could not be executed in this deployment; no synthetic OCR result was generated."
            pages = [{"page": 1, "text": text}]
        except Exception as exc:
            metadata["extraction_error"] = str(exc)
    return text, pages, metadata


def chunk_pages(pages: List[Dict[str, Any]], filename: str):
    chunks = []
    for page in pages:
        words = page["text"].split()
        if not words:
            continue
        for start in range(0, len(words), 100):
            piece = " ".join(words[start:start + 120]).strip()
            if not piece:
                continue
            chunks.append({
                "chunk_id": f"{filename}-{page['page']}-{start}",
                "page_number": page["page"],
                "text": piece,
                "source_document": filename,
                "document_hash": None,
                "clause_number": None,
                "clause_title": None,
                "support_level": "user_uploaded_document",
            })
    return chunks


def enrich_rag(items):
    enriched = []
    for x in items:
        item = dict(x)
        item.setdefault("standard_id", item.get("standard_number"))
        item.setdefault("edition", None)
        item.setdefault("revision", None)
        item.setdefault("amendment_number", None)
        item.setdefault("clause_number", None)
        item.setdefault("clause_title", None)
        item.setdefault("sub_clause", None)
        item.setdefault("page_number", None)
        item.setdefault("source_document", item.get("title"))
        item.setdefault("document_hash", None)
        item["retrieval_score"] = item.get("relevance", item.get("match_score", 0))
        item["evidence_text"] = item.get("text", "")
        enriched.append(item)
    return enriched


@bp.get("/health")
def v8_health():
    init_db()
    bis_data, _, _, rag, _, _ = deps()
    return response("OK", {"platform": "BIS SmartGuide", "version": "8.0", "standards_loaded": len(bis_data), "rag_chunks": rag.chunk_count, "document_sources": rag.document_count, "live_verification": False})


@bp.post("/product-intelligence")
def product_intelligence():
    body = request.get_json(silent=True) or {}
    query = str(body.get("query") or body.get("description") or body.get("product") or "").strip()
    if not query:
        return response("ERROR", None, errors=["Product description is required."]), 400
    _, find_matches, engine, _, _, _ = deps()
    result = engine.analyze(query)
    matches = result.get("candidate_standards") or find_matches(query, 8)
    evidence = [{"standard": m.get("standard_number"), "title": m.get("title"), "source": m.get("official_source"), "match_score": m.get("match_score"), "reasons": m.get("match_reasons", [])} for m in matches[:8]]
    result["ranked_standards"] = matches
    result["evidence_classification"] = "SOURCE-GROUNDED" if matches else "UNVERIFIED"
    return response("OK", result, float(result.get("confidence") or 0), evidence, "local BIS standards corpus")


@bp.get("/rag/search")
def rag_search():
    q = request.args.get("q", "").strip()
    if not q:
        return response("ERROR", None, errors=["Query is required."]), 400
    _, _, _, rag, _, _ = deps()
    hits = enrich_rag(rag.retrieve(q, min(12, max(1, int(request.args.get("limit", 8))))))
    if not hits:
        return response("INSUFFICIENT_EVIDENCE", {"message": "Insufficient verified BIS evidence was found to answer this reliably."}, 0.0, [], None)
    return response("OK", {"query": q, "results": hits}, float(hits[0].get("retrieval_score", 0)) / 100.0, hits, hits[0].get("source_url"))


@bp.get("/rag/clauses")
def rag_clauses():
    q = request.args.get("q", "").strip()
    standard = request.args.get("standard", "").strip().upper().replace(" ", "")
    clause = request.args.get("clause", "").strip()
    if not q and not standard:
        return response("ERROR", None, errors=["Provide q or standard."]), 400
    _, _, _, rag, _, _ = deps()
    hits = enrich_rag(rag.retrieve(q or standard, 20))
    if standard:
        hits = [h for h in hits if standard in str(h.get("standard_number") or "").upper().replace(" ", "")] or hits
    if clause:
        hits = [h for h in hits if str(h.get("clause_number") or "") == clause]
    clauses = [h for h in hits if h.get("clause_number")]
    return response("OK", {"query": q, "standard": standard, "clause": clause, "clauses": clauses, "results": hits, "note": "Existing catalogue records do not contain clause/page metadata unless sourced from an uploaded document or a future verified BIS document ingest."}, float(hits[0].get("retrieval_score", 0)) / 100.0 if hits else 0.0, hits, hits[0].get("source_url") if hits else None)


@bp.post("/document/ingest")
def document_ingest():
    f = request.files.get("file")
    if not f:
        return response("ERROR", None, errors=["Upload a document or image."]), 400
    try:
        name, ext, raw = validate_file(f)
        text, pages, metadata = read_document(name, ext, raw)
    except ValueError as exc:
        return response("ERROR", None, errors=[str(exc)]), 400
    except Exception as exc:
        return response("ERROR", None, errors=["Document processing failed.", str(exc)]), 422
    clauses = detect_clauses(text)
    chunks = chunk_pages(pages, name)
    for c in chunks:
        c["document_hash"] = metadata["document_hash"]
    _, find_matches, _, _, _, _ = deps()
    candidates = find_matches(text[:16000], 8) if text.strip() else []
    result = {"filename": name, "metadata": metadata, "characters_extracted": len(text), "pages": pages if len(pages) <= 20 else [{"page": p["page"], "characters": len(p["text"])} for p in pages], "clauses_detected": clauses, "chunks": chunks[:200], "candidate_standards": candidates, "document_analysis_notice": "Document analysis does not constitute BIS certification or legal approval."}
    status = "OCR_UNAVAILABLE" if ext in {".png", ".jpg", ".jpeg", ".webp"} and not metadata.get("ocr") else "OK"
    return response(status, result, min(0.95, 0.5 + (0.2 if text.strip() else 0)), [{"document_hash": metadata["document_hash"], "chunks": len(chunks), "clauses": len(clauses)}], "user-uploaded document")


@bp.post("/ocr")
def ocr():
    f = request.files.get("file")
    if not f:
        return response("ERROR", None, errors=["Upload an image."]), 400
    try:
        name, ext, raw = validate_file(f)
    except ValueError as exc:
        return response("ERROR", None, errors=[str(exc)]), 400
    if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
        return response("ERROR", None, errors=["OCR accepts PNG, JPG, JPEG or WEBP images."]), 400
    try:
        from PIL import Image
        import pytesseract
        image = Image.open(io.BytesIO(raw))
        text = pytesseract.image_to_string(image).strip()
        if not text:
            return response("OCR_FAILED", {"filename": name, "message": "OCR could not reliably read this image."}, 0.0, [], None)
        markers = extract_markers(text)
        return response("OK", {"filename": name, "text": text, "markers": markers, "standard_number": extract_standard_number(text), "image_hash": sha256_bytes(raw)}, 0.75, [{"type": "ocr_text", "text": text[:1000]}], "OCR engine")
    except Exception as exc:
        return response("OCR_UNAVAILABLE", {"filename": name, "message": "OCR could not be executed in this deployment.", "detail": str(exc)}, 0.0, [], None, ["No synthetic OCR result was generated."])


@bp.post("/verify/mark")
def verify_mark():
    body = request.get_json(silent=True) or {}
    text = str(body.get("text") or "").strip()
    licence = str(body.get("licence") or body.get("cm_l") or "").strip()
    markers = extract_markers(text + " " + licence)
    cml = markers["cm_l_candidates"] or ([licence] if licence.isdigit() else [])
    format_valid = bool(cml and all(5 <= len(re.sub(r"\D", "", x)) <= 10 for x in cml))
    data = {"detected_cm_l": cml, "standard_number": extract_standard_number(text), "format_appears_valid": format_valid, "verification_status": "SOURCE_UNAVAILABLE", "message": UNVERIFIED}
    return response("SOURCE_UNAVAILABLE", data, 0.0, [{"type": "format_check", "result": format_valid}], None, ["Official BIS CM/L lookup is not connected in this deployment."])


@bp.post("/verify/crs")
def verify_crs():
    body = request.get_json(silent=True) or {}
    text = str(body.get("text") or body.get("r_number") or "").strip()
    candidates = extract_markers(text)["r_number_candidates"]
    data = {"detected_r_numbers": candidates, "format_appears_valid": bool(candidates), "verification_status": "SOURCE_UNAVAILABLE", "message": UNVERIFIED}
    return response("SOURCE_UNAVAILABLE", data, 0.0, [{"type": "format_check", "result": bool(candidates)}], None, ["Official CRS registry lookup is not connected in this deployment."])


@bp.post("/verify/huid")
def verify_huid():
    body = request.get_json(silent=True) or {}
    text = str(body.get("text") or body.get("huid") or "").strip()
    candidates = extract_markers(text)["huid_candidates"]
    data = {"detected_huid": candidates, "verification_status": "SOURCE_UNAVAILABLE", "message": "Live verification is unavailable; use the official BIS verification channel."}
    return response("SOURCE_UNAVAILABLE", data, 0.0, [{"type": "huid_detected", "result": bool(candidates)}], None, ["Official HUID verification is not connected in this deployment."])


@bp.post("/qr/decode")
def qr_decode():
    f = request.files.get("file")
    if not f:
        return response("ERROR", None, errors=["Upload a QR/barcode image."]), 400
    try:
        name, ext, raw = validate_file(f)
        if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise ValueError("QR/barcode decoding accepts image files only.")
        from PIL import Image
        image = Image.open(io.BytesIO(raw))
        decoded = []
        try:
            import cv2
            import numpy as np
            detector = cv2.QRCodeDetector()
            text, _, _ = detector.detectAndDecode(cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR))
            if text:
                decoded.append({"type": "QR", "value": text})
        except Exception:
            pass
        try:
            from pyzbar.pyzbar import decode
            for item in decode(image):
                decoded.append({"type": item.type, "value": item.data.decode("utf-8", "replace")})
        except Exception:
            pass
        if not decoded:
            return response("DECODE_FAILED", {"filename": name, "message": "No QR/barcode could be reliably decoded."}, 0.0, [], None)
        results = []
        for item in decoded:
            value = item["value"]
            official = bool(re.match(r"https://(?:www\.)?(?:bis\.gov\.in|standards\.bis\.gov\.in|lims\.bis\.gov\.in)(?:/|$)", value, re.I))
            results.append({**item, "looks_like_official_bis_url": official, "verification_status": "SOURCE_UNAVAILABLE"})
        return response("OK", {"filename": name, "decoded": results, "image_hash": sha256_bytes(raw)}, 0.8, results, None)
    except ValueError as exc:
        return response("ERROR", None, errors=[str(exc)]), 400
    except Exception as exc:
        return response("ERROR", None, errors=["QR/barcode processing failed.", str(exc)]), 422


@bp.get("/labs/match")
def labs_match():
    product = request.args.get("product", "").strip()
    standard = request.args.get("standard", "").strip()
    test = request.args.get("test", "").strip()
    city = request.args.get("city", "").strip()
    _, find_matches, _, _, _, search_laboratories = deps()
    if not standard and product:
        m = find_matches(product, 1)
        standard = m[0].get("standard_number", "") if m else ""
    data = search_laboratories(query=test or product, standard_number=standard, city=city)
    for lab in data.get("laboratories", []):
        lab["source_status"] = "LOCAL_SNAPSHOT_UNVERIFIED"
        lab["verification_status"] = "NOT_VERIFIED_LIVE"
        lab["maps_url"] = "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(lab.get("name", "") + ", " + lab.get("address", ""))
    data["trust_boundary"] = "Laboratory records in this deployment are a local snapshot and are not asserted as live verified scope. Confirm current recognition and capability in official BIS LIMS before booking testing."
    return response("OK", data, 0.5 if data.get("laboratories") else 0.0, data.get("laboratories", []), "BIS LIMS directory handoff")


@bp.post("/tests/analyze")
def test_analyze():
    body = request.get_json(silent=True) or {}
    text = str(body.get("text") or body.get("report_text") or "").strip()
    if not text and request.files.get("file"):
        f = request.files["file"]
        name, ext, raw = validate_file(f)
        text, _, _ = read_document(name, ext, raw)
    if not text:
        return response("ERROR", None, errors=["Test report text or file is required."]), 400
    values = []
    patterns = [
        ("voltage", r"(?:voltage|rated voltage)\s*[:=-]?\s*(\d+(?:\.\d+)?)\s*(V|volt|volts)"),
        ("power", r"(?:power|rated power)\s*[:=-]?\s*(\d+(?:\.\d+)?)\s*(W|kW|watt|watts)"),
        ("current", r"(?:current|rated current)\s*[:=-]?\s*(\d+(?:\.\d+)?)\s*(A|amp|amps)"),
        ("temperature", r"(?:temperature|temp)\s*[:=-]?\s*(-?\d+(?:\.\d+)?)\s*(C|°C)"),
        ("pressure", r"(?:pressure)\s*[:=-]?\s*(\d+(?:\.\d+)?)\s*(MPa|kPa|bar|Pa)"),
    ]
    for key, pat in patterns:
        for m in re.finditer(pat, text, re.I):
            values.append({"parameter": key, "measured_value": float(m.group(1)), "unit": m.group(2), "required_value": None, "pass_fail": "UNVERIFIED"})
    std = str(body.get("standard") or extract_standard_number(text) or "").strip()
    return response("OK", {"standard": std, "test_report_number": None, "laboratory": None, "product": None, "measurements": values, "requirements_verified": False, "message": "Unable to verify requirement from available evidence." if not std else "Measured values extracted; required limits are not fabricated and remain unverified until mapped to a verified clause."}, 0.6 if values else 0.2, values, None)


@bp.post("/label/analyze")
def label_analyze():
    body = request.get_json(silent=True) or {}
    text = str(body.get("text") or "").strip()
    if not text and request.files.get("file"):
        f = request.files["file"]
        name, ext, raw = validate_file(f)
        text, _, _ = read_document(name, ext, raw)
    markers = extract_markers(text)
    fields = {"product_name": None, "manufacturer": None, "model": None, "standard_number": extract_standard_number(text), "cm_l": markers["cm_l_candidates"], "r_numbers": markers["r_number_candidates"]}
    for key, labels in {"product_name": ["product name", "product"], "manufacturer": ["manufacturer", "manufactured by"], "model": ["model", "model no"]}.items():
        for label in labels:
            m = re.search(rf"{re.escape(label)}\s*[:#-]\s*([^\n,;]+)", text, re.I)
            if m:
                fields[key] = m.group(1).strip()
                break
    checks = [{"field": "standard_number", "status": "PASS" if fields["standard_number"] else "UNVERIFIED"}, {"field": "cm_l_or_r_number", "status": "PASS" if fields["cm_l"] or fields["r_numbers"] else "UNVERIFIED"}]
    return response("OK", {"fields": fields, "checks": checks, "overall": "UNVERIFIED", "message": "Mandatory declarations are not assumed without verified product-specific source evidence."}, 0.55 if text else 0.0, checks, None)


@bp.get("/amendments")
def amendments():
    return response("SOURCE_UNAVAILABLE", {"records": [], "message": "Live official amendment/Gazette retrieval is not connected in this deployment.", "demo_data": False}, 0.0, [], "https://www.bis.gov.in/")


@bp.post("/amendments/impact")
def amendment_impact():
    body = request.get_json(silent=True) or {}
    std = str(body.get("standard") or "").strip()
    product = str(body.get("product") or "").strip()
    text = str(body.get("amendment") or body.get("text") or "").strip()
    if not text:
        return response("SOURCE_UNAVAILABLE", {"impact": None, "message": "No verified amendment text was supplied; live amendment retrieval is unavailable."}, 0.0, [], None)
    clauses = detect_clauses(text)
    level = "LOW"
    if re.search(r"critical|prohibit|mandatory|shall not|effective immediately", text, re.I): level = "CRITICAL"
    elif re.search(r"new requirement|replace|revise|amend|shall", text, re.I): level = "HIGH"
    elif re.search(r"change|modify|update", text, re.I): level = "MEDIUM"
    return response("INFERRED", {"standard": std, "product": product, "impact_level": level, "affected_clauses": clauses, "previous_requirement": None, "new_requirement": None, "required_action": "Review the supplied amendment against the official Gazette and current BIS standard before acting.", "verified": False}, 0.35, [{"type": "user_supplied_amendment_text", "hash": sha256_bytes(text.encode())}], None)


@bp.get("/alerts")
def alerts():
    init_db()
    with db() as con:
        rows = con.execute("SELECT * FROM sg_alerts ORDER BY created_at DESC LIMIT 100").fetchall()
    return response("OK", {"alerts": [dict(r) for r in rows], "live_monitoring": False}, 0.0, [], None)


@bp.post("/alerts")
def create_alert():
    init_db()
    body = request.get_json(silent=True) or {}
    title = str(body.get("title") or "").strip()
    if not title:
        return response("ERROR", None, errors=["Alert title is required."]), 400
    import uuid
    item = {"id": "ALT-" + uuid.uuid4().hex[:10].upper(), "title": title, "severity": str(body.get("severity") or "MEDIUM").upper(), "alert_date": str(body.get("date") or now()), "source": body.get("source"), "product": body.get("product"), "action": body.get("action"), "status": "OPEN", "created_at": now()}
    with db() as con:
        con.execute("INSERT INTO sg_alerts VALUES (?,?,?,?,?,?,?,?,?)", tuple(item.values()))
    return response("CREATED", item, 1.0, [{"type": "user_created_alert", "id": item["id"]}], item["source"])


@bp.post("/persona")
def persona():
    body = request.get_json(silent=True) or {}
    rid = str(body.get("role") or "general").strip().lower()
    if rid not in ROLES: rid = "general"
    return response("OK", {"role": rid, **ROLES[rid]}, 1.0, [], "SmartGuide persona configuration")


@bp.get("/evidence")
def evidence():
    init_db()
    with db() as con:
        rows = con.execute("SELECT * FROM sg_evidence ORDER BY created_at DESC LIMIT 100").fetchall()
    return response("OK", {"records": [dict(r) for r in rows]}, 0.0, [], None)


@bp.post("/agent/orchestrate")
def orchestrate():
    body = request.get_json(silent=True) or {}
    message = str(body.get("message") or "").strip()
    role = str(body.get("role") or "general").strip().lower()
    if not message: return response("ERROR", None, errors=["Message is required."]), 400
    if role not in ROLES: role = "general"
    _, find_matches, _, rag, resources, _ = deps()
    matches = find_matches(message, 5)
    rag_hits = enrich_rag(rag.retrieve(message, 5))
    route = ["product-intelligence", "rag/search"]
    low = message.lower()
    if any(x in low for x in ["cm/l", "cml", "isi mark", "isi"]): route.append("verify/mark")
    if "r-number" in low or "crs" in low: route.append("verify/crs")
    if "huid" in low or "hallmark" in low: route.append("verify/huid")
    if any(x in low for x in ["lab", "laboratory"]): route.append("labs/match")
    if any(x in low for x in ["test report", "test result"]): route.append("tests/analyze")
    if any(x in low for x in ["label", "packaging", "marking"]): route.append("label/analyze")
    if any(x in low for x in ["amendment", "gazette", "changed", "revision"]): route.append("amendments/impact")
    if "compliant" in low or "compliance" in low: route.append("compliance passport")
    return response("OK", {"role": role, "route": route, "candidate_standards": matches, "retrieved_evidence": rag_hits, "answer_policy": "Only source-grounded claims may be presented as verified; otherwise return INFERRED or SOURCE_UNAVAILABLE.", "official_resources": resources}, float(rag_hits[0].get("retrieval_score", 0))/100 if rag_hits else 0.0, rag_hits, rag_hits[0].get("source_url") if rag_hits else None)


@bp.post("/report/pdf")
def report_pdf():
    body = request.get_json(silent=True) or {}
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import mm
    except Exception as exc:
        return response("UNAVAILABLE", {"message": "PDF generation dependency is unavailable.", "detail": str(exc)}, 0.0, [], None), 503
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet(); story = [Paragraph("BIS SmartGuide — Compliance Intelligence Report", styles["Title"]), Spacer(1, 8)]
    product = str(body.get("product") or "Unspecified product")
    story.append(Paragraph(f"Product: {product}", styles["Heading2"]))
    for key in ["standard", "status", "risk", "score", "role"]:
        if key in body: story.append(Paragraph(f"{key.title()}: {str(body[key])}", styles["BodyText"]))
    story.append(Spacer(1, 10))
    evidence = body.get("evidence") or []
    if evidence:
        data = [["Evidence", "Source", "Status"]]
        for e in evidence[:20]: data.append([str(e.get("title") or e.get("standard") or e.get("type") or "Evidence"), str(e.get("source") or "Not supplied"), str(e.get("verification_status") or e.get("status") or "UNVERIFIED")])
        t = Table(data, repeatRows=1); t.setStyle(TableStyle([("GRID", (0,0), (-1,-1), 0.4, colors.grey), ("BACKGROUND", (0,0), (-1,0), colors.lightgrey)])); story += [t, Spacer(1, 10)]
    story.append(Paragraph(NOTICE, styles["BodyText"]))
    doc.build(story); buf.seek(0)
    return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name="bis-smartguide-report.pdf")


def register(app):
    init_db()
    app.register_blueprint(bp)
    return app
