#!/usr/bin/env python3
"""
Test Data Parser - Verification Script

This script tests the fixed test_data_parser_enterprise.yaml configuration
to verify that the Large Data MCP Server is being used correctly.
"""

import sys
import json
import sqlite3
import requests
from pathlib import Path
from datetime import datetime

class TestDataParserVerifier:
    """Verify the fixed test data parser configuration"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.config_path = "config/test_data_parser_enterprise.yaml"
        self.db_path = "./data/large_tool_data.db"
        self.results = []
    
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log a test result"""
        status = "✅" if passed else "❌"
        self.results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
    
    def test_small_dataset(self) -> bool:
        """Test with small dataset (<= 100 records) - should return full data"""
        print("\n" + "="*80)
        print("TEST 1: Small Dataset (50 records)")
        print("="*80 + "\n")

        try:
            response = requests.post(
                f"{self.base_url}/query/form",
                data={
                    "input": "Generate 50 test records for revenue metric, program MFG, sector PFNA, plant p1, values 10 to 100, uom count",
                    "thread_id": f"test_small_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "config_path": self.config_path
                },
                timeout=60
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Small dataset request",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
            
            result = response.json()
            response_text = result.get("response", "")
            
            # Check for full data (not reference_id)
            has_reference_id = "reference_id" in response_text or "ref_" in response_text
            
            self.log_result(
                "Small dataset returns full data",
                not has_reference_id,
                f"Response length: {len(response_text)} chars"
            )
            
            return not has_reference_id
            
        except Exception as e:
            self.log_result(
                "Small dataset test",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def test_large_dataset(self) -> bool:
        """Test with large dataset (> 100 records) - should use Large Data MCP Server"""
        print("\n" + "="*80)
        print("TEST 2: Large Dataset (1000 records)")
        print("="*80 + "\n")

        try:
            response = requests.post(
                f"{self.base_url}/query/form",
                data={
                    "input": "Generate 1000 test records for revenue and cost metrics, program MFG, sector PFNA, plant p1, values 10 to 100, uom count, 5% negative values from -10 to 1",
                    "thread_id": f"test_large_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "config_path": self.config_path
                },
                timeout=120
            )
            
            if response.status_code != 200:
                self.log_result(
                    "Large dataset request",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
            
            result = response.json()
            response_text = result.get("response", "")
            
            # Check for reference_id
            has_reference_id = "reference_id" in response_text or "ref_" in response_text
            self.log_result(
                "Large dataset returns reference_id",
                has_reference_id,
                f"Response contains reference_id: {has_reference_id}"
            )
            
            # Check for preview (not full data)
            has_preview = "preview" in response_text.lower()
            self.log_result(
                "Large dataset returns preview",
                has_preview,
                f"Response contains preview: {has_preview}"
            )
            
            # Check response is short (not full 1000 records)
            is_short = len(response_text) < 10000  # Full 1000 records would be much longer
            self.log_result(
                "Large dataset response is short",
                is_short,
                f"Response length: {len(response_text)} chars (should be < 10K)"
            )
            
            # Extract reference_id if present
            if has_reference_id:
                import re
                ref_match = re.search(r'ref_[a-zA-Z0-9]+', response_text)
                if ref_match:
                    reference_id = ref_match.group(0)
                    print(f"\n   📋 Reference ID: {reference_id}")
                    return self.verify_database_storage(reference_id)
            
            return has_reference_id and has_preview and is_short
            
        except Exception as e:
            self.log_result(
                "Large dataset test",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def verify_database_storage(self, reference_id: str) -> bool:
        """Verify data is stored in the database"""
        print("\n" + "="*80)
        print("TEST 3: Database Storage Verification")
        print("="*80 + "\n")
        
        try:
            db_path = Path(self.db_path)
            if not db_path.exists():
                self.log_result(
                    "Database file exists",
                    False,
                    f"Database not found: {self.db_path}"
                )
                return False
            
            self.log_result(
                "Database file exists",
                True,
                f"Path: {self.db_path}"
            )
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if reference exists
            cursor.execute(
                "SELECT reference_id, tool_name, record_count, size_bytes, created_at FROM large_data_references WHERE reference_id = ?",
                (reference_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                self.log_result(
                    "Reference ID in database",
                    False,
                    f"Reference ID not found: {reference_id}"
                )
                conn.close()
                return False
            
            ref_id, tool_name, record_count, size_bytes, created_at = row
            
            self.log_result(
                "Reference ID in database",
                True,
                f"Found: {ref_id}"
            )
            
            self.log_result(
                "Record count correct",
                record_count == 1000,
                f"Expected: 1000, Got: {record_count}"
            )
            
            self.log_result(
                "Data size reasonable",
                size_bytes > 0,
                f"Size: {size_bytes:,} bytes ({size_bytes/1024/1024:.2f} MB)"
            )
            
            conn.close()
            return True
            
        except Exception as e:
            self.log_result(
                "Database verification",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*80)
        print("TEST REPORT")
        print("="*80 + "\n")
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {(passed/total)*100:.1f}%\n")
        
        if failed > 0:
            print("Failed Tests:")
            for result in self.results:
                if not result["passed"]:
                    print(f"  ❌ {result['test']}")
                    if result["details"]:
                        print(f"     {result['details']}")
            print()
        
        return failed == 0
    
    def run_tests(self) -> bool:
        """Run all tests"""
        print("\n" + "🧪 "*20)
        print("   TEST DATA PARSER - VERIFICATION TESTS")
        print("🧪 "*20 + "\n")
        
        # Test 1: Small dataset
        test1 = self.test_small_dataset()
        
        # Test 2: Large dataset
        test2 = self.test_large_dataset()
        
        # Generate report
        all_ok = self.generate_report()
        
        if all_ok:
            print("🎉 "*20)
            print("   ALL TESTS PASSED!")
            print("   The Large Data MCP Server is working correctly.")
            print("🎉 "*20 + "\n")
        else:
            print("⚠️  "*20)
            print("   SOME TESTS FAILED")
            print("   Please review the errors above.")
            print("⚠️  "*20 + "\n")
        
        return all_ok


def main():
    """Main test execution"""
    print("\n📋 Prerequisites:")
    print("   1. API server must be running: python api.py")
    print("   2. Configuration: config/test_data_parser_enterprise.yaml")
    print("   3. Large Data MCP Server must be available\n")
    
    input("Press Enter to start tests...")
    
    verifier = TestDataParserVerifier()
    success = verifier.run_tests()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

