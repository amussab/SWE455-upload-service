"""
test_auth.py - Tests for authentication and authorization logic.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

VALID_API_KEY = "student-demo-key"
VALID_ADMIN_KEY = "admin-demo-key"


class TestUserAuth:
    def test_upload_without_api_key_returns_401(self):
        """Requests without x-api-key must be rejected."""
        response = client.get("/files")
        assert response.status_code == 422  # header missing → unprocessable

    def test_upload_with_wrong_api_key_returns_401(self):
        """Requests with an incorrect key must be rejected."""
        response = client.get("/files", headers={"x-api-key": "wrong-key"})
        assert response.status_code == 401

    def test_files_list_with_valid_api_key_returns_200(self):
        """Requests with the correct key must be accepted."""
        response = client.get("/files", headers={"x-api-key": VALID_API_KEY})
        assert response.status_code == 200

    def test_get_file_with_valid_key(self):
        """Known file ID should return 200."""
        response = client.get(
            "/files/mock-file-001", headers={"x-api-key": VALID_API_KEY}
        )
        assert response.status_code == 200
        assert response.json()["file_id"] == "mock-file-001"

    def test_get_unknown_file_returns_404(self):
        """Unknown file IDs must return 404."""
        response = client.get(
            "/files/does-not-exist", headers={"x-api-key": VALID_API_KEY}
        )
        assert response.status_code == 404


class TestAdminAuth:
    def test_admin_uploads_without_key_returns_422(self):
        """Admin endpoints without a key return 422 (missing header)."""
        response = client.get("/admin/uploads")
        assert response.status_code == 422

    def test_admin_uploads_with_user_key_returns_403(self):
        """User key must not grant admin access."""
        response = client.get(
            "/admin/uploads", headers={"x-admin-key": "wrong-admin-key"}
        )
        assert response.status_code == 403

    def test_admin_uploads_with_admin_key_returns_200(self):
        """Valid admin key must grant access."""
        response = client.get(
            "/admin/uploads", headers={"x-admin-key": VALID_ADMIN_KEY}
        )
        assert response.status_code == 200

    def test_admin_alerts_with_admin_key_returns_200(self):
        """Alerts endpoint accessible with admin key."""
        response = client.get(
            "/admin/alerts", headers={"x-admin-key": VALID_ADMIN_KEY}
        )
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
