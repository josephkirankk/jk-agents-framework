"""
VectorDB Wrapper Module

This module provides wrappers for both VectorDB API service and TsSearch
(Typesense) API service, offering search and upsert functionality with
proper error handling and validation.
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

# TsSearch (Typesense) components
from .ts_client import TsSearchClient
from .ts_models import (
    TsSearchRequest,
    TsSearchResponse,
    TsSearchFilters,
    TsDefectResult,
    SearchType
)
from .ts_exceptions import (
    TsSearchException,
    TsSearchConnectionError,
    TsSearchValidationError,
    TsSearchServerError,
    TsSearchTimeoutError,
    TsSearchNotFoundError
)

__all__ = [
    # VectorDB components
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
    'upsert_json_defects_sync',

    # TsSearch components
    'TsSearchClient',
    'TsSearchRequest',
    'TsSearchResponse',
    'TsSearchFilters',
    'TsDefectResult',
    'SearchType',
    'TsSearchException',
    'TsSearchConnectionError',
    'TsSearchValidationError',
    'TsSearchServerError',
    'TsSearchTimeoutError',
    'TsSearchNotFoundError'
]

__version__ = "1.0.0"
