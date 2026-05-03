# REST API Documentation — Gateway Service
## SWE 455 Cloud Applications Engineering | Member 3

---

## Base URL

| Environment | URL |
|-------------|-----|
| Local       | `http://localhost:8000` |
| Production  | `https://api.your-cloud-domain.com` |

Interactive Swagger UI is available at: `{BASE_URL}/docs`

---

## Authentication

The Gateway Service implements two access tiers (Factor 15: Auth & Authorization).

| Tier  | Header        | Scope                          |
|-------|---------------|-------------------------------|
| User  | `x-api-key`   | Upload files, view own history |
| Admin | `x-admin-key` | View all uploads, view alerts  |

Keys are supplied through environment variables (`API_KEY`, `ADMIN_API_KEY`).
They are never hardcoded in source code.

In production this can be replaced with:
- AWS Cognito (user pools + JWT tokens)
- IAM-based request signing
- OAuth 2.0 / OIDC

---

## Endpoints

---

### 1. POST /files/upload

**Purpose:** Upload a file for security validation.

**Auth:** `x-api-key` header required.

**Request:**

```
POST /files/upload
Content-Type: multipart/form-data
x-api-key: student-demo-key
```

| Field     | Type   | Required | Description                       |
|-----------|--------|----------|-----------------------------------|
| `file`    | binary | Yes      | The file to validate              |
| `user_id` | string | No       | Query param — caller's user ID    |

**Response (202 Accepted):**

```json
{
  "file_id": "f1a2b3c4-d5e6-7890-abcd-ef1234567890",
  "status": "pending",
  "message": "File received and queued for validation.",
  "filename": "report.pdf",
  "size_bytes": 204800,
  "uploaded_at": "2025-01-01T12:00:00Z"
}
```

**Error responses:**

| Code | Reason                          |
|------|---------------------------------|
| 401  | Missing or invalid `x-api-key`  |
| 422  | No file attached to request     |

**curl example:**
```bash
curl -X POST http://localhost:8000/files/upload \
  -H "x-api-key: student-demo-key" \
  -F "file=@/path/to/your/file.pdf" \
  -F "user_id=user-001"
```

---

### 2. GET /files/{file_id}

**Purpose:** Retrieve the validation result for a previously uploaded file.

**Auth:** `x-api-key` header required.

**Request:**
```
GET /files/f1a2b3c4-d5e6-7890-abcd-ef1234567890
x-api-key: student-demo-key
```

**Response (200 OK):**
```json
{
  "file_id": "f1a2b3c4-d5e6-7890-abcd-ef1234567890",
  "filename": "report.pdf",
  "status": "accepted",
  "size_bytes": 204800,
  "user_id": "user-001",
  "uploaded_at": "2025-01-01T12:00:00Z",
  "validated_at": "2025-01-01T12:00:05Z",
  "rejection_reason": null
}
```

**Status values:**

| Status      | Meaning                                              |
|-------------|------------------------------------------------------|
| `pending`   | File queued, validation not yet complete             |
| `accepted`  | File passed all validation checks                    |
| `rejected`  | File failed at least one check (type, size, MIME)    |
| `suspicious`| Extension/MIME mismatch or other spoofing indicator  |

**Error responses:**

| Code | Reason                         |
|------|--------------------------------|
| 401  | Missing or invalid `x-api-key` |
| 404  | `file_id` does not exist       |

**curl example:**
```bash
curl http://localhost:8000/files/mock-file-001 \
  -H "x-api-key: student-demo-key"
```

---

### 3. GET /files

**Purpose:** List upload history for the authenticated user.

**Auth:** `x-api-key` header required.

**Request:**
```
GET /files?user_id=user-001
x-api-key: student-demo-key
```

**Response (200 OK):**
```json
{
  "total": 2,
  "files": [
    {
      "file_id": "mock-file-001",
      "filename": "invoice.pdf",
      "status": "accepted",
      "size_bytes": 102400,
      "user_id": "user-demo",
      "uploaded_at": "2025-01-01T10:00:00Z",
      "validated_at": "2025-01-01T10:00:05Z",
      "rejection_reason": null
    }
  ]
}
```

**curl example:**
```bash
curl "http://localhost:8000/files?user_id=user-demo" \
  -H "x-api-key: student-demo-key"
```

---

### 4. GET /admin/uploads *(Admin)*

**Purpose:** View all upload records across all users.

**Auth:** `x-admin-key` header required.

**Response (200 OK):**
```json
{
  "total": 3,
  "files": [ ... ]
}
```

**curl example:**
```bash
curl http://localhost:8000/admin/uploads \
  -H "x-admin-key: admin-demo-key"
```

---

### 5. GET /admin/alerts *(Admin)*

**Purpose:** View all suspicious upload alerts flagged by the validation engine.

**Auth:** `x-admin-key` header required.

**Response (200 OK):**
```json
{
  "total": 1,
  "alerts": [
    {
      "alert_id": "alert-001",
      "file_id": "mock-file-003",
      "filename": "report.pdf",
      "reason": "Extension mismatch: claimed .pdf but magic bytes indicate executable.",
      "detected_at": "2025-01-03T14:00:04Z",
      "user_id": "user-demo"
    }
  ]
}
```

**curl example:**
```bash
curl http://localhost:8000/admin/alerts \
  -H "x-admin-key: admin-demo-key"
```

---

### 6. GET /health

**Purpose:** Liveness check — verifies the service process is running.

**Auth:** None required.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "gateway-service",
  "version": "1.0.0",
  "environment": "development"
}
```

---

### 7. GET /ready

**Purpose:** Readiness check — verifies all downstream dependencies are reachable.

**Auth:** None required.

**Response (200 OK):**
```json
{
  "status": "ready",
  "dependencies": {
    "database": "ok",
    "validation_service": "ok",
    "storage": "ok"
  }
}
```

---

### 8. GET /metrics

**Purpose:** Runtime metrics for monitoring dashboards.

**Auth:** None required.

**Response (200 OK):**
```json
{
  "uptime_seconds": 3623.45,
  "total_uploads": 120,
  "accepted": 98,
  "rejected": 15,
  "suspicious": 5,
  "pending": 2
}
```

---

## Error Response Format

All error responses follow a consistent structure:

```json
{
  "detail": "Human-readable error message."
}
```
