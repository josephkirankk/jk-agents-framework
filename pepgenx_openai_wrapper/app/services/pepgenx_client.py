"""
PepGenX API client.

This module provides a robust HTTP client for interacting with the PepGenX API,
including error handling, retries, and proper logging.
"""

import asyncio
import time
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException, status

from ..core.auth import get_pepgenx_headers
from ..core.config import settings
from ..core.logging import get_logger, log_pepgenx_request, log_pepgenx_response
from ..models.pepgenx_models import PepGenXErrorResponse, PepGenXRequest, PepGenXResponse

logger = get_logger("pepgenx_client")


class PepGenXClient:
    """HTTP client for PepGenX API with retry logic and error handling."""
    
    def __init__(self):
        self.base_url = settings.pepgenx_api_url
        self.timeout = settings.http_timeout_seconds
        self.max_retries = settings.http_max_retries
        
        # Create HTTP client with proper configuration
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=100),
            headers={"User-Agent": "PepGenX-OpenAI-Wrapper/1.0.0"}
        )
        
        logger.info("PepGenX client initialized", base_url=self.base_url)
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
        logger.debug("PepGenX client closed")
    
    async def generate_completion(
        self,
        request: PepGenXRequest,
        stream: bool = False
    ) -> PepGenXResponse:
        """
        Generate completion using PepGenX API.
        
        Args:
            request: PepGenX request payload
            stream: Whether to stream the response (if supported)
            
        Returns:
            PepGenXResponse: The API response
            
        Raises:
            HTTPException: If the API call fails
        """
        start_time = time.time()
        
        try:
            # Get authentication headers
            headers = get_pepgenx_headers()
            
            # Prepare request payload
            payload = request.dict(exclude_none=True)
            
            # Log the request (sanitized)
            log_pepgenx_request(logger, self.base_url, headers, payload)
            
            # Make the API call with retries
            response_data = await self._make_request_with_retries(
                method="POST",
                url=self.base_url,
                headers=headers,
                json=payload
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Log the response
            log_pepgenx_response(logger, 200, response_data, duration_ms)
            
            # Parse response
            return self._parse_response(response_data, request.generation_model)
            
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                "PepGenX API call failed",
                error=str(e),
                duration_ms=duration_ms,
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"PepGenX API error: {str(e)}"
            )
    
    async def _make_request_with_retries(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        json: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.
        
        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            json: Request JSON payload
            
        Returns:
            Dict[str, Any]: Response JSON data
            
        Raises:
            HTTPException: If all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(
                    "Making PepGenX API request",
                    attempt=attempt + 1,
                    max_retries=self.max_retries + 1
                )
                
                response = await self._client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json
                )
                
                # Handle different response status codes
                if response.status_code == 200:
                    try:
                        return response.json()
                    except Exception as e:
                        logger.error("Failed to parse JSON response", error=str(e))
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Invalid JSON response from PepGenX API"
                        )
                
                elif response.status_code == 401:
                    logger.error("PepGenX API authentication failed")
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="PepGenX API authentication failed"
                    )
                
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    if attempt < self.max_retries:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(
                            "PepGenX API rate limited, retrying",
                            wait_time=wait_time,
                            attempt=attempt + 1
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail="PepGenX API rate limit exceeded"
                        )
                
                elif 500 <= response.status_code < 600:
                    # Server error - retry
                    if attempt < self.max_retries:
                        wait_time = 2 ** attempt
                        logger.warning(
                            "PepGenX API server error, retrying",
                            status_code=response.status_code,
                            wait_time=wait_time,
                            attempt=attempt + 1
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail=f"PepGenX API server error: {response.status_code}"
                        )
                
                else:
                    # Other client errors
                    try:
                        error_data = response.json()
                        error_message = error_data.get("error", f"HTTP {response.status_code}")
                    except:
                        error_message = f"HTTP {response.status_code}: {response.text}"
                    
                    logger.error(
                        "PepGenX API client error",
                        status_code=response.status_code,
                        error=error_message
                    )
                    
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"PepGenX API error: {error_message}"
                    )
            
            except HTTPException:
                # Re-raise HTTP exceptions
                raise
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.warning(
                        "PepGenX API request failed, retrying",
                        error=str(e),
                        wait_time=wait_time,
                        attempt=attempt + 1
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    break
        
        # All retries failed
        logger.error("All PepGenX API retries failed", error=str(last_exception))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"PepGenX API unavailable: {str(last_exception)}"
        )
    
    def _parse_response(self, response_data: Dict[str, Any], model: str) -> PepGenXResponse:
        """
        Parse PepGenX API response into structured format.
        
        Args:
            response_data: Raw response data from API
            model: Model name used for the request
            
        Returns:
            PepGenXResponse: Parsed response
        """
        try:
            # Store raw response for debugging
            parsed_response = PepGenXResponse(
                raw_response=response_data,
                model=model
            )
            
            # Try to extract standard fields
            # Note: This will need to be updated based on actual PepGenX response format
            
            if "id" in response_data:
                parsed_response.id = response_data["id"]
            
            if "choices" in response_data:
                parsed_response.choices = response_data["choices"]
            elif "text" in response_data:
                # Single text response
                parsed_response.choices = [{
                    "text": response_data["text"],
                    "index": 0,
                    "finish_reason": response_data.get("finish_reason", "stop")
                }]
            elif "content" in response_data:
                # Alternative content field
                parsed_response.choices = [{
                    "text": response_data["content"],
                    "index": 0,
                    "finish_reason": response_data.get("finish_reason", "stop")
                }]
            
            if "usage" in response_data:
                parsed_response.usage = response_data["usage"]
            
            if "created" in response_data:
                parsed_response.created = response_data["created"]
            elif "timestamp" in response_data:
                parsed_response.created = response_data["timestamp"]
            else:
                parsed_response.created = int(time.time())
            
            # Handle error responses
            if "error" in response_data:
                parsed_response.error = response_data["error"]
                parsed_response.error_code = response_data.get("error_code")
            
            logger.debug("PepGenX response parsed successfully")
            return parsed_response
            
        except Exception as e:
            logger.error("Failed to parse PepGenX response", error=str(e), exc_info=True)
            # Return raw response as fallback
            return PepGenXResponse(
                raw_response=response_data,
                model=model,
                error=f"Failed to parse response: {str(e)}"
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check against PepGenX API.
        
        Returns:
            Dict[str, Any]: Health check results
        """
        try:
            # Simple health check request
            test_request = PepGenXRequest(
                generation_model="gpt-4",
                custom_prompt="Hello"
                # system_prompt will use the default from config
            )
            
            start_time = time.time()
            response = await self.generate_completion(test_request)
            duration_ms = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": duration_ms,
                "api_accessible": True,
                "error": None
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "response_time_ms": None,
                "api_accessible": False,
                "error": str(e)
            }
