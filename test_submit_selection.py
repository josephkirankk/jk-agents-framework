#!/usr/bin/env python3
"""
Test script for the Submit Selection API endpoint.

This script tests the /submit-selection endpoint with various scenarios
including valid requests, validation errors, and edge cases.
"""

import json
import requests
from datetime import datetime
from pathlib import Path

# API base URL - adjust as needed
BASE_URL = "http://localhost:8000"
SUBMIT_SELECTION_URL = f"{BASE_URL}/submit-selection"

def create_valid_request():
    """Create a valid submit selection request."""
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "original_input": "Bearing overheating in motor pump",
        "remarks": "This issue has been recurring for the past week. Temperature readings show 85°C which is above normal operating range.",
        "selected_defect": {
            "defect_code": "DEF001",
            "defect_text": "Bearing overheating",
            "confidence_score": 0.92,
            "mapping_status": "EXACT_MATCH",
            "curator_action": "AUTO_ACCEPT"
        },
        "selected_pairs": [
            {
                "root_cause": {
                    "root_cause_code": "RC001",
                    "root_cause_text": "Insufficient lubrication",
                    "is_primary": True
                },
                "corrective_action": {
                    "action_code": "CA001",
                    "action_text": "Apply proper lubrication",
                    "is_primary": True
                },
                "pair_id": "primary"
            },
            {
                "root_cause": {
                    "root_cause_code": "RC002",
                    "root_cause_text": "Excessive load",
                    "is_primary": False
                },
                "corrective_action": {
                    "action_code": "CA002",
                    "action_text": "Reduce operational load",
                    "is_primary": False
                },
                "pair_id": "alt-0-1"
            }
        ],
        "analysis_metadata": {
            "agent_name": "jk_pilger_agent_v8",
            "config_path": "config/jk-gemba.yaml",
            "submission_source": "enhanced_defect_analysis_page",
            "total_pairs_selected": 2
        }
    }

def test_valid_request():
    """Test a valid submit selection request."""
    print("Testing valid request...")
    
    request_data = create_valid_request()
    
    try:
        response = requests.post(
            SUBMIT_SELECTION_URL,
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Valid request test PASSED")
            return True
        else:
            print("❌ Valid request test FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Valid request test FAILED with exception: {e}")
        return False

def test_invalid_timestamp():
    """Test request with invalid timestamp."""
    print("\nTesting invalid timestamp...")
    
    request_data = create_valid_request()
    request_data["timestamp"] = "invalid-timestamp"
    
    try:
        response = requests.post(
            SUBMIT_SELECTION_URL,
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 400:
            print("✅ Invalid timestamp test PASSED")
            return True
        else:
            print("❌ Invalid timestamp test FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Invalid timestamp test FAILED with exception: {e}")
        return False

def test_empty_pairs():
    """Test request with empty selected_pairs."""
    print("\nTesting empty selected_pairs...")
    
    request_data = create_valid_request()
    request_data["selected_pairs"] = []
    request_data["analysis_metadata"]["total_pairs_selected"] = 0
    
    try:
        response = requests.post(
            SUBMIT_SELECTION_URL,
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 422:  # Validation error
            print("✅ Empty pairs test PASSED")
            return True
        else:
            print("❌ Empty pairs test FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Empty pairs test FAILED with exception: {e}")
        return False

def test_mismatched_total_pairs():
    """Test request with mismatched total_pairs_selected."""
    print("\nTesting mismatched total_pairs_selected...")
    
    request_data = create_valid_request()
    request_data["analysis_metadata"]["total_pairs_selected"] = 5  # Should be 2
    
    try:
        response = requests.post(
            SUBMIT_SELECTION_URL,
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 422:  # Validation error
            print("✅ Mismatched total pairs test PASSED")
            return True
        else:
            print("❌ Mismatched total pairs test FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Mismatched total pairs test FAILED with exception: {e}")
        return False

def check_saved_file():
    """Check if the JSON file was saved correctly."""
    print("\nChecking saved files...")
    
    user_responses_dir = Path("user_responses")
    if not user_responses_dir.exists():
        print("❌ user_responses directory not found")
        return False
    
    json_files = list(user_responses_dir.glob("submit_*.json"))
    if not json_files:
        print("❌ No submit_*.json files found")
        return False
    
    # Check the most recent file
    latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
    print(f"Found saved file: {latest_file}")
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        print("✅ File saved and readable")
        print(f"Saved data keys: {list(saved_data.keys())}")
        return True
        
    except Exception as e:
        print(f"❌ Error reading saved file: {e}")
        return False

def main():
    """Run all tests."""
    print("Starting Submit Selection API Tests")
    print("=" * 50)
    
    # Check if API is running
    try:
        health_response = requests.get(f"{BASE_URL}/health")
        if health_response.status_code != 200:
            print("❌ API is not running or not healthy")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("Make sure the API server is running on http://localhost:8000")
        return
    
    print("✅ API is running and healthy")
    print()
    
    # Run tests
    tests_passed = 0
    total_tests = 4
    
    if test_valid_request():
        tests_passed += 1
    
    if test_invalid_timestamp():
        tests_passed += 1
    
    if test_empty_pairs():
        tests_passed += 1
    
    if test_mismatched_total_pairs():
        tests_passed += 1
    
    # Check saved files
    if check_saved_file():
        print("✅ File saving functionality works")
    
    print("\n" + "=" * 50)
    print(f"Tests completed: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests PASSED!")
    else:
        print("⚠️  Some tests FAILED")

if __name__ == "__main__":
    main()
