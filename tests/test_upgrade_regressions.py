"""Regression tests for the SIH demo-critical SmartGuide journeys."""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import app


def test_mobile_phone_finds_electronics_standard():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.post("/v8/product-intelligence", json={"query": "mobile phone"})
        assert response.status_code == 200
        data = response.get_json()
        assert data["classification"] != "NON_PRODUCT"
        candidates = data.get("candidate_standards", [])
        numbers = " ".join(str(x.get("standard_number", "")) for x in candidates)
        assert numbers, "mobile phone must not silently return an empty standards list"
        assert "62368" in numbers or "16046" in numbers or "13252" in numbers


def test_mobile_phone_typo_and_aliases_do_not_crash():
    app.config["TESTING"] = True
    with app.test_client() as client:
        for query in ["smartphone", "cell phone", "mobile handset", "moblie phone"]:
            response = client.post("/v8/product-intelligence", json={"query": query})
            assert response.status_code == 200
            data = response.get_json()
            assert data.get("classification") != "NON_PRODUCT"
            assert data.get("candidate_standards") is not None


def test_lab_search_returns_official_verification_handoff():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/v8/labs/search?standard=IS%2FIEC%2062368-1")
        assert response.status_code == 200
        data = response.get_json()
        assert data.get("laboratories") is not None
        resources = data.get("official_resources", {})
        assert resources.get("bis_lims_search") or data.get("official_lims_search")


def test_universal_product_rejects_unrelated_standard_substitution():
    """An unknown product such as mouse must not inherit a mobile-phone result."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.post("/v5/product-intelligence", json={"description": "mouse"})
        assert response.status_code == 200
        data = response.get_json()
        assert data.get("classification") != "NON_PRODUCT"
        numbers = " ".join(str(x.get("standard_number", "")) for x in data.get("ranked_standards", []))
        products = " ".join(str(x.get("product", "")) for x in data.get("ranked_standards", []))
        assert "mobile" not in products.lower()
        assert "16046" not in numbers
        assert "13252" not in numbers


def test_advanced_features_share_universal_product_context():
    """Product-aware advanced workflows expose one common product context."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.post("/v5/procurement", json={"product": "mouse", "hs_code": "8471"})
        assert response.status_code == 200
        data = response.get_json()
        context = data.get("universal_product_context") or {}
        assert context.get("resolved_product") == "mouse"
        assert data.get("universal_product_gateway", {}).get("enabled") is True
