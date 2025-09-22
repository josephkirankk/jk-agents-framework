"""
TsSearch Client

This module provides a client for interacting with the TsSearch (Typesense) API.
This is completely separate from the existing VectorDB client.
"""

import os
import logging
from typing import Optional, Dict, Any, Union
import httpx
from urllib.parse import urljoin

from .ts_models import (
    TsSearchRequest,
    TsSearchResponse,
    TsSearchErrorResponse,
    TsSearchResult,
    SearchType,
    TsSearchFilters
)
from .ts_exceptions import (
    TsSearchException,
    TsSearchConnectionError,
    TsSearchValidationError,
    TsSearchServerError,
    TsSearchTimeoutError,
    TsSearchNotFoundError
)

logger = logging.getLogger(__name__)


class TsSearchClient:
    """
    Client for interacting with the TsSearch (Typesense) API service.
    
    This client provides methods for searching defects using hybrid, keyword, and vector search,
    with proper error handling, validation, and connection management.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the TsSearch client.
        
        Args:
            base_url: Base URL for the TsSearch API. If None, uses HYBRID_SEARCH_BASE_URL env var.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts.
            headers: Additional headers to include in requests.
        """
        self.base_url = base_url or os.getenv("HYBRID_SEARCH_BASE_URL", "http://localhost:3000")
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Ensure base_url ends with /
        if not self.base_url.endswith('/'):
            self.base_url += '/'
            
        # Default headers
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "TsSearch-Python-Client/1.0.0"
        }
        
        # Add custom headers if provided
        if headers:
            self.headers.update(headers)
            
        self._client: Optional[httpx.AsyncClient] = None
        
        logger.info(f"TsSearchClient initialized with base_url: {self.base_url}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_client(self):
        """Ensure HTTP client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers=self.headers,
                follow_redirects=True
            )

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        """
        Make an HTTP request with retry logic and error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: JSON data for POST requests
            params: Query parameters for GET requests
            
        Returns:
            HTTP response object
            
        Raises:
            TsSearchException: For various error conditions
        """
        await self._ensure_client()
        
        url = urljoin(self.base_url, endpoint)
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")
                
                response = await self._client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params
                )
                
                # Check for HTTP errors
                if response.status_code >= 400:
                    await self._handle_error_response(response)
                
                logger.debug(f"Request successful: {response.status_code}")
                return response
                
            except httpx.TimeoutException as e:
                if attempt == self.max_retries:
                    raise TsSearchTimeoutError(f"Request timed out after {self.timeout}s") from e
                logger.warning(f"Request timeout on attempt {attempt + 1}, retrying...")
                
            except httpx.ConnectError as e:
                if attempt == self.max_retries:
                    raise TsSearchConnectionError(f"Failed to connect to TsSearch server: {str(e)}") from e
                logger.warning(f"Connection error on attempt {attempt + 1}, retrying...")
                
            except Exception as e:
                if attempt == self.max_retries:
                    raise TsSearchException(f"Unexpected error: {str(e)}") from e
                logger.warning(f"Unexpected error on attempt {attempt + 1}, retrying...")

    async def _handle_error_response(self, response: httpx.Response):
        """Handle error responses from the API."""
        try:
            error_data = response.json()
            if isinstance(error_data, dict) and "error" in error_data:
                error_info = error_data["error"]
                message = error_info.get("message", "Unknown error")
                details = error_info.get("details", "")
                full_message = f"{message}. {details}".strip(". ")
            else:
                full_message = str(error_data)
        except Exception:
            full_message = response.text or f"HTTP {response.status_code}"
        
        if response.status_code == 400:
            raise TsSearchValidationError(full_message, response.status_code, response)
        elif response.status_code == 404:
            raise TsSearchNotFoundError(full_message, response.status_code, response)
        elif response.status_code >= 500:
            raise TsSearchServerError(full_message, response.status_code, response)
        else:
            raise TsSearchException(full_message, response.status_code, response)

    async def search_post(self, request: TsSearchRequest) -> TsSearchResponse:
        """
        Perform a search using POST method with full request body.
        
        Args:
            request: TsSearchRequest object with search parameters
            
        Returns:
            TsSearchResponse object with search results
            
        Raises:
            TsSearchException: For various error conditions
        """
        try:
            # Convert request to dict, handling filters properly
            request_data = request.model_dump(exclude_none=True)
            
            # Convert filters to dict if present
            if request.filters:
                request_data["filters"] = request.filters.model_dump(exclude_none=True)
            
            logger.info(f"Performing POST search: query='{request.query}', type={request.search_type}, limit={request.limit}")
            
            response = await self._make_request("POST", "api/v1/search", data=request_data)
            
            # Parse response
            response_data = response.json()
            search_response = TsSearchResponse.model_validate(response_data)
            
            logger.info(f"Search completed: found {search_response.data.total_found} results in {search_response.data.processing_time_ms}ms")
            
            return search_response
            
        except TsSearchException:
            raise
        except Exception as e:
            raise TsSearchException(f"Failed to perform POST search: {str(e)}") from e

    async def search_get(
        self,
        query: str,
        search_type: SearchType = SearchType.HYBRID,
        limit: int = 10,
        collection: str = "defects",
        machine: Optional[str] = None,
        subsystem: Optional[str] = None,
        component: Optional[str] = None,
        defect_type: Optional[str] = None,
        include_highlights: bool = False,
        min_text_match_score: Optional[float] = None,
        min_similarity_score: Optional[float] = None
    ) -> TsSearchResponse:
        """
        Perform a search using GET method with query parameters.
        
        Args:
            query: Search query string
            search_type: Type of search (hybrid, keyword, vector)
            limit: Number of results to return
            collection: Collection to search in
            machine: Machine type filter
            subsystem: Subsystem filter
            component: Component filter
            defect_type: Defect type filter
            include_highlights: Whether to include highlights
            min_text_match_score: Minimum text match score
            min_similarity_score: Minimum similarity score
            
        Returns:
            TsSearchResponse object with search results
            
        Raises:
            TsSearchException: For various error conditions
        """
        try:
            # Build query parameters
            params = {
                "q": query,
                "type": search_type.value,
                "limit": limit,
                "collection": collection,
                "include_highlights": include_highlights
            }
            
            # Add optional filters
            if machine:
                params["machine"] = machine
            if subsystem:
                params["subsystem"] = subsystem
            if component:
                params["component"] = component
            if defect_type:
                params["defect_type"] = defect_type
            if min_text_match_score is not None:
                params["min_text_match_score"] = min_text_match_score
            if min_similarity_score is not None:
                params["min_similarity_score"] = min_similarity_score
            
            logger.info(f"Performing GET search: query='{query}', type={search_type.value}, limit={limit}")
            
            response = await self._make_request("GET", "api/v1/search", params=params)
            
            # Parse response
            response_data = response.json()
            search_response = TsSearchResponse.model_validate(response_data)
            
            logger.info(f"Search completed: found {search_response.data.total_found} results in {search_response.data.processing_time_ms}ms")
            
            return search_response
            
        except TsSearchException:
            raise
        except Exception as e:
            raise TsSearchException(f"Failed to perform GET search: {str(e)}") from e

    async def search(self, request: TsSearchRequest) -> TsSearchResponse:
        """
        Convenience method that uses POST search by default.
        
        Args:
            request: TsSearchRequest object with search parameters
            
        Returns:
            TsSearchResponse object with search results
        """
        return await self.search_post(request)

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a basic health check by making a simple search request.
        
        Returns:
            Dictionary with health status information
            
        Raises:
            TsSearchException: If health check fails
        """
        try:
            # Make a simple search request
            response = await self.search_get("test", limit=1)
            
            return {
                "status": "healthy",
                "server_url": self.base_url,
                "response_time_ms": response.data.processing_time_ms,
                "timestamp": response.timestamp
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "server_url": self.base_url,
                "error": str(e),
                "timestamp": None
            }
