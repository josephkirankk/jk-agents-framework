"""
Thread ID Management Utility

This module provides utilities for managing conversation thread IDs
to enable proper conversation continuity and isolation.
"""

import uuid
import re
from datetime import datetime
from typing import Optional
import logging

log = logging.getLogger("thread_manager")


def generate_unique_thread_id() -> str:
    """
    Generate a unique thread ID for a new conversation.
    
    Returns:
        str: A unique thread ID in the format 'thread-{uuid}'
    """
    unique_id = str(uuid.uuid4())
    thread_id = f"thread-{unique_id}"
    log.debug(f"Generated new thread ID: {thread_id}")
    return thread_id


def generate_timestamped_thread_id() -> str:
    """
    Generate a timestamped thread ID for a new conversation.
    
    Returns:
        str: A timestamped thread ID in the format 'thread-{timestamp}-{short_uuid}'
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_uuid = str(uuid.uuid4())[:8]
    thread_id = f"thread-{timestamp}-{short_uuid}"
    log.debug(f"Generated timestamped thread ID: {thread_id}")
    return thread_id


def validate_thread_id(thread_id: str) -> bool:
    """
    Validate that a thread ID has a proper format.
    
    Args:
        thread_id: The thread ID to validate
        
    Returns:
        bool: True if the thread ID is valid, False otherwise
    """
    if not thread_id or not isinstance(thread_id, str):
        return False
    
    # Allow alphanumeric characters, hyphens, and underscores
    # Length should be reasonable (between 5 and 100 characters)
    pattern = r'^[a-zA-Z0-9_-]{5,100}$'
    is_valid = bool(re.match(pattern, thread_id))
    
    if not is_valid:
        log.warning(f"Invalid thread ID format: {thread_id}")
    
    return is_valid


def get_or_create_thread_id(provided_thread_id: Optional[str] = None) -> str:
    """
    Get the provided thread ID if valid, or create a new one.
    
    Args:
        provided_thread_id: Optional thread ID provided by the client
        
    Returns:
        str: A valid thread ID (either the provided one or a new one)
    """
    if provided_thread_id:
        if validate_thread_id(provided_thread_id):
            log.info(f"Using provided thread ID: {provided_thread_id}")
            return provided_thread_id
        else:
            log.warning(f"Invalid thread ID provided: {provided_thread_id}, generating new one")
    
    # Generate new thread ID
    new_thread_id = generate_unique_thread_id()
    log.info(f"Created new thread ID: {new_thread_id}")
    return new_thread_id


def create_supervisor_thread_id(base_thread_id: str) -> str:
    """
    Create a supervisor-specific thread ID based on the main thread ID.
    
    Args:
        base_thread_id: The main thread ID for the conversation
        
    Returns:
        str: A supervisor-specific thread ID
    """
    supervisor_thread_id = f"{base_thread_id}-supervisor"
    log.debug(f"Created supervisor thread ID: {supervisor_thread_id}")
    return supervisor_thread_id


def create_step_thread_id(base_thread_id: str, step_id: str) -> str:
    """
    Create a step-specific thread ID based on the main thread ID and step ID.
    
    Args:
        base_thread_id: The main thread ID for the conversation
        step_id: The step ID
        
    Returns:
        str: A step-specific thread ID
    """
    step_thread_id = f"{base_thread_id}-step-{step_id}"
    log.debug(f"Created step thread ID: {step_thread_id}")
    return step_thread_id
