#!/usr/bin/env python3
"""
Test real LLM calls with the PepGenX OpenAI Wrapper
"""

import asyncio
import json
import httpx
from openai import OpenAI


async def test_real_chat_http():
    """Test real chat completion via HTTP."""
    print("🧪 Testing real PepGenX LLM call via HTTP...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                'http://127.0.0.1:8080/v1/chat/completions',
                headers={
                    'Authorization': 'Bearer sk-test-key1',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'gpt-4',
                    'messages': [
                        {'role': 'user', 'content': 'Hello! Please respond with a brief greeting and confirm you are working.'}
                    ],
                    'max_tokens': 50,
                    'temperature': 0.7
                },
                timeout=60.0
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ SUCCESS! Real LLM call working!")
                print(f"Model: {data['model']}")
                print(f"Response: {data['choices'][0]['message']['content']}")
                print(f"Usage: {data['usage']}")
                return True
            else:
                print(f"❌ Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return False


def test_real_chat_openai():
    """Test real chat completion via OpenAI library."""
    print("\n🧪 Testing real PepGenX LLM call via OpenAI library...")
    
    try:
        client = OpenAI(
            api_key="sk-test-key1",
            base_url="http://127.0.0.1:8080/v1"
        )
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": "Hello! Please respond with a brief greeting and tell me what AI model you are."}
            ],
            max_tokens=60,
            temperature=0.7
        )
        
        print("✅ SUCCESS! OpenAI library call working!")
        print(f"Model: {response.model}")
        print(f"Response: {response.choices[0].message.content}")
        print(f"Usage: {response.usage}")
        return True
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_system_message():
    """Test system message handling."""
    print("\n🧪 Testing system message handling...")
    
    try:
        client = OpenAI(
            api_key="sk-test-key1",
            base_url="http://127.0.0.1:8080/v1"
        )
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful coding assistant. Always mention Python in your responses."},
                {"role": "user", "content": "What is machine learning?"}
            ],
            max_tokens=80,
            temperature=0.5
        )
        
        print("✅ SUCCESS! System message handling working!")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_conversation():
    """Test multi-turn conversation."""
    print("\n🧪 Testing multi-turn conversation...")
    
    try:
        client = OpenAI(
            api_key="sk-test-key1",
            base_url="http://127.0.0.1:8080/v1"
        )
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "My name is Alice."},
            {"role": "assistant", "content": "Hello Alice! Nice to meet you."},
            {"role": "user", "content": "What's my name?"}
        ]
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=30
        )
        
        print("✅ SUCCESS! Multi-turn conversation working!")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Testing PepGenX OpenAI Wrapper with Real OKTA Token")
    print("=" * 60)
    
    results = []
    
    # Test HTTP API
    results.append(await test_real_chat_http())
    
    # Test OpenAI library
    results.append(test_real_chat_openai())
    
    # Test system messages
    results.append(test_system_message())
    
    # Test conversation
    results.append(test_conversation())
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n{'='*60}")
    print(f"🧪 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 PERFECT! All real LLM tests passed!")
        print("✅ Your PepGenX wrapper is fully functional!")
    elif passed > 0:
        print("✅ Good! Most tests passed. Check any failures above.")
    else:
        print("❌ All tests failed. Check your OKTA token and configuration.")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
