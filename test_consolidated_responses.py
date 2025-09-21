#!/usr/bin/env python3
"""
Test script for the consolidated responses API endpoint.

This script tests the new /consolidated-responses endpoint with various scenarios:
1. Get all submissions (no date filters)
2. Get submissions with start date filter
3. Get submissions with end date filter
4. Get submissions with both start and end date filters
5. Test invalid date formats
6. Test invalid date ranges
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


def test_consolidated_responses_api(
    base_url: str = "http://localhost:8000",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Test the consolidated responses API endpoint.
    
    Args:
        base_url: Base URL of the API server
        start_date: Optional start date filter (ISO 8601 format)
        end_date: Optional end date filter (ISO 8601 format)
    
    Returns:
        API response as dictionary
    """
    url = f"{base_url}/consolidated-responses"
    
    # Prepare request payload
    payload = {}
    if start_date:
        payload["start_date"] = start_date
    if end_date:
        payload["end_date"] = end_date
    
    print(f"\n🔍 Testing: {url}")
    print(f"📝 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data.get('message', 'No message')}")
            print(f"📈 Total Count: {data.get('total_count', 0)}")
            
            # Print query metadata
            metadata = data.get('query_metadata', {})
            print(f"🔧 Query Metadata:")
            for key, value in metadata.items():
                print(f"   {key}: {value}")
            
            # Print first few submissions (if any)
            submissions = data.get('submissions', [])
            if submissions:
                print(f"\n📋 First 3 submissions:")
                for i, submission in enumerate(submissions[:3]):
                    print(f"   {i+1}. {submission.get('timestamp', 'No timestamp')} - "
                          f"{submission.get('original_input', 'No input')[:50]}...")
            
            return data
        else:
            error_data = response.json()
            print(f"❌ Error: {error_data}")
            return error_data
            
    except requests.exceptions.RequestException as e:
        print(f"🚨 Request failed: {e}")
        return {"error": str(e)}
    except json.JSONDecodeError as e:
        print(f"🚨 JSON decode failed: {e}")
        print(f"Raw response: {response.text}")
        return {"error": f"JSON decode error: {e}"}


def main():
    """Run comprehensive tests for the consolidated responses API."""
    
    print("🚀 Starting Consolidated Responses API Tests")
    print("=" * 60)
    
    # Test 1: Get all submissions (no filters)
    print("\n1️⃣ Test 1: Get all submissions (no date filters)")
    result1 = test_consolidated_responses_api()
    
    # Test 2: Get submissions from today
    print("\n2️⃣ Test 2: Get submissions from today")
    today = datetime.now().strftime("%Y-%m-%dT00:00:00Z")
    result2 = test_consolidated_responses_api(start_date=today)
    
    # Test 3: Get submissions from last 7 days
    print("\n3️⃣ Test 3: Get submissions from last 7 days")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%dT00:00:00Z")
    result3 = test_consolidated_responses_api(start_date=week_ago)
    
    # Test 4: Get submissions for a specific date range
    print("\n4️⃣ Test 4: Get submissions for specific date range")
    start_date = "2025-09-20T00:00:00Z"
    end_date = "2025-09-20T23:59:59Z"
    result4 = test_consolidated_responses_api(start_date=start_date, end_date=end_date)
    
    # Test 5: Test invalid date format
    print("\n5️⃣ Test 5: Test invalid date format")
    result5 = test_consolidated_responses_api(start_date="invalid-date")
    
    # Test 6: Test invalid date range (start > end)
    print("\n6️⃣ Test 6: Test invalid date range (start > end)")
    result6 = test_consolidated_responses_api(
        start_date="2025-09-21T00:00:00Z",
        end_date="2025-09-20T00:00:00Z"
    )
    
    print("\n" + "=" * 60)
    print("🏁 All tests completed!")
    
    # Summary
    print("\n📊 Test Summary:")
    tests = [
        ("All submissions", result1),
        ("Today's submissions", result2),
        ("Last 7 days", result3),
        ("Specific date range", result4),
        ("Invalid date format", result5),
        ("Invalid date range", result6)
    ]
    
    for test_name, result in tests:
        if isinstance(result, dict):
            if result.get('status') == 'success':
                count = result.get('total_count', 0)
                print(f"   ✅ {test_name}: {count} submissions")
            else:
                print(f"   ❌ {test_name}: Error - {result.get('message', 'Unknown error')}")
        else:
            print(f"   ❓ {test_name}: Unexpected result type")


if __name__ == "__main__":
    main()
