"""
VectorDB API Client

This module provides the main client class for interacting with the VectorDB API service.
It handles HTTP requests, response validation, and error handling.
"""

import os
import logging
from typing import Optional, Dict, Any
from urllib.parse import urljoin

import httpx
from pydantic import ValidationError

from .models import (
    SearchRequest,
    SearchResponse,
    UpsertRequest,
    UpsertResponse,
    HealthResponse,
    ErrorResponse
)
from .exceptions import VectorDBError, VectorDBConnectionError, VectorDBValidationError


logger = logging.getLogger(__name__)


class VectorDBClient:
    """
    Client for interacting with the VectorDB API service.
    
    This client provides methods for searching and upserting defects in the vector database,
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
        Initialize the VectorDB client.
        
        Args:
            base_url: Base URL for the VectorDB API. If None, uses VECTORDB_BASE_URL env var.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts.
            headers: Additional headers to include in requests.
        """
        self.base_url = base_url or os.getenv("VECTORDB_BASE_URL", "http://localhost:8010")
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Ensure base_url ends with /
        if not self.base_url.endswith('/'):
            self.base_url += '/'
            
        # Default headers
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "VectorDB-Python-Client/1.0.0"
        }
        
        if headers:
            self.headers.update(headers)
            
        # Create HTTP client
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers=self.headers,
            follow_redirects=True
        )
        
        logger.info(f"VectorDB client initialized with base_url: {self.base_url}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        """
        Make an HTTP request with error handling and retries.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            
        Returns:
            HTTP response object
            
        Raises:
            VectorDBConnectionError: If connection fails
            VectorDBError: If API returns an error
        """
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        
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
                    error_detail = "Unknown error"
                    try:
                        error_data = response.json()
                        if isinstance(error_data, dict) and "detail" in error_data:
                            error_detail = error_data["detail"]
                        else:
                            error_detail = str(error_data)
                    except Exception:
                        error_detail = response.text or f"HTTP {response.status_code}"
                    
                    raise VectorDBError(
                        f"API request failed: {error_detail}",
                        status_code=response.status_code,
                        response=response
                    )
                
                logger.debug(f"Request successful: {response.status_code}")
                return response
                
            except httpx.ConnectError as e:
                if attempt == self.max_retries:
                    raise VectorDBConnectionError(
                        f"Failed to connect to VectorDB API at {url}: {str(e)}"
                    ) from e
                logger.warning(f"Connection attempt {attempt + 1} failed, retrying...")
                
            except httpx.TimeoutException as e:
                if attempt == self.max_retries:
                    raise VectorDBConnectionError(
                        f"Request to {url} timed out after {self.timeout}s"
                    ) from e
                logger.warning(f"Request attempt {attempt + 1} timed out, retrying...")
                
            except VectorDBError:
                # Don't retry API errors
                raise
                
            except Exception as e:
                if attempt == self.max_retries:
                    raise VectorDBError(f"Unexpected error: {str(e)}") from e
                logger.warning(f"Request attempt {attempt + 1} failed: {str(e)}, retrying...")
    
    async def health_check(self) -> HealthResponse:
        """
        Check the health status of the VectorDB API.

        Returns:
            HealthResponse object with status information

        Raises:
            VectorDBError: If the health check fails
        """
        try:
            response = await self._make_request("GET", "/health")
            data = response.json()
            return HealthResponse.model_validate(data)

        except ValidationError as e:
            raise VectorDBValidationError(f"Invalid health response format: {str(e)}") from e

    async def search(self, request: SearchRequest) -> SearchResponse:
        """
        Search for defects using natural language query.

        Args:
            request: SearchRequest object with query parameters

        Returns:
            SearchResponse object with search results

        Raises:
            VectorDBError: If the search fails
            VectorDBValidationError: If request/response validation fails
        """
        try:
            # Validate request
            if not isinstance(request, SearchRequest):
                request = SearchRequest.model_validate(request)

            # Make API request
            response = await self._make_request(
                "POST",
                "/search",
                data=request.model_dump()
            )

            # Parse and validate response
            data = response.json()
            return SearchResponse.model_validate(data)

        except ValidationError as e:
            raise VectorDBValidationError(f"Invalid search request/response: {str(e)}") from e

    async def search_get(
        self,
        query: str,
        top_n: int = 5,
        min_score: float = 0.7
    ) -> SearchResponse:
        """
        Search for defects using GET method (convenience method).

        Args:
            query: Search query in natural language
            top_n: Number of results to return (1-50)
            min_score: Minimum similarity score (0.0-1.0)

        Returns:
            SearchResponse object with search results

        Raises:
            VectorDBError: If the search fails
        """
        try:
            # Make API request with query parameters
            response = await self._make_request(
                "GET",
                "/search",
                params={
                    "query": query,
                    "top_n": top_n,
                    "min_score": min_score
                }
            )

            # Parse and validate response
            data = response.json()
            return SearchResponse.model_validate(data)

        except ValidationError as e:
            raise VectorDBValidationError(f"Invalid search response: {str(e)}") from e

    async def upsert(self, request: UpsertRequest) -> UpsertResponse:
        """
        Create or update a defect in the vector database.

        Args:
            request: UpsertRequest object with defect data

        Returns:
            UpsertResponse object with operation result

        Raises:
            VectorDBError: If the upsert fails
            VectorDBValidationError: If request/response validation fails
        """
        try:
            # Validate request
            if not isinstance(request, UpsertRequest):
                request = UpsertRequest.model_validate(request)

            # Make API request
            response = await self._make_request(
                "POST",
                "/upsert",
                data=request.model_dump()
            )

            # Parse and validate response
            data = response.json()
            return UpsertResponse.model_validate(data)

        except ValidationError as e:
            raise VectorDBValidationError(f"Invalid upsert request/response: {str(e)}") from e

    async def upsert_json_defects(self, json_string: str) -> Dict[str, Any]:
        """
        Parse JSON string containing defects and upsert them to the database.

        This method takes a JSON string with defects array and upserts each defect
        to the VectorDB. It handles the mapping from the JSON structure to the
        UpsertRequest format.

        Args:
            json_string: JSON string containing defects array

        Returns:
            Dictionary with summary of upsert operations

        Raises:
            VectorDBError: If JSON parsing or upsert operations fail
            VectorDBValidationError: If JSON structure is invalid
        """
        import json

        try:
            # Parse JSON string
            data = json.loads(json_string)

            if "defects" not in data:
                raise VectorDBValidationError("JSON must contain 'defects' array")

            defects = data["defects"]
            if not isinstance(defects, list):
                raise VectorDBValidationError("'defects' must be an array")

            results = {
                "total_defects": len(defects),
                "successful_upserts": 0,
                "failed_upserts": 0,
                "results": [],
                "errors": []
            }

            logger.info(f"Starting batch upsert of {len(defects)} defects")

            # Process each defect
            for i, defect_data in enumerate(defects):
                try:
                    # Map JSON structure to UpsertRequest format
                    upsert_request = UpsertRequest(
                        defect_code=defect_data.get("defect_code", ""),
                        defect_text=defect_data.get("defect_text", ""),
                        subsystem=defect_data.get("subsystem", ""),
                        severity=defect_data.get("severity", "Medium"),
                        typical_frequency=defect_data.get("typical_frequency", "Unknown"),
                        symptoms=defect_data.get("symptoms", []),
                        detection_methods=defect_data.get("detection_methods", []),
                        early_warning_signals=defect_data.get("early_warning_signals", []),
                        tags=defect_data.get("tags", []),
                        likely_root_causes=defect_data.get("likely_root_causes", []),
                        recommended_actions=defect_data.get("recommended_actions", [])
                    )

                    # Perform upsert
                    response = await self.upsert(upsert_request)

                    results["successful_upserts"] += 1
                    results["results"].append({
                        "defect_code": response.defect_code,
                        "operation": response.operation,
                        "success": response.success,
                        "message": response.message
                    })

                    logger.debug(f"Successfully upserted defect {i+1}/{len(defects)}: {response.defect_code}")

                except Exception as e:
                    results["failed_upserts"] += 1
                    error_msg = f"Failed to upsert defect {i+1}: {str(e)}"
                    results["errors"].append({
                        "defect_index": i,
                        "defect_code": defect_data.get("defect_code", "unknown"),
                        "error": error_msg
                    })
                    logger.error(error_msg)

            logger.info(
                f"Batch upsert completed: {results['successful_upserts']} successful, "
                f"{results['failed_upserts']} failed"
            )

            return results

        except json.JSONDecodeError as e:
            raise VectorDBValidationError(f"Invalid JSON format: {str(e)}") from e
        except Exception as e:
            raise VectorDBError(f"Failed to process JSON defects: {str(e)}") from e
