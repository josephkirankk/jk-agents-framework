"""
Memory integration module for conversation context management.

This module provides functions for initializing and interacting with the conversation
memory system, including storing, retrieving, and enhancing messages with context.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union, Tuple

from .types import AppConfig

log = logging.getLogger("memory_integration")

# In-memory storage for simple conversations
_conversations: Dict[str, List[Dict[str, Any]]] = {}

async def initialize_conversation_memory(app_cfg: AppConfig) -> bool:
    """
    Initialize the conversation memory system based on configuration.
    
    Args:
        app_cfg: Application configuration with memory settings
        
    Returns:
        True if memory system was initialized successfully
    """
    try:
        if not is_conversation_memory_enabled(app_cfg):
            log.info("Conversation memory not enabled in configuration")
            return False
        
        log.info("Initializing conversation memory system")
        # For now, we're using in-memory storage which doesn't need initialization
        # In the future, this could initialize database connections, etc.
        return True
    except Exception as e:
        log.error(f"Failed to initialize conversation memory: {e}")
        return False

def is_conversation_memory_enabled(app_cfg: AppConfig) -> bool:
    """
    Check if conversation memory is enabled in configuration.
    
    Args:
        app_cfg: Application configuration
        
    Returns:
        True if conversation memory is enabled
    """
    return (
        app_cfg is not None and
        hasattr(app_cfg, "conversation_memory") and
        getattr(app_cfg.conversation_memory, "enabled", False)
    )

def enhance_system_message_with_memory(
    system_message: str, 
    thread_id: str,
    prepend: bool = True
) -> str:
    """
    Enhance system message with conversation memory.
    
    Args:
        system_message: Original system message
        thread_id: Conversation thread ID
        prepend: Whether to prepend memory to system message (True) or append it
        
    Returns:
        Enhanced system message with conversation context
    """
    context = get_conversation_context(thread_id)
    if not context:
        return system_message
    
    if prepend:
        return f"{context}\n\n{system_message}"
    else:
        return f"{system_message}\n\n{context}"

def get_conversation_context(thread_id: str) -> str:
    """
    Get conversation context for a thread.
    
    Args:
        thread_id: Conversation thread ID
        
    Returns:
        Formatted conversation context
    """
    if thread_id not in _conversations:
        return ""
    
    messages = _conversations[thread_id]
    if not messages:
        return ""
    
    # Build context string
    context = "Previous conversation context:\n"
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        context += f"[{role}]: {content}\n"
    
    return context

async def store_conversation_memory(
    thread_id: str,
    messages: List[Dict[str, Any]]
) -> bool:
    """
    Store conversation messages in memory.
    
    Args:
        thread_id: Conversation thread ID
        messages: List of messages to store
        
    Returns:
        True if storage was successful
    """
    try:
        if thread_id not in _conversations:
            _conversations[thread_id] = []
        
        # Store only the latest message
        if messages and len(messages) > 0:
            _conversations[thread_id].extend(messages)
            log.info(f"Stored {len(messages)} message(s) for thread {thread_id}")
            
        return True
    except Exception as e:
        log.error(f"Failed to store conversation memory: {e}")
        return False

async def store_conversation_turn(
    thread_id: str,
    user_input: str,
    assistant_response: str
) -> bool:
    """
    Store a complete conversation turn (user input + assistant response).
    
    Args:
        thread_id: Conversation thread ID
        user_input: User input message
        assistant_response: Assistant's response
        
    Returns:
        True if storage was successful
    """
    messages = [
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": assistant_response}
    ]
    return await store_conversation_memory(thread_id, messages)

def inject_conversation_context(
    thread_id: str,
    user_input: str
) -> str:
    """
    Inject conversation context into user input.
    
    Args:
        thread_id: Conversation thread ID
        user_input: Original user input
        
    Returns:
        Enhanced user input with conversation context
    """
    context = get_conversation_context(thread_id)
    if not context:
        return user_input
    
    return f"{context}\n\nCurrent user input: {user_input}"
