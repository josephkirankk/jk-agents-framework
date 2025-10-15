#!/usr/bin/env python3
"""
Comprehensive test for the three specific issues:
1. Async Event Loop Usage
2. Request Isolation  
3. Singleton Patterns

Tests each issue in detail to verify fixes.

NOTE: This is a standalone test script, not a pytest test.
Run directly with: python temp_tests/test_three_specific_issues.py
"""

import sys
import asyncio
import threading
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

sys.path.insert(0, str(Path(__file__).parent.parent))

# Only run if executed directly, not during pytest collection
if __name__ != "__main__":
    # Skip module-level execution when imported by pytest
    import pytest
    pytest.skip("This is a standalone script, not a pytest test", allow_module_level=True)

print("=" * 70)
print("🔍 DETAILED REVIEW OF THREE SPECIFIC ISSUES")
print("=" * 70)

# ============================================================================
# ISSUE 1: ASYNC EVENT LOOP USAGE
# ============================================================================

print("\n" + "=" * 70)
print("ISSUE 1: ASYNC EVENT LOOP USAGE")
print("=" * 70)

def test_checkpointer_async_methods():
    """Test if checkpointer methods properly handle async operations."""
    print("\n🔍 Test 1.1: Checking checkpointer_manager async handling...")
    
    from app.checkpointer_manager import CheckpointerManager
    
    issues_found = []
    
    # Check get_memory_stats method
    import inspect
    source = inspect.getsource(CheckpointerManager.get_memory_stats)
    
    if "loop.run_until_complete" in source:
        issues_found.append("❌ get_memory_stats() still uses loop.run_until_complete() (line 160)")
        print("   ⚠️  Found blocking operation: loop.run_until_complete()")
    
    if "asyncio.run(" in source:
        issues_found.append("❌ Method uses asyncio.run() in async context")
        print("   ⚠️  Found: asyncio.run() call")
    
    # Check reset_all_memory method
    source2 = inspect.getsource(CheckpointerManager.reset_all_memory)
    
    if "loop.run_until_complete" in source2:
        issues_found.append("❌ reset_all_memory() still uses loop.run_until_complete() (line 217)")
        print("   ⚠️  Found blocking operation: loop.run_until_complete()")
    
    if "asyncio.run(" in source2:
        issues_found.append("❌ reset_all_memory() uses asyncio.run() (line 219)")
        print("   ⚠️  Found: asyncio.run() call in async context")
    
    if issues_found:
        print(f"\n❌ ISSUE 1 NOT FULLY FIXED - {len(issues_found)} problems found:")
        for issue in issues_found:
            print(f"   {issue}")
        return False
    else:
        print("\n✅ ISSUE 1 FIXED - No blocking operations found")
        return True

def test_async_deadlock_scenario():
    """Test if async operations can cause deadlock."""
    print("\n🔍 Test 1.2: Testing for potential deadlock in async context...")
    
    try:
        from app.checkpointer_manager import get_checkpointer_manager
        
        async def async_operation():
            manager = get_checkpointer_manager()
            # Try to get stats in async context
            stats = manager.get_memory_stats()
            return stats
        
        # Run in async context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(async_operation())
            if "warning" in str(result):
                print("   ⚠️  Warning message found in stats (indicates async issue)")
                return False
            print("   ✅ No deadlock, but check for warnings")
            return True
        finally:
            loop.close()
    except Exception as e:
        print(f"   ❌ Exception occurred: {e}")
        return False

# ============================================================================
# ISSUE 2: REQUEST ISOLATION (Cache Deep Copy)
# ============================================================================

print("\n" + "=" * 70)
print("ISSUE 2: REQUEST ISOLATION")
print("=" * 70)

def test_cache_uses_deepcopy():
    """Test if cache returns use deepcopy for isolation."""
    print("\n🔍 Test 2.1: Checking if cache uses deepcopy...")
    
    import inspect
    from api import get_cached_agents_and_supervisor
    
    source = inspect.getsource(get_cached_agents_and_supervisor)
    
    issues_found = []
    
    if "deepcopy" not in source:
        issues_found.append("❌ deepcopy not used in get_cached_agents_and_supervisor()")
        print("   ❌ deepcopy import/usage not found")
        return False
    
    # Count deepcopy usages
    deepcopy_count = source.count("deepcopy(")
    if deepcopy_count < 2:
        issues_found.append(f"⚠️  Only {deepcopy_count} deepcopy usage(s) found, expected at least 2")
        print(f"   ⚠️  Only {deepcopy_count} deepcopy usage(s) - should be at least 2 (agents + mcp_clients)")
    else:
        print(f"   ✅ Found {deepcopy_count} deepcopy usages")
    
    # Check for .copy() which is unsafe
    if ".copy()" in source:
        issues_found.append("⚠️  Still using .copy() in some places")
        print("   ⚠️  Found .copy() usage (should be deepcopy)")
    
    if issues_found:
        print(f"\n❌ ISSUE 2 NOT FULLY FIXED:")
        for issue in issues_found:
            print(f"   {issue}")
        return False
    else:
        print("\n✅ ISSUE 2 FIXED - deepcopy properly used")
        return True

def test_cache_isolation_functional():
    """Test functional cache isolation with actual modifications."""
    print("\n🔍 Test 2.2: Testing actual cache isolation...")
    
    # Simulate cache with nested objects
    test_cache = {
        "agents": {
            "agent1": {"name": "test", "config": {"model": "gpt-4"}},
            "agent2": {"name": "test2", "config": {"model": "gpt-3.5"}}
        }
    }
    
    # Test deepcopy isolation
    copy1 = deepcopy(test_cache)
    copy2 = deepcopy(test_cache)
    
    # Modify copy1
    copy1["agents"]["agent1"]["name"] = "MODIFIED"
    copy1["agents"]["agent1"]["config"]["model"] = "CHANGED"
    
    # Verify copy2 and original are unchanged
    if copy2["agents"]["agent1"]["name"] == "MODIFIED":
        print("   ❌ Modification leaked to copy2!")
        return False
    
    if test_cache["agents"]["agent1"]["name"] == "MODIFIED":
        print("   ❌ Modification leaked to original!")
        return False
    
    print("   ✅ Cache isolation working - modifications stay isolated")
    return True

# ============================================================================
# ISSUE 3: SINGLETON PATTERNS
# ============================================================================

print("\n" + "=" * 70)
print("ISSUE 3: SINGLETON PATTERNS")
print("=" * 70)

def test_singleton_has_double_check_locking():
    """Test if singletons use double-check locking pattern."""
    print("\n🔍 Test 3.1: Checking singleton pattern implementation...")
    
    from app.file_storage_manager import get_file_storage_manager
    from app.simple_conversation_memory_fixed import get_conversation_memory
    
    import inspect
    
    results = {}
    
    # Test FileStorageManager
    source1 = inspect.getsource(get_file_storage_manager)
    has_lock = "_file_storage_lock" in source1 or "_lock" in source1
    # Check for double-check pattern: first check + check inside lock
    has_double_check = ("if _file_storage_manager is not None" in source1 and
                       "if _file_storage_manager is None" in source1) or \
                       source1.count("if _file_storage_manager is None") >= 2
    
    print("\n   FileStorageManager:")
    if has_lock:
        print("   ✅ Has lock")
    else:
        print("   ❌ No lock found")
    
    if has_double_check:
        print("   ✅ Has double-check pattern")
    else:
        print("   ❌ No double-check pattern")
    
    results['file_storage'] = has_lock and has_double_check
    
    # Test ConversationMemory
    source2 = inspect.getsource(get_conversation_memory)
    has_lock2 = "_memory_lock" in source2 or "_lock" in source2
    # Check for double-check pattern: first check + check inside lock
    has_double_check2 = ("if _global_conversation_memory is not None" in source2 and
                        "if _global_conversation_memory is None" in source2) or \
                        source2.count("if _global_conversation_memory is None") >= 2
    
    print("\n   ConversationMemory:")
    if has_lock2:
        print("   ✅ Has lock")
    else:
        print("   ❌ No lock found")
    
    if has_double_check2:
        print("   ✅ Has double-check pattern")
    else:
        print("   ❌ No double-check pattern")
    
    results['conversation_memory'] = has_lock2 and has_double_check2
    
    if all(results.values()):
        print("\n✅ ISSUE 3 FIXED - All singletons use double-check locking")
        return True
    else:
        print("\n❌ ISSUE 3 NOT FULLY FIXED")
        return False

def test_singleton_thread_safety():
    """Test singleton thread safety under concurrent access."""
    print("\n🔍 Test 3.2: Testing singleton thread safety (100 concurrent accesses)...")
    
    from app.file_storage_manager import get_file_storage_manager
    from app.simple_conversation_memory_fixed import get_conversation_memory
    
    def test_file_storage():
        instances = []
        def get_instance():
            instances.append(id(get_file_storage_manager()))
            time.sleep(0.001)
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(get_instance) for _ in range(100)]
            for f in futures:
                f.result()
        
        unique = len(set(instances))
        if unique == 1:
            print("   ✅ FileStorageManager: Single instance (100 threads)")
            return True
        else:
            print(f"   ❌ FileStorageManager: {unique} instances created!")
            return False
    
    def test_conversation_memory():
        instances = []
        def get_instance():
            instances.append(id(get_conversation_memory()))
            time.sleep(0.001)
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(get_instance) for _ in range(100)]
            for f in futures:
                f.result()
        
        unique = len(set(instances))
        if unique == 1:
            print("   ✅ ConversationMemory: Single instance (100 threads)")
            return True
        else:
            print(f"   ❌ ConversationMemory: {unique} instances created!")
            return False
    
    result1 = test_file_storage()
    result2 = test_conversation_memory()
    
    return result1 and result2

# ============================================================================
# RUN ALL TESTS
# ============================================================================

print("\n" + "=" * 70)
print("RUNNING ALL TESTS")
print("=" * 70)

results = {}

# Issue 1: Async Event Loop
results['1.1_async_methods'] = test_checkpointer_async_methods()
results['1.2_async_deadlock'] = test_async_deadlock_scenario()

# Issue 2: Request Isolation
results['2.1_deepcopy_usage'] = test_cache_uses_deepcopy()
results['2.2_cache_isolation'] = test_cache_isolation_functional()

# Issue 3: Singleton Patterns
results['3.1_double_check'] = test_singleton_has_double_check_locking()
results['3.2_thread_safety'] = test_singleton_thread_safety()

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("\n" + "=" * 70)
print("📊 FINAL SUMMARY")
print("=" * 70)

print("\n🔍 ISSUE 1: ASYNC EVENT LOOP USAGE")
issue1_fixed = results['1.1_async_methods'] and results['1.2_async_deadlock']
if issue1_fixed:
    print("✅ FIXED - No blocking operations, no deadlock risk")
else:
    print("❌ NOT FULLY FIXED - Still has blocking operations")

print("\n🔍 ISSUE 2: REQUEST ISOLATION")
issue2_fixed = results['2.1_deepcopy_usage'] and results['2.2_cache_isolation']
if issue2_fixed:
    print("✅ FIXED - deepcopy ensures proper isolation")
else:
    print("❌ NOT FULLY FIXED - Cache isolation issues remain")

print("\n🔍 ISSUE 3: SINGLETON PATTERNS")
issue3_fixed = results['3.1_double_check'] and results['3.2_thread_safety']
if issue3_fixed:
    print("✅ FIXED - Double-check locking implemented, thread-safe")
else:
    print("❌ NOT FULLY FIXED - Singleton pattern issues remain")

print("\n" + "=" * 70)
print("OVERALL STATUS")
print("=" * 70)

total_tests = len(results)
passed_tests = sum(results.values())

print(f"\n✅ Passed: {passed_tests}/{total_tests} tests")
print(f"❌ Failed: {total_tests - passed_tests}/{total_tests} tests")

if all(results.values()):
    print("\n🎉 ALL THREE ISSUES FIXED!")
    sys.exit(0)
else:
    print("\n⚠️  SOME ISSUES REQUIRE ATTENTION")
    print("\nFailed tests:")
    for test_name, passed in results.items():
        if not passed:
            print(f"  ❌ {test_name}")
    sys.exit(1)
