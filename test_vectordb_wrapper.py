"""
Test script for VectorDB wrapper functionality.

This script tests the VectorDB wrapper against a real VectorDB API server
running on localhost:8010. It performs comprehensive testing of search,
upsert, and error handling functionality.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vectordb_wrapper import (
    VectorDBClient,
    SearchRequest,
    UpsertRequest,
    vectordb_wrapper
)
from vectordb_wrapper.exceptions import VectorDBError, VectorDBConnectionError
from vectordb_wrapper.utils import setup_logging, format_search_results


# Setup logging
setup_logging("INFO")
logger = logging.getLogger(__name__)


class VectorDBTester:
    """Test class for VectorDB wrapper functionality."""
    
    def __init__(self, base_url: str = "http://localhost:8010"):
        self.base_url = base_url
        self.test_results = []
        self.test_defect_code = f"TEST.WRAPPER.{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def log_test_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result."""
        status = "PASS" if success else "FAIL"
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        logger.info(f"[{status}] {test_name}: {message}")
    
    async def test_health_check(self):
        """Test health check endpoint."""
        try:
            async with VectorDBClient(base_url=self.base_url) as client:
                health = await client.health_check()
                
                if health.status and health.pinecone_connected:
                    self.log_test_result(
                        "Health Check", 
                        True, 
                        f"Status: {health.status}, Pinecone: {health.pinecone_connected}"
                    )
                    return True
                else:
                    self.log_test_result(
                        "Health Check", 
                        False, 
                        f"Unhealthy status: {health.status}"
                    )
                    return False
                    
        except Exception as e:
            self.log_test_result("Health Check", False, f"Exception: {str(e)}")
            return False
    
    async def test_upsert_defect(self):
        """Test upserting a defect."""
        try:
            async with VectorDBClient(base_url=self.base_url) as client:
                request = UpsertRequest(
                    defect_code=self.test_defect_code,
                    defect_text="Test defect for wrapper validation - motor bearing failure with vibration",
                    subsystem="MOT",
                    severity="High",
                    typical_frequency="Medium",
                    symptoms=["excessive vibration", "abnormal noise", "overheating"],
                    detection_methods=["vibration analysis", "temperature monitoring"],
                    early_warning_signals=["slight vibration increase"],
                    tags=["motor", "bearing", "vibration", "test"],
                    likely_root_causes=["lack of lubrication", "contamination", "misalignment"],
                    recommended_actions=["replace bearing", "check lubrication", "verify alignment"]
                )
                
                response = await client.upsert(request)
                
                if response.success and response.defect_code == self.test_defect_code:
                    self.log_test_result(
                        "Upsert Defect", 
                        True, 
                        f"Operation: {response.operation}, Message: {response.message}"
                    )
                    return True
                else:
                    self.log_test_result(
                        "Upsert Defect", 
                        False, 
                        f"Unexpected response: {response.message}"
                    )
                    return False
                    
        except Exception as e:
            self.log_test_result("Upsert Defect", False, f"Exception: {str(e)}")
            return False
    
    async def test_search_post(self):
        """Test POST search functionality."""
        try:
            async with VectorDBClient(base_url=self.base_url) as client:
                request = SearchRequest(
                    query="motor bearing failure vibration",
                    top_n=5,
                    min_score=0.5
                )
                
                response = await client.search(request)
                
                if response.total_results >= 0 and response.execution_time_ms > 0:
                    found_test_defect = any(
                        result.defect.defect_code == self.test_defect_code 
                        for result in response.results
                    )
                    
                    self.log_test_result(
                        "Search POST", 
                        True, 
                        f"Found {response.total_results} results in {response.execution_time_ms}ms, "
                        f"Test defect found: {found_test_defect}"
                    )
                    return True
                else:
                    self.log_test_result(
                        "Search POST", 
                        False, 
                        f"Invalid response: {response.total_results} results"
                    )
                    return False
                    
        except Exception as e:
            self.log_test_result("Search POST", False, f"Exception: {str(e)}")
            return False
    
    async def test_search_get(self):
        """Test GET search functionality."""
        try:
            async with VectorDBClient(base_url=self.base_url) as client:
                response = await client.search_get(
                    query="bearing failure",
                    top_n=3,
                    min_score=0.7
                )
                
                if response.total_results >= 0 and response.execution_time_ms > 0:
                    self.log_test_result(
                        "Search GET", 
                        True, 
                        f"Found {response.total_results} results in {response.execution_time_ms}ms"
                    )
                    return True
                else:
                    self.log_test_result(
                        "Search GET", 
                        False, 
                        f"Invalid response: {response.total_results} results"
                    )
                    return False
                    
        except Exception as e:
            self.log_test_result("Search GET", False, f"Exception: {str(e)}")
            return False
    
    async def test_decorator_function(self, client: VectorDBClient):
        """Test function for the vectordb_wrapper decorator."""
        try:
            request = SearchRequest(query="pump failure", top_n=2)
            response = await client.search(request)
            return response
        except Exception as e:
            logger.error(f"Decorator test exception: {e}")
            return None
    
    async def test_decorator_functionality(self):
        """Test decorator functionality."""
        try:
            # Create a decorated version of the test function
            from vectordb_wrapper.decorators import vectordb_wrapper

            @vectordb_wrapper(log_requests=True, log_responses=True)
            async def decorated_search(client: VectorDBClient):
                request = SearchRequest(query="pump failure", top_n=2)
                return await client.search(request)

            result = await decorated_search()
            success = result is not None and hasattr(result, 'total_results')
            message = (
                f"Found {result.total_results} results" if success
                else "Decorator failed"
            )
            self.log_test_result("Decorator Test", success, message)
            return success
        except Exception as e:
            self.log_test_result("Decorator Test", False, f"Exception: {str(e)}")
            return False
    
    async def test_error_handling(self):
        """Test error handling with invalid requests."""
        try:
            # Test with invalid base URL
            try:
                async with VectorDBClient(base_url="http://invalid-url:9999", timeout=5.0) as client:
                    await client.health_check()
                self.log_test_result("Error Handling", False, "Should have failed with invalid URL")
                return False
            except VectorDBConnectionError:
                self.log_test_result("Error Handling", True, "Correctly caught connection error")
                return True
            except Exception as e:
                self.log_test_result("Error Handling", True, f"Caught expected error: {type(e).__name__}")
                return True
                
        except Exception as e:
            self.log_test_result("Error Handling", False, f"Unexpected exception: {str(e)}")
            return False
    
    async def test_validation(self):
        """Test request validation."""
        try:
            async with VectorDBClient(base_url=self.base_url) as client:
                # Test with invalid search request (empty query should fail validation)
                try:
                    request = SearchRequest(query="", top_n=5)  # Empty query should fail
                    await client.search(request)
                    self.log_test_result("Validation Test", False, "Should have failed with empty query")
                    return False
                except Exception:
                    self.log_test_result("Validation Test", True, "Correctly caught validation error")
                    return True
                    
        except Exception as e:
            self.log_test_result("Validation Test", False, f"Unexpected exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all tests and return summary."""
        print("=" * 60)
        print("VectorDB Wrapper Test Suite")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"Test defect code: {self.test_defect_code}")
        print()
        
        # Run tests in order
        tests = [
            ("Health Check", self.test_health_check),
            ("Upsert Defect", self.test_upsert_defect),
            ("Search POST", self.test_search_post),
            ("Search GET", self.test_search_get),
            ("Decorator Test", self.test_decorator_functionality),
            ("Error Handling", self.test_error_handling),
            ("Validation Test", self.test_validation),
        ]
        
        for test_name, test_func in tests:
            print(f"Running {test_name}...")
            await test_func()
            print()
        
        # Print summary
        print("=" * 60)
        print("Test Summary")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["status"] == "PASS")
        total = len(self.test_results)
        
        for result in self.test_results:
            status_icon = "✓" if result["status"] == "PASS" else "✗"
            print(f"{status_icon} {result['test']}: {result['message']}")
        
        print()
        print(f"Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed!")
            return True
        else:
            print("❌ Some tests failed!")
            return False


async def main():
    """Main test function."""
    # Check if VECTORDB_BASE_URL is set
    base_url = os.getenv("VECTORDB_BASE_URL", "http://localhost:8010")
    
    print(f"VectorDB Wrapper Test Suite")
    print(f"Base URL: {base_url}")
    print()
    
    # Create tester and run tests
    tester = VectorDBTester(base_url=base_url)
    success = await tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
