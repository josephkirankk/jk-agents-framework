"""
Verify SerperToolWrapper Fix

Tests that SerperToolWrapper now correctly handles both positional and keyword arguments.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Set tokenizer parallelism
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import json
import asyncio
from unittest.mock import Mock

from app.mcp_loader import SerperToolWrapper


async def test_wrapper_with_positional_args():
    """Test SerperToolWrapper with positional dict argument (how TimeoutTool calls it)"""
    print("\n" + "=" * 80)
    print("TEST 1: SerperToolWrapper with Positional Dict Argument")
    print("=" * 80)
    
    # Create mock MCP tool
    mock_tool = Mock()
    mock_tool.name = "google_search"
    mock_tool.description = "Search Google"
    
    # Track what parameters were passed to inner tool
    captured_params = {}
    
    async def mock_arun(params):
        captured_params.clear()
        captured_params.update(params)
        return json.dumps({"results": ["result1", "result2"]})
    
    mock_tool.arun = mock_arun
    
    # Create wrapper
    wrapper = SerperToolWrapper(inner=mock_tool)
    
    # Simulate how TimeoutTool calls SerperToolWrapper:
    # It passes payload as a positional argument (not **kwargs)
    payload = {"query": "best smartphones under 20000 rupees India 2025"}
    
    print(f"\n  Calling wrapper._arun(payload) where payload = {payload}")
    result = await wrapper._arun(payload)
    
    # Check that inner tool received 'q' (not 'query') AND injected parameters
    if (captured_params.get("q") == "best smartphones under 20000 rupees India 2025" and
        "query" not in captured_params and  # Should be converted to 'q'
        captured_params.get("gl") == "us" and
        captured_params.get("hl") == "en"):
        print(f"\n  ✅ PASS: Parameters correctly extracted and defaults injected")
        print(f"     Input (positional):  {payload}")
        print(f"     Passed to MCP tool: {captured_params}")
        print(f"     Note: 'query' converted to 'q' for Serper compatibility")
        return True
    else:
        print(f"\n  ❌ FAIL: Parameters not handled correctly")
        print(f"     Expected: q='best smartphones...', gl='us', hl='en' (NO 'query' key)")
        print(f"     Got: {captured_params}")
        return False


async def test_wrapper_with_kwargs():
    """Test SerperToolWrapper with keyword arguments"""
    print("\n" + "=" * 80)
    print("TEST 2: SerperToolWrapper with Keyword Arguments")
    print("=" * 80)
    
    # Create mock MCP tool
    mock_tool = Mock()
    mock_tool.name = "google_search"
    mock_tool.description = "Search Google"
    
    # Track what parameters were passed to inner tool
    captured_params = {}
    
    async def mock_arun(params):
        captured_params.clear()
        captured_params.update(params)
        return json.dumps({"results": ["result1", "result2"]})
    
    mock_tool.arun = mock_arun
    
    # Create wrapper
    wrapper = SerperToolWrapper(inner=mock_tool)
    
    # Call with keyword arguments
    print(f"\n  Calling wrapper._arun(query='test', gl='in')")
    result = await wrapper._arun(query="test search", gl="in")
    
    # Check that inner tool received 'q' (converted from 'query')
    if (captured_params.get("q") == "test search" and
        "query" not in captured_params and  # Should be converted to 'q'
        captured_params.get("gl") == "in" and
        captured_params.get("hl") == "en"):
        print(f"\n  ✅ PASS: Kwargs correctly handled and defaults injected")
        print(f"     Input (kwargs):      query='test search', gl='in'")
        print(f"     Passed to MCP tool: {captured_params}")
        print(f"     Note: 'query' converted to 'q' for Serper compatibility")
        return True
    else:
        print(f"\n  ❌ FAIL: Parameters not handled correctly")
        print(f"     Expected: q='test search', gl='in', hl='en' (NO 'query' key)")
        print(f"     Got: {captured_params}")
        return False


async def test_wrapper_with_list_args():
    """Test SerperToolWrapper with args as list containing dict (as seen in log)"""
    print("\n" + "=" * 80)
    print("TEST 3: SerperToolWrapper with List Containing Dict")
    print("=" * 80)
    
    # Create mock MCP tool
    mock_tool = Mock()
    mock_tool.name = "google_search"
    mock_tool.description = "Search Google"
    
    # Track what parameters were passed to inner tool
    captured_params = {}
    
    async def mock_arun(params):
        captured_params.clear()
        captured_params.update(params)
        return json.dumps({"results": ["result1", "result2"]})
    
    mock_tool.arun = mock_arun
    
    # Create wrapper
    wrapper = SerperToolWrapper(inner=mock_tool)
    
    # Simulate the format seen in log: args=[[{'query': ..., 'gl': 'in', 'hl': 'en'}]]
    # This means the tool receives a list containing a dict
    list_arg = [{'query': 'smartphones India', 'gl': 'in', 'hl': 'en'}]
    
    print(f"\n  Calling wrapper._arun([{{...}}]) with list arg")
    result = await wrapper._arun(list_arg)
    
    # Check that inner tool received 'q' (converted from 'query')
    if (captured_params.get("q") == "smartphones India" and
        "query" not in captured_params and
        captured_params.get("gl") == "in" and
        captured_params.get("hl") == "en"):
        print(f"\n  ✅ PASS: List arg correctly unwrapped and parameters converted")
        print(f"     Input (list):        [{{'query': 'smartphones India', ...}}]")
        print(f"     Passed to MCP tool: {captured_params}")
        print(f"     Note: List unwrapped and 'query' converted to 'q'")
        return True
    else:
        print(f"\n  ❌ FAIL: Parameters not handled correctly")
        print(f"     Expected: q='smartphones India', gl='in', hl='en'")
        print(f"     Got: {captured_params}")
        return False


async def test_empty_query_handling():
    """Test that wrapper warns about missing query"""
    print("\n" + "=" * 80)
    print("TEST 4: Empty Query Handling")
    print("=" * 80)
    
    # Create mock MCP tool
    mock_tool = Mock()
    mock_tool.name = "google_search"
    mock_tool.description = "Search Google"
    
    # Track what parameters were passed to inner tool
    captured_params = {}
    
    async def mock_arun(params):
        captured_params.clear()
        captured_params.update(params)
        return json.dumps({"results": []})
    
    mock_tool.arun = mock_arun
    
    # Create wrapper
    wrapper = SerperToolWrapper(inner=mock_tool)
    
    # Call with empty dict (missing query)
    print(f"\n  Calling wrapper._arun({{}})")
    result = await wrapper._arun({})
    
    # Should still inject gl and hl
    if captured_params.get("gl") == "us" and captured_params.get("hl") == "en":
        print(f"\n  ✅ PASS: Defaults injected even with empty input")
        print(f"     Input (positional):  {{}}")
        print(f"     Passed to MCP tool: {captured_params}")
        print(f"     Note: Warning should be logged about missing query")
        return True
    else:
        print(f"\n  ❌ FAIL: Defaults not injected")
        print(f"     Got: {captured_params}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("  SERPER WRAPPER FIX VERIFICATION")
    print("=" * 80)
    print(f"\nPython Version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print(f"Test Location: {__file__}")
    
    results = []
    
    # Run async tests
    results.append(("Positional Args", await test_wrapper_with_positional_args()))
    results.append(("Keyword Args", await test_wrapper_with_kwargs()))
    results.append(("List Args", await test_wrapper_with_list_args()))
    results.append(("Empty Query Handling", await test_empty_query_handling()))
    
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
        print("✅ SerperToolWrapper fix is working correctly!")
        print("\n🎯 What Was Fixed:")
        print("   - SerperToolWrapper now accepts both *args and **kwargs")
        print("   - Parameters correctly extracted from dict, list, or kwargs")
        print("   - 'query' parameter is converted to 'q' for Serper MCP server")
        print("   - Default gl='us' and hl='en' are injected when missing")
        print("   - Query parameter will no longer be 'undefined'")
        print("\n📝 Next Step:")
        print("   - Run the actual curl command to verify end-to-end")
        return 0
    else:
        print("⚠️  Some tests failed. Review the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
