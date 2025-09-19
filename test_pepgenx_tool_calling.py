#!/usr/bin/env python3
"""
Test PepGenX wrapper tool calling capability.
"""

import asyncio
import json
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

# Load environment variables
load_dotenv()

async def test_pepgenx_tool_calling():
    """Test if PepGenX wrapper supports tool calling."""
    
    print("🧪 Testing PepGenX Wrapper Tool Calling")
    print("=" * 50)
    
    # Test tool - using simpler format for testing
    test_tool = {
        "name": "calculate",
        "description": "Perform basic arithmetic calculations",
        "args_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2+2')"
                }
            },
            "required": ["expression"],
            "additionalProperties": False
        }
    }
    
    try:
        # Initialize model pointing to PepGenX wrapper
        model = init_chat_model("openai:gpt-4o")
        print(f"✅ Model initialized: {type(model).__name__}")
        
        # Bind tools
        bound_model = model.bind_tools([test_tool], parallel_tool_calls=False)
        print("✅ Tools bound successfully")
        
        # Test tool calling
        messages = [
            {"role": "system", "content": "You MUST use the calculate tool for any mathematical task. ALWAYS use the tool - never just describe what you would do."},
            {"role": "user", "content": "Calculate 2 + 2 using the calculate tool"}
        ]
        
        print("\n📤 Sending request...")
        response = await bound_model.ainvoke(messages)
        
        print(f"\n📥 Response received:")
        print(f"Content: {response.content}")
        
        tool_calls = getattr(response, 'tool_calls', [])
        print(f"Tool calls: {len(tool_calls)}")
        
        if tool_calls:
            print("✅ Tool calling WORKS!")
            for i, call in enumerate(tool_calls):
                print(f"  Tool {i+1}: {call.get('name', 'unknown')}")
                print(f"  Args: {call.get('args', {})}")
        else:
            print("❌ No tool calls made")
            print("This explains why OpenAI models don't work - PepGenX wrapper doesn't support tool calling")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pepgenx_tool_calling())
