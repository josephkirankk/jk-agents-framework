#!/usr/bin/env python
"""
Quick Verification: 'undefined' Search Parameter Fix

This script quickly verifies that the SerperToolWrapper fix is working correctly
without requiring API calls or full integration tests.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from unittest.mock import Mock
import json

from app.mcp_loader import SerperToolWrapper


async def test_undefined_filtering():
    """Test that 'undefined' is filtered out"""
    print("\n" + "=" * 80)
    print("TEST 1: Filter 'undefined' String")
    print("=" * 80)
    
    # Create mock MCP tool
    mock_tool = Mock()
    mock_tool.name = "google_search"
    mock_tool.description = "Search Google"
    
    async def mock_arun(params):
        return json.dumps({"results": []})
    
    mock_tool.arun = mock_arun
    
    # Create wrapper
    wrapper = SerperToolWrapper(inner=mock_tool)
    
    # Try to call with "undefined"
    try:
        await wrapper._arun({"query": "undefined"})
        print("❌ FAILED: Should have raised ValueError")
        return False
    except ValueError as e:
        if "google_search requires a valid" in str(e):
            print(f"✅ PASSED: Correctly raised ValueError")
            print(f"   Error message: {e}")
            return True
        else:
            print(f"❌ FAILED: Wrong error: {e}")
            return False


async def test_valid_query_accepted():
    """Test that valid queries are accepted"""
    print("\n" + "=" * 80)
    print("TEST 2: Accept Valid Query")
    print("=" * 80)
    
    # Create mock MCP tool
    mock_tool = Mock()
    mock_tool.name = "google_search"
    mock_tool.description = "Search Google"
    
    captured_params = {}
    
    async def mock_arun(params):
        captured_params.clear()
        captured_params.update(params)
        return json.dumps({"results": ["result1"]})
    
    mock_tool.arun = mock_arun
    
    # Create wrapper
    wrapper = SerperToolWrapper(inner=mock_tool)
    
    # Call with valid query
    try:
        result = await wrapper._arun({"query": "best smartphones India"})
        
        # Check parameters
        if (captured_params.get("q") == "best smartphones India" and
            captured_params.get("gl") == "us" and
            captured_params.get("hl") == "en" and
            "query" not in captured_params):
            print("✅ PASSED: Valid query accepted")
            print(f"   Input:  {{'query': 'best smartphones India'}}")
            print(f"   Output: {captured_params}")
            return True
        else:
            print(f"❌ FAILED: Parameters incorrect")
            print(f"   Got: {captured_params}")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}")
        return False


async def test_empty_string_filtered():
    """Test that empty strings are filtered"""
    print("\n" + "=" * 80)
    print("TEST 3: Filter Empty String")
    print("=" * 80)
    
    # Create mock MCP tool
    mock_tool = Mock()
    mock_tool.name = "google_search"
    mock_tool.description = "Search Google"
    
    async def mock_arun(params):
        return json.dumps({"results": []})
    
    mock_tool.arun = mock_arun
    
    # Create wrapper
    wrapper = SerperToolWrapper(inner=mock_tool)
    
    # Try to call with empty string
    try:
        await wrapper._arun({"query": ""})
        print("❌ FAILED: Should have raised ValueError")
        return False
    except ValueError as e:
        if "google_search requires a valid" in str(e):
            print(f"✅ PASSED: Correctly raised ValueError for empty string")
            return True
        else:
            print(f"❌ FAILED: Wrong error: {e}")
            return False


async def test_case_insensitive():
    """Test that filtering is case-insensitive"""
    print("\n" + "=" * 80)
    print("TEST 4: Case-Insensitive Filtering")
    print("=" * 80)
    
    # Create mock MCP tool
    mock_tool = Mock()
    mock_tool.name = "google_search"
    mock_tool.description = "Search Google"
    
    async def mock_arun(params):
        return json.dumps({"results": []})
    
    mock_tool.arun = mock_arun
    
    # Create wrapper
    wrapper = SerperToolWrapper(inner=mock_tool)
    
    # Test different cases
    test_cases = ["UNDEFINED", "Undefined", "UnDeFiNeD"]
    all_passed = True
    
    for test_value in test_cases:
        try:
            await wrapper._arun({"query": test_value})
            print(f"❌ FAILED: '{test_value}' should have been filtered")
            all_passed = False
        except ValueError:
            print(f"✅ Correctly filtered: '{test_value}'")
    
    return all_passed


async def main():
    """Run all verification tests"""
    print("\n" + "=" * 80)
    print("UNDEFINED SEARCH PARAMETER FIX - VERIFICATION")
    print("=" * 80)
    print("\nThis script verifies the fix is working correctly.")
    
    results = []
    
    # Run tests
    results.append(("Filter 'undefined'", await test_undefined_filtering()))
    results.append(("Accept valid query", await test_valid_query_accepted()))
    results.append(("Filter empty string", await test_empty_string_filtered()))
    results.append(("Case-insensitive", await test_case_insensitive()))
    
    # Summary
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{'=' * 80}")
    print(f"RESULTS: {passed}/{total} tests passed")
    print(f"{'=' * 80}\n")
    
    if passed == total:
        print("✅ The 'undefined' search parameter fix is working correctly!")
        print("\n🎯 What Was Fixed:")
        print("   - 'undefined' strings are now filtered out")
        print("   - Empty and None values are rejected")
        print("   - Valid queries are accepted and converted correctly")
        print("   - ValueError is raised for invalid queries (fail-fast)")
        print("\n📝 Next Steps:")
        print("   - Run full unit tests: pytest tests/test_serper_wrapper_undefined_fix.py")
        print("   - Run integration test: python integration_tests/test_10_serper_search_integration.py")
        print("   - Test with real API calls")
        return 0
    else:
        print("⚠️  Some tests failed. Review the output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
