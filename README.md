# Gateway Service
### Secure File Validation System — SWE 455 Cloud Applications Engineering

**Role:** Member 3 — API, Auth & Docs Lead  
**Responsible for:** Gateway service, authentication, monitoring endpoints, REST API documentation, OpenAPI/Swagger, admin APIs, 15-Factor sections 11, 13, 14, 15.

---

## Project Overview

This is the **Gateway Service** for the Secure File Validation System. It is the single
entry point for all client-facing API requests. It handles:

- Receiving file upload requests from users
- Delegating validation to Member 2's Validation Engine
- Returning results stored by Member 1's database
- Protecting endpoints with API key authentication
- Exposing health, readiness, and metrics for monitoring

---

## Features

| Feature                     | Status       | Notes                                    |
|-----------------------------|--------------|------------------------------------------|
| File upload endpoint        | ✅ Implemented | Returns mock `pending` status for now   |
| File status lookup          | ✅ Implemented | Returns mock records                     |
| Upload history list         | ✅ Implemented | Returns mock records                     |
| Admin upload viewer         | ✅ Implemented | Returns all mock records                 |
| Admin suspicious alerts     | ✅ Implemented | Returns mock alert records               |
| API key auth (user)         | ✅ Implemented | `x-api-key` header                       |
| Admin key auth              | ✅ Implemented | `x-admin-key` header                     |
| Health check                | ✅ Implemented | `/health`                                |
| Readiness check             | ✅ Implemented | `/ready`                                 |
| Runtime metrics             | ✅ Implemented | `/metrics`                               |
| Swagger / OpenAPI UI        | ✅ Implemented | Auto-generated at `/docs`                |
| Structured stdout logging   | ✅ Implemented | Factor 11 compliant                      |
| Docker container            | ✅ Implemented | Exposes port 8000                        |

---

## API Summary

| Method | Path                   | Auth          | Description                        |
|--------|------------------------|---------------|------------------------------------|
| POST   | `/files/upload`        | `x-api-key`   | Upload a file for validation       |
| GET    | `/files/{file_id}`     | `x-api-key`   | Get validation result for a file   |
| GET    | `/files`               | `x-api-key`   | List upload history                |
| GET    | `/admin/uploads`       | `x-admin-key` | View all uploads (admin)           |
| GET    | `/admin/alerts`        | `x-admin-key` | View suspicious alerts (admin)     |
| GET    | `/health`              | None          | Liveness check                     |
| GET    | `/ready`               | None          | Readiness check                    |
| GET    | `/metrics`             | None          | Runtime metrics                    |

---

## Environment Variables

Copy `.env.example` to `.env` and set your values:

```bash
cp .env.example .env
```

| Variable               | Description              | Default            |
|------------------------|--------------------------|--------------------|
| `API_KEY`              | User API key             | `student-demo-key` |
| `ADMIN_API_KEY`        | Admin API key            | `admin-demo-key`   |
| `APP_ENV`              | Environment name         | `development`      |
| `LOG_LEVEL`            | Logging verbosity        | `INFO`             |
| `VALIDATION_SERVICE_URL` | Member 2 service URL   | `http://validation-service:8001` |
| `DATABASE_URL`         | Member 1 database URL    | `sqlite:///./dev.db` |

---

## How to Run Locally

### Prerequisites
- Python 3.11+

### Steps

```bash
# 1. Clone and enter the directory
cd gateway-service

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment
cp .env.example .env

# 5. Run the server
uvicorn app.main:app --reload --port 8000
```

The API is now available at: `http://localhost:8000`  
Swagger UI: `http://localhost:8000/docs`

---

## How to Run with Docker

```bash
# Build the image
docker build -t gateway-service .

# Run the container
docker run -p 8000:8000 \
  -e API_KEY=student-demo-key \
  -e ADMIN_API_KEY=admin-demo-key \
  -e APP_ENV=production \
  gateway-service
```

---

## How to Run Tests

```bash
# Install dependencies (if not done)
pip install -r requirements.txt

# Run all tests
pytest tests/ -v
```

---

## Example curl Commands

### Upload a file
```bash
curl -X POST http://localhost:8000/files/upload \
  -H "x-api-key: student-demo-key" \
  -F "file=@./myfile.pdf"
```

### Get file status
```bash
curl http://localhost:8000/files/mock-file-001 \
  -H "x-api-key: student-demo-key"
```

### List my uploads
```bash
curl "http://localhost:8000/files?user_id=user-demo" \
  -H "x-api-key: student-demo-key"
```

### Admin: view all uploads
```bash
curl http://localhost:8000/admin/uploads \
  -H "x-admin-key: admin-demo-key"
```

### Admin: view alerts
```bash
curl http://localhost:8000/admin/alerts \
  -H "x-admin-key: admin-demo-key"
```

### Health check
```bash
curl http://localhost:8000/health
```

### Metrics
```bash
curl http://localhost:8000/metrics
```

---

## Integration Notes

### Connecting to Member 2 (Validation Engine)

In `app/services/upload_service.py`, find the `handle_upload` function.
Replace the `TODO` comment with an HTTP call to Member 2's service:

```python
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"{settings.validation_service_url}/validate",
        files={"file": (file.filename, content, file.content_type)},
    )
```

### Connecting to Member 1 (Database / S3)

In `app/services/upload_service.py`, replace the mock `_MOCK_STORE` lookups
with database queries using `asyncpg` or SQLAlchemy async:

```python
record = await db.fetch_one(
    "SELECT * FROM uploads WHERE file_id = $1", file_id
)
```

---

## Demo Script (Member 3's Part)

Use this during the live demonstration:

```bash
# Step 1: Show health
curl http://localhost:8000/health

# Step 2: Upload a file (user endpoint with auth)
curl -X POST http://localhost:8000/files/upload \
  -H "x-api-key: student-demo-key" \
  -F "file=@./test.pdf"

# Step 3: Show auth rejection
curl http://localhost:8000/files \
  -H "x-api-key: wrong-key"
# → 401 Unauthorized

# Step 4: Admin access
curl http://localhost:8000/admin/uploads \
  -H "x-admin-key: admin-demo-key"

# Step 5: Show metrics
curl http://localhost:8000/metrics

# Step 6: Open Swagger UI
open http://localhost:8000/docs
```

---

## Documentation Index

| Document                         | Description                                |
|----------------------------------|--------------------------------------------|
| `docs/openapi.yaml`              | OpenAPI 3.0 specification                  |
| `docs/api_documentation.md`      | Full REST API reference with examples      |
| `docs/auth_design.md`            | Authentication design and upgrade path     |
| `docs/monitoring_logging.md`     | Logging and telemetry design               |
| `docs/factor_mapping_member3.md` | 15-Factor mapping for factors 11, 13, 14, 15 |
