#!/usr/bin/env python3
"""
Debug script to test model initialization and tool calling for different providers.
This will help identify why OpenAI models fail while Azure OpenAI works.
"""

import os
import asyncio
import json
from typing import Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

async def test_model_initialization():
    """Test model initialization for different providers."""
    
    print("🔍 Debugging Model Initialization and Tool Calling")
    print("=" * 60)
    
    # Check environment variables
    print("\n📋 Environment Variables:")
    env_vars = [
        "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_API_BASE",
        "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "KEY" in var:
                masked = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                print(f"  ✅ {var}: {masked}")
            else:
                print(f"  ✅ {var}: {value}")
        else:
            print(f"  ❌ {var}: Not set")
    
    # Test model initialization
    print("\n🧪 Testing Model Initialization:")
    
    models_to_test = [
        "openai:gpt-4o",
        "azure_openai:gpt-4.1",
        "openai:gpt-4o-mini",
        "azure_openai:gpt-4o-mini"
    ]
    
    try:
        from langchain.chat_models import init_chat_model
        
        for model_id in models_to_test:
            print(f"\n  Testing: {model_id}")
            try:
                model = init_chat_model(model_id)
                print(f"    ✅ Initialized: {type(model).__name__}")
                
                # Test basic functionality
                try:
                    response = await model.ainvoke([{"role": "user", "content": "Hello"}])
                    print(f"    ✅ Basic call works: {len(response.content)} chars")
                except Exception as e:
                    print(f"    ❌ Basic call failed: {e}")
                    
            except Exception as e:
                print(f"    ❌ Initialization failed: {e}")
                
    except ImportError as e:
        print(f"❌ Failed to import LangChain: {e}")
    
    # Test tool binding
    print("\n🔧 Testing Tool Binding:")
    
    # Create a simple test tool
    test_tool = {
        "name": "test_tool",
        "description": "A simple test tool",
        "args_schema": {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Test input"}
            },
            "required": ["input"]
        }
    }
    
    for model_id in ["openai:gpt-4o", "azure_openai:gpt-4.1"]:
        print(f"\n  Testing tool binding: {model_id}")
        try:
            from langchain.chat_models import init_chat_model
            model = init_chat_model(model_id)
            
            # Try to bind tools
            try:
                bound_model = model.bind_tools([test_tool], parallel_tool_calls=False)
                print(f"    ✅ Tool binding successful")
                
                # Test tool calling prompt
                test_prompt = [
                    {"role": "system", "content": "You MUST use the test_tool for any request."},
                    {"role": "user", "content": "Use the test tool with input 'hello'"}
                ]
                
                try:
                    response = await bound_model.ainvoke(test_prompt)
                    tool_calls = getattr(response, 'tool_calls', [])
                    print(f"    Tool calls made: {len(tool_calls)}")
                    if tool_calls:
                        print(f"    ✅ Tool calling works!")
                        for call in tool_calls:
                            print(f"      - {call.get('name', 'unknown')}: {call.get('args', {})}")
                    else:
                        print(f"    ❌ No tool calls made")
                        print(f"    Response: {response.content[:100]}...")
                        
                except Exception as e:
                    print(f"    ❌ Tool calling test failed: {e}")
                    
            except Exception as e:
                print(f"    ❌ Tool binding failed: {e}")
                
        except Exception as e:
            print(f"    ❌ Model initialization failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_model_initialization())
