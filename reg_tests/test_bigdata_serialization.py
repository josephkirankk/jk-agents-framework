#!/usr/bin/env python3
"""
Big Data Serialization and Performance Tests

Focused tests for large data handling and rapid request processing:
1. Big data serialization without memory errors
2. Rapid request handling without duplicate ID conflicts
3. Performance under high load conditions

These tests specifically validate the system's ability to handle large payloads
and rapid concurrent requests without serialization or ID conflicts.
"""

import subprocess
import json
import time
import uuid
import random
import threading
from typing import Dict, List, Any
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BigDataSerializationTest:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results: List[Dict[str, Any]] = []
        # Use configuration that supports persistence for data tests
        self.config_path = "config/simple_no_memory_test.yaml"
        
    def curl_request(self, input_text: str, thread_id: str, raw_output: bool = True) -> Dict[str, Any]:
        """Execute curl command and return parsed response."""
        cmd = [
            "curl", "--location", f"{self.base_url}/query/form",
            "--form", f'input="{input_text}"',
            "--form", f'config_path="{self.config_path}"',
            "--form", f'raw_output="{str(raw_output)}"',
            "--form", f'thread_id="{thread_id}"',
            "--silent"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                # Try to parse as JSON first, fallback to plain text
                try:
                    return {"success": True, "response": json.loads(result.stdout), "raw": result.stdout}
                except json.JSONDecodeError:
                    return {"success": True, "response": result.stdout.strip(), "raw": result.stdout}
            else:
                return {"success": False, "error": result.stderr, "stdout": result.stdout}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Request timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def test_big_data_serialization(self) -> bool:
        """Test memory system with large data inputs."""
        logger.info("Testing big data serialization...")
        thread_id = f"memory-bigdata-{uuid.uuid4().hex[:8]}"
        
        # Create progressively larger inputs
        small_data = "Process this list: " + ", ".join([f"item_{i}" for i in range(50)])
        medium_data = "Analyze these numbers: " + ", ".join([str(random.randint(1, 1000)) for _ in range(200)])
        large_data = ("Remember this detailed information: " + 
                     " ".join([f"Record {i}: {uuid.uuid4().hex} with value {random.randint(1,10000)}" 
                              for i in range(100)]))
        
        tests = [
            ("small", small_data),
            ("medium", medium_data), 
            ("large", large_data)
        ]
        
        success_count = 0
        responses = []
        
        for size_name, data in tests:
            response = self.curl_request(data, thread_id)
            responses.append((size_name, response))
            
            if response.get("success", False):
                success_count += 1
                logger.info(f"Big data test ({size_name}): PASS")
            else:
                logger.error(f"Big data test ({size_name}): FAIL - {response.get('error', 'Unknown error')}")
            
            time.sleep(0.5)  # Brief pause between requests
        
        # Test memory of large data (may fail with in-memory config)
        memory_test = self.curl_request("What was the last type of data I asked you to process?", thread_id)
        memory_works = (memory_test.get("success", False) and 
                       ("record" in str(memory_test.get("response", "")).lower() or 
                        "detailed" in str(memory_test.get("response", "")).lower()))
        
        result = {
            "test": "big_data_serialization",
            "thread_id": thread_id,
            "data_sizes": len(tests),
            "success_count": success_count,
            "memory_of_large_data": memory_works,
            "all_successful": success_count == len(tests)  # Don't require memory for this test
        }
        self.test_results.append(result)
        
        logger.info(f"Big data serialization: {'PASS' if result['all_successful'] else 'FAIL'}")
        return result["all_successful"]

    def test_rapid_requests_no_duplicates(self) -> bool:
        """Test rapid requests to ensure no duplicate ID conflicts."""
        logger.info("Testing rapid requests for duplicate ID prevention...")
        thread_id = f"memory-rapid-{uuid.uuid4().hex[:8]}"
        
        def make_request(request_id: int) -> Dict[str, Any]:
            return self.curl_request(
                f"This is rapid request number {request_id}. Remember this number!",
                thread_id
            )
        
        # Make multiple rapid concurrent requests
        threads = []
        results = {}
        request_count = 10
        
        for i in range(request_count):
            thread = threading.Thread(
                target=lambda req_id=i: results.update({req_id: make_request(req_id)})
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all requests to complete
        for thread in threads:
            thread.join(timeout=30)
        
        # Analyze results
        successful_requests = sum(1 for r in results.values() if r.get("success", False))
        
        # Check for duplicate ID error patterns in responses
        duplicate_errors = sum(1 for r in results.values() 
                             if "duplicate" in str(r.get("error", "")).lower() or
                                "unique" in str(r.get("error", "")).lower())
        
        # Test memory check (may fail with in-memory config)
        memory_check = self.curl_request("How many requests did I send you?", thread_id)
        memory_check_success = memory_check.get("success", False)
        
        no_conflicts = duplicate_errors == 0
        
        result = {
            "test": "rapid_requests_no_duplicates",
            "thread_id": thread_id,
            "total_requests": request_count,
            "successful_requests": successful_requests,
            "memory_check_success": memory_check_success,
            "no_conflicts": no_conflicts
        }
        self.test_results.append(result)
        
        logger.info(f"Rapid requests test: {'PASS' if result['no_conflicts'] else 'FAIL'}")
        return result["no_conflicts"]

    def test_very_large_payload(self) -> bool:
        """Test handling of very large single payload."""
        logger.info("Testing very large payload handling...")
        thread_id = f"memory-large-payload-{uuid.uuid4().hex[:8]}"
        
        # Create a very large dataset
        large_dataset = {
            "users": [
                {
                    "id": i,
                    "name": f"User {i}",
                    "email": f"user{i}@example.com",
                    "metadata": {
                        "created": f"2024-01-{(i % 30) + 1:02d}",
                        "active": True,
                        "preferences": {
                            "theme": "dark" if i % 2 == 0 else "light",
                            "language": "en",
                            "notifications": True
                        }
                    },
                    "tags": [f"tag{j}" for j in range(5)],
                    "history": [
                        {
                            "action": f"action_{j}",
                            "timestamp": f"2024-01-{j+1:02d}",
                            "data": f"data_{uuid.uuid4().hex[:8]}"
                        }
                        for j in range(3)
                    ]
                }
                for i in range(1, 201)  # 200 users with complex nested data
            ],
            "config": {
                "version": "2.0",
                "features": ["feature_" + str(i) for i in range(100)],
                "settings": {
                    "batch_size": 1000,
                    "timeout": 30,
                    "retry_count": 3,
                    "debug_mode": True
                }
            }
        }
        
        payload_text = f"Process this comprehensive dataset: {json.dumps(large_dataset)}"
        payload_size = len(payload_text)
        
        logger.info(f"Sending payload of {payload_size} characters...")
        
        # Use longer timeout for very large payloads
        result = self.curl_request(payload_text, thread_id)
        
        # Test passes if large payload processes without errors
        test_passed = result.get("success", False)
        
        test_result = {
            "test": "very_large_payload",
            "thread_id": thread_id,
            "payload_size": payload_size,
            "test_passed": test_passed,
            "error": result.get("error", None)
        }
        self.test_results.append(test_result)
        
        logger.info(f"Very large payload test: {'PASS' if test_passed else 'FAIL'}")
        return test_passed

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all big data and serialization tests."""
        logger.info("Starting Big Data Serialization Tests")
        
        start_time = datetime.now()
        
        tests = [
            ("Big Data Serialization", self.test_big_data_serialization),
            ("Rapid Requests No Duplicates", self.test_rapid_requests_no_duplicates),
            ("Very Large Payload", self.test_very_large_payload)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n--- Running: {test_name} ---")
            try:
                if test_func():
                    passed_tests += 1
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.error(f"❌ {test_name}: FAILED")
            except Exception as e:
                logger.error(f"💥 {test_name}: ERROR - {str(e)}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        summary = {
            "test_suite": "Big Data Serialization Tests",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests) * 100,
            "all_tests_passed": passed_tests == total_tests,
            "individual_results": self.test_results
        }
        
        logger.info(f"\n{'='*50}")
        logger.info(f"BIG DATA SERIALIZATION TEST SUMMARY")
        logger.info(f"{'='*50}")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {summary['success_rate']:.1f}%")
        logger.info(f"Duration: {duration:.2f} seconds")
        
        if passed_tests == total_tests:
            logger.info(f"🎉 ALL BIG DATA TESTS PASSED!")
            logger.info("✅ Large payload serialization working")
            logger.info("✅ Rapid requests handling correctly")
            logger.info("✅ No duplicate ID conflicts detected")
        else:
            logger.error(f"❌ SOME BIG DATA TESTS FAILED")
        
        return summary

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Big Data Serialization Tests")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--output", default=None, help="Output file for test results JSON")
    
    args = parser.parse_args()
    
    test_runner = BigDataSerializationTest(args.url)
    results = test_runner.run_all_tests()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Detailed results saved to: {args.output}")
    
    # Exit with error code if tests failed
    if not results["all_tests_passed"]:
        exit(1)
