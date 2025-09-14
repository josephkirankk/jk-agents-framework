"""
OpenAI-compatible chat completions API endpoints.

This module implements the /v1/chat/completions endpoint that matches
the OpenAI API specification while using PepGenX as the backend.
"""

import time
import uuid
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, StreamingResponse

from ..core.auth import validate_api_key
from ..core.logging import get_logger, log_openai_request, log_openai_response, set_correlation_id
from ..models.openai_models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ErrorDetail,
    ErrorResponse,
)
from ..services.pepgenx_client import PepGenXClient
from ..services.translator import RequestTranslator, ResponseTranslator

logger = get_logger("api.chat")

router = APIRouter(prefix="/v1", tags=["chat"])


@router.post("/chat/completions")
async def create_chat_completion(
    request: ChatCompletionRequest,
    http_request: Request,
    api_key: str = Depends(validate_api_key)
) -> ChatCompletionResponse:
    """
    Create a chat completion using the OpenAI-compatible API.
    
    This endpoint accepts OpenAI-format requests and translates them to PepGenX API calls,
    then translates the responses back to OpenAI format.
    
    Args:
        request: OpenAI chat completion request
        http_request: FastAPI request object for metadata
        api_key: Validated API key
        
    Returns:
        ChatCompletionResponse: OpenAI-compatible response
        
    Raises:
        HTTPException: For various error conditions
    """
    # Set correlation ID for request tracking
    correlation_id = set_correlation_id()
    start_time = time.time()
    
    logger.info(
        "Chat completion request received",
        correlation_id=correlation_id,
        model=request.model,
        messages_count=len(request.messages),
        stream=request.stream,
        client_ip=http_request.client.host if http_request.client else None
    )
    
    # Log OpenAI request details
    log_openai_request(
        logger,
        model=request.model,
        messages_count=len(request.messages),
        stream=request.stream or False
    )
    
    try:
        # Check if streaming is requested
        if request.stream:
            # TODO: Implement streaming support
            logger.warning("Streaming requested but not yet implemented")
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Streaming is not yet supported"
            )
        
        # Validate request parameters
        _validate_request(request)
        
        # Translate OpenAI request to PepGenX format
        try:
            pepgenx_request = RequestTranslator.translate_chat_completion(request)
            logger.debug("Request translated to PepGenX format")
        except Exception as e:
            logger.error("Failed to translate request", error=str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Request translation failed: {str(e)}"
            )
        
        # Make PepGenX API call
        try:
            async with PepGenXClient() as client:
                pepgenx_response = await client.generate_completion(
                    pepgenx_request,
                    stream=request.stream or False
                )
                logger.debug("PepGenX API call completed")
        except HTTPException:
            # Re-raise HTTP exceptions from PepGenX client
            raise
        except Exception as e:
            logger.error("PepGenX API call failed", error=str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Backend API error: {str(e)}"
            )
        
        # Translate PepGenX response to OpenAI format
        try:
            openai_response = ResponseTranslator.translate_chat_completion(
                pepgenx_response,
                request,
                request_id=correlation_id
            )
            logger.debug("Response translated to OpenAI format")
        except Exception as e:
            logger.error("Failed to translate response", error=str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Response translation failed: {str(e)}"
            )
        
        # Calculate duration and log response
        duration_ms = (time.time() - start_time) * 1000
        
        log_openai_response(
            logger,
            model=openai_response.model,
            choices_count=len(openai_response.choices),
            usage=openai_response.usage.dict() if openai_response.usage else None,
            duration_ms=duration_ms
        )
        
        logger.info(
            "Chat completion request completed",
            correlation_id=correlation_id,
            duration_ms=duration_ms,
            status="success"
        )
        
        return openai_response
        
    except HTTPException:
        # Re-raise HTTP exceptions with proper logging
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            "Chat completion request failed",
            correlation_id=correlation_id,
            duration_ms=duration_ms,
            status="error"
        )
        raise
        
    except Exception as e:
        # Handle unexpected errors
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            "Unexpected error in chat completion",
            correlation_id=correlation_id,
            duration_ms=duration_ms,
            error=str(e),
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


def _validate_request(request: ChatCompletionRequest) -> None:
    """
    Validate chat completion request parameters.
    
    Args:
        request: Chat completion request to validate
        
    Raises:
        HTTPException: If validation fails
    """
    # Check message count
    if len(request.messages) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one message is required"
        )
    
    if len(request.messages) > 100:  # Reasonable limit
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many messages (maximum 100)"
        )
    
    # Check message content length
    total_content_length = 0
    for message in request.messages:
        if message.content:
            total_content_length += len(message.content)
    
    if total_content_length > 100000:  # 100KB limit
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Total message content too long (maximum 100KB)"
        )
    
    # Validate model name
    if not request.model or len(request.model.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model name is required"
        )
    
    # Validate n parameter
    if request.n and request.n > 1:
        logger.warning("Multiple choices requested but may not be supported by PepGenX")
    
    # Validate temperature
    if request.temperature is not None and (request.temperature < 0 or request.temperature > 2):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Temperature must be between 0 and 2"
        )
    
    # Validate max_tokens
    if request.max_tokens is not None and request.max_tokens <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="max_tokens must be positive"
        )


# Exception handlers are registered at the app level in main.py


# Additional endpoints for OpenAI compatibility

@router.get("/models")
async def list_models(api_key: str = Depends(validate_api_key)) -> Dict[str, Any]:
    """
    List available models (OpenAI-compatible endpoint).
    
    Args:
        api_key: Validated API key
        
    Returns:
        Dict[str, Any]: List of available models
    """
    # Return a list of supported models
    models = [
        {
            "id": "gpt-4",
            "object": "model",
            "created": 1677610602,
            "owned_by": "pepgenx-wrapper"
        },
        {
            "id": "gpt-4-turbo",
            "object": "model",
            "created": 1677610602,
            "owned_by": "pepgenx-wrapper"
        },
        {
            "id": "gpt-4o",
            "object": "model",
            "created": 1677610602,
            "owned_by": "pepgenx-wrapper"
        },
        {
            "id": "gpt-4o-mini",
            "object": "model",
            "created": 1677610602,
            "owned_by": "pepgenx-wrapper"
        },
        {
            "id": "gpt-3.5-turbo",
            "object": "model",
            "created": 1677610602,
            "owned_by": "pepgenx-wrapper"
        },
        {
            "id": "gpt-5",
            "object": "model",
            "created": 1677610602,
            "owned_by": "pepgenx-wrapper"
        },
        {
            "id": "claude-3-sonnet",
            "object": "model",
            "created": 1677610602,
            "owned_by": "pepgenx-wrapper"
        },
        {
            "id": "claude-3-haiku",
            "object": "model",
            "created": 1677610602,
            "owned_by": "pepgenx-wrapper"
        },
        {
            "id": "claude-3-opus",
            "object": "model",
            "created": 1677610602,
            "owned_by": "pepgenx-wrapper"
        }
    ]
    
    return {
        "object": "list",
        "data": models
    }
