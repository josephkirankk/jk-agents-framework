#!/usr/bin/env python3
"""
Test script to compare memory vs no-memory configurations in JK-Agents API.
"""
import requests
import json
import sys
import time

def test_config(config_path, config_name):
    """Test a configuration with multiple questions."""
    print(f"\n🔧 Testing {config_name} configuration: {config_path}")
    print("=" * 60)
    
    # Test 1: Basic question
    print("Test 1: Basic knowledge question")
    response1 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "What is 7 + 5?",
            "config_path": config_path,
            "thread_id": "test-thread-comparison"
        }
    )
    
    if response1.ok:
        result1 = response1.json()
        if result1.get("success"):
            print(f"✅ Answer: {result1['response']}")
        else:
            print(f"❌ Failed: {result1.get('error')}")
            return False
    else:
        print(f"❌ HTTP Error: {response1.status_code}")
        return False
    
    time.sleep(1)  # Small delay between requests
    
    # Test 2: Memory test - introduce information
    print("\nTest 2: Memory introduction")
    response2 = requests.post(
        "http://localhost:8000/worker", 
        json={
            "agent_name": "simple_test_agent",
            "input": "My favorite color is blue. Please remember this fact about me.",
            "config_path": config_path,
            "thread_id": "test-thread-comparison"
        }
    )
    
    if response2.ok:
        result2 = response2.json()
        if result2.get("success"):
            print(f"✅ Agent response: {result2['response']}")
        else:
            print(f"❌ Failed: {result2.get('error')}")
            return False
    else:
        print(f"❌ HTTP Error: {response2.status_code}")
        return False
    
    time.sleep(1)
    
    # Test 3: Memory recall test
    print("\nTest 3: Memory recall test")
    response3 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "What is my favorite color?",
            "config_path": config_path,
            "thread_id": "test-thread-comparison"
        }
    )
    
    if response3.ok:
        result3 = response3.json()
        if result3.get("success"):
            print(f"✅ Memory recall: {result3['response']}")
            # Check if the agent remembered
            remembers = "blue" in result3['response'].lower()
            print(f"🧠 Memory working: {'Yes' if remembers else 'No'}")
        else:
            print(f"❌ Failed: {result3.get('error')}")
            return False
    else:
        print(f"❌ HTTP Error: {response3.status_code}")
        return False
    
    time.sleep(1)
    
    # Test 4: Different thread test (only for memory config)
    if "memory" in config_path.lower() and "no_memory" not in config_path.lower():
        print("\nTest 4: Different thread test (memory isolation)")
        response4 = requests.post(
            "http://localhost:8000/worker",
            json={
                "agent_name": "simple_test_agent",
                "input": "What is my favorite color?",
                "config_path": config_path,
                "thread_id": "different-thread-test"
            }
        )
        
        if response4.ok:
            result4 = response4.json()
            if result4.get("success"):
                print(f"✅ Different thread response: {result4['response']}")
                # In a different thread, it shouldn't remember
                remembers = "blue" in result4['response'].lower()
                print(f"🔒 Thread isolation working: {'No' if remembers else 'Yes'}")
            else:
                print(f"❌ Failed: {result4.get('error')}")
        else:
            print(f"❌ HTTP Error: {response4.status_code}")
    
    # Test 5: Math calculation
    print("\nTest 5: Math calculation")
    response5 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "Calculate 13 * 9",
            "config_path": config_path,
            "thread_id": "test-thread-comparison"
        }
    )
    
    if response5.ok:
        result5 = response5.json()
        if result5.get("success"):
            print(f"✅ Math result: {result5['response']}")
        else:
            print(f"❌ Failed: {result5.get('error')}")
            return False
    else:
        print(f"❌ HTTP Error: {response5.status_code}")
        return False
    
    return True

def test_supervisor_query(config_path, config_name):
    """Test the supervised query endpoint."""
    print(f"\n🎯 Testing supervised query with {config_name}")
    print("-" * 40)
    
    response = requests.post(
        "http://localhost:8000/query",
        json={
            "input": "What is 6 times 4?",
            "config_path": config_path
        }
    )
    
    if response.ok:
        result = response.json()
        if result.get("success"):
            print(f"✅ Supervised query success: {result['response']}")
            return True
        else:
            print(f"❌ Supervised query failed: {result.get('error')}")
            return False
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        return False

def main():
    """Run comparison tests."""
    print("🧪 JK-Agents Memory Configuration Comparison Test")
    print("=" * 70)
    
    # Test configurations
    configs = [
        ("config/basic_test.yaml", "Memory-Enabled"),
        ("config/simple_no_memory_test.yaml", "No-Memory")
    ]
    
    results = {}
    
    for config_path, config_name in configs:
        try:
            success = test_config(config_path, config_name)
            results[config_name] = success
            
            # Test supervised query
            supervisor_success = test_supervisor_query(config_path, config_name)
            results[f"{config_name} (Supervised)"] = supervisor_success
            
        except Exception as e:
            print(f"❌ Exception testing {config_name}: {e}")
            results[config_name] = False
        
        print("\n" + "=" * 70)
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 30)
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\n🎯 Overall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Both configurations are working.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the configurations.")
        return 1

if __name__ == "__main__":
    sys.exit(main())