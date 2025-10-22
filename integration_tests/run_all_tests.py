#!/usr/bin/env python3
"""
Master Integration Test Runner
NO MOCKING - Runs all integration tests in sequence

Usage:
    python run_all_tests.py                    # Run all tests
    python run_all_tests.py --quick            # Run quick tests only
    python run_all_tests.py --test 1 2 3       # Run specific tests
"""

import asyncio
import sys
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from test_utils import TestStats, print_test_header


# Test modules (with async def main() - can run standalone)
TEST_MODULES = [
    {
        "id": 0,
        "name": "Super Integrated Test (Comprehensive)",
        "module": "test_00_super_integrated",
        "quick": False,
        "optional": True,
        "description": "Comprehensive end-to-end test"
    },
    {
        "id": 1,
        "name": "Agent Types (Normal & React)",
        "module": "test_01_agent_types",
        "quick": True,
        "description": "Basic agent creation and invocation"
    },
    {
        "id": 2,
        "name": "Tool Calling and MCP",
        "module": "test_02_tool_calling_mcp",
        "quick": False,
        "description": "Python code execution via MCP"
    },
    {
        "id": 3,
        "name": "ChromaDB Memory",
        "module": "test_03_chromadb_memory",
        "quick": False,
        "description": "Multi-turn conversation memory"
    },
    {
        "id": 4,
        "name": "Large Data Handling",
        "module": "test_04_large_data_handling",
        "quick": True,
        "description": "SQLite storage and compression"
    },
    {
        "id": 5,
        "name": "LiteLLM Multi-Provider",
        "module": "test_05_litellm_providers",
        "quick": True,
        "description": "Azure, Google, Anthropic providers"
    },
    {
        "id": 6,
        "name": "Large Data MCP Demo - Multi-Turn",
        "module": "test_06_large_data_mcp_demo_multi_turn",
        "quick": False,
        "description": "4-turn multi-agent workflow"
    },
    {
        "id": 10,
        "name": "Serper Search Integration",
        "module": "test_10_serper_search_integration",
        "quick": False,
        "optional": True,
        "description": "Google search via Serper MCP (requires SERPER_API_KEY)"
    }
]

# Pytest-based tests (run separately with pytest)
PYTEST_MODULES = [
    "test_00_env_verification.py",
    "test_01_basic_flow.py",
    "test_01_ado_mcp_connection.py",
    "test_02_api_to_llm_flow.py",
    "test_03_worker_end_to_end.py",
    "test_04_memory_multi_turn.py",
    "test_05_error_handling_recovery.py",
    "test_06_mcp_python_tools.py",
    "test_07_large_data_storage.py",
    "test_07_mcp_ado_tools.py",
    "test_08_concurrency_integration.py",
    "test_08_image_processing.py",
    "test_09_api_critical_flows.py",
    "test_auto_summarization_comprehensive.py"
]


async def run_test(test_info):
    """Run a single test module"""
    print(f"\n{'#' * 80}")
    print(f"  Running Test {test_info['id']}: {test_info['name']}")
    if test_info.get('description'):
        print(f"  {test_info['description']}")
    print(f"{'#' * 80}\n")
    
    try:
        # Import and run test module
        module = __import__(test_info['module'])
        if not hasattr(module, 'main'):
            print(f"⚠️  Test module {test_info['module']} has no main() function")
            return False
        
        success = await module.main()
        return success
    except Exception as e:
        print(f"\n❌ Test {test_info['id']} failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all integration tests"""
    parser = argparse.ArgumentParser(description="Run integration tests")
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run only quick tests'
    )
    parser.add_argument(
        '--test',
        nargs='+',
        type=int,
        help='Run specific test IDs (e.g., --test 1 2 3)'
    )
    parser.add_argument(
        '--include-optional',
        action='store_true',
        help='Include optional tests (e.g., Serper search)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available tests and exit'
    )
    
    args = parser.parse_args()
    
    # List tests if requested
    if args.list:
        print("\n" + "=" * 80)
        print("  AVAILABLE INTEGRATION TESTS")
        print("=" * 80 + "\n")
        print("Async-based tests (run with this script):")
        for test in TEST_MODULES:
            optional = " [OPTIONAL]" if test.get('optional') else ""
            quick = " [QUICK]" if test.get('quick') else ""
            print(f"  {test['id']:2d}. {test['name']}{optional}{quick}")
            if test.get('description'):
                print(f"      {test['description']}")
        print(f"\nPytest-based tests (run with 'pytest {Path(__file__).parent}'):")
        for pytest_test in PYTEST_MODULES:
            print(f"  - {pytest_test}")
        print("\n" + "=" * 80 + "\n")
        return True
    
    print_test_header("JK-AGENTS-CORE INTEGRATION TEST SUITE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working Directory: {Path.cwd()}")
    print()
    
    # Determine which tests to run
    tests_to_run = []
    
    if args.test:
        # Run specific tests
        for test_id in args.test:
            test = next((t for t in TEST_MODULES if t['id'] == test_id), None)
            if test:
                tests_to_run.append(test)
            else:
                print(f"⚠️  Warning: Test {test_id} not found")
    elif args.quick:
        # Run quick tests only
        tests_to_run = [t for t in TEST_MODULES if t.get('quick', False)]
        # Exclude optional tests unless explicitly included
        if not args.include_optional:
            tests_to_run = [t for t in tests_to_run if not t.get('optional')]
        print("Running QUICK tests only\n")
    else:
        # Run all tests
        tests_to_run = TEST_MODULES
        # Exclude optional tests unless explicitly included
        if not args.include_optional:
            tests_to_run = [t for t in tests_to_run if not t.get('optional')]
        print("Running ALL tests\n")
    
    if not tests_to_run:
        print("❌ No tests selected!")
        return False
    
    print(f"Tests to run: {len(tests_to_run)}")
    for test in tests_to_run:
        optional = " [OPTIONAL]" if test.get('optional') else ""
        quick = " [QUICK]" if test.get('quick') else ""
        print(f"  {test['id']:2d}. {test['name']}{optional}{quick}")
    
    if not args.include_optional:
        optional_count = sum(1 for t in TEST_MODULES if t.get('optional'))
        if optional_count > 0:
            print(f"\n  (Excluding {optional_count} optional test(s). Use --include-optional to run them)")
    
    pytest_count = len(PYTEST_MODULES)
    print(f"\n  Note: {pytest_count} pytest-based tests not included. Run with: pytest integration_tests/")
    print()
    
    # Run tests
    stats = TestStats()
    results = {}
    
    for test in tests_to_run:
        try:
            success = await run_test(test)
            results[test['id']] = success
            
            if success:
                stats.passed += 1
            else:
                stats.failed += 1
            stats.total += 1
            
        except Exception as e:
            print(f"❌ Test {test['id']} crashed: {e}")
            results[test['id']] = False
            stats.failed += 1
            stats.total += 1
    
    # Print final summary
    print("\n\n")
    print("=" * 80)
    print("  FINAL INTEGRATION TEST SUMMARY")
    print("=" * 80)
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {stats.duration:.2f}s")
    print()
    
    print(f"Total Tests: {stats.total}")
    print(f"✅ Passed: {stats.passed}")
    print(f"❌ Failed: {stats.failed}")
    
    if stats.total > 0:
        print(f"Pass Rate: {(stats.passed / stats.total) * 100:.1f}%")
    
    print("\nTest Results:")
    for test in tests_to_run:
        test_id = test['id']
        status = "✅ PASS" if results.get(test_id, False) else "❌ FAIL"
        print(f"  {status} - Test {test_id}: {test['name']}")
    
    print("\n" + "=" * 80 + "\n")
    
    all_passed = stats.failed == 0
    
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠️  {stats.failed} TEST(S) FAILED")
    
    print()
    
    return all_passed


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
