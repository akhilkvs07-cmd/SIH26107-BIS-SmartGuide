"""Comprehensive automated test suite for BIS SmartGuide (SIH26107).

Validates:
- Health and Pulse Endpoints
- Standards Corpus Integrity (Zero DEMO placeholders, 31 Authentic Standards)
- Product Intelligence Engine (5-tier classification, typos, ambiguities, unknown products, non-products)
- 15 Realistic Product Test Cases
- 8 User Personas / Role Engine
- Smart Laboratories Directory & Scope Matching
- Reverse Standard Lookup
- Dynamic Knowledge Graph Generation
- Compliance Intelligence V4 (Assessments, SQLite persistence, Passports)
- Advanced Feature Workflows (Mark Verification, Test Report, Label Check)
- Multilingual Agentic RAG Engine
"""

import json
import os
import sys
import pytest

# Ensure backend modules are on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app_upgrade import app
from app import bis_data
from product_intelligence import (
    ProductIntelligenceEngine,
    correct_spelling,
    clean_text
)
from role_engine import RoleEngine
from labs_directory import search_laboratories, OFFICIAL_LAB_DIRECTORY, OFFICIAL_LIMS_SEARCH


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# =========================================================================
# 1. HEALTH AND STATUS ENDPOINTS
# =========================================================================
def test_health_endpoints(client):
    """Verify /health and /api/health both return 200 with authentic counts."""
    for path in ["/health", "/api/health"]:
        res = client.get(path)
        assert res.status_code == 200
        data = res.get_json()
        assert data is not None
        assert data.get("status") in ["ok", "healthy"]
        assert data.get("standards_loaded", 0) >= 30
        assert data.get("rag_chunks", 0) > 0

    res4 = client.get("/v4/health")
    assert res4.status_code == 200
    assert res4.get_json().get("status") == "ready"


def test_api_info(client):
    """Verify /api-info endpoint lists platform metadata and supported roles."""
    res = client.get("/api-info")
    assert res.status_code == 200
    data = res.get_json()
    assert data["platform"] == "BIS SmartGuide"
    assert len(data["supported_roles"]) == 8
    assert len(data["supported_languages"]) == 5


# =========================================================================
# 2. STANDARDS CORPUS INTEGRITY
# =========================================================================
def test_standards_corpus_no_fake_data():
    """Verify all standards are authentic, without DEMO placeholders or mock IDs."""
    assert len(bis_data) >= 31
    for s in bis_data:
        std_no = s.get("standard_number", "")
        assert not std_no.startswith("DEMO-"), f"Found forbidden placeholder: {std_no}"
        assert std_no.startswith("IS"), f"Invalid standard number format: {std_no}"
        assert len(s.get("title", "")) > 5
        assert len(s.get("requirements", [])) >= 3
        assert len(s.get("testing_parameters", [])) >= 2
        assert s.get("scheme") is not None
        assert s.get("mandatory_status") in ["MANDATORY", "VOLUNTARY"]


# =========================================================================
# 3. PRODUCT INTELLIGENCE (5-TIER CLASSIFICATION & TYPO TOLERANCE)
# =========================================================================
@pytest.mark.parametrize("query,expected_fragment", [
    ("gas stove", "4246"),
    ("laptop", "62368"),
    ("electric kettle", "302 (Part 2/Sec 15)"),
    ("electric iron", "302 (Part 2/Sec 3)"),
    ("PVC cable", "694"),
    ("helmet", "4151"),
    ("pressure cooker", "2347"),
    ("air fryer", "302 (Part 2/Sec 9)"),
    ("induction plate", "302 (Part 2/Sec 6)"),
    ("solar food warmer", "13129"),
    ("electric lunch box", "302 (Part 2/Sec 15)"),
    ("smart extension board", "1293"),
    ("rechargeable emergency lamp", "10322 (Part 5/Sec 8)"),
    ("solar water heater", "12933"),
    ("portable garment steamer", "302 (Part 2/Sec 85)"),
])
def test_15_realistic_products(client, query, expected_fragment):
    """Test all 15 realistic products match expected authentic Indian Standards."""
    res = client.post("/v8/product-intelligence", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()
    assert data["classification"] in ["CONFIDENTLY_RECOGNIZED", "POSSIBLE_PRODUCT"]
    top_std = data.get("top_standard") or {}
    all_numbers = [top_std.get("standard_number", "")] + [c.get("standard_number", "") for c in data.get("candidate_standards", [])]
    assert any(expected_fragment in num for num in all_numbers)


def test_typo_resilience(client):
    """Verify Levenshtein distance correction handles realistic misspellings."""
    typo_cases = [
        ("gas stve", "4246"),
        ("elec kettle", "302 (Part 2/Sec 15)"),
        ("indution plate", "302 (Part 2/Sec 6)"),
        ("helmtt", "4151"),
    ]
    for typo, expected_frag in typo_cases:
        res = client.post("/v8/product-intelligence", json={"query": typo})
        assert res.status_code == 200
        data = res.get_json()
        assert data["spelling_corrected"] is True
        assert data["classification"] in ["CONFIDENTLY_RECOGNIZED", "POSSIBLE_PRODUCT"]
        top_std = data.get("top_standard") or {}
        assert expected_frag in top_std.get("standard_number", "")


def test_ambiguous_product(client):
    """Verify ambiguous terms prompt the user with possible sub-categories."""
    res = client.post("/v8/product-intelligence", json={"query": "heater"})
    assert res.status_code == 200
    data = res.get_json()
    assert data.get("clarification_needed") is True or data["classification"] in ["POSSIBLE_PRODUCT", "RELATED_PRODUCT", "UNCERTAIN"]
    assert len(data.get("options", [])) >= 2 or len(data.get("candidate_standards", [])) >= 2


def test_unknown_novel_product(client):
    """Verify novel products infer category and safe baseline standards without fabricating."""
    res = client.post("/v8/product-intelligence", json={"query": "smart solar food warmer"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["classification"] in ["CONFIDENTLY_RECOGNIZED", "POSSIBLE_PRODUCT", "RELATED_PRODUCT"]
    assert data.get("likely_category") is not None


def test_non_product_rejection(client):
    """Verify non-physical concepts or software scripts are cleanly refused."""
    non_products = ["happiness", "python script", "quantum thought"]
    for np in non_products:
        res = client.post("/v8/product-intelligence", json={"query": np})
        assert res.status_code == 200
        data = res.get_json()
        assert data["classification"] in ["NON_PRODUCT", "UNCERTAIN"]
        assert data.get("top_standard") is None


# =========================================================================
# 4. 8 USER PERSONAS / ROLE ENGINE
# =========================================================================
def test_role_engine_listing(client):
    """Verify all 8 roles are returned with schemas and tailored checklists."""
    res = client.get("/v8/roles")
    assert res.status_code == 200
    roles = res.get_json().get("roles", [])
    assert len(roles) == 8
    role_ids = {r["id"] for r in roles}
    expected_ids = {
        "manufacturer", "startup", "importer", "procurement",
        "consumer", "laboratory", "compliance", "general"
    }
    assert role_ids == expected_ids


def test_role_engine_adaptation(client):
    """Verify role adaptation tailors dashboard metrics, checklist and prompt context."""
    for role_id in ["manufacturer", "startup", "importer", "consumer", "laboratory"]:
        res = client.post("/v8/roles/adapt", json={"role": role_id, "product": "electric kettle"})
        assert res.status_code == 200
        data = res.get_json()
        assert "role" in data
        assert "adapted_checklist" in data
        role_cfg = data["role"]
        assert len(role_cfg.get("quick_actions", [])) > 0
        assert role_cfg.get("agent_system_prefix") is not None


# =========================================================================
# 5. SMART LABORATORIES DIRECTORY
# =========================================================================
def test_labs_search_and_filters(client):
    """Verify labs directory search by query, state, and official links."""
    res = client.get("/v8/labs/search?query=appliances")
    assert res.status_code == 200
    data = res.get_json()
    labs = data.get("laboratories", [])
    assert len(labs) > 0
    assert data.get("official_resources", {}).get("bis_lims_search") == OFFICIAL_LIMS_SEARCH or data.get("official_lims_search") == OFFICIAL_LIMS_SEARCH

    # State filter test
    res_state = client.get("/v8/labs/search?state=Delhi")
    assert res_state.status_code == 200
    assert any("Delhi" in l["state"] or "Ghaziabad" in l["city"] or "Delhi" in l["city"] for l in res_state.get_json().get("laboratories", []))


# =========================================================================
# 6. REVERSE STANDARD LOOKUP & KNOWLEDGE GRAPH
# =========================================================================
def test_reverse_standard_lookup(client):
    """Verify reverse lookup by IS number returns complete specifications."""
    res = client.get("/v8/standards/reverse?standard=IS4246")
    assert res.status_code == 200
    data = res.get_json()
    assert data["found"] is True
    assert data["standard_number"] == "IS 4246"
    assert "Domestic Gas Cooking" in data["title"]
    assert len(data["requirements"]) >= 3
    assert len(data["testing_parameters"]) >= 3


def test_dynamic_knowledge_graph(client):
    """Verify dynamic knowledge graph generation with nodes and edges."""
    res = client.get("/v8/knowledge-graph?product=gas%20stove")
    assert res.status_code == 200
    data = res.get_json()
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    assert len(nodes) >= 5
    assert len(edges) >= 4
    node_types = {n["type"] for n in nodes}
    assert "product" in node_types
    assert "standard" in node_types
    assert "scheme" in node_types


# =========================================================================
# 7. COMPLIANCE INTELLIGENCE V4 (ASSESSMENTS & PASSPORTS)
# =========================================================================
def test_compliance_assessment_and_passport(client):
    """Verify assessment generation, SQLite database storage, and passport retrieval."""
    payload = {
        "product": "Gas Stove",
        "model": "GS-2026-PRO",
        "manufacturer": "Apex Kitchen Appliances Ltd",
        "standard_number": "IS 4246",
        "checklist": {
            "Gas soundness and leakage prevention at rated working pressure": True,
            "Thermal efficiency (minimum 68% for domestic burners)": True,
            "Combustion characteristics (CO/CO2 ratio not exceeding 0.02)": True,
            "Surface temperature limits on control knobs and body parts": True,
            "Flame stability, flash back and flame lift resistance": False,
            "Durability of pan supports and mechanical stability": True
        }
    }
    res = client.post("/v4/assess", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assessment_id = data.get("assessment_id")
    assert assessment_id is not None
    assert assessment_id.startswith("BIS-")
    assert data.get("score") > 0

    # Retrieve passport
    pass_res = client.get(f"/v4/passport/{assessment_id}")
    assert pass_res.status_code == 200
    pass_data = pass_res.get_json()
    assert pass_data.get("assessment_id") == assessment_id
    assert pass_data.get("product") == "Gas Stove"


# =========================================================================
# 8. ADVANCED WORKFLOWS V5 (MARK, LABEL, TEST REPORT, SELF-TEST)
# =========================================================================
def test_mark_verification(client):
    """Verify ISI and CM/L mark screening."""
    res = client.post("/v5/verify-mark", json={
        "text": "Manufactured per IS 4246 CM/L-8400123456 Standard Mark",
        "licence": "CM/L-8400123456"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data.get("cm_l_detected") is True or len(data.get("cm_l_numbers", [])) > 0


def test_test_report_parsing(client):
    """Verify test report numerical parameter extraction."""
    res = client.post("/v5/test-report", json={
        "standard": "IS 4246",
        "text": "Thermal efficiency: 69.2%\nGas leakage test: Passed at 0.07 bar\nCO/CO2 ratio: 0.015"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert len(data.get("measurements", [])) > 0


def test_v5_self_test(client):
    """Verify platform live self-test runs and reports status."""
    res = client.get("/v5/self-test")
    assert res.status_code == 200
    data = res.get_json()
    assert data.get("ok") is True or data.get("status") == "PASS"


# =========================================================================
# 9. MULTILINGUAL AI ASSISTANT & LOCAL RAG
# =========================================================================
def test_ai_chat_and_rag(client):
    """Verify multi-turn grounded chat with Indian Standards references."""
    res = client.post("/chat", json={
        "message": "What testing parameters apply to electric kettles under IS 302-2-15?",
        "language": "English"
    })
    assert res.status_code == 200
    data = res.get_json()
    reply = data.get("reply") or data.get("response", "")
    assert len(reply) > 20
    assert "IS 302" in reply or "kettle" in reply.lower() or len(data.get("retrieved", [])) > 0
    assert data.get("disclaimer") is not None
