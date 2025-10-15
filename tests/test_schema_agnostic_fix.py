"""
Test to verify schema-agnostic generator fixes
"""
import json
import sqlite3
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_database_initialization():
    """Test that database is properly initialized"""
    db_path = "./data/schema_test_data.db"
    
    # Check if database exists
    assert os.path.exists(db_path), f"Database does not exist at {db_path}"
    
    # Check if database has tables
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print(f"Tables in database: {tables}")
    
    # Should have at least the datasets table
    table_names = [t[0] for t in tables]
    assert 'datasets' in table_names, f"datasets table not found. Tables: {table_names}"
    
    conn.close()
    print("✅ Database initialization test passed")


def test_dataset_storage():
    """Test that dataset was stored correctly"""
    db_path = "./data/schema_test_data.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check for the specific reference ID from the log
    cursor.execute("SELECT reference_id, record_count, data FROM datasets WHERE reference_id = ?", 
                   ('ref_2b9dc591de9b',))
    result = cursor.fetchone()
    
    if result:
        ref_id, count, data_json = result
        data = json.loads(data_json)
        
        print(f"Reference ID: {ref_id}")
        print(f"Record Count: {count}")
        print(f"Actual records in data: {len(data) if isinstance(data, list) else 'N/A'}")
        
        # Verify record count
        assert count == 900, f"Expected 900 records, got {count}"
        assert isinstance(data, list), f"Data should be a list, got {type(data)}"
        assert len(data) == 900, f"Expected 900 records in data, got {len(data)}"
        
        print("✅ Dataset storage test passed")
    else:
        print("❌ Dataset ref_2b9dc591de9b not found in database")
        
        # List all datasets
        cursor.execute("SELECT reference_id, record_count FROM datasets")
        all_datasets = cursor.fetchall()
        print(f"All datasets in database: {all_datasets}")
        
        assert False, "Dataset not found"
    
    conn.close()


def test_record_structure():
    """Test that records have the correct structure"""
    db_path = "./data/schema_test_data.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT data FROM datasets WHERE reference_id = ?", ('ref_2b9dc591de9b',))
    result = cursor.fetchone()
    
    if result:
        data = json.loads(result[0])
        
        # Check first record structure
        first_record = data[0]
        required_fields = [
            'student_name', 'student_id', 'student_class', 
            'subject', 'marks', 'exam_quarter', 'exam_year'
        ]
        
        for field in required_fields:
            assert field in first_record, f"Required field '{field}' missing from record"
        
        # Verify constraints
        assert first_record['student_class'] == 5, "student_class should be 5"
        assert first_record['subject'] in ['Maths', 'Physics', 'Chemistry'], "Invalid subject"
        assert first_record['exam_year'] in [2023, 2024, 2025], "Invalid exam_year"
        assert 1 <= first_record['marks'] <= 100, "Marks out of range"
        assert first_record['exam_quarter'] in ['Q1', 'Q2', 'Q3', 'Q4'], "Invalid quarter"
        
        print("✅ Record structure test passed")
    else:
        assert False, "Dataset not found"
    
    conn.close()


def test_student_distribution():
    """Test that we have 100 unique students with 9 records each"""
    db_path = "./data/schema_test_data.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT data FROM datasets WHERE reference_id = ?", ('ref_2b9dc591de9b',))
    result = cursor.fetchone()
    
    if result:
        data = json.loads(result[0])
        
        # Count unique students
        student_ids = set()
        student_records = {}
        
        for record in data:
            student_id = record['student_id']
            student_ids.add(student_id)
            
            if student_id not in student_records:
                student_records[student_id] = []
            student_records[student_id].append(record)
        
        print(f"Unique students: {len(student_ids)}")
        assert len(student_ids) == 100, f"Expected 100 unique students, got {len(student_ids)}"
        
        # Verify each student has 9 records (3 subjects × 3 years)
        for student_id, records in student_records.items():
            assert len(records) == 9, f"Student {student_id} has {len(records)} records, expected 9"
            
            # Verify all subjects are covered
            subjects = set(r['subject'] for r in records)
            assert subjects == {'Maths', 'Physics', 'Chemistry'}, f"Student {student_id} missing subjects"
            
            # Verify all years are covered
            years = set(r['exam_year'] for r in records)
            assert years == {2023, 2024, 2025}, f"Student {student_id} missing years"
        
        print("✅ Student distribution test passed")
    else:
        assert False, "Dataset not found"
    
    conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Schema-Agnostic Generator Fixes")
    print("=" * 60)
    
    try:
        test_database_initialization()
        test_dataset_storage()
        test_record_structure()
        test_student_distribution()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

