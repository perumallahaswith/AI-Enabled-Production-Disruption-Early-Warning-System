"""Test suite for ML prediction and early warning endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_machines():
    """Verify machine list endpoint returns 20 machines with computed risk scores."""
    response = client.get("/api/v1/machines/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 20
    first = data[0]
    assert "machine_id" in first
    assert "risk_score" in first
    assert "severity" in first


def test_machine_detail():
    """Verify detail telemetry endpoint for M01."""
    response = client.get("/api/v1/machines/M01")
    assert response.status_code == 200
    data = response.json()
    assert data["machine_id"] == "M01"
    assert "history" in data
    assert len(data["history"]) > 0


def test_live_predictions():
    """Verify live predictions endpoint returns all tools."""
    response = client.get("/api/v1/predictions/live")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 20
    assert "top_contributing_factors" in data[0]
    assert "business_impact" in data[0]
    assert "recommendations" in data[0]


def test_custom_score_endpoint():
    """Verify scoring a custom telemetry vector."""
    payload = {
        "Machine_ID": "M03",
        "Temperature": 385.0,
        "Vibration": 0.95,
        "Pressure": 1.25,
        "Power_Consumption": 140.0,
        "Machine_Efficiency_Pct": 75.0,
        "Cycle_Time_Sec": 85.0,
        "Wafer_Count": 25.0,
        "Days_Since_Maintenance": 28.0
    }
    response = client.post("/api/v1/predictions/score", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "evaluation" in data
    assert data["evaluation"]["composite_risk_score"] > 20.0
    assert len(data["contributing_factors"]) > 0
