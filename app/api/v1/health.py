"""Health and Diagnostics API Endpoints.

Provides comprehensive operational health status, database ping,
and fab telemetry readiness check.
"""

from datetime import datetime, timezone
import os
import platform
from fastapi import APIRouter, status
from pydantic import BaseModel, Field
from typing import Dict, Any

from app.config import settings
from app.database import check_db_connection

router = APIRouter()


class HealthResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "healthy"})
    timestamp: str
    environment: str
    version: str
    fab: Dict[str, Any]
    database: Dict[str, Any]
    system: Dict[str, Any]


@router.get(
    "/",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get System Health and Fab Status",
    description="Returns real-time health diagnostics for the semiconductor early warning platform.",
)
async def get_health_status() -> HealthResponse:
    """Check health of the backend API, database, and fab environment."""
    db_connected = check_db_connection()
    
    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        timestamp=datetime.now(timezone.utc).isoformat(),
        environment=settings.APP_ENV,
        version=settings.APP_VERSION,
        fab={
            "name": settings.FAB_NAME,
            "location": settings.FAB_LOCATION,
            "currency": settings.DEFAULT_CURRENCY,
            "cost_per_wafer": settings.COST_PER_WAFER,
            "downtime_cost_per_hour": settings.DOWNTIME_COST_PER_HOUR,
        },
        database={
            "connected": db_connected,
            "url_type": "sqlite" if settings.DATABASE_URL.startswith("sqlite") else "postgresql",
        },
        system={
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "llm_enabled": settings.LLM_ENABLED,
            "smtp_enabled": settings.SMTP_ENABLED,
        },
    )


@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness Probe",
)
async def liveness_probe() -> Dict[str, str]:
    """Kubernetes / Docker Liveness Probe."""
    return {"status": "alive"}


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness Probe",
)
async def readiness_probe() -> Dict[str, Any]:
    """Kubernetes / Docker Readiness Probe."""
    db_ok = check_db_connection()
    return {
        "ready": db_ok,
        "database": "connected" if db_ok else "unreachable",
    }
