"""Business Impact and Financial Exposure Estimation Engine.

Translates machine risk, wafer throughput, and tool downtime into quantified
business impact, estimated wafer scrap, and financial exposure.
"""

from typing import Dict, Any
from app.config import settings


class BusinessImpactService:
    """Calculates operational and financial exposure for semiconductor disruptions."""

    def __init__(self):
        self.cost_per_wafer = settings.COST_PER_WAFER
        self.cost_per_lot = settings.COST_PER_LOT
        self.downtime_rate_hourly = settings.DOWNTIME_COST_PER_HOUR

    def estimate_impact(self, risk_score: float, machine_telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate scrap wafers, downtime, and dollar exposure for a given risk score."""
        risk_fraction = max(0.0, min(1.0, risk_score / 100.0))
        
        # Nominal tool capacity (e.g. 25 wafers/lot, 120 wafers/shift)
        wafer_count = float(machine_telemetry.get("Wafer_Count", machine_telemetry.get("wafer_count", 25.0)))
        cycle_time = float(machine_telemetry.get("Cycle_Time_Sec", machine_telemetry.get("cycle_time_sec", 60.0)))
        
        if risk_score < 25.0:
            affected_wafers = 0
            affected_lots = 0
            downtime_hours = 0.0
            scrap_rate_pct = 0.1
        elif risk_score < 50.0:
            affected_wafers = int(round(wafer_count * 0.15))
            affected_lots = 1
            downtime_hours = float(round(0.5 * risk_fraction, 1))
            scrap_rate_pct = 1.2
        elif risk_score < 75.0:
            affected_wafers = int(round(wafer_count * 0.6))
            affected_lots = 2
            downtime_hours = float(round(2.5 * risk_fraction, 1))
            scrap_rate_pct = 4.5
        else: # Critical
            affected_wafers = int(round(wafer_count * 1.8))
            affected_lots = max(2, int(round(affected_wafers / 25.0)))
            downtime_hours = float(round(6.0 * risk_fraction, 1))
            scrap_rate_pct = 12.8

        scrap_cost = float(round(affected_wafers * self.cost_per_wafer, 2))
        downtime_cost = float(round(downtime_hours * self.downtime_rate_hourly, 2))
        total_exposure = float(round(scrap_cost + downtime_cost, 2))

        return {
            "risk_score": float(round(risk_score, 1)),
            "estimated_affected_wafers": affected_wafers,
            "estimated_affected_lots": affected_lots,
            "expected_downtime_hours": downtime_hours,
            "estimated_scrap_rate_pct": scrap_rate_pct,
            "estimated_scrap_cost": scrap_cost,
            "estimated_downtime_cost": downtime_cost,
            "total_financial_exposure": total_exposure,
            "currency": settings.DEFAULT_CURRENCY,
            "is_estimate": True,
            "assumptions": {
                "cost_per_wafer": self.cost_per_wafer,
                "downtime_cost_per_hour": self.downtime_rate_hourly,
                "wafers_per_lot": 25,
            }
        }
