#!/usr/bin/env python3
"""
Comprehensive Test Suite for Advanced Memory Agent Configuration via API

This script tests the advanced_memory_agent_test.yaml configuration through the API endpoints,
verifying all advanced memory features including:
- Configuration loading and validation
- Agent initialization with advanced memory system
- Performance monitoring and metrics
- Connection pooling and caching
- Resource management and scaling
- Memory optimization features
"""

import asyncio
import json
import time
import requests
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

class AdvancedMemoryAPITester:
    """Comprehensive tester for advanced memory agent API functionality."""
    
    def __init__(self, base_url: str = "http://localhost:8000", config_path: str = None):
        """Initialize the API tester."""
        self.base_url = base_url.rstrip('/')
        self.config_path = config_path or "config/advanced_memory_agent_test.yaml"
        self.session = requests.Session()
        self.test_results = []
        
        # Test configuration
        self.test_agents = ["coding_assistant", "architecture_advisor", "documentation_helper"]
        self.test_messages = [
            "Hello, I want to test your advanced memory capabilities",
            "Can you analyze the performance of your memory system?",
            "What are your current caching statistics?",
            "How is your connection pooling working?",
            "Remember that I prefer detailed technical explanations",
            "Do you recall my preference from the previous message?",
            "Can you show me your resource utilization metrics?",
            "How does your adaptive scaling work under load?"
        ]
        
        log.info(f"Initialized API tester for {self.base_url}")
        log.info(f"Using config: {self.config_path}")
    
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
    
    def test_api_health(self) -> Dict[str, Any]:
        """Test API health and basic connectivity."""
        log.info("🏥 Testing API health...")
        
        try:
            # Test root endpoint
            response = self._make_request("GET", "/")
            root_data = response.json() if response.status_code == 200 else {}
            
            # Test health endpoint
            health_response = self._make_request("GET", "/health")
            health_data = health_response.json() if health_response.status_code == 200 else {}
            
            result = {
                "test_name": "API Health Check",
                "success": response.status_code == 200 and health_response.status_code == 200,
                "root_status": response.status_code,
                "health_status": health_response.status_code,
                "available_agents": root_data.get("available_agents", []),
                "config_status": root_data.get("config_status", "unknown"),
                "endpoints": root_data.get("endpoints", {}),
                "health_info": health_data
            }
            
            if result["success"]:
                log.info("✅ API health check passed")
                log.info(f"Available agents: {result['available_agents']}")
                log.info(f"Config status: {result['config_status']}")
            else:
                log.error("❌ API health check failed")
            
            return result
            
        except Exception as e:
            log.error(f"Health check failed: {e}")
            return {
                "test_name": "API Health Check",
                "success": False,
                "error": str(e)
            }
    
    def test_config_loading(self) -> Dict[str, Any]:
        """Test configuration loading with advanced memory settings."""
        log.info("⚙️ Testing configuration loading...")
        
        try:
            # Test with specific config path
            test_data = {
                "agent_name": "coding_assistant",
                "input": "Test configuration loading with advanced memory system",
                "config_path": self.config_path
            }
            
            response = self._make_request("POST", "/worker", json=test_data)
            
            result = {
                "test_name": "Configuration Loading",
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "config_path": self.config_path
            }
            
            if response.status_code == 200:
                data = response.json()
                result.update({
                    "agent_response": data.get("response", "")[:200] + "...",
                    "agent_name": data.get("agent_name"),
                    "thread_id": data.get("thread_id"),
                    "metadata": data.get("metadata", {})
                })
                log.info("✅ Configuration loading test passed")
            else:
                result["error"] = response.text
                log.error(f"❌ Configuration loading failed: {response.status_code}")
            
            return result
            
        except Exception as e:
            log.error(f"Configuration loading test failed: {e}")
            return {
                "test_name": "Configuration Loading",
                "success": False,
                "error": str(e)
            }
    
    def test_advanced_memory_agents(self) -> List[Dict[str, Any]]:
        """Test all agents defined in the advanced memory configuration."""
        log.info("🧠 Testing advanced memory agents...")
        
        results = []
        
        for agent_name in self.test_agents:
            log.info(f"Testing agent: {agent_name}")
            
            try:
                test_data = {
                    "agent_name": agent_name,
                    "input": f"Hello {agent_name}, please demonstrate your advanced memory capabilities and current performance metrics",
                    "config_path": self.config_path
                }
                
                start_time = time.time()
                response = self._make_request("POST", "/worker", json=test_data)
                response_time = time.time() - start_time
                
                result = {
                    "test_name": f"Agent Test - {agent_name}",
                    "agent_name": agent_name,
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "response_time_ms": round(response_time * 1000, 2)
                }
                
                if response.status_code == 200:
                    data = response.json()
                    result.update({
                        "agent_response": data.get("response", "")[:300] + "...",
                        "thread_id": data.get("thread_id"),
                        "metadata": data.get("metadata", {})
                    })
                    log.info(f"✅ Agent {agent_name} test passed ({response_time*1000:.1f}ms)")
                else:
                    result["error"] = response.text
                    log.error(f"❌ Agent {agent_name} test failed: {response.status_code}")
                
                results.append(result)
                
                # Small delay between agent tests
                time.sleep(0.5)
                
            except Exception as e:
                log.error(f"Agent {agent_name} test failed: {e}")
                results.append({
                    "test_name": f"Agent Test - {agent_name}",
                    "agent_name": agent_name,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    def test_memory_persistence(self) -> Dict[str, Any]:
        """Test memory persistence across multiple conversations."""
        log.info("💾 Testing memory persistence...")
        
        try:
            agent_name = "architecture_advisor"  # Use agent with memory capabilities
            thread_id = f"test_persistence_{int(time.time())}"
            
            # First conversation - establish context
            first_message = {
                "agent_name": agent_name,
                "input": "I'm working on a microservices architecture project. Please remember this context for our future conversations.",
                "config_path": self.config_path,
                "thread_id": thread_id
            }
            
            response1 = self._make_request("POST", "/worker", json=first_message)
            
            # Wait a moment
            time.sleep(1)
            
            # Second conversation - test memory recall
            second_message = {
                "agent_name": agent_name,
                "input": "What project context did I mention in our previous conversation?",
                "config_path": self.config_path,
                "thread_id": thread_id
            }
            
            response2 = self._make_request("POST", "/worker", json=second_message)
            
            result = {
                "test_name": "Memory Persistence",
                "success": response1.status_code == 200 and response2.status_code == 200,
                "thread_id": thread_id,
                "first_response_status": response1.status_code,
                "second_response_status": response2.status_code
            }
            
            if result["success"]:
                data1 = response1.json()
                data2 = response2.json()
                
                result.update({
                    "first_response": data1.get("response", "")[:200] + "...",
                    "second_response": data2.get("response", "")[:200] + "...",
                    "memory_test_passed": "microservices" in data2.get("response", "").lower()
                })
                
                log.info("✅ Memory persistence test completed")
                if result["memory_test_passed"]:
                    log.info("✅ Memory recall successful")
                else:
                    log.warning("⚠️ Memory recall may not have worked as expected")
            else:
                log.error("❌ Memory persistence test failed")
            
            return result
            
        except Exception as e:
            log.error(f"Memory persistence test failed: {e}")
            return {
                "test_name": "Memory Persistence",
                "success": False,
                "error": str(e)
            }
    
    def test_performance_under_load(self) -> Dict[str, Any]:
        """Test performance under concurrent load."""
        log.info("🚀 Testing performance under load...")
        
        try:
            agent_name = "coding_assistant"
            concurrent_requests = 5
            
            # Prepare concurrent requests
            requests_data = []
            for i in range(concurrent_requests):
                requests_data.append({
                    "agent_name": agent_name,
                    "input": f"Performance test request {i+1}: Analyze system performance and memory optimization",
                    "config_path": self.config_path,
                    "thread_id": f"load_test_{i}_{int(time.time())}"
                })
            
            # Execute concurrent requests
            start_time = time.time()
            responses = []
            
            # Simple concurrent execution (in production, use asyncio or threading)
            for req_data in requests_data:
                try:
                    response = self._make_request("POST", "/worker", json=req_data, timeout=30)
                    responses.append(response)
                except Exception as e:
                    log.warning(f"Request failed during load test: {e}")
                    responses.append(None)
            
            total_time = time.time() - start_time
            
            # Analyze results
            successful_responses = [r for r in responses if r and r.status_code == 200]
            
            result = {
                "test_name": "Performance Under Load",
                "concurrent_requests": concurrent_requests,
                "successful_requests": len(successful_responses),
                "success_rate": len(successful_responses) / concurrent_requests,
                "total_time_seconds": round(total_time, 2),
                "average_time_per_request": round(total_time / concurrent_requests, 2),
                "success": len(successful_responses) >= concurrent_requests * 0.8  # 80% success rate
            }
            
            if result["success"]:
                log.info(f"✅ Load test passed: {result['success_rate']*100:.1f}% success rate")
            else:
                log.error(f"❌ Load test failed: {result['success_rate']*100:.1f}% success rate")
            
            return result
            
        except Exception as e:
            log.error(f"Performance load test failed: {e}")
            return {
                "test_name": "Performance Under Load",
                "success": False,
                "error": str(e)
            }
    
    def test_memory_metrics_api(self) -> Dict[str, Any]:
        """Test memory metrics API endpoints if available."""
        log.info("📊 Testing memory metrics API...")
        
        try:
            # Test memory stats endpoint
            response = self._make_request("GET", "/memory/stats")
            
            result = {
                "test_name": "Memory Metrics API",
                "success": response.status_code == 200,
                "status_code": response.status_code
            }
            
            if response.status_code == 200:
                data = response.json()
                result.update({
                    "memory_stats": data.get("memory_stats", {}),
                    "timestamp": data.get("timestamp"),
                    "status": data.get("status")
                })
                log.info("✅ Memory metrics API test passed")
            else:
                result["error"] = response.text
                log.warning(f"⚠️ Memory metrics API not available: {response.status_code}")
            
            return result
            
        except Exception as e:
            log.warning(f"Memory metrics API test failed: {e}")
            return {
                "test_name": "Memory Metrics API",
                "success": False,
                "error": str(e)
            }
    
    def test_supervised_query(self) -> Dict[str, Any]:
        """Test the supervised multi-agent query endpoint."""
        log.info("🎯 Testing supervised query endpoint...")
        
        try:
            query_data = {
                "input": "I need help with designing a high-performance system architecture. Please coordinate between your specialists to provide comprehensive guidance.",
                "config_path": self.config_path
            }
            
            start_time = time.time()
            response = self._make_request("POST", "/query", json=query_data)
            response_time = time.time() - start_time
            
            result = {
                "test_name": "Supervised Query",
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response_time_ms": round(response_time * 1000, 2)
            }
            
            if response.status_code == 200:
                data = response.json()
                result.update({
                    "response": data.get("response", "")[:300] + "...",
                    "metadata": data.get("metadata", {}),
                    "thread_id": data.get("thread_id")
                })
                log.info(f"✅ Supervised query test passed ({response_time*1000:.1f}ms)")
            else:
                result["error"] = response.text
                log.error(f"❌ Supervised query test failed: {response.status_code}")
            
            return result
            
        except Exception as e:
            log.error(f"Supervised query test failed: {e}")
            return {
                "test_name": "Supervised Query",
                "success": False,
                "error": str(e)
            }
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all tests and compile comprehensive results."""
        log.info("🧪 Starting comprehensive test suite...")
        print("=" * 80)
        print("🚀 ADVANCED MEMORY AGENT API TEST SUITE")
        print("=" * 80)
        
        start_time = time.time()
        all_results = []
        
        # Run all tests
        test_functions = [
            self.test_api_health,
            self.test_config_loading,
            self.test_advanced_memory_agents,
            self.test_memory_persistence,
            self.test_performance_under_load,
            self.test_memory_metrics_api,
            self.test_supervised_query
        ]
        
        for test_func in test_functions:
            try:
                print(f"\n🔍 Running {test_func.__name__}...")
                result = test_func()
                
                if isinstance(result, list):
                    all_results.extend(result)
                else:
                    all_results.append(result)
                    
            except Exception as e:
                log.error(f"Test function {test_func.__name__} failed: {e}")
                all_results.append({
                    "test_name": test_func.__name__,
                    "success": False,
                    "error": str(e)
                })
        
        total_time = time.time() - start_time
        
        # Compile summary
        total_tests = len(all_results)
        successful_tests = sum(1 for r in all_results if r.get("success", False))
        
        summary = {
            "test_suite": "Advanced Memory Agent API Tests",
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
            "total_time_seconds": round(total_time, 2),
            "config_path": self.config_path,
            "base_url": self.base_url,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "detailed_results": all_results
        }
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(f"Success Rate: {summary['success_rate']*100:.1f}%")
        print(f"Total Time: {total_time:.2f} seconds")
        print()
        
        # Print detailed results
        print("📋 DETAILED RESULTS:")
        print("-" * 40)
        for result in all_results:
            status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
            test_name = result.get("test_name", "Unknown Test")
            print(f"{status} {test_name}")
            
            if not result.get("success", False) and "error" in result:
                print(f"    Error: {result['error']}")
        
        print("\n" + "=" * 80)
        
        if summary['success_rate'] >= 0.8:
            print("🎉 TEST SUITE PASSED! Advanced memory agent is working correctly.")
        else:
            print("⚠️ TEST SUITE FAILED! Some issues detected with advanced memory agent.")
        
        return summary


def main():
    """Main function to run the test suite."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Advanced Memory Agent API")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--config", default="config/advanced_memory_agent_test.yaml", help="Config file path")
    parser.add_argument("--output", help="Output file for test results (JSON)")
    
    args = parser.parse_args()
    
    # Create tester
    tester = AdvancedMemoryAPITester(base_url=args.url, config_path=args.config)
    
    try:
        # Run comprehensive tests
        results = tester.run_comprehensive_tests()
        
        # Save results if output file specified
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Results saved to: {args.output}")
        
        # Exit with appropriate code
        exit_code = 0 if results['success_rate'] >= 0.8 else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⏹️ Test suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")
        log.error(f"Test suite error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
