# Monitoring & Logging Design
## Gateway Service — Member 3: API, Auth & Docs Lead
### SWE 455 | Factor 11 & Factor 14

---

## Factor 11: Logs as Event Streams

### Principle

A 15-Factor application **never writes log files**. Instead, it writes all log output
to `stdout` as an unbuffered event stream. The execution environment — ECS, Kubernetes,
or any container runtime — is responsible for collecting, routing, and storing those logs.

### Implementation

The Gateway Service configures Python's standard `logging` module to write to `stdout`:

```python
logging.basicConfig(
    stream=sys.stdout,
    level=getattr(logging, log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
```

Every significant event produces a log line:

```
2025-01-01 12:00:01 INFO app.routes.files POST /files/upload — filename=report.pdf user_id=user-001
2025-01-01 12:00:01 WARNING app.auth Unauthorized access attempt with invalid API key.
```

### Cloud Log Collection

In production (deployed by Member 1 on AWS ECS):

```
Container stdout
      ↓
ECS Log Driver (awslogs)
      ↓
Amazon CloudWatch Logs
      ↓
CloudWatch Insights / Alarms / Dashboards
```

No code changes are needed to switch between local and cloud log routing.
The runtime handles it.

---

## Factor 14: Telemetry

### Principle

A production-grade service must expose data about its own health and runtime
behavior so that operators can monitor it without SSH access.

### Endpoints

#### GET /health — Liveness

Returns 200 if the process is alive. Used by:
- ECS container health checks
- ALB target group health checks
- Kubernetes liveness probes

```json
{
  "status": "healthy",
  "service": "gateway-service",
  "version": "1.0.0",
  "environment": "production"
}
```

#### GET /ready — Readiness

Returns 200 only when all downstream dependencies are reachable:
- Database (Member 1)
- Validation service (Member 2)
- S3 storage (Member 1)

When a dependency is down, this returns a non-200 status. The load balancer
stops routing traffic to the instance until it recovers.

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

#### GET /metrics — Runtime Metrics

Returns aggregated counters about the application's workload:

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

### Production Integration

| Tool             | Integration                                                   |
|------------------|---------------------------------------------------------------|
| **CloudWatch**   | Scrape `/metrics` via Lambda or use ECS container insights    |
| **Prometheus**   | Expose `/metrics` in Prometheus text format (future upgrade)  |
| **Grafana**      | Dashboard panels fed by Prometheus or CloudWatch              |
| **PagerDuty**    | CloudWatch alarms trigger on high rejection rate              |

### Upgrading to Prometheus Format

To expose Prometheus-compatible metrics, add `prometheus-fastapi-instrumentator`:

```python
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)
```

This requires no changes to the existing route logic.
