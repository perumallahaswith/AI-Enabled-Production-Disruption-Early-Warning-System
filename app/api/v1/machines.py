"""Machine Telemetry and Asset Registry API Endpoints."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
import pandas as pd

from app.services.data_ingestion import get_fused_data
from app.services.early_warning import get_early_warning_engine

router = APIRouter()


@router.get("/", summary="List all Fab Machines with Live Status")
def list_machines() -> List[Dict[str, Any]]:
    """Return all 20 fab tools with latest sensor readings and computed risk status."""
    df = get_fused_data()
    engine = get_early_warning_engine()
    
    # Get latest record for each machine
    latest_df = df.sort_values(by="Timestamp").groupby("Machine_ID").last().reset_index()
    
    results = []
    for _, row in latest_df.iterrows():
        eval_res = engine.evaluate_telemetry(row.to_dict())
        results.append({
            "machine_id": str(row["Machine_ID"]),
            "machine_name": str(row.get("Machine_Name", f"Tool {row['Machine_ID']}")),
            "process_stage": str(row.get("Process_Stage", "General")),
            "status": str(row.get("Machine_Status", "Running")),
            "risk_score": eval_res["composite_risk_score"],
            "severity": eval_res["severity"],
            "severity_color": eval_res["severity_color"],
            "ml_probability": eval_res["ml_disruption_probability"],
            "anomaly_score": eval_res["anomaly_score"],
            "temperature": float(round(float(row.get("Temperature", 0)), 1)),
            "vibration": float(round(float(row.get("Vibration", 0)), 2)),
            "efficiency_pct": float(round(float(row.get("Machine_Efficiency_Pct", 90)), 1)),
            "days_since_maintenance": float(round(float(row.get("Days_Since_Maintenance", 10)), 0)),
            "last_seen": str(row["Timestamp"]),
        })
    
    # Sort by risk score descending
    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return results


@router.get("/{machine_id}", summary="Get Machine Telemetry and History")
def get_machine_detail(machine_id: str, limit: int = Query(48, description="Number of historical time points")) -> Dict[str, Any]:
    """Retrieve detailed telemetry time series and health summary for a specific machine."""
    df = get_fused_data()
    mach_df = df[df["Machine_ID"] == machine_id].sort_values(by="Timestamp")
    
    if mach_df.empty:
        raise HTTPException(status_code=404, detail=f"Machine '{machine_id}' not found.")
    
    engine = get_early_warning_engine()
    latest_row = mach_df.iloc[-1].to_dict()
    eval_res = engine.evaluate_telemetry(latest_row)
    
    history_df = mach_df.tail(limit)
    history = [
        {
            "timestamp": str(r["Timestamp"]),
            "temperature": float(round(float(r.get("Temperature", 0)), 1)),
            "vibration": float(round(float(r.get("Vibration", 0)), 3)),
            "pressure": float(round(float(r.get("Pressure", 0)), 2)),
            "power": float(round(float(r.get("Power_Consumption", 0)), 1)),
            "breakdown_risk": int(r.get("Breakdown_Risk_Label", 0)),
        }
        for _, r in history_df.iterrows()
    ]
    
    return {
        "machine_id": machine_id,
        "machine_name": str(latest_row.get("Machine_Name", f"Tool {machine_id}")),
        "process_stage": str(latest_row.get("Process_Stage", "General")),
        "manufacturer": str(latest_row.get("Manufacturer", "OEM")),
        "evaluation": eval_res,
        "history": history,
    }
