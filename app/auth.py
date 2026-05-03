"""
auth.py - Authentication and Authorization (Factor 15).

Implements two levels of access:
  - User endpoints: protected by x-api-key header
  - Admin endpoints: protected by x-admin-key header

Keys are loaded from environment variables only — never hardcoded.
In production this can be replaced with JWT, AWS Cognito, or IAM.
"""

import logging
from fastapi import Header, HTTPException, status, Depends
from app.config import get_settings, Settings

logger = logging.getLogger(__name__)


def require_api_key(
    x_api_key: str = Header(..., description="User API key for authentication"),
    settings: Settings = Depends(get_settings),
) -> str:
    """
    Dependency for user-level endpoints.
    Raises 401 if the key is missing or incorrect.
    """
    if x_api_key != settings.api_key:
        logger.warning("Unauthorized access attempt with invalid API key.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Provide a valid x-api-key header.",
        )
    return x_api_key


def require_admin_key(
    x_admin_key: str = Header(..., description="Admin API key for elevated access"),
    settings: Settings = Depends(get_settings),
) -> str:
    """
    Dependency for admin-level endpoints.
    Raises 403 if the key is missing or incorrect.
    """
    if x_admin_key != settings.admin_api_key:
        logger.warning("Unauthorized admin access attempt.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing admin key. Provide a valid x-admin-key header.",
        )
    return x_admin_key
