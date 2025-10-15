#!/usr/bin/env python3
"""Test the exec() fix for function-to-function calls"""

import random
import string

# Simulate the fixed code execution
def test_exec_fix():
    """Test that functions can call each other with the new exec approach"""
    
    restricted_globals = {
        "__builtins__": __builtins__,
        "random": random,
        "string": string,
    }
    
    code = """
def random_name():
    first_names = ["Alex", "Jordan", "Taylor"]
    last_names = ["Smith", "Johnson", "Lee"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def random_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def generate_student_record(idx):
    return {
        "id": idx,
        "name": random_name(),
        "student_id": random_id()
    }

# Generate records
all_records = [generate_student_record(i) for i in range(10)]

# IMPORTANT: Return full list, not slice
all_records
"""
    
    # OLD WAY (fails):
    print("Testing OLD way (separate dicts)...")
    try:
        local_vars = {}
        exec(code, restricted_globals, local_vars)
        result = local_vars.get('all_records')
        print(f"❌ OLD way should fail but got: {len(result) if result else 'None'} records")
    except Exception as e:
        print(f"✅ OLD way fails as expected: {e}")
    
    # NEW WAY (works):
    print("\nTesting NEW way (same dict)...")
    try:
        exec_namespace = dict(restricted_globals)
        exec(code, exec_namespace, exec_namespace)
        result = exec_namespace.get('all_records')
        if result and len(result) == 10:
            print(f"✅ NEW way works: {len(result)} records generated")
            print(f"   Sample record: {result[0]}")
        else:
            print(f"❌ NEW way failed: {result}")
    except Exception as e:
        print(f"❌ NEW way failed with error: {e}")

if __name__ == "__main__":
    test_exec_fix()
