#!/usr/bin/env python3
"""
Final consistency test to demonstrate the MCP server fix is working
Tests the same CURL command multiple times to verify consistent behavior
"""

import requests
import time
import json

def test_consistency():
    """Test the same request multiple times to verify consistency"""
    
    url = "http://localhost:8000/worker/upload"
    data = {
        'agent_name': 'restaurants_agent',
        'input': 'list top 10 restaurants having good menu score selling pizza in new york. include the scores as well',
        'config_path': 'config/pep_mcp_sample.yaml',
        'raw_output': 'True'
    }
    
    print("🧪 Testing MCP Server Consistency Fix")
    print("=" * 60)
    print(f"Request: {data['input']}")
    print("=" * 60)
    
    results = []
    
    for i in range(5):
        print(f"\n🔄 Test {i+1}/5...")
        
        try:
            start_time = time.time()
            response = requests.post(url, data=data, timeout=60)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                # Check if response contains restaurant data
                if "Detroit Pizza Works" in response.text and "Menu Score" in response.text:
                    print(f"✅ SUCCESS ({duration:.1f}s) - Got restaurant data")
                    results.append("SUCCESS")
                    
                    # Extract first restaurant for verification
                    lines = response.text.split('\n')
                    for line in lines:
                        if "Detroit Pizza Works" in line:
                            print(f"   📍 {line.strip()}")
                            break
                else:
                    print(f"❌ FAILED ({duration:.1f}s) - No restaurant data")
                    print(f"   Response: {response.text[:100]}...")
                    results.append("FAILED")
            else:
                print(f"❌ HTTP ERROR ({duration:.1f}s) - Status: {response.status_code}")
                results.append("HTTP_ERROR")
                
        except Exception as e:
            print(f"❌ EXCEPTION - {str(e)}")
            results.append("EXCEPTION")
        
        # Small delay between requests
        if i < 4:
            time.sleep(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 RESULTS SUMMARY")
    print("=" * 60)
    
    success_count = results.count("SUCCESS")
    total_count = len(results)
    
    print(f"✅ Successful requests: {success_count}/{total_count}")
    print(f"❌ Failed requests: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n🎉 PERFECT! All requests succeeded consistently!")
        print("✅ The MCP server fix is working correctly.")
        return True
    else:
        print(f"\n⚠️  Only {success_count}/{total_count} requests succeeded.")
        print("❌ There may still be intermittent issues.")
        return False

if __name__ == "__main__":
    success = test_consistency()
    
    print("\n" + "=" * 60)
    if success:
        print("🏆 CONSISTENCY TEST PASSED")
        print("The intermittent MCP server issue has been RESOLVED!")
    else:
        print("🚨 CONSISTENCY TEST FAILED")
        print("The MCP server still has intermittent issues.")
    print("=" * 60)
