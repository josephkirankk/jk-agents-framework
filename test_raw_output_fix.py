#!/usr/bin/env python3
"""
Test script to verify the raw_output functionality fix.

This script tests that when raw_output=True, the API endpoints return
only the plain text content from the agent with no JSON wrapping,
metadata, or other API response formatting.
"""

import requests
import json
import sys
from pathlib import Path


def test_query_endpoint_raw_output():
    """Test the /query endpoint with raw_output=True."""
    print("Testing /query endpoint with raw_output=True...")
    
    url = "http://localhost:8000/query"
    data = {
        "input": "What is 2 + 2? Please respond with just the number.",
        "raw_output": True
    }
    
    try:
        response = requests.post(url, json=data, timeout=60)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'Not specified')}")
        
        if response.status_code == 200:
            # Check if response is plain text
            content_type = response.headers.get('content-type', '')
            if 'text/plain' in content_type:
                print("✅ Response is plain text (correct)")
                print(f"Raw response content: '{response.text}'")
                
                # Verify it's not JSON
                try:
                    json.loads(response.text)
                    print("❌ Response is valid JSON (should be plain text)")
                    return False
                except json.JSONDecodeError:
                    print("✅ Response is not JSON (correct)")
                    return True
            else:
                print(f"❌ Response content-type is '{content_type}', expected 'text/plain'")
                print(f"Response content: {response.text[:200]}...")
                return False
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False


def test_worker_endpoint_raw_output():
    """Test the /worker endpoint with raw_output=True."""
    print("\nTesting /worker endpoint with raw_output=True...")
    
    url = "http://localhost:8000/worker"
    data = {
        "agent_name": "math_agent",  # Assuming this agent exists
        "input": "Calculate 5 + 3. Respond with just the number.",
        "raw_output": True
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'Not specified')}")
        
        if response.status_code == 200:
            # Check if response is plain text
            content_type = response.headers.get('content-type', '')
            if 'text/plain' in content_type:
                print("✅ Response is plain text (correct)")
                print(f"Raw response content: '{response.text}'")
                
                # Verify it's not JSON
                try:
                    json.loads(response.text)
                    print("❌ Response is valid JSON (should be plain text)")
                    return False
                except json.JSONDecodeError:
                    print("✅ Response is not JSON (correct)")
                    return True
            else:
                print(f"❌ Response content-type is '{content_type}', expected 'text/plain'")
                print(f"Response content: {response.text[:200]}...")
                return False
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False


def test_formatted_output_still_works():
    """Test that formatted output (raw_output=False) still works correctly."""
    print("\nTesting /worker endpoint with raw_output=False (formatted)...")
    
    url = "http://localhost:8000/worker"
    data = {
        "agent_name": "math_agent",  # Assuming this agent exists
        "input": "Calculate 10 + 15.",
        "raw_output": False
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'Not specified')}")
        
        if response.status_code == 200:
            # Check if response is JSON
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                print("✅ Response is JSON (correct for formatted output)")
                
                # Verify it's valid JSON with expected structure
                try:
                    result = response.json()
                    required_fields = ['success', 'response', 'agent_name']
                    missing_fields = [field for field in required_fields if field not in result]
                    
                    if missing_fields:
                        print(f"❌ Missing required fields: {missing_fields}")
                        return False
                    else:
                        print("✅ Response has correct JSON structure")
                        print(f"Agent response: {result.get('response', '')[:100]}...")
                        return True
                        
                except json.JSONDecodeError:
                    print("❌ Response is not valid JSON")
                    return False
            else:
                print(f"❌ Response content-type is '{content_type}', expected 'application/json'")
                return False
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False


def main():
    """Run all tests."""
    print("Raw Output Functionality Fix Verification")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not running or not healthy")
            print("Please start the server with: python -m app.api")
            return False
    except Exception as e:
        print("❌ Cannot connect to server")
        print("Please start the server with: python -m app.api")
        return False
    
    print("✅ Server is running")
    
    # Run tests
    tests = [
        test_query_endpoint_raw_output,
        test_worker_endpoint_raw_output,
        test_formatted_output_still_works
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Results Summary:")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All {total} tests PASSED!")
        print("\nThe raw_output functionality is working correctly:")
        print("• raw_output=True returns plain text content only")
        print("• raw_output=False returns structured JSON responses")
        print("• No additional metadata or wrapper structures in raw mode")
        return True
    else:
        print(f"❌ {total - passed} out of {total} tests FAILED")
        print("\nThe raw_output functionality needs further fixes.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
