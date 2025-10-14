"""
Memory integration module for JK-Agents Framework.

This module provides functions to initialize conversation memory and integrate
it with existing API endpoints for seamless conversation context injection.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional, Dict, Any

from ..config import AppConfig
from .conversation_store import initialize_conversation_store, get_conversation_store
from .context_enhancer import get_context_enhancer
from .transaction_logger import get_memory_logger


logger = logging.getLogger(__name__)


async def initialize_conversation_memory(app_config: AppConfig) -> bool:
    """
    Initialize conversation memory system based on app configuration.
    
    Args:
        app_config: Application configuration
        
    Returns:
        True if successfully initialized, False otherwise
    """
    if not app_config.conversation_memory.enabled:
        logger.info("Conversation memory disabled in configuration")
        return False
    
    # Get database URL from config or environment
    database_url = app_config.conversation_memory.database_url
    if not database_url:
        database_url = (
            os.getenv('DATABASE_URL') or 
            os.getenv('POSTGRES_URL') or
            os.getenv('POSTGRESQL_URL')
        )
    
    if not database_url:
        logger.warning(
            "Conversation memory enabled but no database URL provided. "
            "Set DATABASE_URL environment variable or conversation_memory.database_url in config."
        )
        return False
    
    try:
        await initialize_conversation_store(
            database_url=database_url,
            pool_size=app_config.conversation_memory.pool_size
        )
        logger.info("Conversation memory initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize conversation memory: {e}")
        return False


async def enhance_system_message_with_memory(
    original_message: str,
    thread_id: str,
    app_config: AppConfig
) -> str:
    """
    Enhance system message with conversation history if memory is enabled.
    
    Args:
        original_message: Original system message
        thread_id: Thread identifier
        app_config: Application configuration
        
    Returns:
        Enhanced system message (or original if memory disabled/failed)
    """
    # Log the enhancement request
    try:
        memory_logger = get_memory_logger()
        from .transaction_logger import prepare_content_for_logging
        
        log_data = {
            'memory_enabled': app_config.conversation_memory.enabled,
            'operation_source': 'memory_integration',
            'max_conversations': app_config.conversation_memory.max_conversations if app_config.conversation_memory.enabled else None,
            'max_context_length': app_config.conversation_memory.max_context_length if app_config.conversation_memory.enabled else None
        }
        
        # Add original message content if logging is configured to include content
        original_content = prepare_content_for_logging(
            original_message, 
            app_config.memory_logging.include_content,
            app_config.memory_logging.max_content_length
        )
        log_data.update({f'original_message_{k}': v for k, v in original_content.items()})
        
        memory_logger.log_transaction(thread_id, 'ENHANCE_SYSTEM_MESSAGE_WITH_MEMORY', log_data)
    except Exception as e:
        logger.warning(f"Failed to log ENHANCE_SYSTEM_MESSAGE_WITH_MEMORY for thread {thread_id}: {e}")
    
    if not app_config.conversation_memory.enabled:
        return original_message
    
    try:
        enhancer = get_context_enhancer()
        enhanced_message = await enhancer.enhance_system_message(
            original_message=original_message,
            thread_id=thread_id,
            max_conversations=app_config.conversation_memory.max_conversations,
            max_length=app_config.conversation_memory.max_context_length,
            prepend=app_config.conversation_memory.prepend_context,
            app_config=app_config
        )
        
        # Log the enhancement result
        try:
            memory_logger = get_memory_logger()
            from .transaction_logger import prepare_content_for_logging
            
            enhancement_log_data = {
                'memory_enabled': True,
                'operation_source': 'memory_integration',
                'operation_result': 'enhancement_completed',
                'enhanced_message_length': len(enhanced_message),
                'enhancement_added': len(enhanced_message) - len(original_message)
            }
            
            # Add enhanced message content if logging is configured to include content
            if app_config.memory_logging.include_content:
                enhanced_content = prepare_content_for_logging(
                    enhanced_message,
                    app_config.memory_logging.include_content,
                    app_config.memory_logging.max_content_length
                )
                enhancement_log_data.update({f'enhanced_message_{k}': v for k, v in enhanced_content.items()})
                
            memory_logger.log_transaction(thread_id, 'ENHANCE_SYSTEM_MESSAGE_COMPLETED', enhancement_log_data)
        except Exception as e:
            logger.warning(f"Failed to log ENHANCE_SYSTEM_MESSAGE_COMPLETED for thread {thread_id}: {e}")
        
        return enhanced_message
    except Exception as e:
        logger.error(f"Failed to enhance system message with memory: {e}")
        return original_message


async def store_conversation_memory(
    thread_id: str,
    user_message: str,
    assistant_response: str,
    app_config: AppConfig,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Store conversation entry in memory if enabled.
    
    Args:
        thread_id: Thread identifier
        user_message: User's message
        assistant_response: Assistant's response
        app_config: Application configuration
        metadata: Optional metadata to store
    """
    # Log the storage request
    try:
        memory_logger = get_memory_logger()
        from .transaction_logger import prepare_content_for_logging
        
        log_data = {
            'memory_enabled': app_config.conversation_memory.enabled,
            'has_metadata': metadata is not None,
            'operation_source': 'memory_integration'
        }
        
        # Add user message content if logging is configured to include content
        user_content = prepare_content_for_logging(
            user_message,
            app_config.memory_logging.include_content,
            app_config.memory_logging.max_content_length
        )
        log_data.update({f'user_message_{k}': v for k, v in user_content.items()})
        
        # Add assistant response content if logging is configured to include content
        assistant_content = prepare_content_for_logging(
            assistant_response,
            app_config.memory_logging.include_content, 
            app_config.memory_logging.max_content_length
        )
        log_data.update({f'assistant_response_{k}': v for k, v in assistant_content.items()})
        
        # Add metadata if present
        if metadata:
            log_data['metadata_keys'] = list(metadata.keys())
            if app_config.memory_logging.include_content:
                log_data['metadata'] = metadata
        
        memory_logger.log_transaction(thread_id, 'STORE_CONVERSATION_MEMORY', log_data)
    except Exception as e:
        logger.warning(f"Failed to log STORE_CONVERSATION_MEMORY for thread {thread_id}: {e}")
    
    if not app_config.conversation_memory.enabled:
        return
    
    try:
        enhancer = get_context_enhancer()
        await enhancer.store_conversation_entry(
            thread_id=thread_id,
            user_message=user_message,
            assistant_response=assistant_response,
            metadata=metadata,
            app_config=app_config
        )
        logger.debug(f"Stored conversation for thread {thread_id}")
    except Exception as e:
        logger.error(f"Failed to store conversation memory: {e}")


async def cleanup_old_conversations(app_config: AppConfig) -> int:
    """
    Clean up old conversations based on configuration.
    
    Args:
        app_config: Application configuration
        
    Returns:
        Number of deleted conversations
    """
    # Log the cleanup operation (no specific thread_id for cleanup)
    try:
        memory_logger = get_memory_logger()
        memory_logger.log_transaction('SYSTEM', 'CLEANUP_OLD_CONVERSATIONS', {
            'memory_enabled': app_config.conversation_memory.enabled,
            'cleanup_days': app_config.conversation_memory.cleanup_days,
            'operation_source': 'memory_integration',
            'operation_type': 'cleanup'
        })
    except Exception as e:
        logger.warning(f"Failed to log CLEANUP_OLD_CONVERSATIONS: {e}")
    
    if not app_config.conversation_memory.enabled or app_config.conversation_memory.cleanup_days <= 0:
        return 0
    
    try:
        store = get_conversation_store()
        deleted_count = await store.cleanup_old_conversations(
            days_to_keep=app_config.conversation_memory.cleanup_days
        )
        logger.info(f"Cleaned up {deleted_count} old conversations")
        return deleted_count
    except Exception as e:
        logger.error(f"Failed to cleanup old conversations: {e}")
        return 0


def is_conversation_memory_enabled(app_config: AppConfig) -> bool:
    """
    Check if conversation memory is enabled and properly configured.
    
    Args:
        app_config: Application configuration
        
    Returns:
        True if conversation memory is enabled and configured
    """
    if not app_config.conversation_memory.enabled:
        return False
    
    # Check if database URL is available
    database_url = app_config.conversation_memory.database_url
    if not database_url:
        database_url = (
            os.getenv('DATABASE_URL') or 
            os.getenv('POSTGRES_URL') or
            os.getenv('POSTGRESQL_URL')
        )
    
    return bool(database_url)