"""
LLM API Request/Response Interceptor

This module provides HTTP interceptors for capturing all LLM API interactions
across different providers (OpenAI, Azure AI, Google Gemini, etc.) using
monkey patching and custom HTTP clients.
"""

from __future__ import annotations
import json
import logging
import time
from typing import Dict, Any, Optional, Union, Callable
from urllib.parse import urlparse
import httpx
import aiohttp
from openai import OpenAI, AsyncOpenAI
from openai._base_client import BaseClient
from openai._types import NOT_GIVEN

from .internal_logger import get_internal_logger, LLMProvider

log = logging.getLogger("llm_interceptor")


class LLMInterceptorMixin:
    """Mixin class to add LLM logging capabilities to HTTP clients."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.internal_logger = get_internal_logger()
        self._agent_context: Optional[Dict[str, Any]] = None
    
    def set_agent_context(self, agent_name: str, user_input: str, correlation_id: Optional[str] = None):
        """Set the current agent context for logging."""
        self._agent_context = {
            "agent_name": agent_name,
            "user_input": user_input,
            "correlation_id": correlation_id
        }
    
    def _detect_llm_provider(self, url: str) -> LLMProvider:
        """Detect LLM provider from URL."""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        if "openai.azure.com" in domain or "cognitiveservices.azure.com" in domain:
            return LLMProvider.AZURE_OPENAI
        elif "api.openai.com" in domain:
            return LLMProvider.OPENAI
        elif "generativelanguage.googleapis.com" in domain:
            return LLMProvider.GOOGLE_GEMINI
        elif "api.anthropic.com" in domain:
            return LLMProvider.ANTHROPIC
        else:
            return LLMProvider.UNKNOWN
    
    def _extract_model_from_request(self, url: str, payload: Dict[str, Any]) -> str:
        """Extract model name from request."""
        # Try to get model from payload first
        if isinstance(payload, dict) and "model" in payload:
            return payload["model"]
        
        # Try to extract from URL path
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split("/")
        
        # Common patterns for model extraction
        for i, part in enumerate(path_parts):
            if part in ["deployments", "models"] and i + 1 < len(path_parts):
                return path_parts[i + 1]
        
        return "unknown"
    
    def _extract_token_usage(self, response_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract token usage information from response."""
        if not isinstance(response_data, dict):
            return None
        
        # OpenAI/Azure OpenAI format
        if "usage" in response_data:
            usage = response_data["usage"]
            return {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            }
        
        # Google Gemini format
        if "usageMetadata" in response_data:
            usage = response_data["usageMetadata"]
            return {
                "prompt_tokens": usage.get("promptTokenCount", 0),
                "completion_tokens": usage.get("candidatesTokenCount", 0),
                "total_tokens": usage.get("totalTokenCount", 0)
            }
        
        return None


class InterceptedHttpxClient(LLMInterceptorMixin, httpx.Client):
    """HTTPX client with LLM request/response interception."""
    
    def request(self, method: str, url: Union[str, httpx.URL], **kwargs) -> httpx.Response:
        """Intercept and log HTTP requests."""
        url_str = str(url)
        provider = self._detect_llm_provider(url_str)
        
        # Only log LLM provider requests
        if provider == LLMProvider.UNKNOWN:
            return super().request(method, url, **kwargs)
        
        # Extract request data
        headers = dict(kwargs.get("headers", {}))
        content = kwargs.get("content")
        json_data = kwargs.get("json")
        
        # Parse request payload
        payload = {}
        if json_data:
            payload = json_data if isinstance(json_data, dict) else {}
        elif content:
            try:
                if isinstance(content, (str, bytes)):
                    payload = json.loads(content) if content else {}
            except (json.JSONDecodeError, TypeError):
                payload = {"raw_content": str(content)[:1000]}  # Truncate large content
        
        model = self._extract_model_from_request(url_str, payload)
        
        # Get agent context
        agent_name = None
        user_input = None
        correlation_id = None
        if self._agent_context:
            agent_name = self._agent_context.get("agent_name")
            user_input = self._agent_context.get("user_input")
            correlation_id = self._agent_context.get("correlation_id")
        
        # Log the interaction
        with self.internal_logger.log_llm_interaction(
            provider=provider,
            model=model,
            agent_name=agent_name,
            user_input=user_input,
            correlation_id=correlation_id
        ) as ctx:
            # Log request
            ctx.log_request(
                endpoint=url_str,
                method=method,
                headers=headers,
                payload=payload
            )
            
            # Make the actual request
            start_time = time.time()
            try:
                response = super().request(method, url, **kwargs)
                
                # Parse response
                response_headers = dict(response.headers)
                response_payload = {}
                
                try:
                    if response.content:
                        response_payload = response.json()
                except (json.JSONDecodeError, ValueError):
                    response_payload = {"raw_content": response.text[:1000]}
                
                # Extract token usage
                token_usage = self._extract_token_usage(response_payload)
                
                # Log response
                ctx.log_response(
                    status_code=response.status_code,
                    headers=response_headers,
                    payload=response_payload,
                    token_usage=token_usage,
                    error_message=None if response.is_success else f"HTTP {response.status_code}: {response.reason_phrase}"
                )
                
                return response
                
            except Exception as e:
                # Log error response
                ctx.log_response(
                    status_code=500,
                    headers={},
                    payload={"error": str(e)},
                    error_message=str(e)
                )
                raise


class InterceptedAsyncHttpxClient(LLMInterceptorMixin, httpx.AsyncClient):
    """Async HTTPX client with LLM request/response interception."""
    
    async def request(self, method: str, url: Union[str, httpx.URL], **kwargs) -> httpx.Response:
        """Intercept and log async HTTP requests."""
        url_str = str(url)
        provider = self._detect_llm_provider(url_str)
        
        # Only log LLM provider requests
        if provider == LLMProvider.UNKNOWN:
            return await super().request(method, url, **kwargs)
        
        # Extract request data
        headers = dict(kwargs.get("headers", {}))
        content = kwargs.get("content")
        json_data = kwargs.get("json")
        
        # Parse request payload
        payload = {}
        if json_data:
            payload = json_data if isinstance(json_data, dict) else {}
        elif content:
            try:
                if isinstance(content, (str, bytes)):
                    payload = json.loads(content) if content else {}
            except (json.JSONDecodeError, TypeError):
                payload = {"raw_content": str(content)[:1000]}
        
        model = self._extract_model_from_request(url_str, payload)
        
        # Get agent context
        agent_name = None
        user_input = None
        correlation_id = None
        if self._agent_context:
            agent_name = self._agent_context.get("agent_name")
            user_input = self._agent_context.get("user_input")
            correlation_id = self._agent_context.get("correlation_id")
        
        # Log the interaction
        with self.internal_logger.log_llm_interaction(
            provider=provider,
            model=model,
            agent_name=agent_name,
            user_input=user_input,
            correlation_id=correlation_id
        ) as ctx:
            # Log request
            ctx.log_request(
                endpoint=url_str,
                method=method,
                headers=headers,
                payload=payload
            )
            
            # Make the actual request
            try:
                response = await super().request(method, url, **kwargs)
                
                # Parse response
                response_headers = dict(response.headers)
                response_payload = {}
                
                try:
                    if response.content:
                        response_payload = response.json()
                except (json.JSONDecodeError, ValueError):
                    response_payload = {"raw_content": response.text[:1000]}
                
                # Extract token usage
                token_usage = self._extract_token_usage(response_payload)
                
                # Log response
                ctx.log_response(
                    status_code=response.status_code,
                    headers=response_headers,
                    payload=response_payload,
                    token_usage=token_usage,
                    error_message=None if response.is_success else f"HTTP {response.status_code}: {response.reason_phrase}"
                )
                
                return response
                
            except Exception as e:
                # Log error response
                ctx.log_response(
                    status_code=500,
                    headers={},
                    payload={"error": str(e)},
                    error_message=str(e)
                )
                raise


class InterceptedAioHttpSession(LLMInterceptorMixin):
    """Wrapper for aiohttp.ClientSession with LLM interception."""
    
    def __init__(self, session: aiohttp.ClientSession):
        super().__init__()
        self._session = session
    
    async def request(self, method: str, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Intercept and log aiohttp requests."""
        provider = self._detect_llm_provider(url)
        
        # Only log LLM provider requests
        if provider == LLMProvider.UNKNOWN:
            return await self._session.request(method, url, **kwargs)
        
        # Extract request data
        headers = dict(kwargs.get("headers", {}))
        json_data = kwargs.get("json")
        data = kwargs.get("data")
        
        # Parse request payload
        payload = {}
        if json_data:
            payload = json_data if isinstance(json_data, dict) else {}
        elif data:
            try:
                if isinstance(data, (str, bytes)):
                    payload = json.loads(data) if data else {}
            except (json.JSONDecodeError, TypeError):
                payload = {"raw_content": str(data)[:1000]}
        
        model = self._extract_model_from_request(url, payload)
        
        # Get agent context
        agent_name = None
        user_input = None
        correlation_id = None
        if self._agent_context:
            agent_name = self._agent_context.get("agent_name")
            user_input = self._agent_context.get("user_input")
            correlation_id = self._agent_context.get("correlation_id")
        
        # Log the interaction
        with self.internal_logger.log_llm_interaction(
            provider=provider,
            model=model,
            agent_name=agent_name,
            user_input=user_input,
            correlation_id=correlation_id
        ) as ctx:
            # Log request
            ctx.log_request(
                endpoint=url,
                method=method,
                headers=headers,
                payload=payload
            )
            
            # Make the actual request
            try:
                response = await self._session.request(method, url, **kwargs)
                
                # Parse response
                response_headers = dict(response.headers)
                response_payload = {}
                
                try:
                    response_text = await response.text()
                    if response_text:
                        response_payload = json.loads(response_text)
                except (json.JSONDecodeError, ValueError):
                    response_payload = {"raw_content": response_text[:1000] if 'response_text' in locals() else ""}
                
                # Extract token usage
                token_usage = self._extract_token_usage(response_payload)
                
                # Log response
                ctx.log_response(
                    status_code=response.status,
                    headers=response_headers,
                    payload=response_payload,
                    token_usage=token_usage,
                    error_message=None if response.ok else f"HTTP {response.status}: {response.reason}"
                )
                
                return response
                
            except Exception as e:
                # Log error response
                ctx.log_response(
                    status_code=500,
                    headers={},
                    payload={"error": str(e)},
                    error_message=str(e)
                )
                raise
    
    def __getattr__(self, name):
        """Delegate other methods to the wrapped session."""
        return getattr(self._session, name)


# Global intercepted clients
_intercepted_httpx_client: Optional[InterceptedHttpxClient] = None
_intercepted_async_httpx_client: Optional[InterceptedAsyncHttpxClient] = None


def get_intercepted_httpx_client() -> InterceptedHttpxClient:
    """Get the global intercepted HTTPX client."""
    global _intercepted_httpx_client
    if _intercepted_httpx_client is None:
        _intercepted_httpx_client = InterceptedHttpxClient()
    return _intercepted_httpx_client


def get_intercepted_async_httpx_client() -> InterceptedAsyncHttpxClient:
    """Get the global intercepted async HTTPX client."""
    global _intercepted_async_httpx_client
    if _intercepted_async_httpx_client is None:
        _intercepted_async_httpx_client = InterceptedAsyncHttpxClient()
    return _intercepted_async_httpx_client


def set_agent_context_for_clients(agent_name: str, user_input: str, correlation_id: Optional[str] = None):
    """Set agent context for all intercepted clients."""
    if _intercepted_httpx_client:
        _intercepted_httpx_client.set_agent_context(agent_name, user_input, correlation_id)
    if _intercepted_async_httpx_client:
        _intercepted_async_httpx_client.set_agent_context(agent_name, user_input, correlation_id)


def wrap_aiohttp_session(session: aiohttp.ClientSession) -> InterceptedAioHttpSession:
    """Wrap an aiohttp session with LLM interception."""
    return InterceptedAioHttpSession(session)
