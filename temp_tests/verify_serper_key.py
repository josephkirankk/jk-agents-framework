#!/usr/bin/env python3
"""
Verify Serper API Key
Tests if the SERPER_API_KEY in .env is valid
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_serper_api_key():
    """Test if Serper API key is valid"""
    api_key = os.getenv("SERPER_API_KEY")
    
    print("=" * 60)
    print("SERPER API KEY VALIDATION TEST")
    print("=" * 60)
    
    if not api_key:
        print("❌ ERROR: SERPER_API_KEY not found in environment")
        print("   Please set it in your .env file")
        return False
    
    # Check if it's the placeholder value
    if api_key == "your-serper-api-key-here":
        print("❌ ERROR: SERPER_API_KEY is still the placeholder value")
        print("   Please replace it with your actual API key from https://serper.dev")
        return False
    
    print(f"✓ Found SERPER_API_KEY: {api_key[:10]}...{api_key[-4:]}")
    print(f"  (Length: {len(api_key)} characters)")
    print()
    
    # Test the API key with a simple search
    print("Testing API key with a simple search...")
    url = "https://google.serper.dev/search"
    
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "q": "test query",
        "num": 1
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: API key is valid and working!")
            data = response.json()
            print(f"   Retrieved {len(data.get('organic', []))} search results")
            return True
        elif response.status_code == 403:
            print("❌ FAILED: 403 Forbidden - Unauthorized")
            print("   Your API key is invalid or expired")
            print("   Please check your key at https://serper.dev")
            print(f"   Response: {response.text}")
            return False
        elif response.status_code == 429:
            print("⚠️  WARNING: 429 Too Many Requests")
            print("   Your API key is valid but rate limit exceeded")
            print("   This is not a key validity issue")
            return True
        else:
            print(f"❌ FAILED: Unexpected status code {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ FAILED: Request timeout")
        print("   Could not connect to Serper API")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Request error: {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}")
        return False

def print_instructions():
    """Print instructions for getting a Serper API key"""
    print()
    print("=" * 60)
    print("HOW TO GET A SERPER API KEY")
    print("=" * 60)
    print("1. Go to https://serper.dev")
    print("2. Sign up for a free account")
    print("3. Get your API key from the dashboard")
    print("4. Update your .env file:")
    print("   SERPER_API_KEY=your_actual_key_here")
    print()
    print("Free tier includes:")
    print("- 2,500 free searches")
    print("- No credit card required")
    print("=" * 60)

if __name__ == "__main__":
    success = test_serper_api_key()
    
    if not success:
        print_instructions()
        sys.exit(1)
    else:
        print()
        print("✅ All checks passed! Your Serper API key is working.")
        sys.exit(0)
