"""Model Evaluation and Metrics API Endpoints."""

import json
import os
from typing import Dict, Any
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/metrics", summary="Get ML Model Evaluation Metrics and Diagnostics")
def get_model_metrics() -> Dict[str, Any]:
    """Retrieve measured evaluation metrics (PR-AUC, ROC-AUC, F1, Confusion Matrix)."""
    metrics_path = "models/metadata/model_metrics.json"
    if not os.path.exists(metrics_path):
        raise HTTPException(status_code=404, detail="Model metrics file not found. Ensure models have been trained.")
    
    with open(metrics_path, "r") as f:
        data = json.load(f)
    return data
