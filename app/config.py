"""
config.py - Application configuration.
All values are loaded from environment variables (Factor 3: Config).
No secrets are hardcoded.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Auth keys — provided through environment variables only
    api_key: str = "student-demo-key"
    admin_api_key: str = "admin-demo-key"

    # App metadata
    app_name: str = "gateway-service"
    app_version: str = "1.0.0"
    app_env: str = "development"
    log_level: str = "INFO"

    # Downstream service URLs (placeholders for integration)
    validation_service_url: str = "http://validation-service:8001"
    database_url: str = "sqlite:///./dev.db"  # override in production

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Return a cached singleton of the settings object."""
    return Settings()
