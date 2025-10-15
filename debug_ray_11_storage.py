#!/usr/bin/env python3
"""
Debug script to understand why ray-11 conversations are not being stored in database.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.memory.memory_integration import store_conversation_memory
from app.memory.conversation_store import get_conversation_store
from app.main import load_app_config

async def test_ray_11_storage():
    """Test exactly what ray-11 was trying to store."""
    print("🔍 Debugging ray-11 storage issue...")
    
    # Ensure DATABASE_URL is set
    if not os.getenv('DATABASE_URL'):
        os.environ['DATABASE_URL'] = 'postgresql://jkagent_user:securepassword@localhost:5432/conversations'
    
    app_config = load_app_config()
    thread_id = "ray-11-debug"
    
    # Test 1: Direct conversation store
    print("\n1. Testing direct conversation store...")
    try:
        store = get_conversation_store()
        await store.store_conversation(
            thread_id=thread_id,
            user_message="print 10 random from 1 to 100",
            assistant_response="Here is a list of 10 random integers between 1 and 100 (inclusive):\n\n[10, 77, 24, 56, 20, 53, 34, 9, 3, 9]",
            metadata={"execution_type": "supervised"},
            app_config=app_config
        )
        print("   ✅ Direct store successful")
    except Exception as e:
        print(f"   ❌ Direct store failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Memory integration store
    print("\n2. Testing memory integration store...")
    try:
        await store_conversation_memory(
            thread_id=thread_id,
            user_message="get random 3 from this",
            assistant_response="Here are 3 random elements selected from the given list: [53, 77, 24]",
            app_config=app_config,
            metadata={"execution_type": "supervised"}
        )
        print("   ✅ Memory integration store successful")
    except Exception as e:
        print(f"   ❌ Memory integration store failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Check what was actually stored
    print("\n3. Checking what was actually stored...")
    try:
        conversations = await store.get_conversation_history(thread_id, limit=10)
        print(f"   Found {len(conversations)} conversations:")
        for i, conv in enumerate(conversations, 1):
            print(f"   {i}. {conv.user_message} -> {conv.assistant_response[:50]}...")
    except Exception as e:
        print(f"   ❌ Failed to retrieve: {e}")
    
    # Test 4: Now try to retrieve context to see if it works
    print("\n4. Testing context retrieval...")
    try:
        from app.memory.context_enhancer import get_context_enhancer
        enhancer = get_context_enhancer()
        context = await enhancer.get_conversation_context(
            thread_id=thread_id,
            max_conversations=5,
            max_length=2000,
            app_config=app_config
        )
        print(f"   Context length: {len(context)} chars")
        if context:
            print(f"   Context preview: {context[:100]}...")
        else:
            print("   ❌ No context retrieved")
    except Exception as e:
        print(f"   ❌ Context retrieval failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    try:
        await store.delete_conversation_history(thread_id)
        print(f"\n🧹 Cleaned up test data for {thread_id}")
    except Exception as e:
        print(f"\n⚠️ Cleanup failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_ray_11_storage())