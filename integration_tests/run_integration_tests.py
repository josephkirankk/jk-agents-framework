#!/usr/bin/env python3
"""
Convenience script to run integration tests with various options.

Usage:
    python run_integration_tests.py                    # Run all tests
    python run_integration_tests.py --quick            # Run quick tests only
    python run_integration_tests.py --test 1 2         # Run tests 1 and 2
    python run_integration_tests.py --parallel         # Run tests in parallel
    python run_integration_tests.py --markers azure    # Run tests with azure marker
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Run integration tests for jk-agents-core",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_integration_tests.py                     # Run all tests
  python run_integration_tests.py --quick             # Quick tests only
  python run_integration_tests.py --test 1 2 4        # Run tests 1, 2, and 4
  python run_integration_tests.py --parallel          # Parallel execution
  python run_integration_tests.py --markers azure     # Tests with azure marker
  python run_integration_tests.py --verbose           # Verbose output
  python run_integration_tests.py --no-api           # Skip API tests
        """
    )
    
    parser.add_argument(
        "--test",
        nargs="+",
        type=int,
        choices=range(1, 6),
        help="Run specific test numbers (1-5)"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run only quick tests (exclude slow tests)"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel using pytest-xdist"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)"
    )
    
    parser.add_argument(
        "--markers",
        nargs="+",
        choices=["integration", "azure", "google", "anthropic", "chromadb", "slow"],
        help="Run tests with specific markers"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output (show test details)"
    )
    
    parser.add_argument(
        "--no-api",
        action="store_true",
        help="Skip API tests (test_02)"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run with coverage report"
    )
    
    parser.add_argument(
        "--html-report",
        action="store_true",
        help="Generate HTML test report"
    )
    
    args = parser.parse_args()
    
    # Change to integration_tests directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Build pytest command
    cmd = ["pytest"]
    
    # Add verbosity
    if args.verbose:
        cmd.extend(["-v", "-s"])
    else:
        cmd.append("-v")
    
    # Add parallel execution
    if args.parallel:
        cmd.extend(["-n", str(args.workers)])
    
    # Add coverage
    if args.coverage:
        cmd.extend([
            "--cov=../app",
            "--cov-report=html",
            "--cov-report=term"
        ])
    
    # Add HTML report
    if args.html_report:
        cmd.extend([
            "--html=test-results/report.html",
            "--self-contained-html"
        ])
    
    # Select tests to run
    test_files = []
    
    if args.test:
        # Run specific tests
        for test_num in args.test:
            test_file = f"test_{test_num:02d}_*.py"
            test_files.append(test_file)
    elif args.no_api:
        # Skip API tests
        test_files = [
            "test_01_*.py",
            "test_03_*.py",
            "test_04_*.py",
            "test_05_*.py"
        ]
    else:
        # Run all tests
        test_files = ["test_*.py"]
    
    # Add markers
    if args.markers:
        for marker in args.markers:
            cmd.extend(["-m", marker])
    
    # Add quick filter
    if args.quick:
        cmd.extend(["-m", "not slow"])
    
    # Add test files
    cmd.extend(test_files)
    
    # Print command
    print("=" * 80)
    print("Running Integration Tests")
    print("=" * 80)
    print(f"Command: {' '.join(cmd)}")
    print(f"Working directory: {os.getcwd()}")
    print("=" * 80)
    print()
    
    # Check environment
    check_environment()
    
    # Run tests
    try:
        result = subprocess.run(cmd, check=False)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)


def check_environment():
    """Check that environment is properly configured."""
    print("Environment Check:")
    print("-" * 80)
    
    # Check Python version
    import sys
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"✓ Python version: {py_version}")
    
    # Check virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    if in_venv:
        print(f"✓ Virtual environment: {sys.prefix}")
    else:
        print("⚠ Warning: Not running in virtual environment")
    
    # Check key dependencies
    try:
        import pytest
        print(f"✓ pytest: {pytest.__version__}")
    except ImportError:
        print("✗ pytest not installed")
    
    try:
        import langchain
        print(f"✓ langchain installed")
    except ImportError:
        print("✗ langchain not installed")
    
    try:
        import chromadb
        print(f"✓ chromadb installed")
    except ImportError:
        print("⚠ chromadb not installed (required for memory tests)")
    
    # Check environment variables
    from dotenv import load_dotenv
    load_dotenv("../.env")
    
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_key = os.getenv("AZURE_OPENAI_API_KEY")
    
    if azure_endpoint and azure_key:
        print(f"✓ Azure OpenAI credentials configured")
    else:
        print("✗ Azure OpenAI credentials NOT configured")
        print("  Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY in .env")
    
    google_key = os.getenv("GOOGLE_API_KEY")
    if google_key:
        print(f"✓ Google API key configured")
    
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        print(f"✓ Anthropic API key configured")
    
    print("-" * 80)
    print()


if __name__ == "__main__":
    main()
