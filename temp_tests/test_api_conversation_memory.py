#!/usr/bin/env python3
"""
Test script to verify conversation memory works with the API.
This demonstrates the correct way to use thread_id for conversation continuity.
"""

import requests
import json
import time
from datetime import datetime

def test_conversation_memory_with_api():
    """Test conversation memory by making two API requests with the same thread_id."""
    
    base_url = "http://localhost:8000"
    
    # Check if API is running
    try:
        health_response = requests.get(f"{base_url}/health", timeout=2)
        if health_response.status_code != 200:
            print("❌ API server is not responding correctly")
            print("   Start the server with: python api.py")
            return False
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to API server")
        print("   Start the server with: python api.py")
        return False
    
    print("=" * 70)
    print("CONVERSATION MEMORY API TEST")
    print("=" * 70)
    print(f"API URL: {base_url}")
    print(f"Config: config/python_exec_agent_working.yaml")
    
    # Generate a unique thread_id for this test
    thread_id = f"test-conversation-{int(time.time())}"
    print(f"Thread ID: {thread_id}")
    print()
    
    # Test 1: First request
    print("=" * 70)
    print("REQUEST 1: Ask to print numbers 1 to 10")
    print("=" * 70)
    
    request1 = {
        "input": "print 1 to 10",
        "config_path": "config/python_exec_agent_working.yaml",
        "thread_id": thread_id
    }
    
    print(f"Sending request...")
    print(f"  Input: {request1['input']}")
    print(f"  Thread ID: {request1['thread_id']}")
    
    try:
        response1 = requests.post(
            f"{base_url}/query",
            json=request1,
            timeout=60
        )
        
        if response1.status_code == 200:
            result1 = response1.json()
            print(f"\n✅ Request 1 successful")
            print(f"Response preview:")
            response_text = result1.get('response', '')
            print(f"  {response_text[:200]}...")
            
            # Check if numbers are in response
            if any(str(i) in response_text for i in range(1, 11)):
                print(f"\n✅ Response contains numbers 1-10")
            else:
                print(f"\n⚠️  Response may not contain expected numbers")
        else:
            print(f"\n❌ Request 1 failed with status {response1.status_code}")
            print(f"   Response: {response1.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ Request 1 failed with error: {e}")
        return False
    
    # Wait a moment
    print("\n" + "-" * 70)
    print("Waiting 2 seconds before next request...")
    time.sleep(2)
    
    # Test 2: Second request - should use context from first
    print("\n" + "=" * 70)
    print("REQUEST 2: Ask to write Fibonacci for 'each number here'")
    print("=" * 70)
    print("Expected behavior: Should use numbers from previous request (1-10)")
    print()
    
    request2 = {
        "input": "write fibonacci for each number here",
        "config_path": "config/python_exec_agent_working.yaml",
        "thread_id": thread_id  # SAME thread_id as request 1
    }
    
    print(f"Sending request...")
    print(f"  Input: {request2['input']}")
    print(f"  Thread ID: {request2['thread_id']}")
    print(f"  Using SAME thread_id: {request2['thread_id'] == request1['thread_id']}")
    
    try:
        response2 = requests.post(
            f"{base_url}/query",
            json=request2,
            timeout=60
        )
        
        if response2.status_code == 200:
            result2 = response2.json()
            print(f"\n✅ Request 2 successful")
            print(f"Response:")
            response_text = result2.get('response', '')
            print(f"  {response_text}")
            
            # Check if response contains Fibonacci numbers
            fibonacci_numbers = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
            has_fibonacci = any(str(fib) in response_text for fib in fibonacci_numbers)
            
            # Check if response asks for numbers (BAD - means no context)
            asks_for_numbers = any(phrase in response_text.lower() for phrase in [
                "provide the numbers",
                "which numbers",
                "what numbers",
                "please provide",
                "need the numbers"
            ])
            
            print(f"\n📊 Analysis:")
            if has_fibonacci and not asks_for_numbers:
                print(f"  ✅ SUCCESS: Response contains Fibonacci numbers")
                print(f"  ✅ SUCCESS: Agent used context from previous request")
                print(f"\n🎉 CONVERSATION MEMORY IS WORKING!")
                return True
            elif asks_for_numbers:
                print(f"  ❌ FAILURE: Agent is asking for numbers")
                print(f"  ❌ FAILURE: Agent did NOT use context from previous request")
                print(f"\n⚠️  CONVERSATION MEMORY IS NOT WORKING")
                print(f"\n💡 Possible causes:")
                print(f"     1. Thread ID not being preserved")
                print(f"     2. Conversation storage failed in request 1")
                print(f"     3. Conversation retrieval failed in request 2")
                return False
            else:
                print(f"  ⚠️  UNCLEAR: Response doesn't clearly show success or failure")
                print(f"  ℹ️  Manual review needed")
                return None
                
        else:
            print(f"\n❌ Request 2 failed with status {response2.status_code}")
            print(f"   Response: {response2.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ Request 2 failed with error: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


def test_without_thread_id():
    """Test what happens when thread_id is NOT provided (should get new thread each time)."""
    
    base_url = "http://localhost:8000"
    
    print("\n\n" + "=" * 70)
    print("NEGATIVE TEST: Requests WITHOUT thread_id (should fail)")
    print("=" * 70)
    print("Expected behavior: Each request gets a NEW thread_id, so no context sharing")
    print()
    
    # Request 1 without thread_id
    request1 = {
        "input": "print 1 to 10",
        "config_path": "config/python_exec_agent_working.yaml"
        # NO thread_id provided
    }
    
    print("REQUEST 1: Without thread_id")
    response1 = requests.post(f"{base_url}/query", json=request1, timeout=60)
    if response1.status_code == 200:
        result1 = response1.json()
        thread_id_1 = result1.get('thread_id', 'unknown')
        print(f"  ✅ Success - Thread ID: {thread_id_1}")
    
    time.sleep(1)
    
    # Request 2 without thread_id
    request2 = {
        "input": "write fibonacci for each number here",
        "config_path": "config/python_exec_agent_working.yaml"
        # NO thread_id provided
    }
    
    print("\nREQUEST 2: Without thread_id")
    response2 = requests.post(f"{base_url}/query", json=request2, timeout=60)
    if response2.status_code == 200:
        result2 = response2.json()
        thread_id_2 = result2.get('thread_id', 'unknown')
        response_text = result2.get('response', '')
        print(f"  ✅ Success - Thread ID: {thread_id_2}")
        
        if thread_id_1 != thread_id_2:
            print(f"\n  ℹ️  Different thread IDs: {thread_id_1} != {thread_id_2}")
            print(f"  ℹ️  This is expected - no conversation context will be shared")
        
        asks_for_numbers = any(phrase in response_text.lower() for phrase in [
            "provide the numbers",
            "which numbers",
            "what numbers"
        ])
        
        if asks_for_numbers:
            print(f"  ✅ As expected: Agent asks for numbers (no context)")
        else:
            print(f"  ⚠️  Unexpected: Agent didn't ask for numbers")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    print(f"\nStarting test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Run main test
    result = test_conversation_memory_with_api()
    
    # Run negative test
    test_without_thread_id()
    
    print(f"\n\nTest completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if result is True:
        print("\n✅ OVERALL RESULT: PASS")
        exit(0)
    elif result is False:
        print("\n❌ OVERALL RESULT: FAIL")
        exit(1)
    else:
        print("\n⚠️  OVERALL RESULT: UNCLEAR")
        exit(2)
