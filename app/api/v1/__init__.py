"""API v1 Router Setup.

Aggregates all domain endpoints (health, machines, alerts, predictions,
spc, simulation, model metrics).
"""

from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.machines import router as machines_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.predictions import router as predictions_router
from app.api.v1.spc import router as spc_router
from app.api.v1.simulation import router as simulation_router
from app.api.v1.models_info import router as models_router

api_v1_router = APIRouter()

api_v1_router.include_router(health_router, prefix="/health", tags=["Health & Diagnostics"])
api_v1_router.include_router(machines_router, prefix="/machines", tags=["Fab Machinery & Telemetry"])
api_v1_router.include_router(alerts_router, prefix="/alerts", tags=["Early Warning & Alerts"])
api_v1_router.include_router(predictions_router, prefix="/predictions", tags=["Disruption Predictions"])
api_v1_router.include_router(spc_router, prefix="/spc", tags=["Statistical Process Control (SPC)"])
api_v1_router.include_router(simulation_router, prefix="/simulation", tags=["What-If Disruption Simulation"])
api_v1_router.include_router(models_router, prefix="/model", tags=["Model Performance & Metrics"])
