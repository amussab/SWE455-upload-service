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

import boto3
from fastapi import UploadFile
from botocore.exceptions import BotoCoreError, ClientError

from app.config import get_settings
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
    filename = file.filename or "unknown"
    uploaded_at = datetime.now(timezone.utc)

    logger.info(
        "File upload received",
        extra={
            "file_id": file_id,
            "filename": filename,
            "size_bytes": size_bytes,
            "user_id": user_id,
        },
    )

    settings = get_settings()

    if settings.upload_bucket_name:
        upload_to_s3(
            bucket_name=settings.upload_bucket_name,
            file_id=file_id,
            filename=filename,
            content=content,
            content_type=file.content_type,
            user_id=user_id,
        )
    else:
        logger.warning("UPLOAD_BUCKET_NAME is not set; using local mock upload behavior")

    record = FileRecord(
        file_id=file_id,
        filename=filename,
        status=ValidationStatus.PENDING,
        size_bytes=size_bytes,
        user_id=user_id,
        uploaded_at=uploaded_at,
    )

    if settings.uploads_table_name:
        save_pending_record(settings.uploads_table_name, record)
    else:
        _MOCK_STORE.append(record)

    return UploadResponse(
        file_id=file_id,
        status=ValidationStatus.PENDING,
        message="File received and queued for validation.",
        filename=filename,
        size_bytes=size_bytes,
        uploaded_at=uploaded_at,
    )


async def get_file_record(file_id: str) -> Optional[FileRecord]:
    """
    Retrieve the validation result for a specific file.

    Integration point: replace mock lookup with a database query.
    """
    settings = get_settings()
    if settings.uploads_table_name:
        return load_record(settings.uploads_table_name, file_id)

    for record in _MOCK_STORE:
        if record.file_id == file_id:
            return record
    return None


async def list_user_files(user_id: Optional[str]) -> List[FileRecord]:
    """
    Return upload history for a user.

    Integration point: replace with a filtered database query.
    """
    settings = get_settings()
    if settings.uploads_table_name:
        records = scan_records(settings.uploads_table_name)
    else:
        records = _MOCK_STORE

    if user_id:
        return [record for record in records if record.user_id == user_id]
    return records


async def list_all_files() -> List[FileRecord]:
    """
    Return all uploads (admin view).

    Integration point: replace with an unfiltered database query.
    """
    settings = get_settings()
    if settings.uploads_table_name:
        return scan_records(settings.uploads_table_name)
    return _MOCK_STORE


def upload_to_s3(
    *,
    bucket_name: str,
    file_id: str,
    filename: str,
    content: bytes,
    content_type: Optional[str],
    user_id: Optional[str],
) -> None:
    key = f"uploads/{file_id}/{filename}"
    metadata = {
        "upload-id": file_id,
        "original-filename": filename,
        "user-id": user_id or "anonymous",
    }

    try:
        boto3.client("s3").put_object(
            Bucket=bucket_name,
            Key=key,
            Body=content,
            ContentType=content_type or "application/octet-stream",
            Metadata=metadata,
        )
    except (BotoCoreError, ClientError):
        logger.exception("Failed to upload file %s to S3 bucket %s", file_id, bucket_name)
        raise


def save_pending_record(table_name: str, record: FileRecord) -> None:
    item = {
        "file_id": record.file_id,
        "upload_id": record.file_id,
        "user_id": record.user_id or "anonymous",
        "original_filename": record.filename,
        "filename": record.filename,
        "status": record.status.value.upper(),
        "size_bytes": record.size_bytes,
        "uploaded_at": record.uploaded_at.isoformat(),
    }

    boto3.resource("dynamodb").Table(table_name).put_item(Item=item)


def load_record(table_name: str, file_id: str) -> Optional[FileRecord]:
    response = boto3.resource("dynamodb").Table(table_name).get_item(Key={"file_id": file_id})
    item = response.get("Item")
    return file_record_from_item(item) if item else None


def scan_records(table_name: str) -> List[FileRecord]:
    response = boto3.resource("dynamodb").Table(table_name).scan()
    return [file_record_from_item(item) for item in response.get("Items", [])]


def file_record_from_item(item: dict) -> FileRecord:
    return FileRecord(
        file_id=item.get("file_id") or item.get("upload_id"),
        filename=item.get("filename") or item.get("original_filename") or "unknown",
        status=parse_status(item.get("status")),
        size_bytes=int(item.get("size_bytes", 0)),
        user_id=item.get("user_id"),
        uploaded_at=parse_datetime(item.get("uploaded_at")) or parse_datetime(item.get("created_at")) or datetime.now(timezone.utc),
        validated_at=parse_datetime(item.get("validated_at")),
        rejection_reason=item.get("rejection_reason") or item.get("reason"),
    )


def parse_status(value: Optional[str]) -> ValidationStatus:
    if not value:
        return ValidationStatus.PENDING

    normalized = value.lower()
    try:
        return ValidationStatus(normalized)
    except ValueError:
        return ValidationStatus.PENDING


def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None

    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None
