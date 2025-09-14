"""
API endpoints for the PepGenX OpenAI Wrapper.

This module contains all the FastAPI route handlers and endpoint definitions.
"""

from .chat import router as chat_router
from .health import router as health_router

__all__ = ["chat_router", "health_router"]
