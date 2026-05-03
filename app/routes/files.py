"""
routes/files.py - User-facing file endpoints.

All endpoints require a valid x-api-key header (Factor 15).
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException, status

from app.auth import require_api_key
from app.models.schemas import UploadResponse, FileRecord, FileListResponse, ErrorResponse
from app.services import upload_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["Files"])


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a file for validation",
    responses={
        401: {"model": ErrorResponse, "description": "Missing or invalid API key"},
        422: {"description": "Validation error (e.g. no file provided)"},
    },
)
async def upload_file(
    file: UploadFile = File(..., description="The file to validate"),
    user_id: Optional[str] = Query(None, description="Optional caller user ID"),
    _: str = Depends(require_api_key),
):
    """
    Upload a file for validation.

    The file is accepted immediately and queued for async validation.
    Poll `GET /files/{file_id}` to retrieve the validation result.

    **Auth:** `x-api-key` header required.
    """
    logger.info("POST /files/upload — filename=%s user_id=%s", file.filename, user_id)
    result = await upload_service.handle_upload(file, user_id)
    return result


@router.get(
    "/{file_id}",
    response_model=FileRecord,
    summary="Get validation result for a specific file",
    responses={
        401: {"model": ErrorResponse, "description": "Missing or invalid API key"},
        404: {"model": ErrorResponse, "description": "File not found"},
    },
)
async def get_file(
    file_id: str,
    _: str = Depends(require_api_key),
):
    """
    Retrieve the validation status and details for a previously uploaded file.

    **Auth:** `x-api-key` header required.
    """
    logger.info("GET /files/%s", file_id)
    record = await upload_service.get_file_record(file_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"File '{file_id}' not found.")
    return record


@router.get(
    "",
    response_model=FileListResponse,
    summary="List upload history for the current user",
    responses={
        401: {"model": ErrorResponse, "description": "Missing or invalid API key"},
    },
)
async def list_files(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    _: str = Depends(require_api_key),
):
    """
    Return all uploaded files associated with the caller.
    Optionally filter by `user_id` query parameter.

    **Auth:** `x-api-key` header required.
    """
    logger.info("GET /files — user_id=%s", user_id)
    files = await upload_service.list_user_files(user_id)
    return FileListResponse(total=len(files), files=files)
