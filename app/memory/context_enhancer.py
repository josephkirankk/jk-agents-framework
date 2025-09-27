"""
Conversation context enhancement for JK-Agents Framework.

This module provides functionality to extract conversation history from storage
and format it for injection into agent system context, enabling conversation memory.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from .conversation_store import ConversationStore, ConversationEntry, get_conversation_store


logger = logging.getLogger(__name__)


class ConversationContextEnhancer:
    """
    Enhances agent system context with conversation history.
    
    This class retrieves past conversation entries from storage and formats them
    into a readable context that can be injected into agent system messages.
    """

    def __init__(self, store: Optional[ConversationStore] = None):
        """
        Initialize the context enhancer.
        
        Args:
            store: Optional ConversationStore instance. If None, uses global store.
        """
        self.store = store

    def _get_store(self) -> ConversationStore:
        """Get the conversation store instance."""
        if self.store is not None:
            return self.store
        return get_conversation_store()

    def format_conversation_history(
        self,
        conversations: List[ConversationEntry],
        max_length: Optional[int] = 2000
    ) -> str:
        """
        Format conversation entries into a readable context string.
        
        Args:
            conversations: List of conversation entries to format
            max_length: Optional maximum length of formatted string
            
        Returns:
            Formatted conversation history string
        """
        if not conversations:
            return ""

        # Build conversation context
        context_parts = ["Previous conversation:"]
        
        for conv in conversations:
            user_part = f"User: {conv.user_message.strip()}"
            assistant_part = f"Assistant: {conv.assistant_response.strip()}"
            
            context_parts.extend([user_part, assistant_part, ""])  # Empty string for spacing

        # Join all parts
        full_context = "\n".join(context_parts).rstrip()  # Remove trailing newlines
        
        # Truncate if necessary
        if max_length and len(full_context) > max_length:
            # Try to truncate at conversation boundaries
            lines = full_context.split('\n')
            truncated_lines = ["Previous conversation:"]
            current_length = len(truncated_lines[0])
            
            # Add conversations until we approach the limit
            for i in range(1, len(lines)):
                line = lines[i]
                if current_length + len(line) + 1 > max_length - 50:  # Leave some buffer
                    truncated_lines.append("... (conversation history truncated)")
                    break
                truncated_lines.append(line)
                current_length += len(line) + 1  # +1 for newline
                
            full_context = "\n".join(truncated_lines)
            
        return full_context

    async def get_conversation_context(
        self,
        thread_id: str,
        max_conversations: int = 5,
        max_length: Optional[int] = 2000
    ) -> str:
        """
        Get formatted conversation context for a thread.
        
        Args:
            thread_id: Thread identifier to get history for
            max_conversations: Maximum number of recent conversations to include
            max_length: Optional maximum length of formatted context
            
        Returns:
            Formatted conversation context string
        """
        try:
            store = self._get_store()
            conversations = await store.get_recent_conversations(
                thread_id=thread_id,
                limit=max_conversations
            )
            
            context = self.format_conversation_history(
                conversations=conversations,
                max_length=max_length
            )
            
            if context:
                logger.debug(f"Generated conversation context for thread {thread_id}: {len(context)} chars")
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to get conversation context for thread {thread_id}: {e}")
            # Return empty context on error to prevent breaking agent execution
            return ""

    async def enhance_system_message(
        self,
        original_message: str,
        thread_id: str,
        max_conversations: int = 5,
        max_length: Optional[int] = 2000,
        prepend: bool = False
    ) -> str:
        """
        Enhance a system message with conversation context.
        
        Args:
            original_message: The original system message
            thread_id: Thread identifier for conversation history
            max_conversations: Maximum number of conversations to include
            max_length: Maximum length of conversation context
            prepend: If True, prepend context to message; otherwise append
            
        Returns:
            Enhanced system message with conversation context
        """
        context = await self.get_conversation_context(
            thread_id=thread_id,
            max_conversations=max_conversations,
            max_length=max_length
        )
        
        if not context:
            return original_message
            
        # Add context to system message
        if prepend:
            enhanced_message = f"{context}\n\n{original_message}"
        else:
            enhanced_message = f"{original_message}\n\n{context}"
            
        return enhanced_message

    async def store_conversation_entry(
        self,
        thread_id: str,
        user_message: str,
        assistant_response: str,
        metadata: Optional[dict] = None
    ) -> None:
        """
        Store a new conversation entry.
        
        Args:
            thread_id: Thread identifier
            user_message: User's message/question
            assistant_response: Agent's response
            metadata: Optional metadata
        """
        try:
            store = self._get_store()
            await store.store_conversation(
                thread_id=thread_id,
                user_message=user_message,
                assistant_response=assistant_response,
                metadata=metadata
            )
            logger.debug(f"Stored conversation entry for thread {thread_id}")
            
        except Exception as e:
            logger.error(f"Failed to store conversation entry for thread {thread_id}: {e}")
            # Don't raise exception as this shouldn't break agent execution


def create_context_enhancer(store: Optional[ConversationStore] = None) -> ConversationContextEnhancer:
    """
    Create a conversation context enhancer instance.
    
    Args:
        store: Optional ConversationStore instance
        
    Returns:
        ConversationContextEnhancer instance
    """
    return ConversationContextEnhancer(store)


# Global instance for convenience
_global_enhancer: Optional[ConversationContextEnhancer] = None


def get_context_enhancer() -> ConversationContextEnhancer:
    """
    Get the global context enhancer instance.
    
    Returns:
        ConversationContextEnhancer instance
    """
    global _global_enhancer
    if _global_enhancer is None:
        _global_enhancer = ConversationContextEnhancer()
    return _global_enhancer