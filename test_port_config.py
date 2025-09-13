#!/usr/bin/env python3
"""
Test script for the updated port configuration.
Tests both PepGenX wrapper (port 8080) and JK-Agents API (port 8000).
"""

import requests
import json
import time

def test_pepgenx_wrapper():
    """Test PepGenX wrapper health endpoint."""
    print("Testing PepGenX Wrapper (port 8080)...")
    try:
        response = requests.get("http://localhost:8080/health/", timeout=10)
        print(f"✅ PepGenX Wrapper Health: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ PepGenX Wrapper Health failed: {e}")
        return False

def test_jk_agents_api():
    """Test JK-Agents API health endpoint."""
    print("\nTesting JK-Agents API (port 8000)...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        print(f"✅ JK-Agents API Health: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ JK-Agents API Health failed: {e}")
        return False

def test_pepgenx_integration():
    """Test PepGenX integration through JK-Agents API."""
    print("\nTesting PepGenX Integration...")
    try:
        # Prepare the request data
        files = {}
        data = {
            'agent_name': 'general_assistant',
            'input': '2 + 5 = ?',
            'config_path': 'config\\pepgenx_simple_test.yaml',
            'raw_output': 'True'
        }
        
        print(f"Sending request to JK-Agents API...")
        response = requests.post(
            "http://localhost:8000/worker/upload",
            data=data,
            files=files,
            timeout=60
        )
        
        print(f"✅ PepGenX Integration Response: {response.status_code}")
        print(f"   Response: {response.text}")
        
        # Check if it's a successful response
        if response.status_code == 200:
            try:
                # Try to parse as JSON first
                json_response = response.json()
                if json_response.get('success', False):
                    print("✅ PepGenX Integration: SUCCESS")
                    return True
                else:
                    print(f"⚠️  PepGenX Integration: API returned error - {json_response.get('error', 'Unknown error')}")
                    return False
            except json.JSONDecodeError:
                # If it's not JSON, it might be raw text (which is good for raw_output=True)
                if response.text and "Error" not in response.text:
                    print("✅ PepGenX Integration: SUCCESS (raw response)")
                    return True
                else:
                    print(f"⚠️  PepGenX Integration: Unexpected response - {response.text}")
                    return False
        else:
            print(f"❌ PepGenX Integration failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ PepGenX Integration failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Updated Port Configuration")
    print("=" * 50)
    
    # Test individual services
    pepgenx_ok = test_pepgenx_wrapper()
    jk_agents_ok = test_jk_agents_api()
    
    if not pepgenx_ok or not jk_agents_ok:
        print("\n❌ Basic health checks failed. Please ensure both services are running:")
        print("   - PepGenX Wrapper: python -m uvicorn app.main:app --host 0.0.0.0 --port 8080")
        print("   - JK-Agents API: python -m uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload")
        return False
    
    # Test integration
    integration_ok = test_pepgenx_integration()
    
    print("\n" + "=" * 50)
    if pepgenx_ok and jk_agents_ok and integration_ok:
        print("🎉 All tests passed! Port configuration is working correctly.")
        print("   - PepGenX Wrapper: ✅ Port 8080")
        print("   - JK-Agents API: ✅ Port 8000")
        print("   - Integration: ✅ Working")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        
    return pepgenx_ok and jk_agents_ok and integration_ok

if __name__ == "__main__":
    main()
