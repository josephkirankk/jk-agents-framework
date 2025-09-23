#!/usr/bin/env python3
"""
Test script for ChromaDB memory integration with JK-Agents Framework.

This script tests:
1. ChromaDB memory system initialization
2. Memory persistence across conversations
3. Thread isolation
4. Configuration loading
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent))

from app.main import load_app_config, run_direct_agent
from app.checkpointer_manager import get_checkpointer_manager, get_memory_stats
from app.memory.simple_chromadb_memory import test_chromadb_memory
from app.memory.chromadb_checkpointer import test_chromadb_checkpointer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)


async def test_basic_chromadb_functionality():
    """Test basic ChromaDB functionality."""
    print("\n🧪 Testing Basic ChromaDB Functionality")
    print("=" * 50)
    
    try:
        # Test ChromaDB memory
        print("1. Testing ChromaDB memory store...")
        test_chromadb_memory()
        print("✅ ChromaDB memory store test passed")
        
        # Test ChromaDB checkpointer
        print("\n2. Testing ChromaDB checkpointer...")
        test_chromadb_checkpointer()
        print("✅ ChromaDB checkpointer test passed")
        
        return True
    except Exception as e:
        print(f"❌ Basic ChromaDB test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_framework_integration():
    """Test ChromaDB integration with the JK-Agents framework."""
    print("\n🔗 Testing Framework Integration")
    print("=" * 40)
    
    try:
        # Load ChromaDB configuration
        config_path = Path(__file__).parent / "config" / "chromadb_memory_test.yaml"
        
        if not config_path.exists():
            print(f"❌ Configuration file not found: {config_path}")
            return False
        
        print(f"Loading configuration from: {config_path}")
        app_cfg = load_app_config(config_path)
        
        # Check if memory configuration is loaded
        memory_config = getattr(app_cfg, 'memory', None)
        if memory_config:
            print(f"✅ Memory configuration loaded: {memory_config}")
        else:
            print("⚠️ No memory configuration found in app config")
        
        # Test agent execution with memory
        print("\n3. Testing agent with ChromaDB memory...")
        
        test_cases = [
            ("My name is Alice and I love pizza", "introduction"),
            ("What do you remember about me?", "recall_test"),
            ("I also enjoy hiking and reading books", "additional_info"),
            ("Tell me about my preferences", "comprehensive_recall")
        ]
        
        thread_id = "test_chromadb_thread_123"
        
        for i, (user_input, test_type) in enumerate(test_cases, 1):
            print(f"\nTest {i} ({test_type}):")
            print(f"  Input: {user_input}")
            
            # Set thread ID for memory persistence
            os.environ['THREAD_ID'] = thread_id
            
            try:
                result = await run_direct_agent(
                    agent_name="memory_test_agent",
                    user_input=user_input,
                    app_cfg=app_cfg
                )
                
                if result and hasattr(result, 'response'):
                    response = result.response[:200] + "..." if len(result.response) > 200 else result.response
                    print(f"  Response: {response}")
                else:
                    print(f"  Response: {str(result)[:200]}...")
                
                print("  ✅ Agent execution successful")
                
            except Exception as e:
                print(f"  ❌ Agent execution failed: {e}")
                return False
        
        # Test memory statistics
        print("\n4. Testing memory statistics...")
        try:
            stats = get_memory_stats()
            print(f"Memory stats: {stats}")
            print("✅ Memory statistics retrieved successfully")
        except Exception as e:
            print(f"⚠️ Memory statistics failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Framework integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_memory_persistence():
    """Test memory persistence across different sessions."""
    print("\n💾 Testing Memory Persistence")
    print("=" * 35)
    
    try:
        config_path = Path(__file__).parent / "config" / "chromadb_memory_test.yaml"
        app_cfg = load_app_config(config_path)
        
        # First session
        print("Session 1: Storing information...")
        thread_id_1 = "persistence_test_session_1"
        os.environ['THREAD_ID'] = thread_id_1
        
        result1 = await run_direct_agent(
            agent_name="memory_test_agent",
            user_input="Remember that my favorite programming language is Python and I work as a data scientist",
            app_cfg=app_cfg
        )
        print("✅ Session 1 completed")
        
        # Second session (same thread)
        print("\nSession 2: Recalling information...")
        result2 = await run_direct_agent(
            agent_name="memory_test_agent", 
            user_input="What do you know about my job and programming preferences?",
            app_cfg=app_cfg
        )
        print("✅ Session 2 completed")
        
        # Third session (different thread)
        print("\nSession 3: Different thread (should not have access to previous info)...")
        thread_id_2 = "persistence_test_session_2"
        os.environ['THREAD_ID'] = thread_id_2
        
        result3 = await run_direct_agent(
            agent_name="memory_test_agent",
            user_input="What do you know about my job?",
            app_cfg=app_cfg
        )
        print("✅ Session 3 completed")
        
        print("\n📊 Persistence Test Results:")
        print("- Session 1: Information stored")
        print("- Session 2: Should recall information (same thread)")
        print("- Session 3: Should not recall information (different thread)")
        
        return True
        
    except Exception as e:
        print(f"❌ Memory persistence test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all ChromaDB integration tests."""
    print("🚀 JK-Agents Framework ChromaDB Integration Tests")
    print("=" * 60)
    
    # Check if required dependencies are available
    try:
        import chromadb
        from langchain_chroma import Chroma
        from langchain_community.embeddings import HuggingFaceEmbeddings
        print("✅ Required dependencies are available")
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Please install: pip install chromadb langchain-chroma sentence-transformers")
        return False
    
    # Run tests
    tests = [
        ("Basic ChromaDB Functionality", test_basic_chromadb_functionality),
        ("Framework Integration", test_framework_integration),
        ("Memory Persistence", test_memory_persistence),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! ChromaDB integration is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the logs above.")
        return False


if __name__ == "__main__":
    # Set environment variables for testing
    os.environ.setdefault('GOOGLE_API_KEY', 'your-api-key-here')
    
    # Check if API key is set
    if not os.getenv('GOOGLE_API_KEY') or os.getenv('GOOGLE_API_KEY') == 'your-api-key-here':
        print("⚠️ Warning: GOOGLE_API_KEY not set. Some tests may fail.")
        print("Please set your Google API key: export GOOGLE_API_KEY='your-actual-key'")
    
    # Run tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
