"""Test suite for health and diagnostics endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


def test_root_endpoint():
    """Verify root gateway information endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "platform" in data
    assert data["version"] == settings.APP_VERSION
    assert "health_check" in data


def test_health_endpoint():
    """Verify system health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "fab" in data
    assert data["fab"]["name"] == settings.FAB_NAME
    assert data["database"]["connected"] is True
    assert "system" in data


def test_api_v1_health_endpoint():
    """Verify /api/v1/health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_liveness_readiness():
    """Verify k8s / container liveness and readiness probes."""
    live_res = client.get("/health/live")
    assert live_res.status_code == 200
    assert live_res.json()["status"] == "alive"

    ready_res = client.get("/health/ready")
    assert ready_res.status_code == 200
    assert ready_res.json()["ready"] is True
