"""
Tests for conversation memory functionality in JK-Agents Framework.

This module tests the PostgreSQL-based conversation storage, context enhancement,
and integration with API endpoints.
"""
import asyncio
import os
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from typing import Dict, Any
from unittest.mock import AsyncMock, Mock, patch

# Test configuration for PostgreSQL
TEST_DATABASE_URL = os.getenv(
    'TEST_DATABASE_URL',
    'postgresql://jkagent_user:securepassword@localhost:5432/conversations_test'
)

# Import modules to test
from app.config import AppConfig, ConversationMemoryConfig
from app.memory.conversation_store import ConversationStore, ConversationEntry
from app.memory.context_enhancer import ConversationContextEnhancer
from app.memory.memory_integration import (
    initialize_conversation_memory,
    enhance_system_message_with_memory,
    store_conversation_memory,
    is_conversation_memory_enabled
)


class TestConversationStore:
    """Test cases for ConversationStore."""

    @pytest_asyncio.fixture
    async def store(self):
        """Create a test conversation store."""
        store = ConversationStore(TEST_DATABASE_URL, pool_size=2)
        await store.initialize()
        yield store
        await store.close()

    @pytest_asyncio.fixture
    async def clean_store(self, store):
        """Provide a clean store and cleanup after test."""
        # Clean any existing test data
        await store.delete_conversation_history("test_thread_1")
        await store.delete_conversation_history("test_thread_2")
        yield store
        # Cleanup after test
        await store.delete_conversation_history("test_thread_1")
        await store.delete_conversation_history("test_thread_2")

    @pytest.mark.asyncio
    async def test_store_conversation(self, clean_store):
        """Test storing a conversation entry."""
        thread_id = "test_thread_1"
        user_message = "Hello, how can you help me?"
        assistant_response = "I can help you with various tasks."
        metadata = {"test": True}
        
        await clean_store.store_conversation(
            thread_id=thread_id,
            user_message=user_message,
            assistant_response=assistant_response,
            metadata=metadata
        )
        
        conversations = await clean_store.get_conversation_history(thread_id, limit=1)
        assert len(conversations) == 1
        
        conv = conversations[0]
        assert conv.thread_id == thread_id
        assert conv.user_message == user_message
        assert conv.assistant_response == assistant_response
        assert conv.metadata == metadata

    @pytest.mark.asyncio
    async def test_get_recent_conversations(self, clean_store):
        """Test retrieving recent conversations."""
        thread_id = "test_thread_1"
        
        # Store multiple conversations
        conversations_data = [
            ("First question", "First response"),
            ("Second question", "Second response"),
            ("Third question", "Third response")
        ]
        
        for user_msg, assistant_msg in conversations_data:
            await clean_store.store_conversation(
                thread_id=thread_id,
                user_message=user_msg,
                assistant_response=assistant_msg
            )
            await asyncio.sleep(0.1)  # Small delay to ensure different timestamps
        
        # Get recent conversations
        recent = await clean_store.get_recent_conversations(thread_id, limit=2)
        assert len(recent) == 2
        
        # Should be in chronological order (oldest to newest)
        assert recent[0].user_message == "Second question"
        assert recent[1].user_message == "Third question"

    @pytest.mark.asyncio
    async def test_count_conversations(self, clean_store):
        """Test counting conversations."""
        thread_id = "test_thread_1"
        
        # Initially should be 0
        count = await clean_store.count_conversations(thread_id)
        assert count == 0
        
        # Add some conversations
        for i in range(3):
            await clean_store.store_conversation(
                thread_id=thread_id,
                user_message=f"Question {i}",
                assistant_response=f"Response {i}"
            )
        
        count = await clean_store.count_conversations(thread_id)
        assert count == 3

    @pytest.mark.asyncio
    async def test_delete_conversation_history(self, clean_store):
        """Test deleting conversation history."""
        thread_id = "test_thread_1"
        
        # Add conversations
        await clean_store.store_conversation(
            thread_id=thread_id,
            user_message="Test question",
            assistant_response="Test response"
        )
        
        # Verify it exists
        count = await clean_store.count_conversations(thread_id)
        assert count == 1
        
        # Delete and verify
        deleted_count = await clean_store.delete_conversation_history(thread_id)
        assert deleted_count == 1
        
        count = await clean_store.count_conversations(thread_id)
        assert count == 0


class TestConversationContextEnhancer:
    """Test cases for ConversationContextEnhancer."""

    @pytest.fixture
    def enhancer(self):
        """Create a test context enhancer with mock store."""
        mock_store = AsyncMock()
        return ConversationContextEnhancer(store=mock_store)

    def test_format_conversation_history_empty(self, enhancer):
        """Test formatting empty conversation history."""
        result = enhancer.format_conversation_history([])
        assert result == ""

    def test_format_conversation_history(self, enhancer):
        """Test formatting conversation history."""
        conversations = [
            ConversationEntry(
                thread_id="test",
                user_message="Hello",
                assistant_response="Hi there!",
                timestamp=datetime.now(timezone.utc)
            ),
            ConversationEntry(
                thread_id="test",
                user_message="How are you?",
                assistant_response="I'm doing well, thank you!",
                timestamp=datetime.now(timezone.utc)
            )
        ]
        
        result = enhancer.format_conversation_history(conversations)
        
        assert "Previous conversation:" in result
        assert "User: Hello" in result
        assert "Assistant: Hi there!" in result
        assert "User: How are you?" in result
        assert "Assistant: I'm doing well, thank you!" in result

    def test_format_conversation_history_truncation(self, enhancer):
        """Test conversation history truncation."""
        # Create a conversation with very long content
        long_message = "This is a very long message. " * 100
        conversations = [
            ConversationEntry(
                thread_id="test",
                user_message=long_message,
                assistant_response=long_message,
                timestamp=datetime.now(timezone.utc)
            )
        ]
        
        result = enhancer.format_conversation_history(conversations, max_length=200)
        
        assert len(result) <= 200
        assert "Previous conversation:" in result
        assert "... (conversation history truncated)" in result

    @pytest.mark.asyncio
    async def test_get_conversation_context(self, enhancer):
        """Test getting conversation context."""
        # Mock store response
        mock_conversations = [
            ConversationEntry(
                thread_id="test_thread",
                user_message="Test question",
                assistant_response="Test response",
                timestamp=datetime.now(timezone.utc)
            )
        ]
        enhancer.store.get_recent_conversations.return_value = mock_conversations
        
        result = await enhancer.get_conversation_context("test_thread", max_conversations=1)
        
        assert "Previous conversation:" in result
        assert "User: Test question" in result
        assert "Assistant: Test response" in result
        enhancer.store.get_recent_conversations.assert_called_once_with(
            thread_id="test_thread",
            limit=1
        )

    @pytest.mark.asyncio
    async def test_enhance_system_message(self, enhancer):
        """Test enhancing system message with conversation context."""
        original_message = "You are a helpful assistant."
        
        # Mock store response
        mock_conversations = [
            ConversationEntry(
                thread_id="test_thread",
                user_message="Previous question",
                assistant_response="Previous response",
                timestamp=datetime.now(timezone.utc)
            )
        ]
        enhancer.store.get_recent_conversations.return_value = mock_conversations
        
        result = await enhancer.enhance_system_message(
            original_message=original_message,
            thread_id="test_thread",
            max_conversations=1
        )
        
        assert original_message in result
        assert "Previous conversation:" in result
        assert "User: Previous question" in result
        assert "Assistant: Previous response" in result

    @pytest.mark.asyncio
    async def test_enhance_system_message_prepend(self, enhancer):
        """Test enhancing system message with prepend option."""
        original_message = "You are a helpful assistant."
        
        # Mock store response
        mock_conversations = [
            ConversationEntry(
                thread_id="test_thread",
                user_message="Previous question",
                assistant_response="Previous response",
                timestamp=datetime.now(timezone.utc)
            )
        ]
        enhancer.store.get_recent_conversations.return_value = mock_conversations
        
        result = await enhancer.enhance_system_message(
            original_message=original_message,
            thread_id="test_thread",
            max_conversations=1,
            prepend=True
        )
        
        # Context should come before the original message
        context_index = result.find("Previous conversation:")
        original_index = result.find(original_message)
        assert context_index < original_index

    @pytest.mark.asyncio
    async def test_store_conversation_entry(self, enhancer):
        """Test storing conversation entry."""
        await enhancer.store_conversation_entry(
            thread_id="test_thread",
            user_message="Test question",
            assistant_response="Test response",
            metadata={"test": True}
        )
        
        enhancer.store.store_conversation.assert_called_once_with(
            thread_id="test_thread",
            user_message="Test question",
            assistant_response="Test response",
            metadata={"test": True}
        )


class TestMemoryIntegration:
    """Test cases for memory integration functions."""

    @pytest.fixture
    def app_config(self):
        """Create test app configuration."""
        return AppConfig(
            models={"default": "openai:gpt-4o-mini"},
            supervisor={"name": "test_supervisor", "prompt": "Test supervisor prompt"},
            agents=[],
            conversation_memory=ConversationMemoryConfig(
                enabled=True,
                database_url=TEST_DATABASE_URL,
                max_conversations=5,
                max_context_length=2000,
                pool_size=2
            )
        )

    @pytest.fixture
    def disabled_memory_config(self):
        """Create app configuration with disabled memory."""
        return AppConfig(
            models={"default": "openai:gpt-4o-mini"},
            supervisor={"name": "test_supervisor", "prompt": "Test supervisor prompt"},
            agents=[],
            conversation_memory=ConversationMemoryConfig(enabled=False)
        )

    @pytest.mark.asyncio
    async def test_initialize_conversation_memory_disabled(self, disabled_memory_config):
        """Test initialization with disabled memory."""
        result = await initialize_conversation_memory(disabled_memory_config)
        assert result is False

    @pytest.mark.asyncio
    async def test_initialize_conversation_memory_no_url(self):
        """Test initialization without database URL."""
        config = AppConfig(
            models={"default": "openai:gpt-4o-mini"},
            supervisor={"name": "test_supervisor", "prompt": "Test supervisor prompt"},
            agents=[],
            conversation_memory=ConversationMemoryConfig(
                enabled=True,
                database_url=None
            )
        )
        
        with patch.dict(os.environ, {}, clear=True):
            result = await initialize_conversation_memory(config)
            assert result is False

    @pytest.mark.asyncio
    @patch('app.memory.memory_integration.initialize_conversation_store')
    async def test_initialize_conversation_memory_success(self, mock_init, app_config):
        """Test successful memory initialization."""
        mock_init.return_value = Mock()
        
        result = await initialize_conversation_memory(app_config)
        assert result is True
        mock_init.assert_called_once_with(
            database_url=TEST_DATABASE_URL,
            pool_size=2
        )

    @pytest.mark.asyncio
    @patch('app.memory.memory_integration.get_context_enhancer')
    async def test_enhance_system_message_with_memory(self, mock_get_enhancer, app_config):
        """Test enhancing system message with memory."""
        mock_enhancer = AsyncMock()
        mock_enhancer.enhance_system_message.return_value = "Enhanced message"
        mock_get_enhancer.return_value = mock_enhancer
        
        result = await enhance_system_message_with_memory(
            original_message="Original message",
            thread_id="test_thread",
            app_config=app_config
        )
        
        assert result == "Enhanced message"
        mock_enhancer.enhance_system_message.assert_called_once_with(
            original_message="Original message",
            thread_id="test_thread",
            max_conversations=5,
            max_length=2000,
            prepend=False
        )

    @pytest.mark.asyncio
    async def test_enhance_system_message_with_memory_disabled(self, disabled_memory_config):
        """Test enhancing system message with disabled memory."""
        original_message = "Original message"
        
        result = await enhance_system_message_with_memory(
            original_message=original_message,
            thread_id="test_thread",
            app_config=disabled_memory_config
        )
        
        assert result == original_message

    @pytest.mark.asyncio
    @patch('app.memory.memory_integration.get_context_enhancer')
    async def test_store_conversation_memory(self, mock_get_enhancer, app_config):
        """Test storing conversation memory."""
        mock_enhancer = AsyncMock()
        mock_get_enhancer.return_value = mock_enhancer
        
        await store_conversation_memory(
            thread_id="test_thread",
            user_message="Test question",
            assistant_response="Test response",
            app_config=app_config,
            metadata={"test": True}
        )
        
        mock_enhancer.store_conversation_entry.assert_called_once_with(
            thread_id="test_thread",
            user_message="Test question",
            assistant_response="Test response",
            metadata={"test": True}
        )

    @pytest.mark.asyncio
    async def test_store_conversation_memory_disabled(self, disabled_memory_config):
        """Test storing conversation memory with disabled memory."""
        # Should not raise any exceptions
        await store_conversation_memory(
            thread_id="test_thread",
            user_message="Test question",
            assistant_response="Test response",
            app_config=disabled_memory_config
        )

    def test_is_conversation_memory_enabled(self, app_config, disabled_memory_config):
        """Test checking if conversation memory is enabled."""
        assert is_conversation_memory_enabled(app_config) is True
        assert is_conversation_memory_enabled(disabled_memory_config) is False

    def test_is_conversation_memory_enabled_no_url(self):
        """Test checking memory enablement without database URL."""
        config = AppConfig(
            models={"default": "openai:gpt-4o-mini"},
            supervisor={"name": "test_supervisor", "prompt": "Test supervisor prompt"},
            agents=[],
            conversation_memory=ConversationMemoryConfig(
                enabled=True,
                database_url=None
            )
        )
        
        with patch.dict(os.environ, {}, clear=True):
            assert is_conversation_memory_enabled(config) is False


# Integration tests (require actual PostgreSQL database)
@pytest.mark.integration
class TestConversationMemoryIntegration:
    """Integration tests for conversation memory with real database."""

    @pytest_asyncio.fixture
    async def real_store(self):
        """Create a real conversation store for integration testing."""
        store = ConversationStore(TEST_DATABASE_URL, pool_size=2)
        await store.initialize()
        
        # Clean up any existing test data
        await store.delete_conversation_history("integration_test_thread")
        
        yield store
        
        # Cleanup after test
        await store.delete_conversation_history("integration_test_thread")
        await store.close()

    @pytest.mark.asyncio
    async def test_full_conversation_flow(self, real_store):
        """Test complete conversation storage and retrieval flow."""
        thread_id = "integration_test_thread"
        enhancer = ConversationContextEnhancer(store=real_store)
        
        # Initially should have no context
        context = await enhancer.get_conversation_context(thread_id, max_conversations=5)
        assert context == ""
        
        # Store first conversation
        await enhancer.store_conversation_entry(
            thread_id=thread_id,
            user_message="What is the weather like?",
            assistant_response="I don't have access to real-time weather data, but I can help you find weather information."
        )
        
        # Should now have context
        context = await enhancer.get_conversation_context(thread_id, max_conversations=5)
        assert "Previous conversation:" in context
        assert "What is the weather like?" in context
        
        # Store second conversation
        await enhancer.store_conversation_entry(
            thread_id=thread_id,
            user_message="Can you help me with Python programming?",
            assistant_response="Yes, I'd be happy to help you with Python programming!"
        )
        
        # Should have both conversations in context
        context = await enhancer.get_conversation_context(thread_id, max_conversations=5)
        assert "What is the weather like?" in context
        assert "Can you help me with Python programming?" in context
        
        # Test system message enhancement
        original_system = "You are a helpful assistant."
        enhanced_system = await enhancer.enhance_system_message(
            original_message=original_system,
            thread_id=thread_id,
            max_conversations=2
        )
        
        assert original_system in enhanced_system
        assert "Previous conversation:" in enhanced_system
        assert "What is the weather like?" in enhanced_system
        assert "Can you help me with Python programming?" in enhanced_system


if __name__ == "__main__":
    pytest.main([__file__, "-v"])