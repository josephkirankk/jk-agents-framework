#!/usr/bin/env python3
"""
Test PepGenX API directly to see if it supports function calling.
"""

import asyncio
import json
import httpx
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

async def test_pepgenx_api_direct():
    """Test PepGenX API directly."""
    
    print("🧪 Testing PepGenX API Direct")
    print("=" * 40)
    
    # Load OKTA token
    with open('pepgenx_openai_wrapper/okta_token.json', 'r') as f:
        token_data = json.load(f)
    access_token = token_data['access_token']
    
    # PepGenX API payload
    payload = {
        "generation_model": "gpt-4o",
        "custom_prompt": "System: You MUST use the calculate tool for any mathematical task. ALWAYS use the tool - never just describe what you would do.\n\nUser: Calculate 2 + 2 using the calculate tool",
        "system_prompt": 1,
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
    
    headers = {
        "Content-Type": "application/json",
        "project_id": os.getenv("PEPGENX_PROJECT_ID"),
        "team_id": os.getenv("PEPGENX_TEAM_ID"),
        "x-pepgenx-apikey": os.getenv("PEPGENX_API_KEY"),
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "PepGenX-Test/1.0.0"
    }
    
    print("📤 Request payload:")
    print(json.dumps(payload, indent=2))
    print(f"\n📤 Headers (sanitized):")
    sanitized_headers = {k: v if k not in ["Authorization", "x-pepgenx-apikey"] else f"{v[:10]}..." for k, v in headers.items()}
    print(json.dumps(sanitized_headers, indent=2))
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                os.getenv("PEPGENX_API_URL"),
                headers=headers,
                json=payload,
                timeout=30.0
            )
            
            print(f"\n📥 Response status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print("📥 Response data:")
                print(json.dumps(response_data, indent=2))
                
                # Check for tool calls in response
                if isinstance(response_data, dict):
                    # Look for tool calls in various possible locations
                    tool_calls_found = False
                    
                    # Check if there are choices with tool_calls
                    if "choices" in response_data:
                        for choice in response_data["choices"]:
                            if isinstance(choice, dict) and "tool_calls" in choice:
                                print(f"\n✅ Tool calls found in choice: {choice['tool_calls']}")
                                tool_calls_found = True
                    
                    # Check if tool_calls is at root level
                    if "tool_calls" in response_data:
                        print(f"\n✅ Tool calls found at root: {response_data['tool_calls']}")
                        tool_calls_found = True
                    
                    if not tool_calls_found:
                        print("\n❌ No tool calls found in response")
                        print("This suggests PepGenX API may not support function calling or tools are not being processed")
                        
            else:
                print(f"❌ Error response: {response.text}")
                
    except Exception as e:
        print(f"❌ Request failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pepgenx_api_direct())
