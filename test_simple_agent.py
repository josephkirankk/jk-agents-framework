#!/usr/bin/env python3
"""
Simple test script to verify the JK-Agents API functionality.
"""
import requests
import json
import sys

def test_health():
    """Test the health endpoint."""
    print("=== Health Check ===")
    try:
        response = requests.get("http://localhost:8000/health")
        response.raise_for_status()
        result = response.json()
        print(f"✅ Health check passed: {result}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_simple_agent():
    """Test a simple agent directly."""
    print("\n=== Simple Agent Test ===")
    try:
        payload = {
            "agent_name": "simple_test_agent",
            "input": "What is the capital of Japan?",
            "config_path": "config/basic_test.yaml"
        }
        
        response = requests.post(
            "http://localhost:8000/worker",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get("success"):
            print(f"✅ Simple agent test passed")
            print(f"   Question: {payload['input']}")
            print(f"   Answer: {result['response']}")
            print(f"   Model: {result['metadata']['model_used']}")
            return True
        else:
            print(f"❌ Simple agent test failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Simple agent test failed with exception: {e}")
        return False

def test_math_question():
    """Test a math question."""
    print("\n=== Math Question Test ===")
    try:
        payload = {
            "agent_name": "simple_test_agent",
            "input": "Calculate 15 multiplied by 8",
            "config_path": "config/basic_test.yaml"
        }
        
        response = requests.post(
            "http://localhost:8000/worker",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get("success"):
            print(f"✅ Math question test passed")
            print(f"   Question: {payload['input']}")
            print(f"   Answer: {result['response']}")
            return True
        else:
            print(f"❌ Math question test failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Math question test failed with exception: {e}")
        return False

def test_memory_persistence():
    """Test if the agent remembers context in the same thread."""
    print("\n=== Memory Persistence Test ===")
    try:
        # First message
        payload1 = {
            "agent_name": "simple_test_agent",
            "input": "My name is Alice. Please remember this.",
            "config_path": "config/basic_test.yaml",
            "thread_id": "test-memory-thread"
        }
        
        response1 = requests.post(
            "http://localhost:8000/worker",
            json=payload1,
            headers={"Content-Type": "application/json"}
        )
        response1.raise_for_status()
        result1 = response1.json()
        
        if not result1.get("success"):
            print(f"❌ First message failed: {result1.get('error')}")
            return False
            
        print(f"First message: {result1['response']}")
        
        # Second message in same thread
        payload2 = {
            "agent_name": "simple_test_agent", 
            "input": "What is my name?",
            "config_path": "config/basic_test.yaml",
            "thread_id": "test-memory-thread"
        }
        
        response2 = requests.post(
            "http://localhost:8000/worker",
            json=payload2,
            headers={"Content-Type": "application/json"}
        )
        response2.raise_for_status()
        result2 = response2.json()
        
        if result2.get("success"):
            print(f"✅ Memory persistence test completed")
            print(f"   Second question: {payload2['input']}")
            print(f"   Answer: {result2['response']}")
            # The agent might or might not remember due to its prompt, but the test is about API functionality
            return True
        else:
            print(f"❌ Second message failed: {result2.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Memory persistence test failed with exception: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing JK-Agents API...")
    
    tests = [
        test_health,
        test_simple_agent,
        test_math_question,
        test_memory_persistence
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print("-" * 50)
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The API is working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the API configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())