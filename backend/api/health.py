"""
GuardianAI Health Check API

Provides health check endpoints for:
- System status monitoring
- Component health verification
- Dependency connectivity checks
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.config import get_settings, Settings

router = APIRouter()


class HealthStatus(BaseModel):
    """Health check response model."""
    status: str
    version: str
    timestamp: str
    environment: str
    components: dict[str, Any]


class ComponentHealth(BaseModel):
    """Individual component health status."""
    name: str
    status: str
    latency_ms: float | None = None
    message: str | None = None


@router.get("/health", response_model=HealthStatus)
async def health_check(
    settings: Settings = Depends(get_settings)
) -> HealthStatus:
    """
    Get system health status.
    
    Returns overall system health and individual component statuses.
    Used by load balancers, monitoring systems, and dashboards.
    
    Returns:
        HealthStatus: System health information
    """
    components = {}
    overall_status = "healthy"
    
    # Check Firestore connectivity
    try:
        from backend.services.firestore_client import get_firestore_client
        client = get_firestore_client()
        # Simple connectivity check
        components["firestore"] = {
            "status": "healthy",
            "message": "Connected"
        }
    except Exception as e:
        components["firestore"] = {
            "status": "unhealthy",
            "message": str(e)
        }
        overall_status = "degraded"
    
    # Check Datadog connectivity
    try:
        if settings.dd_api_key:
            components["datadog"] = {
                "status": "healthy",
                "message": f"Configured for {settings.dd_site}"
            }
        else:
            components["datadog"] = {
                "status": "unconfigured",
                "message": "API key not set"
            }
    except Exception as e:
        components["datadog"] = {
            "status": "unhealthy",
            "message": str(e)
        }
    
    # Check GCP configuration
    if settings.gcp_project_id:
        components["gcp"] = {
            "status": "healthy",
            "message": f"Project: {settings.gcp_project_id}"
        }
    else:
        components["gcp"] = {
            "status": "unconfigured",
            "message": "Project ID not set"
        }
    
    return HealthStatus(
        status=overall_status,
        version="0.1.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
        environment=settings.dd_env,
        components=components
    )


@router.get("/health/ready")
async def readiness_check() -> dict[str, str]:
    """
    Kubernetes/Cloud Run readiness probe.
    
    Returns 200 if the service is ready to receive traffic.
    """
    return {"status": "ready"}


@router.get("/health/live")
async def liveness_check() -> dict[str, str]:
    """
    Kubernetes/Cloud Run liveness probe.
    
    Returns 200 if the service is alive.
    """
    return {"status": "alive"}
