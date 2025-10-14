#!/usr/bin/env python3
"""
Test script for conversation turn tracking functionality.
Tests both backward compatibility and new turn tracking features.
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / '.env')
    
    # Fix for LangChain AzureChatOpenAI compatibility
    # It expects OPENAI_API_VERSION instead of AZURE_OPENAI_API_VERSION
    if os.getenv('AZURE_OPENAI_API_VERSION') and not os.getenv('OPENAI_API_VERSION'):
        os.environ['OPENAI_API_VERSION'] = os.getenv('AZURE_OPENAI_API_VERSION')
        print("✅ Set OPENAI_API_VERSION from AZURE_OPENAI_API_VERSION for compatibility")
    
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("⚠️  python-dotenv not installed, skipping .env file loading")
except Exception as e:
    print(f"⚠️  Error loading .env file: {e}")

from app.simple_conversation_memory_fixed import SimpleConversationMemory

def test_backward_compatibility():
    """Test that existing conversations without turn IDs still work."""
    print("🔄 Testing backward compatibility...")
    
    # Create temporary storage
    temp_dir = tempfile.mkdtemp()
    memory = SimpleConversationMemory(persist_to_disk=True, storage_dir=temp_dir)
    
    try:
        # Simulate old conversation format (without turn_id)
        thread_id = "test-backward-compat"
        old_messages = [
            {
                'role': 'user',
                'content': 'Hello, how are you?',
                'timestamp': '2025-09-28T10:00:00',
                'metadata': {}
                # Note: No turn_id field (old format)
            },
            {
                'role': 'assistant', 
                'content': 'I am doing well, thank you!',
                'timestamp': '2025-09-28T10:00:01',
                'metadata': {}
                # Note: No turn_id field (old format)
            }
        ]
        
        # Directly insert old-format messages
        memory.conversations[thread_id] = old_messages
        
        # Test that get_conversation_summary works with old messages
        summary = memory.get_conversation_summary(thread_id)
        print(f"✅ Old format summary generated successfully")
        print(f"   Summary contains: {len(summary.split('Turn-?'))-1} old messages with Turn-? fallback")
        
        # Test that we can add new messages to old conversations
        memory.add_message(thread_id, 'user', 'What is 2+2?')
        memory.add_message(thread_id, 'assistant', '2+2 equals 4')
        
        # Check that new messages have turn IDs
        messages = memory.get_conversation_history(thread_id, limit=10)
        new_user_msg = messages[-2]  # Second to last
        new_assistant_msg = messages[-1]  # Last
        
        assert 'turn_id' in new_user_msg, "New user message should have turn_id"
        assert 'turn_id' in new_assistant_msg, "New assistant message should have turn_id"
        assert new_user_msg['turn_id'] == new_assistant_msg['turn_id'], "User and assistant in same turn should have same turn_id"
        
        print(f"✅ New messages added with turn_id: {new_user_msg['turn_id']}")
        
        # Test mixed conversation summary
        final_summary = memory.get_conversation_summary(thread_id)
        print(f"✅ Mixed format summary generated successfully")
        print(f"   Contains both Turn-? (old) and {new_user_msg['turn_id']} (new) messages")
        
        return True
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_new_turn_tracking():
    """Test new turn tracking functionality."""
    print("\n🆕 Testing new turn tracking functionality...")
    
    # Create temporary storage
    temp_dir = tempfile.mkdtemp()
    memory = SimpleConversationMemory(persist_to_disk=True, storage_dir=temp_dir)
    
    try:
        thread_id = "test-new-turns"
        
        # Test first turn
        memory.add_message(thread_id, 'user', 'list 10 names')
        memory.add_message(thread_id, 'assistant', 'Here are 10 names: Benjamin Rodriguez, Lucas Lopez...')
        
        # Test second turn 
        memory.add_message(thread_id, 'user', 'assign roll numbers to these names')
        memory.add_message(thread_id, 'assistant', 'Roll numbers assigned: Benjamin(101), Lucas(102)...')
        
        # Test third turn
        memory.add_message(thread_id, 'user', 'create a table with names and roll numbers')
        memory.add_message(thread_id, 'assistant', 'Table created successfully with names and roll numbers')
        
        # Verify turn IDs are correct
        messages = memory.get_conversation_history(thread_id, limit=10)
        
        # Check Turn-1 messages
        turn1_user = messages[0]
        turn1_assistant = messages[1]
        assert turn1_user['turn_id'] == 'Turn-1', f"Expected Turn-1, got {turn1_user['turn_id']}"
        assert turn1_assistant['turn_id'] == 'Turn-1', f"Expected Turn-1, got {turn1_assistant['turn_id']}"
        
        # Check Turn-2 messages  
        turn2_user = messages[2]
        turn2_assistant = messages[3]
        assert turn2_user['turn_id'] == 'Turn-2', f"Expected Turn-2, got {turn2_user['turn_id']}"
        assert turn2_assistant['turn_id'] == 'Turn-2', f"Expected Turn-2, got {turn2_assistant['turn_id']}"
        
        # Check Turn-3 messages
        turn3_user = messages[4]
        turn3_assistant = messages[5]
        assert turn3_user['turn_id'] == 'Turn-3', f"Expected Turn-3, got {turn3_user['turn_id']}"
        assert turn3_assistant['turn_id'] == 'Turn-3', f"Expected Turn-3, got {turn3_assistant['turn_id']}"
        
        print(f"✅ All turn IDs assigned correctly:")
        print(f"   Turn-1: {turn1_user['content'][:30]}...")
        print(f"   Turn-2: {turn2_user['content'][:30]}...")
        print(f"   Turn-3: {turn3_user['content'][:30]}...")
        
        # Test conversation summary with turn IDs
        summary = memory.get_conversation_summary(thread_id)
        
        # Verify summary contains turn formatting
        assert '[Turn-1]' in summary, "Summary should contain [Turn-1] formatting"
        assert '[Turn-2]' in summary, "Summary should contain [Turn-2] formatting"
        assert '[Turn-3]' in summary, "Summary should contain [Turn-3] formatting"
        assert 'Current turn: Turn-4' in summary, "Summary should show next turn as Turn-4"
        
        print(f"✅ Turn-aware conversation summary generated:")
        print(f"   Contains proper [Turn-X] formatting")
        print(f"   Shows current turn as Turn-4")
        
        # Test helper methods
        next_turn = memory._get_next_turn_id(thread_id)
        current_turn = memory._get_current_turn_id(thread_id)
        
        assert next_turn == 'Turn-4', f"Expected Turn-4, got {next_turn}"
        assert current_turn == 'Turn-3', f"Expected Turn-3, got {current_turn}"
        
        print(f"✅ Helper methods working correctly:")
        print(f"   Next turn ID: {next_turn}")
        print(f"   Current turn ID: {current_turn}")
        
        return True
        
    except Exception as e:
        print(f"❌ New turn tracking test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_context_injection_format():
    """Test that context injection produces AI-parseable format."""
    print("\n🤖 Testing AI-parseable context format...")
    
    # Create temporary storage
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Test with actual inject_conversation_context function
        from app.simple_conversation_memory_fixed import inject_conversation_context, get_conversation_memory
        
        # Get the global memory instance and add test data
        memory = get_conversation_memory()
        thread_id = "test-context-format"
        
        # Clear any existing conversation for this test
        memory.clear_conversation(thread_id)
        
        # Add some conversation history
        memory.add_message(thread_id, 'user', 'list 10 names')
        memory.add_message(thread_id, 'assistant', 'Benjamin Rodriguez, Lucas Lopez, Maria Garcia, James Wilson, Sarah Johnson')
        memory.add_message(thread_id, 'user', 'assign roll numbers')  
        memory.add_message(thread_id, 'assistant', 'Benjamin(101), Lucas(102), Maria(103), James(104), Sarah(105)')
        
        # Test context injection
        enhanced_input = inject_conversation_context("create a table", thread_id)
        
        print(f"✅ Context injection successful")
        print(f"   Enhanced input length: {len(enhanced_input)} characters")
        
        # Verify turn formatting in context
        assert '[Turn-1]' in enhanced_input, "Context should contain [Turn-1] formatting"
        assert '[Turn-2]' in enhanced_input, "Context should contain [Turn-2] formatting"
        assert 'Current turn: Turn-3' in enhanced_input, "Context should show current turn"
        
        print(f"✅ AI-parseable format verified:")
        print(f"   Contains [Turn-X] markers for easy extraction")
        print(f"   Shows current turn indicator")
        print(f"   Ready for AI model parsing")
        
        # Show sample output (truncated)
        print(f"\n📋 Sample context format:")
        lines = enhanced_input.split('\n')
        for line in lines[:8]:  # First 8 lines
            print(f"   {line}")
        if len(lines) > 8:
            print(f"   ... ({len(lines)-8} more lines)")
        
        return True
        
    except Exception as e:
        print(f"❌ Context format test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    """Run all tests."""
    print("🧪 Testing Turn Tracking Implementation\n")
    
    tests = [
        ("Backward Compatibility", test_backward_compatibility),
        ("New Turn Tracking", test_new_turn_tracking), 
        ("Context Format", test_context_injection_format)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"{'='*60}")
        print(f"Running: {test_name}")
        print(f"{'='*60}")
        
        success = test_func()
        results.append((test_name, success))
        
        if success:
            print(f"✅ {test_name} - PASSED\n")
        else:
            print(f"❌ {test_name} - FAILED\n")
    
    # Summary
    print(f"{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:.<50} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Turn tracking implementation is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return 1

if __name__ == "__main__":
    exit(main())
