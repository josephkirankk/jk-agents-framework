"""
Health check endpoints.

This module provides health check and monitoring endpoints for the wrapper service.
"""

import time
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.auth import check_auth_health, validate_api_key
from ..core.config import settings
from ..core.logging import get_logger
from ..services.pepgenx_client import PepGenXClient

logger = get_logger("api.health")

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns:
        Dict[str, Any]: Health status information
    """
    return {
        "status": "healthy",
        "timestamp": int(time.time()),
        "version": "1.0.0",
        "service": "pepgenx-openai-wrapper"
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint that verifies all dependencies.
    
    Returns:
        Dict[str, Any]: Detailed readiness status
        
    Raises:
        HTTPException: If service is not ready
    """
    logger.info("Performing readiness check")
    
    health_status = {
        "status": "ready",
        "timestamp": int(time.time()),
        "checks": {}
    }
    
    # Check authentication system
    try:
        auth_health = check_auth_health()
        health_status["checks"]["auth"] = auth_health
        
        # Determine if auth is healthy
        auth_healthy = (
            auth_health.get("okta_token_file") == "valid" and
            "count:" in auth_health.get("api_keys_configured", "")
        )
        
        if not auth_healthy:
            health_status["status"] = "not_ready"
            
    except Exception as e:
        logger.error("Auth health check failed", error=str(e))
        health_status["checks"]["auth"] = {"error": str(e)}
        health_status["status"] = "not_ready"
    
    # Check PepGenX API connectivity
    try:
        async with PepGenXClient() as client:
            pepgenx_health = await client.health_check()
            health_status["checks"]["pepgenx_api"] = pepgenx_health
            
            if pepgenx_health.get("status") != "healthy":
                health_status["status"] = "not_ready"
                
    except Exception as e:
        logger.error("PepGenX health check failed", error=str(e))
        health_status["checks"]["pepgenx_api"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "not_ready"
    
    # Check configuration
    try:
        config_health = {
            "pepgenx_api_url": bool(settings.pepgenx_api_url),
            "pepgenx_project_id": bool(settings.pepgenx_project_id),
            "pepgenx_team_id": bool(settings.pepgenx_team_id),
            "pepgenx_api_key": bool(settings.pepgenx_api_key),
            "okta_token_file": settings.okta_token_file_path.exists(),
            "api_keys_count": len(settings.api_keys_list)
        }
        health_status["checks"]["config"] = config_health
        
        # Check if all required config is present
        required_config = [
            config_health["pepgenx_api_url"],
            config_health["pepgenx_project_id"],
            config_health["pepgenx_team_id"],
            config_health["pepgenx_api_key"],
            config_health["okta_token_file"],
            config_health["api_keys_count"] > 0
        ]
        
        if not all(required_config):
            health_status["status"] = "not_ready"
            
    except Exception as e:
        logger.error("Config health check failed", error=str(e))
        health_status["checks"]["config"] = {"error": str(e)}
        health_status["status"] = "not_ready"
    
    # Return appropriate status code
    if health_status["status"] == "not_ready":
        logger.warning("Service not ready", checks=health_status["checks"])
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status
        )
    
    logger.info("Service ready", checks=health_status["checks"])
    return health_status


@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check endpoint for Kubernetes/Docker health checks.
    
    Returns:
        Dict[str, Any]: Liveness status
    """
    return {
        "status": "alive",
        "timestamp": int(time.time())
    }


@router.get("/detailed")
async def detailed_health_check(
    api_key: str = Depends(validate_api_key)
) -> Dict[str, Any]:
    """
    Detailed health check with authentication required.
    
    Args:
        api_key: Validated API key
        
    Returns:
        Dict[str, Any]: Comprehensive health information
    """
    logger.info("Performing detailed health check")
    
    health_info = {
        "status": "healthy",
        "timestamp": int(time.time()),
        "version": "1.0.0",
        "service": "pepgenx-openai-wrapper",
        "details": {}
    }
    
    # System information
    health_info["details"]["system"] = {
        "log_level": settings.log_level,
        "log_format": settings.log_format,
        "host": settings.openai_wrapper_host,
        "port": settings.openai_wrapper_port,
        "metrics_enabled": settings.enable_metrics,
        "rate_limit_rpm": settings.rate_limit_requests_per_minute
    }
    
    # Authentication details
    health_info["details"]["auth"] = check_auth_health()
    
    # PepGenX API details
    try:
        async with PepGenXClient() as client:
            pepgenx_health = await client.health_check()
            health_info["details"]["pepgenx_api"] = pepgenx_health
    except Exception as e:
        health_info["details"]["pepgenx_api"] = {
            "status": "error",
            "error": str(e)
        }
        health_info["status"] = "degraded"
    
    # Configuration details (sanitized)
    health_info["details"]["config"] = {
        "pepgenx_api_url": settings.pepgenx_api_url,
        "pepgenx_project_id": settings.pepgenx_project_id[:8] + "..." if settings.pepgenx_project_id else None,
        "pepgenx_team_id": settings.pepgenx_team_id[:8] + "..." if settings.pepgenx_team_id else None,
        "okta_token_file": str(settings.okta_token_file_path),
        "api_keys_configured": len(settings.api_keys_list),
        "cors_origins": settings.cors_origins_list,
        "http_timeout": settings.http_timeout_seconds,
        "http_max_retries": settings.http_max_retries,
        "cache_ttl": settings.cache_ttl_seconds
    }
    
    return health_info


@router.get("/metrics")
async def metrics_endpoint() -> Dict[str, Any]:
    """
    Basic metrics endpoint (Prometheus-style metrics would go here).
    
    Returns:
        Dict[str, Any]: Basic metrics information
    """
    # In a production system, this would return Prometheus metrics
    # For now, return basic information
    return {
        "timestamp": int(time.time()),
        "uptime_seconds": int(time.time()),  # Would track actual uptime
        "requests_total": 0,  # Would track request count
        "requests_errors": 0,  # Would track error count
        "response_time_avg": 0.0,  # Would track average response time
        "pepgenx_api_calls": 0,  # Would track PepGenX API calls
        "active_connections": 0  # Would track active connections
    }
