"""
routes/health.py - Observability endpoints (Factor 11, Factor 14).

These endpoints are publicly accessible (no auth required) so that
load balancers, ECS health checks, and Kubernetes probes can use them.
"""

import logging
from fastapi import APIRouter

from app.config import get_settings
from app.models.schemas import HealthResponse, ReadinessResponse, MetricsResponse
from app.services.monitoring_service import get_metrics, get_readiness

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Observability"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Basic liveness check",
)
async def health():
    """
    Returns 200 OK if the service process is running.
    Used by load balancers and container orchestrators for liveness probes.
    """
    settings = get_settings()
    logger.debug("GET /health")
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness check — verifies downstream dependencies",
)
async def ready():
    """
    Returns 200 OK only when all downstream dependencies (DB, validation service)
    are reachable. Used by orchestrators to decide whether to send traffic.
    """
    logger.debug("GET /ready")
    return get_readiness()


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="Application runtime metrics",
)
async def metrics():
    """
    Returns counters for uploads, rejections, and service uptime.
    Can be scraped by Prometheus or forwarded to CloudWatch / Grafana.
    """
    logger.debug("GET /metrics")
    return get_metrics()
