#!/bin/bash

# Test script for Submit Selection API endpoint using curl
# This script demonstrates how to call the /submit-selection endpoint

API_URL="http://localhost:8000/submit-selection"

echo "Testing Submit Selection API endpoint..."
echo "========================================"

# Test 1: Valid request
echo "Test 1: Valid request"
echo "---------------------"

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "ngrok-skip-browser-warning: true" \
  -d '{
    "timestamp": "2024-01-15T10:30:45.123Z",
    "original_input": "Bearing overheating in motor pump",
    "remarks": "This issue has been recurring for the past week. Temperature readings show 85°C which is above normal operating range.",
    "selected_issue": {
      "issue_code": "DEF001",
      "issue_text": "Bearing overheating",
      "confidence_score": 0.92,
      "mapping_status": "EXACT_MATCH",
      "curator_action": "AUTO_ACCEPT"
    },
    "selected_pairs": [
      {
        "root_cause": {
          "root_cause_code": "RC001",
          "root_cause_text": "Insufficient lubrication",
          "is_primary": true
        },
        "corrective_action": {
          "action_code": "CA001",
          "action_text": "Apply proper lubrication",
          "is_primary": true
        },
        "pair_id": "primary"
      },
      {
        "root_cause": {
          "root_cause_code": "RC002",
          "root_cause_text": "Excessive load",
          "is_primary": false
        },
        "corrective_action": {
          "action_code": "CA002",
          "action_text": "Reduce operational load",
          "is_primary": false
        },
        "pair_id": "alt-0-1"
      }
    ],
    "analysis_metadata": {
      "agent_name": "general_agent",
      "config_path": "config/multi_provider_example.yaml",
      "submission_source": "general_analysis_page",
      "total_pairs_selected": 2
    }
  }' | jq '.'

echo -e "\n\n"

# Test 2: Invalid timestamp
echo "Test 2: Invalid timestamp"
echo "-------------------------"

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "ngrok-skip-browser-warning: true" \
  -d '{
    "timestamp": "invalid-timestamp",
    "original_input": "Test input",
    "selected_issue": {
      "issue_code": "DEF001",
      "issue_text": "Test issue",
      "confidence_score": 0.8,
      "mapping_status": "EXACT_MATCH",
      "curator_action": "AUTO_ACCEPT"
    },
    "selected_pairs": [
      {
        "root_cause": {
          "root_cause_code": "RC001",
          "root_cause_text": "Test root cause",
          "is_primary": true
        },
        "corrective_action": {
          "action_code": "CA001",
          "action_text": "Test corrective action",
          "is_primary": true
        },
        "pair_id": "primary"
      }
    ],
    "analysis_metadata": {
      "agent_name": "test_agent",
      "config_path": "config/test.yaml",
      "submission_source": "test",
      "total_pairs_selected": 1
    }
  }' | jq '.'

echo -e "\n\n"

# Test 3: Empty pairs
echo "Test 3: Empty selected_pairs"
echo "----------------------------"

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "ngrok-skip-browser-warning: true" \
  -d '{
    "timestamp": "2024-01-15T10:30:45.123Z",
    "original_input": "Test input",
    "selected_issue": {
      "issue_code": "DEF001",
      "issue_text": "Test issue",
      "confidence_score": 0.8,
      "mapping_status": "EXACT_MATCH",
      "curator_action": "AUTO_ACCEPT"
    },
    "selected_pairs": [],
    "analysis_metadata": {
      "agent_name": "test_agent",
      "config_path": "config/test.yaml",
      "submission_source": "test",
      "total_pairs_selected": 0
    }
  }' | jq '.'

echo -e "\n\nAll tests completed!"
