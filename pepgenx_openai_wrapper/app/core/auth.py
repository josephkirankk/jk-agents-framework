"""
Authentication and authorization for the PepGenX OpenAI Wrapper.

This module handles:
- OpenAI API key validation for incoming requests
- OKTA token management for PepGenX API calls
- Token caching and refresh logic
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings
from .logging import get_logger

logger = get_logger("auth")

# Security scheme for Bearer token authentication
security = HTTPBearer()


class TokenCache:
    """Simple in-memory cache for OKTA tokens with expiration."""
    
    def __init__(self):
        self._token: Optional[str] = None
        self._expires_at: Optional[datetime] = None
        self._last_refresh: Optional[datetime] = None
    
    def get_token(self) -> Optional[str]:
        """Get cached token if still valid."""
        if not self._token or not self._expires_at:
            return None
        
        # Check if token is expired or close to expiring
        threshold = timedelta(minutes=settings.okta_token_refresh_threshold_minutes)
        if datetime.now() >= (self._expires_at - threshold):
            logger.info("Token expired or close to expiring, needs refresh")
            return None
        
        return self._token
    
    def set_token(self, token: str, expires_in_seconds: Optional[int] = None) -> None:
        """Cache token with expiration."""
        self._token = token
        self._last_refresh = datetime.now()
        
        if expires_in_seconds:
            self._expires_at = datetime.now() + timedelta(seconds=expires_in_seconds)
        else:
            # Default to 1 hour if no expiration provided
            self._expires_at = datetime.now() + timedelta(hours=1)
        
        logger.info("Token cached", expires_at=self._expires_at.isoformat())
    
    def clear(self) -> None:
        """Clear cached token."""
        self._token = None
        self._expires_at = None
        self._last_refresh = None
        logger.info("Token cache cleared")


# Global token cache instance
token_cache = TokenCache()


def load_okta_token() -> str:
    """
    Load OKTA access token from file with caching.
    
    Returns:
        str: The access token
        
    Raises:
        HTTPException: If token cannot be loaded or is invalid
    """
    # Try to get cached token first
    cached_token = token_cache.get_token()
    if cached_token:
        logger.debug("Using cached OKTA token")
        return cached_token
    
    # Load token from file
    token_file_path = settings.okta_token_file_path
    
    try:
        logger.info("Loading OKTA token from file", path=str(token_file_path))
        
        if not token_file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"OKTA token file not found: {token_file_path}"
            )
        
        with open(token_file_path, 'r', encoding='utf-8') as f:
            token_data = json.load(f)
        
        if 'access_token' not in token_data:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="'access_token' not found in OKTA token file"
            )
        
        access_token = token_data['access_token']
        
        # Extract expiration if available
        expires_in = token_data.get('expires_in')
        if expires_in:
            try:
                expires_in = int(expires_in)
            except (ValueError, TypeError):
                expires_in = None
        
        # Cache the token
        token_cache.set_token(access_token, expires_in)
        
        logger.info("OKTA token loaded successfully")
        return access_token
        
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in OKTA token file", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Invalid JSON in OKTA token file: {e}"
        )
    except Exception as e:
        logger.error("Failed to load OKTA token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to load OKTA token: {e}"
        )


def validate_api_key(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Validate OpenAI-style API key from Authorization header.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        str: The validated API key
        
    Raises:
        HTTPException: If API key is invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    api_key = credentials.credentials
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validate API key format
    if not api_key.startswith("sk-"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if API key is in the allowed list
    valid_keys = settings.api_keys_list
    if api_key not in valid_keys:
        logger.warning("Invalid API key attempted", key_prefix=api_key[:10] + "...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.debug("API key validated", key_prefix=api_key[:10] + "...")
    return api_key


def get_pepgenx_headers() -> Dict[str, str]:
    """
    Get headers required for PepGenX API calls.
    
    Returns:
        Dict[str, str]: Headers dictionary with authentication and configuration
        
    Raises:
        HTTPException: If OKTA token cannot be loaded
    """
    access_token = load_okta_token()
    
    headers = {
        "Content-Type": "application/json",
        "project_id": settings.pepgenx_project_id,
        "team_id": settings.pepgenx_team_id,
        "x-pepgenx-apikey": settings.pepgenx_api_key,
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "PepGenX-OpenAI-Wrapper/1.0.0"
    }
    
    # Add the cookie header from the original script if needed
    # Note: This should be made configurable or removed in production
    # headers["cookie"] = "..."  # TODO: Make this configurable
    
    return headers


def refresh_okta_token() -> None:
    """
    Force refresh of OKTA token by clearing cache.
    This will cause the next request to reload the token from file.
    """
    logger.info("Forcing OKTA token refresh")
    token_cache.clear()


# Health check for authentication system
def check_auth_health() -> Dict[str, str]:
    """
    Check the health of the authentication system.
    
    Returns:
        Dict[str, str]: Health status information
    """
    health_status = {
        "okta_token_file": "unknown",
        "api_keys_configured": "unknown",
        "token_cache": "unknown"
    }
    
    try:
        # Check OKTA token file
        token_file_path = settings.okta_token_file_path
        if token_file_path.exists():
            health_status["okta_token_file"] = "exists"
            
            # Try to load token
            with open(token_file_path, 'r', encoding='utf-8') as f:
                token_data = json.load(f)
            
            if 'access_token' in token_data:
                health_status["okta_token_file"] = "valid"
            else:
                health_status["okta_token_file"] = "invalid_format"
        else:
            health_status["okta_token_file"] = "missing"
    
    except Exception as e:
        health_status["okta_token_file"] = f"error: {str(e)}"
    
    # Check API keys configuration
    try:
        api_keys = settings.api_keys_list
        if api_keys:
            health_status["api_keys_configured"] = f"count: {len(api_keys)}"
        else:
            health_status["api_keys_configured"] = "none"
    except Exception as e:
        health_status["api_keys_configured"] = f"error: {str(e)}"
    
    # Check token cache
    cached_token = token_cache.get_token()
    if cached_token:
        health_status["token_cache"] = "active"
    else:
        health_status["token_cache"] = "empty"
    
    return health_status
