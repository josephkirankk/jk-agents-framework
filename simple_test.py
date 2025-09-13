#!/usr/bin/env python3
"""Simple test to verify port configuration."""

import requests
import json

def test_pepgenx_integration():
    """Test PepGenX integration through JK-Agents API."""
    print("🚀 Testing PepGenX Integration with Updated Port Configuration")
    print("=" * 60)
    
    try:
        # Prepare the request data
        data = {
            'agent_name': 'general_assistant',
            'input': '2 + 5 = ?',
            'config_path': 'config\\pepgenx_simple_test.yaml',
            'raw_output': 'True'
        }
        
        print(f"📤 Sending request to JK-Agents API (port 8000)...")
        print(f"   Agent: {data['agent_name']}")
        print(f"   Input: {data['input']}")
        print(f"   Config: {data['config_path']}")
        
        response = requests.post(
            "http://localhost:8000/worker/upload",
            data=data,
            timeout=60
        )
        
        print(f"\n📥 Response received:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Length: {len(response.text)} characters")
        
        if response.status_code == 200:
            print(f"   Response Content: {response.text[:200]}...")
            
            # Check if it's a successful response
            if "Error" not in response.text and response.text.strip():
                print("\n✅ SUCCESS: PepGenX Integration is working!")
                print(f"   Full Response: {response.text}")
                return True
            else:
                print(f"\n⚠️  WARNING: Response contains error or is empty")
                print(f"   Full Response: {response.text}")
                return False
        else:
            print(f"\n❌ FAILED: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        return False

if __name__ == "__main__":
    success = test_pepgenx_integration()
    if success:
        print("\n🎉 Port configuration update is working correctly!")
        print("   - PepGenX Wrapper: ✅ Port 8080")
        print("   - JK-Agents API: ✅ Port 8000")
        print("   - Integration: ✅ Working")
    else:
        print("\n❌ Port configuration test failed.")
