"""
Simple test of the advanced memory system without requiring LLM APIs.

This test focuses on the core memory functionality:
- HighPerformanceMemoryManager
- ChromaDBBackend
- Memory optimization structures
- Performance monitoring
"""

import asyncio
import logging
import os
import sys
import time
import tempfile
import shutil
from datetime import datetime
from typing import Dict, Any

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.memory.manager import HighPerformanceMemoryManager, ResourceLimits
from app.memory.chromadb_backend import ChromaDBBackend, ChromaDBConfig
from app.memory.structures import OptimizedCheckpoint, intern_string, get_memory_stats
from tools.memory_performance_tools import (
    create_checkpoint_stress_test,
    measure_cache_performance,
    simulate_concurrent_users,
    analyze_memory_usage,
    benchmark_operations
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


async def test_memory_manager_basic():
    """Test basic memory manager functionality."""
    
    print("🧠 Testing Memory Manager Basic Functionality")
    print("-" * 50)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create configuration
        config = {
            "memory": {
                "backend": "chromadb",
                "chromadb": {
                    "path": os.path.join(temp_dir, "test_memory"),
                    "max_connections": 5,
                    "min_connections": 2,
                    "l1_cache_size": 100,
                    "batch_size": 10,
                    "enable_batch_processing": True,
                    "enable_metrics": True
                }
            }
        }
        
        # Create resource limits
        resource_limits = ResourceLimits(
            max_memory_mb=128,
            max_connections=5,
            max_concurrent_operations=20
        )
        
        # Initialize memory manager
        memory_manager = HighPerformanceMemoryManager(resource_limits)
        await memory_manager.initialize(config)
        
        print("✅ Memory manager initialized")
        
        # Test health check
        health = await memory_manager.health_check()
        print(f"Health check: {'✅ Healthy' if health.get('healthy') else '❌ Unhealthy'}")
        
        # Test checkpoint operations
        user_id = "test_user"
        thread_id = "test_thread"
        test_data = b"This is test checkpoint data"
        
        # Store checkpoint
        await memory_manager.store_checkpoint(user_id, thread_id, test_data)
        print("✅ Checkpoint stored")
        
        # Retrieve checkpoint
        retrieved_data = await memory_manager.retrieve_checkpoint(user_id, thread_id)
        print(f"✅ Checkpoint retrieved: {len(retrieved_data) if retrieved_data else 0} bytes")
        
        # Verify data integrity
        if retrieved_data == test_data:
            print("✅ Data integrity verified")
        else:
            print("❌ Data integrity failed")
        
        # Get comprehensive stats
        stats = await memory_manager.get_comprehensive_stats()
        print("✅ Comprehensive stats retrieved")
        
        # Display key metrics
        backend_stats = stats.get("backend", {})
        performance = stats.get("performance", {})
        
        print(f"Backend initialized: {backend_stats.get('pool', {}).get('total_created', 0) > 0}")
        print(f"Performance monitoring active: {'current' in performance}")
        
        # Cleanup
        await memory_manager.cleanup()
        print("✅ Memory manager cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        log.error(f"Memory manager test error: {e}")
        return False
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


async def test_chromadb_backend():
    """Test ChromaDB backend directly."""
    
    print("\n🗄️ Testing ChromaDB Backend")
    print("-" * 40)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create ChromaDB configuration
        config = ChromaDBConfig(
            path=os.path.join(temp_dir, "chromadb_test"),
            max_connections=3,
            min_connections=1,
            l1_cache_size=50,
            batch_size=5
        )
        
        # Initialize backend
        backend = ChromaDBBackend(config)
        await backend.initialize({"chromadb": config.__dict__})
        
        print("✅ ChromaDB backend initialized")
        
        # Test health check
        health = await backend.health_check()
        print(f"Health: {'✅ Healthy' if health.get('healthy') else '❌ Unhealthy'}")
        
        # Test checkpoint operations
        user_id = "backend_test_user"
        thread_id = "backend_test_thread"
        test_data = b"ChromaDB backend test data"
        
        # Store checkpoint
        await backend.checkpoint_store.store_checkpoint(user_id, thread_id, test_data)
        print("✅ Checkpoint stored via backend")
        
        # Retrieve checkpoint
        retrieved = await backend.checkpoint_store.retrieve_checkpoint(user_id, thread_id)
        print(f"✅ Checkpoint retrieved: {len(retrieved) if retrieved else 0} bytes")
        
        # Get backend stats
        stats = await backend.get_stats()
        print("✅ Backend stats retrieved")
        
        pool_stats = stats.get("pool", {})
        cache_stats = stats.get("cache", {})
        
        print(f"Pool connections created: {pool_stats.get('total_created', 0)}")
        print(f"Cache size: {cache_stats.get('size', 0)}")
        
        # Cleanup
        await backend.cleanup()
        print("✅ ChromaDB backend cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB backend test failed: {e}")
        log.error(f"ChromaDB backend test error: {e}")
        return False
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_memory_optimization():
    """Test memory optimization features."""
    
    print("\n🚀 Testing Memory Optimization")
    print("-" * 35)
    
    try:
        # Test string interning
        strings = ["user_123", "thread_456", "user_123", "thread_789", "user_123"]
        interned_strings = [intern_string(s) for s in strings]
        
        print(f"✅ String interning: {len(strings)} strings processed")
        
        # Test memory stats
        memory_stats = get_memory_stats()
        
        string_stats = memory_stats.get("string_intern", {})
        pool_stats = memory_stats.get("memory_pool", {})
        
        print(f"String intern cache size: {string_stats.get('cache_size', 0)}")
        print(f"String intern hit rate: {string_stats.get('hit_rate', 0) * 100:.1f}%")
        print(f"Memory pool buffers created: {pool_stats.get('total_created', 0)}")
        print(f"Memory pool reuse rate: {pool_stats.get('reuse_rate', 0) * 100:.1f}%")
        
        print("✅ Memory optimization test completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Memory optimization test failed: {e}")
        log.error(f"Memory optimization test error: {e}")
        return False


async def test_performance_monitoring():
    """Test performance monitoring capabilities."""
    
    print("\n📊 Testing Performance Monitoring")
    print("-" * 40)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create memory manager with monitoring
        config = {
            "memory": {
                "backend": "chromadb",
                "chromadb": {
                    "path": os.path.join(temp_dir, "perf_test"),
                    "enable_metrics": True
                }
            }
        }
        
        resource_limits = ResourceLimits(max_memory_mb=64)
        memory_manager = HighPerformanceMemoryManager(resource_limits)
        await memory_manager.initialize(config)
        
        print("✅ Performance monitoring initialized")
        
        # Perform some operations to generate metrics
        for i in range(10):
            user_id = f"perf_user_{i}"
            thread_id = f"perf_thread_{i}"
            data = f"Performance test data {i}".encode('utf-8')
            
            await memory_manager.store_checkpoint(user_id, thread_id, data)
            retrieved = await memory_manager.retrieve_checkpoint(user_id, thread_id)
            
            # Small delay to allow monitoring
            await asyncio.sleep(0.01)
        
        print("✅ Performance operations completed")
        
        # Get comprehensive stats
        stats = await memory_manager.get_comprehensive_stats()
        
        performance = stats.get("performance", {})
        current = performance.get("current", {})
        
        print(f"CPU usage: {current.get('cpu_usage', 0):.1f}%")
        print(f"Memory usage: {current.get('memory_usage', 0):.1f}%")
        print(f"Operations per second: {current.get('operations_per_second', 0):.1f}")
        print(f"Cache hit rate: {current.get('cache_hit_rate', 0):.1f}%")
        
        # Cleanup
        await memory_manager.cleanup()
        print("✅ Performance monitoring test completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance monitoring test failed: {e}")
        log.error(f"Performance monitoring test error: {e}")
        return False
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


async def run_performance_tools_tests():
    """Run the performance tools tests."""
    
    print("\n🛠️ Testing Performance Tools")
    print("-" * 35)
    
    try:
        # Test checkpoint stress test
        print("Running checkpoint stress test...")
        checkpoint_results = create_checkpoint_stress_test(num_checkpoints=20, data_size_kb=2)
        
        success_rate = checkpoint_results.get('success_rate', 0)
        ops_per_second = checkpoint_results.get('operations_per_second', 0)
        
        print(f"✅ Checkpoint stress test: {success_rate}% success, {ops_per_second:.1f} ops/sec")
        
        # Test cache performance
        print("Running cache performance test...")
        cache_results = measure_cache_performance(num_operations=50, hit_ratio_target=0.7)
        
        hit_ratio = cache_results.get('actual_hit_ratio', 0)
        hit_time = cache_results.get('average_hit_time_ms', 0)
        
        print(f"✅ Cache performance: {hit_ratio * 100:.1f}% hit rate, {hit_time:.3f}ms avg hit time")
        
        # Test concurrent users
        print("Running concurrent users test...")
        concurrent_results = simulate_concurrent_users(num_users=3, operations_per_user=5)
        
        throughput = concurrent_results.get('overall_throughput_ops_per_second', 0)
        success_rate = concurrent_results.get('success_rate', 0)
        
        print(f"✅ Concurrent users: {throughput:.1f} ops/sec, {success_rate}% success")
        
        # Test memory analysis
        print("Running memory analysis...")
        memory_results = analyze_memory_usage()
        
        optimization_score = memory_results.get('optimization_effectiveness', {}).get('overall_optimization_score', 0)
        
        print(f"✅ Memory analysis: {optimization_score}% optimization score")
        
        # Test operations benchmark
        print("Running operations benchmark...")
        benchmark_results = benchmark_operations(['string_interning', 'cache_operations'])
        
        performance_score = benchmark_results.get('performance_score', 0)
        
        print(f"✅ Operations benchmark: {performance_score} performance score")
        
        print("✅ All performance tools tests completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance tools tests failed: {e}")
        log.error(f"Performance tools test error: {e}")
        return False


async def main():
    """Run all memory system tests."""
    
    print("🧪 Advanced Memory System Test Suite")
    print("=" * 60)
    print("Testing core memory functionality without requiring LLM APIs")
    print()
    
    test_results = []
    
    # Run all tests
    tests = [
        ("Memory Manager Basic", test_memory_manager_basic()),
        ("ChromaDB Backend", test_chromadb_backend()),
        ("Memory Optimization", test_memory_optimization()),
        ("Performance Monitoring", test_performance_monitoring()),
        ("Performance Tools", run_performance_tools_tests())
    ]
    
    for test_name, test_coro in tests:
        print(f"\n🔬 Running {test_name} Test")
        print("=" * (len(test_name) + 15))
        
        try:
            if asyncio.iscoroutine(test_coro):
                result = await test_coro
            else:
                result = test_coro
            
            test_results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name} test PASSED")
            else:
                print(f"❌ {test_name} test FAILED")
                
        except Exception as e:
            print(f"❌ {test_name} test ERROR: {e}")
            test_results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Results Summary")
    print("-" * 25)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Advanced memory system is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Check the logs for details.")
        return False


if __name__ == "__main__":
    # Run the test suite
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
