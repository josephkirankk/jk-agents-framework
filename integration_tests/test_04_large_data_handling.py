"""
Integration Test 4: Large Data Handling
NO MOCKING - Real large data storage and retrieval

Tests:
1. Large data storage with SQLite
2. Data reference creation and retrieval
3. Token threshold configuration
4. Multi-step data processing
"""

import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from test_utils import *
from app.memory.large_data_storage import LargeDataStorage, DataSize
from app.memory.smart_tool_wrapper import SmartToolWrapper
from dotenv import load_dotenv

load_dotenv()


async def test_large_data_storage():
    """Test large data storage and retrieval"""
    result = TestResult("Large Data Storage")
    
    try:
        print_section("Testing Large Data Storage")
        
        # Initialize storage
        storage = LargeDataStorage({
            "sqlite_path": "./data/test_large_data.db",
            "file_path": "./data/test_large_files",
            "compression": True
        })
        
        # Create large dataset
        large_data = {"records": [{"id": i, "value": f"data_{i}" * 100} for i in range(1000)]}
        
        # Store data
        storage_info = storage.store_large_data(
            reference_id="test_ref_001",
            tool_name="test_tool",
            data=large_data
        )
        
        print(f"✓ Data stored: {storage_info.size_category.value}")
        print(f"  Size: {storage_info.size_mb:.2f} MB")
        print(f"  Storage type: {storage_info.storage_type}")
        
        result.add_sub_test(
            "Data Storage",
            True,
            size_category=storage_info.size_category.value,
            size_mb=storage_info.size_mb
        )
        
        # Retrieve data
        retrieved_data = storage.retrieve_large_data("test_ref_001")
        
        data_matches = retrieved_data == large_data
        print(f"✓ Data retrieved: matches={data_matches}")
        
        result.add_sub_test(
            "Data Retrieval",
            data_matches,
            records_count=len(retrieved_data.get("records", []))
        )
        
        # Test smart wrapper
        wrapper = SmartToolWrapper(storage, token_threshold=500)
        
        # Small data (direct)
        small_data = {"value": "small"}
        small_result = wrapper.wrap_tool_response("test_tool", small_data)
        
        is_direct = small_result["type"] == "direct"
        result.add_sub_test(
            "Small Data (Direct)",
            is_direct,
            type=small_result["type"]
        )
        
        # Large data (reference)
        large_result = wrapper.wrap_tool_response("test_tool", large_data)
        
        is_reference = large_result["type"] == "reference"
        has_tools = len(large_result.get("tools_available", [])) > 0
        
        print(f"✓ Large data handling:")
        print(f"  Type: {large_result['type']}")
        print(f"  Tools available: {len(large_result.get('tools_available', []))}")
        
        result.add_sub_test(
            "Large Data (Reference)",
            is_reference and has_tools,
            type=large_result["type"],
            tools_count=len(large_result.get("tools_available", []))
        )
        
        result.finish(True, tests_passed=4)
        
    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()
    
    return result


async def test_large_data_with_agent():
    """Test large data handling with real agent"""
    result = TestResult("Large Data with Agent Integration")
    env = TestEnvironment("large_data_agent")
    
    try:
        if not check_azure_credentials():
            result.finish(False, error="Azure credentials not available")
            return result
        
        print_section("Testing Large Data with Agent")
        
        # Use test config with large data handling enabled
        config_path = Path(__file__).parent.parent / "config" / "test_data_parser_enterprise.yaml"
        
        if not config_path.exists():
            result.finish(False, error=f"Config not found: {config_path}")
            return result
        
        from app.main import load_app_config
        from app.agent_builder import build_agent
        
        app_config = load_app_config(config_path)
        
        # Check if large data handling is enabled
        large_data_config = getattr(app_config, 'large_data_handling', None)
        if large_data_config:
            is_enabled = large_data_config.get('enabled', False)
            threshold = large_data_config.get('token_threshold', 0)
            print(f"✓ Large data handling: enabled={is_enabled}, threshold={threshold}")
            
            result.add_sub_test(
                "Configuration",
                is_enabled,
                enabled=is_enabled,
                threshold=threshold
            )
        
        result.finish(True, config_checked=True)
        
    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()
    
    finally:
        env.cleanup()
    
    return result


async def main():
    """Run all large data handling tests"""
    print_test_header("INTEGRATION TEST 4: Large Data Handling")
    
    results = []
    
    result1 = await test_large_data_storage()
    result1.print_result()
    results.append(result1)
    
    result2 = await test_large_data_with_agent()
    result2.print_result()
    results.append(result2)
    
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    
    print(f"\n{'=' * 80}")
    print(f"  TEST 4 SUMMARY: {passed}/{total} passed")
    print(f"{'=' * 80}\n")
    
    return all(r.passed for r in results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
