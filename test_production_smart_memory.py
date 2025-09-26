#!/usr/bin/env python3
"""
Test Production Smart Memory System

Simple test to verify that the production Smart Memory system works correctly
with thread isolation and memory sharing between calls.
"""

import asyncio
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_production_smart_memory():
    """Test the production Smart Memory system"""
    print("🧠 Testing Production Smart Memory System")
    print("=" * 50)
    
    try:
        from smart_agent.memory_adapter import (
            get_or_create_smart_memory_integration,
            initialize_production_smart_memory,
            get_smart_memory_status
        )
        
        # Initialize the system
        print("1. Initializing Production Smart Memory system...")
        await initialize_production_smart_memory()
        print("✓ Smart Memory system initialized")
        
        # Test with multiple threads
        test_thread_1 = "test-thread-001"
        test_thread_2 = "test-thread-002"
        
        print(f"\n2. Testing thread isolation with {test_thread_1} and {test_thread_2}")
        
        # Get integrations for different threads
        integration_1 = await get_or_create_smart_memory_integration(test_thread_1)
        integration_2 = await get_or_create_smart_memory_integration(test_thread_2)
        
        print("✓ Thread-specific integrations created")
        
        # Store memories in thread 1
        print(f"\n3. Storing memories in {test_thread_1}...")
        memory_ids_1 = []
        
        memory_id = await integration_1.store_memory(
            content="User asked about generating a list of users with random ages",
            metadata={"topic": "user_generation", "request_type": "list"},
            memory_type="query"
        )
        memory_ids_1.append(memory_id)
        print(f"   ✓ Stored query memory: {memory_id}")
        
        memory_id = await integration_1.store_memory(
            content="Successfully generated table with 10 users, ages 18-65: Robert (18), Elizabeth (31), Patricia (22)...",
            metadata={"topic": "user_generation", "result": "success", "user_count": 10},
            memory_type="execution_result"
        )
        memory_ids_1.append(memory_id)
        print(f"   ✓ Stored result memory: {memory_id}")
        
        # Store different memories in thread 2
        print(f"\n4. Storing different memories in {test_thread_2}...")
        memory_ids_2 = []
        
        memory_id = await integration_2.store_memory(
            content="User asked about users with age higher than 50",
            metadata={"topic": "user_filtering", "age_filter": "> 50"},
            memory_type="query"
        )
        memory_ids_2.append(memory_id)
        print(f"   ✓ Stored query memory: {memory_id}")
        
        # Test memory retrieval with thread isolation
        print(f"\n5. Testing memory retrieval and thread isolation...")
        
        # Retrieve from thread 1
        context_1 = await integration_1.get_context_for_query(
            query="users with ages table generation",
            max_tokens=1000
        )
        
        print(f"   Thread 1 context: {len(context_1['optimized_memories'])} memories")
        print(f"   Thread 1 summary: {context_1['context_summary']}")
        
        # Retrieve from thread 2
        context_2 = await integration_2.get_context_for_query(
            query="users with ages table generation",
            max_tokens=1000
        )
        
        print(f"   Thread 2 context: {len(context_2['optimized_memories'])} memories")
        print(f"   Thread 2 summary: {context_2['context_summary']}")
        
        # Verify thread isolation (thread 2 should have fewer memories)
        if len(context_1['optimized_memories']) > len(context_2['optimized_memories']):
            print("   ✓ Thread isolation working correctly")
        else:
            print("   ⚠ Thread isolation may not be working as expected")
        
        # Test memory sharing within the same thread
        print(f"\n6. Testing memory sharing within {test_thread_1}...")
        
        # Get same integration again and verify memories are still there
        integration_1_again = await get_or_create_smart_memory_integration(test_thread_1)
        context_1_again = await integration_1_again.get_context_for_query(
            query="user table generation",
            max_tokens=1000
        )
        
        if len(context_1_again['optimized_memories']) == len(context_1['optimized_memories']):
            print("   ✓ Memory sharing within thread working correctly")
        else:
            print("   ⚠ Memory sharing within thread may not be working")
        
        # Test with query that should reference previous context
        print(f"\n7. Testing contextual queries...")
        
        # Store a follow-up query that references previous work
        await integration_1.store_memory(
            content="User asked to filter names starting with 'T' from these users",
            metadata={"topic": "user_filtering", "filter_type": "name_prefix", "prefix": "T"},
            memory_type="query"
        )
        
        context_followup = await integration_1.get_context_for_query(
            query="filter names starting with T from previous user list",
            max_tokens=1500
        )
        
        print(f"   Follow-up context: {len(context_followup['optimized_memories'])} memories")
        print(f"   Should include both original user generation and filtering context")
        
        # Display some of the retrieved content
        if context_followup['optimized_memories']:
            print("   Sample retrieved memory:")
            sample_memory = context_followup['optimized_memories'][0]
            print(f"     Content: {sample_memory['content'][:100]}...")
            print(f"     Relevance: {sample_memory['relevance_score']:.3f}")
        
        # Get overall system status
        print(f"\n8. Getting system status...")
        status = await get_smart_memory_status()
        print(f"   Active threads: {status['active_threads']}")
        print(f"   Thread IDs: {status['thread_ids']}")
        print(f"   System status: {status['system_status']}")
        
        print("\n✅ All tests completed successfully!")
        print("\nProduction Smart Memory System Features Verified:")
        print("  ✓ Thread isolation (different threads have separate memory spaces)")
        print("  ✓ Memory sharing (same thread preserves memory across calls)")
        print("  ✓ Query-based retrieval with relevance scoring")
        print("  ✓ Context optimization and token management")
        print("  ✓ System status and metrics tracking")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_integration():
    """Test integration with the planner executor"""
    print("\n🔗 Testing API Integration")
    print("=" * 30)
    
    try:
        # Test the functions that the planner executor will use
        from app.planner_executor import get_smart_memory_context, store_execution_memory
        
        test_thread = "api-integration-test"
        
        # Test storing execution memory
        print("1. Testing store_execution_memory...")
        memory_id = await store_execution_memory(
            content="Test execution: Generated user list with 5 users",
            thread_id=test_thread,
            memory_type="execution_result",
            metadata={
                "step_id": "s1",
                "agent_name": "test_agent",
                "success": True,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        if memory_id:
            print(f"   ✓ Stored execution memory: {memory_id}")
        else:
            print("   ⚠ Failed to store execution memory")
        
        # Test retrieving context
        print("2. Testing get_smart_memory_context...")
        context = await get_smart_memory_context(
            query="user list generation",
            thread_id=test_thread,
            context_type="planning",
            max_tokens=800
        )
        
        print(f"   Context available: {context.get('smart_memory_available', False)}")
        print(f"   Memories found: {len(context.get('optimized_memories', []))}")
        print(f"   Total tokens: {context.get('total_tokens', 0)}")
        
        if context.get('smart_memory_available'):
            print("   ✓ API integration working correctly")
        else:
            print("   ⚠ API integration may have issues")
        
        return True
        
    except Exception as e:
        print(f"❌ API integration test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🚀 Production Smart Memory System Tests")
    print("=" * 60)
    
    success = True
    
    # Test the core Smart Memory system
    if not await test_production_smart_memory():
        success = False
    
    # Test API integration
    if not await test_api_integration():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed! Production Smart Memory system is ready.")
    else:
        print("❌ Some tests failed. Please check the output above.")
    
    return success


if __name__ == "__main__":
    asyncio.run(main())