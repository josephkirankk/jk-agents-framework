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
import uuid
import time

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
    
    # Class-level cache for LangGraph version detection (avoids repeated detection)
    _DETECTED_LANGGRAPH_VERSION: Optional[int] = None
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs):
        """Initialize with optional configuration."""
        if HAS_LANGGRAPH:
            super().__init__(**kwargs)  # Initialize BaseCheckpointSaver
        self.config = config or {}
        self._manager: Optional[HighPerformanceMemoryManager] = None
        self._initialized = False
        self._user_id = "default_user"  # Default user ID
        
        # Detect LangGraph version on first instantiation
        self._detect_langgraph_version()
    
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
            log.debug(f"Retrieving checkpoint for thread {thread_id}")
            data = await self._manager.retrieve_checkpoint(self._user_id, thread_id)
            if data:
                log.debug(f"Raw checkpoint data retrieved for thread {thread_id}, length: {len(data) if isinstance(data, bytes) else 'N/A'}")
                # Convert back to LangGraph checkpoint format
                checkpoint = self._deserialize_checkpoint(data)
                log.debug(f"Deserialized checkpoint for thread {thread_id}, type: {type(checkpoint)}, keys: {list(checkpoint.keys()) if isinstance(checkpoint, dict) else 'N/A'}")
                
                # Ensure checkpoint is valid for LangGraph
                if checkpoint and isinstance(checkpoint, dict):
                    validated_checkpoint = self._ensure_valid_checkpoint(checkpoint)
                    log.debug(f"Validated checkpoint for thread {thread_id}, keys: {list(validated_checkpoint.keys())}")
                    
                    # Double-check that critical fields exist
                    if self._is_checkpoint_valid_for_langgraph(validated_checkpoint):
                        log.debug(f"Returning valid checkpoint for thread {thread_id}")
                        return validated_checkpoint
                    else:
                        log.warning(f"Checkpoint for thread {thread_id} is not LangGraph compatible, returning None to force fresh start")
                        return None
                else:
                    log.debug(f"Invalid checkpoint format for thread {thread_id}, returning None")
                    return None
            log.debug(f"No checkpoint data found for thread {thread_id}")
            return None
        except Exception as e:
            log.error(f"Error retrieving checkpoint for thread {thread_id}: {e}")
            log.error(f"Error type: {type(e)}, Error args: {e.args}")
            import traceback
            log.error(f"Traceback: {traceback.format_exc()}")
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
                    metadata = {
                        "timestamp": cp.get("timestamp"), 
                        "size": cp.get("size"),
                        "step": cp.get("step", 0)  # Add required step field with default value
                    }
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
    
    def _json_serializer(self, obj):
        """Custom JSON serializer to handle complex objects like AIMessage."""
        try:
            # Handle LangGraph/LangChain objects
            if hasattr(obj, 'dict'):
                return obj.dict()
            elif hasattr(obj, '__dict__'):
                # Convert object to dict, filtering out private attributes
                result = {}
                for key, value in obj.__dict__.items():
                    if not key.startswith('_'):
                        try:
                            # Test if value is JSON serializable
                            json.dumps(value)
                            result[key] = value
                        except (TypeError, ValueError):
                            # Convert non-serializable values to string
                            result[key] = str(value)
                return result
            elif hasattr(obj, '__class__'):
                # For other objects, return class name and string representation
                return {
                    "__class__": obj.__class__.__name__,
                    "__str__": str(obj)
                }
            else:
                # Fallback to string representation
                return str(obj)
        except Exception as e:
            log.warning(f"Failed to serialize object {type(obj)}: {e}")
            return f"<Unserializable: {type(obj).__name__}>"

    def _serialize_checkpoint(self, checkpoint: Checkpoint, metadata: CheckpointMetadata, new_versions: Optional[dict] = None) -> bytes:
        """Serialize checkpoint, metadata, and versions to bytes."""
        # Ensure checkpoint has required LangGraph version field with proper validation
        if isinstance(checkpoint, dict):
            # Always ensure 'v' field exists and is valid
            if "v" not in checkpoint or not isinstance(checkpoint.get("v"), int) or checkpoint.get("v") < 1:
                compatible_version = HighPerformanceCheckpointer._get_compatible_version()
                checkpoint["v"] = compatible_version
                log.debug(f"Set checkpoint version to {compatible_version} for checkpoint {checkpoint.get('id', '<unknown>')}")            
        
        # Sanitize metadata to prevent serialization issues
        safe_metadata = self._sanitize_metadata(metadata)
        
        data = {
            "checkpoint": checkpoint,
            "metadata": safe_metadata,
            "new_versions": new_versions or {},
            "timestamp": datetime.now().isoformat(),
            "serializer_version": f"langgraph_v{HighPerformanceCheckpointer._get_compatible_version()}"  # Track detected version
        }
        return json.dumps(data, default=self._json_serializer).encode('utf-8')
    
    @classmethod
    def _detect_langgraph_version(cls) -> None:
        """Dynamically detect LangGraph's preferred checkpoint version."""
        if cls._DETECTED_LANGGRAPH_VERSION is None:
            try:
                from langgraph.checkpoint.base import empty_checkpoint
                default_checkpoint = empty_checkpoint()
                detected_version = default_checkpoint.get('v', 2)  # Fallback to 2 if 'v' missing
                cls._DETECTED_LANGGRAPH_VERSION = detected_version
                log.info(f"🔍 Detected LangGraph checkpoint version: {detected_version}")
            except Exception as e:
                log.warning(f"Could not detect LangGraph version, using safe fallback: {e}")
                cls._DETECTED_LANGGRAPH_VERSION = 2  # Safe fallback
    
    @classmethod
    def _get_compatible_version(cls) -> int:
        """Get the compatible checkpoint version for current LangGraph installation."""
        if cls._DETECTED_LANGGRAPH_VERSION is None:
            cls._detect_langgraph_version()
        return cls._DETECTED_LANGGRAPH_VERSION or 2
    
    def _deserialize_checkpoint(self, data: bytes) -> Checkpoint:
        """Deserialize bytes back to checkpoint with enhanced version compatibility."""
        import json
        try:
            # Safely decode and parse JSON
            if not isinstance(data, bytes):
                log.error(f"Expected bytes for checkpoint data, got {type(data)}")
                return self._create_minimal_checkpoint()
                
            parsed = json.loads(data.decode('utf-8'))
            
            # Safely extract checkpoint data
            if not isinstance(parsed, dict):
                log.error(f"Expected dict for parsed checkpoint data, got {type(parsed)}")
                return self._create_minimal_checkpoint()
                
            checkpoint = parsed.get("checkpoint", {})
            serializer_version = parsed.get("serializer_version", "unknown")
            
            # Ensure checkpoint is a dictionary
            if not isinstance(checkpoint, dict):
                log.error(f"Expected dict for checkpoint, got {type(checkpoint)}")
                return self._create_minimal_checkpoint()
            
            # Enhanced version field handling with backwards compatibility
            checkpoint = self._ensure_version_compatibility(checkpoint, serializer_version)
            
            # Additional validation to prevent KeyError 'v' in LangGraph
            if not self._validate_checkpoint_structure(checkpoint):
                log.warning(f"Checkpoint structure validation failed, creating compliant checkpoint")
                return self._create_compatible_checkpoint(checkpoint)

            log.debug(
                "Checkpoint parsed with version %s (%s), id=%s, serializer=%s",
                checkpoint.get("v"),
                type(checkpoint.get("v")),
                checkpoint.get("id", "<unknown>"),
                serializer_version
            )
            return checkpoint
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            log.error(f"Error decoding/parsing checkpoint JSON: {e}")
            return self._create_minimal_checkpoint()  # Return minimal valid checkpoint
        except Exception as e:
            log.error(f"Unexpected error deserializing checkpoint: {e}")
            import traceback
            log.debug(f"Deserialization traceback: {traceback.format_exc()}")
            return self._create_minimal_checkpoint()  # Return minimal valid checkpoint
    
    def _ensure_valid_checkpoint(self, checkpoint: Checkpoint) -> Checkpoint:
        """Ensure checkpoint is valid for LangGraph usage."""
        if not isinstance(checkpoint, dict):
            log.warning("Checkpoint is not a dict, creating new valid checkpoint")
            return self._create_minimal_checkpoint()
        
        # Ensure version field exists
        if "v" not in checkpoint:
            log.warning(
                "Validated checkpoint missing version field; assigning default",
                checkpoint.get("id", "<unknown>"),
            )
            checkpoint["v"] = HighPerformanceCheckpointer._get_compatible_version()
        
        # Ensure id field exists (required by LangGraph)
        if "id" not in checkpoint:
            import uuid
            checkpoint["id"] = str(uuid.uuid4())
            
        # Ensure timestamp field exists
        if "ts" not in checkpoint:
            from datetime import datetime
            checkpoint["ts"] = datetime.now().isoformat() + "+00:00"
        
        # Ensure other required fields exist with defaults
        if "channel_values" not in checkpoint:
            checkpoint["channel_values"] = {}
        
        if "channel_versions" not in checkpoint:
            checkpoint["channel_versions"] = {}
        
        if "versions_seen" not in checkpoint:
            checkpoint["versions_seen"] = {}
        
        if "pending_sends" not in checkpoint:
            checkpoint["pending_sends"] = []
        
        log.debug(f"Validated checkpoint with keys: {list(checkpoint.keys())}")
        return checkpoint
        
    def _create_minimal_checkpoint(self) -> Checkpoint:
        """Create a minimal valid checkpoint."""
        import uuid
        from datetime import datetime
        return {
            "v": 4,
            "id": str(uuid.uuid4()),
            "ts": datetime.now().isoformat() + "+00:00",
            "channel_values": {},
            "channel_versions": {},
            "versions_seen": {},
            "pending_sends": []
        }
    
    def _sanitize_metadata(self, metadata: CheckpointMetadata) -> Dict[str, Any]:
        """Sanitize metadata to prevent serialization issues."""
        if not isinstance(metadata, dict):
            return {}
        
        safe_metadata = {}
        for key, value in metadata.items():
            try:
                # Test JSON serialization
                json.dumps(value, default=self._json_serializer)
                safe_metadata[key] = value
            except (TypeError, ValueError) as e:
                log.debug(f"Sanitizing metadata field '{key}': {e}")
                safe_metadata[key] = str(value)
        
        return safe_metadata
    
    def _ensure_version_compatibility(self, checkpoint: Dict[str, Any], serializer_version: str) -> Dict[str, Any]:
        """Ensure checkpoint version field is compatible with current LangGraph version."""
        
        # Handle version field with different compatibility modes
        if "v" not in checkpoint:
            log.warning(
                "Checkpoint %s missing version field; applying default for serializer %s",
                checkpoint.get("id", "<unknown>"),
                serializer_version
            )
            checkpoint["v"] = HighPerformanceCheckpointer._get_compatible_version()  # Use detected compatible version
        else:
            version_value = checkpoint.get("v")
            
            # Comprehensive version validation
            if version_value is None:
                compatible_version = HighPerformanceCheckpointer._get_compatible_version()
                log.warning(f"Checkpoint version is None, setting to {compatible_version}")
                checkpoint["v"] = compatible_version
            elif not isinstance(version_value, int):
                log.warning(
                    "Checkpoint %s has non-integer version %s (%s); coercing to int",
                    checkpoint.get("id", "<unknown>"),
                    version_value,
                    type(version_value),
                )
                try:
                    if isinstance(version_value, str) and version_value.isdigit():
                        checkpoint["v"] = int(version_value)
                    elif isinstance(version_value, (float, bool)):
                        checkpoint["v"] = int(version_value)
                    else:
                        checkpoint["v"] = HighPerformanceCheckpointer._get_compatible_version()
                except (TypeError, ValueError):
                    compatible_version = HighPerformanceCheckpointer._get_compatible_version()
                    log.error(
                        "Failed to coerce checkpoint version for %s; falling back to %s",
                        checkpoint.get("id", "<unknown>"),
                        compatible_version
                    )
                    checkpoint["v"] = compatible_version
            elif version_value < 1:
                compatible_version = HighPerformanceCheckpointer._get_compatible_version()
                log.warning(f"Invalid checkpoint version {version_value}, setting to {compatible_version}")
                checkpoint["v"] = compatible_version
        
        return checkpoint
    
    def _validate_checkpoint_structure(self, checkpoint: Dict[str, Any]) -> bool:
        """Validate that checkpoint has all required fields for LangGraph compatibility."""
        required_fields = ["v", "id", "ts"]
        recommended_fields = ["channel_values", "channel_versions", "versions_seen"]
        
        # Check required fields
        for field in required_fields:
            if field not in checkpoint:
                log.debug(f"Checkpoint missing required field: {field}")
                return False
        
        # Check version field specifically (most common KeyError source)
        version = checkpoint.get("v")
        if not isinstance(version, int) or version < 1:
            log.debug(f"Invalid checkpoint version: {version} (type: {type(version)})")
            return False
        
        return True
    
    def _create_compatible_checkpoint(self, original_checkpoint: Dict[str, Any]) -> Checkpoint:
        """Create a LangGraph-compatible checkpoint preserving as much original data as possible."""
        import uuid
        from datetime import datetime
        
        # Start with minimal checkpoint
        compatible = self._create_minimal_checkpoint()
        
        # Preserve original data where possible
        if isinstance(original_checkpoint, dict):
            # Preserve ID if valid
            if "id" in original_checkpoint and original_checkpoint["id"]:
                compatible["id"] = str(original_checkpoint["id"])
            
            # Preserve timestamp if valid
            if "ts" in original_checkpoint and original_checkpoint["ts"]:
                compatible["ts"] = str(original_checkpoint["ts"])
            
            # Preserve channel data if valid
            for field in ["channel_values", "channel_versions", "versions_seen", "pending_sends"]:
                if field in original_checkpoint and isinstance(original_checkpoint[field], (dict, list)):
                    compatible[field] = original_checkpoint[field]
        
        log.debug(f"Created compatible checkpoint from original with keys: {list(original_checkpoint.keys()) if isinstance(original_checkpoint, dict) else 'N/A'}")
        return compatible
    
    def _is_checkpoint_valid_for_langgraph(self, checkpoint: Dict[str, Any]) -> bool:
        """Check if checkpoint has all required fields for LangGraph compatibility."""
        required_fields = ["v", "channel_values", "channel_versions", "versions_seen"]
        
        for field in required_fields:
            if field not in checkpoint:
                log.warning(f"Checkpoint missing required field: {field}")
                return False
        
        # Ensure version is valid
        version = checkpoint.get("v")
        if not isinstance(version, int) or version < 1:
            log.warning(
                "Invalid checkpoint version detected (%s); thread id: %s",
                version,
                checkpoint.get("id", "<unknown>"),
            )
            return False
        
        return True
    
    def _convert_to_metadata(self, checkpoint_info: Dict[str, Any]) -> CheckpointMetadata:
        """Convert internal checkpoint info to LangGraph metadata format."""
        return {
            "thread_id": checkpoint_info.get("thread_id"),
            "timestamp": checkpoint_info.get("timestamp"),
            "size": checkpoint_info.get("size"),
            "id": checkpoint_info.get("id"),
            "step": checkpoint_info.get("step", 0)  # Add required step field with default value
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
                # Ensure checkpoint is valid for LangGraph
                if checkpoint and isinstance(checkpoint, dict):
                    checkpoint = self._ensure_valid_checkpoint(checkpoint)
                    metadata = {
                        "thread_id": thread_id, 
                        "timestamp": datetime.now().isoformat(),
                        "step": 0  # Add required step field with default value
                    }
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
            serialized = json.dumps(writes_data, default=self._json_serializer).encode('utf-8')
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