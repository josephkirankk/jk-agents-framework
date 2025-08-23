#!/usr/bin/env python3
"""
Test script for jk_tools_agent to verify tool loading and functionality.
This script tests the agent without making API calls to avoid quota limits.
"""

import sys
import os
from pathlib import Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import load_app_config
from app.python_tool_loader import load_python_function_tools, validate_python_tools
import logging

def test_tool_loading():
    """Test that the text_processor tool loads correctly."""
    print("=== Testing Tool Loading ===")
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Load config
        app_cfg = load_app_config(Path('config/gemba_agents_v1.yaml'))
        print(f"✓ Config loaded successfully")
        
        # Find jk_tools_agent
        jk_agent = None
        for agent in app_cfg.agents:
            if agent.name == 'jk_tools_agent':
                jk_agent = agent
                break
        
        if not jk_agent:
            print("✗ jk_tools_agent not found in config")
            return False
            
        print(f"✓ Found agent: {jk_agent.name}")
        print(f"✓ Agent description: {jk_agent.description}")
        
        # Test tool loading
        tools = load_python_function_tools(jk_agent.python_tools)
        print(f"✓ Loaded {len(tools)} tools: {[t.name for t in tools]}")
        
        validated_tools = validate_python_tools(tools)
        print(f"✓ Validated {len(validated_tools)} tools: {[t.name for t in validated_tools]}")
        
        # Find and test the text_processor tool
        text_processor = None
        for tool in validated_tools:
            if tool.name == 'text_processor':
                text_processor = tool
                break
        
        if not text_processor:
            print("✗ text_processor tool not found")
            return False
            
        print(f"✓ Found text_processor tool")
        print(f"  - Description: {text_processor.description}")
        print(f"  - Args schema: {text_processor.args_schema}")
        
        # Test the tool functionality
        print("\n=== Testing Tool Functionality ===")
        
        test_cases = [
            ("Hello world", "word_count"),
            ("This is a test sentence with exactly ten words here", "word_count"),
            ("Short text", "char_count"),
            ("This is some text that needs cleaning!@#$%", "clean"),
            ("This is a long sentence. It has multiple sentences. This is the last one.", "summary")
        ]
        
        for text, operation in test_cases:
            try:
                result = text_processor._run(text, operation)
                print(f"✓ {operation}('{text[:30]}{'...' if len(text) > 30 else ''}')")
                print(f"  Result: {result}")
            except Exception as e:
                print(f"✗ {operation} failed: {e}")
                return False
        
        print("\n=== Testing Word Count Accuracy ===")
        
        # Test specific word counts
        word_count_tests = [
            ("One", 1),
            ("One two", 2),
            ("One two three four five", 5),
            ("This is exactly ten words in this sentence right here", 10),
            ("A poem with exactly thirteen words should be counted correctly by text processor", 13)
        ]
        
        for text, expected_count in word_count_tests:
            result = text_processor._run(text, "word_count")
            actual_count = result.get("word_count", 0)
            if actual_count == expected_count:
                print(f"✓ '{text}' -> {actual_count} words (expected {expected_count})")
            else:
                print(f"✗ '{text}' -> {actual_count} words (expected {expected_count})")
                return False
        
        print("\n=== All Tests Passed! ===")
        print("The jk_tools_agent is properly configured and the text_processor tool is working correctly.")
        print("The agent should now use the tool when asked to write poems with specific word counts.")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent_prompt():
    """Test that the agent prompt is properly configured."""
    print("\n=== Testing Agent Prompt Configuration ===")
    
    try:
        app_cfg = load_app_config(Path('config/gemba_agents_v1.yaml'))
        
        jk_agent = None
        for agent in app_cfg.agents:
            if agent.name == 'jk_tools_agent':
                jk_agent = agent
                break
        
        if not jk_agent:
            print("✗ jk_tools_agent not found")
            return False
        
        prompt = jk_agent.prompt
        
        # Check for key phrases in the prompt
        required_phrases = [
            "MUST use the text_processor tool",
            "operation=\"word_count\"",
            "workflow should be:",
            "Write a poem",
            "count the words",
            "exactly the requested number of words"
        ]
        
        missing_phrases = []
        for phrase in required_phrases:
            if phrase not in prompt:
                missing_phrases.append(phrase)
        
        if missing_phrases:
            print(f"✗ Missing required phrases in prompt: {missing_phrases}")
            return False
        
        print("✓ Agent prompt contains all required instructions")
        print("✓ Agent is configured to use text_processor tool mandatorily")
        print("✓ Agent has clear workflow instructions")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing agent prompt: {e}")
        return False

if __name__ == "__main__":
    print("Testing jk_tools_agent configuration and functionality...\n")
    
    success = True
    success &= test_tool_loading()
    success &= test_agent_prompt()
    
    if success:
        print("\n🎉 All tests passed! The agent is ready to use.")
        print("\nTo test with API calls (when quota allows):")
        print("curl --location 'http://localhost:8000/worker' \\")
        print("--header 'Content-Type: application/json' \\")
        print("--data '{")
        print('    "agent_name": "jk_tools_agent",')
        print('    "input": "write a poem with exactly 15 words",')
        print('    "config_path": "config/gemba_agents_v1.yaml"')
        print("}'")
    else:
        print("\n❌ Some tests failed. Please check the configuration.")
        sys.exit(1)
