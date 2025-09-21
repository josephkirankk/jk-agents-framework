#!/usr/bin/env python3
"""
Test script to isolate the Unicode encoding issue in agent system.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

from app.agent_builder import build_react_agent
from app.config import AppConfig
from app.direct_agent_logger import create_direct_agent_logger

async def test_agent_unicode():
    """Test Unicode handling in the agent system."""
    
    # Test input with Hindi/Devanagari characters
    test_input = "rack पट्टी के बोल्ट लूज हो गए हैं, उसको टाइट करना पड़ेगा।"
    
    print("🧪 Testing Unicode Encoding in Agent System")
    print("=" * 60)
    
    print(f"📝 Original input: {test_input}")
    print(f"📝 Input type: {type(test_input)}")
    print(f"📝 Input encoding: {test_input.encode('utf-8')}")
    print()
    
    try:
        # Create app config
        app_config = AppConfig()
        
        # Create a simple custom placeholder
        custom_placeholders = {
            "user_input": test_input
        }
        
        print("🔄 Building agent with custom placeholders...")
        
        # Create DirectAgentLogger
        direct_logger = create_direct_agent_logger(
            agent_name="test_agent",
            user_input="Test Unicode",
            business_context="Testing Unicode handling"
        )
        
        # Build agent with custom placeholders
        compiled_agent, mcp_client = await build_react_agent(
            target_agent="jk_pilger_new_entries_agent",
            default_model="google:gemini-2.5-flash-lite",
            business_context="Testing Unicode handling",
            original_user_question="",
            dependent_request_responses="",
            config_path=None,
            enable_llm_payload_logging=True,
            llm_payload_logger=direct_logger.get_llm_payload_logger(),
            custom_placeholders=custom_placeholders
        )
        
        print("✅ Agent built successfully!")
        
        # Check the rendered prompt
        rendered_prompt = getattr(compiled_agent, "_rendered_prompt", "(none)")
        
        print("\n📄 Checking rendered prompt...")
        print(f"   Rendered prompt type: {type(rendered_prompt)}")
        print(f"   Rendered prompt length: {len(rendered_prompt)} characters")
        
        # Look for the user input in the rendered prompt
        if test_input in rendered_prompt:
            print("✅ User input preserved correctly in rendered prompt!")
        else:
            print("❌ User input corrupted in rendered prompt!")
            
            # Find the USER INPUT section
            if 'USER INPUT:' in rendered_prompt:
                lines = rendered_prompt.split('\n')
                for i, line in enumerate(lines):
                    if 'USER INPUT:' in line and i + 1 < len(lines):
                        actual_input = lines[i + 1]
                        print(f"   Expected: {test_input}")
                        print(f"   Got:      {actual_input}")
                        
                        # Check character by character
                        print("\n🔍 Character-by-character comparison:")
                        for j, (expected, actual) in enumerate(zip(test_input, actual_input)):
                            if expected != actual:
                                print(f"   Position {j}: expected '{expected}' (U+{ord(expected):04X}), got '{actual}' (U+{ord(actual):04X})")
                        break
        
        # Test the DirectAgentLogger
        print("\n🔄 Testing DirectAgentLogger...")
        
        # Log a request with the agent
        system_context = "Business context:\nTesting Unicode handling\n\nPrevious step results:\n(none)"
        trigger_message = "Please analyze the provided data."
        
        direct_logger.log_agent_request(compiled_agent, system_context, trigger_message)
        
        print("✅ DirectAgentLogger test completed!")
        print(f"   Log file: {direct_logger.log_file_path}")
        
        # Check the log file content
        if direct_logger.log_file_path and direct_logger.log_file_path.exists():
            with open(direct_logger.log_file_path, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            if test_input in log_content:
                print("✅ User input preserved correctly in log file!")
            else:
                print("❌ User input corrupted in log file!")
                
                # Find the USER INPUT section in the log
                if 'USER INPUT:' in log_content:
                    lines = log_content.split('\n')
                    for i, line in enumerate(lines):
                        if 'USER INPUT:' in line and i + 1 < len(lines):
                            actual_input = lines[i + 1]
                            print(f"   Expected: {test_input}")
                            print(f"   Got:      {actual_input}")
                            break
        
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent_unicode())
