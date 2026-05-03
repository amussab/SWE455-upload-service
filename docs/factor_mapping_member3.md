# 15-Factor Application — Member 3 Factor Mapping
## Gateway Service | SWE 455 Cloud Applications Engineering

**Member 3 — API, Auth & Docs Lead**
Assigned factors: **11, 13, 14, 15**

---

## Factor 11: Logs

> *Treat logs as event streams.*

### Requirement
A 15-Factor application never manages its own log files. It writes all events
to `stdout` as an unbuffered stream. The execution environment routes, stores,
and aggregates those events.

### How the Gateway Service satisfies this factor

1. **stdout only.** The logging configuration in `app/main.py` explicitly writes to
   `sys.stdout`. There are no file handlers, no rotating log files, and no custom
   log sinks inside the application.

2. **Structured format.** Every log line follows the format:
   ```
   TIMESTAMP LEVEL MODULE MESSAGE
   ```
   Example:
   ```
   2025-01-01 12:00:01 INFO app.routes.files POST /files/upload — filename=report.pdf
   2025-01-01 12:00:01 WARNING app.auth Unauthorized access attempt with invalid API key.
   ```

3. **Runtime log routing.** In production, the AWS ECS task definition specifies
   the `awslogs` log driver. ECS automatically captures `stdout` output and forwards
   it to Amazon CloudWatch Logs — without any change to application code.

4. **Log level controlled by environment.** The `LOG_LEVEL` environment variable
   (Factor 3) controls verbosity. Setting `LOG_LEVEL=DEBUG` enables verbose output
   in development without code changes.

### Architecture flow
```
Application (stdout)
       ↓
ECS awslogs driver
       ↓
Amazon CloudWatch Logs
       ↓
CloudWatch Insights / Alarms
```

---

## Factor 13: API First

> *Design and document the API contract before implementation.*

### Requirement
Services should expose well-documented, stable APIs so that consumers and
team members can integrate against a known contract independently of the
implementation schedule.

### How the Gateway Service satisfies this factor

1. **API-first design.** The REST API endpoints, request/response schemas,
   authentication requirements, and status codes were defined in `docs/openapi.yaml`
   and `docs/api_documentation.md` before any route code was written.

2. **OpenAPI 3.0 specification.** The `docs/openapi.yaml` file is a complete,
   machine-readable API contract. Any team member or external tool can generate
   client SDKs, test stubs, or mock servers from it.

3. **Automatic Swagger UI.** FastAPI generates an interactive Swagger UI at
   `/docs` directly from the Pydantic models and route decorators. This UI
   always reflects the actual implementation — it cannot drift from the code.

4. **Stable integration surface.** Member 2 (validation engine) and Member 1
   (infrastructure / database) can integrate against the documented endpoints
   without waiting for this service to be deployed. They use the OpenAPI spec
   as the contract.

5. **Pydantic schemas as the single source of truth.** The `app/models/schemas.py`
   file defines all request and response shapes. FastAPI uses these models to:
   - Validate incoming requests
   - Serialize outgoing responses
   - Generate OpenAPI documentation
   
   One definition — three uses.

---

## Factor 14: Telemetry

> *Expose health, readiness, and metrics endpoints.*

### Requirement
A cloud-native service must make its runtime state observable without
requiring direct access to the host or the process.

### How the Gateway Service satisfies this factor

Three dedicated observability endpoints are implemented in `app/routes/health.py`:

| Endpoint  | Purpose                              | Consumer                          |
|-----------|--------------------------------------|-----------------------------------|
| `/health` | Liveness — is the process alive?     | ECS / ALB health checks           |
| `/ready`  | Readiness — are dependencies up?     | Load balancer routing decisions   |
| `/metrics`| Counters — uploads, rejections, etc. | CloudWatch / Prometheus / Grafana |

**Liveness (`/health`):**
Returns 200 if the application process is running. ECS uses this to decide
whether to restart the container.

**Readiness (`/ready`):**
Returns 200 only when the database, validation service, and storage are all
reachable. During startup or when a dependency is degraded, this returns a
non-200 status, causing the load balancer to stop routing traffic to this
instance.

**Metrics (`/metrics`):**
Returns counters aggregated from the database (mock data in current phase).
In production, these values are fetched from live DB queries and can be
forwarded to Prometheus, CloudWatch, or Grafana dashboards.

**No credentials required** for observability endpoints. Load balancers and
monitoring agents must reach them without authentication.

---

## Factor 15: Authentication and Authorization

> *Protect services using externally managed credentials.*

### Requirement
All non-public endpoints must require authentication. Credentials must
never be hardcoded — they are supplied by the runtime environment.

### How the Gateway Service satisfies this factor

1. **Two-tier API key authentication.**

   | Tier   | Header         | Protected Endpoints                                    |
   |--------|----------------|--------------------------------------------------------|
   | User   | `x-api-key`    | `POST /files/upload`, `GET /files`, `GET /files/{id}` |
   | Admin  | `x-admin-key`  | `GET /admin/uploads`, `GET /admin/alerts`              |
   | Public | *(none)*       | `/health`, `/ready`, `/metrics`                        |

2. **Environment-variable secrets.** The API keys are read exclusively from
   environment variables (`API_KEY`, `ADMIN_API_KEY`). They are never written
   in source code. The `.env.example` file shows the required variable names
   without real values.

3. **Dependency injection pattern.** Authentication logic lives in `app/auth.py`
   as FastAPI dependencies (`require_api_key`, `require_admin_key`). Routes
   declare these dependencies declaratively — business logic never handles auth.

4. **Separation of user and admin scopes.** A valid user key cannot access
   admin endpoints. A missing admin key returns HTTP 403 (not 401), making the
   distinction explicit.

5. **Production upgrade path.** Because auth is encapsulated in two dependency
   functions, upgrading to JWT, AWS Cognito, or IAM requires changing only
   `app/auth.py`. All routes continue to work without modification.

### Secret provisioning in production

```
AWS Secrets Manager
       ↓
Terraform (Member 1 — ECS task definition)
       ↓
Environment variable injected into container at runtime
       ↓
app/config.py reads API_KEY, ADMIN_API_KEY
       ↓
app/auth.py compares incoming header value
```

The application never knows how the secret is stored — it only reads from the
environment. This is the correct 15-Factor pattern.
