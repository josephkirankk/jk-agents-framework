#!/usr/bin/env python
"""Quick verification script to test if the API fix works."""

import requests
import json
import sys

def test_api():
    """Test the /query endpoint with JSON."""
    print("=" * 60)
    print("Testing /query endpoint with JSON payload")
    print("=" * 60)
    
    payload = {
        'input': 'What is 2 + 2? Please answer briefly.',
        'thread_id': 'verify_test_001'
    }
    
    print(f"\n📤 Sending request:")
    print(f"   URL: http://localhost:8000/query")
    print(f"   Payload: {json.dumps(payload, indent=6)}")
    
    try:
        response = requests.post(
            'http://localhost:8000/query',
            json=payload,
            timeout=30
        )
        
        print(f"\n📥 Response:")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS!")
            print(f"   Response keys: {list(data.keys())}")
            if 'response' in data:
                print(f"   Answer: {data['response'][:200]}")
            return True
        else:
            print(f"   ❌ FAILED!")
            print(f"   Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def test_error_handling():
    """Test error handling with invalid request."""
    print("\n" + "=" * 60)
    print("Testing error handling with invalid request")
    print("=" * 60)
    
    payload = {
        'input': '',  # Empty input should fail
        'thread_id': 'verify_test_002'
    }
    
    print(f"\n📤 Sending invalid request (empty input)")
    
    try:
        response = requests.post(
            'http://localhost:8000/query',
            json=payload,
            timeout=10
        )
        
        print(f"\n📥 Response:")
        print(f"   Status: {response.status_code}")
        
        if response.status_code in [400, 422]:
            print(f"   ✅ Error handling works correctly!")
            return True
        else:
            print(f"   ⚠️  Unexpected status code")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("\n🔍 API Fix Verification Script")
    print("=" * 60)
    
    # Test 1: Normal request
    test1_pass = test_api()
    
    # Test 2: Error handling
    test2_pass = test_error_handling()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Test 1 (Normal Request): {'✅ PASS' if test1_pass else '❌ FAIL'}")
    print(f"Test 2 (Error Handling): {'✅ PASS' if test2_pass else '❌ FAIL'}")
    
    if test1_pass and test2_pass:
        print("\n🎉 All verification tests passed!")
        print("The API fix is working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Review the output above.")
        sys.exit(1)
