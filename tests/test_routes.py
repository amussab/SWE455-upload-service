"""
test_routes.py - Tests for endpoint behavior and response shapes.
"""

import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

API_KEY = "student-demo-key"
ADMIN_KEY = "admin-demo-key"


class TestHealthRoutes:
    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "healthy"
        assert "service" in body
        assert "version" in body

    def test_ready_returns_200(self):
        response = client.get("/ready")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ready"
        assert "dependencies" in body

    def test_metrics_returns_200(self):
        response = client.get("/metrics")
        assert response.status_code == 200
        body = response.json()
        assert "total_uploads" in body
        assert "uptime_seconds" in body
        assert body["uptime_seconds"] >= 0


class TestFileRoutes:
    def test_upload_mock_file_returns_202(self):
        """Upload endpoint should accept a file and return PENDING status."""
        fake_file = io.BytesIO(b"fake file content for testing")
        response = client.post(
            "/files/upload",
            headers={"x-api-key": API_KEY},
            files={"file": ("test.txt", fake_file, "text/plain")},
        )
        assert response.status_code == 202
        body = response.json()
        assert body["status"] == "pending"
        assert "file_id" in body
        assert body["filename"] == "test.txt"
        assert body["size_bytes"] > 0

    def test_upload_with_user_id_query_param(self):
        """Upload endpoint should accept optional user_id query param."""
        fake_file = io.BytesIO(b"another test file")
        response = client.post(
            "/files/upload?user_id=user-123",
            headers={"x-api-key": API_KEY},
            files={"file": ("doc.pdf", fake_file, "application/pdf")},
        )
        assert response.status_code == 202

    def test_list_files_response_shape(self):
        """List endpoint should return total count and files array."""
        response = client.get("/files", headers={"x-api-key": API_KEY})
        assert response.status_code == 200
        body = response.json()
        assert "total" in body
        assert "files" in body
        assert isinstance(body["files"], list)


class TestAdminRoutes:
    def test_admin_uploads_response_shape(self):
        """Admin uploads should return files list with correct structure."""
        response = client.get("/admin/uploads", headers={"x-admin-key": ADMIN_KEY})
        assert response.status_code == 200
        body = response.json()
        assert "total" in body
        assert "files" in body

    def test_admin_alerts_response_shape(self):
        """Admin alerts should return alerts list."""
        response = client.get("/admin/alerts", headers={"x-admin-key": ADMIN_KEY})
        assert response.status_code == 200
        body = response.json()
        assert "total" in body
        assert "alerts" in body
        if body["total"] > 0:
            alert = body["alerts"][0]
            assert "alert_id" in alert
            assert "reason" in alert
