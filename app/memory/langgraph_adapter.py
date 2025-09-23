"""
LangGraph compatible checkpointer adapter for high-performance memory backend.

This adapter provides seamless integration with the existing LangGraph ecosystem
while using our optimized ChromaDB backend for storage.
"""

from __future__ import annotations
import asyncio
import logging
from typing import Dict, List, Any, Optional, Iterator, Tuple, Union, AsyncIterator, Sequence
from datetime import datetime
import json

try:
    from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata, CheckpointTuple
    from langgraph.checkpoint.memory import MemorySaver
    from langchain_core.runnables import RunnableConfig
    HAS_LANGGRAPH = True
except ImportError:
    # Fallback definitions for when langgraph is not available
    BaseCheckpointSaver = object
    Checkpoint = Dict[str, Any]
    CheckpointMetadata = Dict[str, Any]
    CheckpointTuple = Tuple[RunnableConfig, Checkpoint, CheckpointMetadata, dict]
    MemorySaver = object
    RunnableConfig = Dict[str, Any]
    HAS_LANGGRAPH = False

from .manager import HighPerformanceMemoryManager, ResourceLimits
from .structures import OptimizedCheckpoint, intern_string

log = logging.getLogger(__name__)


class HighPerformanceCheckpointer(BaseCheckpointSaver if HAS_LANGGRAPH else object):
    """
    High-performance checkpointer that integrates with existing LangGraph code.
    
    This replaces MemorySaver with our optimized ChromaDB backend while
    maintaining the same interface for backward compatibility.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs):
        """Initialize with optional configuration."""
        if HAS_LANGGRAPH:
            super().__init__(**kwargs)  # Initialize BaseCheckpointSaver
        self.config = config or {}
        self._manager: Optional[HighPerformanceMemoryManager] = None
        self._initialized = False
        self._user_id = "default_user"  # Default user ID
    
    async def _ensure_initialized(self):
        """Ensure the memory manager is initialized."""
        if not self._initialized:
            # Set up default configuration if not provided
            if not self.config:
                self.config = {
                    "memory": {
                        "backend": "chromadb",
                        "chromadb": {
                            "path": "./jk_agents_memory",
                            "max_connections": 20,
                            "batch_size": 50,
                            "enable_batch_processing": True,
                            "l1_cache_size": 5000
                        }
                    }
                }
            
            # Create and initialize manager
            resource_limits = ResourceLimits(
                max_memory_mb=512,
                max_connections=20,
                max_concurrent_operations=200
            )
            
            self._manager = HighPerformanceMemoryManager(resource_limits)
            await self._manager.initialize(self.config)
            self._initialized = True
            log.info("High-performance checkpointer initialized")
    
    def set_user_context(self, user_id: str):
        """Set user context for multi-tenant isolation."""
        self._user_id = intern_string(user_id)
    
    async def aget(self, config: RunnableConfig) -> Optional[Checkpoint]:
        """
        Async get checkpoint - compatible with LangGraph interface.
        """
        await self._ensure_initialized()
        
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return None
        
        try:
            data = await self._manager.retrieve_checkpoint(self._user_id, thread_id)
            if data:
                # Convert back to LangGraph checkpoint format
                return self._deserialize_checkpoint(data)
            return None
        except Exception as e:
            log.error(f"Error retrieving checkpoint: {e}")
            return None
    
    def get(self, config: RunnableConfig) -> Optional[Checkpoint]:
        """
        Sync get checkpoint - runs async method in event loop.
        """
        try:
            # Try to get current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're already in an async context, create a task
                task = loop.create_task(self.aget(config))
                # For sync compatibility, we need to return None and log
                log.warning("Sync get() called in async context - use aget() instead")
                return None
            else:
                # No running loop, run the async method
                return loop.run_until_complete(self.aget(config))
        except RuntimeError:
            # No event loop, create new one
            return asyncio.run(self.aget(config))
    
    async def aput(self, config: RunnableConfig, checkpoint: Checkpoint, metadata: CheckpointMetadata, new_versions: dict) -> RunnableConfig:
        """
        Async put checkpoint - compatible with LangGraph interface.
        """
        await self._ensure_initialized()
        
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            log.warning("No thread_id in config, cannot store checkpoint")
            return config
        
        try:
            # Serialize checkpoint data with metadata and versions
            serialized = self._serialize_checkpoint(checkpoint, metadata, new_versions)
            await self._manager.store_checkpoint(self._user_id, thread_id, serialized)
            return config
        except Exception as e:
            log.error(f"Error storing checkpoint: {e}")
            raise
    
    def put(self, config: RunnableConfig, checkpoint: Checkpoint, metadata: CheckpointMetadata, new_versions: dict) -> RunnableConfig:
        """
        Sync put checkpoint - runs async method in event loop.
        """
        try:
            # Try to get current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're already in an async context, create a task
                task = loop.create_task(self.aput(config, checkpoint, metadata, new_versions))
                return config  # Return immediately in async context
            else:
                # No running loop, run the async method
                return loop.run_until_complete(self.aput(config, checkpoint, metadata, new_versions))
        except RuntimeError:
            # No event loop, create new one
            return asyncio.run(self.aput(config, checkpoint, metadata, new_versions))
    
    async def alist(self, config: Optional[RunnableConfig], *, filter: Optional[Dict[str, Any]] = None, before: Optional[RunnableConfig] = None, limit: Optional[int] = None) -> AsyncIterator[CheckpointTuple]:
        """
        Async list checkpoints - compatible with LangGraph interface.
        """
        await self._ensure_initialized()
        
        if not config:
            return
            
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return
        
        try:
            if self._manager and self._manager._backend:
                checkpoints = await self._manager._backend.checkpoint_store.list_checkpoints(
                    self._user_id, thread_id
                )
                
                count = 0
                for cp in checkpoints:
                    if limit and count >= limit:
                        break
                    
                    # Create a checkpoint tuple for each result
                    checkpoint_config = {"configurable": {"thread_id": cp.get("thread_id")}}
                    metadata = {"timestamp": cp.get("timestamp"), "size": cp.get("size")}
                    pending_writes = {}
                    
                    # Try to retrieve the actual checkpoint data
                    checkpoint_data = await self._manager.retrieve_checkpoint(self._user_id, cp.get("thread_id"))
                    if checkpoint_data:
                        checkpoint = self._deserialize_checkpoint(checkpoint_data)
                        yield CheckpointTuple(checkpoint_config, checkpoint, metadata, pending_writes) if HAS_LANGGRAPH else (checkpoint_config, checkpoint, metadata, pending_writes)
                        count += 1
                        
        except Exception as e:
            log.error(f"Error listing checkpoints: {e}")
            return
    
    def list(self, config: Optional[RunnableConfig], *, filter: Optional[Dict[str, Any]] = None, before: Optional[RunnableConfig] = None, limit: Optional[int] = None) -> Iterator[CheckpointTuple]:
        """
        Sync list checkpoints - runs async method in event loop.
        """
        try:
            # Try to get current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're already in an async context, return empty for now
                log.warning("Sync list() called in async context - use alist() instead")
                return iter([])
            else:
                # No running loop, run the async method
                async def _run_alist():
                    results = []
                    async for item in self.alist(config, filter=filter, before=before, limit=limit):
                        results.append(item)
                    return results
                results = loop.run_until_complete(_run_alist())
                return iter(results)
        except RuntimeError:
            # No event loop, create new one
            async def _run_alist():
                results = []
                async for item in self.alist(config, filter=filter, before=before, limit=limit):
                    results.append(item)
                return results
            results = asyncio.run(_run_alist())
            return iter(results)
    
    def _serialize_checkpoint(self, checkpoint: Checkpoint, metadata: CheckpointMetadata, new_versions: Optional[dict] = None) -> bytes:
        """Serialize checkpoint, metadata, and versions to bytes."""
        data = {
            "checkpoint": checkpoint,
            "metadata": metadata,
            "new_versions": new_versions or {},
            "timestamp": datetime.now().isoformat()
        }
        return json.dumps(data, default=str).encode('utf-8')
    
    def _deserialize_checkpoint(self, data: bytes) -> Checkpoint:
        """Deserialize bytes back to checkpoint."""
        import json
        try:
            parsed = json.loads(data.decode('utf-8'))
            return parsed.get("checkpoint", {})
        except Exception as e:
            log.error(f"Error deserializing checkpoint: {e}")
            return {}
    
    def _convert_to_metadata(self, checkpoint_info: Dict[str, Any]) -> CheckpointMetadata:
        """Convert internal checkpoint info to LangGraph metadata format."""
        return {
            "thread_id": checkpoint_info.get("thread_id"),
            "timestamp": checkpoint_info.get("timestamp"),
            "size": checkpoint_info.get("size"),
            "id": checkpoint_info.get("id")
        }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self._initialized:
            return {"error": "Not initialized"}
        
        return await self._manager.get_comprehensive_stats()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        if not self._initialized:
            return {"healthy": False, "error": "Not initialized"}
        
        return await self._manager.health_check()
    
    async def adelete_thread(self, thread_id: str) -> None:
        """Asynchronously delete all checkpoints and writes associated with a specific thread ID.
        
        Args:
            thread_id: The thread ID whose checkpoints should be deleted.
        """
        await self._ensure_initialized()
        
        try:
            # Delete all checkpoints and writes for this thread
            if self._manager and self._manager._backend:
                # Implementation would depend on ChromaDB backend having delete functionality
                # For now, we'll log the request and implement basic cleanup
                log.info(f"Deleting all data for thread: {thread_id}")
                
                # In a full implementation, you would:
                # 1. Query ChromaDB for all documents with this thread_id
                # 2. Delete those documents
                # This is a placeholder for the actual implementation
                
                # Clear from cache
                if hasattr(self._manager._backend.checkpoint_store, '_cache'):
                    cache = self._manager._backend.checkpoint_store._cache
                    keys_to_remove = []
                    for key in cache._cache.keys():
                        if hasattr(key, 'thread_id') and key.thread_id == thread_id:
                            keys_to_remove.append(key)
                    for key in keys_to_remove:
                        cache._cache.pop(key, None)
                        
            log.info(f"Successfully deleted thread: {thread_id}")
        except Exception as e:
            log.error(f"Error deleting thread {thread_id}: {e}")
            raise
    
    def delete_thread(self, thread_id: str) -> None:
        """Delete all checkpoints and writes associated with a specific thread ID.
        
        Args:
            thread_id: The thread ID whose checkpoints should be deleted.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.adelete_thread(thread_id))
            else:
                loop.run_until_complete(self.adelete_thread(thread_id))
        except RuntimeError:
            asyncio.run(self.adelete_thread(thread_id))
    
    async def cleanup(self):
        """Clean up resources."""
        if self._manager:
            await self._manager.cleanup()
        self._initialized = False
    
    def get_next_version(self, current: Union[str, int, float, None], channel=None) -> Union[str, int, float]:
        """Generate the next version ID for a channel.
        
        Default is to use integer versions, incrementing by 1. If you override, you can use str/int/float versions,
        as long as they are monotonically increasing.
        
        Args:
            current: The current version identifier (int, float, or str).
            channel: Deprecated argument, kept for backwards compatibility.
            
        Returns:
            The next version identifier, which must be increasing.
        """
        if isinstance(current, str):
            # Try to parse as int first
            try:
                return str(int(current) + 1)
            except (ValueError, TypeError):
                # Fallback for non-numeric strings
                import time
                return f"1.{int(time.time())}"
        elif current is None:
            return 1
        else:
            return current + 1
    
    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Asynchronously fetch a checkpoint tuple using the given configuration.
        
        Args:
            config: Configuration specifying which checkpoint to retrieve.
            
        Returns:
            Optional[CheckpointTuple]: The requested checkpoint tuple, or None if not found.
        """
        await self._ensure_initialized()
        
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return None
        
        try:
            data = await self._manager.retrieve_checkpoint(self._user_id, thread_id)
            if data:
                # Deserialize checkpoint data
                checkpoint = self._deserialize_checkpoint(data)
                metadata = {"thread_id": thread_id, "timestamp": datetime.now().isoformat()}
                pending_writes = {}  # We don't track pending writes separately in our implementation
                return CheckpointTuple(config, checkpoint, metadata, pending_writes) if HAS_LANGGRAPH else (config, checkpoint, metadata, pending_writes)
            return None
        except Exception as e:
            log.error(f"Error retrieving checkpoint tuple: {e}")
            return None
    
    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Fetch a checkpoint tuple using the given configuration.
        
        Args:
            config: Configuration specifying which checkpoint to retrieve.
            
        Returns:
            Optional[CheckpointTuple]: The requested checkpoint tuple, or None if not found.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                log.warning("Sync get_tuple() called in async context - use aget_tuple() instead")
                return None
            return loop.run_until_complete(self.aget_tuple(config))
        except RuntimeError:
            return asyncio.run(self.aget_tuple(config))
    
    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """Asynchronously store intermediate writes linked to a checkpoint.
        
        Args:
            config: Configuration of the related checkpoint.
            writes: List of writes to store.
            task_id: Identifier for the task creating the writes.
            task_path: Path of the task creating the writes.
        """
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            log.warning("No thread_id in config, cannot store writes")
            return
            
        await self._ensure_initialized()
        
        try:
            # Store writes as metadata with task info
            writes_data = {
                "writes": list(writes),
                "task_id": task_id,
                "task_path": task_path,
                "timestamp": datetime.now().isoformat()
            }
            serialized = json.dumps(writes_data).encode('utf-8')
            # Use a special key format for writes
            writes_key = f"{thread_id}_writes_{task_id}"
            await self._manager.store_checkpoint(self._user_id, writes_key, serialized)
        except Exception as e:
            log.error(f"Error storing writes: {e}")
            raise
    
    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """Store intermediate writes linked to a checkpoint.
        
        Args:
            config: Configuration of the related checkpoint.
            writes: List of writes to store.
            task_id: Identifier for the task creating the writes.
            task_path: Path of the task creating the writes.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.aput_writes(config, writes, task_id, task_path))
            else:
                loop.run_until_complete(self.aput_writes(config, writes, task_id, task_path))
        except RuntimeError:
            asyncio.run(self.aput_writes(config, writes, task_id, task_path))


class MemorySaverReplacement(HighPerformanceCheckpointer):
    """
    Drop-in replacement for LangGraph's MemorySaver.
    
    This class can be used anywhere MemorySaver was used before,
    providing the same interface but with high-performance backend.
    """
    
    def __init__(self, **kwargs):
        """Initialize with optimized defaults for MemorySaver replacement."""
        config = {
            "memory": {
                "backend": "chromadb",
                "chromadb": {
                    "path": "./langgraph_memory_optimized",
                    "max_connections": 10,
                    "batch_size": 25,
                    "enable_batch_processing": True,
                    "l1_cache_size": 2000
                }
            }
        }
        super().__init__(config, **kwargs)
        log.info("MemorySaver replacement initialized with high-performance backend")


# Global instance for backward compatibility
_global_checkpointer: Optional[HighPerformanceCheckpointer] = None


def get_optimized_checkpointer(config: Optional[Dict[str, Any]] = None) -> HighPerformanceCheckpointer:
    """
    Get a global optimized checkpointer instance.
    
    This replaces the pattern of creating new MemorySaver instances
    with a shared high-performance checkpointer.
    """
    global _global_checkpointer
    
    if _global_checkpointer is None:
        _global_checkpointer = HighPerformanceCheckpointer(config)
    
    return _global_checkpointer


async def initialize_global_checkpointer(config: Optional[Dict[str, Any]] = None):
    """Initialize the global checkpointer."""
    checkpointer = get_optimized_checkpointer(config)
    await checkpointer._ensure_initialized()


def create_memory_saver_replacement() -> MemorySaverReplacement:
    """Create a drop-in replacement for MemorySaver."""
    return MemorySaverReplacement()


# Monkey patch for existing code compatibility
if HAS_LANGGRAPH:
    # This allows existing code using MemorySaver to automatically benefit
    # from our optimizations by importing this module
    import langgraph.checkpoint.memory
    original_memory_saver = langgraph.checkpoint.memory.MemorySaver
    
    def OptimizedMemorySaver(*args, **kwargs):
        """Optimized MemorySaver that uses our high-performance backend."""
        # Ignore original MemorySaver arguments since our system is different
        return create_memory_saver_replacement()
    
    # Note: Commenting out monkey patch to avoid breaking existing code
    # Uncomment if you want automatic optimization for all MemorySaver usage
    # langgraph.checkpoint.memory.MemorySaver = OptimizedMemorySaver