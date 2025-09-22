#!/usr/bin/env python3
"""
Test script to check Unicode handling in the API endpoint.
"""

import requests
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

def test_api_unicode():
    """Test Unicode handling in the API endpoint."""
    
    # Test input with Hindi/Devanagari characters
    test_input = "rack पट्टी के बोल्ट लूज हो गए हैं, उसको टाइट करना पड़ेगा।"
    
    print("🧪 Testing Unicode Encoding in API Endpoint")
    print("=" * 60)
    
    print(f"📝 Original input: {test_input}")
    print(f"📝 Input type: {type(test_input)}")
    print(f"📝 Input encoding: {test_input.encode('utf-8')}")
    print()
    
    try:
        # Prepare the form data
        form_data = {
            'user_input': test_input,
            'top_n': '5',
            'min_score': '0.2'
        }
        
        print("🔄 Sending request to API endpoint...")
        print(f"   Form data: {form_data}")
        print()
        
        # Send the request
        response = requests.post(
            'http://localhost:8000/defect-analysis-with-pilger/form',
            data=form_data,
            timeout=120
        )
        
        print(f"✅ API request completed!")
        print(f"   Status code: {response.status_code}")
        print(f"   Response length: {len(response.text)} characters")
        print()
        
        if response.status_code == 200:
            # Parse the JSON response
            result = response.json()
            
            # Check the original_input in the response
            original_input = result.get('original_input', '')
            print(f"📊 API Response:")
            print(f"   Original input: {original_input}")
            print(f"   Original input type: {type(original_input)}")
            print(f"   Original input encoding: {original_input.encode('utf-8')}")
            print()
            
            # Check if the Unicode characters are preserved
            if original_input == test_input:
                print("✅ Unicode characters preserved correctly in API response!")
            else:
                print("❌ Unicode characters corrupted in API response!")
                print(f"   Expected: {test_input}")
                print(f"   Got:      {original_input}")
                
                # Character-by-character comparison
                print("\n🔍 Character-by-character comparison:")
                for i, (expected, actual) in enumerate(zip(test_input, original_input)):
                    if expected != actual:
                        print(f"   Position {i}: expected '{expected}' (U+{ord(expected):04X}), got '{actual}' (U+{ord(actual):04X})")
            
            # Check the defect analysis results
            defect_analysis = result.get('defect_analysis', {})
            intent_data = defect_analysis.get('intent_data', {})
            interpreted_meaning = intent_data.get('interpreted_meaning', '')
            
            print(f"\n📊 Intent Analysis:")
            print(f"   Interpreted meaning: {interpreted_meaning}")
            print(f"   Component: {intent_data.get('component', '')}")
            print(f"   Issue: {intent_data.get('issue', '')}")
            
        else:
            print(f"❌ API request failed with status code: {response.status_code}")
            print(f"   Response: {response.text}")
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_unicode()
