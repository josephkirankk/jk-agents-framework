#!/usr/bin/env python3
"""
Debug script to test conversation memory storage and retrieval.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.simple_conversation_memory_fixed import (
    get_conversation_memory,
    inject_conversation_context,
    store_conversation_turn,
    get_conversation_context_metadata
)

def test_conversation_memory():
    """Test conversation memory storage and retrieval."""
    
    print("=" * 60)
    print("CONVERSATION MEMORY DEBUG TEST")
    print("=" * 60)
    
    # Test thread ID
    thread_id = "test-thread-12345"
    
    # Get memory instance
    memory = get_conversation_memory()
    print(f"\n✅ Got conversation memory instance: {memory}")
    print(f"   Storage directory: {memory.storage_dir}")
    print(f"   Persist to disk: {memory.persist_to_disk}")
    
    # Clear any existing conversation
    memory.clear_conversation(thread_id)
    print(f"\n🧹 Cleared conversation for thread: {thread_id}")
    
    # Test 1: Store first turn
    print("\n" + "=" * 60)
    print("TEST 1: Store first conversation turn")
    print("=" * 60)
    
    user_input_1 = "print 1 to 10"
    assistant_response_1 = "Here are the numbers from 1 to 10:\n1\n2\n3\n4\n5\n6\n7\n8\n9\n10"
    
    store_conversation_turn(
        thread_id=thread_id,
        user_input=user_input_1,
        assistant_response=assistant_response_1
    )
    
    print(f"✅ Stored turn 1")
    print(f"   User: {user_input_1}")
    print(f"   Assistant: {assistant_response_1[:50]}...")
    
    # Verify storage
    history = memory.get_conversation_history(thread_id, limit=-1)
    print(f"\n📊 Conversation history after turn 1:")
    print(f"   Total messages: {len(history)}")
    for i, msg in enumerate(history):
        print(f"   Message {i+1}: role={msg['role']}, turn_id={msg.get('turn_id', 'N/A')}")
    
    # Test 2: Check if context injection works
    print("\n" + "=" * 60)
    print("TEST 2: Inject conversation context for turn 2")
    print("=" * 60)
    
    user_input_2 = "write fibonacci for each number here"
    enhanced_input_2 = inject_conversation_context(user_input_2, thread_id)
    
    print(f"✅ Context injection successful")
    print(f"   Original input: {user_input_2}")
    print(f"   Enhanced input length: {len(enhanced_input_2)} chars")
    print(f"\n   Enhanced input preview:")
    print("   " + "-" * 56)
    for line in enhanced_input_2.split('\n')[:10]:
        print(f"   {line}")
    if len(enhanced_input_2.split('\n')) > 10:
        print(f"   ... ({len(enhanced_input_2.split('\n')) - 10} more lines)")
    print("   " + "-" * 56)
    
    # Check if context contains the previous conversation
    if "1" in enhanced_input_2 and "10" in enhanced_input_2:
        print("\n✅ Context contains previous conversation data")
    else:
        print("\n❌ Context DOES NOT contain previous conversation data")
    
    # Test 3: Get metadata
    print("\n" + "=" * 60)
    print("TEST 3: Get conversation metadata")
    print("=" * 60)
    
    metadata = get_conversation_context_metadata(thread_id)
    print(f"✅ Metadata retrieved:")
    print(f"   Word count: {metadata['word_count']}")
    print(f"   Turn count: {metadata['turn_count']}")
    print(f"   Message count: {metadata['message_count']}")
    print(f"   Has structured data: {metadata['has_structured_data']}")
    print(f"   Summarization recommended: {metadata['summarization_recommended']}")
    print(f"   Memory size: {metadata['memory_size_bytes']} bytes")
    
    # Test 4: Store second turn
    print("\n" + "=" * 60)
    print("TEST 4: Store second conversation turn")
    print("=" * 60)
    
    assistant_response_2 = "Fibonacci for 1-10: 1, 1, 2, 3, 5, 8, 13, 21, 34, 55"
    
    store_conversation_turn(
        thread_id=thread_id,
        user_input=user_input_2,
        assistant_response=assistant_response_2
    )
    
    print(f"✅ Stored turn 2")
    print(f"   User: {user_input_2}")
    print(f"   Assistant: {assistant_response_2}")
    
    # Verify storage
    history = memory.get_conversation_history(thread_id, limit=-1)
    print(f"\n📊 Conversation history after turn 2:")
    print(f"   Total messages: {len(history)}")
    for i, msg in enumerate(history):
        print(f"   Message {i+1}: role={msg['role']}, turn_id={msg.get('turn_id', 'N/A')}, content_preview={msg['content'][:30]}...")
    
    # Test 5: Verify persistence to disk
    print("\n" + "=" * 60)
    print("TEST 5: Verify disk persistence")
    print("=" * 60)
    
    import os
    storage_path = Path(memory.storage_dir) / f"{thread_id}.json"
    if storage_path.exists():
        print(f"✅ Conversation file exists: {storage_path}")
        print(f"   File size: {storage_path.stat().st_size} bytes")
        
        # Read and display file content
        import json
        with open(storage_path, 'r') as f:
            data = json.load(f)
        print(f"   Thread ID in file: {data.get('thread_id')}")
        print(f"   Messages in file: {len(data.get('messages', []))}")
        print(f"   Last updated: {data.get('updated_at')}")
    else:
        print(f"❌ Conversation file DOES NOT exist: {storage_path}")
        print(f"   Expected location: {storage_path}")
        print(f"   Storage directory exists: {Path(memory.storage_dir).exists()}")
        if Path(memory.storage_dir).exists():
            files = list(Path(memory.storage_dir).glob("*.json"))
            print(f"   Files in storage directory: {len(files)}")
            for f in files[:5]:
                print(f"      - {f.name}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_conversation_memory()
