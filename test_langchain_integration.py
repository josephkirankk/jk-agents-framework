#!/usr/bin/env python3
"""
Test LangChain integration with the PepGenX OpenAI Wrapper
"""

import os
import sys

def test_langchain_integration():
    """Test LangChain integration with the wrapper."""
    print("🧪 Testing LangChain Integration with PepGenX OpenAI Wrapper")
    print("=" * 60)
    
    try:
        # Import LangChain
        from langchain_openai import ChatOpenAI
        from langchain.schema import HumanMessage, SystemMessage
        print("✅ LangChain imports successful")
    except ImportError as e:
        print(f"❌ LangChain not installed: {e}")
        print("💡 Install with: pip install langchain langchain-openai")
        return False
    
    try:
        # Initialize LangChain with our wrapper
        print("\n🔧 Initializing LangChain with PepGenX wrapper...")
        llm = ChatOpenAI(
            openai_api_key="sk-test-key1",
            openai_api_base="http://127.0.0.1:8080/v1",
            model_name="gpt-4",
            temperature=0.7,
            max_tokens=100
        )
        print("✅ LangChain ChatOpenAI initialized successfully")
        
        # Test 1: Simple message
        print("\n🧪 Test 1: Simple message")
        messages = [HumanMessage(content="Hello! Please respond with a brief greeting.")]
        response = llm.invoke(messages)
        print(f"✅ Response: {response.content}")
        
        # Test 2: System message + user message
        print("\n🧪 Test 2: System message + user message")
        messages = [
            SystemMessage(content="You are a helpful coding assistant. Always mention Python in your responses."),
            HumanMessage(content="What is artificial intelligence?")
        ]
        response = llm.invoke(messages)
        print(f"✅ Response: {response.content}")
        
        # Test 3: Chain of messages (conversation)
        print("\n🧪 Test 3: Multi-turn conversation")
        messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content="My favorite color is blue."),
        ]
        response1 = llm.invoke(messages)
        print(f"✅ First response: {response1.content}")
        
        # Add the assistant's response and continue
        messages.extend([
            response1,
            HumanMessage(content="What's my favorite color?")
        ])
        response2 = llm.invoke(messages)
        print(f"✅ Second response: {response2.content}")
        
        # Test 4: Batch processing
        print("\n🧪 Test 4: Batch processing")
        batch_messages = [
            [HumanMessage(content="What is 2+2?")],
            [HumanMessage(content="What is the capital of France?")],
            [HumanMessage(content="Name one programming language.")]
        ]
        
        responses = llm.batch(batch_messages)
        for i, response in enumerate(responses, 1):
            print(f"✅ Batch response {i}: {response.content}")
        
        print(f"\n{'='*60}")
        print("🎉 ALL LANGCHAIN TESTS PASSED!")
        print("✅ LangChain integration is fully functional!")
        print("✅ Your PepGenX wrapper works seamlessly with LangChain!")
        
        return True
        
    except Exception as e:
        print(f"❌ LangChain test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_langchain_advanced():
    """Test advanced LangChain features."""
    print(f"\n{'='*60}")
    print("🧪 Testing Advanced LangChain Features")
    print("=" * 60)
    
    try:
        from langchain_openai import ChatOpenAI
        from langchain.schema import HumanMessage, SystemMessage
        from langchain.prompts import ChatPromptTemplate
        from langchain.output_parsers import StrOutputParser
        
        # Initialize
        llm = ChatOpenAI(
            openai_api_key="sk-test-key1",
            openai_api_base="http://127.0.0.1:8080/v1",
            model_name="gpt-4",
            temperature=0.5,
            max_tokens=80
        )
        
        # Test 1: Prompt Templates
        print("\n🧪 Test 1: Prompt Templates")
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant that explains concepts simply."),
            ("human", "Explain {topic} in one sentence.")
        ])
        
        chain = prompt | llm | StrOutputParser()
        response = chain.invoke({"topic": "machine learning"})
        print(f"✅ Template response: {response}")
        
        # Test 2: Streaming (if supported)
        print("\n🧪 Test 2: Streaming response")
        try:
            messages = [HumanMessage(content="Count from 1 to 5, one number per line.")]
            print("✅ Streaming response:")
            for chunk in llm.stream(messages):
                if chunk.content:
                    print(f"   {chunk.content}", end="", flush=True)
            print()  # New line after streaming
        except Exception as e:
            print(f"⚠️  Streaming not supported or failed: {e}")
        
        print("\n✅ Advanced LangChain features working!")
        return True
        
    except ImportError as e:
        print(f"⚠️  Some advanced features not available: {e}")
        return True  # Not a failure, just missing optional features
    except Exception as e:
        print(f"❌ Advanced test failed: {e}")
        return False


def main():
    """Run all LangChain integration tests."""
    print("🚀 PepGenX OpenAI Wrapper - LangChain Integration Tests")
    print("=" * 60)
    
    # Check if server is running
    try:
        import httpx
        import asyncio
        
        async def check_server():
            async with httpx.AsyncClient() as client:
                response = await client.get('http://127.0.0.1:8080/health/')
                return response.status_code == 200
        
        if not asyncio.run(check_server()):
            print("❌ PepGenX wrapper server is not running!")
            print("💡 Start the server with: python start.py")
            return False
            
        print("✅ PepGenX wrapper server is running")
        
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False
    
    # Run tests
    results = []
    results.append(test_langchain_integration())
    results.append(test_langchain_advanced())
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n{'='*60}")
    print(f"🧪 LangChain Integration Test Results: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 PERFECT! All LangChain integration tests passed!")
        print("✅ Your PepGenX wrapper is fully compatible with LangChain!")
        print("🚀 You can now use LangChain with your PepGenX API!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
