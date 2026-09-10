import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app_upgrade import app


def test_v8_health():
    client = app.test_client()
    r = client.get("/api/v8/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "OK"


def test_product_intelligence_has_evidence_boundary():
    client = app.test_client()
    r = client.post("/api/v8/product-intelligence", json={"query": "2 burner domestic LPG gas stove"})
    assert r.status_code == 200
    data = r.get_json()
    assert "data" in data
    assert "ranked_standards" in data["data"]
    assert "evidence_classification" in data["data"]


def test_mark_verification_never_claims_live_verified():
    client = app.test_client()
    r = client.post("/api/v8/verify/mark", json={"text": "ISI CM/L 1234567 IS 4246"})
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "SOURCE_UNAVAILABLE"
    assert data["data"]["verification_status"] == "SOURCE_UNAVAILABLE"


def test_document_ingest_text_has_hash_and_clauses():
    client = app.test_client()
    payload = b"IS 4246\n1.1 Scope\n1.2 Requirements\nCM/L: 1234567"
    r = client.post("/api/v8/document/ingest", data={"file": (io.BytesIO(payload), "sample.txt")}, content_type="multipart/form-data")
    assert r.status_code == 200
    data = r.get_json()["data"]
    assert data["metadata"]["document_hash"]
    assert len(data["clauses_detected"]) >= 2


def test_amendment_without_source_is_not_verified():
    client = app.test_client()
    r = client.post("/api/v8/amendments/impact", json={"standard": "IS 4246", "product": "gas stove", "amendment": "1.2 Revised requirement shall apply"})
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "INFERRED"
    assert data["data"]["verified"] is False


def test_agent_router_returns_workflow_route():
    client = app.test_client()
    r = client.post("/api/v8/agent/orchestrate", json={"role": "manufacturer_msme", "message": "I manufacture gas stoves. Find a lab and check the standard."})
    assert r.status_code == 200
    route = r.get_json()["data"]["route"]
    assert "product-intelligence" in route
    assert "labs/match" in route
