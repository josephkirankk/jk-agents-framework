#!/usr/bin/env python3
"""
Corrected debug script to investigate Ray-12 memory retrieval failure.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def debug_ray12_memory_issue():
    """Debug the Ray-12 memory retrieval issue step by step."""
    print("🔍 Debugging Ray-12 Memory Issue (CORRECTED)")
    print("=" * 50)
    
    # Set up environment
    if not os.getenv('DATABASE_URL'):
        os.environ['DATABASE_URL'] = 'postgresql://jkagent_user:securepassword@localhost:5432/conversations'
        print(f"🔧 Set DATABASE_URL: {os.environ['DATABASE_URL']}")
    
    # Step 1: Test basic database connection
    print("\nSTEP 1: Testing database connection...")
    try:
        from app.memory.conversation_store import get_conversation_store, initialize_conversation_store
        from app.main import load_app_config
        
        # Initialize conversation store
        database_url = os.environ['DATABASE_URL']
        store = await initialize_conversation_store(database_url, 10)
        print("   ✅ Database connection successful")
        
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False
    
    # Step 2: Check if Ray-12 conversations exist in database
    print("\nSTEP 2: Searching for Ray-12 conversations...")
    try:
        conversations = await store.get_conversation_history("ray-12", limit=10)
        print(f"   📊 Found {len(conversations)} conversations for thread 'ray-12'")
        
        # Also check for any conversations with similar thread IDs
        async with store._get_connection() as conn:
            # Check exact match
            count_query = "SELECT COUNT(*) FROM conversations WHERE thread_id = $1"
            exact_count = await conn.fetchval(count_query, "ray-12")
            print(f"   📊 Exact match count: {exact_count}")
            
            # Check for similar thread IDs
            like_query = "SELECT thread_id, COUNT(*) FROM conversations WHERE thread_id ILIKE $1 GROUP BY thread_id ORDER BY thread_id"
            like_rows = await conn.fetch(like_query, "%ray%")
            print(f"   📊 Thread IDs containing 'ray': {len(like_rows)}")
            for row in like_rows:
                print(f"      - {row['thread_id']}: {row['count']} conversations")
            
            # Get all thread IDs to see what's actually stored
            all_threads_query = "SELECT DISTINCT thread_id FROM conversations ORDER BY thread_id LIMIT 20"
            all_threads = await conn.fetch(all_threads_query)
            print(f"   📊 All thread IDs in database ({len(all_threads)} total):")
            for row in all_threads:
                print(f"      - '{row['thread_id']}'")
                
    except Exception as e:
        print(f"   ❌ Database query failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Test context enhancer directly (if conversations exist)
    print("\nSTEP 3: Testing context enhancer directly...")
    try:
        from app.memory.context_enhancer import ConversationContextEnhancer
        
        app_config = load_app_config()
        enhancer = ConversationContextEnhancer(store=store)
        
        print(f"   🔧 Created ConversationContextEnhancer")
        
        # Test get_conversation_context method
        context = await enhancer.get_conversation_context("ray-12", 5, 2000, app_config)
        print(f"   📝 Context retrieved: {len(context)} characters")
        
        if context:
            print(f"   📄 Context preview:")
            print(f"      {context[:500]}...")
        else:
            print(f"   ⚠️ No context returned from get_conversation_context")
            
    except Exception as e:
        print(f"   ❌ Context enhancer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Test with a thread that actually has data (if any exist)
    if len(all_threads) > 0:
        print("\nSTEP 4: Testing with an existing thread...")
        try:
            test_thread = all_threads[0]['thread_id']
            print(f"   🧪 Testing with thread: '{test_thread}'")
            
            # Get conversations for this thread
            test_conversations = await store.get_conversation_history(test_thread, limit=5)
            print(f"   📊 Found {len(test_conversations)} conversations")
            
            for i, conv in enumerate(test_conversations, 1):
                print(f"   {i}. {conv.timestamp}")
                print(f"      User: {conv.user_message}")
                print(f"      Assistant: {conv.assistant_response[:100]}...")
                print()
            
            # Test context enhancement for this thread
            context = await enhancer.get_conversation_context(test_thread, 5, 2000, app_config)
            print(f"   📝 Context for existing thread: {len(context)} characters")
            
            if context:
                print(f"   ✅ Context enhancement WORKS for existing thread!")
                print(f"   📄 Context preview:")
                print(f"      {context[:300]}...")
            else:
                print(f"   ❌ Context enhancement FAILED even for existing thread")
                
        except Exception as e:
            print(f"   ❌ Existing thread test failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Step 5: Investigate storage issue for ray-12
    print("\nSTEP 5: Investigating why ray-12 conversations were not stored...")
    
    # Check the memory log timestamps to understand the expected storage times
    print("   📋 Expected storage times from memory logs:")
    print("      - First conversation: 2025-09-27 13:31:27.857 (give me 10 random numbers)")
    print("      - Second conversation: 2025-09-27 13:32:08.976 (from this get 5 random numbers)")
    
    # Check if there are any conversations stored around those times
    try:
        async with store._get_connection() as conn:
            time_range_query = """
            SELECT thread_id, user_message, assistant_response, timestamp 
            FROM conversations 
            WHERE timestamp BETWEEN '2025-09-27 13:31:00' AND '2025-09-27 13:33:00'
            ORDER BY timestamp ASC
            """
            time_range_rows = await conn.fetch(time_range_query)
            print(f"   📊 Conversations stored in time range: {len(time_range_rows)}")
            
            for row in time_range_rows:
                print(f"      {row['timestamp']} [{row['thread_id']}]: {row['user_message'][:50]}...")
            
    except Exception as e:
        print(f"   ❌ Time range query failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 6: Test storage mechanism directly
    print("\nSTEP 6: Testing storage mechanism with ray-12...")
    try:
        # Try to store a test conversation for ray-12
        await store.store_conversation(
            thread_id="ray-12",
            user_message="Test storage for ray-12",
            assistant_response="This is a test response to verify storage works",
            metadata={"test": True}
        )
        print("   ✅ Test storage successful")
        
        # Immediately try to retrieve it
        test_conversations = await store.get_conversation_history("ray-12", limit=1)
        print(f"   📊 Retrieved {len(test_conversations)} test conversations")
        
        if len(test_conversations) > 0:
            print("   ✅ Storage and retrieval working correctly!")
            print("   🔍 This means the original ray-12 conversations were NEVER stored")
            print("   🚨 CONCLUSION: Storage failure in the original system, not retrieval failure")
        else:
            print("   ❌ Test storage/retrieval failed - deeper database issue")
        
        # Clean up test data
        await store.delete_conversation_history("ray-12")
        print("   🧹 Test data cleaned up")
        
    except Exception as e:
        print(f"   ❌ Storage test failed: {e}")
        import traceback
        traceback.print_exc()
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(debug_ray12_memory_issue())
        if success:
            print("\n🎯 Debug completed successfully")
        else:
            print("\n❌ Debug failed")
    except Exception as e:
        print(f"\n💥 Debug crashed: {e}")
        import traceback
        traceback.print_exc()