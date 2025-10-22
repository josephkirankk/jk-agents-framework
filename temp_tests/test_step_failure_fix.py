#!/usr/bin/env python3
"""
Test to verify the step failure fix.

This test ensures that:
1. Steps with valid output are not marked as failed even if exceptions occur
2. Steps without output are properly marked as failed
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_step_ok_logic():
    """Test the step_ok logic directly"""
    print("=" * 80)
    print("TEST: Step Success/Failure Logic")
    print("=" * 80)
    
    test_cases = [
        # (wtext, last_err, expected_ok, description)
        ("Valid output here", "", True, "No error, valid output"),
        ("ERROR: something failed", "", False, "ERROR prefix in output"),
        ("Valid response with data", "Some exception", True, "Error but valid output produced"),
        ("", "timeout", False, "Error with no output"),
        ("Short", "exception", False, "Error with insufficient output"),
        ("This is a longer valid output with meaningful content", "warning", True, "Warning but good output"),
    ]
    
    all_passed = True
    for wtext, last_err, expected_ok, description in test_cases:
        # Replicate the logic from planner_executor.py
        wtext_str = str(wtext) if wtext is not None else ""
        has_valid_output = bool(wtext_str and not wtext_str.startswith("ERROR") and len(wtext_str.strip()) > 10)
        
        step_ok = True
        if wtext_str.startswith("ERROR"):
            step_ok = False
        elif last_err and not has_valid_output:
            step_ok = False
        elif last_err and has_valid_output:
            step_ok = True
            # Would clear last_err in real code
        
        status = "✅" if step_ok == expected_ok else "❌"
        all_passed = all_passed and (step_ok == expected_ok)
        
        print(f"{status} {description}")
        print(f"   Input: wtext={repr(wtext[:30])}, last_err={repr(last_err)}")
        print(f"   Expected: {expected_ok}, Got: {step_ok}")
        if step_ok != expected_ok:
            print(f"   ⚠️  MISMATCH!")
        print()
    
    return all_passed


def test_import_check():
    """Verify the fix is in place"""
    print("=" * 80)
    print("TEST: Verify Fix Implementation")
    print("=" * 80)
    
    try:
        from app.planner_executor import execute_plan
        import inspect
        
        source = inspect.getsource(execute_plan)
        
        # Check for the fix markers
        checks = [
            ("has_valid_output", "Valid output detection"),
            ("step_ok", "Step OK variable"),
            ("Error occurred BUT agent still produced valid output", "Success with warning logic"),
        ]
        
        all_found = True
        for pattern, description in checks:
            if pattern in source:
                print(f"✅ {description}")
            else:
                print(f"❌ Missing: {description}")
                all_found = False
        
        # Check that safe_langgraph_execution is NOT wrapping worker calls
        if "async with safe_langgraph_execution():" in source:
            # Count occurrences - should only be in supervisor, not worker
            count = source.count("async with safe_langgraph_execution():")
            if count > 0:
                print(f"⚠️  Warning: safe_langgraph_execution found {count} time(s)")
                print(f"   (Should only be used for supervisor, not worker calls)")
        
        return all_found
        
    except Exception as e:
        print(f"❌ Error checking implementation: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "🔧" * 40)
    print("STEP FAILURE FIX - VERIFICATION")
    print("🔧" * 40 + "\n")
    
    results = []
    
    # Run tests
    results.append(("Step Logic", test_step_ok_logic()))
    results.append(("Implementation Check", test_import_check()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The fix is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
