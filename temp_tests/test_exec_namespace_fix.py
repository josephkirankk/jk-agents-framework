#!/usr/bin/env python3
"""
Test for exec() Namespace Fix

This test verifies that the fix for function-to-function calls in exec() is working correctly.

Issue: When exec() uses separate globals and locals dicts, functions cannot call each other
Fix: Use the same dict for both globals and locals

Date: October 12, 2025
"""

import sys
import random
import string
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_exec_namespace_old_way():
    """Test the OLD broken way - should fail"""
    print("\n" + "="*80)
    print("  TEST 1: OLD WAY (Separate Dicts) - Should FAIL")
    print("="*80)
    
    restricted_globals = {
        "__builtins__": __builtins__,
        "random": random,
        "string": string,
    }
    
    code = """
def random_name():
    first_names = ["Alex", "Jordan", "Taylor"]
    return random.choice(first_names)

def generate_record(idx):
    name = random_name()  # This will fail
    return {"id": idx, "name": name}

records = [generate_record(i) for i in range(5)]
records
"""
    
    try:
        local_vars = {}
        exec(code, restricted_globals, local_vars)
        result = local_vars.get('records')
        print(f"❌ UNEXPECTED: Old way should fail but got {len(result)} records")
        return False
    except NameError as e:
        if "'random_name' is not defined" in str(e):
            print(f"✅ EXPECTED FAILURE: {e}")
            return True
        else:
            print(f"❌ WRONG ERROR: {e}")
            return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False


def test_exec_namespace_new_way():
    """Test the NEW fixed way - should succeed"""
    print("\n" + "="*80)
    print("  TEST 2: NEW WAY (Same Dict) - Should SUCCEED")
    print("="*80)
    
    restricted_globals = {
        "__builtins__": __builtins__,
        "random": random,
        "string": string,
    }
    
    code = """
def random_name():
    first_names = ["Alex", "Jordan", "Taylor"]
    return random.choice(first_names)

def random_id():
    return ''.join(random.choices(string.ascii_uppercase, k=5))

def generate_record(idx):
    name = random_name()  # Should work now
    student_id = random_id()  # Should work now
    return {"id": idx, "name": name, "student_id": student_id}

records = [generate_record(i) for i in range(5)]
records
"""
    
    try:
        # NEW FIX: Use same dict for both globals and locals
        exec_namespace = dict(restricted_globals)
        exec(code, exec_namespace, exec_namespace)
        
        # Check for result
        result = exec_namespace.get('records')
        
        if result and len(result) == 5:
            print(f"✅ SUCCESS: Generated {len(result)} records")
            print(f"   Sample: {result[0]}")
            
            # Verify all records have required fields
            for i, rec in enumerate(result):
                if 'id' not in rec or 'name' not in rec or 'student_id' not in rec:
                    print(f"❌ Record {i} missing fields: {rec}")
                    return False
            
            print("✅ All records have required fields")
            return True
        else:
            print(f"❌ FAILED: Expected 5 records, got {len(result) if result else 'None'}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_exec_with_nested_functions():
    """Test with nested function calls"""
    print("\n" + "="*80)
    print("  TEST 3: NESTED FUNCTION CALLS")
    print("="*80)
    
    restricted_globals = {
        "__builtins__": __builtins__,
        "random": random,
        "string": string,
    }
    
    code = """
def generate_first_name():
    return random.choice(["Alice", "Bob", "Charlie"])

def generate_last_name():
    return random.choice(["Smith", "Jones", "Brown"])

def generate_full_name():
    # Calls two other functions
    return f"{generate_first_name()} {generate_last_name()}"

def generate_student():
    # Calls function that calls other functions
    return {
        "name": generate_full_name(),
        "id": ''.join(random.choices(string.digits, k=6))
    }

students = [generate_student() for _ in range(3)]
students
"""
    
    try:
        exec_namespace = dict(restricted_globals)
        exec(code, exec_namespace, exec_namespace)
        
        result = exec_namespace.get('students')
        
        if result and len(result) == 3:
            print(f"✅ SUCCESS: Generated {len(result)} students with nested calls")
            for student in result:
                print(f"   - {student['name']} (ID: {student['id']})")
            return True
        else:
            print(f"❌ FAILED: Expected 3 students, got {len(result) if result else 'None'}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_variable_detection():
    """Test that common variable names are detected correctly"""
    print("\n" + "="*80)
    print("  TEST 4: VARIABLE DETECTION")
    print("="*80)
    
    restricted_globals = {
        "__builtins__": __builtins__,
        "random": random,
    }
    
    test_cases = [
        ("result = [1, 2, 3]", "result", [1, 2, 3]),
        ("records = [{'a': 1}]", "records", [{'a': 1}]),
        ("all_records = [{'b': 2}]", "all_records", [{'b': 2}]),
        ("output = [4, 5, 6]", "output", [4, 5, 6]),
    ]
    
    all_passed = True
    for code, var_name, expected in test_cases:
        try:
            exec_namespace = dict(restricted_globals)
            exec(code, exec_namespace, exec_namespace)
            
            # Check if variable exists
            if var_name in exec_namespace:
                result = exec_namespace[var_name]
                if result == expected:
                    print(f"✅ {var_name}: Detected correctly = {result}")
                else:
                    print(f"❌ {var_name}: Expected {expected}, got {result}")
                    all_passed = False
            else:
                print(f"❌ {var_name}: Not found in namespace")
                all_passed = False
                
        except Exception as e:
            print(f"❌ {var_name}: Error - {e}")
            all_passed = False
    
    return all_passed


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("  EXEC NAMESPACE FIX - INTEGRATION TESTS")
    print("="*80)
    print("\nThese tests verify the fix for function-to-function calls in exec()")
    print("Issue: Separate globals/locals dicts prevent function calls")
    print("Fix: Use same dict for both globals and locals")
    
    results = {
        "Test 1 (Old Way)": test_exec_namespace_old_way(),
        "Test 2 (New Way)": test_exec_namespace_new_way(),
        "Test 3 (Nested Calls)": test_exec_with_nested_functions(),
        "Test 4 (Variable Detection)": test_variable_detection(),
    }
    
    print("\n" + "="*80)
    print("  TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*80)
    if all_passed:
        print("  🎉 ALL TESTS PASSED")
    else:
        print("  ❌ SOME TESTS FAILED")
    print("="*80 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
