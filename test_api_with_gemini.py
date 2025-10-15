#!/usr/bin/env python3
"""
Test API with Google Gemini model using LiteLLM adapter
"""

import json
import requests
import sys

def test_gemini_with_litellm():
    """Test the API with Gemini using LiteLLM adapter."""
    # Define API endpoint for the multimodal API (uses LiteLLM directly)
    url = "http://localhost:8000/multimodal"
    
    # Create form data with Gemini model and test query
    data = {
        "model": "gemini/gemini-2.5-flash-lite",  # Use LiteLLM format
        "prompt": "Calculate 25 * 6 and provide a step by step explanation",
        "temperature": 0.2,
        "system_message": "You are an expert at math calculations. Provide clear step-by-step explanations."
    }
    
    # Make API call
    print(f"Making request to {url} with Gemini via LiteLLM...")
    response = requests.post(url, data=data)
    
    # Handle response
    if response.status_code == 200:
        result = response.json()
        print("✅ API call succeeded!")
        print(f"Response: {json.dumps(result, indent=2)}")
        return True
    else:
        print(f"❌ API call failed with status {response.status_code}")
        print(f"Error: {response.text}")
        return False

if __name__ == "__main__":
    success = test_gemini_with_litellm()
    if not success:
        sys.exit(1)
