"""
Service layer for the PepGenX OpenAI Wrapper.

This module contains business logic for interacting with the PepGenX API
and translating between OpenAI and PepGenX formats.
"""

from .pepgenx_client import PepGenXClient
from .translator import RequestTranslator, ResponseTranslator

__all__ = ["PepGenXClient", "RequestTranslator", "ResponseTranslator"]
