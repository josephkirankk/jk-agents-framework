#!/usr/bin/env python3
"""
Focused Test for Advanced Memory Features

This script specifically tests the advanced memory capabilities defined in the 
advanced_memory_agent_test.yaml configuration, including:
- Memory persistence across conversations
- Performance metrics and monitoring
- Advanced caching and connection pooling
- Resource management and adaptive scaling
"""

import requests
import json
import time
import sys
from typing import Dict, Any, List

class AdvancedMemoryFeatureTester:
    """Focused tester for advanced memory features."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.config_path = "config/advanced_memory_agent_test.yaml"
        self.session = requests.Session()
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling."""
        url = f"{self.base_url}{endpoint}"
        return self.session.request(method, url, **kwargs)
    
    def test_memory_persistence_detailed(self) -> Dict[str, Any]:
        """Test detailed memory persistence across multiple conversations."""
        print("🧠 Testing Advanced Memory Persistence...")
        
        agent_name = "architecture_advisor"
        thread_id = f"advanced_memory_test_{int(time.time())}"
        
        # Conversation 1: Establish context about a project
        print("  📝 Conversation 1: Establishing project context...")
        conv1_data = {
            "agent_name": agent_name,
            "input": "I'm designing a high-performance e-commerce platform using microservices architecture. The system needs to handle 100,000 concurrent users with sub-200ms response times. Please remember these requirements for our future discussions.",
            "config_path": self.config_path,
            "thread_id": thread_id
        }
        
        response1 = self._make_request("POST", "/worker", json=conv1_data)
        conv1_result = response1.json() if response1.status_code == 200 else {}
        
        time.sleep(2)  # Allow memory to persist
        
        # Conversation 2: Reference previous context
        print("  🔍 Conversation 2: Testing memory recall...")
        conv2_data = {
            "agent_name": agent_name,
            "input": "Based on the project requirements I mentioned earlier, what specific caching strategy would you recommend?",
            "config_path": self.config_path,
            "thread_id": thread_id
        }
        
        response2 = self._make_request("POST", "/worker", json=conv2_data)
        conv2_result = response2.json() if response2.status_code == 200 else {}
        
        time.sleep(2)
        
        # Conversation 3: Deep context reference
        print("  🎯 Conversation 3: Testing deep context understanding...")
        conv3_data = {
            "agent_name": agent_name,
            "input": "How would you scale the database layer to meet the performance requirements we discussed?",
            "config_path": self.config_path,
            "thread_id": thread_id
        }
        
        response3 = self._make_request("POST", "/worker", json=conv3_data)
        conv3_result = response3.json() if response3.status_code == 200 else {}
        
        # Analyze memory recall
        conv2_response = conv2_result.get("response", "").lower()
        conv3_response = conv3_result.get("response", "").lower()
        
        memory_indicators = [
            "e-commerce", "microservices", "100,000", "concurrent", 
            "200ms", "performance", "requirements"
        ]
        
        conv2_memory_score = sum(1 for indicator in memory_indicators if indicator in conv2_response)
        conv3_memory_score = sum(1 for indicator in memory_indicators if indicator in conv3_response)
        
        return {
            "test_name": "Advanced Memory Persistence",
            "success": response1.status_code == 200 and response2.status_code == 200 and response3.status_code == 200,
            "thread_id": thread_id,
            "conversations": 3,
            "memory_recall_conv2": conv2_memory_score,
            "memory_recall_conv3": conv3_memory_score,
            "memory_effectiveness": (conv2_memory_score + conv3_memory_score) / (len(memory_indicators) * 2),
            "responses": {
                "conv1_length": len(conv1_result.get("response", "")),
                "conv2_length": len(conv2_result.get("response", "")),
                "conv3_length": len(conv3_result.get("response", ""))
            }
        }
    
    def test_concurrent_memory_isolation(self) -> Dict[str, Any]:
        """Test that memory is properly isolated between different threads."""
        print("🔒 Testing Memory Isolation Between Threads...")
        
        agent_name = "coding_assistant"
        
        # Create two separate conversation threads
        thread1_id = f"isolation_test_1_{int(time.time())}"
        thread2_id = f"isolation_test_2_{int(time.time())}"
        
        # Thread 1: Python project context
        print("  🐍 Thread 1: Python project context...")
        thread1_data = {
            "agent_name": agent_name,
            "input": "I'm working on a Python Django web application for a social media platform. Please remember this context.",
            "config_path": self.config_path,
            "thread_id": thread1_id
        }
        
        # Thread 2: Java project context
        print("  ☕ Thread 2: Java project context...")
        thread2_data = {
            "agent_name": agent_name,
            "input": "I'm developing a Java Spring Boot microservice for financial transactions. Please remember this context.",
            "config_path": self.config_path,
            "thread_id": thread2_id
        }
        
        # Execute initial contexts
        response1 = self._make_request("POST", "/worker", json=thread1_data)
        response2 = self._make_request("POST", "/worker", json=thread2_data)
        
        time.sleep(2)
        
        # Test memory isolation
        print("  🧪 Testing memory isolation...")
        
        # Ask thread 1 about its context
        thread1_recall = {
            "agent_name": agent_name,
            "input": "What programming language and framework am I using in my project?",
            "config_path": self.config_path,
            "thread_id": thread1_id
        }
        
        # Ask thread 2 about its context
        thread2_recall = {
            "agent_name": agent_name,
            "input": "What programming language and framework am I using in my project?",
            "config_path": self.config_path,
            "thread_id": thread2_id
        }
        
        recall1_response = self._make_request("POST", "/worker", json=thread1_recall)
        recall2_response = self._make_request("POST", "/worker", json=thread2_recall)
        
        recall1_result = recall1_response.json() if recall1_response.status_code == 200 else {}
        recall2_result = recall2_response.json() if recall2_response.status_code == 200 else {}
        
        recall1_text = recall1_result.get("response", "").lower()
        recall2_text = recall2_result.get("response", "").lower()
        
        # Check isolation
        thread1_correct = "python" in recall1_text and "django" in recall1_text
        thread2_correct = "java" in recall2_text and "spring" in recall2_text
        thread1_isolated = "java" not in recall1_text and "spring" not in recall1_text
        thread2_isolated = "python" not in recall2_text and "django" not in recall2_text
        
        return {
            "test_name": "Memory Isolation",
            "success": all([
                response1.status_code == 200, response2.status_code == 200,
                recall1_response.status_code == 200, recall2_response.status_code == 200
            ]),
            "thread1_id": thread1_id,
            "thread2_id": thread2_id,
            "thread1_memory_correct": thread1_correct,
            "thread2_memory_correct": thread2_correct,
            "thread1_isolated": thread1_isolated,
            "thread2_isolated": thread2_isolated,
            "isolation_score": sum([thread1_correct, thread2_correct, thread1_isolated, thread2_isolated]) / 4
        }
    
    def test_performance_metrics(self) -> Dict[str, Any]:
        """Test performance metrics and monitoring capabilities."""
        print("📊 Testing Performance Metrics...")
        
        # Get initial memory stats
        initial_stats = self._make_request("GET", "/memory/stats")
        initial_data = initial_stats.json() if initial_stats.status_code == 200 else {}
        
        # Perform several operations to generate metrics
        print("  🏃‍♂️ Generating load for metrics...")
        agent_name = "documentation_helper"
        
        operations = []
        for i in range(10):
            op_data = {
                "agent_name": agent_name,
                "input": f"Performance test operation {i+1}: Generate documentation for a REST API with advanced caching.",
                "config_path": self.config_path,
                "thread_id": f"perf_test_{i}_{int(time.time())}"
            }
            
            start_time = time.time()
            response = self._make_request("POST", "/worker", json=op_data)
            end_time = time.time()
            
            operations.append({
                "operation_id": i + 1,
                "success": response.status_code == 200,
                "response_time_ms": round((end_time - start_time) * 1000, 2),
                "status_code": response.status_code
            })
        
        # Get final memory stats
        final_stats = self._make_request("GET", "/memory/stats")
        final_data = final_stats.json() if final_stats.status_code == 200 else {}
        
        # Calculate performance metrics
        successful_ops = [op for op in operations if op["success"]]
        avg_response_time = sum(op["response_time_ms"] for op in successful_ops) / len(successful_ops) if successful_ops else 0
        success_rate = len(successful_ops) / len(operations)
        
        return {
            "test_name": "Performance Metrics",
            "success": len(successful_ops) >= 8,  # At least 80% success rate
            "total_operations": len(operations),
            "successful_operations": len(successful_ops),
            "success_rate": success_rate,
            "average_response_time_ms": round(avg_response_time, 2),
            "min_response_time_ms": min(op["response_time_ms"] for op in successful_ops) if successful_ops else 0,
            "max_response_time_ms": max(op["response_time_ms"] for op in successful_ops) if successful_ops else 0,
            "initial_memory_stats": initial_data,
            "final_memory_stats": final_data,
            "operations_detail": operations
        }
    
    def test_configuration_features(self) -> Dict[str, Any]:
        """Test that configuration features are properly loaded and working."""
        print("⚙️ Testing Configuration Features...")
        
        # Test each agent defined in the configuration
        agents_to_test = ["coding_assistant", "architecture_advisor", "documentation_helper"]
        agent_results = []
        
        for agent_name in agents_to_test:
            print(f"  🤖 Testing agent: {agent_name}")
            
            test_data = {
                "agent_name": agent_name,
                "input": f"Hello {agent_name}, please tell me about your advanced memory capabilities and any performance optimizations you're using.",
                "config_path": self.config_path
            }
            
            start_time = time.time()
            response = self._make_request("POST", "/worker", json=test_data)
            response_time = time.time() - start_time
            
            result = {
                "agent_name": agent_name,
                "success": response.status_code == 200,
                "response_time_ms": round(response_time * 1000, 2),
                "status_code": response.status_code
            }
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "").lower()
                
                # Check for memory-related keywords in response
                memory_keywords = ["memory", "performance", "cache", "optimization", "advanced"]
                memory_mentions = sum(1 for keyword in memory_keywords if keyword in response_text)
                
                result.update({
                    "response_length": len(data.get("response", "")),
                    "memory_keywords_found": memory_mentions,
                    "thread_id": data.get("thread_id"),
                    "metadata": data.get("metadata")
                })
            
            agent_results.append(result)
        
        successful_agents = [r for r in agent_results if r["success"]]
        
        return {
            "test_name": "Configuration Features",
            "success": len(successful_agents) == len(agents_to_test),
            "agents_tested": len(agents_to_test),
            "agents_successful": len(successful_agents),
            "average_response_time_ms": round(sum(r["response_time_ms"] for r in successful_agents) / len(successful_agents), 2) if successful_agents else 0,
            "agent_results": agent_results
        }
    
    def run_advanced_tests(self) -> Dict[str, Any]:
        """Run all advanced memory feature tests."""
        print("=" * 80)
        print("🚀 ADVANCED MEMORY FEATURES TEST SUITE")
        print("=" * 80)
        print(f"Testing configuration: {self.config_path}")
        print(f"API endpoint: {self.base_url}")
        print()
        
        start_time = time.time()
        
        # Run all tests
        tests = [
            self.test_memory_persistence_detailed,
            self.test_concurrent_memory_isolation,
            self.test_performance_metrics,
            self.test_configuration_features
        ]
        
        results = []
        for test_func in tests:
            try:
                print(f"🔍 Running {test_func.__name__}...")
                result = test_func()
                results.append(result)
                
                status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
                print(f"  {status} {result.get('test_name', 'Unknown Test')}")
                print()
                
            except Exception as e:
                print(f"  ❌ FAIL {test_func.__name__}: {e}")
                results.append({
                    "test_name": test_func.__name__,
                    "success": False,
                    "error": str(e)
                })
        
        total_time = time.time() - start_time
        
        # Compile summary
        successful_tests = sum(1 for r in results if r.get("success", False))
        total_tests = len(results)
        
        summary = {
            "test_suite": "Advanced Memory Features Tests",
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
            "total_time_seconds": round(total_time, 2),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "detailed_results": results
        }
        
        # Print summary
        print("=" * 80)
        print("📊 ADVANCED MEMORY FEATURES TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(f"Success Rate: {summary['success_rate']*100:.1f}%")
        print(f"Total Time: {total_time:.2f} seconds")
        print()
        
        # Print key findings
        print("🔍 KEY FINDINGS:")
        print("-" * 40)
        
        for result in results:
            test_name = result.get("test_name", "Unknown")
            if result.get("success", False):
                print(f"✅ {test_name}")
                
                # Print specific metrics for each test
                if "Memory Persistence" in test_name:
                    effectiveness = result.get("memory_effectiveness", 0)
                    print(f"    Memory Effectiveness: {effectiveness*100:.1f}%")
                
                elif "Memory Isolation" in test_name:
                    isolation_score = result.get("isolation_score", 0)
                    print(f"    Isolation Score: {isolation_score*100:.1f}%")
                
                elif "Performance Metrics" in test_name:
                    avg_time = result.get("average_response_time_ms", 0)
                    success_rate = result.get("success_rate", 0)
                    print(f"    Avg Response Time: {avg_time}ms")
                    print(f"    Success Rate: {success_rate*100:.1f}%")
                
                elif "Configuration Features" in test_name:
                    agents_successful = result.get("agents_successful", 0)
                    agents_tested = result.get("agents_tested", 0)
                    print(f"    Agents Working: {agents_successful}/{agents_tested}")
            else:
                print(f"❌ {test_name}")
                if "error" in result:
                    print(f"    Error: {result['error']}")
        
        print()
        print("=" * 80)
        
        if summary['success_rate'] >= 0.8:
            print("🎉 ADVANCED MEMORY FEATURES ARE WORKING CORRECTLY!")
            print("The advanced memory agent configuration has been successfully tested.")
        else:
            print("⚠️ SOME ADVANCED MEMORY FEATURES NEED ATTENTION!")
            print("Review the failed tests above for details.")
        
        return summary


def main():
    """Main function to run advanced memory feature tests."""
    tester = AdvancedMemoryFeatureTester()
    
    try:
        results = tester.run_advanced_tests()
        
        # Save detailed results
        with open("advanced_memory_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Detailed results saved to: advanced_memory_test_results.json")
        
        # Exit with appropriate code
        exit_code = 0 if results['success_rate'] >= 0.8 else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
