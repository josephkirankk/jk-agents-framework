"""
Translation services between OpenAI and PepGenX API formats.

This module handles the conversion of requests and responses between
the OpenAI-compatible format and the PepGenX API format.
"""

import time
import uuid
from typing import Any, Dict, List, Optional

from ..core.logging import get_logger
from ..models.openai_models import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    MessageRole,
    Usage,
    get_pepgenx_model,
)
from ..models.pepgenx_models import (
    PepGenXRequest,
    PepGenXResponse,
    format_messages_for_pepgenx,
)

logger = get_logger("translator")


class RequestTranslator:
    """Translates OpenAI requests to PepGenX format."""
    
    @staticmethod
    def translate_chat_completion(request: ChatCompletionRequest) -> PepGenXRequest:
        """
        Translate OpenAI chat completion request to PepGenX format.
        
        Args:
            request: OpenAI chat completion request
            
        Returns:
            PepGenXRequest: Translated request for PepGenX API
        """
        logger.debug("Translating OpenAI request to PepGenX format")
        
        # Convert messages to PepGenX format
        messages_dict = [msg.dict() for msg in request.messages]
        custom_prompt, system_prompt = format_messages_for_pepgenx(messages_dict)
        
        # Map model name
        pepgenx_model = get_pepgenx_model(request.model)
        
        # Create PepGenX request
        pepgenx_request = PepGenXRequest(
            generation_model=pepgenx_model,
            custom_prompt=custom_prompt,
            system_prompt=system_prompt
        )
        
        # Map optional parameters if supported by PepGenX
        if request.temperature is not None:
            pepgenx_request.temperature = request.temperature
        
        if request.max_tokens is not None:
            pepgenx_request.max_tokens = request.max_tokens
        
        if request.top_p is not None:
            pepgenx_request.top_p = request.top_p
        
        if request.frequency_penalty is not None:
            pepgenx_request.frequency_penalty = request.frequency_penalty
        
        if request.presence_penalty is not None:
            pepgenx_request.presence_penalty = request.presence_penalty
        
        if request.stop is not None:
            pepgenx_request.stop = request.stop
        
        logger.debug(
            "Request translation completed",
            original_model=request.model,
            pepgenx_model=pepgenx_model,
            messages_count=len(request.messages),
            custom_prompt_length=len(custom_prompt)
        )
        
        return pepgenx_request


class ResponseTranslator:
    """Translates PepGenX responses to OpenAI format."""
    
    @staticmethod
    def translate_chat_completion(
        pepgenx_response: PepGenXResponse,
        original_request: ChatCompletionRequest,
        request_id: Optional[str] = None
    ) -> ChatCompletionResponse:
        """
        Translate PepGenX response to OpenAI chat completion format.
        
        Args:
            pepgenx_response: Response from PepGenX API
            original_request: Original OpenAI request for context
            request_id: Optional request ID for tracking
            
        Returns:
            ChatCompletionResponse: OpenAI-compatible response
        """
        logger.debug("Translating PepGenX response to OpenAI format")
        
        # Generate response ID if not provided
        if not request_id:
            request_id = f"chatcmpl-{uuid.uuid4().hex[:29]}"
        
        # Handle error responses
        if pepgenx_response.error:
            logger.error("PepGenX response contains error", error=pepgenx_response.error)
            # For now, we'll create a response with an error message
            # In production, this might need to raise an HTTPException instead
            choices = [
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(
                        role=MessageRole.ASSISTANT,
                        content=f"Error: {pepgenx_response.error}"
                    ),
                    finish_reason="error"
                )
            ]
        else:
            # Translate choices
            choices = ResponseTranslator._translate_choices(pepgenx_response)
        
        # Translate usage information
        usage = ResponseTranslator._translate_usage(pepgenx_response)
        
        # Create OpenAI response
        openai_response = ChatCompletionResponse(
            id=request_id,
            model=original_request.model,  # Use original model name
            choices=choices,
            usage=usage,
            created=pepgenx_response.created or int(time.time()),
            system_fingerprint=f"pepgenx-wrapper-{int(time.time())}"
        )
        
        logger.debug(
            "Response translation completed",
            response_id=request_id,
            choices_count=len(choices),
            has_usage=usage is not None
        )
        
        return openai_response
    
    @staticmethod
    def _translate_choices(pepgenx_response: PepGenXResponse) -> List[ChatCompletionChoice]:
        """
        Translate PepGenX choices to OpenAI format.
        
        Args:
            pepgenx_response: PepGenX response
            
        Returns:
            List[ChatCompletionChoice]: OpenAI-compatible choices
        """
        choices = []
        
        if pepgenx_response.choices:
            for i, choice in enumerate(pepgenx_response.choices):
                # Handle different choice formats
                if isinstance(choice, dict):
                    text = choice.get("text", "")
                    finish_reason = choice.get("finish_reason", "stop")
                elif hasattr(choice, "text"):
                    text = choice.text
                    finish_reason = getattr(choice, "finish_reason", "stop")
                else:
                    text = str(choice)
                    finish_reason = "stop"
                
                openai_choice = ChatCompletionChoice(
                    index=i,
                    message=ChatMessage(
                        role=MessageRole.ASSISTANT,
                        content=text
                    ),
                    finish_reason=finish_reason
                )
                choices.append(openai_choice)
        
        elif pepgenx_response.raw_response:
            # Try to extract text from raw response
            raw = pepgenx_response.raw_response
            text = ""
            
            # Common response field names to check
            for field in ["text", "content", "response", "output", "result"]:
                if field in raw:
                    text = str(raw[field])
                    break
            
            if not text and isinstance(raw, dict):
                # If no standard field found, try to find any string value
                for value in raw.values():
                    if isinstance(value, str) and len(value) > 10:  # Reasonable content length
                        text = value
                        break
            
            if not text:
                text = "No content found in response"
                logger.warning("Could not extract content from PepGenX response")
            
            choices.append(
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(
                        role=MessageRole.ASSISTANT,
                        content=text
                    ),
                    finish_reason="stop"
                )
            )
        
        else:
            # Fallback: empty response
            logger.warning("No choices or raw response found in PepGenX response")
            choices.append(
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(
                        role=MessageRole.ASSISTANT,
                        content="No response generated"
                    ),
                    finish_reason="stop"
                )
            )
        
        return choices
    
    @staticmethod
    def _translate_usage(pepgenx_response: PepGenXResponse) -> Optional[Usage]:
        """
        Translate PepGenX usage information to OpenAI format.
        
        Args:
            pepgenx_response: PepGenX response
            
        Returns:
            Optional[Usage]: OpenAI-compatible usage information
        """
        if pepgenx_response.usage:
            usage_data = pepgenx_response.usage
            
            # Handle different usage formats
            if isinstance(usage_data, dict):
                prompt_tokens = usage_data.get("prompt_tokens", 0)
                completion_tokens = usage_data.get("completion_tokens", 0)
                total_tokens = usage_data.get("total_tokens", prompt_tokens + completion_tokens)
            elif hasattr(usage_data, "prompt_tokens"):
                prompt_tokens = getattr(usage_data, "prompt_tokens", 0)
                completion_tokens = getattr(usage_data, "completion_tokens", 0)
                total_tokens = getattr(usage_data, "total_tokens", prompt_tokens + completion_tokens)
            else:
                # Fallback: estimate based on content length
                logger.debug("Usage information not in expected format, estimating")
                return ResponseTranslator._estimate_usage(pepgenx_response)
            
            return Usage(
                prompt_tokens=prompt_tokens or 0,
                completion_tokens=completion_tokens or 0,
                total_tokens=total_tokens or 0
            )
        
        else:
            # Try to extract from raw response
            if pepgenx_response.raw_response and isinstance(pepgenx_response.raw_response, dict):
                raw = pepgenx_response.raw_response
                if "usage" in raw:
                    usage_data = raw["usage"]
                    if isinstance(usage_data, dict):
                        return Usage(
                            prompt_tokens=usage_data.get("prompt_tokens", 0),
                            completion_tokens=usage_data.get("completion_tokens", 0),
                            total_tokens=usage_data.get("total_tokens", 0)
                        )
            
            # Estimate usage if not provided
            return ResponseTranslator._estimate_usage(pepgenx_response)
    
    @staticmethod
    def _estimate_usage(pepgenx_response: PepGenXResponse) -> Usage:
        """
        Estimate token usage when not provided by PepGenX.
        
        Args:
            pepgenx_response: PepGenX response
            
        Returns:
            Usage: Estimated usage information
        """
        # Simple estimation: ~4 characters per token (rough average for English)
        total_chars = 0
        
        if pepgenx_response.choices:
            for choice in pepgenx_response.choices:
                if isinstance(choice, dict):
                    text = choice.get("text", "")
                elif hasattr(choice, "text"):
                    text = choice.text
                else:
                    text = str(choice)
                total_chars += len(text)
        
        elif pepgenx_response.raw_response:
            # Estimate from raw response
            raw_str = str(pepgenx_response.raw_response)
            total_chars = len(raw_str)
        
        estimated_tokens = max(1, total_chars // 4)  # Rough estimation
        
        logger.debug("Estimated token usage", chars=total_chars, tokens=estimated_tokens)
        
        return Usage(
            prompt_tokens=0,  # We don't have prompt info in response
            completion_tokens=estimated_tokens,
            total_tokens=estimated_tokens
        )
