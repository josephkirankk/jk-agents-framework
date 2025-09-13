"""
PepGenX API models.

These models define the request and response structures for the PepGenX API,
based on the existing antropic_test.py script and expected API behavior.
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class PepGenXRequest(BaseModel):
    """PepGenX API request payload."""
    
    generation_model: str = Field(..., description="Model to use for generation")
    custom_prompt: str = Field(..., description="The prompt text for generation")
    system_prompt: Union[int, str] = Field(
        default=2,
        description="System prompt identifier or text"
    )
    
    # Optional parameters that might be supported
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Sampling temperature"
    )
    max_tokens: Optional[int] = Field(
        default=None,
        gt=0,
        description="Maximum tokens to generate"
    )
    top_p: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling parameter"
    )
    frequency_penalty: Optional[float] = Field(
        default=None,
        ge=-2.0,
        le=2.0,
        description="Frequency penalty"
    )
    presence_penalty: Optional[float] = Field(
        default=None,
        ge=-2.0,
        le=2.0,
        description="Presence penalty"
    )
    stop: Optional[Union[str, List[str]]] = Field(
        default=None,
        description="Stop sequences"
    )
    
    @field_validator("custom_prompt")
    @classmethod
    def validate_custom_prompt(cls, v):
        """Ensure custom prompt is not empty."""
        if not v or not v.strip():
            raise ValueError("Custom prompt cannot be empty")
        return v.strip()

    @field_validator("generation_model")
    @classmethod
    def validate_generation_model(cls, v):
        """Ensure generation model is not empty."""
        if not v or not v.strip():
            raise ValueError("Generation model cannot be empty")
        return v.strip()


class PepGenXChoice(BaseModel):
    """A choice in PepGenX response (structure to be determined)."""
    text: str = Field(..., description="Generated text")
    index: Optional[int] = Field(default=0, description="Choice index")
    finish_reason: Optional[str] = Field(default=None, description="Finish reason")
    logprobs: Optional[Dict[str, Any]] = Field(default=None, description="Log probabilities")


class PepGenXUsage(BaseModel):
    """Token usage information from PepGenX."""
    prompt_tokens: Optional[int] = Field(default=None, description="Prompt tokens used")
    completion_tokens: Optional[int] = Field(default=None, description="Completion tokens used")
    total_tokens: Optional[int] = Field(default=None, description="Total tokens used")


class PepGenXResponse(BaseModel):
    """
    PepGenX API response.
    
    Note: This structure is based on assumptions and may need to be updated
    based on actual PepGenX API response format.
    """
    
    # Core response fields
    id: Optional[str] = Field(default=None, description="Response ID")
    model: Optional[str] = Field(default=None, description="Model used")
    choices: Optional[List[PepGenXChoice]] = Field(default=None, description="Generated choices")
    usage: Optional[PepGenXUsage] = Field(default=None, description="Token usage")
    
    # Raw response fields (for handling unknown response formats)
    raw_response: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Raw response from PepGenX API"
    )
    
    # Metadata
    created: Optional[int] = Field(default=None, description="Creation timestamp")
    object: Optional[str] = Field(default=None, description="Object type")
    
    # Error handling
    error: Optional[str] = Field(default=None, description="Error message if any")
    error_code: Optional[str] = Field(default=None, description="Error code if any")
    
    @field_validator("choices", mode="before")
    @classmethod
    def validate_choices(cls, v):
        """Handle various choice formats."""
        if v is None:
            return None

        if isinstance(v, list):
            return v

        # If it's a single choice, wrap it in a list
        if isinstance(v, dict):
            return [v]

        # If it's a string, create a simple choice
        if isinstance(v, str):
            return [{"text": v, "index": 0}]

        return v


class PepGenXErrorResponse(BaseModel):
    """PepGenX API error response."""
    
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(default=None, description="Error code")
    error_type: Optional[str] = Field(default=None, description="Error type")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    
    # HTTP status information
    status_code: Optional[int] = Field(default=None, description="HTTP status code")
    
    # Request context
    request_id: Optional[str] = Field(default=None, description="Request ID for debugging")


# System prompt mappings
SYSTEM_PROMPT_MAPPINGS = {
    1: "default",
    2: "helpful_assistant",
    3: "creative_writer",
    4: "code_assistant",
    5: "analytical_thinker",
    # Add more mappings as needed
}


def get_system_prompt_id(system_text: Optional[str]) -> Union[int, str]:
    """
    Map system prompt text to PepGenX system prompt ID.
    
    Args:
        system_text: System prompt text from OpenAI request
        
    Returns:
        Union[int, str]: System prompt ID or text for PepGenX
    """
    if not system_text:
        return 2  # Default helpful assistant
    
    # Simple keyword matching for common system prompts
    text_lower = system_text.lower()
    
    if "helpful assistant" in text_lower:
        return 2
    elif "creative" in text_lower or "writer" in text_lower:
        return 3
    elif "code" in text_lower or "programming" in text_lower:
        return 4
    elif "analyz" in text_lower or "analytical" in text_lower:
        return 5
    else:
        # For custom system prompts, we might need to pass the text directly
        # This depends on PepGenX API capabilities
        return system_text


def format_messages_for_pepgenx(messages: List[Dict[str, Any]]) -> tuple[str, Union[int, str]]:
    """
    Convert OpenAI messages format to PepGenX custom_prompt and system_prompt.
    
    Args:
        messages: List of OpenAI chat messages
        
    Returns:
        tuple: (custom_prompt, system_prompt) for PepGenX API
    """
    system_messages = []
    conversation_messages = []
    
    for message in messages:
        role = message.get("role", "")
        content = message.get("content", "")
        
        if role == "system" or role == "developer":
            system_messages.append(content)
        elif role in ["user", "assistant"]:
            # Format as conversation
            if role == "user":
                conversation_messages.append(f"User: {content}")
            else:
                conversation_messages.append(f"Assistant: {content}")
    
    # Combine system messages
    system_prompt = get_system_prompt_id(
        " ".join(system_messages) if system_messages else None
    )
    
    # Create custom prompt
    if conversation_messages:
        custom_prompt = "\n".join(conversation_messages)
    else:
        # Fallback: use the last message content
        last_message = messages[-1] if messages else {}
        custom_prompt = last_message.get("content", "Hello")
    
    return custom_prompt, system_prompt
