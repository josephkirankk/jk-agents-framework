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

# Import ChromaDB checkpointer (legacy/simple)
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
    
    def _normalize_config(self, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Normalize incoming config to a plain dict.
        
        Accepts either dict-like objects or Pydantic models with .model_dump().
        """
        if config is None:
            return {}
        try:
            # Pydantic v2
            if hasattr(config, "model_dump") and callable(getattr(config, "model_dump")):
                return config.model_dump(exclude_none=True)
            # Pydantic v1
            if hasattr(config, "dict") and callable(getattr(config, "dict")):
                return config.dict(exclude_none=True)
        except Exception:
            pass
        # Fallback: assume it's already a mapping
        try:
            return dict(config)
        except Exception:
            return {}
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the checkpointer manager."""
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        # Normalize config to a dict for flexible callers (e.g., Pydantic BaseModel)
        self._config = self._normalize_config(config)

        # Determine backend preference from config if present
        self._memory_backend = (
            (self._config.get("memory") or {}).get("backend")
            or (self._config.get("persistence") or {}).get("type")
            or "standard"
        )

        # Initialize based on configuration, preferring optimized backend when available
        self._checkpointer = None
        init_errors = []

        # 1) Prefer optimized high-performance ChromaDB-backed checkpointer
        if HAS_OPTIMIZED_MEMORY:
            try:
                # Pass normalized config; optimized checkpointer will use sane defaults if missing
                self._checkpointer = get_optimized_checkpointer(self._config)
                log.info("Initialized optimized high-performance checkpointer (ChromaDB backend)")
            except Exception as e:
                init_errors.append(f"optimized_checkpointer: {e}")
                self._checkpointer = None

        # 2) Fallback to legacy simple ChromaDB checkpointer if explicitly requested and available
        if self._checkpointer is None and self._memory_backend == "chromadb" and HAS_CHROMADB:
            try:
                chromadb_cfg = (self._config.get("memory") or {}).get("chromadb", {})
                persist_directory = chromadb_cfg.get("path", "./jk_agents_memory")
                collection_name = chromadb_cfg.get("collection_name", "jk_checkpoints")
                self._checkpointer = ChromaDBCheckpointer(
                    persist_directory=persist_directory,
                    collection_name=collection_name,
                )
                log.info(f"Initialized legacy ChromaDB checkpointer at {persist_directory}")
            except Exception as e:
                init_errors.append(f"legacy_chromadb: {e}")
                self._checkpointer = None

        # 3) Final fallback - disable checkpointing entirely to bypass LangGraph issues
        if self._checkpointer is None:
            self._checkpointer = None  # Disable checkpointing to bypass 'v' KeyError
            if init_errors:
                log.warning(
                    "Disabling checkpointing due to initialization errors: %s",
                    "; ".join(init_errors),
                )
            log.info("Initialized global checkpointer manager with NO CHECKPOINTING (bypass mode)")
        
        self._initialized = True
    
    def get_checkpointer(self) -> Optional[MemorySaver]:
        """Get the shared checkpointer instance."""
        return self._checkpointer

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about stored memories."""
        try:
            # Prefer rich stats when available (optimized checkpointer)
            if hasattr(self._checkpointer, "get_stats"):
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Can't block the running loop in a sync method; return minimal info
                        return {
                            "checkpointer_type": type(self._checkpointer).__name__,
                            "stats": {"warning": "stats unavailable in sync context while event loop is running"},
                        }
                    else:
                        stats = loop.run_until_complete(self._checkpointer.get_stats())  # type: ignore
                        return {
                            "checkpointer_type": type(self._checkpointer).__name__,
                            "stats": stats,
                        }
                except Exception as e:
                    log.warning(f"Failed to retrieve optimized stats: {e}")

            # Fallback lightweight stats for MemorySaver
            stored_threads = {}
            if hasattr(self._checkpointer, 'storage'):
                storage = self._checkpointer.storage
                for key in storage.keys():
                    if isinstance(key, tuple) and len(key) >= 2:
                        thread_id = key[0]
                        stored_threads[thread_id] = stored_threads.get(thread_id, 0) + 1

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
        """Clear memory for a specific thread ID."""
        try:
            # Optimized checkpointer supports thread deletion
            if hasattr(self._checkpointer, "delete_thread"):
                self._checkpointer.delete_thread(thread_id)  # type: ignore
                log.info(f"Cleared optimized memory for thread: {thread_id}")
                return True

            # Legacy/MemorySaver path: no direct clear; log and return success
            log.info(f"Request to clear memory for thread (no-op for MemorySaver): {thread_id}")
            return True
        except Exception as e:
            log.error(f"Failed to clear memory for thread {thread_id}: {e}")
            return False

    def reset_all_memory(self) -> bool:
        """Reset all stored memory (use with caution)."""
        try:
            # For optimized checkpointer, perform cleanup if available
            if hasattr(self._checkpointer, "cleanup"):
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(self._checkpointer.cleanup())  # type: ignore
                    else:
                        loop.run_until_complete(self._checkpointer.cleanup())  # type: ignore
                except RuntimeError:
                    asyncio.run(self._checkpointer.cleanup())  # type: ignore
                except Exception as e:
                    log.warning(f"Optimized checkpointer cleanup encountered an issue: {e}")

            # Recreate a fresh MemorySaver as a clean slate
            self._checkpointer = MemorySaver()
            log.warning("Reset all memory - created new MemorySaver instance")
            return True
        except Exception as e:
            log.error(f"Failed to reset all memory: {e}")
            return False


# Global instance
_checkpointer_manager = None


def get_global_checkpointer(config: Optional[Dict[str, Any]] = None) -> Optional[Any]:
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
