#!/usr/bin/env python3
"""
Integration Test Runner for JK-Agents Framework

This script runs comprehensive integration tests for the JK-Agents Framework,
including multi-model and multi-turn conversation tests. It validates:

1. API key loading from .env file
2. Multi-model support (Azure, Google, OpenAI, etc.)
3. Multi-turn conversation with context preservation
4. Tool binding for different model providers
5. Memory system integration

Run with:
  python run_integration_tests.py [test_names]

Examples:
  python run_integration_tests.py                  # Run all tests
  python run_integration_tests.py model_test       # Run just the model test
  python run_integration_tests.py multiturn gemini # Run multiturn and gemini tests
"""

import os
import sys
import subprocess
from pathlib import Path
import argparse

# ANSI color codes
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

# Define test modules
TEST_MODULES = {
    "model_test": {
        "file": "tests/test_litellm_multimodel_integration.py",
        "description": "Multi-model provider integration test"
    },
    "multiturn": {
        "file": "tests/test_litellm_multiturn_workflow.py",
        "description": "Multi-turn conversation workflow test"
    },
    "gemini": {
        "file": "tests/test_gemini_tool_binding.py",
        "description": "Google Gemini tool binding test"
    }
}

def print_header(text):
    """Print a formatted header."""
    border = "=" * (len(text) + 8)
    print(f"\n{BLUE}{border}{RESET}")
    print(f"{BLUE}==  {text}  =={RESET}")
    print(f"{BLUE}{border}{RESET}\n")

def run_test(test_name, test_info):
    """Run a specific test module."""
    print_header(f"Running {test_name}: {test_info['description']}")
    
    # Check if the test file exists
    test_path = Path(test_info["file"])
    if not test_path.exists():
        print(f"{RED}Error: Test file {test_path} not found{RESET}")
        return False
    
    # Activate virtual environment and run the test
    cmd = [sys.executable, str(test_path)]
    try:
        # Run the test and capture output
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        # Print the output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"{RED}STDERR:{RESET}\n{result.stderr}")
        
        # Check if the test was successful
        success = result.returncode == 0
        if success:
            print(f"{GREEN}✓ {test_name} completed successfully (exit code {result.returncode}){RESET}")
        else:
            print(f"{RED}✗ {test_name} failed with exit code {result.returncode}{RESET}")
        
        return success
    except Exception as e:
        print(f"{RED}Error running {test_name}: {str(e)}{RESET}")
        return False

def main():
    """Main entry point for the test runner."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run integration tests for JK-Agents Framework")
    parser.add_argument("tests", nargs="*", help="Specific tests to run (default: all)")
    args = parser.parse_args()
    
    # Determine which tests to run
    tests_to_run = {}
    if args.tests:
        for test in args.tests:
            if test in TEST_MODULES:
                tests_to_run[test] = TEST_MODULES[test]
            else:
                print(f"{YELLOW}Warning: Unknown test '{test}', skipping{RESET}")
    else:
        tests_to_run = TEST_MODULES
    
    if not tests_to_run:
        print(f"{RED}Error: No valid tests specified{RESET}")
        print(f"Available tests: {', '.join(TEST_MODULES.keys())}")
        return 1
    
    # Print header
    print_header("JK-AGENTS FRAMEWORK INTEGRATION TEST SUITE")
    print(f"Running {len(tests_to_run)} test modules:")
    for test_name, test_info in tests_to_run.items():
        print(f"  {BLUE}•{RESET} {test_name}: {test_info['description']}")
    
    # Check for .env file
    env_path = Path(".env")
    if env_path.exists():
        print(f"\n{GREEN}✓ Found .env file at project root{RESET}")
    else:
        print(f"\n{YELLOW}Warning: No .env file found at project root{RESET}")
        print(f"{YELLOW}Some tests may fail due to missing API credentials{RESET}")
    
    # Run the tests
    results = {}
    for test_name, test_info in tests_to_run.items():
        results[test_name] = run_test(test_name, test_info)
    
    # Print summary
    print_header("TEST SUMMARY")
    passed = sum(1 for success in results.values() if success)
    failed = len(results) - passed
    
    for test_name, success in results.items():
        status = f"{GREEN}PASS{RESET}" if success else f"{RED}FAIL{RESET}"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {len(results)}, {GREEN}Passed: {passed}{RESET}, {RED}Failed: {failed}{RESET}")
    
    # Return exit code based on test results
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
