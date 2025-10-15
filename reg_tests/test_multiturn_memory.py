#!/usr/bin/env python3
"""
Multi-Turn Memory System Tests

Focused tests for multi-turn conversation memory functionality:
1. Basic memory persistence across turns
2. Complex conversation context building
3. Thread isolation between different conversations

These tests specifically validate memory persistence and context preservation
across multiple conversation turns.
"""

import subprocess
import json
import time
import uuid
import random
from typing import Dict, List, Any
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiTurnMemoryTest:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results: List[Dict[str, Any]] = []
        # Use configuration with memory enabled for multi-turn tests
        self.config_path = "config/multiturn_memory_test.yaml"
        
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

    def test_multiturn_complex_conversation(self) -> bool:
        """Test complex multi-turn conversation with context building."""
        logger.info("Testing complex multi-turn conversation...")
        thread_id = f"memory-complex-{uuid.uuid4().hex[:8]}"
        
        conversation_turns = [
            "I'm planning a vacation to Japan in spring. I love cherry blossoms.",
            "What are some good cities to visit during cherry blossom season?",
            "I'm particularly interested in traditional temples and gardens.",
            "Can you suggest some specific temples with beautiful cherry blossoms?",
            "Based on what I told you about my preferences, create a 3-day itinerary."
        ]
        
        responses = []
        for i, turn in enumerate(conversation_turns):
            response = self.curl_request(turn, thread_id)
            responses.append(response)
            
            if not response.get("success", False):
                logger.warning(f"Turn {i+1} failed: {response}")
                
            time.sleep(0.5)  # Brief pause between turns
        
        # Check if the final response incorporates context from all previous turns
        final_response = str(responses[-1].get("response", "")).lower()
        context_preserved = (
            "japan" in final_response and
            ("cherry" in final_response or "blossom" in final_response) and
            ("temple" in final_response or "garden" in final_response) and
            ("itinerary" in final_response or "day" in final_response)
        )
        
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
        a_correct = (response_a2.get("success", False) and 
                    "blue" in str(response_a2.get("response", "")).lower() and
                    "new york" in str(response_a2.get("response", "")).lower())
        
        b_correct = (response_b2.get("success", False) and 
                    "red" in str(response_b2.get("response", "")).lower() and
                    "california" in str(response_b2.get("response", "")).lower())
        
        # Cross-contamination check - A shouldn't know B's info
        cross_contamination = ("red" in str(response_a2.get("response", "")).lower() or
                             "california" in str(response_a2.get("response", "")).lower())
        
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
        """Run all multi-turn memory tests."""
        logger.info("Starting Multi-Turn Memory System Tests")
        
        start_time = datetime.now()
        
        tests = [
            ("Basic Memory Persistence", self.test_basic_memory_persistence),
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
            "test_suite": "Multi-Turn Memory System Tests",
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
        logger.info(f"MULTI-TURN MEMORY TEST SUMMARY")
        logger.info(f"{'='*50}")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {summary['success_rate']:.1f}%")
        logger.info(f"Duration: {duration:.2f} seconds")
        
        if passed_tests == total_tests:
            logger.info(f"🎉 ALL MULTI-TURN MEMORY TESTS PASSED!")
            logger.info("✅ Basic memory persistence working")
            logger.info("✅ Complex conversation context preserved")
            logger.info("✅ Thread isolation working correctly")
        else:
            logger.error(f"❌ SOME MULTI-TURN MEMORY TESTS FAILED")
        
        return summary

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Turn Memory System Tests")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--output", default=None, help="Output file for test results JSON")
    
    args = parser.parse_args()
    
    test_runner = MultiTurnMemoryTest(args.url)
    results = test_runner.run_all_tests()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Detailed results saved to: {args.output}")
    
    # Exit with error code if tests failed
    if not results["all_tests_passed"]:
        exit(1)
