#!/usr/bin/env python3
"""
Multi-Step Supervisor Test Script

This script demonstrates the difference between:
1. Single-step routing (what we had before)
2. Multi-step orchestration (what this tests)

The test will show how the supervisor creates comprehensive workflows
with multiple agents working in sequence.
"""

import requests
import json
import time
import sys
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

class MultiStepSupervisorTester:
    """Test multi-step supervisor orchestration."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.config_path = "config/supervisor_multistep_test.yaml"
        self.session = requests.Session()
        self.thread_id = f"multistep_test_{int(time.time())}"
        
        # Multi-step test scenarios
        self.scenarios = [
            {
                "name": "Complete Feature Development Workflow",
                "query": "I need to implement a complete user registration feature for ShopSmart. This should include architecture design, code implementation, deployment setup, and documentation. Please create a comprehensive workflow.",
                "expected_steps": ["senior_architect", "lead_developer", "devops_engineer", "tech_writer"],
                "context": "End-to-end feature development"
            },
            {
                "name": "Performance Optimization Workflow", 
                "query": "Our ShopSmart platform is experiencing performance issues. I need a complete workflow to analyze, optimize, deploy improvements, and document the changes.",
                "expected_steps": ["senior_architect", "lead_developer", "devops_engineer", "tech_writer"],
                "context": "Performance optimization pipeline"
            },
            {
                "name": "New Microservice Development",
                "query": "We need to add a new payment processing microservice to ShopSmart. Please create a workflow that covers the complete development lifecycle from design to documentation.",
                "expected_steps": ["senior_architect", "lead_developer", "devops_engineer", "tech_writer"],
                "context": "New service development lifecycle"
            }
        ]
        
        log.info(f"Initialized multi-step supervisor tester for {self.base_url}")
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
    
    def test_multistep_workflow(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test multi-step workflow for a specific scenario."""
        log.info(f"🚀 Testing multi-step scenario: {scenario['name']}")
        
        try:
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
                "expected_steps": scenario["expected_steps"],
                "context": scenario["context"]
            }
            
            if response.status_code == 200:
                data = response.json()
                result.update({
                    "response": data.get("response", "")[:500] + "...",
                    "metadata": data.get("metadata", {}),
                    "thread_id": data.get("thread_id"),
                    "full_response_length": len(data.get("response", ""))
                })
                
                # Check if this was actually a multi-step workflow
                metadata = data.get("metadata", {})
                total_steps = metadata.get("total_steps", 0)
                
                result.update({
                    "actual_steps": total_steps,
                    "is_multistep": total_steps > 1,
                    "step_efficiency": min(total_steps / len(scenario["expected_steps"]), 1.0) if scenario["expected_steps"] else 0
                })
                
                if total_steps > 1:
                    log.info(f"✅ Multi-step workflow executed: {total_steps} steps in {response_time:.1f}s")
                else:
                    log.warning(f"⚠️ Single-step execution detected: {total_steps} steps")
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
                "expected_steps": scenario["expected_steps"]
            }
    
    def run_multistep_test(self) -> Dict[str, Any]:
        """Run comprehensive multi-step supervisor test."""
        print("=" * 80)
        print("🚀 MULTI-STEP SUPERVISOR ORCHESTRATION TEST")
        print("=" * 80)
        print(f"Configuration: {self.config_path}")
        print(f"Thread ID: {self.thread_id}")
        print()
        print("This test demonstrates TRUE multi-step workflows where:")
        print("- Supervisor creates comprehensive plans with multiple steps")
        print("- Multiple agents work in sequence with dependencies")
        print("- Each step builds upon previous step results")
        print("- Complete workflows are orchestrated automatically")
        print()
        
        start_time = time.time()
        scenario_results = []
        
        for i, scenario in enumerate(self.scenarios, 1):
            print(f"📋 Scenario {i}/{len(self.scenarios)}: {scenario['name']}")
            result = self.test_multistep_workflow(scenario)
            scenario_results.append(result)
            
            time.sleep(3)  # Allow processing time between scenarios
            print()
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_scenarios = [r for r in scenario_results if r.get("success", False)]
        multistep_scenarios = [r for r in successful_scenarios if r.get("is_multistep", False)]
        
        summary = {
            "test_suite": "Multi-Step Supervisor Orchestration Test",
            "total_scenarios": len(self.scenarios),
            "successful_scenarios": len(successful_scenarios),
            "multistep_scenarios": len(multistep_scenarios),
            "success_rate": len(successful_scenarios) / len(self.scenarios),
            "multistep_rate": len(multistep_scenarios) / len(successful_scenarios) if successful_scenarios else 0,
            "total_time_seconds": round(total_time, 2),
            "thread_id": self.thread_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "scenario_results": scenario_results
        }
        
        # Print summary
        print("=" * 80)
        print("📊 MULTI-STEP TEST RESULTS SUMMARY")
        print("=" * 80)
        print(f"Total Scenarios: {len(self.scenarios)}")
        print(f"Successful: {len(successful_scenarios)}")
        print(f"Multi-Step Workflows: {len(multistep_scenarios)}")
        print(f"Success Rate: {summary['success_rate']*100:.1f}%")
        print(f"Multi-Step Rate: {summary['multistep_rate']*100:.1f}%")
        print(f"Total Time: {total_time:.2f} seconds")
        print()
        
        # Print detailed results
        print("📋 DETAILED SCENARIO RESULTS:")
        print("-" * 60)
        for result in scenario_results:
            status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
            scenario_name = result.get("scenario_name", "Unknown")
            actual_steps = result.get("actual_steps", 0)
            is_multistep = result.get("is_multistep", False)
            
            print(f"{status} {scenario_name}")
            print(f"    Steps Executed: {actual_steps}")
            print(f"    Multi-Step: {'✅ Yes' if is_multistep else '❌ No (Single-step routing)'}")
            
            if not result.get("success", False) and "error" in result:
                print(f"    Error: {result['error']}")
        
        print()
        print("=" * 80)
        
        if summary['multistep_rate'] >= 0.8:
            print("🎉 MULTI-STEP SUPERVISOR TEST PASSED!")
            print("The supervisor is successfully creating and orchestrating multi-step workflows.")
        else:
            print("⚠️ MULTI-STEP SUPERVISOR NEEDS ATTENTION!")
            print("The supervisor is still doing single-step routing instead of multi-step orchestration.")
            print()
            print("🔍 ANALYSIS:")
            print("- Check supervisor prompt format")
            print("- Ensure JSON response includes 'goal' and 'plan' structure")
            print("- Verify agent dependencies and workflow logic")
        
        return summary


def main():
    """Main function to run the multi-step supervisor test."""
    tester = MultiStepSupervisorTester()
    
    try:
        results = tester.run_multistep_test()
        
        # Save detailed results
        with open("multistep_supervisor_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Detailed results saved to: multistep_supervisor_test_results.json")
        
        # Exit with appropriate code
        exit_code = 0 if results['multistep_rate'] >= 0.8 else 1
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
