"""
Conversation context enhancement for JK-Agents Framework.

This module provides functionality to extract conversation history from storage
and format it for injection into agent system context, enabling conversation memory.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from .conversation_store import ConversationStore, ConversationEntry, get_conversation_store
from .transaction_logger import get_memory_logger


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
        max_length: Optional[int] = 2000,
        app_config = None
    ) -> str:
        """
        Get formatted conversation context for a thread.
        
        Args:
            thread_id: Thread identifier to get history for
            max_conversations: Maximum number of recent conversations to include
            max_length: Optional maximum length of formatted context
            app_config: Optional app configuration for logging settings
            
        Returns:
            Formatted conversation context string
        """
        # Log the context retrieval operation with content if enabled
        try:
            memory_logger = get_memory_logger()
            from .transaction_logger import prepare_content_for_logging
            
            # Get logging settings from app config or use defaults
            include_content = True  # Default to include content
            max_content_length = 1000  # Default limit
            
            if app_config and hasattr(app_config, 'memory_logging'):
                include_content = app_config.memory_logging.include_content
                max_content_length = app_config.memory_logging.max_content_length
            
            log_data = {
                'max_conversations': max_conversations,
                'max_length': max_length,
                'operation_type': 'context_retrieval',
                'operation_source': 'context_enhancer'
            }
            
            memory_logger.log_transaction(thread_id, 'GET_CONVERSATION_CONTEXT', log_data)
        except Exception as e:
            logger.warning(f"Failed to log GET_CONVERSATION_CONTEXT for thread {thread_id}: {e}")
        
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
            
            # Log the retrieved context content if enabled
            try:
                memory_logger = get_memory_logger()
                from .transaction_logger import prepare_content_for_logging
                
                # Get logging settings from app config or use defaults
                include_content = True  # Default to include content
                max_content_length = 1000  # Default limit
                
                if app_config and hasattr(app_config, 'memory_logging'):
                    include_content = app_config.memory_logging.include_content
                    max_content_length = app_config.memory_logging.max_content_length
                
                log_data = {
                    'conversations_retrieved': len(conversations),
                    'operation_source': 'context_enhancer',
                    'operation_result': 'context_retrieved'
                }
                
                # Add context content if logging configuration allows
                if context:
                    context_content = prepare_content_for_logging(context, include_content, max_content_length)
                    log_data.update({f'context_{k}': v for k, v in context_content.items()})
                
                memory_logger.log_transaction(thread_id, 'GET_CONVERSATION_CONTEXT_RESULT', log_data)
            except Exception as e:
                logger.warning(f"Failed to log GET_CONVERSATION_CONTEXT_RESULT for thread {thread_id}: {e}")
            
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
        prepend: bool = False,
        app_config = None
    ) -> str:
        """
        Enhance a system message with conversation context.
        
        Args:
            original_message: The original system message
            thread_id: Thread identifier for conversation history
            max_conversations: Maximum number of conversations to include
            max_length: Maximum length of conversation context
            prepend: If True, prepend context to message; otherwise append
            app_config: Optional app configuration for logging settings
            
        Returns:
            Enhanced system message with conversation context
        """
        # Log the system message enhancement operation
        try:
            memory_logger = get_memory_logger()
            from .transaction_logger import prepare_content_for_logging
            
            # Get logging settings from app config or use defaults
            include_content = True  # Default to include content
            max_content_length = 1000  # Default limit
            
            if app_config and hasattr(app_config, 'memory_logging'):
                include_content = app_config.memory_logging.include_content
                max_content_length = app_config.memory_logging.max_content_length
            
            log_data = {
                'max_conversations': max_conversations,
                'max_length': max_length,
                'prepend': prepend,
                'operation_type': 'message_enhancement',
                'operation_source': 'context_enhancer'
            }
            
            # Add original message content if logging configuration allows
            original_content = prepare_content_for_logging(original_message, include_content, max_content_length)
            log_data.update({f'original_message_{k}': v for k, v in original_content.items()})
            
            memory_logger.log_transaction(thread_id, 'ENHANCE_SYSTEM_MESSAGE', log_data)
        except Exception as e:
            logger.warning(f"Failed to log ENHANCE_SYSTEM_MESSAGE for thread {thread_id}: {e}")
        
        context = await self.get_conversation_context(
            thread_id=thread_id,
            max_conversations=max_conversations,
            max_length=max_length,
            app_config=app_config
        )
        
        if not context:
            return original_message
            
        # Add context to system message
        if prepend:
            enhanced_message = f"{context}\n\n{original_message}"
        else:
            enhanced_message = f"{original_message}\n\n{context}"
        
        # Log the enhanced message result if logging configuration allows
        try:
            memory_logger = get_memory_logger()
            from .transaction_logger import prepare_content_for_logging
            
            # Get logging settings from app config or use defaults
            include_content = True  # Default to include content
            max_content_length = 1000  # Default limit
            
            if app_config and hasattr(app_config, 'memory_logging'):
                include_content = app_config.memory_logging.include_content
                max_content_length = app_config.memory_logging.max_content_length
            
            log_data = {
                'enhancement_added': len(enhanced_message) - len(original_message),
                'operation_source': 'context_enhancer',
                'operation_result': 'message_enhanced'
            }
            
            # Add enhanced message content if logging configuration allows
            enhanced_content = prepare_content_for_logging(enhanced_message, include_content, max_content_length)
            log_data.update({f'enhanced_message_{k}': v for k, v in enhanced_content.items()})
            
            memory_logger.log_transaction(thread_id, 'ENHANCE_SYSTEM_MESSAGE_RESULT', log_data)
        except Exception as e:
            logger.warning(f"Failed to log ENHANCE_SYSTEM_MESSAGE_RESULT for thread {thread_id}: {e}")
            
        return enhanced_message

    async def store_conversation_entry(
        self,
        thread_id: str,
        user_message: str,
        assistant_response: str,
        metadata: Optional[dict] = None,
        app_config = None
    ) -> None:
        """
        Store a new conversation entry.
        
        Args:
            thread_id: Thread identifier
            user_message: User's message/question
            assistant_response: Agent's response
            metadata: Optional metadata
            app_config: Optional app configuration for logging settings
        """
        # Log the storage operation (via context enhancer) with content if enabled
        try:
            memory_logger = get_memory_logger()
            from .transaction_logger import prepare_content_for_logging
            
            # Get logging settings from app config or use defaults
            include_content = True  # Default to include content
            max_content_length = 1000  # Default limit
            
            if app_config and hasattr(app_config, 'memory_logging'):
                include_content = app_config.memory_logging.include_content
                max_content_length = app_config.memory_logging.max_content_length
            
            log_data = {
                'has_metadata': metadata is not None,
                'operation_source': 'context_enhancer'
            }
            
            # Add actual message content if logging configuration allows
            user_content = prepare_content_for_logging(user_message, include_content, max_content_length)
            log_data.update({f'user_message_{k}': v for k, v in user_content.items()})
            
            assistant_content = prepare_content_for_logging(assistant_response, include_content, max_content_length)
            log_data.update({f'assistant_response_{k}': v for k, v in assistant_content.items()})
            
            if metadata and include_content:
                log_data['metadata'] = metadata
            elif metadata:
                log_data['metadata_keys'] = list(metadata.keys())
            
            memory_logger.log_transaction(thread_id, 'STORE_CONVERSATION_ENTRY_VIA_ENHANCER', log_data)
        except Exception as e:
            logger.warning(f"Failed to log STORE_CONVERSATION_ENTRY_VIA_ENHANCER for thread {thread_id}: {e}")
        
        try:
            store = self._get_store()
            await store.store_conversation(
                thread_id=thread_id,
                user_message=user_message,
                assistant_response=assistant_response,
                metadata=metadata,
                app_config=app_config
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