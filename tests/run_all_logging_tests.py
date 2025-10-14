#!/usr/bin/env python3
"""
Test runner for all logging system tests.
Runs all tests for both agentlogs and agents_direct_logs functionality.
"""

import unittest
import sys
from pathlib import Path

# Add the parent directory to the path so we can import test modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Change to tests directory for imports
import os
os.chdir(Path(__file__).resolve().parent)

# Import all test modules
from test_agentlogs_directory import TestAgentlogsDirectory
from test_agents_direct_logs_directory import TestAgentsDirectLogsDirectory  
from test_logging_system_integration import TestLoggingSystemIntegration


def create_test_suite():
    """Create a test suite combining all logging tests."""
    suite = unittest.TestSuite()
    
    # Add agentlogs tests
    suite.addTest(unittest.makeSuite(TestAgentlogsDirectory))
    
    # Add agents_direct_logs tests
    suite.addTest(unittest.makeSuite(TestAgentsDirectLogsDirectory))
    
    # Add integration tests
    suite.addTest(unittest.makeSuite(TestLoggingSystemIntegration))
    
    return suite


def run_all_tests():
    """Run all logging system tests with detailed output."""
    print("🧪 LOGGING SYSTEM COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print()
    
    # Create test suite
    suite = create_test_suite()
    
    # Create test runner with high verbosity
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    
    # Run all tests
    result = runner.run(suite)
    
    print()
    print("=" * 80)
    print("📊 TEST SUMMARY:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("   ✅ ALL TESTS PASSED!")
        print()
        print("🎉 Log directory organization is working correctly!")
        print("   - agentlogs/ directory functionality: ✅ VERIFIED")
        print("   - agents_direct_logs/ directory functionality: ✅ VERIFIED") 
        print("   - Integration between both systems: ✅ VERIFIED")
        print("   - Error handling: ✅ VERIFIED")
        print("   - File separation: ✅ VERIFIED")
        print("   - Concurrent operations: ✅ VERIFIED")
        return True
    else:
        print("   ❌ SOME TESTS FAILED!")
        if result.failures:
            print("\n   Failures:")
            for test, traceback in result.failures:
                print(f"   - {test}: {traceback.split('AssertionError:')[-1].strip()}")
        
        if result.errors:
            print("\n   Errors:")
            for test, traceback in result.errors:
                print(f"   - {test}: {traceback.split('Error:')[-1].strip()}")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
