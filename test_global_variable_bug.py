#!/usr/bin/env python3
"""
Simple test to isolate the global variable assignment issue in conversation_store.py
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_global_variable_assignment():
    """Test exactly what's happening with the global variable."""
    print("🔍 Testing Global Variable Assignment Bug")
    print("=" * 50)
    
    # Set DATABASE_URL
    if not os.getenv('DATABASE_URL'):
        os.environ['DATABASE_URL'] = 'postgresql://jkagent_user:securepassword@localhost:5432/conversations'
    
    # Import the conversation store module
    from app.memory import conversation_store
    
    print(f"1. Initial global _conversation_store: {conversation_store._conversation_store}")
    print(f"2. Module id: {id(conversation_store)}")
    print(f"3. Global variable id: {id(conversation_store._conversation_store)}")
    
    # Test direct access to the functions
    from app.memory.conversation_store import (
        _conversation_store,
        initialize_conversation_store, 
        get_conversation_store
    )
    
    print(f"4. Imported _conversation_store: {_conversation_store}")
    print(f"5. Same object? {_conversation_store is conversation_store._conversation_store}")
    
    # Now test initialization
    print(f"\n6. Calling initialize_conversation_store...")
    database_url = os.getenv('DATABASE_URL')
    store = await initialize_conversation_store(database_url, 10)
    
    print(f"7. Returned store: {store}")
    print(f"8. Global conversation_store._conversation_store after init: {conversation_store._conversation_store}")
    print(f"9. Imported _conversation_store after init: {_conversation_store}")
    
    # Check if they're the same object
    print(f"10. returned == global from module: {store is conversation_store._conversation_store}")
    print(f"11. returned == imported global: {store is _conversation_store}")
    print(f"12. module global == imported global: {conversation_store._conversation_store is _conversation_store}")
    
    # Test get_conversation_store
    try:
        retrieved_store = get_conversation_store()
        print(f"13. get_conversation_store() returned: {retrieved_store}")
        print(f"14. get_conversation_store() == returned: {retrieved_store is store}")
        print(f"15. get_conversation_store() == global: {retrieved_store is conversation_store._conversation_store}")
    except Exception as e:
        print(f"13. get_conversation_store() failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_global_variable_assignment())