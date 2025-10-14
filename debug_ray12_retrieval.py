#!/usr/bin/env python3
"""
Debug script to investigate Ray-12 memory retrieval failure.
This will help identify exactly why context retrieval is not working.
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
    print("🔍 Debugging Ray-12 Memory Retrieval Issue")
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
    print("\nSTEP 2: Checking for Ray-12 conversations in database...")
    try:
        conversations = await store.get_conversation_history("ray-12", limit=10)
        print(f"   📊 Found {len(conversations)} conversations for thread 'ray-12'")
        
        for i, conv in enumerate(conversations, 1):
            print(f"   {i}. {conv.timestamp}")
            print(f"      User: {conv.user_message}")
            print(f"      Assistant: {conv.assistant_response[:100]}...")
            if conv.metadata:
                print(f"      Metadata: {conv.metadata}")
            print()
            
    except Exception as e:
        print(f"   ❌ Database query failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Test context enhancer directly
    print("\nSTEP 3: Testing context enhancer directly...")
    try:
        from app.memory.context_enhancer import ContextEnhancer
        
        app_config = load_app_config()
        enhancer = ContextEnhancer(
            max_conversations=5,
            max_context_length=2000,
            prepend=False
        )
        
        print(f"   🔧 Created ContextEnhancer:")
        print(f"      - max_conversations: 5")
        print(f"      - max_context_length: 2000")
        print(f"      - prepend: False")
        
        # Test get_conversation_context method
        context = await enhancer.get_conversation_context("ray-12", 5, 2000)
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
    
    # Step 4: Test system message enhancement
    print("\nSTEP 4: Testing system message enhancement...")
    try:
        original_message = "You are an AI system with Python code execution capabilities.\nUse the run_python_code tool for all computational tasks.\n"
        
        enhanced_message = await enhancer.enhance_system_message(
            original_message=original_message,
            thread_id="ray-12",
            max_conversations=5,
            max_length=2000
        )
        
        enhancement_added = len(enhanced_message) - len(original_message)
        print(f"   📊 Enhancement results:")
        print(f"      - Original length: {len(original_message)}")
        print(f"      - Enhanced length: {len(enhanced_message)}")
        print(f"      - Characters added: {enhancement_added}")
        
        if enhancement_added > 0:
            print(f"   ✅ Enhancement successful!")
            print(f"   📄 Enhanced message preview:")
            added_content = enhanced_message[len(original_message):]
            print(f"      Added content: {added_content[:300]}...")
        else:
            print(f"   ❌ No enhancement added - this is the problem!")
            
    except Exception as e:
        print(f"   ❌ System message enhancement failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 5: Test memory integration flow
    print("\nSTEP 5: Testing memory integration flow...")
    try:
        from app.memory.memory_integration import (
            enhance_system_message_with_memory,
            initialize_conversation_memory
        )
        
        # Initialize memory system
        memory_init = await initialize_conversation_memory(app_config)
        print(f"   🔧 Memory system initialized: {memory_init}")
        
        # Test enhancement
        original_message = "You are an AI system with Python code execution capabilities.\nUse the run_python_code tool for all computational tasks.\n"
        enhanced = await enhance_system_message_with_memory(
            original_message=original_message,
            thread_id="ray-12",
            app_config=app_config
        )
        
        enhancement_added = len(enhanced) - len(original_message)
        print(f"   📊 Memory integration results:")
        print(f"      - Characters added: {enhancement_added}")
        
        if enhancement_added > 0:
            print(f"   ✅ Memory integration working!")
        else:
            print(f"   ❌ Memory integration failing - matches log behavior")
            
    except Exception as e:
        print(f"   ❌ Memory integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 6: Investigate conversation store configuration
    print("\nSTEP 6: Investigating conversation store configuration...")
    try:
        print(f"   🔧 ConversationStore details:")
        print(f"      - Database URL: {store.database_url}")
        print(f"      - Pool size: {store.pool_size}")
        print(f"      - Connection pool: {store._pool}")
        
        # Test connection pool
        if store._pool:
            print(f"      - Pool status: Active")
            print(f"      - Pool size current: {store._pool.get_size()}")
            print(f"      - Pool max size: {store._pool.get_max_size()}")
        else:
            print(f"      - Pool status: Not initialized")
            
        # Test direct database query
        print(f"\n   🗄️ Testing direct database query...")
        async with store._get_connection() as conn:
            count_query = "SELECT COUNT(*) FROM conversations WHERE thread_id = $1"
            count = await conn.fetchval(count_query, "ray-12")
            print(f"      - Conversations in DB for ray-12: {count}")
            
            if count > 0:
                detail_query = """
                SELECT thread_id, user_message, assistant_response, timestamp 
                FROM conversations 
                WHERE thread_id = $1 
                ORDER BY timestamp ASC
                """
                rows = await conn.fetch(detail_query, "ray-12")
                print(f"      - Retrieved {len(rows)} rows:")
                for row in rows:
                    print(f"        {row['timestamp']}: {row['user_message'][:50]}...")
            
    except Exception as e:
        print(f"   ❌ Store configuration check failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 7: Final diagnosis
    print("\nSTEP 7: Final diagnosis...")
    
    if len(conversations) > 0:
        if enhancement_added > 0:
            print("   ✅ DIAGNOSIS: Memory system is working correctly")
            print("      The issue may be in the API layer or timing")
        else:
            print("   🔍 DIAGNOSIS: Data exists but enhancement is failing")
            print("      The issue is in the context enhancement logic")
            print("      Possible causes:")
            print("      - Context enhancer not retrieving from conversation store")
            print("      - Context formatting issues") 
            print("      - Configuration mismatch between storage and retrieval")
    else:
        print("   ❌ DIAGNOSIS: No conversations found in database")
        print("      The storage operation may not be working correctly")
        print("      Or thread ID mismatch between storage and retrieval")
    
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