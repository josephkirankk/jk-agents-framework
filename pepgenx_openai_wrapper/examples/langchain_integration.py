#!/usr/bin/env python3
"""
PepGenX OpenAI Wrapper - LangChain Integration Example

This example shows how to use the PepGenX wrapper with LangChain,
demonstrating that it works seamlessly with popular AI frameworks.

Prerequisites:
1. Start the wrapper: python start.py
2. Install dependencies: pip install langchain langchain-openai

Usage:
    python examples/langchain_integration.py
"""

try:
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage, SystemMessage, AIMessage
    from langchain.prompts import ChatPromptTemplate
    from langchain.chains import LLMChain
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


def test_basic_langchain_chat():
    """Test basic LangChain chat functionality."""
    print("\n📋 Basic LangChain Chat")
    print("-" * 30)
    
    # Initialize LangChain with PepGenX wrapper
    llm = ChatOpenAI(
        openai_api_key="sk-test-key1",
        openai_api_base="http://127.0.0.1:8000/v1",
        model_name="gpt-4",
        temperature=0.7
    )
    
    # Simple message
    messages = [
        HumanMessage(content="Hello! Tell me a fun fact about space.")
    ]
    
    try:
        response = llm(messages)
        print(f"✅ LangChain chat successful!")
        print(f"Response: {response.content}")
        return True
    except Exception as e:
        print(f"❌ LangChain chat failed: {e}")
        return False


def test_langchain_with_system_message():
    """Test LangChain with system messages."""
    print("\n🤖 LangChain with System Message")
    print("-" * 35)
    
    llm = ChatOpenAI(
        openai_api_key="sk-test-key1",
        openai_api_base="http://127.0.0.1:8000/v1",
        model_name="gpt-4",
        temperature=0.3
    )
    
    messages = [
        SystemMessage(content="You are a helpful Python programming tutor."),
        HumanMessage(content="Explain what a list comprehension is in Python.")
    ]
    
    try:
        response = llm(messages)
        print(f"✅ System message with LangChain successful!")
        print(f"Response: {response.content}")
        return True
    except Exception as e:
        print(f"❌ System message failed: {e}")
        return False


def test_langchain_conversation():
    """Test multi-turn conversation with LangChain."""
    print("\n💬 LangChain Conversation")
    print("-" * 25)
    
    llm = ChatOpenAI(
        openai_api_key="sk-test-key1",
        openai_api_base="http://127.0.0.1:8000/v1",
        model_name="gpt-4"
    )
    
    # Simulate a conversation
    messages = [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content="My favorite color is blue."),
        AIMessage(content="That's nice! Blue is a beautiful color."),
        HumanMessage(content="What's my favorite color?")
    ]
    
    try:
        response = llm(messages)
        print(f"✅ LangChain conversation successful!")
        print(f"Response: {response.content}")
        return True
    except Exception as e:
        print(f"❌ Conversation failed: {e}")
        return False


def test_langchain_prompt_template():
    """Test LangChain with prompt templates."""
    print("\n📝 LangChain Prompt Template")
    print("-" * 30)
    
    llm = ChatOpenAI(
        openai_api_key="sk-test-key1",
        openai_api_base="http://127.0.0.1:8000/v1",
        model_name="gpt-4",
        temperature=0.5
    )
    
    # Create a prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that explains {topic} in simple terms."),
        ("human", "Explain {concept} to me.")
    ])
    
    try:
        # Create a chain
        chain = LLMChain(llm=llm, prompt=prompt)
        
        # Run the chain
        response = chain.run(
            topic="computer science",
            concept="machine learning"
        )
        
        print(f"✅ LangChain prompt template successful!")
        print(f"Response: {response}")
        return True
    except Exception as e:
        print(f"❌ Prompt template failed: {e}")
        return False


def test_different_models_langchain():
    """Test different models with LangChain."""
    print("\n🔄 Different Models with LangChain")
    print("-" * 35)
    
    models = ["gpt-4", "gpt-3.5-turbo", "claude-3-sonnet"]
    success_count = 0
    
    for model in models:
        print(f"\n   Testing {model}...")
        
        llm = ChatOpenAI(
            openai_api_key="sk-test-key1",
            openai_api_base="http://127.0.0.1:8000/v1",
            model_name=model,
            temperature=0.7
        )
        
        try:
            response = llm([HumanMessage(content=f"Say hello from {model}")])
            print(f"   ✅ {model}: {response.content[:50]}...")
            success_count += 1
        except Exception as e:
            print(f"   ❌ {model}: {e}")
    
    print(f"\n✅ {success_count}/{len(models)} models worked with LangChain")
    return success_count > 0


def main():
    """Main function to run LangChain integration tests."""
    print("🦜 PepGenX OpenAI Wrapper - LangChain Integration")
    print("=" * 50)
    
    if not LANGCHAIN_AVAILABLE:
        print("❌ LangChain not available!")
        print("Install with: pip install langchain langchain-openai")
        return
    
    print("✅ LangChain libraries available")
    
    # Run tests
    tests = [
        test_basic_langchain_chat,
        test_langchain_with_system_message,
        test_langchain_conversation,
        test_langchain_prompt_template,
        test_different_models_langchain
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print(f"\n{'='*50}")
    print(f"🧪 LangChain Integration Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Perfect! PepGenX wrapper works seamlessly with LangChain!")
    elif passed > 0:
        print("✅ Good! Most LangChain features work with PepGenX wrapper.")
    else:
        print("❌ Issues detected. Check your wrapper configuration.")
    
    print("\n💡 Tips:")
    print("- Use openai_api_base parameter to point to your wrapper")
    print("- Set openai_api_key to one of your wrapper API keys")
    print("- All LangChain features should work transparently")


if __name__ == "__main__":
    main()
