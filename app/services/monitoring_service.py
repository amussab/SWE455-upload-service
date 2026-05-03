"""
monitoring_service.py - Application telemetry (Factor 14).

Provides runtime metrics that can be scraped by Prometheus,
CloudWatch, or any monitoring backend.
"""

import time
from datetime import datetime, timezone
from app.models.schemas import MetricsResponse, ReadinessResponse

# Application start time — used to calculate uptime
_START_TIME: float = time.monotonic()
_START_WALL: datetime = datetime.now(timezone.utc)


def get_metrics() -> MetricsResponse:
    """
    Return simple counters about the application's runtime state.

    Integration point: replace mock counts with live queries from the database.
    Example:
        counts = await db.fetch_one("SELECT status, COUNT(*) FROM uploads GROUP BY status")
    """
    uptime = time.monotonic() - _START_TIME

    # TODO: replace with real DB aggregation
    return MetricsResponse(
        uptime_seconds=round(uptime, 2),
        total_uploads=3,
        accepted=1,
        rejected=1,
        suspicious=1,
        pending=0,
    )


def get_readiness() -> ReadinessResponse:
    """
    Check whether all downstream dependencies are reachable.

    Integration point: perform real health-checks against:
      - Database (Member 1)
      - Validation service (Member 2)
      - S3 bucket (Member 1)

    Example:
        db_ok = await db.execute("SELECT 1")
        val_ok = await httpx.get(VALIDATION_SERVICE_URL + "/health")
    """
    # TODO: replace mock statuses with real dependency pings
    return ReadinessResponse(
        status="ready",
        dependencies={
            "database": "ok (mock)",
            "validation_service": "ok (mock)",
            "storage": "ok (mock)",
        },
    )
