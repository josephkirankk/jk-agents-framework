#!/usr/bin/env python3
"""
ChromaDB Multi-Turn Memory Test

Focused test for ChromaDB-backed multi-turn memory functionality:
1. Basic memory persistence across conversation turns
2. Context building over multiple interactions
3. Thread isolation with ChromaDB storage
4. Memory retrieval and serialization validation

This test validates that ChromaDB integration works properly for conversation memory.
"""

import subprocess
import json
import time
import uuid
from typing import Dict, List, Any
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChromaDBMultiTurnTest:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results: List[Dict[str, Any]] = []
        # Use simple ChromaDB configuration for multi-turn memory tests
        self.config_path = "config/simple_chromadb_test.yaml"
        
    def curl_request(self, input_text: str, thread_id: str, raw_output: bool = True, timeout: int = 30) -> Dict[str, Any]:
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
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
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

    def test_basic_chromadb_memory(self) -> bool:
        """Test basic ChromaDB memory persistence across turns."""
        logger.info("Testing basic ChromaDB memory persistence...")
        thread_id = f"chromadb-basic-{uuid.uuid4().hex[:8]}"
        
        # Turn 1: Store information
        response1 = self.curl_request(
            "Hello! My name is Sarah and I'm 28 years old. I love hiking and photography. Please remember this about me.", 
            thread_id
        )
        
        if not response1.get("success", False):
            logger.error(f"Turn 1 failed: {response1}")
            return False
        
        logger.info("Turn 1 completed successfully")
        time.sleep(2)  # Allow time for ChromaDB storage
        
        # Turn 2: Test memory recall
        response2 = self.curl_request(
            "What do you remember about me? Please tell me my name, age, and hobbies.", 
            thread_id
        )
        
        if not response2.get("success", False):
            logger.error(f"Turn 2 failed: {response2}")
            return False
        
        # Check if memory was preserved
        response_text = str(response2.get("response", "")).lower()
        memory_preserved = (
            "sarah" in response_text and 
            ("28" in response_text or "twenty" in response_text) and
            ("hiking" in response_text or "photography" in response_text)
        )
        
        result = {
            "test": "basic_chromadb_memory",
            "thread_id": thread_id,
            "turns": 2,
            "memory_preserved": memory_preserved,
            "response1": response1.get("response", ""),
            "response2": response2.get("response", "")
        }
        self.test_results.append(result)
        
        logger.info(f"Basic ChromaDB memory test: {'PASS' if memory_preserved else 'FAIL'}")
        if memory_preserved:
            logger.info("✅ ChromaDB successfully stored and retrieved conversation memory")
        else:
            logger.error("❌ ChromaDB failed to preserve memory across turns")
            
        return memory_preserved

    def test_context_building(self) -> bool:
        """Test context building over multiple ChromaDB-stored turns."""
        logger.info("Testing ChromaDB context building over multiple turns...")
        thread_id = f"chromadb-context-{uuid.uuid4().hex[:8]}"
        
        conversation_turns = [
            ("I'm planning to buy a new car. I prefer electric vehicles.", "car_preference"),
            ("My budget is around $40,000 and I need good range for long trips.", "budget_range"),
            ("I'm considering Tesla Model 3 and Polestar 2. What do you think?", "specific_models"),
            ("Based on everything I told you, which car would you recommend and why?", "recommendation")
        ]
        
        responses = []
        for i, (turn_text, turn_type) in enumerate(conversation_turns):
            logger.info(f"Executing turn {i+1}: {turn_type}")
            response = self.curl_request(turn_text, thread_id)
            responses.append(response)
            
            if not response.get("success", False):
                logger.warning(f"Turn {i+1} failed: {response}")
                break
                
            time.sleep(1)  # Allow time for ChromaDB storage
        
        # Check if final response incorporates all previous context
        if responses and len(responses) == len(conversation_turns):
            final_response = str(responses[-1].get("response", "")).lower()
            context_preserved = (
                "electric" in final_response and
                ("40" in final_response or "budget" in final_response) and
                ("tesla" in final_response or "polestar" in final_response) and
                len(final_response) > 100  # Substantial recommendation
            )
        else:
            context_preserved = False
        
        result = {
            "test": "chromadb_context_building",
            "thread_id": thread_id,
            "total_turns": len(conversation_turns),
            "successful_turns": sum(1 for r in responses if r.get("success", False)),
            "context_preserved": context_preserved,
            "conversation_complete": len(responses) == len(conversation_turns) and context_preserved
        }
        self.test_results.append(result)
        
        logger.info(f"ChromaDB context building test: {'PASS' if context_preserved else 'FAIL'}")
        if context_preserved:
            logger.info("✅ ChromaDB successfully built context over multiple turns")
        else:
            logger.error("❌ ChromaDB failed to build proper context")
            
        return context_preserved

    def test_thread_isolation(self) -> bool:
        """Test that ChromaDB maintains separate memory for different threads."""
        logger.info("Testing ChromaDB thread isolation...")
        
        thread_a = f"chromadb-iso-a-{uuid.uuid4().hex[:8]}"
        thread_b = f"chromadb-iso-b-{uuid.uuid4().hex[:8]}"
        
        # Set different information in each thread
        response_a1 = self.curl_request(
            "My favorite programming language is Python and I work at Google.", 
            thread_a
        )
        response_b1 = self.curl_request(
            "My favorite programming language is JavaScript and I work at Microsoft.", 
            thread_b
        )
        
        time.sleep(2)  # Allow ChromaDB storage
        
        # Test memory isolation
        response_a2 = self.curl_request(
            "What programming language do I prefer and where do I work?", 
            thread_a
        )
        response_b2 = self.curl_request(
            "What programming language do I prefer and where do I work?", 
            thread_b
        )
        
        # Verify isolation
        a_response = str(response_a2.get("response", "")).lower()
        b_response = str(response_b2.get("response", "")).lower()
        
        a_correct = (response_a2.get("success", False) and 
                    "python" in a_response and "google" in a_response)
        
        b_correct = (response_b2.get("success", False) and 
                    "javascript" in b_response and "microsoft" in b_response)
        
        # Check for cross-contamination
        cross_contamination = (
            "javascript" in a_response or "microsoft" in a_response or
            "python" in b_response or "google" in b_response
        )
        
        isolation_working = a_correct and b_correct and not cross_contamination
        
        result = {
            "test": "chromadb_thread_isolation",
            "thread_a": thread_a,
            "thread_b": thread_b,
            "thread_a_correct": a_correct,
            "thread_b_correct": b_correct,
            "no_cross_contamination": not cross_contamination,
            "isolation_working": isolation_working
        }
        self.test_results.append(result)
        
        logger.info(f"ChromaDB thread isolation test: {'PASS' if isolation_working else 'FAIL'}")
        if isolation_working:
            logger.info("✅ ChromaDB successfully maintains thread isolation")
        else:
            logger.error("❌ ChromaDB thread isolation failed")
            logger.error(f"Thread A correct: {a_correct}, Thread B correct: {b_correct}")
            logger.error(f"Cross contamination: {cross_contamination}")
            
        return isolation_working

    def test_memory_persistence_after_delay(self) -> bool:
        """Test that ChromaDB memory persists after longer delays."""
        logger.info("Testing ChromaDB memory persistence after delay...")
        thread_id = f"chromadb-persist-{uuid.uuid4().hex[:8]}"
        
        # Store complex information
        response1 = self.curl_request(
            "I'm organizing a wedding for June 15th, 2024. The venue is Sunset Gardens, 150 guests expected. "
            "Wedding colors are navy blue and gold. The caterer is Elegant Bites and the photographer is Lisa Chen.",
            thread_id
        )
        
        if not response1.get("success", False):
            logger.error(f"Initial storage failed: {response1}")
            return False
        
        logger.info("Memory stored, waiting 5 seconds to simulate delay...")
        time.sleep(5)  # Simulate time delay
        
        # Test detailed recall
        response2 = self.curl_request(
            "Can you tell me all the details about my wedding that I mentioned? Include date, venue, colors, and vendors.",
            thread_id
        )
        
        if not response2.get("success", False):
            logger.error(f"Memory recall failed: {response2}")
            return False
        
        # Check if detailed memory was preserved
        response_text = str(response2.get("response", "")).lower()
        memory_preserved = (
            ("june" in response_text or "15" in response_text) and
            "sunset gardens" in response_text and
            ("150" in response_text or "guests" in response_text) and
            ("navy" in response_text or "blue" in response_text) and
            ("elegant bites" in response_text or "lisa chen" in response_text)
        )
        
        result = {
            "test": "chromadb_persistence_delay",
            "thread_id": thread_id,
            "delay_seconds": 5,
            "memory_preserved": memory_preserved,
            "detailed_recall": len(str(response2.get("response", ""))) > 200
        }
        self.test_results.append(result)
        
        logger.info(f"ChromaDB persistence delay test: {'PASS' if memory_preserved else 'FAIL'}")
        if memory_preserved:
            logger.info("✅ ChromaDB successfully maintained detailed memory after delay")
        else:
            logger.error("❌ ChromaDB failed to maintain memory after delay")
            
        return memory_preserved

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all ChromaDB multi-turn memory tests."""
        logger.info("Starting ChromaDB Multi-Turn Memory Tests")
        logger.info("="*60)
        
        start_time = datetime.now()
        
        tests = [
            ("Basic ChromaDB Memory", self.test_basic_chromadb_memory),
            ("Context Building", self.test_context_building),
            ("Thread Isolation", self.test_thread_isolation),
            ("Memory Persistence After Delay", self.test_memory_persistence_after_delay)
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
            "test_suite": "ChromaDB Multi-Turn Memory Tests",
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
        
        logger.info(f"\n{'='*60}")
        logger.info(f"CHROMADB MULTI-TURN MEMORY TEST SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {summary['success_rate']:.1f}%")
        logger.info(f"Duration: {duration:.2f} seconds")
        
        if passed_tests == total_tests:
            logger.info(f"🎉 ALL CHROMADB MEMORY TESTS PASSED!")
            logger.info("✅ ChromaDB memory persistence working")
            logger.info("✅ Multi-turn context building working")
            logger.info("✅ Thread isolation working")
            logger.info("✅ Memory persistence after delays working")
        else:
            logger.error(f"❌ SOME CHROMADB MEMORY TESTS FAILED")
            logger.error("Please check ChromaDB configuration and memory system setup")
        
        return summary

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ChromaDB Multi-Turn Memory Tests")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--output", default=None, help="Output file for test results JSON")
    
    args = parser.parse_args()
    
    test_runner = ChromaDBMultiTurnTest(args.url)
    results = test_runner.run_all_tests()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Detailed results saved to: {args.output}")
    
    # Exit with error code if tests failed
    if not results["all_tests_passed"]:
        exit(1)
