"""
schemas.py - Pydantic models for request and response bodies.
These define the API contract (Factor 13: API First).
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class ValidationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SUSPICIOUS = "suspicious"


# ── File Upload ──────────────────────────────────────────────

class UploadResponse(BaseModel):
    file_id: str = Field(..., description="Unique identifier for the uploaded file")
    status: ValidationStatus = Field(..., description="Current validation status")
    message: str = Field(..., description="Human-readable status message")
    filename: str = Field(..., description="Original filename as uploaded")
    size_bytes: int = Field(..., description="File size in bytes")
    uploaded_at: datetime = Field(..., description="UTC timestamp of upload")

    model_config = {"json_schema_extra": {
        "example": {
            "file_id": "f1a2b3c4-d5e6-7890-abcd-ef1234567890",
            "status": "pending",
            "message": "File received and queued for validation.",
            "filename": "report.pdf",
            "size_bytes": 204800,
            "uploaded_at": "2025-01-01T12:00:00Z",
        }
    }}


class FileRecord(BaseModel):
    file_id: str
    filename: str
    status: ValidationStatus
    size_bytes: int
    user_id: Optional[str] = None
    uploaded_at: datetime
    validated_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    model_config = {"json_schema_extra": {
        "example": {
            "file_id": "f1a2b3c4-d5e6-7890-abcd-ef1234567890",
            "filename": "report.pdf",
            "status": "accepted",
            "size_bytes": 204800,
            "user_id": "user-001",
            "uploaded_at": "2025-01-01T12:00:00Z",
            "validated_at": "2025-01-01T12:00:05Z",
            "rejection_reason": None,
        }
    }}


class FileListResponse(BaseModel):
    total: int
    files: List[FileRecord]


# ── Admin ────────────────────────────────────────────────────

class AlertRecord(BaseModel):
    alert_id: str
    file_id: str
    filename: str
    reason: str
    detected_at: datetime
    user_id: Optional[str] = None

    model_config = {"json_schema_extra": {
        "example": {
            "alert_id": "alert-001",
            "file_id": "f1a2b3c4-d5e6-7890-abcd-ef1234567890",
            "filename": "malicious.exe",
            "reason": "Extension mismatch: claimed .pdf but magic bytes indicate executable.",
            "detected_at": "2025-01-01T12:00:10Z",
            "user_id": "user-002",
        }
    }}


class AlertListResponse(BaseModel):
    total: int
    alerts: List[AlertRecord]


# ── Health & Metrics ─────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str


class ReadinessResponse(BaseModel):
    status: str
    dependencies: dict


class MetricsResponse(BaseModel):
    uptime_seconds: float
    total_uploads: int
    accepted: int
    rejected: int
    suspicious: int
    pending: int


# ── Generic Error ────────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
