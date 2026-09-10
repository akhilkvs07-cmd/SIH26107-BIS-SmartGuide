"""BIS SmartGuide V4 upgrade layer.

Adds a modular API layer without replacing the existing prototype routes:
- evidence-aware compliance assessments
- persistent SQLite assessment history
- product compliance passports
- corrective-action tracking
- document extraction for PDF/TXT/MD/JSON and optional OCR for images
- analytics and assessment comparison

All results remain decision-support only; this module never issues BIS
certification and clearly separates prototype evidence from official sources.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from flask import Blueprint, jsonify, request

bp = Blueprint("compliance_upgrade", __name__, url_prefix="/v4")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "smartguide.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "documents")
os.makedirs(UPLOAD_DIR, exist_ok=True)

NOTICE = "AI-assisted prototype assessment only. It does not issue, verify, or grant BIS certification and is not an official regulatory decision. Verify current BIS requirements, amendments, QCOs, schemes and laboratory scope through official BIS sources."


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _db() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db() -> None:
    with _db() as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS assessments (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                product TEXT NOT NULL,
                model TEXT,
                manufacturer TEXT,
                standard_number TEXT,
                score INTEGER NOT NULL,
                risk TEXT NOT NULL,
                status TEXT NOT NULL,
                evidence_quality TEXT NOT NULL,
                result_json TEXT NOT NULL,
                evidence_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS actions (
                id TEXT PRIMARY KEY,
                assessment_id TEXT NOT NULL,
                requirement TEXT NOT NULL,
                priority TEXT NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'OPEN',
                created_at TEXT NOT NULL,
                FOREIGN KEY (assessment_id) REFERENCES assessments(id)
            );
            """
        )


def _risk(score: int, failed: int, unchecked: int) -> str:
    if failed >= 2 or score < 50:
        return "HIGH"
    if failed or unchecked or score < 80:
        return "MEDIUM"
    return "LOW"


def _evidence_quality(evidence: dict[str, Any]) -> str:
    if not evidence:
        return "LOW"
    fields = [v for v in evidence.values() if v not in (None, "", [], {})]
    if len(fields) >= 6:
        return "HIGH"
    if len(fields) >= 3:
        return "MEDIUM"
    return "LOW"


def _hash_evidence(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _extract_values(text: str) -> dict[str, Any]:
    text = str(text or "")
    low = text.lower()
    values: dict[str, Any] = {}
    patterns = {
        "voltage": r"(?:voltage|rated voltage)\s*[:=-]?\s*(\d+(?:\.\d+)?)\s*(v|volt|volts)?",
        "power": r"(?:power|rated power)\s*[:=-]?\s*(\d+(?:\.\d+)?)\s*(w|kw|watt|watts)?",
        "current": r"(?:current|rated current)\s*[:=-]?\s*(\d+(?:\.\d+)?)\s*(a|amp|amps)?",
        "temperature": r"(?:temperature|temp)\s*[:=-]?\s*(-?\d+(?:\.\d+)?)\s*(c|°c|deg c)?",
        "pressure": r"(?:pressure)\s*[:=-]?\s*(\d+(?:\.\d+)?)\s*(mpa|kpa|bar|pa)?",
        "leakage": r"(?:leakage|leak)\s*[:=-]?\s*(\d+(?:\.\d+)?)\s*(%|percent)?",
        "thickness": r"(?:thickness|material thickness)\s*[:=-]?\s*(\d+(?:\.\d+)?)\s*(mm|cm)?",
    }
    for key, pattern in patterns.items():
        m = re.search(pattern, low)
        if m:
            values[key] = {"value": float(m.group(1)), "unit": m.group(2) or ""}
    for key, labels in {
        "manufacturer": ["manufacturer", "maker"],
        "model": ["model", "model no", "model number"],
        "certificate": ["certificate", "certificate no", "certificate number"],
        "standard": ["standard", "is number", "bis standard"],
    }.items():
        for label in labels:
            m = re.search(rf"{re.escape(label)}\s*[:#=-]\s*([^\n,;]+)", text, re.I)
            if m:
                values[key] = m.group(1).strip()[:160]
                break
    values["keywords"] = [k for k in ["test report", "certificate", "laboratory", "manufacturer", "model", "bis", "is "] if k in low]
    return values


def _read_document(file_storage):
    name = os.path.basename(file_storage.filename or "document")
    ext = os.path.splitext(name)[1].lower()
    raw_bytes = file_storage.read()
    text = ""
    metadata: dict[str, Any] = {"filename": name, "extension": ext, "bytes": len(raw_bytes)}
    if ext in {".txt", ".md", ".json"}:
        text = raw_bytes.decode("utf-8", "ignore")
        if ext == ".json":
            try:
                text = json.dumps(json.loads(text), ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                pass
    elif ext == ".pdf":
        try:
            from pypdf import PdfReader
            import io
            reader = PdfReader(io.BytesIO(raw_bytes))
            pages = []
            for page in reader.pages:
                pages.append(page.extract_text() or "")
            text = "\n".join(pages)
            metadata["pages"] = len(reader.pages)
        except Exception as exc:
            metadata["extraction_error"] = str(exc)
    elif ext in {".png", ".jpg", ".jpeg", ".webp"}:
        try:
            from PIL import Image
            import io
            image = Image.open(io.BytesIO(raw_bytes))
            metadata["width"], metadata["height"] = image.size
            metadata["format"] = image.format
        except Exception as exc:
            metadata["extraction_error"] = str(exc)
        try:
            import pytesseract
            from PIL import Image
            import io
            text = pytesseract.image_to_string(Image.open(io.BytesIO(raw_bytes)))
            metadata["ocr"] = True
        except Exception:
            metadata["ocr"] = False
            metadata["ocr_notice"] = "Image received. OCR is unavailable in this deployment."
    else:
        raise ValueError("Supported files: TXT, MD, JSON, PDF, PNG, JPG, JPEG and WEBP.")
    return name, text, metadata


def _get_dependencies():
    # Imported lazily so the original application remains the source of truth.
    from app import OFFICIAL_RESOURCES, compliance_result, find_matches
    return OFFICIAL_RESOURCES, compliance_result, find_matches


def _build_assessment(product: str, checks: dict[str, Any], evidence: dict[str, Any], document_text: str = "") -> dict[str, Any]:
    official, compliance_result, find_matches = _get_dependencies()
    base = compliance_result(product, checks)
    if not base.get("found"):
        return {**base, "notice": NOTICE}
    standard = base.get("standard") or {}
    failed = list(base.get("failed", []))
    unchecked = list(base.get("not_checked", []))
    passed = list(base.get("passed", []))
    extracted = _extract_values(document_text)
    merged_evidence = {**evidence, **extracted}
    # Evidence increases traceability but never silently turns an unchecked
    # requirement into a pass. A human or explicit test mapping is required.
    evidence_hits = []
    text_low = document_text.lower()
    for req in standard.get("requirements", []):
        if req.lower() in text_low:
            evidence_hits.append(req)
    quality = _evidence_quality(merged_evidence)
    score = int(base.get("score", 0))
    if evidence_hits and unchecked:
        score = min(100, score + min(15, len(evidence_hits) * 5))
    risk = _risk(score, len(failed), len(unchecked))
    actions = []
    for req in failed:
        actions.append({"requirement": req, "priority": "HIGH", "action": f"Correct '{req}', attach supporting evidence, and reassess."})
    for req in unchecked:
        actions.append({"requirement": req, "priority": "MEDIUM", "action": f"Provide objective evidence for '{req}' before final conformity review."})
    if not actions:
        actions.append({"requirement": "Ongoing conformity", "priority": "LOW", "action": "Maintain evidence and verify current BIS requirements and amendments."})
    return {
        "assessment_version": "4.0",
        "product": product,
        "standard": standard,
        "score": score,
        "risk": risk,
        "status": "FAIL" if failed else ("REVIEW" if unchecked else "PASS"),
        "passed": passed,
        "failed": failed,
        "not_checked": unchecked,
        "evidence": merged_evidence,
        "evidence_hits": evidence_hits,
        "evidence_quality": quality,
        "confidence": round(min(0.98, 0.45 + score / 200 + (0.1 if quality == "HIGH" else 0.05 if quality == "MEDIUM" else 0)), 2),
        "corrective_actions": actions,
        "official_resources": official,
        "notice": NOTICE,
    }


@bp.before_app_request
def _ensure_db():
    init_db()


@bp.get("/health")
def upgrade_health():
    init_db()
    return jsonify({"status": "ready", "upgrade": "BIS SmartGuide V4 Compliance Intelligence", "database": "sqlite", "features": ["evidence mapping", "PDF extraction", "optional image OCR", "assessment history", "risk scoring", "corrective actions", "compliance passport", "analytics"], "notice": NOTICE})


@bp.post("/assess")
def assess():
    body = request.get_json(silent=True) or {}
    product = str(body.get("product", "")).strip()
    if not product:
        return jsonify({"error": "Product is required."}), 400
    checks = body.get("checks") or body.get("checklist") or {}
    evidence = body.get("evidence") or {}
    if not evidence and (body.get("model") or body.get("manufacturer")):
        evidence = {"model": body.get("model", ""), "manufacturer": body.get("manufacturer", "")}
    result = _build_assessment(product, checks, evidence, str(body.get("document_text", "")))
    if not result.get("standard"):
        return jsonify(result), 404
    assessment_id = "BIS-" + uuid.uuid4().hex[:10].upper()
    evidence_hash = _hash_evidence(result.get("evidence", {}))
    result["assessment_id"] = assessment_id
    result["created_at"] = _now()
    with _db() as con:
        con.execute("INSERT INTO assessments VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (assessment_id, result["created_at"], product, result["evidence"].get("model"), result["evidence"].get("manufacturer"), result["standard"].get("standard_number"), int(result["score"]), result["risk"], result["status"], result["evidence_quality"], json.dumps(result, ensure_ascii=False), evidence_hash))
        for action in result["corrective_actions"]:
            con.execute("INSERT INTO actions VALUES (?,?,?,?,?,?,?)", (uuid.uuid4().hex[:12], assessment_id, action["requirement"], action["priority"], action["action"], "OPEN", result["created_at"]))
    result["evidence_hash"] = evidence_hash
    return jsonify(result)


@bp.post("/document")
def document_intelligence():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "Upload a TXT, MD, JSON, PDF or image file."}), 400
    try:
        name, text, metadata = _read_document(f)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    matches = []
    if text.strip():
        _, _, find_matches = _get_dependencies()
        matches = find_matches(text[:12000], 5)
    extracted = _extract_values(text)
    return jsonify({"filename": name, "metadata": metadata, "characters_extracted": len(text), "extracted_fields": extracted, "candidate_standards": matches, "document_hash": _hash_evidence({"name": name, "text": text}), "notice": NOTICE})


@bp.get("/assessments")
def assessments():
    limit = min(max(int(request.args.get("limit", 20)), 1), 100)
    with _db() as con:
        rows = con.execute("SELECT id,created_at,product,model,manufacturer,standard_number,score,risk,status,evidence_quality,evidence_hash FROM assessments ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return jsonify({"count": len(rows), "assessments": [dict(r) for r in rows]})


@bp.get("/assessments/<assessment_id>")
def assessment_detail(assessment_id: str):
    with _db() as con:
        row = con.execute("SELECT * FROM assessments WHERE id=?", (assessment_id,)).fetchone()
        actions = con.execute("SELECT * FROM actions WHERE assessment_id=? ORDER BY created_at", (assessment_id,)).fetchall()
    if not row:
        return jsonify({"error": "Assessment not found."}), 404
    result = json.loads(row["result_json"])
    result["evidence_hash"] = row["evidence_hash"]
    result["actions"] = [dict(x) for x in actions]
    return jsonify(result)


@bp.patch("/actions/<action_id>")
def update_action(action_id: str):
    body = request.get_json(silent=True) or {}
    status = str(body.get("status", "")).upper()
    if status not in {"OPEN", "IN_PROGRESS", "RESOLVED", "REJECTED"}:
        return jsonify({"error": "Status must be OPEN, IN_PROGRESS, RESOLVED or REJECTED."}), 400
    with _db() as con:
        cur = con.execute("UPDATE actions SET status=? WHERE id=?", (status, action_id))
        if cur.rowcount == 0:
            return jsonify({"error": "Action not found."}), 404
    return jsonify({"success": True, "action_id": action_id, "status": status})


@bp.get("/passport/<assessment_id>")
def passport(assessment_id: str):
    with _db() as con:
        row = con.execute("SELECT * FROM assessments WHERE id=?", (assessment_id,)).fetchone()
        if not row:
            return jsonify({"error": "Assessment not found."}), 404
        history = con.execute("SELECT id,created_at,score,risk,status,standard_number FROM assessments WHERE product=? ORDER BY created_at DESC", (row["product"],)).fetchall()
    result = json.loads(row["result_json"])
    return jsonify({"passport_id": "PASS-" + assessment_id, "assessment_id": assessment_id, "product": row["product"], "model": row["model"], "manufacturer": row["manufacturer"], "standard": result.get("standard"), "score": row["score"], "risk": row["risk"], "status": row["status"], "evidence_hash": row["evidence_hash"], "assessment_history": [dict(x) for x in history], "notice": NOTICE})


@bp.get("/analytics")
def analytics():
    with _db() as con:
        total = con.execute("SELECT COUNT(*) c FROM assessments").fetchone()["c"]
        avg = con.execute("SELECT COALESCE(AVG(score),0) a FROM assessments").fetchone()["a"]
        risks = {r["risk"]: r["c"] for r in con.execute("SELECT risk,COUNT(*) c FROM assessments GROUP BY risk")}
        statuses = {r["status"]: r["c"] for r in con.execute("SELECT status,COUNT(*) c FROM assessments GROUP BY status")}
        actions = {r["status"]: r["c"] for r in con.execute("SELECT status,COUNT(*) c FROM actions GROUP BY status")}
    return jsonify({"total_assessments": total, "average_score": round(float(avg), 1), "risk_breakdown": risks, "status_breakdown": statuses, "action_breakdown": actions})


@bp.post("/compare")
def compare():
    body = request.get_json(silent=True) or {}
    a, b = body.get("assessment_a"), body.get("assessment_b")
    if not a or not b:
        return jsonify({"error": "Provide assessment_a and assessment_b."}), 400
    def get(aid):
        with _db() as con:
            row = con.execute("SELECT * FROM assessments WHERE id=?", (aid,)).fetchone()
        return row
    ra, rb = get(a), get(b)
    if not ra or not rb:
        return jsonify({"error": "One or both assessments were not found."}), 404
    return jsonify({"before": {"id": a, "score": ra["score"], "risk": ra["risk"], "status": ra["status"]}, "after": {"id": b, "score": rb["score"], "risk": rb["risk"], "status": rb["status"]}, "score_change": rb["score"] - ra["score"], "risk_changed": ra["risk"] != rb["risk"], "notice": NOTICE})


def register(app):
    init_db()
    app.register_blueprint(bp)
    return app
