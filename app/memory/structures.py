"""
High-performance data structures for zero-copy memory operations.

These structures minimize memory usage through:
- __slots__ for reduced per-instance overhead
- String interning for deduplicated strings
- Memory pools for buffer reuse
- Efficient serialization with orjson
"""

from __future__ import annotations
import time
import hashlib
import threading
import weakref
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Union, Set
from collections import defaultdict
import logging

try:
    import orjson
    HAS_ORJSON = True
except ImportError:
    import json as orjson
    HAS_ORJSON = False

log = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class OptimizedCheckpoint:
    """
    Memory-efficient checkpoint structure.
    
    Uses __slots__ to reduce memory overhead by ~40% compared to regular classes.
    All fields are immutable (frozen=True) to prevent accidental modifications.
    """
    thread_id: str
    user_hash: int      # 8 bytes instead of full user_id string
    timestamp: int      # Unix timestamp (8 bytes vs 56 for datetime)
    data: bytes         # Pre-serialized data, no copying needed
    size: int           # Size in bytes for memory tracking
    
    @classmethod
    def create(cls, thread_id: str, user_id: str, data: Any) -> 'OptimizedCheckpoint':
        """Create an optimized checkpoint from raw data."""
        # Serialize data once using fastest available serializer
        if HAS_ORJSON:
            serialized = orjson.dumps(data)
        else:
            import json
            serialized = json.dumps(data).encode('utf-8')
        
        # Hash user_id to save memory
        user_hash = hash(user_id) & 0x7FFFFFFFFFFFFFFF  # Positive hash
        
        return cls(
            thread_id=thread_id,
            user_hash=user_hash,
            timestamp=int(time.time()),
            data=serialized,
            size=len(serialized)
        )
    
    def deserialize(self) -> Any:
        """Deserialize checkpoint data."""
        if HAS_ORJSON:
            return orjson.loads(self.data)
        else:
            import json
            return json.loads(self.data.decode('utf-8'))


class StringIntern:
    """
    String interning to reduce memory usage for repeated strings.
    
    Common strings like "thread-", "user-", agent names, etc. are stored once
    and referenced everywhere, reducing memory usage significantly.
    """
    
    def __init__(self, max_size: int = 10000):
        self._cache: Dict[str, str] = {}
        self._max_size = max_size
        self._lock = threading.RLock()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}
    
    def intern(self, s: str) -> str:
        """
        Intern a string, returning the cached version if available.
        This saves memory when the same strings are used repeatedly.
        """
        if not isinstance(s, str):
            return s
            
        with self._lock:
            if s in self._cache:
                self._stats["hits"] += 1
                return self._cache[s]
            
            # Cache miss
            self._stats["misses"] += 1
            
            # Evict oldest entries if cache is full
            if len(self._cache) >= self._max_size:
                # Remove 10% of oldest entries (simple FIFO)
                to_remove = max(1, self._max_size // 10)
                for _ in range(to_remove):
                    if self._cache:
                        self._cache.pop(next(iter(self._cache)))
                        self._stats["evictions"] += 1
            
            # Store and return interned string
            self._cache[s] = s
            return s
    
    def stats(self) -> Dict[str, Any]:
        """Get interning statistics."""
        with self._lock:
            hit_rate = self._stats["hits"] / max(1, self._stats["hits"] + self._stats["misses"])
            return {
                **self._stats,
                "cache_size": len(self._cache),
                "hit_rate": hit_rate
            }


class MemoryPool:
    """
    Memory pool for reusing byte buffers to avoid allocations.
    
    Pre-allocates buffers and reuses them to eliminate garbage collection
    overhead and improve performance.
    """
    
    def __init__(self, buffer_size: int = 64 * 1024, pool_size: int = 100):
        self.buffer_size = buffer_size
        self._available: List[bytearray] = []
        self._in_use: Set[int] = set()  # Track buffer IDs
        self._lock = threading.RLock()
        self._stats = {"total_created": 0, "reused": 0, "peak_usage": 0}
        
        # Pre-allocate buffers
        for _ in range(pool_size):
            buffer = bytearray(buffer_size)
            self._available.append(buffer)
            self._stats["total_created"] += 1
    
    def acquire(self) -> bytearray:
        """Acquire a buffer from the pool."""
        with self._lock:
            if self._available:
                buffer = self._available.pop()
                buffer_id = id(buffer)
                self._in_use.add(buffer_id)
                self._stats["reused"] += 1
                self._stats["peak_usage"] = max(self._stats["peak_usage"], len(self._in_use))
                return buffer
            else:
                # Pool exhausted, create new buffer
                buffer = bytearray(self.buffer_size)
                buffer_id = id(buffer)
                self._in_use.add(buffer_id)
                self._stats["total_created"] += 1
                self._stats["peak_usage"] = max(self._stats["peak_usage"], len(self._in_use))
                return buffer
    
    def release(self, buffer: bytearray) -> None:
        """Release a buffer back to the pool."""
        if not isinstance(buffer, bytearray):
            return
            
        with self._lock:
            buffer_id = id(buffer)
            if buffer_id in self._in_use:
                self._in_use.remove(buffer_id)
                # Clear buffer and return to pool
                buffer.clear()
                self._available.append(buffer)
    
    def stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        with self._lock:
            return {
                **self._stats,
                "available_buffers": len(self._available),
                "in_use_buffers": len(self._in_use),
                "reuse_rate": self._stats["reused"] / max(1, self._stats["total_created"])
            }


class CacheKey:
    """
    Efficient cache key implementation with hash caching.
    
    Caches the hash value to avoid recomputing it repeatedly,
    which is important for high-frequency operations.
    """
    
    __slots__ = ('_key', '_hash')
    
    def __init__(self, *parts):
        self._key = tuple(str(part) for part in parts)
        self._hash = None
    
    def __hash__(self) -> int:
        if self._hash is None:
            self._hash = hash(self._key)
        return self._hash
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, CacheKey):
            return False
        return self._key == other._key
    
    def __str__(self) -> str:
        return ':'.join(self._key)


class LRUCache:
    """
    High-performance LRU cache implementation.
    
    Uses a combination of dict + doubly-linked list for O(1) operations.
    Thread-safe with minimal locking overhead.
    """
    
    class _Node:
        __slots__ = ('key', 'value', 'prev', 'next')
        
        def __init__(self, key, value):
            self.key = key
            self.value = value
            self.prev = None
            self.next = None
    
    def __init__(self, maxsize: int = 10000):
        self.maxsize = maxsize
        self._cache: Dict[Any, 'LRUCache._Node'] = {}
        self._lock = threading.RLock()
        
        # Create dummy head and tail nodes
        self._head = self._Node(None, None)
        self._tail = self._Node(None, None)
        self._head.next = self._tail
        self._tail.prev = self._head
        
        # Statistics
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}
    
    def _add_node(self, node: '_Node') -> None:
        """Add node right after head."""
        node.prev = self._head
        node.next = self._head.next
        self._head.next.prev = node
        self._head.next = node
    
    def _remove_node(self, node: '_Node') -> None:
        """Remove an existing node from the linked list."""
        prev_node = node.prev
        next_node = node.next
        prev_node.next = next_node
        next_node.prev = prev_node
    
    def _move_to_head(self, node: '_Node') -> None:
        """Move certain node to head."""
        self._remove_node(node)
        self._add_node(node)
    
    def _pop_tail(self) -> '_Node':
        """Pop the current tail node."""
        last_node = self._tail.prev
        self._remove_node(last_node)
        return last_node
    
    def get(self, key: Any) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key in self._cache:
                node = self._cache[key]
                # Move to head (most recently used)
                self._move_to_head(node)
                self._stats["hits"] += 1
                return node.value
            else:
                self._stats["misses"] += 1
                return None
    
    def set(self, key: Any, value: Any) -> None:
        """Set value in cache."""
        with self._lock:
            if key in self._cache:
                # Update existing node
                node = self._cache[key]
                node.value = value
                self._move_to_head(node)
            else:
                # Add new node
                new_node = self._Node(key, value)
                
                if len(self._cache) >= self.maxsize:
                    # Evict least recently used
                    tail = self._pop_tail()
                    del self._cache[tail.key]
                    self._stats["evictions"] += 1
                
                self._cache[key] = new_node
                self._add_node(new_node)
    
    def delete(self, key: Any) -> bool:
        """Delete key from cache."""
        with self._lock:
            if key in self._cache:
                node = self._cache[key]
                self._remove_node(node)
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cached data."""
        with self._lock:
            self._cache.clear()
            self._head.next = self._tail
            self._tail.prev = self._head
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            hit_rate = self._stats["hits"] / max(1, self._stats["hits"] + self._stats["misses"])
            return {
                **self._stats,
                "size": len(self._cache),
                "maxsize": self.maxsize,
                "hit_rate": hit_rate,
                "usage_ratio": len(self._cache) / self.maxsize
            }


# Global instances for efficiency
_string_intern = StringIntern()
_memory_pool = MemoryPool()

def intern_string(s: str) -> str:
    """Global string interning function."""
    return _string_intern.intern(s)

def get_buffer() -> bytearray:
    """Get a buffer from global pool."""
    return _memory_pool.acquire()

def return_buffer(buffer: bytearray) -> None:
    """Return buffer to global pool."""
    _memory_pool.release(buffer)

def get_memory_stats() -> Dict[str, Any]:
    """Get global memory optimization statistics."""
    return {
        "string_intern": _string_intern.stats(),
        "memory_pool": _memory_pool.stats()
    }