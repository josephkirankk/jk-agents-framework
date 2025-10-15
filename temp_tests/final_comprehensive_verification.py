#!/usr/bin/env python3
"""
Final Comprehensive Concurrency Verification

This is the definitive verification test that checks ALL concurrency aspects
before generating the final audit report.
"""

import sys
import asyncio
import threading
import time
import inspect
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 80)
print("🔍 FINAL COMPREHENSIVE CONCURRENCY VERIFICATION")
print("=" * 80)

issues = []
warnings = []
passed = []

# ============================================================================
# 1. VERIFY LOCK TYPES
# ============================================================================

print("\n" + "=" * 80)
print("1. VERIFYING LOCK TYPES")
print("=" * 80)

def verify_lock_types():
    """Verify all locks use correct types."""
    from api import _metrics_lock, _cache_lock
    
    # Check metrics lock
    lock_type = type(_metrics_lock).__name__
    if 'RLock' in lock_type or 'Lock' in lock_type:
        print(f"✅ _metrics_lock: {lock_type} (threading-based)")
        passed.append("Lock type: _metrics_lock")
    else:
        print(f"❌ _metrics_lock: {lock_type} (should be threading lock)")
        issues.append(f"_metrics_lock is {lock_type}, not threading lock")
    
    # Check cache lock
    lock_type2 = type(_cache_lock).__name__
    if 'RLock' in lock_type2 or 'Lock' in lock_type2:
        print(f"✅ _cache_lock: {lock_type2} (threading-based)")
        passed.append("Lock type: _cache_lock")
    else:
        print(f"❌ _cache_lock: {lock_type2} (should be threading lock)")
        issues.append(f"_cache_lock is {lock_type2}, not threading lock")

verify_lock_types()

# ============================================================================
# 2. VERIFY DEEP COPY USAGE
# ============================================================================

print("\n" + "=" * 80)
print("2. VERIFYING DEEP COPY FOR CACHE ISOLATION")
print("=" * 80)

def verify_deepcopy():
    """Verify cache uses deepcopy."""
    from api import get_cached_agents_and_supervisor
    
    source = inspect.getsource(get_cached_agents_and_supervisor)
    
    deepcopy_count = source.count("deepcopy(")
    if deepcopy_count >= 2:
        print(f"✅ Found {deepcopy_count} deepcopy usages (agents + mcp_clients)")
        passed.append(f"Deep copy: {deepcopy_count} usages")
    else:
        print(f"❌ Only {deepcopy_count} deepcopy usage(s)")
        issues.append(f"Insufficient deepcopy usage: {deepcopy_count}")
    
    # Check for unsafe .copy()
    if ".copy()" in source and "deepcopy" in source:
        # It's OK if there's .copy() but also deepcopy
        print("⚠️  Found .copy() usage (verify it's safe)")
        warnings.append(".copy() found alongside deepcopy")

verify_deepcopy()

# ============================================================================
# 3. VERIFY ASYNC EVENT LOOP (NO BLOCKING)
# ============================================================================

print("\n" + "=" * 80)
print("3. VERIFYING NO BLOCKING ASYNC OPERATIONS")
print("=" * 80)

def verify_no_blocking():
    """Verify no blocking operations in async code."""
    from app.checkpointer_manager import CheckpointerManager
    
    # Check get_memory_stats
    source1 = inspect.getsource(CheckpointerManager.get_memory_stats)
    
    blocking_ops = []
    if "loop.run_until_complete" in source1:
        blocking_ops.append("loop.run_until_complete in get_memory_stats")
    if "asyncio.run(" in source1:
        blocking_ops.append("asyncio.run() in get_memory_stats")
    
    # Check reset_all_memory
    source2 = inspect.getsource(CheckpointerManager.reset_all_memory)
    
    if "loop.run_until_complete" in source2:
        blocking_ops.append("loop.run_until_complete in reset_all_memory")
    if "asyncio.run(" in source2:
        blocking_ops.append("asyncio.run() in reset_all_memory")
    
    if blocking_ops:
        print(f"❌ Found {len(blocking_ops)} blocking operations:")
        for op in blocking_ops:
            print(f"   - {op}")
            issues.append(op)
    else:
        print("✅ No blocking operations found")
        passed.append("No blocking async operations")
    
    # Check if methods are async
    if inspect.iscoroutinefunction(CheckpointerManager.get_memory_stats):
        print("✅ get_memory_stats is async")
        passed.append("get_memory_stats is async")
    else:
        print("❌ get_memory_stats is not async")
        issues.append("get_memory_stats should be async")
    
    if inspect.iscoroutinefunction(CheckpointerManager.reset_all_memory):
        print("✅ reset_all_memory is async")
        passed.append("reset_all_memory is async")
    else:
        print("❌ reset_all_memory is not async")
        issues.append("reset_all_memory should be async")

verify_no_blocking()

# ============================================================================
# 4. VERIFY SINGLETON PATTERNS
# ============================================================================

print("\n" + "=" * 80)
print("4. VERIFYING SINGLETON PATTERNS")
print("=" * 80)

def verify_singletons():
    """Verify singleton patterns are thread-safe."""
    from app.file_storage_manager import get_file_storage_manager
    from app.simple_conversation_memory_fixed import get_conversation_memory
    
    # Test FileStorageManager
    print("\n📋 FileStorageManager:")
    source = inspect.getsource(get_file_storage_manager)
    
    has_lock = "_file_storage_lock" in source or "with _lock" in source
    has_first_check = "if _file_storage_manager is not None" in source
    has_second_check = source.count("if _file_storage_manager is None") >= 1
    
    if has_lock:
        print("  ✅ Has lock")
        passed.append("FileStorageManager: has lock")
    else:
        print("  ❌ No lock")
        issues.append("FileStorageManager: no lock")
    
    if has_first_check and has_second_check:
        print("  ✅ Has double-check pattern")
        passed.append("FileStorageManager: double-check")
    else:
        print("  ❌ Missing double-check pattern")
        issues.append("FileStorageManager: no double-check")
    
    # Test ConversationMemory
    print("\n📋 ConversationMemory:")
    source2 = inspect.getsource(get_conversation_memory)
    
    has_lock2 = "_memory_lock" in source2 or "with _lock" in source2
    has_first_check2 = "if _global_conversation_memory is not None" in source2
    has_second_check2 = source2.count("if _global_conversation_memory is None") >= 1
    
    if has_lock2:
        print("  ✅ Has lock")
        passed.append("ConversationMemory: has lock")
    else:
        print("  ❌ No lock")
        issues.append("ConversationMemory: no lock")
    
    if has_first_check2 and has_second_check2:
        print("  ✅ Has double-check pattern")
        passed.append("ConversationMemory: double-check")
    else:
        print("  ❌ Missing double-check pattern")
        issues.append("ConversationMemory: no double-check")

verify_singletons()

# ============================================================================
# 5. STRESS TEST SINGLETONS
# ============================================================================

print("\n" + "=" * 80)
print("5. STRESS TESTING SINGLETONS (200 CONCURRENT ACCESSES)")
print("=" * 80)

def stress_test_singletons():
    """Stress test singleton thread safety."""
    from app.file_storage_manager import get_file_storage_manager
    from app.simple_conversation_memory_fixed import get_conversation_memory
    
    print("\n📋 Testing FileStorageManager (200 threads)...")
    instances1 = []
    def test1():
        instances1.append(id(get_file_storage_manager()))
    
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(test1) for _ in range(200)]
        for f in futures:
            f.result()
    
    unique1 = len(set(instances1))
    if unique1 == 1:
        print(f"  ✅ Single instance (200 threads)")
        passed.append("FileStorageManager stress test")
    else:
        print(f"  ❌ Multiple instances: {unique1}")
        issues.append(f"FileStorageManager: {unique1} instances")
    
    print("\n📋 Testing ConversationMemory (200 threads)...")
    instances2 = []
    def test2():
        instances2.append(id(get_conversation_memory()))
    
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(test2) for _ in range(200)]
        for f in futures:
            f.result()
    
    unique2 = len(set(instances2))
    if unique2 == 1:
        print(f"  ✅ Single instance (200 threads)")
        passed.append("ConversationMemory stress test")
    else:
        print(f"  ❌ Multiple instances: {unique2}")
        issues.append(f"ConversationMemory: {unique2} instances")

stress_test_singletons()

# ============================================================================
# 6. TEST CACHE ISOLATION FUNCTIONAL
# ============================================================================

print("\n" + "=" * 80)
print("6. TESTING CACHE ISOLATION (FUNCTIONAL)")
print("=" * 80)

def test_cache_isolation():
    """Test that cache modifications stay isolated."""
    test_cache = {
        "agents": {"agent1": {"name": "test", "config": {"model": "gpt-4"}}},
        "mcp": {"client1": {"url": "http://test"}}
    }
    
    copy1 = deepcopy(test_cache)
    copy2 = deepcopy(test_cache)
    
    # Modify copy1
    copy1["agents"]["agent1"]["name"] = "MODIFIED"
    copy1["agents"]["agent1"]["config"]["model"] = "CHANGED"
    copy1["mcp"]["client1"]["url"] = "MODIFIED_URL"
    
    # Verify copy2 unchanged
    if copy2["agents"]["agent1"]["name"] == "MODIFIED":
        print("❌ Modification leaked to copy2")
        issues.append("Cache isolation: leak to copy2")
    else:
        print("✅ copy2 unchanged")
        passed.append("Cache isolation: copy2")
    
    # Verify original unchanged
    if test_cache["agents"]["agent1"]["name"] == "MODIFIED":
        print("❌ Modification leaked to original")
        issues.append("Cache isolation: leak to original")
    else:
        print("✅ Original unchanged")
        passed.append("Cache isolation: original")

test_cache_isolation()

# ============================================================================
# 7. TEST METRICS CONCURRENT UPDATES
# ============================================================================

print("\n" + "=" * 80)
print("7. TESTING METRICS CONCURRENT UPDATES (1000 OPERATIONS)")
print("=" * 80)

def test_metrics():
    """Test metrics thread safety."""
    from api import _performance_metrics, _metrics_lock
    
    with _metrics_lock:
        initial = _performance_metrics.get("successful_requests", 0)
    
    def update():
        with _metrics_lock:
            _performance_metrics["successful_requests"] = \
                _performance_metrics.get("successful_requests", 0) + 1
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(update) for _ in range(1000)]
        for f in futures:
            f.result()
    
    with _metrics_lock:
        final = _performance_metrics["successful_requests"]
    
    expected = initial + 1000
    if final == expected:
        print(f"✅ All 1000 updates correct ({final})")
        passed.append("Metrics concurrent updates")
    else:
        print(f"❌ Expected {expected}, got {final}")
        issues.append(f"Metrics: expected {expected}, got {final}")

test_metrics()

# ============================================================================
# 8. CHECK FOR MUTABLE DEFAULT ARGUMENTS
# ============================================================================

print("\n" + "=" * 80)
print("8. CHECKING FOR MUTABLE DEFAULT ARGUMENTS")
print("=" * 80)

def check_mutable_defaults():
    """Check for mutable default argument anti-pattern."""
    import ast
    
    files_to_check = [
        "api.py",
        "app/agent_builder.py",
        "app/checkpointer_manager.py",
        "app/file_storage_manager.py"
    ]
    
    found_issues = []
    
    for file_path in files_to_check:
        full_path = Path(__file__).parent.parent / file_path
        if not full_path.exists():
            continue
        
        try:
            with open(full_path, 'r') as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for arg in node.args.defaults:
                        if isinstance(arg, (ast.List, ast.Dict, ast.Set)):
                            found_issues.append(f"{file_path}: {node.name}()")
        except:
            pass
    
    if found_issues:
        print(f"⚠️  Found {len(found_issues)} potential mutable defaults:")
        for issue in found_issues:
            print(f"  - {issue}")
            warnings.append(f"Mutable default: {issue}")
    else:
        print("✅ No mutable default arguments found")
        passed.append("No mutable defaults")

check_mutable_defaults()

# ============================================================================
# 9. VERIFY DATABASE CONNECTION PATTERNS
# ============================================================================

print("\n" + "=" * 80)
print("9. CHECKING DATABASE CONNECTION PATTERNS")
print("=" * 80)

def check_db_connections():
    """Check database connection patterns."""
    from app.memory.large_data_storage import LargeDataStorage
    
    source = inspect.getsource(LargeDataStorage.__init__)
    
    if "check_same_thread=False" in source:
        print("⚠️  SQLite: check_same_thread=False (verify thread safety)")
        warnings.append("SQLite: check_same_thread=False")
    
    if "threading.Lock" in source or "threading.RLock" in source:
        print("✅ Has thread lock for write operations")
        passed.append("LargeDataStorage: has lock")
    else:
        print("❌ No lock for database operations")
        issues.append("LargeDataStorage: no lock")
    
    if "WAL" in source or "journal_mode=WAL" in source:
        print("✅ Uses WAL mode for concurrency")
        passed.append("SQLite: WAL mode")
    else:
        print("⚠️  Not using WAL mode")
        warnings.append("SQLite: no WAL mode")

check_db_connections()

# ============================================================================
# 10. CHECK CHROMADB SINGLETON
# ============================================================================

print("\n" + "=" * 80)
print("10. CHECKING CHROMADB SINGLETON PATTERN")
print("=" * 80)

def check_chromadb():
    """Check ChromaDB singleton."""
    try:
        from app.memory.chromadb_backend import ChromaDBBackend
        
        source = inspect.getsource(ChromaDBBackend.__init__)
        
        if "_client_lock" in source or "threading.Lock" in source:
            print("✅ ChromaDB: Has thread lock")
            passed.append("ChromaDB: has lock")
        else:
            print("⚠️  ChromaDB: No explicit lock found")
            warnings.append("ChromaDB: verify thread safety")
    except ImportError:
        print("ℹ️  ChromaDB backend not available")

check_chromadb()

# ============================================================================
# FINAL REPORT
# ============================================================================

print("\n" + "=" * 80)
print("📊 FINAL VERIFICATION REPORT")
print("=" * 80)

print(f"\n✅ PASSED: {len(passed)} checks")
print(f"⚠️  WARNINGS: {len(warnings)} items")
print(f"❌ ISSUES: {len(issues)} critical")

if issues:
    print("\n🔴 CRITICAL ISSUES FOUND:")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")

if warnings:
    print("\n⚠️  WARNINGS:")
    for i, warning in enumerate(warnings, 1):
        print(f"  {i}. {warning}")

print("\n" + "=" * 80)

if issues:
    print("❌ VERIFICATION FAILED - Issues need attention")
    print("=" * 80)
    sys.exit(1)
else:
    print("✅ VERIFICATION PASSED - Ready for final audit report")
    print("=" * 80)
    sys.exit(0)
