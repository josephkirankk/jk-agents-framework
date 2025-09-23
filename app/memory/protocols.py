"""
Protocol definitions for high-performance memory backends.

These protocols define the interface that all memory backends must implement,
ensuring consistency and enabling easy swapping of backends.
"""

from __future__ import annotations
from typing import Protocol, Dict, List, Any, Optional, AsyncContextManager
from datetime import datetime
import asyncio


class CheckpointStore(Protocol):
    """Protocol for storing and retrieving conversation checkpoints."""
    
    async def store_checkpoint(
        self, 
        user_id: str, 
        thread_id: str, 
        checkpoint_data: bytes
    ) -> None:
        """Store a checkpoint for a user thread."""
        ...
    
    async def retrieve_checkpoint(
        self, 
        user_id: str, 
        thread_id: str
    ) -> Optional[bytes]:
        """Retrieve the latest checkpoint for a user thread."""
        ...
    
    async def list_checkpoints(
        self, 
        user_id: str, 
        thread_id: str
    ) -> List[Dict[str, Any]]:
        """List all checkpoints for a user thread."""
        ...
    
    async def cleanup_old_checkpoints(
        self, 
        user_id: str, 
        older_than: datetime
    ) -> int:
        """Clean up old checkpoints and return count deleted."""
        ...


class ContextStore(Protocol):
    """Protocol for storing and retrieving semantic context."""
    
    async def store_context(
        self, 
        user_id: str, 
        content: str, 
        metadata: Dict[str, Any]
    ) -> str:
        """Store context and return document ID."""
        ...
    
    async def retrieve_context(
        self, 
        user_id: str, 
        query: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant context based on semantic similarity."""
        ...
    
    async def cleanup_user_context(
        self, 
        user_id: str
    ) -> int:
        """Clean up all context for a user and return count deleted."""
        ...


class MemoryBackend(Protocol):
    """High-level protocol for complete memory backend implementations."""
    
    checkpoint_store: CheckpointStore
    context_store: ContextStore
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the memory backend with configuration."""
        ...
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check and return status."""
        ...
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get performance and usage statistics."""
        ...
    
    async def cleanup(self) -> None:
        """Clean up resources and close connections."""
        ...


class ConnectionPool(Protocol):
    """Protocol for database connection pools."""
    
    async def acquire(self) -> AsyncContextManager[Any]:
        """Acquire a connection from the pool."""
        ...
    
    async def release(self, connection: Any) -> None:
        """Release a connection back to the pool."""
        ...
    
    async def close_all(self) -> None:
        """Close all connections in the pool."""
        ...
    
    @property
    def size(self) -> int:
        """Current pool size."""
        ...
    
    @property
    def available(self) -> int:
        """Number of available connections."""
        ...


class Cache(Protocol):
    """Protocol for caching implementations."""
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        ...
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set value in cache with TTL in seconds."""
        ...
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        ...
    
    async def clear(self) -> None:
        """Clear all cached data."""
        ...
    
    async def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        ...


class MetricsCollector(Protocol):
    """Protocol for performance metrics collection."""
    
    def record_latency(self, operation: str, duration: float) -> None:
        """Record operation latency in seconds."""
        ...
    
    def increment_counter(self, metric: str, tags: Dict[str, str] = None) -> None:
        """Increment a counter metric."""
        ...
    
    def set_gauge(self, metric: str, value: float, tags: Dict[str, str] = None) -> None:
        """Set a gauge metric value."""
        ...
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        ...