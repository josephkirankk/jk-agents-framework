#!/usr/bin/env python3
"""
Demonstration of the raw_output functionality fix.

This script shows the difference between raw_output=True and raw_output=False
by making sample requests to the API endpoints.
"""

import requests
import json


def demo_raw_vs_formatted():
    """Demonstrate the difference between raw and formatted output."""
    
    print("Raw Output Functionality Demonstration")
    print("=" * 50)
    
    # Check if server is running
    try:
        health_response = requests.get("http://localhost:8000/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ Server is not running. Please start with: python -m app.api")
            return
    except Exception:
        print("❌ Cannot connect to server. Please start with: python -m app.api")
        return
    
    print("✅ Server is running\n")
    
    # Test data
    test_input = "What is the capital of France? Please respond briefly."
    
    print("Testing /worker endpoint with the same input:")
    print(f"Input: '{test_input}'\n")
    
    # Test 1: Formatted output (default behavior)
    print("1. FORMATTED OUTPUT (raw_output=False):")
    print("-" * 40)
    
    formatted_data = {
        "agent_name": "general_agent",  # Assuming this exists
        "input": test_input,
        "raw_output": False
    }
    
    try:
        response = requests.post("http://localhost:8000/worker", json=formatted_data, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'Not specified')}")
        
        if response.status_code == 200:
            # Pretty print JSON
            result = response.json()
            print("Response Structure:")
            print(json.dumps(result, indent=2)[:500] + "..." if len(str(result)) > 500 else json.dumps(result, indent=2))
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")
    
    print("\n" + "=" * 50 + "\n")
    
    # Test 2: Raw output
    print("2. RAW OUTPUT (raw_output=True):")
    print("-" * 40)
    
    raw_data = {
        "agent_name": "general_agent",  # Assuming this exists
        "input": test_input,
        "raw_output": True
    }
    
    try:
        response = requests.post("http://localhost:8000/worker", json=raw_data, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'Not specified')}")
        
        if response.status_code == 200:
            print("Raw Response Content:")
            print(f"'{response.text}'")
            
            # Verify it's not JSON
            try:
                json.loads(response.text)
                print("\n⚠️  Warning: Response is valid JSON (unexpected for raw output)")
            except json.JSONDecodeError:
                print("\n✅ Confirmed: Response is plain text, not JSON")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")
    
    print("\n" + "=" * 50)
    print("\nKEY DIFFERENCES:")
    print("• Formatted output: Returns JSON with metadata, success flags, etc.")
    print("• Raw output: Returns only the agent's response as plain text")
    print("• Raw output has Content-Type: text/plain")
    print("• Formatted output has Content-Type: application/json")
    print("• Raw output can be used directly without JSON parsing")


if __name__ == "__main__":
    demo_raw_vs_formatted()
