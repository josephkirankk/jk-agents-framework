# Concurrency Fixes - Part 1: Critical Lock Issues

## Fix #1: Thread-Safe Performance Metrics (api.py)

### Problem
Using `asyncio.Lock()` instead of `threading.Lock()` - only protects coroutines, not threads.

### Solution
```python
import threading
from collections import deque

# Line 92-100 in api.py - REPLACE
_performance_metrics = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "thread_contexts": {},
    "response_times": deque(maxlen=1000),  # Use deque with maxlen
    "memory_operations": deque(maxlen=1000)
}
_metrics_lock = threading.RLock()  # ✅ Use threading.RLock

# Update all usages of _metrics_lock from:
# async with _metrics_lock:
# TO:
# with _metrics_lock:
```

---

## Fix #2: Thread-Safe Preload Cache (api.py)

### Problem  
`asyncio.Lock()` doesn't protect against thread races. Shallow copy allows mutation.

### Solution
```python
import threading
from copy import deepcopy

# Line 127-129 - REPLACE
_preloaded_cache: Dict[str, Dict[str, Any]] = {}
_cache_lock = threading.RLock()  # ✅ Use threading.RLock
_preload_initialized = False

# In get_cached_agents_and_supervisor() - UPDATE return statement
with _cache_lock:
    if cache_key and cache_key in _preloaded_cache:
        cached = _preloaded_cache[cache_key]
        return (
            deepcopy(cached["agents"]),      # ✅ Deep copy
            cached["supervisor"],
            deepcopy(cached["mcp_clients"]), # ✅ Deep copy
            cached["app_config"]
        )
```

---

## Fix #3: Remove Blocking Event Loop Calls (checkpointer_manager.py)

### Problem
`loop.run_until_complete()` blocks the entire event loop.

### Solution
```python
# Make get_memory_stats async - Line 146
async def get_memory_stats(self) -> Dict[str, Any]:
    """Get statistics - ASYNC VERSION."""
    try:
        if hasattr(self._checkpointer, "get_stats"):
            stats = await self._checkpointer.get_stats()  # ✅ Just await
            return {
                "checkpointer_type": type(self._checkpointer).__name__,
                "stats": stats,
            }
        # ... rest of method
```

Update callers to use `await get_memory_stats()`.

---

## Fix #4: Thread-Safe Singletons

### Generic Implementation
```python
import threading
from typing import Optional, TypeVar, Callable

T = TypeVar('T')

class ThreadSafeSingleton:
    def __init__(self, factory: Callable[[], T]):
        self._factory = factory
        self._instance: Optional[T] = None
        self._lock = threading.Lock()
    
    def get(self) -> T:
        if self._instance is not None:
            return self._instance
        
        with self._lock:
            if self._instance is None:
                self._instance = self._factory()
        
        return self._instance
```

### Apply to file_storage_manager.py
```python
_file_storage_holder = ThreadSafeSingleton(lambda: FileStorageManager())

def get_file_storage_manager() -> FileStorageManager:
    return _file_storage_holder.get()
```

---

## Quick Test Script

```python
# Quick validation test
import threading
from concurrent.futures import ThreadPoolExecutor

def test_metrics_lock():
    from api import _metrics_lock
    assert isinstance(_metrics_lock, threading.RLock), "Should be threading.RLock"
    print("✅ Metrics lock is thread-safe")

def test_cache_lock():
    from api import _cache_lock
    assert isinstance(_cache_lock, threading.RLock), "Should be threading.RLock"
    print("✅ Cache lock is thread-safe")

def test_singleton_isolation():
    from app.file_storage_manager import get_file_storage_manager
    instances = []
    
    def get_id():
        instances.append(id(get_file_storage_manager()))
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        list(executor.map(lambda x: get_id(), range(20)))
    
    assert len(set(instances)) == 1, f"Got {len(set(instances))} instances"
    print("✅ Singleton pattern is thread-safe")

if __name__ == "__main__":
    test_metrics_lock()
    test_cache_lock()
    test_singleton_isolation()
    print("\n✅ All critical fixes validated")
```
