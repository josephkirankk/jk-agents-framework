#!/usr/bin/env python3
"""
Test PepGenX wrapper directly with HTTP requests to debug tool calling.
"""

import asyncio
import json
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_pepgenx_direct():
    """Test PepGenX wrapper directly with HTTP requests."""
    
    print("🧪 Testing PepGenX Wrapper Direct HTTP")
    print("=" * 50)
    
    # Test payload with tools
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "system", 
                "content": "You MUST use the calculate tool for any mathematical task. ALWAYS use the tool - never just describe what you would do."
            },
            {
                "role": "user", 
                "content": "Calculate 2 + 2 using the calculate tool"
            }
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "calculate",
                    "description": "Perform basic arithmetic calculations",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "Mathematical expression to evaluate (e.g., '2+2')"
                            }
                        },
                        "required": ["expression"]
                    }
                }
            }
        ],
        "tool_choice": "auto",
        "temperature": 0.1
    }
    
    print("📤 Request payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://127.0.0.1:8080/v1/chat/completions",
                headers={
                    "Authorization": "Bearer sk-test-key1",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30.0
            )
            
            print(f"\n📥 Response status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print("📥 Response data:")
                print(json.dumps(response_data, indent=2))
                
                # Check for tool calls
                if "choices" in response_data and response_data["choices"]:
                    choice = response_data["choices"][0]
                    message = choice.get("message", {})
                    tool_calls = message.get("tool_calls", [])
                    
                    if tool_calls:
                        print(f"\n✅ Tool calls found: {len(tool_calls)}")
                        for i, call in enumerate(tool_calls):
                            print(f"  Tool {i+1}: {call}")
                    else:
                        print("\n❌ No tool calls in response")
                        print(f"Message content: {message.get('content', 'No content')}")
            else:
                print(f"❌ Error response: {response.text}")
                
    except Exception as e:
        print(f"❌ Request failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pepgenx_direct())
