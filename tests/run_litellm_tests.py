#!/usr/bin/env python3
"""
Runner script for LiteLLM integration test with the JK-Agents Framework.
This script runs the LiteLLM wrapper integration test and reports the results.
"""

import os
import sys
import asyncio
from pathlib import Path
import importlib.util
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env")
except ImportError:
    print("⚠️ dotenv not installed, skipping environment loading")

async def run_test(test_module_name, test_function_name):
    """Run a test from the specified module and function"""
    print(f"\n{'=' * 80}")
    print(f"RUNNING TEST: {test_module_name} - {test_function_name}")
    print(f"{'=' * 80}")
    
    try:
        # Import the test module
        spec = importlib.util.spec_from_file_location(
            test_module_name, 
            str(Path(__file__).parent / f"{test_module_name}.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get the test function
        test_func = getattr(module, test_function_name)
        
        # Run the test
        start_time = time.time()
        result = await test_func()
        end_time = time.time()
        
        # Report result
        duration = round(end_time - start_time, 2)
        status = "PASSED" if result else "FAILED"
        print(f"\nTest {test_module_name} - {test_function_name}: {status} (took {duration}s)")
        
        return result
    except Exception as e:
        print(f"\n❌ Error running test {test_module_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def run_all_tests():
    """Run all LiteLLM integration tests"""
    print("🚀 Running LiteLLM Integration Tests for JK-Agents Framework")
    print("=" * 80)
    
    # Define tests to run
    tests = [
        # Module name, function name
        ("test_litellm_wrapper_integration", "test_litellm_model_with_framework")
    ]
    
    # Results tracking
    results = {}
    
    # Run each test
    for test_module, test_func in tests:
        results[(test_module, test_func)] = await run_test(test_module, test_func)
    
    # Report overall results
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for (module, func), result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {module}.{func}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    # Return True if all tests passed
    return passed == total

if __name__ == "__main__":
    # Check if test modules exist
    required_modules = [
        "test_litellm_wrapper_integration.py"
    ]
    
    missing_modules = []
    for module in required_modules:
        if not Path(__file__).parent.joinpath(module).exists():
            missing_modules.append(module)
    
    if missing_modules:
        print(f"❌ Missing test modules: {', '.join(missing_modules)}")
        print("Please ensure all test files are created before running this script.")
        sys.exit(1)
    
    # Create test image if needed
    try:
        from create_test_image import create_test_image
        create_test_image()
    except Exception as e:
        print(f"⚠️ Warning: Could not create test image: {e}")
    
    # Run tests
    asyncio.run(run_all_tests())
