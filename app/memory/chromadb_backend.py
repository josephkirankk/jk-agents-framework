"""
High-performance ChromaDB backend implementation.

Provides optimized ChromaDB integration with:
- Connection pooling for efficient resource usage
- Multi-level caching for sub-millisecond retrieval
- Batch operations for maximum throughput
- User isolation for multi-tenant support
- Async-first design for concurrency
"""

from __future__ import annotations
import asyncio
import hashlib
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime, timedelta
import threading
from dataclasses import dataclass, field

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
    path: Optional[str] = None  # For persistent storage
    
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


class AsyncConnectionPool:
    """
    High-performance async connection pool for ChromaDB.
    
    Manages connections efficiently with proper lifecycle management,
    health checking, and automatic scaling.
    """
    
    def __init__(self, config: ChromaDBConfig):
        self.config = config
        self._available: asyncio.Queue[chromadb.Client] = asyncio.Queue()
        self._in_use: set = set()
        self._lock = asyncio.Lock()
        self._closed = False
        
        # Connection factory
        if config.path:
            # Persistent client
            self._client_settings = Settings(
                persist_directory=config.path,
                anonymized_telemetry=False
            )
        else:
            # HTTP client
            self._client_settings = Settings(
                chroma_server_host=config.host,
                chroma_server_http_port=config.port,
                anonymized_telemetry=False
            )
        
        # Stats
        self._stats = {
            "total_created": 0,
            "active_connections": 0,
            "peak_usage": 0,
            "connection_errors": 0
        }
    
    async def initialize(self):
        """Initialize the connection pool with minimum connections."""
        if not HAS_CHROMADB:
            raise RuntimeError("ChromaDB not installed. Run: pip install chromadb")
            
        for _ in range(self.config.min_connections):
            try:
                client = chromadb.Client(self._client_settings)
                await self._available.put(client)
                self._stats["total_created"] += 1
            except Exception as e:
                log.error(f"Failed to create initial connection: {e}")
                self._stats["connection_errors"] += 1
    
    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[chromadb.Client, None]:
        """Acquire a connection from the pool."""
        if self._closed:
            raise RuntimeError("Connection pool is closed")
        
        client = None
        try:
            # Try to get existing connection
            try:
                client = await asyncio.wait_for(
                    self._available.get(), 
                    timeout=self.config.connection_timeout
                )
            except asyncio.TimeoutError:
                # Pool exhausted, create new connection if under limit
                async with self._lock:
                    if len(self._in_use) < self.config.max_connections:
                        client = chromadb.Client(self._client_settings)
                        self._stats["total_created"] += 1
                    else:
                        raise RuntimeError("Connection pool exhausted")
            
            # Track connection usage
            async with self._lock:
                self._in_use.add(id(client))
                self._stats["active_connections"] = len(self._in_use)
                self._stats["peak_usage"] = max(
                    self._stats["peak_usage"], 
                    len(self._in_use)
                )
            
            yield client
            
        except Exception as e:
            log.error(f"Connection error: {e}")
            self._stats["connection_errors"] += 1
            raise
        finally:
            # Return connection to pool
            if client:
                async with self._lock:
                    self._in_use.discard(id(client))
                    self._stats["active_connections"] = len(self._in_use)
                
                try:
                    await self._available.put(client)
                except Exception as e:
                    log.warning(f"Failed to return connection to pool: {e}")
    
    async def close(self):
        """Close all connections in the pool."""
        self._closed = True
        
        # Close all available connections
        while not self._available.empty():
            try:
                client = await self._available.get()
                # ChromaDB client doesn't have explicit close method
                del client
            except Exception as e:
                log.warning(f"Error closing connection: {e}")
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        return {
            **self._stats,
            "available_connections": self._available.qsize(),
            "pool_utilization": len(self._in_use) / self.config.max_connections,
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
    
    async def _ensure_collection(self, client: chromadb.Client, user_id: str):
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
        # Create optimized checkpoint
        checkpoint = OptimizedCheckpoint.create(
            intern_string(thread_id),
            user_id,
            {"data": checkpoint_data.decode('utf-8') if isinstance(checkpoint_data, bytes) else checkpoint_data}
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
            collection = await self._ensure_collection(client, user_id)
            
            # Store in ChromaDB
            collection.upsert(
                ids=[f"{thread_id}_{checkpoint.timestamp}"],
                documents=[checkpoint.data.decode('utf-8')],
                metadatas=[{
                    "user_hash": str(checkpoint.user_hash),
                    "thread_id": thread_id,
                    "timestamp": checkpoint.timestamp,
                    "size": checkpoint.size
                }]
            )
    
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
        
        # Query ChromaDB
        async with self.pool.acquire() as client:
            try:
                collection = await self._ensure_collection(client, user_id)
                
                # Query for latest checkpoint
                results = collection.query(
                    query_texts=[f"thread:{thread_id}"],
                    where={"thread_id": thread_id},
                    n_results=1
                )
                
                if results["documents"] and results["documents"][0]:
                    document = results["documents"][0][0]
                    metadata = results["metadatas"][0][0]
                    
                    # Create checkpoint from results
                    checkpoint = OptimizedCheckpoint(
                        thread_id=thread_id,
                        user_hash=int(metadata["user_hash"]),
                        timestamp=int(metadata["timestamp"]),
                        data=document.encode('utf-8'),
                        size=int(metadata["size"])
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
                collection = await self._ensure_collection(client, user_id)
                
                results = collection.query(
                    query_texts=[f"thread:{thread_id}"],
                    where={"thread_id": thread_id},
                    n_results=100  # Reasonable limit
                )
                
                checkpoints = []
                for i, metadata in enumerate(results["metadatas"][0]):
                    checkpoints.append({
                        "thread_id": metadata["thread_id"],
                        "timestamp": metadata["timestamp"],
                        "size": metadata["size"],
                        "id": results["ids"][0][i]
                    })
                
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
                collection = await self._ensure_collection(client, user_id)
                
                # Query old checkpoints
                cutoff_timestamp = int(older_than.timestamp())
                results = collection.query(
                    query_texts=["cleanup"],
                    where={"timestamp": {"$lt": cutoff_timestamp}},
                    n_results=1000
                )
                
                if results["ids"] and results["ids"][0]:
                    # Delete old checkpoints
                    collection.delete(ids=results["ids"][0])
                    return len(results["ids"][0])
                    
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
                    collection = await self._ensure_collection(client, user_id)
                    
                    # Prepare batch data
                    ids = []
                    documents = []
                    metadatas = []
                    
                    for item in user_items:
                        if item["operation"] == "store":
                            checkpoint = item["checkpoint"]
                            ids.append(f"{item['thread_id']}_{checkpoint.timestamp}")
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