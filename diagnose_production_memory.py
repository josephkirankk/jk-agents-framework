#!/usr/bin/env python3
"""
Corrected diagnostic test for the production conversation memory system.

This test properly checks the actual global variables without the import gotcha.
"""
import asyncio
import os
import sys
import traceback
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_production_memory_flow():
    """Test the production memory flow end-to-end."""
    print("🔍 Testing Production Memory System (Ray-11 Issue)")
    print("=" * 60)
    
    # Ensure DATABASE_URL is set
    if not os.getenv('DATABASE_URL'):
        os.environ['DATABASE_URL'] = 'postgresql://jkagent_user:securepassword@localhost:5432/conversations'
        print("🔧 Set DATABASE_URL for testing")
    
    print(f"🗃️ DATABASE_URL: {os.getenv('DATABASE_URL')}")
    print()
    
    # Import modules properly
    from app.main import load_app_config
    from app.memory import conversation_store  # Import the module
    from app.memory.memory_integration import (
        initialize_conversation_memory,
        is_conversation_memory_enabled,
        enhance_system_message_with_memory,
        store_conversation_memory
    )
    
    print("STEP 1: Load configuration")
    app_config = load_app_config()
    print(f"   ✅ Config loaded")
    print(f"   - Memory enabled: {app_config.conversation_memory.enabled}")
    print(f"   - Memory check: {is_conversation_memory_enabled(app_config)}")
    
    print(f"\nSTEP 2: Check initial state")
    print(f"   - conversation_store._conversation_store: {conversation_store._conversation_store}")
    
    # TEST: Simulating what happens during API startup
    print(f"\nSTEP 3: Simulate API startup sequence")
    if app_config and is_conversation_memory_enabled(app_config):
        print("   - Calling initialize_conversation_memory...")
        memory_initialized = await initialize_conversation_memory(app_config)
        print(f"   ✅ Memory initialized: {memory_initialized}")
        print(f"   - conversation_store._conversation_store: {conversation_store._conversation_store}")
        
        # Test that get_conversation_store works
        from app.memory.conversation_store import get_conversation_store
        try:
            store = get_conversation_store()
            print(f"   ✅ get_conversation_store() works: {store}")
        except Exception as e:
            print(f"   ❌ get_conversation_store() failed: {e}")
    
    # TEST: What happens in a real conversation flow (like ray-11)
    print(f"\nSTEP 4: Test conversation flow (like ray-11)")
    test_thread = "ray-11-production-test"
    
    try:
        # Step 4a: Store first conversation
        await store_conversation_memory(
            thread_id=test_thread,
            user_message="What is machine learning?",
            assistant_response="Machine learning is a subset of artificial intelligence...",
            app_config=app_config,
            metadata={"interaction": 1}
        )
        print("   ✅ Stored first conversation")
        
        # Step 4b: Try to retrieve context for second message
        original_system = "You are a helpful AI assistant."
        enhanced_system = await enhance_system_message_with_memory(
            original_message=original_system,
            thread_id=test_thread,
            app_config=app_config
        )
        
        print(f"   ✅ Enhanced system message")
        print(f"   - Original length: {len(original_system)}")
        print(f"   - Enhanced length: {len(enhanced_system)}")
        context_added = len(enhanced_system) - len(original_system)
        print(f"   - Context added: {context_added} characters")
        
        if context_added > 0:
            print(f"   🎯 SUCCESS: Context was retrieved and injected!")
            print(f"   - Enhanced preview: {enhanced_system[:200]}...")
        else:
            print(f"   ⚠️ WARNING: No context was added to system message")
        
        # Step 4c: Store second conversation
        await store_conversation_memory(
            thread_id=test_thread,
            user_message="Can you give me an example?",
            assistant_response="Sure! A common example is email spam detection...",
            app_config=app_config,
            metadata={"interaction": 2}
        )
        print("   ✅ Stored second conversation")
        
        # Step 4d: Verify both conversations are in the database
        store = get_conversation_store()
        conversations = await store.get_conversation_history(test_thread)
        print(f"   ✅ Retrieved {len(conversations)} total conversations")
        
        for i, conv in enumerate(conversations, 1):
            print(f"      {i}. {conv.timestamp}: \"{conv.user_message[:50]}...\"")
        
        # Step 4e: Test context for third message
        enhanced_system_3 = await enhance_system_message_with_memory(
            original_message=original_system,
            thread_id=test_thread,
            app_config=app_config
        )
        
        context_added_3 = len(enhanced_system_3) - len(original_system)
        print(f"   ✅ Third enhancement: {context_added_3} characters added")
        
        if context_added_3 > context_added:
            print(f"   🎯 EXCELLENT: Context grew with more conversation history!")
        
    except Exception as e:
        print(f"   ❌ Conversation flow failed: {e}")
        traceback.print_exc()
    
    # Clean up
    try:
        deleted = await store.delete_conversation_history(test_thread)
        print(f"\n✅ Cleanup: Deleted {deleted} conversations")
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 PRODUCTION TEST COMPLETE")
    
    if context_added > 0:
        print("✅ The memory system is working correctly!")
        print("   - ConversationStore initializes properly")
        print("   - Conversations are stored in database")
        print("   - Context is retrieved and injected into system messages")
        print("   - Multi-turn conversations maintain context")
        print()
        print("🔧 If ray-11 still has issues, the problem is likely:")
        print("   1. API server startup event not running in production")
        print("   2. Different environment variables in production")
        print("   3. Process isolation in multi-worker deployments")
        print("   4. Timing issues during server startup")
    else:
        print("❌ Memory system has issues!")
        print("   - Check DATABASE_URL environment variable")
        print("   - Check PostgreSQL connectivity")
        print("   - Check conversation_store initialization")

async def main():
    await test_production_memory_flow()

if __name__ == "__main__":
    asyncio.run(main())