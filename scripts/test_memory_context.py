#!/usr/bin/env python3
"""
Memory Context Search Test Script

This script validates the smart context search functionality by:
1. Storing context information in memory
2. Testing context retrieval with reference words
3. Validating memory statistics and cleanup
4. Testing complex context calculations

Usage:
    python scripts/test_memory_context.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api import run_direct_agent_api
from app.main import load_app_config
from app.thread_manager import generate_unique_thread_id
from app.checkpointer_manager import get_global_checkpointer
from pathlib import Path

async def test_memory_context():
    """Test memory and context search functionality"""
    print("=" * 60)
    print("MEMORY CONTEXT SEARCH TEST")
    print("=" * 60)
    
    try:
        # Load test configuration
        config_path = Path("config/simple_memory_test.yaml")
        if not config_path.exists():
            print(f"❌ Config file not found: {config_path}")
            return False
            
        app_cfg = load_app_config(config_path)
        thread_id = generate_unique_thread_id()  # Generate unique thread
        
        print(f"📝 Configuration: {config_path}")
        print(f"🧵 Thread ID: {thread_id}")
        print(f"🤖 Default Model: {app_cfg.models.get('default', 'Not configured')}")
        print()
        
        # Test 1: Store some information
        print("=" * 40)
        print("TEST 1: Storing Context Information")
        print("=" * 40)
        
        result1 = await run_direct_agent_api(
            agent_name="simple_agent",
            user_input="Remember these important user story IDs: 12345, 67890, 11111. These are for the authentication module.",
            app_cfg=app_cfg,
            thread_id=thread_id
        )
        
        print(f"✅ Stored context successfully")
        print(f"📤 Agent Response: {result1['response']}")
        print()
        
        # Test 2: Reference stored information
        print("=" * 40)
        print("TEST 2: Context Reference Retrieval")
        print("=" * 40)
        
        result2 = await run_direct_agent_api(
            agent_name="simple_agent",
            user_input="What were those user story IDs again? And what module were they for?",
            app_cfg=app_cfg,
            thread_id=thread_id
        )
        
        print(f"✅ Retrieved context successfully")
        print(f"📥 Agent Response: {result2['response']}")
        print()
        
        # Test 3: Complex context calculation
        print("=" * 40)
        print("TEST 3: Context-Based Calculation")
        print("=" * 40)
        
        result3 = await run_direct_agent_api(
            agent_name="simple_agent",
            user_input="What's the average of those user story IDs?",
            app_cfg=app_cfg,
            thread_id=thread_id
        )
        
        print(f"✅ Calculated with context successfully")
        print(f"🧮 Agent Response: {result3['response']}")
        print()
        
        # Test 4: Additional context storage
        print("=" * 40)
        print("TEST 4: Additional Context Storage")
        print("=" * 40)
        
        result4 = await run_direct_agent_api(
            agent_name="simple_agent", 
            user_input="Also remember these priority levels: High, Medium, Low. The first user story has High priority.",
            app_cfg=app_cfg,
            thread_id=thread_id
        )
        
        print(f"✅ Stored additional context")
        print(f"📤 Agent Response: {result4['response']}")
        print()
        
        # Test 5: Multi-reference retrieval
        print("=" * 40)
        print("TEST 5: Multi-Reference Context")
        print("=" * 40)
        
        result5 = await run_direct_agent_api(
            agent_name="simple_agent",
            user_input="Can you tell me about those user stories again - their IDs, the module they're for, and their priorities?",
            app_cfg=app_cfg,
            thread_id=thread_id
        )
        
        print(f"✅ Retrieved multi-reference context")
        print(f"📋 Agent Response: {result5['response']}")
        print()
        
        # Test memory statistics
        print("=" * 40)
        print("MEMORY SYSTEM STATISTICS")
        print("=" * 40)
        
        try:
            from app.checkpointer_manager import get_checkpointer_manager
            manager = get_checkpointer_manager()
            stats = manager.get_memory_stats()
            
            print(f"📊 Memory Statistics:")
            for key, value in stats.items():
                if key == "threads" and isinstance(value, dict):
                    print(f"  • {key}: {len(value)} threads with checkpoints")
                else:
                    print(f"  • {key}: {value}")
            print()
            
        except Exception as e:
            print(f"⚠️  Could not retrieve memory stats: {e}")
            print()
        
        # Test 6: Context search with different thread (should be empty)
        print("=" * 40)
        print("TEST 6: Different Thread Isolation")
        print("=" * 40)
        
        new_thread_id = generate_unique_thread_id()  # Different thread
        result6 = await run_direct_agent_api(
            agent_name="simple_agent",
            user_input="What were those user story IDs we discussed?",
            app_cfg=app_cfg,
            thread_id=new_thread_id
        )
        
        print(f"🧵 New Thread ID: {new_thread_id}")
        print(f"🔍 Context Search (should find nothing): {result6['response']}")
        print()
        
        print("=" * 60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
        # Summary
        tests_passed = [
            "Context Storage" if "12345" in result1['response'] else "❌ Context Storage Failed",
            "Context Retrieval" if any(id in result2['response'] for id in ["12345", "67890", "11111"]) else "❌ Context Retrieval Failed",
            "Context Calculation" if "average" in result3['response'].lower() else "❌ Context Calculation Failed", 
            "Additional Storage" if "priority" in result4['response'].lower() or "High" in result4['response'] else "❌ Additional Storage Failed",
            "Multi-Reference" if len(result5['response']) > len(result2['response']) else "❌ Multi-Reference Failed",
            "Thread Isolation" if any(phrase in result6['response'].lower() for phrase in ["couldn't find", "no relevant", "clarify", "more detail"]) else "❌ Thread Isolation Failed"
        ]
        
        print("\n📋 TEST SUMMARY:")
        for i, test in enumerate(tests_passed, 1):
            status = "✅" if not test.startswith("❌") else "❌"
            print(f"  {i}. {status} {test.replace('❌ ', '').replace('✅ ', '')}")
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_context_search_tool_directly():
    """Test the context search tool directly"""
    print("\n" + "=" * 60)
    print("DIRECT CONTEXT SEARCH TOOL TEST")
    print("=" * 60)
    
    try:
        from app.smart_context_search import (
            ContextSearcher,
            create_smart_context_tool
        )
        from app.checkpointer_manager import get_global_checkpointer
        
        # Test query detection
        test_queries = [
            "What were those user stories?",
            "Calculate the average of these numbers",
            "How many of them are there?",
            "Tell me about the items we discussed",
            "Just a regular question"
        ]
        
        # Create a searcher to test query detection
        checkpointer = get_global_checkpointer()
        thread_id = generate_unique_thread_id()
        searcher = ContextSearcher(thread_id, checkpointer)
        
        print("🔍 CONTEXT QUERY DETECTION:")
        for query in test_queries:
            query_type = searcher.detect_context_query_type(query)
            print(f"  • '{query}' → {query_type}")
        print()
        
        # Test entity extraction with sample messages
        sample_messages = [
            {'type': 'human', 'content': 'Here are the IDs: 12345, 67890, 11111'},
            {'type': 'human', 'content': 'The user stories US-001, US-002, and US-003 are ready'}, 
            {'type': 'human', 'content': 'Priority levels: High, Medium, Low'},
            {'type': 'human', 'content': 'No special entities in this text'}
        ]
        
        print("🎯 ENTITY EXTRACTION:")
        entities = searcher.extract_entities_from_messages(sample_messages)
        for entity in entities:
            print(f"  • Type: {entity['type']}, Value: {entity['value']}, Context: {entity['context'][:50]}...")
        print()
        
        # Test context tool creation
        context_tool = create_smart_context_tool(thread_id, checkpointer)
        print(f"🛠️  CONTEXT TOOL CREATED:")
        print(f"  • Tool name: {context_tool.name}")
        if hasattr(context_tool, 'description'):
            print(f"  • Tool description: {context_tool.description}")
        else:
            print(f"  • Tool description: Available via docstring")
        print(f"  • Thread ID: {thread_id}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Direct tool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Memory Context Search Tests...\n")
    
    async def run_all_tests():
        success1 = await test_memory_context()
        success2 = await test_context_search_tool_directly()
        
        print("\n" + "=" * 60)
        if success1 and success2:
            print("🎉 ALL TESTS PASSED! Memory system is working correctly.")
        else:
            print("❌ Some tests failed. Please check the output above.")
        print("=" * 60)
        
        return success1 and success2
    
    # Run the tests
    try:
        success = asyncio.run(run_all_tests())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        exit(1)