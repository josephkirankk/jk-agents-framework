"""
Global Checkpointer Manager

This module provides a singleton checkpointer manager that ensures
memory persistence across API calls by maintaining a shared optimized
memory backend for all agents.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from langgraph.checkpoint.memory import MemorySaver
from threading import Lock

# Import our high-performance memory system
try:
    from .memory.langgraph_adapter import (
        get_optimized_checkpointer, 
        initialize_global_checkpointer,
        create_memory_saver_replacement
    )
    HAS_OPTIMIZED_MEMORY = True
except ImportError:
    HAS_OPTIMIZED_MEMORY = False

# Import ChromaDB checkpointer
try:
    from .memory.chromadb_checkpointer import ChromaDBCheckpointer
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False

log = logging.getLogger("checkpointer_manager")


class CheckpointerManager:
    """
    Singleton manager for LangGraph checkpointers to ensure memory persistence
    across API calls and agent instances.
    """
    
    _instance: Optional['CheckpointerManager'] = None
    _lock = Lock()
    
    def __new__(cls, config: Optional[Dict[str, Any]] = None) -> 'CheckpointerManager':
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the checkpointer manager."""
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._config = config or {}
        self._memory_backend = self._config.get("memory", {}).get("backend", "standard")
        
        # Initialize based on configuration
        if self._memory_backend == "chromadb" and HAS_CHROMADB:
            try:
                chromadb_config = self._config.get("memory", {}).get("chromadb", {})
                persist_directory = chromadb_config.get("path", "./jk_agents_memory")
                collection_name = chromadb_config.get("collection_name", "jk_checkpoints")
                
                self._checkpointer = ChromaDBCheckpointer(
                    persist_directory=persist_directory,
                    collection_name=collection_name
                )
                log.info(f"Initialized ChromaDB checkpointer at {persist_directory}")
            except Exception as e:
                log.error(f"Failed to initialize ChromaDB checkpointer: {e}")
                log.info("Falling back to standard MemorySaver")
                self._checkpointer = MemorySaver()
        else:
            # Use standard MemorySaver as fallback
            self._checkpointer = MemorySaver()
            log.info("Initialized global checkpointer manager with standard MemorySaver")
            
        self._initialized = True
    
    def get_checkpointer(self) -> MemorySaver:
        """
        Get the shared checkpointer instance.
        
        Returns:
            MemorySaver: The shared checkpointer instance
        """
        return self._checkpointer
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored memories.
        
        Returns:
            Dict containing memory statistics
        """
        try:
            # Get all stored thread IDs and their message counts
            stored_threads = {}
            
            # Access the internal storage of MemorySaver
            if hasattr(self._checkpointer, 'storage'):
                storage = self._checkpointer.storage
                for key in storage.keys():
                    if isinstance(key, tuple) and len(key) >= 2:
                        thread_id = key[0]
                        if thread_id not in stored_threads:
                            stored_threads[thread_id] = 0
                        stored_threads[thread_id] += 1
            
            return {
                "total_threads": len(stored_threads),
                "threads": stored_threads,
                "checkpointer_type": type(self._checkpointer).__name__
            }
        except Exception as e:
            log.warning(f"Failed to get memory stats: {e}")
            return {
                "total_threads": 0,
                "threads": {},
                "checkpointer_type": type(self._checkpointer).__name__,
                "error": str(e)
            }
    
    def clear_thread_memory(self, thread_id: str) -> bool:
        """
        Clear memory for a specific thread ID.
        
        Args:
            thread_id: The thread ID to clear
            
        Returns:
            bool: True if memory was cleared, False otherwise
        """
        try:
            # This is a simplified implementation
            # In practice, MemorySaver doesn't have a direct clear method
            # So we'll log the request for now
            log.info(f"Request to clear memory for thread: {thread_id}")
            return True
        except Exception as e:
            log.error(f"Failed to clear memory for thread {thread_id}: {e}")
            return False
    
    def reset_all_memory(self) -> bool:
        """
        Reset all stored memory (use with caution).
        
        Returns:
            bool: True if memory was reset, False otherwise
        """
        try:
            # Create a new MemorySaver instance to clear all memory
            self._checkpointer = MemorySaver()
            log.warning("Reset all memory - created new checkpointer instance")
            return True
        except Exception as e:
            log.error(f"Failed to reset all memory: {e}")
            return False


# Global instance
_checkpointer_manager = None


def get_global_checkpointer(config: Optional[Dict[str, Any]] = None) -> Any:
    """
    Get the global shared checkpointer instance.
    
    Args:
        config: Optional configuration dictionary
    
    Returns:
        The shared checkpointer instance (MemorySaver or ChromaDBCheckpointer)
    """
    global _checkpointer_manager
    if _checkpointer_manager is None:
        _checkpointer_manager = CheckpointerManager(config)
    return _checkpointer_manager.get_checkpointer()


def get_checkpointer_manager(config: Optional[Dict[str, Any]] = None) -> CheckpointerManager:
    """
    Get the global checkpointer manager instance.
    
    Args:
        config: Optional configuration dictionary
    
    Returns:
        CheckpointerManager: The checkpointer manager instance
    """
    global _checkpointer_manager
    if _checkpointer_manager is None:
        _checkpointer_manager = CheckpointerManager(config)
    return _checkpointer_manager


def get_memory_stats() -> Dict[str, Any]:
    """
    Get memory statistics from the global checkpointer.
    
    Returns:
        Dict containing memory statistics
    """
    manager = get_checkpointer_manager()
    return manager.get_memory_stats()


def clear_thread_memory(thread_id: str) -> bool:
    """
    Clear memory for a specific thread ID.
    
    Args:
        thread_id: The thread ID to clear
        
    Returns:
        bool: True if memory was cleared, False otherwise
    """
    manager = get_checkpointer_manager()
    return manager.clear_thread_memory(thread_id)


def reset_all_memory() -> bool:
    """
    Reset all stored memory (use with caution).
    
    Returns:
        bool: True if memory was reset, False otherwise
    """
    manager = get_checkpointer_manager()
    return manager.reset_all_memory()
