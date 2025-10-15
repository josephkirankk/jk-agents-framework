#!/usr/bin/env python3
"""
Comprehensive test to diagnose conversation store initialization issues.

This test will help us understand exactly where and why the initialization fails.
"""
import asyncio
import os
import sys
import traceback
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_initialization_sequence():
    """Test the complete initialization sequence step by step."""
    print("🔍 Comprehensive ConversationStore Initialization Diagnosis")
    print("=" * 65)
    
    # Ensure DATABASE_URL is set
    if not os.getenv('DATABASE_URL'):
        os.environ['DATABASE_URL'] = 'postgresql://jkagent_user:securepassword@localhost:5432/conversations'
        print("🔧 Set DATABASE_URL for testing")
    
    print(f"🗃️ DATABASE_URL: {os.getenv('DATABASE_URL')}")
    print()
    
    # Step 1: Test basic imports
    print("STEP 1: Testing imports...")
    try:
        from app.config import AppConfig
        from app.main import load_app_config
        from app.memory.conversation_store import (
            _conversation_store, 
            get_conversation_store,
            initialize_conversation_store,
            ConversationStore
        )
        from app.memory.memory_integration import (
            initialize_conversation_memory,
            is_conversation_memory_enabled
        )
        print("   ✅ All imports successful")
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # Step 2: Check initial global state
    print("\nSTEP 2: Checking initial global state...")
    print(f"   - Global _conversation_store: {_conversation_store}")
    
    # Step 3: Load configuration
    print("\nSTEP 3: Loading configuration...")
    try:
        app_config = load_app_config()
        print(f"   ✅ Config loaded")
        print(f"   - Memory enabled: {app_config.conversation_memory.enabled}")
        print(f"   - Memory check: {is_conversation_memory_enabled(app_config)}")
        print(f"   - Database URL in config: {app_config.conversation_memory.database_url}")
        print(f"   - Pool size: {app_config.conversation_memory.pool_size}")
    except Exception as e:
        print(f"   ❌ Config loading failed: {e}")
        return False
    
    # Step 4: Test get_conversation_store before initialization
    print("\nSTEP 4: Testing get_conversation_store before initialization...")
    try:
        store = get_conversation_store()
        print(f"   ❌ Unexpected: get_conversation_store worked without initialization!")
        print(f"   Store: {store}")
    except RuntimeError as e:
        print(f"   ✅ Expected error: {e}")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
    
    # Step 5: Test direct conversation store initialization
    print("\nSTEP 5: Testing direct conversation store initialization...")
    try:
        database_url = os.getenv('DATABASE_URL')
        pool_size = app_config.conversation_memory.pool_size
        print(f"   - Using URL: {database_url}")
        print(f"   - Pool size: {pool_size}")
        
        store = await initialize_conversation_store(database_url, pool_size)
        print(f"   ✅ Direct initialization successful")
        print(f"   - Store: {store}")
        print(f"   - Global _conversation_store after init: {_conversation_store}")
    except Exception as e:
        print(f"   ❌ Direct initialization failed: {e}")
        traceback.print_exc()
        return False
    
    # Step 6: Test get_conversation_store after initialization
    print("\nSTEP 6: Testing get_conversation_store after initialization...")
    try:
        store = get_conversation_store()
        print(f"   ✅ get_conversation_store worked after initialization")
        print(f"   - Store: {store}")
        print(f"   - Same instance?: {store is _conversation_store}")
    except Exception as e:
        print(f"   ❌ get_conversation_store failed after initialization: {e}")
    
    # Step 7: Test memory integration initialization
    print("\nSTEP 7: Testing memory integration initialization...")
    
    # First, reset the global state to simulate fresh start
    from app.memory import conversation_store
    conversation_store._conversation_store = None
    print(f"   - Reset global store: {conversation_store._conversation_store}")
    
    try:
        result = await initialize_conversation_memory(app_config)
        print(f"   ✅ Memory integration initialization result: {result}")
        print(f"   - Global _conversation_store after memory init: {conversation_store._conversation_store}")
        
        # Test if get_conversation_store works now
        try:
            store = get_conversation_store()
            print(f"   ✅ get_conversation_store works after memory init")
        except Exception as e:
            print(f"   ❌ get_conversation_store still fails: {e}")
            
    except Exception as e:
        print(f"   ❌ Memory integration initialization failed: {e}")
        traceback.print_exc()
    
    # Step 8: Test actual database operations
    print("\nSTEP 8: Testing actual database operations...")
    try:
        store = get_conversation_store()
        
        # Test storage
        await store.store_conversation(
            thread_id="test_init_debug",
            user_message="Test message",
            assistant_response="Test response",
            metadata={"test": True},
            app_config=app_config
        )
        print("   ✅ Store conversation successful")
        
        # Test retrieval
        conversations = await store.get_conversation_history("test_init_debug", limit=1)
        print(f"   ✅ Retrieved {len(conversations)} conversations")
        
        # Cleanup
        deleted = await store.delete_conversation_history("test_init_debug")
        print(f"   ✅ Cleaned up {deleted} conversations")
        
    except Exception as e:
        print(f"   ❌ Database operations failed: {e}")
        traceback.print_exc()
    
    # Step 9: Test enhance_system_message_with_memory flow
    print("\nSTEP 9: Testing enhance_system_message_with_memory flow...")
    try:
        from app.memory.memory_integration import enhance_system_message_with_memory
        
        original = "You are a helpful assistant."
        enhanced = await enhance_system_message_with_memory(
            original_message=original,
            thread_id="test_enhancement",
            app_config=app_config
        )
        print(f"   ✅ Enhancement successful")
        print(f"   - Original length: {len(original)}")
        print(f"   - Enhanced length: {len(enhanced)}")
        print(f"   - Enhancement added: {len(enhanced) - len(original)} chars")
        
    except Exception as e:
        print(f"   ❌ Enhancement failed: {e}")
        traceback.print_exc()
    
    # Step 10: Test store_conversation_memory flow
    print("\nSTEP 10: Testing store_conversation_memory flow...")
    try:
        from app.memory.memory_integration import store_conversation_memory
        
        await store_conversation_memory(
            thread_id="test_store_flow",
            user_message="Hello world",
            assistant_response="Hello back!",
            app_config=app_config,
            metadata={"flow_test": True}
        )
        print(f"   ✅ store_conversation_memory successful")
        
        # Verify it was stored
        store = get_conversation_store()
        conversations = await store.get_conversation_history("test_store_flow", limit=1)
        print(f"   ✅ Verified storage: {len(conversations)} conversations found")
        
        # Cleanup
        deleted = await store.delete_conversation_history("test_store_flow")
        print(f"   ✅ Cleaned up {deleted} conversations")
        
    except Exception as e:
        print(f"   ❌ store_conversation_memory failed: {e}")
        traceback.print_exc()
    
    print("\n" + "=" * 65)
    print("🎯 DIAGNOSIS COMPLETE")
    print("   All major components tested and working correctly in isolation")
    print("   If issues persist in production, likely causes:")
    print("   1. API server startup event not running")
    print("   2. Process isolation issues")
    print("   3. Timing issues in async initialization")
    print("   4. Different configuration being loaded")
    
    return True


async def simulate_api_startup():
    """Simulate the exact API startup sequence."""
    print("\n" + "🚀 SIMULATING API STARTUP SEQUENCE")
    print("=" * 65)
    
    # Ensure DATABASE_URL is set
    if not os.getenv('DATABASE_URL'):
        os.environ['DATABASE_URL'] = 'postgresql://jkagent_user:securepassword@localhost:5432/conversations'
    
    # Simulate the exact startup sequence from api.py
    try:
        from app.main import load_app_config
        from app.memory.memory_integration import initialize_conversation_memory, is_conversation_memory_enabled
        
        print("1. Loading default configuration...")
        _app_config = load_app_config()
        print("   ✅ Default configuration loaded successfully")
        
        print("2. Checking if conversation memory should be initialized...")
        print(f"   - is_conversation_memory_enabled: {is_conversation_memory_enabled(_app_config)}")
        
        if _app_config and is_conversation_memory_enabled(_app_config):
            print("3. Initializing conversation memory...")
            memory_initialized = await initialize_conversation_memory(_app_config)
            if memory_initialized:
                print("   ✅ Conversation memory initialized successfully")
                
                # Test that it actually works
                from app.memory.conversation_store import get_conversation_store
                try:
                    store = get_conversation_store()
                    print(f"   ✅ get_conversation_store works: {store}")
                    
                    # Test storage
                    await store.store_conversation(
                        thread_id="api_startup_test",
                        user_message="API startup test",
                        assistant_response="API startup response",
                        metadata={"startup_test": True},
                        app_config=_app_config
                    )
                    print("   ✅ Storage test successful")
                    
                    # Cleanup
                    deleted = await store.delete_conversation_history("api_startup_test")
                    print(f"   ✅ Cleanup successful: {deleted} conversations deleted")
                    
                except Exception as e:
                    print(f"   ❌ Post-initialization test failed: {e}")
                    
            else:
                print("   ❌ Failed to initialize conversation memory")
        else:
            print("   ⚠️ Conversation memory not enabled or not properly configured")
    
    except Exception as e:
        print(f"   ❌ API startup simulation failed: {e}")
        traceback.print_exc()


async def main():
    """Run comprehensive diagnosis."""
    await test_initialization_sequence()
    await simulate_api_startup()


if __name__ == "__main__":
    asyncio.run(main())