"""
Logging configuration for the PepGenX OpenAI Wrapper.

This module sets up structured logging with correlation IDs, proper formatting,
and integration with monitoring systems.
"""

import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any, Dict, Optional

import structlog
from structlog.types import EventDict, Processor

from .config import settings

# Context variable for request correlation ID
correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def add_correlation_id(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add correlation ID to log events."""
    cid = correlation_id.get()
    if cid:
        event_dict["correlation_id"] = cid
    return event_dict


def add_timestamp(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add timestamp to log events."""
    import time
    event_dict["timestamp"] = time.time()
    return event_dict


def setup_logging() -> None:
    """Configure structured logging for the application."""
    
    # Configure structlog processors
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        add_correlation_id,
        add_timestamp,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
    ]
    
    if settings.log_format == "json":
        processors.extend([
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ])
    else:
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True)
        ])
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
    )
    
    # Silence noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def set_correlation_id(cid: Optional[str] = None) -> str:
    """Set correlation ID for the current context."""
    if cid is None:
        cid = str(uuid.uuid4())
    correlation_id.set(cid)
    return cid


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID."""
    return correlation_id.get()


class LoggingMiddleware:
    """Middleware to add correlation IDs and log requests/responses."""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger("middleware.logging")
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Generate correlation ID
        cid = set_correlation_id()
        
        # Log request
        request_info = {
            "method": scope["method"],
            "path": scope["path"],
            "query_string": scope.get("query_string", b"").decode("utf-8", errors="ignore"),
            "client": str(scope.get("client", "unknown")),
            "headers": {
                k.decode("utf-8", errors="ignore"): v.decode("utf-8", errors="ignore")
                for k, v in scope.get("headers", [])
            },
        }
        
        self.logger.info("Request started", **request_info)
        
        # Wrap send to log response
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                self.logger.info(
                    "Response sent",
                    status_code=message["status"],
                    headers={
                        k.decode("utf-8", errors="ignore"): v.decode("utf-8", errors="ignore")
                        for k, v in message.get("headers", [])
                    },
                )
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            self.logger.error("Request failed", error=str(e), exc_info=True)
            raise
        finally:
            self.logger.info("Request completed")


# Request/Response logging utilities
def log_pepgenx_request(
    logger: structlog.BoundLogger,
    url: str,
    headers: Dict[str, Any],
    payload: Dict[str, Any]
) -> None:
    """Log PepGenX API request (sanitized)."""
    sanitized_headers = {k: v for k, v in headers.items() if k.lower() not in ["authorization", "x-pepgenx-apikey"]}
    sanitized_headers["authorization"] = "Bearer ***"
    sanitized_headers["x-pepgenx-apikey"] = "***"
    
    logger.info(
        "PepGenX API request",
        url=url,
        headers=sanitized_headers,
        payload=payload
    )


def log_pepgenx_response(
    logger: structlog.BoundLogger,
    status_code: int,
    response_data: Dict[str, Any],
    duration_ms: float
) -> None:
    """Log PepGenX API response."""
    logger.info(
        "PepGenX API response",
        status_code=status_code,
        response_size=len(str(response_data)),
        duration_ms=duration_ms
    )


def log_openai_request(
    logger: structlog.BoundLogger,
    model: str,
    messages_count: int,
    stream: bool = False
) -> None:
    """Log OpenAI-compatible request."""
    logger.info(
        "OpenAI request received",
        model=model,
        messages_count=messages_count,
        stream=stream
    )


def log_openai_response(
    logger: structlog.BoundLogger,
    model: str,
    choices_count: int,
    usage: Optional[Dict[str, Any]] = None,
    duration_ms: float = 0
) -> None:
    """Log OpenAI-compatible response."""
    logger.info(
        "OpenAI response sent",
        model=model,
        choices_count=choices_count,
        usage=usage,
        duration_ms=duration_ms
    )
