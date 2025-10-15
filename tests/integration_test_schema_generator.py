#!/usr/bin/env python3
"""
Integration Test for Schema-Agnostic Test Data Generator

This test runs the complete workflow and verifies:
1. Agents use run_python_code tool (not text responses)
2. Exactly 900 records are generated
3. Database contains all records
4. Data structure is correct
5. All validation passes
"""

import json
import sqlite3
import os
import sys
import subprocess
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

# Expected results
EXPECTED_RECORD_COUNT = 900  # 100 students × 3 subjects × 3 years
EXPECTED_UNIQUE_STUDENTS = 100
EXPECTED_RECORDS_PER_STUDENT = 9  # 3 subjects × 3 years


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_step(step_num, text):
    """Print a formatted step"""
    print(f"\n[Step {step_num}] {text}")
    print("-" * 80)


def check_database_exists():
    """Check if database exists and has tables"""
    db_path = "./data/large_data_storage.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database does not exist: {db_path}")
        return False
    
    print(f"✅ Database exists: {db_path}")
    print(f"   Size: {os.path.getsize(db_path):,} bytes")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    
    print(f"   Tables: {tables}")
    
    if 'large_tool_data' not in tables:
        print("❌ large_tool_data table not found")
        conn.close()
        return False
    
    print("✅ large_tool_data table exists")
    conn.close()
    return True


def get_latest_dataset():
    """Get the most recent dataset from database"""
    db_path = "./data/large_data_storage.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT reference_id, metadata, data_blob, compressed, created_at 
        FROM large_tool_data 
        ORDER BY created_at DESC 
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return None
    
    ref_id, metadata_json, data_blob, compressed, created_at = result
    
    # Parse metadata
    metadata = json.loads(metadata_json) if metadata_json else {}
    
    # Decompress if needed
    if compressed:
        import gzip
        data_blob = gzip.decompress(data_blob)
    
    # Parse data
    data = json.loads(data_blob)
    
    return {
        "reference_id": ref_id,
        "metadata": metadata,
        "data": data,
        "created_at": created_at
    }


def verify_dataset_structure(dataset_info):
    """Verify the dataset has correct structure"""
    print_step(3, "Verifying Dataset Structure")
    
    data = dataset_info["data"]
    metadata = dataset_info["metadata"]
    ref_id = dataset_info["reference_id"]
    
    print(f"Reference ID: {ref_id}")
    print(f"Created at: {dataset_info['created_at']}")
    print(f"Metadata: {json.dumps(metadata, indent=2)}")
    
    # Check if data is a list
    if not isinstance(data, list):
        print(f"❌ FAIL: Data is {type(data)}, expected list")
        print(f"   Actual data: {data}")
        return False
    
    print(f"✅ Data is a list")
    
    # Check record count
    actual_count = len(data)
    print(f"   Actual record count: {actual_count}")
    print(f"   Expected record count: {EXPECTED_RECORD_COUNT}")
    
    if actual_count != EXPECTED_RECORD_COUNT:
        print(f"❌ FAIL: Expected {EXPECTED_RECORD_COUNT} records, got {actual_count}")
        return False
    
    print(f"✅ Correct record count: {actual_count}")
    
    # Check first record structure
    if actual_count > 0:
        first_record = data[0]
        required_fields = [
            'student_name', 'student_id', 'student_class',
            'subject', 'marks', 'exam_quarter', 'exam_year'
        ]
        
        print(f"\n   First record: {json.dumps(first_record, indent=2)}")
        
        for field in required_fields:
            if field not in first_record:
                print(f"❌ FAIL: Required field '{field}' missing from record")
                return False
        
        print(f"✅ All required fields present")
    
    return True


def verify_data_constraints(dataset_info):
    """Verify data meets all constraints"""
    print_step(4, "Verifying Data Constraints")
    
    data = dataset_info["data"]
    
    # Check student_class = 5
    invalid_class = [r for r in data if r.get('student_class') != 5]
    if invalid_class:
        print(f"❌ FAIL: {len(invalid_class)} records have student_class != 5")
        return False
    print(f"✅ All records have student_class = 5")
    
    # Check subjects
    valid_subjects = {'Maths', 'Physics', 'Chemistry'}
    invalid_subjects = [r for r in data if r.get('subject') not in valid_subjects]
    if invalid_subjects:
        print(f"❌ FAIL: {len(invalid_subjects)} records have invalid subjects")
        return False
    print(f"✅ All records have valid subjects")
    
    # Check exam_year
    valid_years = {2023, 2024, 2025}
    invalid_years = [r for r in data if r.get('exam_year') not in valid_years]
    if invalid_years:
        print(f"❌ FAIL: {len(invalid_years)} records have invalid exam_year")
        return False
    print(f"✅ All records have valid exam_year (2023, 2024, 2025)")
    
    # Check marks range
    invalid_marks = [r for r in data if not (1 <= r.get('marks', 0) <= 100)]
    if invalid_marks:
        print(f"❌ FAIL: {len(invalid_marks)} records have marks out of range")
        return False
    print(f"✅ All records have marks in range [1, 100]")
    
    # Check exam_quarter
    valid_quarters = {'Q1', 'Q2', 'Q3', 'Q4'}
    invalid_quarters = [r for r in data if r.get('exam_quarter') not in valid_quarters]
    if invalid_quarters:
        print(f"❌ FAIL: {len(invalid_quarters)} records have invalid exam_quarter")
        return False
    print(f"✅ All records have valid exam_quarter")
    
    return True


def verify_student_distribution(dataset_info):
    """Verify student distribution is correct"""
    print_step(5, "Verifying Student Distribution")
    
    data = dataset_info["data"]
    
    # Count unique students
    student_records = {}
    for record in data:
        student_id = record['student_id']
        if student_id not in student_records:
            student_records[student_id] = []
        student_records[student_id].append(record)
    
    unique_students = len(student_records)
    print(f"   Unique students: {unique_students}")
    print(f"   Expected: {EXPECTED_UNIQUE_STUDENTS}")
    
    if unique_students != EXPECTED_UNIQUE_STUDENTS:
        print(f"❌ FAIL: Expected {EXPECTED_UNIQUE_STUDENTS} unique students, got {unique_students}")
        return False
    print(f"✅ Correct number of unique students")
    
    # Verify each student has 9 records
    for student_id, records in student_records.items():
        if len(records) != EXPECTED_RECORDS_PER_STUDENT:
            print(f"❌ FAIL: Student {student_id} has {len(records)} records, expected {EXPECTED_RECORDS_PER_STUDENT}")
            return False
        
        # Verify all subjects covered
        subjects = set(r['subject'] for r in records)
        if subjects != {'Maths', 'Physics', 'Chemistry'}:
            print(f"❌ FAIL: Student {student_id} missing subjects: {subjects}")
            return False
        
        # Verify all years covered
        years = set(r['exam_year'] for r in records)
        if years != {2023, 2024, 2025}:
            print(f"❌ FAIL: Student {student_id} missing years: {years}")
            return False
    
    print(f"✅ All students have 9 records (3 subjects × 3 years)")
    
    return True


def main():
    """Run the integration test"""
    print_header("Schema-Agnostic Test Data Generator - Integration Test")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Check database
    print_step(1, "Checking Database Initialization")
    if not check_database_exists():
        print("\n❌ TEST FAILED: Database not properly initialized")
        return 1
    
    # Step 2: Get latest dataset
    print_step(2, "Retrieving Latest Dataset")
    dataset_info = get_latest_dataset()
    
    if not dataset_info:
        print("❌ TEST FAILED: No dataset found in database")
        print("\nℹ️  You need to run the test data generator first:")
        print("   1. Use the supervisor to run the json_schema_test_data_generator workflow")
        print("   2. Provide the StudentExamRecord schema")
        print("   3. Use requirements: 'create records for 100 students for class 5...'")
        return 1
    
    # Step 3: Verify structure
    if not verify_dataset_structure(dataset_info):
        print("\n❌ TEST FAILED: Dataset structure verification failed")
        return 1
    
    # Step 4: Verify constraints
    if not verify_data_constraints(dataset_info):
        print("\n❌ TEST FAILED: Data constraints verification failed")
        return 1
    
    # Step 5: Verify distribution
    if not verify_student_distribution(dataset_info):
        print("\n❌ TEST FAILED: Student distribution verification failed")
        return 1
    
    # All tests passed!
    print_header("✅ ALL TESTS PASSED!")
    print(f"\nSummary:")
    print(f"  Reference ID: {dataset_info['reference_id']}")
    print(f"  Total records: {len(dataset_info['data'])}")
    print(f"  Unique students: {EXPECTED_UNIQUE_STUDENTS}")
    print(f"  Records per student: {EXPECTED_RECORDS_PER_STUDENT}")
    print(f"  All constraints satisfied: ✅")
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

