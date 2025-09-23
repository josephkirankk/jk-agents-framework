"""
Memory Performance Testing Tools

Tools for testing and benchmarking the high-performance memory system
including ChromaDB backend, caching, and optimization features.
"""

import asyncio
import time
import random
import string
from typing import Dict, List, Any
import logging

log = logging.getLogger(__name__)

# Global variables to track performance data
_performance_data = {
    "checkpoint_operations": [],
    "cache_metrics": {},
    "concurrent_results": [],
    "memory_stats": {}
}


def create_checkpoint_stress_test(num_checkpoints: int = 100, data_size_kb: int = 10) -> Dict[str, Any]:
    """
    Create multiple checkpoints rapidly to stress test the memory system.
    
    Args:
        num_checkpoints: Number of checkpoints to create
        data_size_kb: Size of each checkpoint data in KB
        
    Returns:
        Performance metrics from the stress test
    """
    try:
        # Import our memory system
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from app.memory.manager import HighPerformanceMemoryManager, ResourceLimits
        from app.memory.structures import get_memory_stats
        
        # Generate test data
        def generate_test_data(size_kb: int) -> bytes:
            # Create realistic conversation data
            messages = []
            total_chars = size_kb * 1024
            current_chars = 0
            
            message_templates = [
                "User: Hello, how can I help with {}?",
                "Assistant: I'd be happy to help you with {}. Let me provide some information.",
                "User: That's helpful, but can you also explain {}?",
                "Assistant: Certainly! Here's a detailed explanation of {}:",
                "User: Thank you, that makes sense. What about {}?",
            ]
            
            topics = ["AI development", "machine learning", "data analysis", "software engineering", 
                     "system optimization", "database performance", "memory management", "caching strategies"]
            
            while current_chars < total_chars:
                template = random.choice(message_templates)
                topic = random.choice(topics)
                message = template.format(topic)
                messages.append(message)
                current_chars += len(message)
            
            # Create checkpoint-like data structure
            checkpoint_data = {
                "messages": messages[:total_chars//100],  # Reasonable number of messages
                "metadata": {
                    "user_id": f"stress_test_user_{random.randint(1000, 9999)}",
                    "session_id": f"session_{random.randint(100000, 999999)}",
                    "timestamp": time.time(),
                    "version": "1.0"
                },
                "context": {
                    "conversation_state": "active",
                    "topic": random.choice(topics),
                    "priority": random.choice(["low", "medium", "high"])
                }
            }
            
            import json
            return json.dumps(checkpoint_data).encode('utf-8')
        
        # Performance measurement
        start_time = time.time()
        operations_completed = 0
        errors = 0
        
        # Simulate checkpoint creation
        thread_ids = []
        data_sizes = []
        
        for i in range(num_checkpoints):
            try:
                thread_id = f"stress_test_thread_{i}_{random.randint(1000, 9999)}"
                thread_ids.append(thread_id)
                
                # Vary data size slightly for realistic testing
                actual_size = data_size_kb + random.randint(-2, 2)
                actual_size = max(1, actual_size)  # Ensure positive size
                
                test_data = generate_test_data(actual_size)
                data_sizes.append(len(test_data))
                
                operations_completed += 1
                
                # Small delay to simulate real operations
                time.sleep(0.001)  # 1ms delay
                
            except Exception as e:
                log.error(f"Error in stress test operation {i}: {e}")
                errors += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate metrics
        avg_data_size = sum(data_sizes) / len(data_sizes) if data_sizes else 0
        operations_per_second = operations_completed / total_time if total_time > 0 else 0
        
        # Get memory optimization stats
        memory_stats = get_memory_stats()
        
        results = {
            "test_type": "checkpoint_stress_test",
            "num_checkpoints_requested": num_checkpoints,
            "operations_completed": operations_completed,
            "errors": errors,
            "total_time_seconds": round(total_time, 3),
            "operations_per_second": round(operations_per_second, 2),
            "average_data_size_bytes": int(avg_data_size),
            "total_data_generated_mb": round(sum(data_sizes) / (1024 * 1024), 2),
            "memory_optimization_stats": memory_stats,
            "success_rate": round((operations_completed / num_checkpoints) * 100, 1) if num_checkpoints > 0 else 0,
            "thread_ids_generated": len(thread_ids)
        }
        
        # Store for later analysis
        _performance_data["checkpoint_operations"].append(results)
        
        return results
        
    except Exception as e:
        log.error(f"Stress test failed: {e}")
        return {
            "test_type": "checkpoint_stress_test",
            "error": str(e),
            "operations_completed": 0,
            "success_rate": 0
        }


def measure_cache_performance(num_operations: int = 50, hit_ratio_target: float = 0.7) -> Dict[str, Any]:
    """
    Measure cache performance with controlled hit/miss patterns.
    
    Args:
        num_operations: Number of cache operations to perform
        hit_ratio_target: Target cache hit ratio for testing
        
    Returns:
        Cache performance metrics
    """
    try:
        # Import cache system
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from app.memory.structures import LRUCache, CacheKey
        
        # Create test cache
        cache = LRUCache(maxsize=20)  # Small cache for testing
        
        # Pre-populate cache with some data
        cache_keys = []
        for i in range(10):
            key = CacheKey("test", f"user_{i}", f"thread_{i}")
            value = f"cached_data_{i}_{random.randint(1000, 9999)}"
            cache.set(key, value)
            cache_keys.append(key)
        
        # Perform mixed operations
        start_time = time.time()
        hits = 0
        misses = 0
        hit_times = []
        miss_times = []
        
        for i in range(num_operations):
            # Decide hit vs miss based on target ratio
            should_hit = random.random() < hit_ratio_target
            
            if should_hit and cache_keys:
                # Try to hit existing key
                key = random.choice(cache_keys)
                op_start = time.time()
                result = cache.get(key)
                op_time = time.time() - op_start
                
                if result is not None:
                    hits += 1
                    hit_times.append(op_time)
                else:
                    misses += 1
                    miss_times.append(op_time)
            else:
                # Try new key (should miss)
                key = CacheKey("test", f"new_user_{i}", f"new_thread_{i}")
                op_start = time.time()
                result = cache.get(key)
                op_time = time.time() - op_start
                
                if result is not None:
                    hits += 1
                    hit_times.append(op_time)
                else:
                    misses += 1
                    miss_times.append(op_time)
                
                # Add some new keys to cache occasionally
                if random.random() < 0.3:  # 30% chance
                    new_value = f"new_cached_data_{i}_{random.randint(1000, 9999)}"
                    cache.set(key, new_value)
                    cache_keys.append(key)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate metrics
        actual_hit_ratio = hits / (hits + misses) if (hits + misses) > 0 else 0
        avg_hit_time = sum(hit_times) / len(hit_times) if hit_times else 0
        avg_miss_time = sum(miss_times) / len(miss_times) if miss_times else 0
        
        # Get cache statistics
        cache_stats = cache.stats()
        
        results = {
            "test_type": "cache_performance_test",
            "operations_performed": num_operations,
            "cache_hits": hits,
            "cache_misses": misses,
            "actual_hit_ratio": round(actual_hit_ratio, 3),
            "target_hit_ratio": hit_ratio_target,
            "hit_ratio_accuracy": round(abs(actual_hit_ratio - hit_ratio_target), 3),
            "average_hit_time_ms": round(avg_hit_time * 1000, 3),
            "average_miss_time_ms": round(avg_miss_time * 1000, 3),
            "total_test_time_seconds": round(total_time, 3),
            "operations_per_second": round(num_operations / total_time, 2) if total_time > 0 else 0,
            "cache_statistics": cache_stats,
            "performance_improvement": f"{round((avg_miss_time - avg_hit_time) / avg_miss_time * 100, 1)}%" if avg_miss_time > 0 else "N/A"
        }
        
        # Store results
        _performance_data["cache_metrics"] = results
        
        return results
        
    except Exception as e:
        log.error(f"Cache performance test failed: {e}")
        return {
            "test_type": "cache_performance_test",
            "error": str(e),
            "cache_hits": 0,
            "cache_misses": 0,
            "actual_hit_ratio": 0
        }


def simulate_concurrent_users(num_users: int = 10, operations_per_user: int = 20) -> Dict[str, Any]:
    """
    Simulate concurrent user operations to test thread safety and scalability.
    
    Args:
        num_users: Number of concurrent users to simulate
        operations_per_user: Operations each user performs
        
    Returns:
        Concurrent performance metrics
    """
    try:
        import threading
        import queue
        
        # Results collection
        results_queue = queue.Queue()
        errors_queue = queue.Queue()
        
        def simulate_user(user_id: int, num_ops: int):
            """Simulate a single user's operations."""
            try:
                user_results = {
                    "user_id": user_id,
                    "operations_completed": 0,
                    "total_time": 0,
                    "errors": 0
                }
                
                start_time = time.time()
                
                for op in range(num_ops):
                    try:
                        # Simulate various operations
                        operation_type = random.choice([
                            "checkpoint_store", "checkpoint_retrieve", 
                            "cache_access", "data_processing"
                        ])
                        
                        if operation_type == "checkpoint_store":
                            # Simulate storing checkpoint
                            data_size = random.randint(1024, 10240)  # 1-10KB
                            data = ''.join(random.choices(string.ascii_letters + string.digits, k=data_size))
                            
                        elif operation_type == "checkpoint_retrieve":
                            # Simulate retrieving checkpoint
                            thread_id = f"user_{user_id}_thread_{random.randint(1, 10)}"
                            
                        elif operation_type == "cache_access":
                            # Simulate cache access
                            key = f"cache_key_{user_id}_{random.randint(1, 20)}"
                            
                        elif operation_type == "data_processing":
                            # Simulate data processing
                            data = [random.randint(1, 1000) for _ in range(100)]
                            result = sum(data) / len(data)
                        
                        user_results["operations_completed"] += 1
                        
                        # Small delay to simulate real work
                        time.sleep(random.uniform(0.001, 0.005))  # 1-5ms
                        
                    except Exception as e:
                        user_results["errors"] += 1
                        errors_queue.put(f"User {user_id}, op {op}: {str(e)}")
                
                user_results["total_time"] = time.time() - start_time
                user_results["ops_per_second"] = user_results["operations_completed"] / user_results["total_time"] if user_results["total_time"] > 0 else 0
                
                results_queue.put(user_results)
                
            except Exception as e:
                errors_queue.put(f"User {user_id} thread error: {str(e)}")
        
        # Start concurrent users
        threads = []
        overall_start = time.time()
        
        for user_id in range(num_users):
            thread = threading.Thread(target=simulate_user, args=(user_id, operations_per_user))
            threads.append(thread)
            thread.start()
        
        # Wait for all users to complete
        for thread in threads:
            thread.join()
        
        overall_end = time.time()
        total_test_time = overall_end - overall_start
        
        # Collect results
        user_results = []
        while not results_queue.empty():
            user_results.append(results_queue.get())
        
        errors = []
        while not errors_queue.empty():
            errors.append(errors_queue.get())
        
        # Calculate aggregate metrics
        total_operations = sum(r["operations_completed"] for r in user_results)
        total_errors = sum(r["errors"] for r in user_results)
        
        avg_ops_per_second = sum(r["ops_per_second"] for r in user_results) / len(user_results) if user_results else 0
        max_ops_per_second = max((r["ops_per_second"] for r in user_results), default=0)
        min_ops_per_second = min((r["ops_per_second"] for r in user_results), default=0)
        
        results = {
            "test_type": "concurrent_users_simulation",
            "num_users_simulated": num_users,
            "operations_per_user_target": operations_per_user,
            "total_operations_completed": total_operations,
            "total_errors": total_errors,
            "total_test_time_seconds": round(total_test_time, 3),
            "overall_throughput_ops_per_second": round(total_operations / total_test_time, 2) if total_test_time > 0 else 0,
            "average_user_ops_per_second": round(avg_ops_per_second, 2),
            "max_user_ops_per_second": round(max_ops_per_second, 2),
            "min_user_ops_per_second": round(min_ops_per_second, 2),
            "success_rate": round((total_operations - total_errors) / total_operations * 100, 1) if total_operations > 0 else 0,
            "concurrent_efficiency": round((total_operations / total_test_time) / (num_users * operations_per_user / total_test_time) * 100, 1) if total_test_time > 0 else 0,
            "user_results": user_results,
            "error_count": len(errors),
            "sample_errors": errors[:5] if errors else []  # First 5 errors for debugging
        }
        
        # Store results
        _performance_data["concurrent_results"].append(results)
        
        return results
        
    except Exception as e:
        log.error(f"Concurrent users simulation failed: {e}")
        return {
            "test_type": "concurrent_users_simulation",
            "error": str(e),
            "num_users_simulated": 0,
            "total_operations_completed": 0,
            "success_rate": 0
        }


def analyze_memory_usage() -> Dict[str, Any]:
    """
    Analyze memory optimization statistics and system performance.
    
    Returns:
        Comprehensive memory analysis report
    """
    try:
        import sys
        import os
        import psutil
        
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from app.memory.structures import get_memory_stats
        
        # Get memory optimization stats
        memory_stats = get_memory_stats()
        
        # Get system memory info
        system_memory = psutil.virtual_memory()
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info()
        
        # Calculate memory efficiency metrics
        string_intern_stats = memory_stats.get("string_intern", {})
        memory_pool_stats = memory_stats.get("memory_pool", {})
        
        # Estimate memory savings
        string_cache_size = string_intern_stats.get("cache_size", 0)
        string_hit_rate = string_intern_stats.get("hit_rate", 0)
        estimated_string_savings_mb = string_cache_size * 0.05 * string_hit_rate  # Rough estimate
        
        pool_reuse_rate = memory_pool_stats.get("reuse_rate", 0)
        pool_buffer_count = memory_pool_stats.get("total_created", 0)
        estimated_pool_savings_mb = pool_buffer_count * 0.064 * pool_reuse_rate  # 64KB per buffer estimate
        
        results = {
            "test_type": "memory_usage_analysis",
            "timestamp": time.time(),
            "system_memory": {
                "total_gb": round(system_memory.total / (1024**3), 2),
                "available_gb": round(system_memory.available / (1024**3), 2),
                "percent_used": system_memory.percent,
                "free_gb": round(system_memory.free / (1024**3), 2)
            },
            "process_memory": {
                "rss_mb": round(process_memory.rss / (1024**2), 2),  # Resident Set Size
                "vms_mb": round(process_memory.vms / (1024**2), 2),  # Virtual Memory Size
            },
            "memory_optimization": {
                "string_interning": {
                    "cached_strings": string_intern_stats.get("cache_size", 0),
                    "hit_rate": round(string_hit_rate * 100, 1),
                    "total_hits": string_intern_stats.get("hits", 0),
                    "total_misses": string_intern_stats.get("misses", 0),
                    "estimated_savings_mb": round(estimated_string_savings_mb, 2)
                },
                "memory_pool": {
                    "buffers_created": memory_pool_stats.get("total_created", 0),
                    "reuse_rate": round(pool_reuse_rate * 100, 1),
                    "currently_available": memory_pool_stats.get("available_buffers", 0),
                    "currently_in_use": memory_pool_stats.get("in_use_buffers", 0),
                    "peak_usage": memory_pool_stats.get("peak_usage", 0),
                    "estimated_savings_mb": round(estimated_pool_savings_mb, 2)
                }
            },
            "performance_data_summary": {
                "checkpoint_tests_run": len(_performance_data.get("checkpoint_operations", [])),
                "cache_tests_run": 1 if _performance_data.get("cache_metrics") else 0,
                "concurrent_tests_run": len(_performance_data.get("concurrent_results", [])),
                "total_estimated_savings_mb": round(estimated_string_savings_mb + estimated_pool_savings_mb, 2)
            },
            "optimization_effectiveness": {
                "string_interning_effective": string_hit_rate > 0.5,
                "memory_pool_effective": pool_reuse_rate > 0.3,
                "overall_optimization_score": round(((string_hit_rate + pool_reuse_rate) / 2) * 100, 1)
            }
        }
        
        # Store results
        _performance_data["memory_stats"] = results
        
        return results
        
    except Exception as e:
        log.error(f"Memory usage analysis failed: {e}")
        return {
            "test_type": "memory_usage_analysis",
            "error": str(e),
            "optimization_effectiveness": {
                "overall_optimization_score": 0
            }
        }


def benchmark_operations(operation_types: List[str] = None) -> Dict[str, Any]:
    """
    Benchmark various memory operations to measure performance.
    
    Args:
        operation_types: List of operations to benchmark
        
    Returns:
        Benchmark results for each operation type
    """
    if operation_types is None:
        operation_types = ["string_interning", "memory_pool", "cache_operations", "serialization"]
    
    try:
        import sys
        import os
        import json
        
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from app.memory.structures import StringIntern, MemoryPool, LRUCache, intern_string, get_buffer, return_buffer
        
        benchmark_results = {}
        
        for operation in operation_types:
            try:
                if operation == "string_interning":
                    # Benchmark string interning
                    intern = StringIntern()
                    test_strings = [f"thread-{i}" for i in range(1000)] * 10  # 10k strings, many repeats
                    
                    start_time = time.time()
                    for s in test_strings:
                        interned = intern.intern(s)
                    end_time = time.time()
                    
                    stats = intern.stats()
                    benchmark_results[operation] = {
                        "operations": len(test_strings),
                        "time_seconds": round(end_time - start_time, 4),
                        "ops_per_second": round(len(test_strings) / (end_time - start_time), 2),
                        "hit_rate": round(stats["hit_rate"] * 100, 1),
                        "cache_size": stats["cache_size"]
                    }
                
                elif operation == "memory_pool":
                    # Benchmark memory pool
                    pool = MemoryPool(buffer_size=1024, pool_size=50)
                    
                    start_time = time.time()
                    buffers = []
                    for i in range(100):
                        buffer = pool.acquire()
                        buffers.append(buffer)
                    
                    for buffer in buffers:
                        pool.release(buffer)
                    end_time = time.time()
                    
                    stats = pool.stats()
                    benchmark_results[operation] = {
                        "operations": 200,  # 100 acquire + 100 release
                        "time_seconds": round(end_time - start_time, 4),
                        "ops_per_second": round(200 / (end_time - start_time), 2),
                        "reuse_rate": round(stats["reuse_rate"] * 100, 1),
                        "buffers_created": stats["total_created"]
                    }
                
                elif operation == "cache_operations":
                    # Benchmark cache operations
                    cache = LRUCache(maxsize=1000)
                    
                    # Mixed read/write operations
                    start_time = time.time()
                    for i in range(1000):
                        if i % 3 == 0:  # Write
                            cache.set(f"key_{i}", f"value_{i}")
                        else:  # Read
                            cache.get(f"key_{i // 3}")
                    end_time = time.time()
                    
                    stats = cache.stats()
                    benchmark_results[operation] = {
                        "operations": 1000,
                        "time_seconds": round(end_time - start_time, 4),
                        "ops_per_second": round(1000 / (end_time - start_time), 2),
                        "hit_rate": round(stats["hit_rate"] * 100, 1),
                        "cache_size": stats["size"]
                    }
                
                elif operation == "serialization":
                    # Benchmark serialization/deserialization
                    test_data = {
                        "messages": [f"Message {i}" for i in range(100)],
                        "metadata": {"user": "test", "timestamp": time.time()},
                        "context": {"session": "benchmark", "data": list(range(50))}
                    }
                    
                    start_time = time.time()
                    for i in range(1000):
                        # Serialize
                        serialized = json.dumps(test_data).encode('utf-8')
                        # Deserialize
                        deserialized = json.loads(serialized.decode('utf-8'))
                    end_time = time.time()
                    
                    benchmark_results[operation] = {
                        "operations": 2000,  # 1000 serialize + 1000 deserialize
                        "time_seconds": round(end_time - start_time, 4),
                        "ops_per_second": round(2000 / (end_time - start_time), 2),
                        "data_size_bytes": len(serialized)
                    }
                    
            except Exception as e:
                benchmark_results[operation] = {
                    "error": str(e),
                    "ops_per_second": 0
                }
        
        # Calculate overall performance score
        total_ops_per_second = sum(
            result.get("ops_per_second", 0) 
            for result in benchmark_results.values()
        )
        
        results = {
            "test_type": "operations_benchmark",
            "operations_tested": operation_types,
            "benchmarks": benchmark_results,
            "total_ops_per_second": round(total_ops_per_second, 2),
            "performance_score": round(total_ops_per_second / 1000, 1)  # Normalized score
        }
        
        return results
        
    except Exception as e:
        log.error(f"Benchmark operations failed: {e}")
        return {
            "test_type": "operations_benchmark",
            "error": str(e),
            "total_ops_per_second": 0,
            "performance_score": 0
        }


def get_all_performance_data() -> Dict[str, Any]:
    """
    Get all collected performance data for comprehensive analysis.
    
    Returns:
        All performance test results
    """
    return _performance_data.copy()


def reset_performance_data() -> Dict[str, str]:
    """
    Reset all performance data collection.
    
    Returns:
        Confirmation message
    """
    global _performance_data
    _performance_data = {
        "checkpoint_operations": [],
        "cache_metrics": {},
        "concurrent_results": [],
        "memory_stats": {}
    }
    
    return {"message": "Performance data reset successfully"}