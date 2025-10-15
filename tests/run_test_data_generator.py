#!/usr/bin/env python3
"""
Script to run the Schema-Agnostic Test Data Generator

This script executes the test data generator workflow using the supervisor
and verifies that all agents follow instructions correctly.
"""

import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.supervisor import Supervisor
from app.config_loader import load_config

# Test schema
STUDENT_EXAM_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "StudentExamRecord",
    "description": "Schema for storing student exam data",
    "type": "object",
    "properties": {
        "student_name": {
            "type": "string",
            "description": "Full name of the student"
        },
        "student_id": {
            "type": "string",
            "description": "Unique identifier for the student"
        },
        "student_class": {
            "type": "integer",
            "description": "Class of the student from 1 to 10",
            "minimum": 1,
            "maximum": 10,
            "default": 1
        },
        "subject": {
            "type": "string",
            "description": "Subject name",
            "enum": ["Maths", "Physics", "Chemistry"],
            "default": "Maths"
        },
        "marks": {
            "type": "integer",
            "description": "Marks scored in the subject (1–100)",
            "minimum": 1,
            "maximum": 100,
            "default": 50
        },
        "exam_quarter": {
            "type": "string",
            "description": "Exam quarter",
            "enum": ["Q1", "Q2", "Q3", "Q4"],
            "default": "Q1"
        },
        "exam_year": {
            "type": "integer",
            "description": "Year of the exam in YYYY format",
            "minimum": 2000,
            "maximum": 2100,
            "default": 2025
        }
    },
    "required": [
        "student_name",
        "student_id",
        "student_class",
        "subject",
        "marks",
        "exam_quarter",
        "exam_year"
    ],
    "additionalProperties": False
}

# Test requirements
TEST_REQUIREMENTS = "create records for 100 students for class 5 for all the subjects per student for years 2023,2024,2025. ensure it looks real"


def main():
    """Run the test data generator"""
    print("=" * 80)
    print("  Running Schema-Agnostic Test Data Generator")
    print("=" * 80)
    
    # Load configuration
    print("\n[1] Loading configuration...")
    config = load_config("config/json_schema_test_data_generator.yaml")
    
    # Create supervisor
    print("[2] Initializing supervisor...")
    supervisor = Supervisor(config)
    
    # Prepare user request
    schema_json = json.dumps(STUDENT_EXAM_SCHEMA, indent=2)
    user_request = f"""schema :
{schema_json}

Request : {TEST_REQUIREMENTS}"""
    
    print(f"\n[3] Executing workflow...")
    print(f"    Schema: StudentExamRecord")
    print(f"    Requirements: {TEST_REQUIREMENTS}")
    print(f"    Expected records: 900 (100 students × 3 subjects × 3 years)")
    
    # Execute
    print("\n[4] Running agents...")
    print("-" * 80)
    
    result = supervisor.execute(user_request)
    
    print("\n" + "=" * 80)
    print("  Workflow Execution Complete")
    print("=" * 80)
    
    # Display result
    print(f"\nFinal Result:")
    print(result)
    
    # Check for reference ID in result
    if "ref_" in result:
        import re
        ref_ids = re.findall(r'ref_[a-f0-9]{12}', result)
        if ref_ids:
            print(f"\n✅ Reference ID found: {ref_ids[0]}")
            print(f"\nNext step: Run integration test to verify the data:")
            print(f"  python tests/integration_test_schema_generator.py")
    else:
        print(f"\n⚠️  No reference ID found in result")
        print(f"   This may indicate the data was not stored correctly")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

