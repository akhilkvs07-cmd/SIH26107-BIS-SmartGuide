"""End-to-End User Journey Tests (Journeys A through G).

Verifies the 7 mandatory user journeys from the SIH26107 specification:
- Journey A: Manufacturer launches a new domestic appliance (Gas Stove)
- Journey B: Startup with an ambiguous product ('heater')
- Journey C: Importer bringing in IT/AV equipment (Laptop)
- Journey D: Consumer verifying a product in the market (ISI / CM-L)
- Journey E: Laboratory looking up test requirements & apparatus
- Journey F: Procurement officer preparing a tender (Tender specs & CoA)
- Journey G: Non-English speaking MSME owner (Hindi/Kannada/Telugu/Tamil)
"""

import json
import os
import sys
import pytest

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app_upgrade import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_journey_a_manufacturer_gas_stove(client):
    """Journey A: Manufacturer launches a new domestic gas stove."""
    # 1. Natural language query
    res = client.post("/v8/product-intelligence", json={
        "query": "We manufacture a 2-burner domestic LPG gas stove"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["classification"] == "CONFIDENTLY_RECOGNIZED"
    assert "4246" in data["top_standard"]["standard_number"]
    assert "Gas Stoves" in data["top_standard"]["qco_order"]

    # 2. Check laboratories for testing
    lab_res = client.get("/v8/labs/search?standard=IS4246")
    assert lab_res.status_code == 200
    lab_data = lab_res.get_json()
    assert lab_data["count"] >= 2
    assert any("Sahibabad" in l["city"] or "Mohali" in l["city"] or "Chennai" in l["city"] for l in lab_data["laboratories"])

    # 3. Create compliance assessment and passport
    assess_res = client.post("/v4/assess", json={
        "product": "Domestic Gas Stove",
        "model": "GS-2026-PRO",
        "manufacturer": "Bharat Cooking Appliances Ltd",
        "checks": {
            "Gas soundness and leakage prevention at rated working pressure": True,
            "Thermal efficiency (minimum 68% for domestic burners)": True,
            "Combustion characteristics (CO/CO2 ratio not exceeding 0.02)": True,
            "Surface temperature limits on control knobs and body parts": True,
            "Flame stability, flash back and flame lift resistance": True,
            "Durability of pan supports and mechanical stability": True
        }
    })
    assert assess_res.status_code == 200
    assess_data = assess_res.get_json()
    assert assess_data["status"] == "PASS"
    assert assess_data["risk"] == "LOW"
    assert assess_data["score"] == 100

    # 4. Verify passport
    pass_res = client.get(f"/v4/passport/{assess_data['assessment_id']}")
    assert pass_res.status_code == 200
    assert pass_res.get_json()["product"] == "Domestic Gas Stove"


def test_journey_b_startup_ambiguous_heater(client):
    """Journey B: Startup with ambiguous 'heater' input."""
    # 1. Initial ambiguous query
    res = client.post("/v8/product-intelligence", json={"query": "heater"})
    assert res.status_code == 200
    data = res.get_json()
    assert data.get("clarification_needed") is True or len(data.get("options", [])) >= 3
    options = data.get("options", [])
    assert any("water heater" in o["product"].lower() or "room heater" in o["product"].lower() for o in options)

    # 2. Clarified query for room heater
    res2 = client.post("/v8/product-intelligence", json={"query": "electric room heater for winter"})
    assert res2.status_code == 200
    data2 = res2.get_json()
    assert data2["classification"] == "CONFIDENTLY_RECOGNIZED"
    assert "302 (Part 2/Sec 30)" in data2["top_standard"]["standard_number"]


def test_journey_c_importer_laptop_crs(client):
    """Journey C: Importer bringing in IT/AV equipment (Laptop)."""
    # 1. Search product
    res = client.post("/v8/product-intelligence", json={"query": "Laptop computer with USB-C power delivery"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["classification"] == "CONFIDENTLY_RECOGNIZED"
    top_std = data["top_standard"]
    assert "62368" in top_std["standard_number"]
    assert "Scheme II" in top_std["scheme"] or "CRS" in top_std["scheme"]

    # 2. Importer role adaptation
    role_res = client.post("/v8/roles/adapt", json={"role": "importer", "product": "laptop"})
    assert role_res.status_code == 200
    role_data = role_res.get_json()
    assert "importer" in role_data["role"]["id"].lower()
    assert any("port" in a.lower() or "customs" in a.lower() or "fmcs" in a.lower() or "licence" in a.lower() for a in role_data["adapted_checklist"].get("role_specific_actions", []))


def test_journey_d_consumer_verification(client):
    """Journey D: Consumer verifying a product in the market."""
    # 1. Screen ISI / CM-L label
    res = client.post("/v5/verify-mark", json={
        "text": "Conforms to IS 4246 CM/L-8400123456 Made in India",
        "licence": "CM/L-8400123456"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data.get("cm_l_detected") is True
    assert "8400123456" in data.get("cm_l_numbers", [])
    assert data.get("official_care_url") is not None


def test_journey_e_laboratory_test_requirements(client):
    """Journey E: Laboratory looking up test requirements and apparatus."""
    res = client.get("/v8/standards/reverse?standard=IS302(Part2/Sec15)")
    assert res.status_code == 200
    data = res.get_json()
    assert data["found"] is True
    params = data.get("testing_parameters", [])
    assert len(params) >= 3
    assert any("leakage" in p.lower() or "dielectric" in p.lower() or "boil" in p.lower() for p in params)


def test_journey_f_procurement_officer_tender(client):
    """Journey F: Procurement officer preparing a tender."""
    res = client.post("/v5/procurement", json={
        "product": "PVC Insulated Cable",
        "hs_code": "8544",
        "raw_material": "Electrolytic Grade Copper Conductor"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert "checks" in data
    assert "IS 694" in str(data) or "pvc" in str(data).lower()


def test_journey_g_multilingual_msme(client):
    """Journey G: Multilingual MSME owner in regional languages."""
    languages = ["Hindi", "Kannada", "Telugu", "Tamil"]
    for lang in languages:
        res = client.post("/chat", json={
            "message": "Gas stove standards and safety tests",
            "language": lang
        })
        assert res.status_code == 200
        data = res.get_json()
        assert len(data.get("reply", "")) > 10
        assert data.get("disclaimer") is not None
