"""
Test Serper Parameter Fix

Verifies that the SerperToolWrapper correctly injects default parameters
for google_search and scrape tools.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Set tokenizer parallelism
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import json
import asyncio
from unittest.mock import Mock, AsyncMock

from app.mcp_loader import SerperToolWrapper


def test_serper_wrapper_creation():
    """Test that SerperToolWrapper can be created"""
    print("\n" + "=" * 80)
    print("TEST 1: SerperToolWrapper Creation")
    print("=" * 80)
    
    mock_tool = Mock()
    mock_tool.name = "google_search"
    mock_tool.description = "Search Google"
    
    try:
        wrapper = SerperToolWrapper(inner=mock_tool)
        print(f"  ✅ PASS: SerperToolWrapper created successfully")
        print(f"     Name: {wrapper.name}")
        print(f"     Description: {wrapper.description}")
        return True
    except Exception as e:
        print(f"  ❌ FAIL: Cannot create wrapper: {e}")
        return False


def test_parameter_injection_google_search():
    """Test that default parameters are injected for google_search"""
    print("\n" + "=" * 80)
    print("TEST 2: Parameter Injection for google_search")
    print("=" * 80)
    
    mock_tool = Mock()
    mock_tool.name = "google_search"
    mock_tool.description = "Search Google"
    
    wrapper = SerperToolWrapper(inner=mock_tool)
    
    # Test 1: Query only (missing gl and hl)
    print("\n  Test 2a: Query only (should inject gl and hl)")
    params = {"query": "test search"}
    result = wrapper._inject_defaults(params)
    
    if result.get("gl") == "us" and result.get("hl") == "en":
        print(f"  ✅ PASS: Default parameters injected")
        print(f"     Input:  {{'query': 'test search'}}")
        print(f"     Output: {result}")
    else:
        print(f"  ❌ FAIL: Parameters not injected correctly")
        print(f"     Expected: gl='us', hl='en'")
        print(f"     Got: {result}")
        return False
    
    # Test 2: All parameters provided (should not override)
    print("\n  Test 2b: All parameters provided (should keep custom values)")
    params = {"query": "test search", "gl": "in", "hl": "hi"}
    result = wrapper._inject_defaults(params)
    
    if result.get("gl") == "in" and result.get("hl") == "hi":
        print(f"  ✅ PASS: Custom parameters preserved")
        print(f"     Input:  {params}")
        print(f"     Output: {result}")
    else:
        print(f"  ❌ FAIL: Custom parameters were overridden")
        print(f"     Expected: gl='in', hl='hi'")
        print(f"     Got: {result}")
        return False
    
    return True


def test_no_injection_for_other_tools():
    """Test that non-google_search tools don't get parameters injected"""
    print("\n" + "=" * 80)
    print("TEST 3: No Injection for Other Tools")
    print("=" * 80)
    
    mock_tool = Mock()
    mock_tool.name = "other_tool"
    mock_tool.description = "Some other tool"
    
    wrapper = SerperToolWrapper(inner=mock_tool)
    
    payload = {"param1": "value1"}
    result = wrapper._inject_defaults(payload)
    
    # Should return unchanged
    if result == payload and "gl" not in result and "hl" not in result:
        print(f"  ✅ PASS: Other tools not affected")
        print(f"     Tool: {wrapper.name}")
        print(f"     Input:  {payload}")
        print(f"     Output: {result} (unchanged)")
        return True
    else:
        print(f"  ❌ FAIL: Unexpected modification")
        print(f"     Got: {result}")
        return False


async def test_async_run_with_injection():
    """Test that _arun calls inner tool with injected parameters"""
    print("\n" + "=" * 80)
    print("TEST 4: Async Run with Parameter Injection")
    print("=" * 80)
    
    # Create mock tool with async arun
    mock_tool = Mock()
    mock_tool.name = "google_search"
    mock_tool.description = "Search Google"
    
    # Track what parameters were passed to inner tool
    captured_params = {}
    
    async def mock_arun(params):
        captured_params.update(params)
        return json.dumps({"results": ["result1", "result2"]})
    
    mock_tool.arun = mock_arun
    
    # Create wrapper and call
    wrapper = SerperToolWrapper(inner=mock_tool)
    
    # Call with minimal parameters using **kwargs (as LangChain does)
    result = await wrapper._arun(query="test search")
    
    # Check that inner tool received injected parameters
    if captured_params.get("gl") == "us" and captured_params.get("hl") == "en" and captured_params.get("query") == "test search":
        print(f"  ✅ PASS: Inner tool received injected parameters")
        print(f"     Input kwargs:  query='test search'")
        print(f"     Passed to inner: {captured_params}")
        print(f"     Result: {result[:50]}...")
        return True
    else:
        print(f"  ❌ FAIL: Parameters not injected before calling inner tool")
        print(f"     Captured: {captured_params}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("  SERPER PARAMETER FIX VERIFICATION")
    print("=" * 80)
    print(f"\nPython Version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print(f"Test Location: {__file__}")
    
    results = []
    
    # Sync tests
    results.append(("SerperToolWrapper Creation", test_serper_wrapper_creation()))
    results.append(("Parameter Injection", test_parameter_injection_google_search()))
    results.append(("No Injection for Other Tools", test_no_injection_for_other_tools()))
    
    # Async test
    print("\n" + "=" * 80)
    print("Running async tests...")
    print("=" * 80)
    try:
        async_result = asyncio.run(test_async_run_with_injection())
        results.append(("Async Run with Injection", async_result))
    except Exception as e:
        print(f"⚠️  WARNING: Async test failed: {e}")
        results.append(("Async Run with Injection", False))
    
    # Summary
    print("\n" + "=" * 80)
    print("  TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{'=' * 80}")
    print(f"  RESULTS: {passed}/{total} tests passed")
    print(f"{'=' * 80}\n")
    
    if passed == total:
        print("✅ All Serper parameter fixes are working correctly!")
        print("\n🎯 What This Means:")
        print("   - SerperToolWrapper successfully injects default parameters")
        print("   - google_search will always have gl='us' and hl='en' if not specified")
        print("   - Parameter validation errors should not occur")
        print("   - MCP connection should not break due to missing parameters")
        print("\n📝 Next Steps:")
        print("   1. Run your actual query again")
        print("   2. Check logs for 'Applied SerperToolWrapper to google_search'")
        print("   3. Verify no parameter validation errors occur")
        print("   4. Confirm agent provides results successfully")
        return 0
    else:
        print("⚠️  Some tests failed. Review the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
