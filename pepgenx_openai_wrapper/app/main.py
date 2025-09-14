"""
Main FastAPI application for the PepGenX OpenAI Wrapper.

This module sets up the FastAPI application with all middleware, routers,
and configuration needed for production deployment.
"""

import time
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from .api import chat_router, health_router
from .core.config import settings
from .core.logging import LoggingMiddleware, get_logger, setup_logging

# Setup logging first
setup_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting PepGenX OpenAI Wrapper", version="1.0.0")
    logger.info("Configuration loaded", 
                pepgenx_api_url=settings.pepgenx_api_url,
                log_level=settings.log_level,
                port=settings.openai_wrapper_port)
    
    yield
    
    # Shutdown
    logger.info("Shutting down PepGenX OpenAI Wrapper")


# Create FastAPI application
app = FastAPI(
    title="PepGenX OpenAI Wrapper",
    description="OpenAI-compatible API wrapper for PepGenX AI platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods_list,
    allow_headers=["*"] if settings.cors_headers == "*" else settings.cors_headers.split(","),
    expose_headers=["X-Request-ID", "X-RateLimit-Remaining", "X-RateLimit-Reset"]
)

# Add trusted host middleware for security
if settings.openai_wrapper_host != "0.0.0.0":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[settings.openai_wrapper_host, "localhost", "127.0.0.1"]
    )

# Add custom logging middleware
app.add_middleware(LoggingMiddleware)


# Custom middleware for request/response headers
@app.middleware("http")
async def add_custom_headers(request: Request, call_next):
    """Add custom headers to all responses."""
    start_time = time.time()
    
    # Add request ID header if not present
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        import uuid
        request_id = str(uuid.uuid4())
    
    response = await call_next(request)
    
    # Add response headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Powered-By"] = "PepGenX-OpenAI-Wrapper/1.0.0"
    response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
    
    # Add rate limiting headers (placeholder - implement actual rate limiting)
    response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests_per_minute)
    response.headers["X-RateLimit-Remaining"] = str(settings.rate_limit_requests_per_minute - 1)
    response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
    
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unhandled errors.
    
    Args:
        request: FastAPI request object
        exc: Unhandled exception
        
    Returns:
        JSONResponse: Error response
    """
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Internal server error",
                "type": "api_error",
                "code": "500"
            }
        }
    )


# Include routers
app.include_router(health_router)
app.include_router(chat_router)


# Root endpoint
@app.get("/")
async def root() -> Dict[str, Any]:
    """
    Root endpoint with service information.
    
    Returns:
        Dict[str, Any]: Service information
    """
    return {
        "service": "PepGenX OpenAI Wrapper",
        "version": "1.0.0",
        "description": "OpenAI-compatible API wrapper for PepGenX AI platform",
        "docs": "/docs",
        "health": "/health",
        "openai_base_url": f"http://{settings.openai_wrapper_host}:{settings.openai_wrapper_port}/v1",
        "endpoints": {
            "chat_completions": "/v1/chat/completions",
            "models": "/v1/models",
            "health": "/health",
            "ready": "/health/ready",
            "metrics": "/health/metrics"
        },
        "timestamp": int(time.time())
    }


# OpenAI-compatible base URL info
@app.get("/v1")
async def openai_base() -> Dict[str, Any]:
    """
    OpenAI v1 API base endpoint.
    
    Returns:
        Dict[str, Any]: API information
    """
    return {
        "message": "PepGenX OpenAI-compatible API v1",
        "version": "1.0.0",
        "endpoints": [
            "/v1/chat/completions",
            "/v1/models"
        ],
        "documentation": f"http://{settings.openai_wrapper_host}:{settings.openai_wrapper_port}/docs"
    }


# Metrics endpoint for Prometheus (if enabled)
if settings.enable_metrics:
    @app.get("/metrics")
    async def prometheus_metrics() -> Response:
        """
        Prometheus metrics endpoint.
        
        Returns:
            Response: Prometheus-formatted metrics
        """
        # In a production system, this would return actual Prometheus metrics
        # For now, return basic metrics in Prometheus format
        metrics_data = f"""# HELP pepgenx_wrapper_requests_total Total number of requests
# TYPE pepgenx_wrapper_requests_total counter
pepgenx_wrapper_requests_total 0

# HELP pepgenx_wrapper_request_duration_seconds Request duration in seconds
# TYPE pepgenx_wrapper_request_duration_seconds histogram
pepgenx_wrapper_request_duration_seconds_bucket{{le="0.1"}} 0
pepgenx_wrapper_request_duration_seconds_bucket{{le="0.5"}} 0
pepgenx_wrapper_request_duration_seconds_bucket{{le="1.0"}} 0
pepgenx_wrapper_request_duration_seconds_bucket{{le="2.0"}} 0
pepgenx_wrapper_request_duration_seconds_bucket{{le="5.0"}} 0
pepgenx_wrapper_request_duration_seconds_bucket{{le="+Inf"}} 0
pepgenx_wrapper_request_duration_seconds_sum 0
pepgenx_wrapper_request_duration_seconds_count 0

# HELP pepgenx_wrapper_pepgenx_api_calls_total Total number of PepGenX API calls
# TYPE pepgenx_wrapper_pepgenx_api_calls_total counter
pepgenx_wrapper_pepgenx_api_calls_total 0

# HELP pepgenx_wrapper_errors_total Total number of errors
# TYPE pepgenx_wrapper_errors_total counter
pepgenx_wrapper_errors_total 0
"""
        
        return Response(
            content=metrics_data,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )


# Development server runner
if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting development server")
    uvicorn.run(
        "app.main:app",
        host=settings.openai_wrapper_host,
        port=settings.openai_wrapper_port,
        reload=True,
        log_level=settings.log_level.lower(),
        access_log=True
    )
