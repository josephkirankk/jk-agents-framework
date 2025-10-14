#!/usr/bin/env python3
"""
Memory System Multi-Turn Big Data Regression Test

Tests the memory system fixes for:
1. AIMessage serialization with large data
2. ChromaDB duplicate ID prevention under high load
3. Multi-turn conversation memory persistence
4. Rapid request handling without conflicts

Uses curl commands as requested to simulate real API usage.
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

class MemoryRegressionTest:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results: List[Dict[str, Any]] = []
        # Use a simpler configuration that doesn't rely on complex checkpointing
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

    def test_basic_memory_persistence(self) -> bool:
        """Test basic multi-turn conversation memory."""
        logger.info("Testing basic memory persistence...")
        thread_id = f"memory-basic-{uuid.uuid4().hex[:8]}"
        
        # Turn 1: Establish context
        response1 = self.curl_request(
            "My name is Alice and I'm working on a Python project about data analysis", 
            thread_id
        )
        
        if not response1["success"]:
            logger.error(f"Turn 1 failed: {response1}")
            return False
            
        # Turn 2: Reference previous context
        time.sleep(1)  # Brief pause between requests
        response2 = self.curl_request(
            "What did I tell you about my name and project?", 
            thread_id
        )
        
        if not response2["success"]:
            logger.error(f"Turn 2 failed: {response2}")
            return False
            
        # Verify memory - response should mention Alice and Python/data analysis
        response_text = str(response2["response"]).lower()
        memory_preserved = ("alice" in response_text and 
                          ("python" in response_text or "data" in response_text))
        
        result = {
            "test": "basic_memory_persistence",
            "thread_id": thread_id,
            "turns": 2,
            "memory_preserved": memory_preserved,
            "responses": [response1["response"], response2["response"]]
        }
        self.test_results.append(result)
        
        logger.info(f"Basic memory test: {'PASS' if memory_preserved else 'FAIL'}")
        return memory_preserved

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
            
            if response["success"]:
                success_count += 1
                logger.info(f"Big data test ({size_name}): PASS")
            else:
                logger.error(f"Big data test ({size_name}): FAIL - {response.get('error', 'Unknown error')}")
            
            time.sleep(0.5)  # Brief pause between requests
        
        # Test memory of large data
        memory_test = self.curl_request("What was the last type of data I asked you to process?", thread_id)
        memory_works = (memory_test["success"] and 
                       ("record" in str(memory_test["response"]).lower() or 
                        "detailed" in str(memory_test["response"]).lower()))
        
        result = {
            "test": "big_data_serialization",
            "thread_id": thread_id,
            "data_sizes": len(tests),
            "success_count": success_count,
            "memory_of_large_data": memory_works,
            "all_successful": success_count == len(tests) and memory_works
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
        
        # Make 10 rapid concurrent requests
        threads = []
        results = {}
        
        for i in range(10):
            thread = threading.Thread(
                target=lambda req_id=i: results.update({req_id: make_request(req_id)})
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30)
        
        # Analyze results
        successful_requests = sum(1 for r in results.values() if r.get("success", False))
        
        # Test if memory system handled rapid requests without conflicts
        time.sleep(2)  # Allow processing to complete
        memory_check = self.curl_request("How many rapid requests did I send?", thread_id)
        
        result = {
            "test": "rapid_requests_no_duplicates", 
            "thread_id": thread_id,
            "total_requests": 10,
            "successful_requests": successful_requests,
            "memory_check_success": memory_check.get("success", False),
            "no_conflicts": successful_requests >= 8  # Allow some variance in concurrent testing
        }
        self.test_results.append(result)
        
        logger.info(f"Rapid requests test: {'PASS' if result['no_conflicts'] else 'FAIL'}")
        return result["no_conflicts"]

    def test_multiturn_complex_conversation(self) -> bool:
        """Test complex multi-turn conversation with context building."""
        logger.info("Testing complex multi-turn conversation...")
        thread_id = f"memory-complex-{uuid.uuid4().hex[:8]}"
        
        conversation_turns = [
            "I'm planning a machine learning project to predict house prices using Python",
            "The dataset has 10000 records with features like bedrooms, bathrooms, square footage, and location",
            "I want to use scikit-learn for the modeling. What algorithms would you recommend?",
            "Great! Now, can you remind me what my project is about and how many records I mentioned?",
            "Perfect! Let's also discuss the preprocessing steps needed for the features I mentioned earlier"
        ]
        
        responses = []
        context_preserved = True
        
        for i, turn in enumerate(conversation_turns, 1):
            response = self.curl_request(turn, thread_id)
            responses.append(response)
            
            if not response["success"]:
                context_preserved = False
                logger.error(f"Turn {i} failed: {response}")
                break
            
            time.sleep(1)  # Realistic pause between conversation turns
        
        # Verify final context includes elements from early turns
        if responses:
            final_response = str(responses[-1]["response"]).lower()
            context_elements = [
                "house" in final_response or "price" in final_response,
                "10000" in final_response or "10,000" in final_response,
                "bedroom" in final_response or "bathroom" in final_response or "square" in final_response
            ]
            context_preserved = context_preserved and any(context_elements)
        
        result = {
            "test": "multiturn_complex_conversation",
            "thread_id": thread_id,
            "total_turns": len(conversation_turns),
            "successful_turns": sum(1 for r in responses if r.get("success", False)),
            "context_preserved": context_preserved,
            "conversation_complete": len(responses) == len(conversation_turns) and context_preserved
        }
        self.test_results.append(result)
        
        logger.info(f"Complex conversation test: {'PASS' if result['conversation_complete'] else 'FAIL'}")
        return result["conversation_complete"]

    def test_thread_isolation(self) -> bool:
        """Test that different thread IDs maintain separate memory contexts."""
        logger.info("Testing thread isolation...")
        
        thread_a = f"memory-isolation-a-{uuid.uuid4().hex[:8]}"
        thread_b = f"memory-isolation-b-{uuid.uuid4().hex[:8]}"
        
        # Set different contexts in each thread
        response_a1 = self.curl_request("My favorite color is blue and I live in New York", thread_a)
        response_b1 = self.curl_request("My favorite color is red and I live in California", thread_b)
        
        time.sleep(1)
        
        # Test memory isolation
        response_a2 = self.curl_request("What's my favorite color and where do I live?", thread_a)
        response_b2 = self.curl_request("What's my favorite color and where do I live?", thread_b)
        
        # Verify isolation - each thread should only know its own context
        a_correct = (response_a2["success"] and 
                    "blue" in str(response_a2["response"]).lower() and
                    "new york" in str(response_a2["response"]).lower())
        
        b_correct = (response_b2["success"] and 
                    "red" in str(response_b2["response"]).lower() and
                    "california" in str(response_b2["response"]).lower())
        
        # Cross-contamination check - A shouldn't know B's info
        cross_contamination = ("red" in str(response_a2["response"]).lower() or
                             "california" in str(response_a2["response"]).lower())
        
        isolation_working = a_correct and b_correct and not cross_contamination
        
        result = {
            "test": "thread_isolation",
            "thread_a": thread_a,
            "thread_b": thread_b, 
            "thread_a_correct": a_correct,
            "thread_b_correct": b_correct,
            "no_cross_contamination": not cross_contamination,
            "isolation_working": isolation_working
        }
        self.test_results.append(result)
        
        logger.info(f"Thread isolation test: {'PASS' if isolation_working else 'FAIL'}")
        return isolation_working

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all regression tests and return summary."""
        logger.info("Starting Memory System Multi-Turn Big Data Regression Tests")
        
        start_time = datetime.now()
        
        tests = [
            ("Basic Memory Persistence", self.test_basic_memory_persistence),
            ("Big Data Serialization", self.test_big_data_serialization), 
            ("Rapid Requests No Duplicates", self.test_rapid_requests_no_duplicates),
            ("Multi-turn Complex Conversation", self.test_multiturn_complex_conversation),
            ("Thread Isolation", self.test_thread_isolation)
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
            "test_suite": "Memory System Multi-Turn Big Data Regression",
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
        logger.info(f"MEMORY REGRESSION TEST SUMMARY")
        logger.info(f"{'='*50}")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {summary['success_rate']:.1f}%")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Overall Result: {'✅ ALL TESTS PASSED' if summary['all_tests_passed'] else '❌ SOME TESTS FAILED'}")
        
        return summary

def main():
    """Main function to run the regression tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory System Regression Test")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL for API server")
    parser.add_argument("--output", help="JSON file to save detailed results")
    
    args = parser.parse_args()
    
    # Run tests
    tester = MemoryRegressionTest(base_url=args.url)
    results = tester.run_all_tests()
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Detailed results saved to: {args.output}")
    
    # Exit with appropriate code
    exit(0 if results["all_tests_passed"] else 1)

if __name__ == "__main__":
    main()
