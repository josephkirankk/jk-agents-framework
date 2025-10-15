#!/usr/bin/env python3
"""
Verify environment variable expansion in MCP loader.
"""
import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.mcp_loader import _expand_env_vars


def test_env_expansion():
    """Test various environment variable expansion formats."""
    
    # Set test variables
    os.environ['TEST_VAR_1'] = 'value1'
    os.environ['TEST_VAR_2'] = 'value2'
    os.environ['AZURE_DEVOPS_EXT_PAT'] = 'test-pat-token-123'
    
    print("=" * 80)
    print("Testing Environment Variable Expansion")
    print("=" * 80)
    
    # Test 1: ${VAR} format
    print("\n✅ Test 1: ${VAR} format")
    result1 = _expand_env_vars({'key': '${TEST_VAR_1}'})
    print(f"   Input:  {{'key': '${{TEST_VAR_1}}'}}")
    print(f"   Output: {result1}")
    assert result1['key'] == 'value1', f"Expected 'value1', got {result1['key']}"
    print("   ✓ PASSED")
    
    # Test 2: $VAR format
    print("\n✅ Test 2: $VAR format")
    result2 = _expand_env_vars({'key': '$TEST_VAR_2'})
    print(f"   Input:  {{'key': '$TEST_VAR_2'}}")
    print(f"   Output: {result2}")
    assert result2['key'] == 'value2', f"Expected 'value2', got {result2['key']}"
    print("   ✓ PASSED")
    
    # Test 3: Multiple variables
    print("\n✅ Test 3: Multiple variables in one string")
    result3 = _expand_env_vars({'key': '${TEST_VAR_1}:${TEST_VAR_2}'})
    print(f"   Input:  {{'key': '${{TEST_VAR_1}}:${{TEST_VAR_2}}'}}")
    print(f"   Output: {result3}")
    assert result3['key'] == 'value1:value2', f"Expected 'value1:value2', got {result3['key']}"
    print("   ✓ PASSED")
    
    # Test 4: Azure DevOps PAT token
    print("\n✅ Test 4: Azure DevOps PAT token")
    result4 = _expand_env_vars({'AZURE_DEVOPS_EXT_PAT': '${AZURE_DEVOPS_EXT_PAT}'})
    print(f"   Input:  {{'AZURE_DEVOPS_EXT_PAT': '${{AZURE_DEVOPS_EXT_PAT}}'}}")
    print(f"   Output: {{'AZURE_DEVOPS_EXT_PAT': '{result4['AZURE_DEVOPS_EXT_PAT'][:20]}...'}}")
    assert result4['AZURE_DEVOPS_EXT_PAT'] == 'test-pat-token-123', \
        f"Expected 'test-pat-token-123', got {result4['AZURE_DEVOPS_EXT_PAT']}"
    print("   ✓ PASSED")
    
    # Test 5: Non-existent variable (should remain unchanged)
    print("\n✅ Test 5: Non-existent variable")
    result5 = _expand_env_vars({'key': '${NON_EXISTENT_VAR}'})
    print(f"   Input:  {{'key': '${{NON_EXISTENT_VAR}}'}}")
    print(f"   Output: {result5}")
    assert result5['key'] == '${NON_EXISTENT_VAR}', \
        f"Expected '${{NON_EXISTENT_VAR}}', got {result5['key']}"
    print("   ✓ PASSED (unchanged as expected)")
    
    # Test 6: Direct value (no expansion needed)
    print("\n✅ Test 6: Direct value (no expansion)")
    result6 = _expand_env_vars({'key': 'direct-value'})
    print(f"   Input:  {{'key': 'direct-value'}}")
    print(f"   Output: {result6}")
    assert result6['key'] == 'direct-value', f"Expected 'direct-value', got {result6['key']}"
    print("   ✓ PASSED")
    
    # Test 7: Mixed types
    print("\n✅ Test 7: Non-string values (should pass through)")
    result7 = _expand_env_vars({'num': 123, 'bool': True, 'str': '${TEST_VAR_1}'})
    print(f"   Input:  {{'num': 123, 'bool': True, 'str': '${{TEST_VAR_1}}'}}")
    print(f"   Output: {result7}")
    assert result7['num'] == 123, "Number should pass through unchanged"
    assert result7['bool'] is True, "Boolean should pass through unchanged"
    assert result7['str'] == 'value1', "String should be expanded"
    print("   ✓ PASSED")
    
    print("\n" + "=" * 80)
    print("✓ ALL TESTS PASSED")
    print("=" * 80)
    print("\nEnvironment variable expansion is working correctly!")
    print("\nYou can now run: pytest integration_tests/test_07_mcp_ado_tools.py -v")


if __name__ == "__main__":
    try:
        test_env_expansion()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
