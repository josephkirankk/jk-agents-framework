#!/usr/bin/env python3
"""
Test script for file upload functionality with the worker endpoint.
"""

import requests
import json
import os
from pathlib import Path

def test_file_upload():
    """Test the file upload endpoint with a sample image."""
    
    # API endpoint
    url = "http://localhost:8000/worker/upload"
    
    # Create a simple test image (1x1 pixel PNG)
    # This is a minimal valid PNG file
    png_data = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D,  # IHDR chunk length
        0x49, 0x48, 0x44, 0x52,  # IHDR
        0x00, 0x00, 0x00, 0x01,  # Width: 1
        0x00, 0x00, 0x00, 0x01,  # Height: 1
        0x08, 0x02,              # Bit depth: 8, Color type: 2 (RGB)
        0x00, 0x00, 0x00,        # Compression, filter, interlace
        0x90, 0x77, 0x53, 0xDE,  # CRC
        0x00, 0x00, 0x00, 0x0C,  # IDAT chunk length
        0x49, 0x44, 0x41, 0x54,  # IDAT
        0x08, 0x99, 0x01, 0x01, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x02, 0x00, 0x01,
        0xE2, 0x21, 0xBC, 0x33,  # CRC
        0x00, 0x00, 0x00, 0x00,  # IEND chunk length
        0x49, 0x45, 0x4E, 0x44,  # IEND
        0xAE, 0x42, 0x60, 0x82   # CRC
    ])
    
    # Save test image
    test_image_path = "test_image.png"
    with open(test_image_path, "wb") as f:
        f.write(png_data)
    
    try:
        # Prepare the request
        data = {
            "agent_name": "python_exec_agent",
            "input": "What can you tell me about this image?",
            "config_path": "config/gemba-predictive-v1.yaml"
        }
        
        files = {
            "files": ("test_image.png", open(test_image_path, "rb"), "image/png")
        }
        
        print("Testing file upload endpoint...")
        print(f"URL: {url}")
        print(f"Data: {data}")
        print(f"Files: test_image.png")
        
        # Make the request
        response = requests.post(url, data=data, files=files)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nSuccess: {result.get('success')}")
            print(f"Agent: {result.get('agent_name')}")
            print(f"Response: {result.get('response')}")
            print(f"Metadata: {json.dumps(result.get('metadata', {}), indent=2)}")
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure it's running on localhost:8000")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
        if 'files' in locals():
            files['files'][1].close()

def test_regular_endpoint():
    """Test the regular worker endpoint for comparison."""
    
    url = "http://localhost:8000/worker"
    
    data = {
        "agent_name": "python_exec_agent",
        "input": "Calculate 2 + 2",
        "config_path": "config/gemba-predictive-v1.yaml"
    }
    
    try:
        print("\nTesting regular worker endpoint...")
        print(f"URL: {url}")
        print(f"Data: {data}")
        
        response = requests.post(url, json=data)
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success')}")
            print(f"Agent: {result.get('agent_name')}")
            print(f"Response: {result.get('response')}")
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure it's running on localhost:8000")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("=== File Upload API Test ===")
    test_file_upload()
    test_regular_endpoint()
    print("\n=== Test Complete ===")
