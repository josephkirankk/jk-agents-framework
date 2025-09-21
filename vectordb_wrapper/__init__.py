"""
VectorDB Wrapper Module

This module provides a wrapper for the VectorDB API service, offering
search and upsert functionality with proper error handling and validation.
"""

from .client import VectorDBClient
from .models import (
    SearchRequest,
    SearchResponse,
    UpsertRequest,
    UpsertResponse,
    DefectData,
    SearchResult,
    HealthResponse
)
from .decorators import vectordb_wrapper
from .utils import upsert_json_defects, upsert_json_defects_sync

__all__ = [
    'VectorDBClient',
    'SearchRequest',
    'SearchResponse',
    'UpsertRequest',
    'UpsertResponse',
    'DefectData',
    'SearchResult',
    'HealthResponse',
    'vectordb_wrapper',
    'upsert_json_defects',
    'upsert_json_defects_sync'
]

__version__ = "1.0.0"
