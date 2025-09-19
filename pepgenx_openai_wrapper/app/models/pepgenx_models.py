"""
PepGenX API models.

These models define the request and response structures for the PepGenX API,
based on the existing antropic_test.py script and expected API behavior.
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator

from ..core.config import settings


def get_default_system_prompt() -> int:
    """Get the default system prompt ID from settings."""
    try:
        default_prompt = settings.pepgenx_default_system_prompt
        # PepGenX API requires system_prompt to be 1-7, not 0
        if default_prompt == 0:
            return 1  # Use system prompt 1 instead of 0
        return default_prompt
    except Exception:
        # Fallback to 1 if settings not available (PepGenX requires 1-7)
        return 1


class PepGenXRequest(BaseModel):
    """PepGenX API request payload."""

    generation_model: str = Field(..., description="Model to use for generation")
    custom_prompt: str = Field(..., description="The prompt text for generation")
    system_prompt: Optional[Union[int, str]] = Field(
        default=None,
        description="System prompt identifier or text "
                    "(None=use default from config)"
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
    tools: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of tools the model can call"
    )
    tool_choice: Optional[Union[str, Dict[str, Any]]] = Field(
        default=None,
        description="Controls which tool is called by the model"
    )
    raw_response: Optional[bool] = Field(
        default=True,
        description="Whether to return raw response from PepGenX API"
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

    NOTE: Always returns 0 for direct response mode as requested.
    System prompts are handled by including them in the custom_prompt instead.

    Args:
        system_text: System prompt text from OpenAI request

    Returns:
        Union[int, str]: Always returns 0 for direct response mode
    """
    # Always use system prompt 0 (direct response mode) as requested
    return 0


def format_messages_for_pepgenx(messages: List[Dict[str, Any]]) -> tuple[str, Optional[Union[int, str]]]:
    """
    Convert OpenAI messages format to PepGenX custom_prompt and system_prompt.

    NOTE: Always uses system_prompt=0 (direct response mode). System messages
    are included in the custom_prompt for better control and consistency.

    Args:
        messages: List of OpenAI chat messages

    Returns:
        tuple: (custom_prompt, system_prompt) for PepGenX API
        system_prompt will always be 0 for direct response mode
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

    # Always use system prompt 0 (direct response mode)
    system_prompt = 0

    # Create custom prompt - include system messages at the beginning
    prompt_parts = []

    # Add system messages as instructions at the beginning
    if system_messages:
        system_text = " ".join(system_messages)
        prompt_parts.append(f"Instructions: {system_text}")

    # Add conversation messages
    if conversation_messages:
        # If there's only one user message and we have system instructions,
        # format it cleanly
        if len(conversation_messages) == 1 and conversation_messages[0].startswith("User: "):
            user_message = conversation_messages[0][6:]  # Remove "User: " prefix
            if system_messages:
                prompt_parts.append(f"\nUser: {user_message}")
            else:
                # No system messages, just use the user message directly
                prompt_parts = [user_message]
        else:
            # Multi-turn conversation
            prompt_parts.extend(conversation_messages)
    else:
        # Fallback: use the last message content
        last_message = messages[-1] if messages else {}
        fallback_content = last_message.get("content", "Hello")
        if system_messages:
            prompt_parts.append(f"\nUser: {fallback_content}")
        else:
            prompt_parts = [fallback_content]

    custom_prompt = "\n".join(prompt_parts) if len(prompt_parts) > 1 else prompt_parts[0] if prompt_parts else "Hello"

    return custom_prompt, system_prompt
