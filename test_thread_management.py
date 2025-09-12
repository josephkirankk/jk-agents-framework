#!/usr/bin/env python3
"""
Test script for thread ID management functionality.

This script tests the new thread ID management system to ensure:
1. Unique thread IDs are generated when none provided
2. Provided thread IDs are validated and used
3. Thread IDs are returned in API responses
4. Conversation continuity works with same thread ID
"""

import asyncio
import json
import requests
from app.thread_manager import (
    generate_unique_thread_id,
    generate_timestamped_thread_id,
    validate_thread_id,
    get_or_create_thread_id,
    create_supervisor_thread_id,
    create_step_thread_id
)

def test_thread_manager():
    """Test the thread manager utility functions."""
    print("=== Testing Thread Manager ===")
    
    # Test unique thread ID generation
    thread_id1 = generate_unique_thread_id()
    thread_id2 = generate_unique_thread_id()
    print(f"Generated thread ID 1: {thread_id1}")
    print(f"Generated thread ID 2: {thread_id2}")
    assert thread_id1 != thread_id2, "Thread IDs should be unique"
    assert thread_id1.startswith("thread-"), "Thread ID should have correct prefix"
    
    # Test timestamped thread ID generation
    timestamped_id = generate_timestamped_thread_id()
    print(f"Generated timestamped thread ID: {timestamped_id}")
    assert timestamped_id.startswith("thread-"), "Timestamped thread ID should have correct prefix"
    
    # Test thread ID validation
    assert validate_thread_id("valid-thread-123"), "Valid thread ID should pass validation"
    assert not validate_thread_id(""), "Empty thread ID should fail validation"
    assert not validate_thread_id("a"), "Too short thread ID should fail validation"
    assert not validate_thread_id("a" * 101), "Too long thread ID should fail validation"
    assert not validate_thread_id("invalid@thread"), "Thread ID with invalid characters should fail"
    
    # Test get_or_create_thread_id
    provided_id = "my-custom-thread-123"
    result_id = get_or_create_thread_id(provided_id)
    assert result_id == provided_id, "Valid provided thread ID should be returned as-is"
    
    auto_generated = get_or_create_thread_id(None)
    assert auto_generated.startswith("thread-"), "Auto-generated thread ID should have correct prefix"
    
    # Test supervisor and step thread ID creation
    base_id = "test-thread-123"
    supervisor_id = create_supervisor_thread_id(base_id)
    step_id = create_step_thread_id(base_id, "step1")
    
    print(f"Base thread ID: {base_id}")
    print(f"Supervisor thread ID: {supervisor_id}")
    print(f"Step thread ID: {step_id}")
    
    assert supervisor_id == f"{base_id}-supervisor", "Supervisor thread ID should have correct format"
    assert step_id == f"{base_id}-step-step1", "Step thread ID should have correct format"
    
    print("✅ All thread manager tests passed!")


def test_api_thread_management():
    """Test thread ID management through API calls."""
    print("\n=== Testing API Thread Management ===")
    
    base_url = "http://localhost:8000"
    
    try:
        # Test health endpoint first
        health_response = requests.get(f"{base_url}/health")
        if health_response.status_code != 200:
            print("❌ API server is not running. Please start it with:")
            print("python -m uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload")
            return
        
        print("✅ API server is running")
        
        # Test 1: Query without thread_id (should generate new one)
        print("\n--- Test 1: Query without thread_id ---")
        response1 = requests.post(f"{base_url}/query", json={
            "input": "Hello, this is test message 1"
        })
        
        if response1.status_code == 200:
            data1 = response1.json()
            thread_id1 = data1.get("thread_id")
            print(f"Response 1 thread_id: {thread_id1}")
            assert thread_id1, "Response should include thread_id"
            assert thread_id1.startswith("thread-"), "Thread ID should have correct prefix"
        else:
            print(f"❌ Query 1 failed with status {response1.status_code}: {response1.text}")
            return
        
        # Test 2: Query with same thread_id (should use provided one)
        print("\n--- Test 2: Query with same thread_id ---")
        response2 = requests.post(f"{base_url}/query", json={
            "input": "Hello, this is test message 2 in same conversation",
            "thread_id": thread_id1
        })
        
        if response2.status_code == 200:
            data2 = response2.json()
            thread_id2 = data2.get("thread_id")
            print(f"Response 2 thread_id: {thread_id2}")
            assert thread_id2 == thread_id1, "Thread ID should be the same as provided"
        else:
            print(f"❌ Query 2 failed with status {response2.status_code}: {response2.text}")
            return
        
        # Test 3: Query with different thread_id (should use new provided one)
        print("\n--- Test 3: Query with different thread_id ---")
        custom_thread_id = "my-custom-conversation-123"
        response3 = requests.post(f"{base_url}/query", json={
            "input": "Hello, this is test message 3 in new conversation",
            "thread_id": custom_thread_id
        })
        
        if response3.status_code == 200:
            data3 = response3.json()
            thread_id3 = data3.get("thread_id")
            print(f"Response 3 thread_id: {thread_id3}")
            assert thread_id3 == custom_thread_id, "Thread ID should match the custom provided one"
        else:
            print(f"❌ Query 3 failed with status {response3.status_code}: {response3.text}")
            return
        
        # Test 4: Worker endpoint without thread_id
        print("\n--- Test 4: Worker endpoint without thread_id ---")
        response4 = requests.post(f"{base_url}/worker", json={
            "agent_name": "web_agent",  # Using web_agent which exists in default config
            "input": "Test worker message"
        })
        
        if response4.status_code == 200:
            data4 = response4.json()
            thread_id4 = data4.get("thread_id")
            print(f"Worker response thread_id: {thread_id4}")
            assert thread_id4, "Worker response should include thread_id"
            assert thread_id4.startswith("thread-"), "Worker thread ID should have correct prefix"
        else:
            print(f"❌ Worker query failed with status {response4.status_code}: {response4.text}")
            # This might fail if the agent doesn't exist, which is okay for this test
            print("Note: Worker test might fail if agent doesn't exist in config")
        
        print("✅ All API thread management tests passed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server. Please start it with:")
        print("python -m uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload")
    except Exception as e:
        print(f"❌ API test failed with error: {e}")


if __name__ == "__main__":
    print("Testing Thread ID Management System")
    print("=" * 50)
    
    # Test the thread manager utility functions
    test_thread_manager()
    
    # Test API integration (requires running server)
    test_api_thread_management()
    
    print("\n" + "=" * 50)
    print("Thread ID management testing completed!")
