"""
Advanced Memory Agent Test Suite

This test suite validates the high-performance memory system with:
- Checkpoint stress testing
- Cache performance validation
- Concurrent user simulation
- Memory usage analysis
- Operations benchmarking
- Integration testing
"""

import asyncio
import json
import logging
import os
import shutil
import statistics
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List

# Load environment variables from .env.example if no .env exists
from dotenv import load_dotenv

# Try to load .env first, then .env.example as fallback
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    print("  Loading environment variables from .env")
    load_dotenv(env_file)
else:
    env_example_file = Path(__file__).parent / '.env.example'
    if env_example_file.exists():
        print("  Loading environment variables from .env.example")
        load_dotenv(env_example_file)
        # Check if API key needs to be set
        if os.getenv('AZURE_OPENAI_API_KEY') == 'xxx':
            print("  Warning: AZURE_OPENAI_API_KEY is set to placeholder 'xxx'")
            print("   Please set the actual API key as an environment variable:")
            print("   export AZURE_OPENAI_API_KEY='your-actual-api-key'")
    else:
        print("  No .env or .env.example file found")

from app.agent_builder import create_react_agent
from core.memory_monitor import MemoryMonitor

# Add the app directory to the path
sys.path.append(os.path.dirname(__file__))

from advanced_memory_agent import AdvancedMemoryAgent
from tools.memory_performance_tools import (
    create_checkpoint_stress_test,
    measure_cache_performance,
    simulate_concurrent_users,
    analyze_memory_usage,
    benchmark_operations
)

# Set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class TestAdvancedMemoryAgent:
    """Comprehensive test suite for the Advanced Memory Agent."""
    
    async def create_temp_agent(self):
        """Create a temporary agent for testing."""
        temp_dir = tempfile.mkdtemp()
        
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
            },
            "resource_limits": {
                "max_memory_mb": 128,
                "max_connections": 5,
                "max_concurrent_operations": 20,
                "scale_up_cpu_threshold": 80.0,
                "scale_down_cpu_threshold": 20.0
            }
        }
        
        agent = AdvancedMemoryAgent(config)
        await agent.initialize()
        
        return agent, temp_dir
    
    async def test_agent_initialization(self):
        """Test that the agent initializes correctly."""
        temp_agent, temp_dir = await self.create_temp_agent()
        try:
            assert temp_agent.initialized
            assert temp_agent.memory_manager is not None
            assert temp_agent.conversation_count == 0
            
            # Test health check
            health = await temp_agent.memory_manager.health_check()
            assert health.get("healthy") is True
            print("✅ Agent initialization test passed")
        finally:
            await temp_agent.cleanup()
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    async def test_basic_chat_functionality(self):
        """Test basic chat functionality with memory."""
        temp_agent, temp_dir = await self.create_temp_agent()
        try:
            # First conversation
            result1 = await temp_agent.chat("Hello, my name is Alice", "user1", "thread1")
            
            assert "response" in result1
            assert result1["user_id"] == "user1"
            assert result1["thread_id"] == "thread1"
            assert result1["conversation_count"] == 1
            assert "processing_time_ms" in result1
            
            # Second conversation in same thread
            result2 = await temp_agent.chat("What's my name?", "user1", "thread1")
            
            assert result2["conversation_count"] == 2
            assert result2["thread_id"] == "thread1"
            print("✅ Basic chat functionality test passed")
        finally:
            await temp_agent.cleanup()
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    async def test_memory_persistence(self):
        """Test that memory persists across conversations."""
        temp_agent, temp_dir = await self.create_temp_agent()
        try:
            user_id = "test_user"
            thread_id = "memory_test"
            
            # Store some information
            await temp_agent.chat("Remember that I like pizza", user_id, thread_id)
            await temp_agent.chat("My favorite color is blue", user_id, thread_id)
            
            # Try to recall information
            result = await temp_agent.chat("What do you know about my preferences?", user_id, thread_id)
            
            # Should have memory context
            assert "response" in result
            assert result["conversation_count"] > 0
            print("✅ Memory persistence test passed")
        finally:
            await temp_agent.cleanup()
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    async def test_performance_monitoring(self):
        """Test performance monitoring capabilities."""
        temp_agent, temp_dir = await self.create_temp_agent()
        try:
            # Get initial stats
            stats = await temp_agent.get_comprehensive_stats()
            
            assert "agent_info" in stats
            assert "memory_system" in stats
            assert "health" in stats
            assert "memory_optimization" in stats
            
            # Check agent info
            agent_info = stats["agent_info"]
            assert "conversation_count" in agent_info
            assert "uptime_seconds" in agent_info
            assert agent_info["initialized"] is True
            
            # Check memory system stats
            memory_system = stats["memory_system"]
            assert "backend" in memory_system
            assert "performance" in memory_system
            
            # Check health
            health = stats["health"]
            assert "healthy" in health
            print("✅ Performance monitoring test passed")
        finally:
            await temp_agent.cleanup()
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    async def test_concurrent_operations(self):
        """Test concurrent chat operations."""
        temp_agent, temp_dir = await self.create_temp_agent()
        try:
            async def chat_worker(user_id: str, message: str):
                """Worker function for concurrent testing."""
                return await temp_agent.chat(f"Hello from {user_id}: {message}", user_id, f"thread_{user_id}")
            
            # Create multiple concurrent chat operations
            tasks = []
            for i in range(5):
                task = asyncio.create_task(chat_worker(f"user_{i}", f"message_{i}"))
                tasks.append(task)
            
            # Wait for all to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check that all succeeded
            successful_results = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_results) == 5
            
            # Check that conversation counts are correct
            for result in successful_results:
                assert "conversation_count" in result
                assert "response" in result
            print("✅ Concurrent operations test passed")
        finally:
            await temp_agent.cleanup()
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    async def test_error_handling(self):
        """Test error handling and recovery."""
        temp_agent, temp_dir = await self.create_temp_agent()
        try:
            # Test with invalid user_id (should handle gracefully)
            result = await temp_agent.chat("Test message", "", "thread1")
            
            # Should still get a response, even if there's an error
            assert "response" in result
            
            # Test with very long message
            long_message = "x" * 10000
            result = await temp_agent.chat(long_message, "user1", "thread1")
            assert "response" in result
            print("✅ Error handling test passed")
        finally:
            await temp_agent.cleanup()
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    async def test_memory_optimization_features(self):
        """Test memory optimization features."""
        temp_agent, temp_dir = await self.create_temp_agent()
        try:
            # Generate multiple conversations to trigger optimizations
            for i in range(10):
                await temp_agent.chat(f"Message {i}", "user1", "thread1")
            
            # Get memory optimization stats
            stats = await temp_agent.get_comprehensive_stats()
            memory_opt = stats.get("memory_optimization", {})
            
            # Check string interning
            string_intern = memory_opt.get("string_intern", {})
            assert "cache_size" in string_intern
            assert "hit_rate" in string_intern
            
            # Check memory pool
            memory_pool = memory_opt.get("memory_pool", {})
            assert "total_created" in memory_pool
            assert "reuse_rate" in memory_pool
            print("✅ Memory optimization features test passed")
        finally:
            await temp_agent.cleanup()
            shutil.rmtree(temp_dir, ignore_errors=True)

    async def run_unit_tests(self):
        """Run all unit tests."""
        print("🧪 Running Unit Tests")
        print("=" * 30)
        
        try:
            await self.test_agent_initialization()
            await self.test_basic_chat_functionality()
            await self.test_memory_persistence()
            await self.test_performance_monitoring()
            await self.test_concurrent_operations()
            await self.test_error_handling()
            await self.test_memory_optimization_features()
            print("\n✅ All unit tests passed!")
            return True
        except Exception as e:
            print(f"\n❌ Unit test failed: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return False


async def run_performance_tests():
    """Run comprehensive performance tests."""
    
    print("🏃‍♂️ Running Performance Tests")
    print("=" * 50)
    
    # Test 1: Checkpoint stress test
    print("\n1. Checkpoint Stress Test")
    print("-" * 30)
    
    checkpoint_results = create_checkpoint_stress_test(num_checkpoints=50, data_size_kb=5)
    print(f"✅ Created {checkpoint_results['operations_completed']} checkpoints")
    print(f"📊 Operations per second: {checkpoint_results['operations_per_second']}")
    print(f"💾 Total data generated: {checkpoint_results['total_data_generated_mb']} MB")
    print(f"✨ Success rate: {checkpoint_results['success_rate']}%")
    
    # Test 2: Cache performance
    print("\n2. Cache Performance Test")
    print("-" * 30)
    
    cache_results = measure_cache_performance(num_operations=100, hit_ratio_target=0.8)
    print(f"🎯 Target hit ratio: {cache_results['target_hit_ratio'] * 100}%")
    print(f"📈 Actual hit ratio: {cache_results['actual_hit_ratio'] * 100:.1f}%")
    print(f"⚡ Average hit time: {cache_results['average_hit_time_ms']} ms")
    print(f"🐌 Average miss time: {cache_results['average_miss_time_ms']} ms")
    print(f"🚀 Performance improvement: {cache_results['performance_improvement']}")
    
    # Test 3: Concurrent users simulation
    print("\n3. Concurrent Users Simulation")
    print("-" * 30)
    
    concurrent_results = simulate_concurrent_users(num_users=5, operations_per_user=10)
    print(f"👥 Simulated users: {concurrent_results['num_users_simulated']}")
    print(f"⚡ Total operations: {concurrent_results['total_operations_completed']}")
    print(f"📊 Overall throughput: {concurrent_results['overall_throughput_ops_per_second']} ops/sec")
    print(f"✅ Success rate: {concurrent_results['success_rate']}%")
    print(f"🏆 Concurrent efficiency: {concurrent_results['concurrent_efficiency']}%")
    
    # Test 4: Memory usage analysis
    print("\n4. Memory Usage Analysis")
    print("-" * 30)
    
    memory_results = analyze_memory_usage()
    system_memory = memory_results.get("system_memory", {})
    optimization = memory_results.get("memory_optimization", {})
    
    print(f"💻 System memory usage: {system_memory.get('percent_used', 0)}%")
    print(f"🧠 String interning hit rate: {optimization.get('string_interning', {}).get('hit_rate', 0)}%")
    print(f"♻️ Memory pool reuse rate: {optimization.get('memory_pool', {}).get('reuse_rate', 0)}%")
    print(f"💰 Estimated savings: {memory_results.get('performance_data_summary', {}).get('total_estimated_savings_mb', 0)} MB")
    
    # Test 5: Operations benchmark
    print("\n5. Operations Benchmark")
    print("-" * 30)
    
    benchmark_results = benchmark_operations()
    benchmarks = benchmark_results.get("benchmarks", {})
    
    for operation, results in benchmarks.items():
        if "error" not in results:
            print(f"🔧 {operation}: {results.get('ops_per_second', 0)} ops/sec")
        else:
            print(f"❌ {operation}: {results['error']}")
    
    print(f"\n🏆 Overall performance score: {benchmark_results.get('performance_score', 0)}")
    
    return {
        "checkpoint_stress": checkpoint_results,
        "cache_performance": cache_results,
        "concurrent_users": concurrent_results,
        "memory_analysis": memory_results,
        "operations_benchmark": benchmark_results
    }


async def run_integration_test():
    """Run a comprehensive integration test."""
    
    print("🔧 Running Integration Test")
    print("=" * 40)
    
    # Create agent with test configuration
    temp_dir = tempfile.mkdtemp()
    
    try:
        config = {
            "memory": {
                "backend": "chromadb",
                "chromadb": {
                    "path": os.path.join(temp_dir, "integration_test"),
                    "max_connections": 10,
                    "min_connections": 2,
                    "l1_cache_size": 1000,
                    "batch_size": 20,
                    "enable_batch_processing": True,
                    "enable_metrics": True
                }
            },
            "resource_limits": {
                "max_memory_mb": 256,
                "max_connections": 10,
                "max_concurrent_operations": 50
            }
        }
        
        agent = AdvancedMemoryAgent(config)
        await agent.initialize()
        
        print("✅ Agent initialized")
        
        # Test scenario: Multiple users having conversations
        users = ["alice", "bob", "charlie"]
        conversations = [
            ("alice", "Hello, I'm Alice and I love programming"),
            ("bob", "Hi, I'm Bob and I enjoy hiking"),
            ("charlie", "Hey, I'm Charlie and I like cooking"),
            ("alice", "Do you remember what I like?"),
            ("bob", "What do you know about my hobbies?"),
            ("charlie", "Can you recall my interests?"),
            ("alice", "I also enjoy reading books about AI"),
            ("bob", "I went hiking last weekend"),
            ("charlie", "I cooked a delicious pasta yesterday")
        ]
        
        results = []
        
        for user, message in conversations:
            print(f"💬 {user}: {message}")
            
            result = await agent.chat(message, user, f"{user}_thread")
            results.append(result)
            
            print(f"🤖 Agent: {result['response'][:100]}...")
            print(f"⏱️ Processing time: {result['processing_time_ms']}ms")
            print()
            
            # Small delay to simulate real conversation
            await asyncio.sleep(0.1)
        
        # Get final statistics
        final_stats = await agent.get_comprehensive_stats()
        
        print("📊 Final Statistics:")
        print(f"Conversations: {final_stats['agent_info']['conversation_count']}")
        print(f"Uptime: {final_stats['agent_info']['uptime_seconds']:.2f}s")
        print(f"System Health: {'✅' if final_stats['health']['healthy'] else '❌'}")
        
        # Check memory optimization effectiveness
        memory_opt = final_stats.get("memory_optimization", {})
        string_hit_rate = memory_opt.get("string_intern", {}).get("hit_rate", 0)
        pool_reuse_rate = memory_opt.get("memory_pool", {}).get("reuse_rate", 0)
        
        print(f"String Interning: {string_hit_rate * 100:.1f}% hit rate")
        print(f"Memory Pool: {pool_reuse_rate * 100:.1f}% reuse rate")
        
        # Cleanup
        await agent.cleanup()
        
        print("\n🎉 Integration test completed successfully!")
        
        return {
            "conversations_completed": len(results),
            "final_stats": final_stats,
            "success": True
        }
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return {
            "error": str(e),
            "success": False
        }
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


async def main():
    """Run all tests."""
    
    print("🧪 Advanced Memory Agent Test Suite")
    print("=" * 60)
    print("Testing high-performance memory system with:")
    print("- Adaptive resource management")
    print("- Performance monitoring")
    print("- Memory optimization")
    print("- Circuit breaker patterns")
    print()
    
    try:
        # Create test suite instance
        test_suite = TestAdvancedMemoryAgent()
        
        # Run unit tests first
        unit_test_success = await test_suite.run_unit_tests()
        
        print("\n" + "=" * 60)
        
        # Run performance tests
        performance_results = await run_performance_tests()
        
        print("\n" + "=" * 60)
        
        # Run integration test
        integration_results = await run_integration_test()
        
        print("\n" + "=" * 60)
        print("📋 Test Summary")
        print("-" * 20)
        
        # Performance test summary
        checkpoint_success = performance_results["checkpoint_stress"]["success_rate"] > 90
        cache_efficiency = performance_results["cache_performance"]["actual_hit_ratio"] > 0.5
        concurrent_success = performance_results["concurrent_users"]["success_rate"] > 90
        
        print(f"Unit Tests: {'✅' if unit_test_success else '❌'}")
        print(f"Checkpoint Stress Test: {'✅' if checkpoint_success else '❌'}")
        print(f"Cache Performance: {'✅' if cache_efficiency else '❌'}")
        print(f"Concurrent Operations: {'✅' if concurrent_success else '❌'}")
        print(f"Integration Test: {'✅' if integration_results['success'] else '❌'}")
        
        # Overall assessment
        all_passed = all([unit_test_success, checkpoint_success, cache_efficiency, concurrent_success, integration_results['success']])
        
        print(f"\n🏆 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    # Run the test suite
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
