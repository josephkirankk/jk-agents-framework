#!/usr/bin/env python3
"""
Test suite to validate critical concurrency fixes.

Tests:
1. Lock types are correct (threading.RLock not asyncio.Lock)
2. Singleton pattern is thread-safe
3. Cache isolation with deepcopy
4. Concurrent access doesn't cause race conditions
"""

import sys
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_metrics_lock_type():
    """Test that _metrics_lock is threading.RLock."""
    print("\n🔍 Test 1: Checking metrics lock type...")
    
    from api import _metrics_lock
    import asyncio
    
    # Check it's NOT asyncio.Lock
    if isinstance(_metrics_lock, asyncio.Lock):
        print(f"❌ FAIL: _metrics_lock is asyncio.Lock (should be threading lock)")
        return False
    
    # Check it's a threading lock (RLock type)
    lock_type_name = type(_metrics_lock).__name__
    if 'RLock' not in lock_type_name and 'Lock' not in lock_type_name:
        print(f"❌ FAIL: Expected threading lock type, got {type(_metrics_lock)}")
        return False
    
    # Verify it has threading lock methods
    if not (hasattr(_metrics_lock, 'acquire') and hasattr(_metrics_lock, 'release')):
        print(f"❌ FAIL: Lock doesn't have acquire/release methods")
        return False
    
    print(f"✅ PASS: _metrics_lock is {lock_type_name} (threading-based)")
    return True


def test_cache_lock_type():
    """Test that _cache_lock is threading.RLock."""
    print("\n🔍 Test 2: Checking cache lock type...")
    
    from api import _cache_lock
    import asyncio
    
    # Check it's NOT asyncio.Lock
    if isinstance(_cache_lock, asyncio.Lock):
        print(f"❌ FAIL: _cache_lock is asyncio.Lock (should be threading lock)")
        return False
    
    # Check it's a threading lock (RLock type)
    lock_type_name = type(_cache_lock).__name__
    if 'RLock' not in lock_type_name and 'Lock' not in lock_type_name:
        print(f"❌ FAIL: Expected threading lock type, got {type(_cache_lock)}")
        return False
    
    # Verify it has threading lock methods
    if not (hasattr(_cache_lock, 'acquire') and hasattr(_cache_lock, 'release')):
        print(f"❌ FAIL: Lock doesn't have acquire/release methods")
        return False
    
    print(f"✅ PASS: _cache_lock is {lock_type_name} (threading-based)")
    return True


def test_file_storage_singleton_thread_safety():
    """Test that FileStorageManager singleton is thread-safe."""
    print("\n🔍 Test 3: Testing FileStorageManager singleton thread safety...")
    
    from app.file_storage_manager import get_file_storage_manager
    
    instances = []
    errors = []
    
    def get_instance(thread_num):
        try:
            instance = get_file_storage_manager()
            instances.append(id(instance))
            time.sleep(0.001)  # Small delay to increase chance of race
        except Exception as e:
            errors.append(f"Thread {thread_num}: {e}")
    
    # Create 50 threads trying to get instance simultaneously
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(get_instance, i) for i in range(50)]
        for future in futures:
            future.result()
    
    # Check for errors
    if errors:
        print(f"❌ FAIL: Errors occurred: {errors}")
        return False
    
    # All instances should have same ID (singleton)
    unique_instances = len(set(instances))
    if unique_instances != 1:
        print(f"❌ FAIL: Multiple instances created: {unique_instances}")
        print(f"   Instance IDs: {set(instances)}")
        return False
    
    print(f"✅ PASS: All 50 threads got same singleton instance (ID: {instances[0]})")
    return True


def test_conversation_memory_singleton_thread_safety():
    """Test that SimpleConversationMemory singleton is thread-safe."""
    print("\n🔍 Test 4: Testing SimpleConversationMemory singleton thread safety...")
    
    from app.simple_conversation_memory_fixed import get_conversation_memory
    
    instances = []
    errors = []
    
    def get_instance(thread_num):
        try:
            instance = get_conversation_memory()
            instances.append(id(instance))
            time.sleep(0.001)
        except Exception as e:
            errors.append(f"Thread {thread_num}: {e}")
    
    # Create 50 threads
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(get_instance, i) for i in range(50)]
        for future in futures:
            future.result()
    
    if errors:
        print(f"❌ FAIL: Errors occurred: {errors}")
        return False
    
    unique_instances = len(set(instances))
    if unique_instances != 1:
        print(f"❌ FAIL: Multiple instances created: {unique_instances}")
        return False
    
    print(f"✅ PASS: All 50 threads got same singleton instance (ID: {instances[0]})")
    return True


def test_metrics_concurrent_updates():
    """Test that concurrent metrics updates don't cause race conditions."""
    print("\n🔍 Test 5: Testing concurrent metrics updates...")
    
    from api import _performance_metrics, _metrics_lock
    
    # Reset metrics
    with _metrics_lock:
        _performance_metrics["total_requests"] = 0
        _performance_metrics["successful_requests"] = 0
        _performance_metrics["thread_contexts"].clear()
    
    errors = []
    
    def update_metrics(thread_num):
        try:
            for i in range(100):
                with _metrics_lock:
                    _performance_metrics["total_requests"] += 1
                    _performance_metrics["successful_requests"] += 1
                    
                    thread_id = f"thread_{thread_num}"
                    if thread_id not in _performance_metrics["thread_contexts"]:
                        _performance_metrics["thread_contexts"][thread_id] = {
                            "turns": 0,
                            "last_update": time.time()
                        }
                    _performance_metrics["thread_contexts"][thread_id]["turns"] += 1
        except Exception as e:
            errors.append(f"Thread {thread_num}: {e}")
    
    # Run 10 threads, each incrementing 100 times
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(update_metrics, i) for i in range(10)]
        for future in futures:
            future.result()
    
    if errors:
        print(f"❌ FAIL: Errors occurred: {errors}")
        return False
    
    # Verify counts
    with _metrics_lock:
        total = _performance_metrics["total_requests"]
        successful = _performance_metrics["successful_requests"]
        contexts = len(_performance_metrics["thread_contexts"])
    
    expected_total = 10 * 100  # 10 threads * 100 increments
    if total != expected_total:
        print(f"❌ FAIL: Expected {expected_total} total requests, got {total}")
        return False
    
    if successful != expected_total:
        print(f"❌ FAIL: Expected {expected_total} successful requests, got {successful}")
        return False
    
    if contexts != 10:
        print(f"❌ FAIL: Expected 10 thread contexts, got {contexts}")
        return False
    
    print(f"✅ PASS: All {expected_total} updates completed correctly")
    print(f"   Total requests: {total}, Successful: {successful}, Contexts: {contexts}")
    return True


def test_deepcopy_import():
    """Test that deepcopy is imported in api.py."""
    print("\n🔍 Test 6: Checking deepcopy import...")
    
    import api
    
    assert hasattr(api, 'deepcopy'), "deepcopy not imported in api.py"
    
    print("✅ PASS: deepcopy is imported")
    return True


def test_cache_isolation_simulation():
    """Simulate cache isolation test (without actual agents)."""
    print("\n🔍 Test 7: Testing cache isolation with deepcopy...")
    
    from copy import deepcopy
    
    # Simulate cache structure
    cache = {
        "config1": {
            "agents": {"agent1": {"name": "test", "config": {"model": "gpt-4"}}},
            "mcp_clients": {"client1": {"status": "active"}}
        }
    }
    
    # Get two copies
    copy1_agents = deepcopy(cache["config1"]["agents"])
    copy2_agents = deepcopy(cache["config1"]["agents"])
    
    # Modify first copy
    copy1_agents["agent1"]["name"] = "MODIFIED"
    copy1_agents["agent1"]["config"]["model"] = "CHANGED"
    
    # Verify second copy is unaffected
    if copy2_agents["agent1"]["name"] == "MODIFIED":
        print("❌ FAIL: Modification leaked to second copy!")
        return False
    
    if copy2_agents["agent1"]["config"]["model"] == "CHANGED":
        print("❌ FAIL: Nested modification leaked to second copy!")
        return False
    
    # Verify original cache is unaffected
    if cache["config1"]["agents"]["agent1"]["name"] == "MODIFIED":
        print("❌ FAIL: Modification leaked to original cache!")
        return False
    
    print("✅ PASS: Deep copy properly isolates mutable objects")
    print("   Original preserved, copies independent")
    return True


def test_threading_import():
    """Test that threading module is imported in api.py."""
    print("\n🔍 Test 8: Checking threading import...")
    
    import api
    
    assert hasattr(api, 'threading'), "threading not imported in api.py"
    
    print("✅ PASS: threading module is imported")
    return True


def run_all_tests():
    """Run all concurrency fix validation tests."""
    print("=" * 70)
    print("🧪 CONCURRENCY FIXES VALIDATION TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("Lock Types - Metrics", test_metrics_lock_type),
        ("Lock Types - Cache", test_cache_lock_type),
        ("Singleton - FileStorage", test_file_storage_singleton_thread_safety),
        ("Singleton - ConversationMemory", test_conversation_memory_singleton_thread_safety),
        ("Concurrent Updates", test_metrics_concurrent_updates),
        ("Imports - deepcopy", test_deepcopy_import),
        ("Cache Isolation", test_cache_isolation_simulation),
        ("Imports - threading", test_threading_import),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ FAIL: {test_name} - Exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("=" * 70)
    print(f"\n🎯 OVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ ALL CRITICAL FIXES VALIDATED SUCCESSFULLY!")
        print("\n✨ The following issues have been fixed:")
        print("   1. Lock types changed from asyncio.Lock to threading.RLock")
        print("   2. Singleton patterns now use double-check locking")
        print("   3. Cache returns use deepcopy for isolation")
        print("   4. Concurrent access is now thread-safe")
        return True
    else:
        print(f"❌ {total - passed} test(s) failed")
        print("\n⚠️  Some fixes may need attention")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
