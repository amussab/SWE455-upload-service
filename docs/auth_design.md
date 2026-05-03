# Authentication & Authorization Design
## Gateway Service — Member 3: API, Auth & Docs Lead
### SWE 455 | Factor 15

---

## Overview

The Gateway Service implements two-tier API key authentication to protect all
non-observability endpoints. This satisfies **Factor 15: Authentication and Authorization**
of the 15-Factor Application methodology.

---

## Access Tiers

### Tier 1 — User Access (`x-api-key`)

Applied to:
- `POST /files/upload`
- `GET /files/{file_id}`
- `GET /files`

The caller must include the header `x-api-key: <value>` with every request.
The value is compared against the `API_KEY` environment variable.
A missing or incorrect key returns **HTTP 401 Unauthorized**.

### Tier 2 — Admin Access (`x-admin-key`)

Applied to:
- `GET /admin/uploads`
- `GET /admin/alerts`

The caller must include the header `x-admin-key: <value>` with every request.
The value is compared against the `ADMIN_API_KEY` environment variable.
A missing or incorrect key returns **HTTP 403 Forbidden**.

### Public Endpoints (no auth)

- `GET /health`
- `GET /ready`
- `GET /metrics`

These are intentionally public so that load balancers, ECS health checks,
and monitoring tools can reach them without credentials.

---

## Implementation

Authentication is implemented as **FastAPI dependency functions** in `app/auth.py`.

```python
def require_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
```

Each protected route declares the dependency:

```python
@router.get("/files", dependencies=[Depends(require_api_key)])
```

This approach keeps authentication logic completely separate from business logic.

---

## Secret Management

Keys are **never hardcoded** in source code. They are injected via environment variables:

```
API_KEY=student-demo-key
ADMIN_API_KEY=admin-demo-key
```

In production:
- Store keys in **AWS Secrets Manager** or **SSM Parameter Store**
- Inject into ECS task definitions as environment variables
- Terraform (Member 1) handles provisioning these secrets

---

## Production Upgrade Path

The current API key design is intentionally simple for demo purposes.
It can be upgraded to any of the following without changing the route logic:

| Option              | Description                                        |
|---------------------|----------------------------------------------------|
| **JWT Tokens**      | Replace key check with `python-jose` JWT validation|
| **AWS Cognito**     | Use Cognito User Pools + ID tokens                 |
| **IAM Auth**        | Sign requests with AWS SigV4                       |
| **OAuth 2.0/OIDC**  | Full authorization flow with refresh tokens        |

The FastAPI dependency injection pattern makes this swap straightforward:
only `auth.py` needs to change.

---

## Security Considerations

1. Keys are transmitted in HTTP headers, not URL parameters (prevents logging exposure).
2. Comparison uses direct string equality — for production, use `secrets.compare_digest()` to prevent timing attacks.
3. Admin and user keys are distinct — compromising a user key does not grant admin access.
4. Observability endpoints (`/health`, `/ready`, `/metrics`) are public but expose no sensitive data.
