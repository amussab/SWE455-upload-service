"""
upload_service.py - Handles file upload business logic.

Currently uses mock data. Replace the TODO sections with real calls to:
  - Member 2's validation engine (HTTP or message queue)
  - Member 1's database/S3 storage

The interface is intentionally kept stable so integration requires
minimal changes to this file.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import UploadFile
from app.models.schemas import (
    UploadResponse,
    FileRecord,
    ValidationStatus,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory store — replace with a real DB call (Member 1 / Member 2 scope)
# ---------------------------------------------------------------------------
_MOCK_STORE: List[FileRecord] = [
    FileRecord(
        file_id="mock-file-001",
        filename="invoice.pdf",
        status=ValidationStatus.ACCEPTED,
        size_bytes=102400,
        user_id="user-demo",
        uploaded_at=datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        validated_at=datetime(2025, 1, 1, 10, 0, 5, tzinfo=timezone.utc),
    ),
    FileRecord(
        file_id="mock-file-002",
        filename="malware.exe",
        status=ValidationStatus.REJECTED,
        size_bytes=512000,
        user_id="user-demo",
        uploaded_at=datetime(2025, 1, 2, 9, 0, 0, tzinfo=timezone.utc),
        validated_at=datetime(2025, 1, 2, 9, 0, 3, tzinfo=timezone.utc),
        rejection_reason="File type not allowed: .exe",
    ),
    FileRecord(
        file_id="mock-file-003",
        filename="report.pdf",
        status=ValidationStatus.SUSPICIOUS,
        size_bytes=307200,
        user_id="user-demo",
        uploaded_at=datetime(2025, 1, 3, 14, 0, 0, tzinfo=timezone.utc),
        validated_at=datetime(2025, 1, 3, 14, 0, 4, tzinfo=timezone.utc),
        rejection_reason="Extension mismatch detected.",
    ),
]


async def handle_upload(file: UploadFile, user_id: Optional[str]) -> UploadResponse:
    """
    Accept a file, forward it to the validation engine, and return a response.

    Integration point:
      1. Save the file to S3 / object storage (Member 1 provides bucket URL).
      2. Call Member 2's validation service via HTTP or publish to an SQS queue.
      3. Persist the record to the database (Member 1 provides DB connection).
    """
    file_id = str(uuid.uuid4())
    content = await file.read()
    size_bytes = len(content)

    logger.info(
        "File upload received",
        extra={
            "file_id": file_id,
            "filename": file.filename,
            "size_bytes": size_bytes,
            "user_id": user_id,
        },
    )

    # TODO: Upload content to S3
    # await s3_client.put_object(Bucket=BUCKET, Key=file_id, Body=content)

    # TODO: Send to validation service (Member 2)
    # async with httpx.AsyncClient() as client:
    #     await client.post(f"{VALIDATION_SERVICE_URL}/validate", ...)

    # TODO: Persist record to database (Member 1)
    # await db.execute(INSERT_QUERY, ...)

    return UploadResponse(
        file_id=file_id,
        status=ValidationStatus.PENDING,
        message="File received and queued for validation.",
        filename=file.filename or "unknown",
        size_bytes=size_bytes,
        uploaded_at=datetime.now(timezone.utc),
    )


async def get_file_record(file_id: str) -> Optional[FileRecord]:
    """
    Retrieve the validation result for a specific file.

    Integration point: replace mock lookup with a database query.
    """
    # TODO: return await db.fetch_one("SELECT * FROM uploads WHERE file_id = $1", file_id)
    for record in _MOCK_STORE:
        if record.file_id == file_id:
            return record
    return None


async def list_user_files(user_id: Optional[str]) -> List[FileRecord]:
    """
    Return upload history for a user.

    Integration point: replace with a filtered database query.
    """
    # TODO: return await db.fetch_all("SELECT * FROM uploads WHERE user_id = $1", user_id)
    return _MOCK_STORE


async def list_all_files() -> List[FileRecord]:
    """
    Return all uploads (admin view).

    Integration point: replace with an unfiltered database query.
    """
    # TODO: return await db.fetch_all("SELECT * FROM uploads ORDER BY uploaded_at DESC")
    return _MOCK_STORE
