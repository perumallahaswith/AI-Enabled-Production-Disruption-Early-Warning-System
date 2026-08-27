"""Test suite for application configuration."""

import pytest
from app.config import get_settings, Settings


def test_settings_load():
    """Verify settings instance loads with expected defaults."""
    settings = get_settings()
    assert settings.APP_NAME is not None
    assert "Semiconductor" in settings.APP_NAME
    assert settings.API_V1_STR == "/api/v1"
    assert settings.THRESHOLD_CRITICAL == 100.0
    assert settings.COST_PER_WAFER > 0


def test_risk_weights_sum_normalized():
    """Verify risk weights sum approximately to 1.0."""
    settings = get_settings()
    total_weight = (
        settings.WEIGHT_PREDICTION_RISK
        + settings.WEIGHT_ANOMALY_SEVERITY
        + settings.WEIGHT_BUSINESS_IMPACT
        + settings.WEIGHT_TREND_ESCALATION
        + settings.WEIGHT_PRODUCTION_CRITICALITY
    )
    assert abs(total_weight - 1.0) < 0.001


def test_alert_recipients_parsing():
    """Verify comma-separated alert recipients parse cleanly into list."""
    settings = get_settings()
    recipients = settings.alert_recipients_list
    assert isinstance(recipients, list)
    assert len(recipients) > 0
