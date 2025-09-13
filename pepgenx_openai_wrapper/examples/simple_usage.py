#!/usr/bin/env python3
"""
PepGenX OpenAI Wrapper - Simple Usage Example

This is a minimal example showing how to use the PepGenX wrapper
as a drop-in replacement for the OpenAI API.

Prerequisites:
1. Start the wrapper: python start.py
2. Install OpenAI library: pip install openai

Usage:
    python examples/simple_usage.py
"""

import openai
from openai import OpenAI


def main():
    """Simple example of using PepGenX wrapper as OpenAI API."""
    
    print("🚀 PepGenX OpenAI Wrapper - Simple Usage Example")
    print("=" * 50)
    
    # Configure OpenAI client to use your wrapper
    client = OpenAI(
        api_key="sk-test-key1",  # Your wrapper API key
        base_url="http://127.0.0.1:8080/v1"  # Your wrapper URL
    )
    
    try:
        print("\n📋 Step 1: List available models")
        models = client.models.list()
        print(f"✅ Found {len(models.data)} models:")
        for model in models.data[:3]:  # Show first 3
            print(f"   • {model.id}")
        
        print("\n💬 Step 2: Simple chat completion")
        response = client.chat.completions.create(
            model="claude-4-sonnet",
            messages=[
                {"role": "user", "content": "Hello! Please introduce yourself briefly."}
            ],
            max_tokens=100
        )
        
        print("✅ Chat completion successful!")
        print(f"Response: {response.choices[0].message.content}")
        
        print("\n🤖 Step 3: Chat with system message")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful coding assistant."},
                {"role": "user", "content": "Write a simple Python hello world program."}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        print("✅ System message chat successful!")
        print(f"Response: {response.choices[0].message.content}")
        
        print("\n🎉 Success! Your PepGenX API is working as OpenAI API!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure the wrapper server is running: python start.py")
        print("2. Check your .env configuration")
        print("3. Verify your API key matches the one in .env")


if __name__ == "__main__":
    main()
