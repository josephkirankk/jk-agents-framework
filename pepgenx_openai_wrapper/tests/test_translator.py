"""
Tests for the translation services between OpenAI and PepGenX formats.
"""

import os
import pytest
from unittest.mock import Mock, patch

# Set test environment before importing app modules
os.environ.update({
    "PEPGENX_API_URL": "https://test-api.pepgenx.com/generate",
    "PEPGENX_PROJECT_ID": "test-project-123",
    "PEPGENX_TEAM_ID": "test-team-456",
    "PEPGENX_API_KEY": "test-pepgenx-api-key",
    "OKTA_TOKEN_FILE": "test_okta_token.json",
    "OPENAI_WRAPPER_API_KEYS": "sk-test-key1,sk-test-key2",
    "SECRET_KEY": "test-secret-key",
    "LOG_LEVEL": "DEBUG",
    "LOG_FORMAT": "json"
})

from app.models.openai_models import ChatCompletionRequest, ChatMessage, MessageRole
from app.models.pepgenx_models import PepGenXResponse, PepGenXChoice
from app.services.translator import RequestTranslator, ResponseTranslator


class TestRequestTranslator:
    """Test cases for OpenAI to PepGenX request translation."""
    
    def test_basic_chat_completion_translation(self):
        """Test basic chat completion request translation."""
        # Create OpenAI request
        openai_request = ChatCompletionRequest(
            model="gpt-4",
            messages=[
                ChatMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
                ChatMessage(role=MessageRole.USER, content="Hello, how are you?")
            ]
        )
        
        # Translate to PepGenX format
        pepgenx_request = RequestTranslator.translate_chat_completion(openai_request)
        
        # Verify translation
        assert pepgenx_request.generation_model == "gpt-4"
        assert "Hello, how are you?" in pepgenx_request.custom_prompt
        assert pepgenx_request.system_prompt == 2  # Default helpful assistant
    
    def test_model_mapping(self):
        """Test model name mapping from OpenAI to PepGenX."""
        test_cases = [
            ("gpt-4", "gpt-4"),
            ("gpt-4-turbo", "gpt-4-turbo"),
            ("gpt-4o", "gpt-4o"),
            ("claude-3-sonnet", "claude-3-sonnet"),
            ("unknown-model", "unknown-model")  # Should pass through
        ]
        
        for openai_model, expected_pepgenx_model in test_cases:
            openai_request = ChatCompletionRequest(
                model=openai_model,
                messages=[ChatMessage(role=MessageRole.USER, content="Test")]
            )
            
            pepgenx_request = RequestTranslator.translate_chat_completion(openai_request)
            assert pepgenx_request.generation_model == expected_pepgenx_model
    
    def test_parameter_mapping(self):
        """Test optional parameter mapping."""
        openai_request = ChatCompletionRequest(
            model="gpt-4",
            messages=[ChatMessage(role=MessageRole.USER, content="Test")],
            temperature=0.7,
            max_tokens=100,
            top_p=0.9,
            frequency_penalty=0.5,
            presence_penalty=0.3,
            stop=["END"]
        )
        
        pepgenx_request = RequestTranslator.translate_chat_completion(openai_request)
        
        assert pepgenx_request.temperature == 0.7
        assert pepgenx_request.max_tokens == 100
        assert pepgenx_request.top_p == 0.9
        assert pepgenx_request.frequency_penalty == 0.5
        assert pepgenx_request.presence_penalty == 0.3
        assert pepgenx_request.stop == ["END"]
    
    def test_conversation_formatting(self):
        """Test conversation message formatting."""
        openai_request = ChatCompletionRequest(
            model="gpt-4",
            messages=[
                ChatMessage(role=MessageRole.SYSTEM, content="You are helpful."),
                ChatMessage(role=MessageRole.USER, content="What is AI?"),
                ChatMessage(role=MessageRole.ASSISTANT, content="AI is artificial intelligence."),
                ChatMessage(role=MessageRole.USER, content="Tell me more.")
            ]
        )
        
        pepgenx_request = RequestTranslator.translate_chat_completion(openai_request)
        
        # Check that conversation is properly formatted
        assert "User: What is AI?" in pepgenx_request.custom_prompt
        assert "Assistant: AI is artificial intelligence." in pepgenx_request.custom_prompt
        assert "User: Tell me more." in pepgenx_request.custom_prompt


class TestResponseTranslator:
    """Test cases for PepGenX to OpenAI response translation."""
    
    def test_basic_response_translation(self):
        """Test basic response translation."""
        # Create mock PepGenX response
        pepgenx_response = PepGenXResponse(
            id="test-id",
            model="gpt-4",
            choices=[
                PepGenXChoice(text="Hello! I'm doing well, thank you for asking.", index=0)
            ],
            created=1703123456
        )
        
        # Create mock original request
        original_request = ChatCompletionRequest(
            model="gpt-4",
            messages=[ChatMessage(role=MessageRole.USER, content="Hello")]
        )
        
        # Translate response
        openai_response = ResponseTranslator.translate_chat_completion(
            pepgenx_response, original_request, "test-request-id"
        )
        
        # Verify translation
        assert openai_response.id == "test-request-id"
        assert openai_response.model == "gpt-4"
        assert len(openai_response.choices) == 1
        assert openai_response.choices[0].message.role == MessageRole.ASSISTANT
        assert openai_response.choices[0].message.content == "Hello! I'm doing well, thank you for asking."
        assert openai_response.created == 1703123456
    
    def test_raw_response_handling(self):
        """Test handling of raw response format."""
        # Create PepGenX response with raw data
        pepgenx_response = PepGenXResponse(
            raw_response={
                "text": "This is a raw response",
                "status": "completed"
            }
        )
        
        original_request = ChatCompletionRequest(
            model="gpt-4",
            messages=[ChatMessage(role=MessageRole.USER, content="Test")]
        )
        
        openai_response = ResponseTranslator.translate_chat_completion(
            pepgenx_response, original_request
        )
        
        assert len(openai_response.choices) == 1
        assert openai_response.choices[0].message.content == "This is a raw response"
    
    def test_error_response_handling(self):
        """Test handling of error responses."""
        pepgenx_response = PepGenXResponse(
            error="API rate limit exceeded",
            error_code="rate_limit"
        )
        
        original_request = ChatCompletionRequest(
            model="gpt-4",
            messages=[ChatMessage(role=MessageRole.USER, content="Test")]
        )
        
        openai_response = ResponseTranslator.translate_chat_completion(
            pepgenx_response, original_request
        )
        
        assert len(openai_response.choices) == 1
        assert "Error: API rate limit exceeded" in openai_response.choices[0].message.content
        assert openai_response.choices[0].finish_reason == "error"
    
    def test_usage_translation(self):
        """Test usage information translation."""
        pepgenx_response = PepGenXResponse(
            choices=[PepGenXChoice(text="Test response", index=0)],
            usage={
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        )
        
        original_request = ChatCompletionRequest(
            model="gpt-4",
            messages=[ChatMessage(role=MessageRole.USER, content="Test")]
        )
        
        openai_response = ResponseTranslator.translate_chat_completion(
            pepgenx_response, original_request
        )
        
        assert openai_response.usage is not None
        assert openai_response.usage.prompt_tokens == 10
        assert openai_response.usage.completion_tokens == 5
        assert openai_response.usage.total_tokens == 15
    
    def test_usage_estimation(self):
        """Test usage estimation when not provided."""
        pepgenx_response = PepGenXResponse(
            choices=[PepGenXChoice(text="This is a test response with some content", index=0)]
        )
        
        original_request = ChatCompletionRequest(
            model="gpt-4",
            messages=[ChatMessage(role=MessageRole.USER, content="Test")]
        )
        
        openai_response = ResponseTranslator.translate_chat_completion(
            pepgenx_response, original_request
        )
        
        assert openai_response.usage is not None
        assert openai_response.usage.completion_tokens > 0
        assert openai_response.usage.total_tokens > 0


# Integration test fixtures
@pytest.fixture
def sample_openai_request():
    """Sample OpenAI request for testing."""
    return ChatCompletionRequest(
        model="gpt-4",
        messages=[
            ChatMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
            ChatMessage(role=MessageRole.USER, content="What is the capital of France?")
        ],
        temperature=0.7,
        max_tokens=100
    )


@pytest.fixture
def sample_pepgenx_response():
    """Sample PepGenX response for testing."""
    return PepGenXResponse(
        id="pepgenx-123",
        model="gpt-4",
        choices=[
            PepGenXChoice(
                text="The capital of France is Paris.",
                index=0,
                finish_reason="stop"
            )
        ],
        usage={
            "prompt_tokens": 15,
            "completion_tokens": 8,
            "total_tokens": 23
        },
        created=1703123456
    )


def test_round_trip_translation(sample_openai_request, sample_pepgenx_response):
    """Test complete round-trip translation."""
    # Translate request
    pepgenx_request = RequestTranslator.translate_chat_completion(sample_openai_request)
    
    # Verify request translation
    assert pepgenx_request.generation_model == "gpt-4"
    assert "What is the capital of France?" in pepgenx_request.custom_prompt
    assert pepgenx_request.temperature == 0.7
    assert pepgenx_request.max_tokens == 100
    
    # Translate response
    openai_response = ResponseTranslator.translate_chat_completion(
        sample_pepgenx_response, sample_openai_request, "test-123"
    )
    
    # Verify response translation
    assert openai_response.id == "test-123"
    assert openai_response.model == "gpt-4"
    assert len(openai_response.choices) == 1
    assert openai_response.choices[0].message.content == "The capital of France is Paris."
    assert openai_response.usage.total_tokens == 23
