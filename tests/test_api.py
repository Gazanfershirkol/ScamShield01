"""
Integration Tests for ScamShield AI — FastAPI REST Endpoints

Tests:
1. POST /api/v1/analyze (valid dual, text-only, URL-only, empty, invalid boundaries)
2. GET  /api/v1/health (operational status, model readiness)
3. GET  /api/v1/evaluation (benchmark metrics, confusion matrix)
4. GET  / (root index / discovery)
5. GET  /docs (OpenAPI interactive documentation)
"""

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


@pytest.fixture(scope="module")
def client():
    """Provides a TestClient instance for interacting with the FastAPI app."""
    return TestClient(app)


def test_health_check(client):
    """GET /api/v1/health returns HTTP 200 with status: 'healthy' and model_loaded: True."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == settings.APP_NAME
    assert data["version"] == settings.APP_VERSION
    assert data["model_loaded"] is True
    assert "TF-IDF" in data["classifier_type"]
    assert "timestamp" in data


def test_analyze_valid_dual_payload(client):
    """POST /api/v1/analyze returns HTTP 200 and schema compliant JSON for dual input."""
    payload = {
        "text": "URGENT: Your bank account is locked. Verify immediately at http://secure-bank.xyz/login to avoid penalties.",
        "url": "http://secure-bank.xyz/login",
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["verdict"] == "likely scam"
    assert data["risk_score"] >= settings.VERDICT_SCAM_THRESHOLD
    assert 0.0 <= data["confidence"] <= 1.0
    assert isinstance(data["summary"], str)
    assert isinstance(data["evidence"], list)
    assert len(data["evidence"]) >= 1
    assert isinstance(data["recommended_action"], str)
    assert "analyzed_at" in data

    # Modality breakdowns
    assert data["text_analysis"]["provided"] is True
    assert data["text_analysis"]["risk_score"] > 50
    assert len(data["text_analysis"]["detected_patterns"]) >= 1

    assert data["url_analysis"]["provided"] is True
    assert data["url_analysis"]["risk_score"] > 50
    assert data["url_analysis"]["target_domain"] == "secure-bank.xyz"


def test_analyze_text_only(client):
    """POST /api/v1/analyze with only text succeeds and marks url as not provided."""
    payload = {
        "text": "Hey, are we still meeting for lunch at 1 PM today?",
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["verdict"] == "likely safe"
    assert data["risk_score"] < settings.VERDICT_REVIEW_THRESHOLD
    assert data["text_analysis"]["provided"] is True
    assert data["url_analysis"]["provided"] is False


def test_analyze_url_only(client):
    """POST /api/v1/analyze with only url succeeds and marks text as not provided."""
    payload = {
        "url": "http://192.168.1.1/login",
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["verdict"] in ("needs review", "likely scam")
    assert data["text_analysis"]["provided"] is False
    assert data["url_analysis"]["provided"] is True
    assert data["url_analysis"]["is_ip_address"] is True


def test_analyze_empty_payload(client):
    """Both text and url empty -> returns HTTP 422 Unprocessable Entity."""
    # Completely empty payload
    response = client.post("/api/v1/analyze", json={})
    assert response.status_code == 422

    # Keys present but null
    response = client.post("/api/v1/analyze", json={"text": None, "url": None})
    assert response.status_code == 422


def test_analyze_whitespace_only_payload(client):
    """Payload with only whitespace characters -> returns HTTP 422 Unprocessable Entity."""
    response = client.post("/api/v1/analyze", json={"text": "   ", "url": " \t\n "})
    assert response.status_code == 422
    assert "non-whitespace" in response.text


def test_analyze_payload_length_limits(client):
    """Inputs exceeding configured boundaries return HTTP 422."""
    too_long_url = "http://example.com/" + ("a" * 2050)
    response = client.post("/api/v1/analyze", json={"url": too_long_url})
    assert response.status_code == 422


def test_evaluation_metrics(client):
    """GET /api/v1/evaluation returns valid benchmark metrics and confusion matrix."""
    response = client.get("/api/v1/evaluation")
    assert response.status_code == 200
    data = response.json()

    assert "dataset" in data
    assert data["dataset"]["total_samples"] == 2500
    assert data["dataset"]["train_samples"] == 1750
    assert data["dataset"]["val_samples"] == 375
    assert data["dataset"]["test_samples"] == 375
    assert data["dataset"]["stratified"] is True

    assert "metrics" in data
    assert 0.0 <= data["metrics"]["accuracy"] <= 1.0
    assert 0.0 <= data["metrics"]["f1_score"] <= 1.0

    assert "confusion_matrix" in data
    assert "true_positives" in data["confusion_matrix"]
    assert "true_negatives" in data["confusion_matrix"]

    assert "threshold_strategy" in data
    assert data["threshold_strategy"]["scam_threshold"] == 0.75
    assert data["threshold_strategy"]["review_threshold"] == 0.35


def test_root_endpoint(client):
    """GET / returns HTTP 200 serving the frontend dashboard index.html."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "ScamShield AI" in response.text
    assert "Inspection Workspace" in response.text


def test_static_assets_served(client):
    """Static CSS and JS files must be accessible via /static/ mount."""
    css_res = client.get("/static/css/style.css")
    assert css_res.status_code == 200
    assert "--bg-primary" in css_res.text

    js_res = client.get("/static/js/app.js")
    assert js_res.status_code == 200
    assert "PRESETS" in js_res.text


def test_openapi_docs(client):
    """GET /docs returns HTTP 200 serving Swagger UI."""
    response = client.get("/docs")
    assert response.status_code == 200

