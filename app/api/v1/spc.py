"""Statistical Process Control API Endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Query
import pandas as pd

from app.services.data_ingestion import get_fused_data
from app.services.spc_engine import SPCEngine

router = APIRouter()


@router.get("/{machine_id}", summary="Get SPC Control Limits and Excursions for a Machine")
def get_machine_spc(
    machine_id: str,
    sensor: str = Query("Temperature", description="Sensor name (e.g. Temperature, Vibration, Pressure, Power_Consumption)"),
    points: int = Query(72, description="Number of historical time points")
) -> Dict[str, Any]:
    """Calculate Upper/Lower Control Limits, moving averages, and out-of-spec excursions."""
    df = get_fused_data()
    mach_df = df[df["Machine_ID"] == machine_id].sort_values(by="Timestamp").tail(points)
    
    if mach_df.empty:
        raise HTTPException(status_code=404, detail=f"Machine '{machine_id}' not found.")
    
    if sensor not in mach_df.columns:
        sensor = "Temperature"

    values = mach_df[sensor].fillna(0.0).tolist()
    timestamps = [str(t) for t in mach_df["Timestamp"].tolist()]

    spc = SPCEngine()
    chart_data = spc.compute_control_chart(values, timestamps, sensor_name=sensor)
    chart_data["machine_id"] = machine_id
    chart_data["timestamps"] = timestamps
    chart_data["raw_values"] = [float(round(v, 2)) for v in values]
    
    return chart_data
