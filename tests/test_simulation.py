"""Test suite for what-if simulation and alerts endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_alerts_endpoint():
    """Verify alerts list and structure."""
    response = client.get("/api/v1/alerts/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_simulation_run():
    """Verify disruption scenario execution."""
    payload = {
        "scenario_type": "tool_degradation",
        "machine_id": "M03",
        "temperature_delta": 25.0,
        "vibration_delta": 0.8,
        "efficiency_drop_pct": 30.0,
        "material_shortage_severity": 0.5
    }
    response = client.post("/api/v1/simulation/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "simulated" in data
    assert "timeline_progression" in data
    assert data["simulated"]["composite_risk_score"] > data["baseline"]["composite_risk_score"]


def test_spc_endpoint():
    """Verify SPC control chart endpoint for M01."""
    response = client.get("/api/v1/spc/M01?sensor=Temperature&points=48")
    assert response.status_code == 200
    data = response.json()
    assert "ucl" in data
    assert "lcl" in data
    assert "process_mean" in data
    assert "moving_average" in data
