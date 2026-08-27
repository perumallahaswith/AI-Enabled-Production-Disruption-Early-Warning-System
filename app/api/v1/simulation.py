"""Disruption What-If Simulation API Endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, Body
from pydantic import BaseModel, Field

from app.services.data_ingestion import get_fused_data
from app.services.early_warning import get_early_warning_engine
from app.services.root_cause import RootCauseService
from app.services.business_impact import BusinessImpactService
from app.services.recommendation import RecommendationService

router = APIRouter()


class SimulationRequest(BaseModel):
    scenario_type: str = Field("tool_degradation", json_schema_extra={"example": "tool_degradation"})
    machine_id: str = Field("M03", json_schema_extra={"example": "M03"})
    temperature_delta: float = Field(0.0, json_schema_extra={"example": 15.0})
    vibration_delta: float = Field(0.0, json_schema_extra={"example": 0.65})
    efficiency_drop_pct: float = Field(0.0, json_schema_extra={"example": 20.0})
    material_shortage_severity: float = Field(0.0, json_schema_extra={"example": 0.0})


@router.post("/run", summary="Run Disruption Scenario Simulation")
def run_simulation(req: SimulationRequest) -> Dict[str, Any]:
    """Simulate the progression of a fab disruption and observe real-time risk escalation."""
    df = get_fused_data()
    mach_df = df[df["Machine_ID"] == req.machine_id].sort_values(by="Timestamp")
    
    baseline_row = mach_df.iloc[-1].to_dict() if not mach_df.empty else {
        "Machine_ID": req.machine_id, "Temperature": 350.0, "Vibration": 0.45,
        "Pressure": 1.0, "Power_Consumption": 120.0, "Machine_Efficiency_Pct": 95.0,
        "Cycle_Time_Sec": 60.0, "Wafer_Count": 25.0, "Days_Since_Maintenance": 15.0
    }

    # Baseline Evaluation
    engine = get_early_warning_engine()
    rc_service = RootCauseService()
    bi_service = BusinessImpactService()
    rec_service = RecommendationService()

    base_eval = engine.evaluate_telemetry(baseline_row)

    # Apply Injected Disruption
    sim_row = baseline_row.copy()
    if req.scenario_type == "false_data_disruption":
        sim_row["Vibration"] = float(sim_row.get("Vibration", 0.45)) + (req.vibration_delta if req.vibration_delta > 0 else 0.95)
        sim_row["Temperature"] = float(sim_row.get("Temperature", 350.0)) + (req.temperature_delta if req.temperature_delta > 0 else 28.0)
        sim_row["Pressure"] = float(sim_row.get("Pressure", 1.0)) + 0.45
        sim_row["False_Data_Flag"] = 1
        sim_row["Machine_Efficiency_Pct"] = max(30.0, float(sim_row.get("Machine_Efficiency_Pct", 95.0)) - (req.efficiency_drop_pct if req.efficiency_drop_pct > 0 else 30.0))
    else:
        sim_row["Temperature"] = float(sim_row.get("Temperature", 350.0)) + req.temperature_delta
        sim_row["Vibration"] = float(sim_row.get("Vibration", 0.45)) + req.vibration_delta
        sim_row["Machine_Efficiency_Pct"] = max(30.0, float(sim_row.get("Machine_Efficiency_Pct", 95.0)) - req.efficiency_drop_pct)
    if req.material_shortage_severity > 0:
        sim_row["Avg_Material_Quality_Pct"] = max(50.0, 95.0 - (req.material_shortage_severity * 40.0))
        sim_row["Min_Days_of_Stock"] = max(1.0, 14.0 - (req.material_shortage_severity * 12.0))

    sim_eval = engine.evaluate_telemetry(sim_row)
    sim_risk = sim_eval["composite_risk_score"]
    
    causes = rc_service.attribute_causes(sim_row, top_n=3)
    top_cause_name = causes[0]["factor_name"] if causes else "Injected Process Disruption"
    impact = bi_service.estimate_impact(sim_risk, sim_row)
    recs = rec_service.generate_recommendations(req.machine_id, sim_risk, top_cause_name, sim_row)

    # 4-Step Disruption Timeline Progression
    progression = [
        {"step": "T-0 (Baseline)", "risk_score": base_eval["composite_risk_score"], "status": base_eval["severity"]},
        {"step": "T+15m (Micro-Deviation)", "risk_score": float(round(base_eval["composite_risk_score"] + (sim_risk - base_eval["composite_risk_score"]) * 0.35, 1)), "status": "WATCH"},
        {"step": "T+30m (Drift Detected)", "risk_score": float(round(base_eval["composite_risk_score"] + (sim_risk - base_eval["composite_risk_score"]) * 0.70, 1)), "status": "HIGH"},
        {"step": "T+45m (Critical Excursion)", "risk_score": sim_risk, "status": sim_eval["severity"]},
    ]

    return {
        "scenario": req.scenario_type,
        "machine_id": req.machine_id,
        "baseline": base_eval,
        "simulated": sim_eval,
        "contributing_factors": causes,
        "business_impact": impact,
        "recommendations": recs,
        "timeline_progression": progression,
    }
