#!/usr/bin/env python3
"""
Test script to verify conversation continuity fix.
"""

import sys
import os
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

from app.simple_conversation_memory_fixed import inject_conversation_context, store_conversation_turn

def test_conversation_memory():
    """Test the conversation memory system."""
    # Simulate first conversation
    thread_id = 'test-thread-123'
    first_input = 'list 10 names'
    first_response = '''Here are 10 random names:
1. Benjamin Rodriguez
2. Lucas Lopez  
3. Lucas Wilson
4. Mia Garcia
5. Elijah Davis
6. Olivia Johnson
7. Amelia Garcia
8. Isabella Jones
9. Charlotte Smith
10. Lucas Smith'''
    
    # Store first conversation
    store_conversation_turn(thread_id, first_input, first_response)
    print('✅ Stored first conversation turn')
    
    # Test second conversation with context injection
    second_input = 'assign roll numbers for each name in markdown'
    enhanced_input = inject_conversation_context(second_input, thread_id)
    
    print('\n=== ENHANCED INPUT WITH CONTEXT ===')
    print(enhanced_input)
    print('\n=== END OF ENHANCED INPUT ===')
    
    # Check if context was properly injected
    if 'Benjamin Rodriguez' in enhanced_input and 'Previous conversation context' in enhanced_input:
        print('✅ SUCCESS: Conversation context properly extracted and injected!')
        return True
    else:
        print('❌ FAILED: Conversation context not properly injected')
        return False

if __name__ == "__main__":
    # Run test
    if test_conversation_memory():
        print('\n✅ Conversation memory system is working correctly!')
        print('✅ The fix should resolve the conversation continuity issue!')
    else:
        print('\n❌ Conversation memory system has issues')
