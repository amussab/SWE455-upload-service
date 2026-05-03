# ── Stage 1: dependency installation ────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /install

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install/deps --no-cache-dir -r requirements.txt


# ── Stage 2: runtime image ───────────────────────────────────────────────────
FROM python:3.11-slim

LABEL maintainer="Member 3 — API, Auth & Docs Lead"
LABEL description="Gateway Service for Secure File Validation"

# Non-root user for security
RUN adduser --disabled-password --gecos "" appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install/deps /usr/local

# Copy application source
COPY app/ ./app/

# Environment defaults (override at runtime via ECS task definition or docker run -e)
ENV APP_ENV=production \
    LOG_LEVEL=INFO \
    PORT=8000

# Run as non-root
USER appuser

# Expose the service port (Factor 7: Port Binding)
EXPOSE 8000

# Graceful startup with uvicorn (Factor 9: Disposability)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
