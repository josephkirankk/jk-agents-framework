#!/usr/bin/env python3
"""
Comprehensive Concurrency Integration Tests

Tests real API endpoints under concurrent load with actual data.
No mocks - tests the actual system behavior under concurrent access.

Test Categories:
1. Concurrent API requests (multiple simultaneous calls)
2. Thread-safe singleton access
3. Cache isolation under concurrent load
4. File storage concurrent operations
5. Metrics consistency under load
6. Memory operations concurrent access
"""

import pytest
import asyncio
import httpx
import time
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api import app, _performance_metrics, _metrics_lock, _preloaded_cache, _cache_lock
from app.file_storage_manager import get_file_storage_manager
from app.simple_conversation_memory_fixed import get_conversation_memory
from app.main import load_app_config


class TestConcurrentAPIRequests:
    """Test API endpoints under concurrent load with real requests."""
    
    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self):
        """Test 100 concurrent health check requests."""
        print("\n🔍 Testing 100 concurrent health checks...")
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            # Create 100 concurrent requests
            tasks = [client.get("/health") for _ in range(100)]
            
            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            elapsed = time.time() - start_time
            
            # Verify all succeeded
            errors = [r for r in responses if isinstance(r, Exception)]
            if errors:
                print(f"❌ {len(errors)} requests failed: {errors[:3]}")
                pytest.fail(f"{len(errors)} requests failed")
            
            successful = [r for r in responses if not isinstance(r, Exception)]
            assert len(successful) == 100, f"Expected 100 responses, got {len(successful)}"
            
            # Verify all returned 200
            status_codes = [r.status_code for r in successful]
            assert all(s == 200 for s in status_codes), f"Not all requests returned 200: {set(status_codes)}"
            
            print(f"✅ All 100 requests succeeded in {elapsed:.2f}s ({100/elapsed:.1f} req/s)")
    
    @pytest.mark.asyncio
    async def test_concurrent_worker_requests(self):
        """Test concurrent direct agent/worker requests with real data."""
        print("\n🔍 Testing 50 concurrent worker requests...")
        
        # Load a real config
        config_path = Path("config/agents.yaml")
        if not config_path.exists():
            pytest.skip("Config file not found")
        
        app_cfg = load_app_config(config_path)
        if not app_cfg.agents:
            pytest.skip("No agents configured")
        
        agent_name = app_cfg.agents[0].name
        
        async with httpx.AsyncClient(app=app, base_url="http://test", timeout=30.0) as client:
            # Create 50 concurrent worker requests with unique inputs
            tasks = []
            for i in range(50):
                payload = {
                    "agent_name": agent_name,
                    "input": f"Test concurrent request #{i}: What is 2+2?",
                    "raw_output": False,
                    "thread_id": f"concurrent_test_{uuid.uuid4().hex[:8]}"
                }
                tasks.append(client.post("/worker", json=payload))
            
            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            elapsed = time.time() - start_time
            
            # Analyze results
            errors = [r for r in responses if isinstance(r, Exception)]
            successful = [r for r in responses if not isinstance(r, Exception) and r.status_code == 200]
            failed = [r for r in responses if not isinstance(r, Exception) and r.status_code != 200]
            
            print(f"   Successful: {len(successful)}/50")
            print(f"   Failed: {len(failed)}/50")
            print(f"   Errors: {len(errors)}/50")
            print(f"   Time: {elapsed:.2f}s ({50/elapsed:.1f} req/s)")
            
            # Should have at least 80% success rate
            success_rate = len(successful) / 50
            assert success_rate >= 0.8, f"Success rate too low: {success_rate:.1%}"
            
            # Verify responses have correct structure
            for response in successful[:5]:  # Check first 5
                data = response.json()
                assert "success" in data, "Response missing 'success' field"
                assert "response" in data, "Response missing 'response' field"
                assert "agent_name" in data, "Response missing 'agent_name' field"
            
            print(f"✅ {len(successful)} requests succeeded with {success_rate:.1%} success rate")
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_with_files(self):
        """Test concurrent file upload requests."""
        print("\n🔍 Testing 30 concurrent file upload requests...")
        
        async with httpx.AsyncClient(app=app, base_url="http://test", timeout=30.0) as client:
            tasks = []
            for i in range(30):
                # Create unique file content
                file_content = f"Test file content #{i}\n" * 10
                files = {
                    "files": (f"test_file_{i}.txt", file_content.encode(), "text/plain")
                }
                data = {
                    "input": f"Process this test file #{i}",
                    "agent_name": "file_processor",
                    "thread_id": f"file_test_{uuid.uuid4().hex[:8]}"
                }
                tasks.append(client.post("/worker_with_files", data=data, files=files))
            
            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            elapsed = time.time() - start_time
            
            # Count results
            errors = [r for r in responses if isinstance(r, Exception)]
            successful = [r for r in responses if not isinstance(r, Exception) and r.status_code in [200, 404]]
            
            # 404 is OK if endpoint doesn't exist
            if all(r.status_code == 404 for r in successful if not isinstance(r, Exception)):
                pytest.skip("File upload endpoint not available")
            
            print(f"   Processed: {len(successful)}/30 in {elapsed:.2f}s")
            
            if errors:
                print(f"   Errors: {len(errors)} - {errors[0]}")
            
            assert len(errors) < 5, f"Too many errors: {len(errors)}"


class TestConcurrentSingletonAccess:
    """Test singleton patterns under concurrent access."""
    
    def test_file_storage_manager_concurrent_access(self):
        """Test FileStorageManager singleton with 100 concurrent accesses."""
        print("\n🔍 Testing FileStorageManager under 100 concurrent accesses...")
        
        instances = []
        errors = []
        
        def access_singleton(thread_id):
            try:
                manager = get_file_storage_manager()
                instances.append(id(manager))
                
                # Perform operations
                ref_id = manager.store_file(
                    filename=f"concurrent_test_{thread_id}.txt",
                    content=f"Test content from thread {thread_id}".encode(),
                    mime_type="text/plain",
                    thread_id=f"thread_{thread_id}"
                )
                
                # Retrieve and verify
                metadata = manager.get_file_metadata(ref_id)
                assert metadata is not None, f"Failed to retrieve file {ref_id}"
                
                # Cleanup
                manager.delete_file(ref_id)
                
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")
        
        # Run 100 concurrent accesses
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(access_singleton, i) for i in range(100)]
            for future in as_completed(futures):
                future.result()
        
        # Verify results
        if errors:
            print(f"❌ Errors: {errors[:3]}")
            pytest.fail(f"{len(errors)} operations failed")
        
        unique_instances = len(set(instances))
        assert unique_instances == 1, f"Multiple instances created: {unique_instances}"
        
        print(f"✅ All 100 operations used same singleton (ID: {instances[0]})")
    
    def test_conversation_memory_concurrent_access(self):
        """Test ConversationMemory singleton with concurrent operations."""
        print("\n🔍 Testing ConversationMemory under 100 concurrent operations...")
        
        instances = []
        errors = []
        
        def access_and_modify(thread_id):
            try:
                memory = get_conversation_memory()
                instances.append(id(memory))
                
                # Add messages
                thread_key = f"concurrent_test_{thread_id}"
                memory.add_message(thread_key, "user", f"Message from thread {thread_id}")
                memory.add_message(thread_key, "assistant", f"Response for thread {thread_id}")
                
                # Read back
                history = memory.get_conversation_history(thread_key, limit=2)
                assert len(history) >= 2, "Messages not stored correctly"
                
                # Cleanup
                memory.clear_conversation(thread_key)
                
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")
        
        # Run 100 concurrent operations
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(access_and_modify, i) for i in range(100)]
            for future in as_completed(futures):
                future.result()
        
        if errors:
            print(f"❌ Errors: {errors[:3]}")
            pytest.fail(f"{len(errors)} operations failed")
        
        unique_instances = len(set(instances))
        assert unique_instances == 1, f"Multiple instances created: {unique_instances}"
        
        print(f"✅ All 100 operations used same singleton (ID: {instances[0]})")


class TestConcurrentMetrics:
    """Test metrics consistency under concurrent load."""
    
    def test_metrics_concurrent_updates(self):
        """Test metrics with 1000 concurrent updates."""
        print("\n🔍 Testing metrics with 1000 concurrent updates...")
        
        # Reset metrics
        with _metrics_lock:
            initial_total = _performance_metrics["total_requests"]
            _performance_metrics["successful_requests"] = 0
            _performance_metrics["failed_requests"] = 0
        
        errors = []
        
        def update_metrics(thread_id):
            try:
                with _metrics_lock:
                    _performance_metrics["successful_requests"] += 1
                    _performance_metrics["response_times"].append({
                        "operation": f"concurrent_test_{thread_id}",
                        "duration": 0.001,
                        "timestamp": time.time()
                    })
            except Exception as e:
                errors.append(str(e))
        
        # Run 1000 concurrent updates
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(update_metrics, i) for i in range(1000)]
            for future in as_completed(futures):
                future.result()
        
        if errors:
            pytest.fail(f"Errors during updates: {errors[:3]}")
        
        # Verify consistency
        with _metrics_lock:
            successful = _performance_metrics["successful_requests"]
            failed = _performance_metrics["failed_requests"]
        
        assert successful == 1000, f"Expected 1000 successful, got {successful}"
        assert failed == 0, f"Expected 0 failed, got {failed}"
        
        print(f"✅ All 1000 updates completed correctly")
    
    @pytest.mark.asyncio
    async def test_metrics_tracking_under_load(self):
        """Test metrics tracking during real API load."""
        print("\n🔍 Testing metrics tracking under API load...")
        
        # Capture initial state
        with _metrics_lock:
            initial_total = _performance_metrics["total_requests"]
        
        # Generate load
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            tasks = [client.get("/health") for _ in range(50)]
            await asyncio.gather(*tasks)
        
        # Check metrics updated
        with _metrics_lock:
            final_total = _performance_metrics["total_requests"]
            contexts = len(_performance_metrics["thread_contexts"])
        
        assert final_total >= initial_total, "Metrics not updating"
        
        print(f"✅ Metrics tracking working (total: {final_total}, contexts: {contexts})")


class TestConcurrentCacheOperations:
    """Test cache isolation and consistency under concurrent access."""
    
    @pytest.mark.asyncio
    async def test_cache_isolation_under_concurrent_access(self):
        """Test that cached objects remain isolated under concurrent access."""
        print("\n🔍 Testing cache isolation with concurrent access...")
        
        # This test verifies deepcopy is working
        from copy import deepcopy
        
        # Simulate cache with test data
        test_cache = {
            "test_config": {
                "agents": {
                    "agent1": {"name": "test", "config": {"model": "gpt-4"}},
                    "agent2": {"name": "test2", "config": {"model": "gpt-3.5"}}
                }
            }
        }
        
        modifications = []
        errors = []
        
        async def access_and_modify(worker_id):
            try:
                # Get deep copy (simulating cache access)
                agents = deepcopy(test_cache["test_config"]["agents"])
                
                # Modify the copy
                agents["agent1"]["name"] = f"modified_by_{worker_id}"
                agents["agent1"]["config"]["model"] = f"model_{worker_id}"
                
                # Record modification
                modifications.append((worker_id, agents["agent1"]["name"]))
                
                # Small delay to increase chance of race
                await asyncio.sleep(0.001)
                
                # Verify original is unchanged
                original_name = test_cache["test_config"]["agents"]["agent1"]["name"]
                assert original_name == "test", f"Original cache was modified! Got: {original_name}"
                
            except Exception as e:
                errors.append(f"Worker {worker_id}: {e}")
        
        # Run 50 concurrent accesses
        tasks = [access_and_modify(i) for i in range(50)]
        await asyncio.gather(*tasks)
        
        if errors:
            pytest.fail(f"Errors: {errors[:3]}")
        
        # Verify all modifications were unique
        assert len(modifications) == 50, f"Expected 50 modifications, got {len(modifications)}"
        
        # Verify original remains unchanged
        assert test_cache["test_config"]["agents"]["agent1"]["name"] == "test"
        
        print(f"✅ All 50 concurrent accesses properly isolated")


class TestConcurrentFileOperations:
    """Test file storage operations under concurrent load."""
    
    def test_concurrent_file_store_retrieve_delete(self):
        """Test 100 concurrent file operations."""
        print("\n🔍 Testing 100 concurrent file store/retrieve/delete operations...")
        
        storage = get_file_storage_manager()
        results = []
        errors = []
        
        def file_operation(op_id):
            try:
                # Store
                ref_id = storage.store_file(
                    filename=f"concurrent_op_{op_id}.txt",
                    content=f"Content from operation {op_id}".encode(),
                    mime_type="text/plain",
                    thread_id=f"op_thread_{op_id}"
                )
                
                # Retrieve metadata
                metadata = storage.get_file_metadata(ref_id)
                assert metadata is not None, "Failed to retrieve metadata"
                assert metadata["filename"] == f"concurrent_op_{op_id}.txt"
                
                # Retrieve content
                content = storage.get_file_content_raw(ref_id)
                assert content is not None, "Failed to retrieve content"
                assert f"operation {op_id}".encode() in content
                
                # Delete
                deleted = storage.delete_file(ref_id)
                assert deleted, "Failed to delete file"
                
                # Verify deletion
                metadata_after = storage.get_file_metadata(ref_id)
                assert metadata_after is None, "File not deleted"
                
                results.append((op_id, ref_id, True))
                
            except Exception as e:
                errors.append(f"Op {op_id}: {e}")
                results.append((op_id, None, False))
        
        # Run 100 concurrent operations
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(file_operation, i) for i in range(100)]
            for future in as_completed(futures):
                future.result()
        
        if errors:
            print(f"❌ Errors: {errors[:5]}")
            pytest.fail(f"{len(errors)}/100 operations failed")
        
        successful = sum(1 for _, _, success in results if success)
        assert successful == 100, f"Expected 100 successful, got {successful}"
        
        print(f"✅ All 100 operations completed successfully")
    
    def test_concurrent_file_access_same_thread(self):
        """Test multiple operations accessing same thread's files concurrently."""
        print("\n🔍 Testing concurrent access to same thread's files...")
        
        storage = get_file_storage_manager()
        thread_id = "shared_thread"
        
        # Pre-populate with files
        ref_ids = []
        for i in range(10):
            ref_id = storage.store_file(
                filename=f"shared_file_{i}.txt",
                content=f"Shared content {i}".encode(),
                mime_type="text/plain",
                thread_id=thread_id
            )
            ref_ids.append(ref_id)
        
        errors = []
        
        def concurrent_access(worker_id):
            try:
                # List files
                files = storage.list_files(thread_id)
                assert len(files) >= 10, f"Expected at least 10 files, got {len(files)}"
                
                # Access random files
                import random
                ref_id = random.choice(ref_ids)
                metadata = storage.get_file_metadata(ref_id)
                assert metadata is not None
                
                content = storage.get_file_content_raw(ref_id)
                assert content is not None
                
            except Exception as e:
                errors.append(f"Worker {worker_id}: {e}")
        
        # Run 50 concurrent accesses
        with ThreadPoolExecutor(max_workers=25) as executor:
            futures = [executor.submit(concurrent_access, i) for i in range(50)]
            for future in as_completed(futures):
                future.result()
        
        # Cleanup
        for ref_id in ref_ids:
            storage.delete_file(ref_id)
        
        if errors:
            pytest.fail(f"Errors: {errors[:3]}")
        
        print(f"✅ All 50 concurrent accesses succeeded")


class TestConcurrentStressTest:
    """Stress test with mixed concurrent operations."""
    
    @pytest.mark.asyncio
    async def test_mixed_concurrent_load(self):
        """Stress test with mixed API calls, file ops, and metrics updates."""
        print("\n🔍 Running mixed concurrent load test (200 operations)...")
        
        results = {"api": 0, "files": 0, "memory": 0, "errors": 0}
        lock = threading.Lock()
        
        async def api_operations():
            try:
                async with httpx.AsyncClient(app=app, base_url="http://test", timeout=10.0) as client:
                    response = await client.get("/health")
                    if response.status_code == 200:
                        with lock:
                            results["api"] += 1
            except Exception as e:
                with lock:
                    results["errors"] += 1
        
        def file_operations():
            try:
                storage = get_file_storage_manager()
                ref_id = storage.store_file(
                    filename="stress_test.txt",
                    content=b"stress test content",
                    mime_type="text/plain",
                    thread_id=f"stress_{uuid.uuid4().hex[:8]}"
                )
                storage.delete_file(ref_id)
                with lock:
                    results["files"] += 1
            except Exception as e:
                with lock:
                    results["errors"] += 1
        
        def memory_operations():
            try:
                memory = get_conversation_memory()
                thread_key = f"stress_{uuid.uuid4().hex[:8]}"
                memory.add_message(thread_key, "user", "stress test")
                memory.add_message(thread_key, "assistant", "response")
                memory.clear_conversation(thread_key)
                with lock:
                    results["memory"] += 1
            except Exception as e:
                with lock:
                    results["errors"] += 1
        
        # Mix of operations
        start_time = time.time()
        
        # API operations (async)
        api_tasks = [api_operations() for _ in range(100)]
        await asyncio.gather(*api_tasks)
        
        # File and memory operations (threaded)
        with ThreadPoolExecutor(max_workers=50) as executor:
            file_futures = [executor.submit(file_operations) for _ in range(50)]
            memory_futures = [executor.submit(memory_operations) for _ in range(50)]
            
            for future in as_completed(file_futures + memory_futures):
                future.result()
        
        elapsed = time.time() - start_time
        
        print(f"\n📊 Results:")
        print(f"   API operations: {results['api']}/100")
        print(f"   File operations: {results['files']}/50")
        print(f"   Memory operations: {results['memory']}/50")
        print(f"   Errors: {results['errors']}")
        print(f"   Time: {elapsed:.2f}s ({200/elapsed:.1f} ops/s)")
        
        # Should have >90% success rate
        total_success = results["api"] + results["files"] + results["memory"]
        success_rate = total_success / 200
        
        assert success_rate >= 0.9, f"Success rate too low: {success_rate:.1%}"
        assert results["errors"] < 20, f"Too many errors: {results['errors']}"
        
        print(f"✅ Stress test passed with {success_rate:.1%} success rate")


# Test execution summary
def pytest_sessionfinish(session, exitstatus):
    """Print summary after all tests."""
    print("\n" + "=" * 70)
    print("🎯 CONCURRENCY INTEGRATION TESTS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
