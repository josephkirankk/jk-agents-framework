"""
Thread ID utilities for conversation tracking.

This module provides functions for generating and managing thread IDs.
"""

import uuid
import logging
from typing import Dict, Optional

log = logging.getLogger("thread_id_utils")

# Global cache of thread mappings
_thread_cache: Dict[str, str] = {}

def generate_thread_id() -> str:
    """Generate a new thread ID."""
    return str(uuid.uuid4())

def get_or_create_thread_id(thread_id: Optional[str] = None) -> str:
    """Get an existing thread ID or create a new one if not provided."""
    if thread_id:
        return thread_id
    return generate_thread_id()

def create_supervisor_thread_id(base_thread_id: str) -> str:
    """Create a supervisor-specific thread ID from a base thread ID."""
    supervisor_thread_id = f"{base_thread_id}-supervisor"
    log.debug(f"Created supervisor thread ID: {supervisor_thread_id} from base: {base_thread_id}")
    return supervisor_thread_id

def map_thread_ids(external_id: str, internal_id: str) -> None:
    """Map an external thread ID to an internal thread ID."""
    _thread_cache[external_id] = internal_id
    log.debug(f"Mapped external ID {external_id} to internal ID {internal_id}")

def get_internal_thread_id(external_id: str) -> Optional[str]:
    """Get the internal thread ID for an external ID."""
    return _thread_cache.get(external_id)

def clear_thread_mapping(external_id: str) -> bool:
    """Clear a thread ID mapping."""
    if external_id in _thread_cache:
        del _thread_cache[external_id]
        log.debug(f"Cleared thread mapping for {external_id}")
        return True
    return False
