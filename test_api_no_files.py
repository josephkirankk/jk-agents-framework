#!/usr/bin/env python3
"""
Test script to verify that the /worker/upload endpoint works without files.
"""

import requests
import json

def test_worker_upload_no_files():
    """Test the /worker/upload endpoint without any files."""
    
    # API endpoint
    url = "http://localhost:8000/worker/upload"
    
    # Test data - no files, just form data
    data = {
        "agent_name": "research_agent",  # Assuming this agent exists
        "input": "What is the capital of France?",
        "raw_output": False
    }
    
    try:
        print("Testing /worker/upload endpoint without files...")
        print(f"URL: {url}")
        print(f"Data: {data}")
        
        # Make the request without files
        response = requests.post(url, data=data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ SUCCESS: API call worked without files!")
                print(f"Response: {json.dumps(result, indent=2)}")
            except json.JSONDecodeError:
                print("✅ SUCCESS: API call worked, but response is not JSON")
                print(f"Response text: {response.text}")
        else:
            print(f"❌ FAILED: Status code {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ FAILED: Could not connect to API server")
        print("Make sure the API server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}")

def test_worker_upload_with_files():
    """Test the /worker/upload endpoint with files to ensure it still works."""
    
    # API endpoint
    url = "http://localhost:8000/worker/upload"
    
    # Test data with a simple text file
    data = {
        "agent_name": "research_agent",
        "input": "Please analyze this file",
        "raw_output": False
    }
    
    # Create a simple test file
    test_file_content = "This is a test file content.\nLine 2\nLine 3"
    files = {
        "files": ("test.txt", test_file_content, "text/plain")
    }
    
    try:
        print("\nTesting /worker/upload endpoint with files...")
        print(f"URL: {url}")
        print(f"Data: {data}")
        print(f"Files: test.txt")
        
        # Make the request with files
        response = requests.post(url, data=data, files=files)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ SUCCESS: API call worked with files!")
                print(f"Response: {json.dumps(result, indent=2)}")
            except json.JSONDecodeError:
                print("✅ SUCCESS: API call worked, but response is not JSON")
                print(f"Response text: {response.text}")
        else:
            print(f"❌ FAILED: Status code {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ FAILED: Could not connect to API server")
        print("Make sure the API server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}")

if __name__ == "__main__":
    test_worker_upload_no_files()
    test_worker_upload_with_files()
