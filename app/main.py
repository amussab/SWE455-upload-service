"""
main.py - Gateway Service entry point.

Responsibilities:
  - Creates the FastAPI application
  - Configures structured stdout logging (Factor 11)
  - Registers all routers
  - Exposes OpenAPI / Swagger UI at /docs

Factor 11 (Logs): All logs are written to stdout as structured text.
The cloud runtime (ECS, CloudWatch, or any log aggregator) collects
and routes them without any in-process log shipping.
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import files, admin, health

# ── Logging setup (Factor 11: Logs as event streams) ────────────────────────
def configure_logging(log_level: str) -> None:
    """
    Configure root logger to write structured lines to stdout.
    No log files, no log rotation — the runtime handles persistence.
    """
    logging.basicConfig(
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


# ── Application lifespan ─────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    logger = logging.getLogger(__name__)
    logger.info(
        "Gateway Service starting",
        extra={"env": settings.app_env, "version": settings.app_version},
    )
    yield
    logger.info("Gateway Service shutting down.")


# ── FastAPI app ──────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Secure File Validation — Gateway Service",
        description=(
            "API gateway for the Secure File Validation Service.\n\n"
            "**User endpoints** require an `x-api-key` header.\n"
            "**Admin endpoints** require an `x-admin-key` header.\n\n"
            "See `/docs` for the interactive Swagger UI."
        ),
        version=settings.app_version,
        contact={"name": "Member 3 — API, Auth & Docs Lead"},
        lifespan=lifespan,
    )

    # CORS — restrict origins in production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # tighten this in production
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health.router)
    app.include_router(files.router)
    app.include_router(admin.router)

    return app


app = create_app()
