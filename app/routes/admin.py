"""
routes/admin.py - Admin-only endpoints.

All endpoints require a valid x-admin-key header (Factor 15).
"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status

from app.auth import require_admin_key
from app.models.schemas import (
    FileListResponse,
    AlertListResponse,
    AlertRecord,
    ErrorResponse,
)
from app.services import upload_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])

# Mock alert data — replace with DB query when Member 1's DB is ready
_MOCK_ALERTS = [
    AlertRecord(
        alert_id="alert-001",
        file_id="mock-file-003",
        filename="report.pdf",
        reason="Extension mismatch: claimed .pdf but magic bytes indicate executable.",
        detected_at=datetime(2025, 1, 3, 14, 0, 4, tzinfo=timezone.utc),
        user_id="user-demo",
    )
]


@router.get(
    "/uploads",
    response_model=FileListResponse,
    summary="View all uploads (admin)",
    responses={
        403: {"model": ErrorResponse, "description": "Invalid or missing admin key"},
    },
)
async def admin_list_uploads(
    _: str = Depends(require_admin_key),
):
    """
    Return every upload record across all users.

    **Auth:** `x-admin-key` header required.
    """
    logger.info("GET /admin/uploads — admin access")
    files = await upload_service.list_all_files()
    return FileListResponse(total=len(files), files=files)


@router.get(
    "/alerts",
    response_model=AlertListResponse,
    summary="View suspicious upload alerts (admin)",
    responses={
        403: {"model": ErrorResponse, "description": "Invalid or missing admin key"},
    },
)
async def admin_list_alerts(
    _: str = Depends(require_admin_key),
):
    """
    Return all alerts flagged by the validation engine for suspicious files.

    **Auth:** `x-admin-key` header required.
    """
    logger.info("GET /admin/alerts — admin access")
    return AlertListResponse(total=len(_MOCK_ALERTS), alerts=_MOCK_ALERTS)
