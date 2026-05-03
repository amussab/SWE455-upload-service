from __future__ import annotations

import base64
import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from email.parser import BytesParser
from email.policy import default
from typing import Any

import boto3


JSON_HEADERS = {"Content-Type": "application/json"}
MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", "5242880"))


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    path = event.get("rawPath") or event.get("path") or "/"
    headers = normalize_headers(event.get("headers", {}))

    if method == "GET" and path == "/health":
        return json_response(200, {"status": "healthy", "service": "upload-service"})

    if method == "GET" and path == "/ready":
        return json_response(
            200,
            {
                "status": "ready",
                "dependencies": {
                    "storage": "configured" if upload_bucket_name() else "missing",
                    "database": "configured" if uploads_table_name() else "missing",
                    "queue": "s3-event-notification",
                },
            },
        )

    if method == "GET" and path == "/metrics":
        return json_response(200, metrics_response())

    if method == "POST" and path in {"/files/upload", "/upload"}:
        auth_error = require_header(headers, "x-api-key", os.environ.get("API_KEY", "student-demo-key"), 401)
        if auth_error:
            return auth_error
        return handle_upload(event, headers)

    if method == "GET" and path == "/files":
        auth_error = require_header(headers, "x-api-key", os.environ.get("API_KEY", "student-demo-key"), 401)
        if auth_error:
            return auth_error
        query = event.get("queryStringParameters") or {}
        return json_response(200, list_files_response(query.get("user_id")))

    if method == "GET" and path.startswith("/files/"):
        auth_error = require_header(headers, "x-api-key", os.environ.get("API_KEY", "student-demo-key"), 401)
        if auth_error:
            return auth_error
        file_id = path.rsplit("/", 1)[-1]
        record = get_file_record(file_id)
        if not record:
            return json_response(404, {"detail": f"File '{file_id}' not found."})
        return json_response(200, record)

    if method == "GET" and path == "/admin/uploads":
        auth_error = require_header(headers, "x-admin-key", os.environ.get("ADMIN_API_KEY", "admin-demo-key"), 403)
        if auth_error:
            return auth_error
        return json_response(200, list_files_response(None))

    if method == "GET" and path == "/admin/alerts":
        auth_error = require_header(headers, "x-admin-key", os.environ.get("ADMIN_API_KEY", "admin-demo-key"), 403)
        if auth_error:
            return auth_error
        return json_response(200, alert_response())

    return json_response(404, {"detail": f"No route for {method} {path}"})


def handle_upload(event: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    bucket = upload_bucket_name()
    table = uploads_table_name()

    if not bucket:
        return json_response(500, {"detail": "UPLOAD_BUCKET_NAME is not configured."})

    file_part = extract_uploaded_file(event, headers)
    if not file_part:
        return json_response(422, {"detail": "No file field was found in the multipart request."})

    if len(file_part["content"]) > MAX_UPLOAD_BYTES:
        return json_response(413, {"detail": f"File size exceeded {MAX_UPLOAD_BYTES} bytes."})

    file_id = str(uuid.uuid4())
    user_id = (event.get("queryStringParameters") or {}).get("user_id") or "anonymous"
    uploaded_at = now_iso()
    s3_key = f"uploads/{file_id}/{file_part['filename']}"

    boto3.client("s3").put_object(
        Bucket=bucket,
        Key=s3_key,
        Body=file_part["content"],
        ContentType=file_part["content_type"],
        Metadata={
            "upload-id": file_id,
            "user-id": user_id,
            "original-filename": file_part["filename"],
        },
    )

    record = {
        "file_id": file_id,
        "upload_id": file_id,
        "user_id": user_id,
        "filename": file_part["filename"],
        "original_filename": file_part["filename"],
        "s3_bucket": bucket,
        "s3_key": s3_key,
        "status": "PENDING",
        "size_bytes": len(file_part["content"]),
        "uploaded_at": uploaded_at,
        "content_sha256": hashlib.sha256(file_part["content"]).hexdigest(),
    }

    if table:
        boto3.resource("dynamodb").Table(table).put_item(Item=record)

    return json_response(
        202,
        {
            "file_id": file_id,
            "status": "pending",
            "message": "File received and queued for validation.",
            "filename": file_part["filename"],
            "size_bytes": len(file_part["content"]),
            "uploaded_at": uploaded_at,
        },
    )


def extract_uploaded_file(event: dict[str, Any], headers: dict[str, str]) -> dict[str, Any] | None:
    content_type = headers.get("content-type", "")
    if "multipart/form-data" not in content_type:
        return None

    body = event.get("body") or ""
    body_bytes = base64.b64decode(body) if event.get("isBase64Encoded") else body.encode("utf-8")
    message = BytesParser(policy=default).parsebytes(
        b"Content-Type: " + content_type.encode("utf-8") + b"\r\n\r\n" + body_bytes
    )

    for part in message.iter_parts():
        if part.get_param("name", header="content-disposition") != "file":
            continue
        filename = part.get_filename() or "upload.bin"
        return {
            "filename": filename,
            "content_type": part.get_content_type() or "application/octet-stream",
            "content": part.get_payload(decode=True) or b"",
        }

    return None


def get_file_record(file_id: str) -> dict[str, Any] | None:
    table = uploads_table_name()
    if not table:
        return None

    item = boto3.resource("dynamodb").Table(table).get_item(Key={"file_id": file_id}).get("Item")
    return api_file_record(item) if item else None


def list_files_response(user_id: str | None) -> dict[str, Any]:
    records = scan_file_records()
    if user_id:
        records = [record for record in records if record.get("user_id") == user_id]
    return {"total": len(records), "files": records}


def alert_response() -> dict[str, Any]:
    alerts = [
        {
            "alert_id": f"alert-{record['file_id']}",
            "file_id": record["file_id"],
            "filename": record["filename"],
            "reason": record.get("rejection_reason") or "Suspicious upload detected.",
            "detected_at": record.get("validated_at") or record.get("uploaded_at"),
            "user_id": record.get("user_id"),
        }
        for record in scan_file_records()
        if record.get("status") == "suspicious"
    ]
    return {"total": len(alerts), "alerts": alerts}


def metrics_response() -> dict[str, Any]:
    records = scan_file_records()
    counts = {"accepted": 0, "rejected": 0, "suspicious": 0, "pending": 0}
    for record in records:
        status = record.get("status", "pending")
        if status in counts:
            counts[status] += 1
    return {"uptime_seconds": 0, "total_uploads": len(records), **counts}


def scan_file_records() -> list[dict[str, Any]]:
    table = uploads_table_name()
    if not table:
        return []

    response = boto3.resource("dynamodb").Table(table).scan()
    return [api_file_record(item) for item in response.get("Items", [])]


def api_file_record(item: dict[str, Any]) -> dict[str, Any]:
    status = str(item.get("status", "PENDING")).lower()
    return {
        "file_id": item.get("file_id") or item.get("upload_id"),
        "filename": item.get("filename") or item.get("original_filename") or "unknown",
        "status": status,
        "size_bytes": int(item.get("size_bytes", 0)),
        "user_id": item.get("user_id"),
        "uploaded_at": item.get("uploaded_at") or item.get("created_at") or now_iso(),
        "validated_at": item.get("validated_at"),
        "rejection_reason": item.get("rejection_reason") or item.get("reason"),
    }


def require_header(headers: dict[str, str], name: str, expected: str, status_code: int) -> dict[str, Any] | None:
    if headers.get(name) == expected:
        return None
    return json_response(status_code, {"detail": f"Invalid or missing {name} header."})


def normalize_headers(headers: dict[str, str]) -> dict[str, str]:
    return {key.lower(): value for key, value in headers.items()}


def upload_bucket_name() -> str:
    return os.environ.get("UPLOAD_BUCKET_NAME", "")


def uploads_table_name() -> str:
    return os.environ.get("UPLOADS_TABLE_NAME", "")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    return {"statusCode": status_code, "headers": JSON_HEADERS, "body": json.dumps(body, default=str)}
