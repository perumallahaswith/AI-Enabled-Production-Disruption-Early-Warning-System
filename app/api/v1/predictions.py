"""Disruption Risk Prediction Endpoints."""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Body
import pandas as pd

from app.services.data_ingestion import get_fused_data
from app.services.early_warning import get_early_warning_engine
from app.services.root_cause import RootCauseService
from app.services.business_impact import BusinessImpactService
from app.services.recommendation import RecommendationService

router = APIRouter()


@router.get("/live", summary="Get Live Early Warning Predictions for all Fab Machinery")
def get_live_predictions() -> List[Dict[str, Any]]:
    """Return real-time disruption predictions, risk scores, root cause, and recommendations."""
    df = get_fused_data()
    engine = get_early_warning_engine()
    rc_service = RootCauseService()
    bi_service = BusinessImpactService()
    rec_service = RecommendationService()

    latest_df = df.sort_values(by="Timestamp").groupby("Machine_ID").last().reset_index()
    
    predictions = []
    for _, row in latest_df.iterrows():
        row_dict = row.to_dict()
        eval_res = engine.evaluate_telemetry(row_dict)
        mach_id = str(row["Machine_ID"])
        risk = eval_res["composite_risk_score"]
        
        causes = rc_service.attribute_causes(row_dict, top_n=3)
        top_cause_name = causes[0]["factor_name"] if causes else "Normal Operation"
        
        impact = bi_service.estimate_impact(risk, row_dict)
        recs = rec_service.generate_recommendations(mach_id, risk, top_cause_name, row_dict)

        predictions.append({
            "machine_id": mach_id,
            "machine_name": str(row.get("Machine_Name", f"Tool {mach_id}")),
            "process_stage": str(row.get("Process_Stage", "General")),
            "evaluation": eval_res,
            "top_contributing_factors": causes,
            "business_impact": impact,
            "recommendations": recs,
            "timestamp": str(row["Timestamp"]),
        })

    predictions.sort(key=lambda x: x["evaluation"]["composite_risk_score"], reverse=True)
    return predictions


@router.post("/score", summary="Score Custom / What-If Telemetry Payload")
def score_custom_telemetry(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Score an ad-hoc or simulated machine telemetry dictionary."""
    engine = get_early_warning_engine()
    rc_service = RootCauseService()
    bi_service = BusinessImpactService()
    rec_service = RecommendationService()

    eval_res = engine.evaluate_telemetry(payload)
    mach_id = str(payload.get("Machine_ID", "SIM_TOOL"))
    risk = eval_res["composite_risk_score"]
    
    causes = rc_service.attribute_causes(payload, top_n=3)
    top_cause_name = causes[0]["factor_name"] if causes else "Process Deviation"
    impact = bi_service.estimate_impact(risk, payload)
    recs = rec_service.generate_recommendations(mach_id, risk, top_cause_name, payload)

    return {
        "evaluation": eval_res,
        "contributing_factors": causes,
        "business_impact": impact,
        "recommendations": recs,
    }
