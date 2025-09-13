"""
OpenAI-compatible API models.

These models define the request and response structures that match the OpenAI API specification,
ensuring compatibility with existing OpenAI client libraries and applications.
"""

import time
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class MessageRole(str, Enum):
    """Message roles in OpenAI chat format."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    DEVELOPER = "developer"
    FUNCTION = "function"
    TOOL = "tool"


class ChatMessage(BaseModel):
    """A single message in a chat conversation."""
    role: MessageRole = Field(..., description="The role of the message author")
    content: Optional[Union[str, List[Dict[str, Any]]]] = Field(
        None, description="The content of the message"
    )
    name: Optional[str] = Field(
        None, description="The name of the author of this message"
    )

    @model_validator(mode='after')
    def validate_and_normalize_content(self):
        """Normalize content format and validate."""
        # Handle both string and array content formats
        if isinstance(self.content, list):
            # Extract text from array format: [{'type': 'text', 'text': '...'}]
            text_parts = []
            for item in self.content:
                if isinstance(item, dict) and item.get('type') == 'text':
                    text_parts.append(item.get('text', ''))
                elif isinstance(item, dict) and 'text' in item:
                    text_parts.append(item['text'])
            self.content = ' '.join(text_parts)

        # Validate content is provided for required message types
        if self.role in [MessageRole.SYSTEM, MessageRole.USER, MessageRole.ASSISTANT]:
            if not self.content or (isinstance(self.content, str) and not self.content.strip()):
                raise ValueError(f"Content is required for {self.role} messages")

        return self


class ChatCompletionRequest(BaseModel):
    """OpenAI Chat Completion API request."""
    
    # Required fields
    model: str = Field(..., description="ID of the model to use")
    messages: List[ChatMessage] = Field(..., description="List of messages in the conversation")
    
    # Optional fields with OpenAI defaults
    frequency_penalty: Optional[float] = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Penalty for frequency of tokens"
    )
    logit_bias: Optional[Dict[str, float]] = Field(
        default=None,
        description="Modify likelihood of specified tokens"
    )
    logprobs: Optional[bool] = Field(
        default=False,
        description="Whether to return log probabilities"
    )
    top_logprobs: Optional[int] = Field(
        default=None,
        ge=0,
        le=20,
        description="Number of most likely tokens to return"
    )
    max_tokens: Optional[int] = Field(
        default=None,
        gt=0,
        description="Maximum number of tokens to generate"
    )
    n: Optional[int] = Field(
        default=1,
        ge=1,
        le=128,
        description="Number of chat completion choices to generate"
    )
    presence_penalty: Optional[float] = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Penalty for presence of tokens"
    )
    response_format: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Format of the response"
    )
    seed: Optional[int] = Field(
        default=None,
        description="Random seed for deterministic generation"
    )
    stop: Optional[Union[str, List[str]]] = Field(
        default=None,
        description="Stop sequences"
    )
    stream: Optional[bool] = Field(
        default=False,
        description="Whether to stream back partial progress"
    )
    temperature: Optional[float] = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        description="Sampling temperature"
    )
    top_p: Optional[float] = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling parameter"
    )
    user: Optional[str] = Field(
        default=None,
        description="Unique identifier for the end-user"
    )
    
    @field_validator("messages")
    @classmethod
    def validate_messages(cls, v):
        """Ensure at least one message is provided."""
        if not v:
            raise ValueError("At least one message is required")
        return v

    @field_validator("model")
    @classmethod
    def validate_model(cls, v):
        """Validate model name format."""
        if not v or not v.strip():
            raise ValueError("Model name cannot be empty")
        return v.strip()


class Usage(BaseModel):
    """Token usage information."""
    prompt_tokens: int = Field(..., description="Number of tokens in the prompt")
    completion_tokens: int = Field(..., description="Number of tokens in the completion")
    total_tokens: int = Field(..., description="Total number of tokens used")


class ChatCompletionChoice(BaseModel):
    """A single choice in a chat completion response."""
    index: int = Field(..., description="The index of this choice")
    message: ChatMessage = Field(..., description="The generated message")
    finish_reason: Optional[str] = Field(
        default=None,
        description="Reason why the model stopped generating"
    )
    logprobs: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Log probabilities for the choice"
    )


class ChatCompletionResponse(BaseModel):
    """OpenAI Chat Completion API response."""
    id: str = Field(..., description="Unique identifier for the completion")
    object: Literal["chat.completion"] = Field(
        default="chat.completion",
        description="Object type"
    )
    created: int = Field(
        default_factory=lambda: int(time.time()),
        description="Unix timestamp of creation"
    )
    model: str = Field(..., description="Model used for the completion")
    choices: List[ChatCompletionChoice] = Field(..., description="List of completion choices")
    usage: Optional[Usage] = Field(default=None, description="Token usage information")
    system_fingerprint: Optional[str] = Field(
        default=None,
        description="System fingerprint"
    )


class ChatCompletionStreamChoice(BaseModel):
    """A single choice in a streaming chat completion response."""
    index: int = Field(..., description="The index of this choice")
    delta: Dict[str, Any] = Field(..., description="The delta for this choice")
    finish_reason: Optional[str] = Field(
        default=None,
        description="Reason why the model stopped generating"
    )


class ChatCompletionStreamResponse(BaseModel):
    """OpenAI Chat Completion streaming response chunk."""
    id: str = Field(..., description="Unique identifier for the completion")
    object: Literal["chat.completion.chunk"] = Field(
        default="chat.completion.chunk",
        description="Object type"
    )
    created: int = Field(
        default_factory=lambda: int(time.time()),
        description="Unix timestamp of creation"
    )
    model: str = Field(..., description="Model used for the completion")
    choices: List[ChatCompletionStreamChoice] = Field(..., description="List of completion choices")
    system_fingerprint: Optional[str] = Field(
        default=None,
        description="System fingerprint"
    )


class ErrorDetail(BaseModel):
    """Error detail information."""
    message: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")
    param: Optional[str] = Field(default=None, description="Parameter that caused the error")
    code: Optional[str] = Field(default=None, description="Error code")


class ErrorResponse(BaseModel):
    """OpenAI-compatible error response."""
    error: ErrorDetail = Field(..., description="Error details")


# Model mapping for PepGenX compatibility
OPENAI_TO_PEPGENX_MODELS = {
    "gpt-4": "gpt-4",
    "gpt-4-turbo": "gpt-4-turbo",
    "gpt-4o": "gpt-4o",
    "gpt-4o-mini": "gpt-4o-mini",
    "gpt-3.5-turbo": "gpt-3.5-turbo",
    "gpt-5": "gpt-5",
    "claude-3-sonnet": "claude-3-sonnet",
    "claude-3-haiku": "claude-3-haiku",
    "claude-3-opus": "claude-3-opus",
    "claude-3-7-sonnet": "claude-3-7-sonnet",
}


def get_pepgenx_model(openai_model: str) -> str:
    """
    Map OpenAI model name to PepGenX model name.
    
    Args:
        openai_model: OpenAI model identifier
        
    Returns:
        str: PepGenX model identifier
    """
    return OPENAI_TO_PEPGENX_MODELS.get(openai_model, openai_model)
