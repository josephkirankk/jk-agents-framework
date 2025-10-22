"""
Test Serper Error Fixes

Verifies that:
1. Graceful degradation for scrape failures works
2. Logging configuration works correctly
3. Log files are created in the right location
4. Error messages are clear and actionable
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Set tokenizer parallelism before imports
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import json
from unittest.mock import Mock, AsyncMock
import asyncio

from app.mcp_loader import TimeoutTool
from app.logging_config import (
    quick_setup, 
    get_log_directory, 
    list_recent_logs,
    print_log_info
)


def test_log_directory():
    """Test that log directory can be located"""
    print("\n" + "=" * 80)
    print("TEST 1: Log Directory Detection")
    print("=" * 80)
    
    log_dir = get_log_directory()
    
    print(f"  Log directory: {log_dir}")
    print(f"  Exists: {log_dir.exists()}")
    
    if not log_dir.exists():
        print(f"  Creating directory...")
        log_dir.mkdir(parents=True, exist_ok=True)
    
    if log_dir.exists() and log_dir.is_dir():
        print("  ✅ PASS: Log directory is accessible")
        return True
    else:
        print("  ❌ FAIL: Cannot access log directory")
        return False


def test_logging_setup():
    """Test that logging can be configured"""
    print("\n" + "=" * 80)
    print("TEST 2: Logging Configuration")
    print("=" * 80)
    
    try:
        log_file = quick_setup(verbose=False)
        print(f"  ✅ PASS: Logging configured")
        print(f"  Log file: {log_file}")
        
        if log_file.parent.exists():
            print(f"  ✅ PASS: Log directory exists")
            return True
        else:
            print(f"  ❌ FAIL: Log directory doesn't exist: {log_file.parent}")
            return False
            
    except Exception as e:
        print(f"  ❌ FAIL: Logging setup failed: {e}")
        return False


def test_recent_logs():
    """Test that we can list recent logs"""
    print("\n" + "=" * 80)
    print("TEST 3: Recent Logs Listing")
    print("=" * 80)
    
    try:
        recent = list_recent_logs(count=5)
        print(f"  Found {len(recent)} recent log files")
        
        if recent:
            for i, log_file in enumerate(recent[:3], 1):
                size_kb = log_file.stat().st_size / 1024
                print(f"    {i}. {log_file.name} ({size_kb:.1f} KB)")
            print("  ✅ PASS: Can list recent logs")
        else:
            print("  ⚠️  WARNING: No log files found (this might be first run)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ FAIL: Cannot list logs: {e}")
        return False


async def test_scrape_graceful_degradation():
    """Test that scrape failures are handled gracefully"""
    print("\n" + "=" * 80)
    print("TEST 4: Scrape Tool Graceful Degradation")
    print("=" * 80)
    
    # Create a mock scrape tool that simulates 500 error
    mock_tool = Mock()
    mock_tool.name = "scrape"
    mock_tool.description = "Web scraping tool"
    
    # Simulate Serper scrape 500 error
    async def failing_scrape(payload):
        raise Exception(
            "SearchTool: failed to scrape. Error: Serper API error: "
            "500 Internal Server Error - {\"message\":\"Scraping failed.\",\"statusCode\":500}"
        )
    
    mock_tool.arun = failing_scrape
    
    # Wrap with TimeoutTool
    timeout_tool = TimeoutTool(inner=mock_tool, timeout=5.0, retries=1)
    
    try:
        result = await timeout_tool._arun({"url": "https://example.com"})
        
        # Should return graceful error message, not crash
        if isinstance(result, str):
            result_data = json.loads(result)
            
            if result_data.get("error") == "scrape_unavailable":
                print("  ✅ PASS: Graceful degradation works")
                print(f"  Message: {result_data.get('message')}")
                print(f"  Suggestion: {result_data.get('suggestion')}")
                return True
            else:
                print(f"  ❌ FAIL: Unexpected result: {result_data}")
                return False
        else:
            print(f"  ❌ FAIL: Result is not a string: {type(result)}")
            return False
            
    except Exception as e:
        print(f"  ❌ FAIL: Exception raised (should be handled): {e}")
        return False


async def test_non_scrape_error_still_raises():
    """Test that non-scrape errors still raise properly"""
    print("\n" + "=" * 80)
    print("TEST 5: Non-Scrape Errors Still Raise")
    print("=" * 80)
    
    # Create a mock tool (not scrape) that fails
    mock_tool = Mock()
    mock_tool.name = "google_search"
    mock_tool.description = "Google search tool"
    
    async def failing_search(payload):
        raise ValueError("Authentication failed")
    
    mock_tool.arun = failing_search
    
    # Wrap with TimeoutTool
    timeout_tool = TimeoutTool(inner=mock_tool, timeout=5.0, retries=1)
    
    try:
        result = await timeout_tool._arun({"query": "test"})
        print(f"  ❌ FAIL: Should have raised exception")
        return False
        
    except Exception as e:
        if "Authentication failed" in str(e):
            print("  ✅ PASS: Non-scrape errors still raise properly")
            print(f"  Exception: {type(e).__name__}: {e}")
            return True
        else:
            print(f"  ❌ FAIL: Wrong exception: {e}")
            return False


def test_log_info_display():
    """Test that log info can be displayed"""
    print("\n" + "=" * 80)
    print("TEST 6: Log Info Display")
    print("=" * 80)
    
    try:
        print_log_info()
        print("  ✅ PASS: Log info displayed successfully")
        return True
        
    except Exception as e:
        print(f"  ❌ FAIL: Cannot display log info: {e}")
        return False


async def run_async_tests():
    """Run all async tests"""
    results = []
    
    results.append(("Scrape Graceful Degradation", await test_scrape_graceful_degradation()))
    results.append(("Non-Scrape Errors Raise", await test_non_scrape_error_still_raises()))
    
    return results


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("  SERPER ERROR FIXES VERIFICATION")
    print("=" * 80)
    print(f"\nPython Version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print(f"Test Location: {__file__}")
    
    results = []
    
    # Sync tests
    results.append(("Log Directory", test_log_directory()))
    results.append(("Logging Setup", test_logging_setup()))
    results.append(("Recent Logs", test_recent_logs()))
    
    # Async tests
    print("\n" + "=" * 80)
    print("Running async tests...")
    print("=" * 80)
    try:
        async_results = asyncio.run(run_async_tests())
        results.extend(async_results)
    except Exception as e:
        print(f"⚠️  WARNING: Async tests failed: {e}")
        results.append(("Async Tests", False))
    
    # Display test
    results.append(("Log Info Display", test_log_info_display()))
    
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
        print("✅ All Serper error fixes are working correctly!")
        print("\n📋 Log Files:")
        log_dir = get_log_directory()
        print(f"   Location: {log_dir}")
        recent = list_recent_logs(count=3)
        if recent:
            for log_file in recent:
                print(f"   - {log_file.name}")
        
        print("\n🎯 Next Steps:")
        print("   1. Test with actual Serper queries")
        print("   2. Check that scrape failures are handled gracefully")
        print("   3. Verify logs are being written correctly")
        print(f"   4. View logs: tail -f {log_dir}/agentlog_*.log")
        return 0
    else:
        print("⚠️  Some tests failed. Review the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
