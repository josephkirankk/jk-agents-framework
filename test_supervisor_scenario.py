#!/usr/bin/env python3
"""
Real-World Supervisor Test Script

This script tests the supervisor routing and memory functionality using a realistic
software development project scenario (ShopSmart e-commerce platform).

Test Scenarios:
1. Architecture planning and decision making
2. Code implementation and debugging
3. DevOps and deployment planning
4. Documentation creation
5. Cross-functional collaboration
6. Memory persistence across different agent interactions
"""

import requests
import json
import time
import sys
from typing import Dict, Any, List
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

class SupervisorScenarioTester:
    """Test supervisor routing and memory with realistic development scenarios."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.config_path = "config/supervisor_real_scenario_test.yaml"
        self.session = requests.Session()
        self.thread_id = f"shopsmart_project_{int(time.time())}"
        
        # Realistic development scenarios
        self.scenarios = [
            {
                "name": "Initial Architecture Planning",
                "query": "We're starting the ShopSmart e-commerce platform project. I need help designing the overall microservices architecture. What services should we have and how should they communicate?",
                "expected_agent": "senior_architect",
                "context": "Project kickoff - architecture design phase"
            },
            {
                "name": "Database Design Follow-up",
                "query": "Based on our microservices architecture discussion, how should we design the database schema for the user service and order service? Should we use separate databases?",
                "expected_agent": "senior_architect", 
                "context": "Following up on architecture - database design"
            },
            {
                "name": "User Authentication Implementation",
                "query": "I need to implement JWT-based authentication for the user service in Node.js. Can you help me write the authentication middleware and token validation logic?",
                "expected_agent": "lead_developer",
                "context": "Implementation phase - authentication code"
            },
            {
                "name": "Docker Containerization",
                "query": "Now that we have the user service implemented, I need help creating Docker containers for our microservices. What's the best approach for containerizing Node.js services?",
                "expected_agent": "devops_engineer",
                "context": "Deployment preparation - containerization"
            },
            {
                "name": "API Documentation",
                "query": "We need to document the authentication API endpoints we just implemented. Can you help create comprehensive API documentation for the user service?",
                "expected_agent": "tech_writer",
                "context": "Documentation phase - API specs"
            },
            {
                "name": "Performance Optimization",
                "query": "Our authentication service is experiencing slow response times under load. How can we optimize the JWT validation process and database queries?",
                "expected_agent": "lead_developer",
                "context": "Performance tuning - optimization"
            },
            {
                "name": "Kubernetes Deployment",
                "query": "We're ready to deploy our containerized services to Kubernetes. Can you help me create deployment manifests and set up service discovery?",
                "expected_agent": "devops_engineer",
                "context": "Production deployment - Kubernetes"
            },
            {
                "name": "Architecture Review",
                "query": "After implementing several services, I want to review our current architecture. Are we following microservices best practices? Any improvements needed?",
                "expected_agent": "senior_architect",
                "context": "Architecture review - best practices validation"
            }
        ]
        
        log.info(f"Initialized supervisor scenario tester for {self.base_url}")
        log.info(f"Using config: {self.config_path}")
        log.info(f"Thread ID: {self.thread_id}")
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            log.debug(f"{method} {url} -> {response.status_code}")
            return response
        except requests.exceptions.RequestException as e:
            log.error(f"Request failed: {method} {url} - {e}")
            raise
    
    def test_supervisor_routing(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test supervisor routing for a specific scenario."""
        log.info(f"🎯 Testing scenario: {scenario['name']}")
        
        try:
            # Use the supervised query endpoint to test supervisor routing
            query_data = {
                "input": scenario["query"],
                "config_path": self.config_path,
                "thread_id": self.thread_id
            }
            
            start_time = time.time()
            response = self._make_request("POST", "/query", json=query_data)
            response_time = time.time() - start_time
            
            result = {
                "scenario_name": scenario["name"],
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response_time_ms": round(response_time * 1000, 2),
                "expected_agent": scenario["expected_agent"],
                "context": scenario["context"]
            }
            
            if response.status_code == 200:
                data = response.json()
                result.update({
                    "response": data.get("response", "")[:300] + "...",
                    "metadata": data.get("metadata", {}),
                    "thread_id": data.get("thread_id"),
                    "full_response_length": len(data.get("response", ""))
                })
                
                # Analyze if the response seems appropriate for the expected agent
                response_text = data.get("response", "").lower()
                agent_keywords = {
                    "senior_architect": ["architecture", "microservices", "design", "scalability", "system", "service"],
                    "lead_developer": ["code", "implementation", "function", "api", "database", "jwt", "node.js"],
                    "devops_engineer": ["docker", "kubernetes", "deployment", "container", "infrastructure", "ci/cd"],
                    "tech_writer": ["documentation", "api", "guide", "specification", "readme", "tutorial"]
                }
                
                expected_keywords = agent_keywords.get(scenario["expected_agent"], [])
                keyword_matches = sum(1 for keyword in expected_keywords if keyword in response_text)
                result["keyword_relevance_score"] = keyword_matches / len(expected_keywords) if expected_keywords else 0
                
                log.info(f"✅ Scenario completed: {response_time*1000:.1f}ms, relevance: {result['keyword_relevance_score']*100:.1f}%")
            else:
                result["error"] = response.text
                log.error(f"❌ Scenario failed: {response.status_code}")
            
            return result
            
        except Exception as e:
            log.error(f"Scenario {scenario['name']} failed: {e}")
            return {
                "scenario_name": scenario["name"],
                "success": False,
                "error": str(e),
                "expected_agent": scenario["expected_agent"]
            }
    
    def test_memory_persistence(self) -> Dict[str, Any]:
        """Test memory persistence across the conversation thread."""
        log.info("🧠 Testing memory persistence across scenarios...")
        
        try:
            # Ask a question that requires memory of previous conversations
            memory_test_query = {
                "input": "Can you summarize all the architectural decisions we've made for the ShopSmart project so far? What services have we discussed and what technologies are we using?",
                "config_path": self.config_path,
                "thread_id": self.thread_id
            }
            
            start_time = time.time()
            response = self._make_request("POST", "/query", json=memory_test_query)
            response_time = time.time() - start_time
            
            result = {
                "test_name": "Memory Persistence Test",
                "success": response.status_code == 200,
                "response_time_ms": round(response_time * 1000, 2)
            }
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "").lower()
                
                # Check for memory indicators from previous conversations
                memory_indicators = [
                    "shopsmart", "microservices", "user service", "order service",
                    "jwt", "authentication", "docker", "kubernetes", "node.js"
                ]
                
                memory_score = sum(1 for indicator in memory_indicators if indicator in response_text)
                
                result.update({
                    "response": data.get("response", "")[:500] + "...",
                    "memory_indicators_found": memory_score,
                    "memory_effectiveness": memory_score / len(memory_indicators),
                    "thread_id": data.get("thread_id"),
                    "full_response_length": len(data.get("response", ""))
                })
                
                log.info(f"✅ Memory test completed: {memory_score}/{len(memory_indicators)} indicators found")
            else:
                result["error"] = response.text
                log.error(f"❌ Memory test failed: {response.status_code}")
            
            return result
            
        except Exception as e:
            log.error(f"Memory persistence test failed: {e}")
            return {
                "test_name": "Memory Persistence Test",
                "success": False,
                "error": str(e)
            }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive supervisor and memory test."""
        print("=" * 80)
        print("🚀 SUPERVISOR REAL-WORLD SCENARIO TEST")
        print("=" * 80)
        print(f"Project: ShopSmart E-commerce Platform Development")
        print(f"Configuration: {self.config_path}")
        print(f"Thread ID: {self.thread_id}")
        print()
        
        start_time = time.time()
        scenario_results = []
        
        # Run all scenarios in sequence to build context
        for i, scenario in enumerate(self.scenarios, 1):
            print(f"📋 Scenario {i}/{len(self.scenarios)}: {scenario['name']}")
            result = self.test_supervisor_routing(scenario)
            scenario_results.append(result)
            
            # Brief pause between scenarios to allow for processing
            time.sleep(2)
            print()
        
        # Test memory persistence
        print("🧠 Testing Memory Persistence...")
        memory_result = self.test_memory_persistence()
        
        total_time = time.time() - start_time
        
        # Compile results
        successful_scenarios = [r for r in scenario_results if r.get("success", False)]
        
        summary = {
            "test_suite": "Supervisor Real-World Scenario Test",
            "project_context": "ShopSmart E-commerce Platform",
            "total_scenarios": len(self.scenarios),
            "successful_scenarios": len(successful_scenarios),
            "success_rate": len(successful_scenarios) / len(self.scenarios),
            "memory_test": memory_result,
            "total_time_seconds": round(total_time, 2),
            "thread_id": self.thread_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "scenario_results": scenario_results
        }
        
        # Print summary
        print("=" * 80)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 80)
        print(f"Project Context: ShopSmart E-commerce Platform Development")
        print(f"Total Scenarios: {len(self.scenarios)}")
        print(f"Successful: {len(successful_scenarios)}")
        print(f"Failed: {len(self.scenarios) - len(successful_scenarios)}")
        print(f"Success Rate: {summary['success_rate']*100:.1f}%")
        print(f"Total Time: {total_time:.2f} seconds")
        print()
        
        # Print scenario results
        print("📋 SCENARIO RESULTS:")
        print("-" * 60)
        for result in scenario_results:
            status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
            scenario_name = result.get("scenario_name", "Unknown")
            expected_agent = result.get("expected_agent", "unknown")
            relevance = result.get("keyword_relevance_score", 0) * 100
            
            print(f"{status} {scenario_name}")
            print(f"    Expected Agent: {expected_agent}")
            print(f"    Relevance Score: {relevance:.1f}%")
            
            if not result.get("success", False) and "error" in result:
                print(f"    Error: {result['error']}")
        
        # Print memory test results
        print()
        print("🧠 MEMORY PERSISTENCE RESULTS:")
        print("-" * 40)
        if memory_result.get("success", False):
            effectiveness = memory_result.get("memory_effectiveness", 0) * 100
            indicators_found = memory_result.get("memory_indicators_found", 0)
            print(f"✅ Memory Test PASSED")
            print(f"    Memory Effectiveness: {effectiveness:.1f}%")
            print(f"    Context Indicators Found: {indicators_found}")
        else:
            print(f"❌ Memory Test FAILED")
            if "error" in memory_result:
                print(f"    Error: {memory_result['error']}")
        
        print()
        print("=" * 80)
        
        if summary['success_rate'] >= 0.8 and memory_result.get("success", False):
            print("🎉 SUPERVISOR TEST SUITE PASSED!")
            print("The supervisor routing and memory system are working correctly.")
        else:
            print("⚠️ SUPERVISOR TEST SUITE NEEDS ATTENTION!")
            print("Some scenarios failed or memory persistence issues detected.")
        
        return summary


def main():
    """Main function to run the supervisor scenario test."""
    tester = SupervisorScenarioTester()
    
    try:
        results = tester.run_comprehensive_test()
        
        # Save detailed results
        with open("supervisor_scenario_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Detailed results saved to: supervisor_scenario_test_results.json")
        
        # Exit with appropriate code
        exit_code = 0 if results['success_rate'] >= 0.8 and results['memory_test'].get('success', False) else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        log.error(f"Test suite error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
