"""
High-performance ChromaDB backend implementation.

Provides optimized ChromaDB integration with:
- Connection pooling for efficient resource usage
- Multi-level caching for sub-millisecond retrieval
- Batch operations for maximum throughput
- User isolation for multi-tenant support
- Async-first design for concurrency
"""

import asyncio
import json
import time
import threading
from typing import Optional, Dict, Any, List, AsyncGenerator
import logging
from dataclasses import dataclass, field
import hashlib
import uuid
import random
from contextlib import asynccontextmanager
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    chromadb = None
    Settings = None
    HAS_CHROMADB = False

from .protocols import MemoryBackend, CheckpointStore, ContextStore
from .structures import OptimizedCheckpoint, LRUCache, CacheKey, intern_string

log = logging.getLogger(__name__)


@dataclass
class ChromaDBConfig:
    """Configuration for ChromaDB backend."""
    host: str = "localhost"
    port: int = 8000
    path: Optional[str] = None  # For persistent storage, loaded from env if None
    
    # Connection pool settings
    max_connections: int = 50
    min_connections: int = 5
    connection_timeout: float = 30.0
    
    # Cache settings
    l1_cache_size: int = 10000
    l1_cache_ttl: int = 1800  # 30 minutes
    
    # Batch settings
    batch_size: int = 100
    batch_timeout: float = 0.1  # 100ms
    
    # Collection settings
    checkpoint_collection: str = "jk_checkpoints"
    context_collection: str = "jk_contexts"
    
    # Performance settings
    enable_metrics: bool = True
    enable_batch_processing: bool = True
    
    def load_from_env(self):
        """Load path from centralized config if not set"""
        if self.path is None:
            try:
                from app.database_config import get_chromadb_path
                self.path = get_chromadb_path()
                log.info(f"Using centralized ChromaDB path: {self.path}")
            except ImportError:
                self.path = "./data/chromadb"
                log.warning("Using fallback ChromaDB path")


class AsyncConnectionPool:
    """
    ChromaDB client manager with singleton pattern for persistent storage.
    
    ChromaDB PersistentClient is NOT thread-safe and should not be pooled.
    Instead, we use a singleton client with thread-safe access patterns.
    For high-concurrency scenarios, consider using ChromaDB in client-server mode.
    """
    
    # Class-level singleton client for persistent storage
    _persistent_clients: Dict[str, chromadb.Client] = {}
    _client_lock = threading.Lock()
    
    def __init__(self, config: ChromaDBConfig):
        self.config = config
        self._client: Optional[chromadb.Client] = None
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        self._closed = False
        self._is_persistent = bool(config.path)
        self._client_key = config.path if config.path else f"{config.host}:{config.port}"
        
        # Stats
        self._stats = {
            "total_operations": 0,
            "connection_errors": 0,
            "active_operations": 0
        }
    
    async def initialize(self):
        """Initialize the ChromaDB client (singleton for persistent storage)."""
        if not HAS_CHROMADB:
            raise RuntimeError("ChromaDB not installed. Run: pip install chromadb")
        
        with self._client_lock:
            # Check if singleton client already exists for this path/host
            if self._client_key in AsyncConnectionPool._persistent_clients:
                self._client = AsyncConnectionPool._persistent_clients[self._client_key]
                log.info(f"Reusing existing ChromaDB client for {self._client_key}")
                return
            
            try:
                if self._is_persistent:
                    # Create PersistentClient for local storage
                    log.info(f"Creating ChromaDB PersistentClient: {self.config.path}")
                    self._client = chromadb.PersistentClient(
                        path=self.config.path,
                        settings=Settings(anonymized_telemetry=False)
                    )
                else:
                    # Create HttpClient for server connection
                    log.info(f"Creating ChromaDB HttpClient: {self.config.host}:{self.config.port}")
                    self._client = chromadb.HttpClient(
                        host=self.config.host,
                        port=self.config.port,
                        settings=Settings(anonymized_telemetry=False)
                    )
                
                # Store in singleton registry
                AsyncConnectionPool._persistent_clients[self._client_key] = self._client
                log.info(f"ChromaDB client initialized successfully for {self._client_key}")
                
            except Exception as e:
                log.error(f"Failed to create ChromaDB client: {e}")
                self._stats["connection_errors"] += 1
                raise
    
    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[chromadb.Client, None]:
        """Acquire the singleton ChromaDB client with thread-safe access."""
        if self._closed:
            raise RuntimeError("ChromaDB client manager is closed")
        
        if not self._client:
            raise RuntimeError("ChromaDB client not initialized. Call initialize() first.")
        
        with self._lock:
            self._stats["active_operations"] += 1
            self._stats["total_operations"] += 1
        
        try:
            yield self._client
        except Exception as e:
            log.error(f"ChromaDB operation error: {e}")
            self._stats["connection_errors"] += 1
            raise
        finally:
            with self._lock:
                self._stats["active_operations"] -= 1
    
    async def close(self):
        """Close the ChromaDB client manager."""
        self._closed = True
        # ChromaDB PersistentClient doesn't require explicit close
        # The singleton will be cleaned up when the process ends
        log.info(f"Closed ChromaDB client manager for {self._client_key}")
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            **self._stats,
            "client_key": self._client_key,
            "is_persistent": self._is_persistent,
        }


class ChromaCheckpointStore:
    """High-performance checkpoint store using ChromaDB."""
    
    def __init__(self, pool: AsyncConnectionPool, config: ChromaDBConfig):
        self.pool = pool
        self.config = config
        self._cache = LRUCache(maxsize=config.l1_cache_size)
        self._batch_queue: asyncio.Queue = asyncio.Queue()
        self._batch_processor_task: Optional[asyncio.Task] = None
        
        if config.enable_batch_processing:
            self._batch_processor_task = asyncio.create_task(
                self._batch_processor()
            )
    
    def _get_collection_name(self, user_id: str) -> str:
        """Get user-specific collection name for isolation."""
        user_hash = hashlib.md5(user_id.encode()).hexdigest()[:8]
        return f"{self.config.checkpoint_collection}_{user_hash}"
    
    def _get_cache_key(self, user_id: str, thread_id: str) -> CacheKey:
        """Get cache key for checkpoint."""
        return CacheKey("checkpoint", user_id, thread_id)
    
    def _ensure_collection(self, client: chromadb.Client, user_id: str):
        """Ensure user collection exists."""
        collection_name = self._get_collection_name(user_id)
        try:
            return client.get_collection(collection_name)
        except Exception:
            # Collection doesn't exist, create it
            return client.create_collection(
                name=collection_name,
                metadata={"user_id": user_id, "type": "checkpoints"}
            )
    
    async def store_checkpoint(
        self, 
        user_id: str, 
        thread_id: str, 
        checkpoint_data: bytes
    ) -> None:
        """Store a checkpoint with caching and batching."""
        # Decode payload to a Python structure to avoid double-encoding during storage
        if isinstance(checkpoint_data, bytes):
            try:
                raw_payload = checkpoint_data.decode('utf-8')
            except UnicodeDecodeError as err:
                log.error(
                    "Failed to decode checkpoint payload for thread %s: %s",
                    thread_id,
                    err,
                )
                raw_payload = None
        else:
            raw_payload = checkpoint_data

        payload: Dict[str, Any]
        if isinstance(raw_payload, str):
            try:
                payload = json.loads(raw_payload)
            except json.JSONDecodeError as err:
                log.error(
                    "Checkpoint payload for thread %s is not valid JSON: %s",
                    thread_id,
                    err,
                )
                payload = {"checkpoint_blob": raw_payload}
        elif isinstance(raw_payload, dict):
            payload = raw_payload
        else:
            payload = {"checkpoint_blob": raw_payload}

        # Create optimized checkpoint
        checkpoint = OptimizedCheckpoint.create(
            intern_string(thread_id),
            user_id,
            payload,
        )
        
        # Update cache
        cache_key = self._get_cache_key(user_id, thread_id)
        self._cache.set(cache_key, checkpoint)
        
        # Queue for batch processing
        if self.config.enable_batch_processing:
            await self._batch_queue.put({
                "operation": "store",
                "user_id": user_id,
                "thread_id": thread_id,
                "checkpoint": checkpoint
            })
        else:
            # Immediate storage
            await self._store_immediate(user_id, thread_id, checkpoint)
    
    async def _store_immediate(
        self, 
        user_id: str, 
        thread_id: str, 
        checkpoint: OptimizedCheckpoint
    ):
        """Store checkpoint immediately in ChromaDB."""
        async with self.pool.acquire() as client:
            collection = self._ensure_collection(client, user_id)
            
            # Store in ChromaDB with unique ID
            unique_id = f"{thread_id}_{checkpoint.timestamp}_{uuid.uuid4().hex[:8]}_{random.randint(1000, 9999)}"
            collection.upsert(
                ids=[unique_id],
                documents=[checkpoint.data.decode('utf-8')],
                metadatas=[{
                    "user_hash": str(checkpoint.user_hash),
                    "thread_id": thread_id,
                    "timestamp": checkpoint.timestamp,
                    "size": checkpoint.size
                }]
            )
            
            # Log successful storage for debugging
            log.debug(f"Stored checkpoint with ID: {unique_id} for thread: {thread_id}")
    
    async def retrieve_checkpoint(
        self, 
        user_id: str, 
        thread_id: str
    ) -> Optional[bytes]:
        """Retrieve latest checkpoint with caching."""
        # Check cache first
        cache_key = self._get_cache_key(user_id, thread_id)
        cached = self._cache.get(cache_key)
        if cached:
            return cached.data
        
        # Query ChromaDB using key-based retrieval and choose the latest by timestamp
        async with self.pool.acquire() as client:
            try:
                collection = self._ensure_collection(client, user_id)

                # Fetch all items for this thread_id and pick the latest by metadata.timestamp
                results = collection.get(
                    where={"thread_id": thread_id},
                    include=["metadatas", "documents"],
                )

                metadatas = results.get("metadatas") or []
                documents = results.get("documents") or []
                if metadatas and documents:
                    # metadatas is a list; align with documents list
                    latest_idx = None
                    latest_ts = -1
                    for idx, md in enumerate(metadatas):
                        try:
                            ts_val = int(md.get("timestamp", -1))
                        except Exception:
                            ts_val = -1
                        if ts_val > latest_ts:
                            latest_ts = ts_val
                            latest_idx = idx

                    if latest_idx is not None:
                        document = documents[latest_idx]
                        metadata = metadatas[latest_idx]

                        checkpoint = OptimizedCheckpoint(
                            thread_id=thread_id,
                            user_hash=int(metadata.get("user_hash", 0)),
                            timestamp=int(metadata.get("timestamp", 0)),
                            data=(document or "").encode('utf-8'),
                            size=int(metadata.get("size", 0))
                        )

                        # Cache for next time
                        self._cache.set(cache_key, checkpoint)
                        return checkpoint.data

            except Exception as e:
                log.error(f"Error retrieving checkpoint: {e}")
                return None
        
        return None
    
    async def list_checkpoints(
        self, 
        user_id: str, 
        thread_id: str
    ) -> List[Dict[str, Any]]:
        """List all checkpoints for a thread."""
        async with self.pool.acquire() as client:
            try:
                collection = self._ensure_collection(client, user_id)

                results = collection.get(
                    where={"thread_id": thread_id},
                    include=["metadatas"],
                )

                # Some clients always include ids; others only when requested.
                ids = results.get("ids") or []
                metadatas = results.get("metadatas") or []

                checkpoints = []
                for i, md in enumerate(metadatas):
                    try:
                        checkpoints.append({
                            "thread_id": md.get("thread_id"),
                            "timestamp": int(md.get("timestamp", 0)),
                            "size": int(md.get("size", 0)),
                            "id": ids[i] if i < len(ids) else None,
                        })
                    except Exception:
                        continue

                return sorted(checkpoints, key=lambda x: x["timestamp"], reverse=True)

            except Exception as e:
                log.error(f"Error listing checkpoints: {e}")
                return []
    
    async def cleanup_old_checkpoints(
        self, 
        user_id: str, 
        older_than: datetime
    ) -> int:
        """Clean up old checkpoints."""
        async with self.pool.acquire() as client:
            try:
                collection = self._ensure_collection(client, user_id)

                cutoff_timestamp = int(older_than.timestamp())
                # Use where-based delete; count items first for return value
                results = collection.get(
                    where={"timestamp": {"$lt": cutoff_timestamp}},
                    include=["metadatas"],
                )
                count = len(results.get("metadatas") or [])
                if count:
                    # Prefer where-based deletion to avoid requiring ids
                    collection.delete(where={"timestamp": {"$lt": cutoff_timestamp}})
                    return count

            except Exception as e:
                log.error(f"Error cleaning up checkpoints: {e}")

        return 0
    
    async def _batch_processor(self):
        """Process batched operations for higher throughput."""
        batch = []
        
        while True:
            try:
                # Wait for items or timeout
                try:
                    item = await asyncio.wait_for(
                        self._batch_queue.get(), 
                        timeout=self.config.batch_timeout
                    )
                    batch.append(item)
                except asyncio.TimeoutError:
                    pass
                
                # Process batch if ready or timeout
                if len(batch) >= self.config.batch_size or (
                    batch and time.time() % self.config.batch_timeout < 0.01
                ):
                    await self._process_batch(batch)
                    batch.clear()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"Batch processor error: {e}")
                batch.clear()
    
    async def _process_batch(self, batch: List[Dict[str, Any]]):
        """Process a batch of operations."""
        if not batch:
            return
            
        # Group by user for efficiency
        user_batches = {}
        for item in batch:
            user_id = item["user_id"]
            if user_id not in user_batches:
                user_batches[user_id] = []
            user_batches[user_id].append(item)
        
        # Process each user's batch
        for user_id, user_items in user_batches.items():
            try:
                async with self.pool.acquire() as client:
                    collection = self._ensure_collection(client, user_id)
                    
                    # Prepare batch data
                    ids = []
                    documents = []
                    metadatas = []
                    
                    for item in user_items:
                        if item["operation"] == "store":
                            checkpoint = item["checkpoint"]
                            # Generate unique ID to prevent duplicates
                            unique_id = f"{item['thread_id']}_{checkpoint.timestamp}_{uuid.uuid4().hex[:8]}_{random.randint(1000, 9999)}"
                            ids.append(unique_id)
                            documents.append(checkpoint.data.decode('utf-8'))
                            metadatas.append({
                                "user_hash": str(checkpoint.user_hash),
                                "thread_id": item["thread_id"],
                                "timestamp": checkpoint.timestamp,
                                "size": checkpoint.size
                            })
                    
                    # Batch upsert
                    if ids:
                        collection.upsert(
                            ids=ids,
                            documents=documents,
                            metadatas=metadatas
                        )
                        
            except Exception as e:
                log.error(f"Error processing batch for user {user_id}: {e}")


class ChromaDBBackend:
    """High-performance ChromaDB memory backend."""
    
    def __init__(self, config: Optional[ChromaDBConfig] = None):
        self.config = config or ChromaDBConfig()
        self._pool: Optional[AsyncConnectionPool] = None
        self._checkpoint_store: Optional[ChromaCheckpointStore] = None
        self._initialized = False
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the ChromaDB backend."""
        if self._initialized:
            return
        
        # Load path from environment if not already set
        self.config.load_from_env()
        
        # Update config from parameters
        if "chromadb" in config:
            chromadb_config = config["chromadb"]
            for key, value in chromadb_config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
        
        # Initialize connection pool
        self._pool = AsyncConnectionPool(self.config)
        await self._pool.initialize()
        
        # Initialize stores
        self._checkpoint_store = ChromaCheckpointStore(self._pool, self.config)
        
        self._initialized = True
        log.info("ChromaDB backend initialized successfully")
    
    @property
    def checkpoint_store(self) -> ChromaCheckpointStore:
        """Get checkpoint store."""
        if not self._checkpoint_store:
            raise RuntimeError("Backend not initialized")
        return self._checkpoint_store
    
    @property
    def context_store(self):
        """Context store not implemented yet."""
        raise NotImplementedError("Context store coming in next step")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        if not self._initialized:
            return {"status": "not_initialized", "healthy": False}
        
        try:
            async with self._pool.acquire() as client:
                # Try to list collections as health check
                collections = client.list_collections()
                return {
                    "status": "healthy",
                    "healthy": True,
                    "collections_count": len(collections),
                    "pool_stats": self._pool.stats
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "healthy": False,
                "error": str(e)
            }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self._initialized:
            return {"error": "not_initialized"}
        
        return {
            "pool": self._pool.stats,
            "cache": self._checkpoint_store._cache.stats(),
            "config": {
                "max_connections": self.config.max_connections,
                "batch_size": self.config.batch_size,
                "l1_cache_size": self.config.l1_cache_size
            }
        }
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._checkpoint_store and self._checkpoint_store._batch_processor_task:
            self._checkpoint_store._batch_processor_task.cancel()
            
        if self._pool:
            await self._pool.close()
        
        self._initialized = False