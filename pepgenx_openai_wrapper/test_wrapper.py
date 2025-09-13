#!/usr/bin/env python3
"""
Test script for PepGenX OpenAI Wrapper.

This script provides comprehensive testing of the wrapper functionality,
including API compatibility, error handling, and performance validation.
"""

import asyncio
import json
import time
from typing import Dict, Any, List

import httpx
from openai import OpenAI


class WrapperTester:
    """Comprehensive tester for the PepGenX OpenAI Wrapper."""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = "sk-test-key"):
        self.base_url = base_url
        self.api_key = api_key
        self.openai_base_url = f"{base_url}/v1"
        
        # Initialize OpenAI client
        self.openai_client = OpenAI(
            api_key=api_key,
            base_url=self.openai_base_url
        )
        
        # Initialize HTTP client for direct API calls
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        self.results = {
            "passed": 0,
            "failed": 0,
            "errors": [],
            "tests": []
        }
    
    def log_test(self, name: str, passed: bool, details: str = "", duration: float = 0):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {name} ({duration:.2f}s)")
        if details:
            print(f"    {details}")
        
        self.results["tests"].append({
            "name": name,
            "passed": passed,
            "details": details,
            "duration": duration
        })
        
        if passed:
            self.results["passed"] += 1
        else:
            self.results["failed"] += 1
            self.results["errors"].append(f"{name}: {details}")
    
    async def test_health_endpoints(self):
        """Test all health check endpoints."""
        print("\n🏥 Testing Health Endpoints")
        print("-" * 40)
        
        # Test basic health
        start_time = time.time()
        try:
            response = await self.http_client.get(f"{self.base_url}/health")
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_test("Basic Health Check", True, f"Status: {data.get('status')}", duration)
                else:
                    self.log_test("Basic Health Check", False, f"Unexpected status: {data.get('status')}", duration)
            else:
                self.log_test("Basic Health Check", False, f"HTTP {response.status_code}", duration)
        except Exception as e:
            self.log_test("Basic Health Check", False, f"Exception: {str(e)}", time.time() - start_time)
        
        # Test liveness
        start_time = time.time()
        try:
            response = await self.http_client.get(f"{self.base_url}/health/live")
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Liveness Check", True, f"Status: {data.get('status')}", duration)
            else:
                self.log_test("Liveness Check", False, f"HTTP {response.status_code}", duration)
        except Exception as e:
            self.log_test("Liveness Check", False, f"Exception: {str(e)}", time.time() - start_time)
        
        # Test readiness
        start_time = time.time()
        try:
            response = await self.http_client.get(f"{self.base_url}/health/ready")
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                checks = data.get("checks", {})
                self.log_test("Readiness Check", True, f"Status: {status}, Checks: {len(checks)}", duration)
            elif response.status_code == 503:
                data = response.json()
                self.log_test("Readiness Check", False, f"Service not ready: {data}", duration)
            else:
                self.log_test("Readiness Check", False, f"HTTP {response.status_code}", duration)
        except Exception as e:
            self.log_test("Readiness Check", False, f"Exception: {str(e)}", time.time() - start_time)
    
    async def test_authentication(self):
        """Test authentication mechanisms."""
        print("\n🔐 Testing Authentication")
        print("-" * 40)
        
        # Test valid API key
        start_time = time.time()
        try:
            response = await self.http_client.get(
                f"{self.openai_base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                self.log_test("Valid API Key", True, "Authentication successful", duration)
            else:
                self.log_test("Valid API Key", False, f"HTTP {response.status_code}: {response.text}", duration)
        except Exception as e:
            self.log_test("Valid API Key", False, f"Exception: {str(e)}", time.time() - start_time)
        
        # Test invalid API key
        start_time = time.time()
        try:
            response = await self.http_client.get(
                f"{self.openai_base_url}/models",
                headers={"Authorization": "Bearer sk-invalid-key"}
            )
            duration = time.time() - start_time
            
            if response.status_code == 401:
                self.log_test("Invalid API Key Rejection", True, "Correctly rejected invalid key", duration)
            else:
                self.log_test("Invalid API Key Rejection", False, f"Expected 401, got {response.status_code}", duration)
        except Exception as e:
            self.log_test("Invalid API Key Rejection", False, f"Exception: {str(e)}", time.time() - start_time)
        
        # Test missing API key
        start_time = time.time()
        try:
            response = await self.http_client.get(f"{self.openai_base_url}/models")
            duration = time.time() - start_time
            
            if response.status_code == 401:
                self.log_test("Missing API Key Rejection", True, "Correctly rejected missing key", duration)
            else:
                self.log_test("Missing API Key Rejection", False, f"Expected 401, got {response.status_code}", duration)
        except Exception as e:
            self.log_test("Missing API Key Rejection", False, f"Exception: {str(e)}", time.time() - start_time)
    
    def test_openai_compatibility(self):
        """Test OpenAI library compatibility."""
        print("\n🤖 Testing OpenAI Library Compatibility")
        print("-" * 40)
        
        # Test models endpoint
        start_time = time.time()
        try:
            models = self.openai_client.models.list()
            duration = time.time() - start_time
            
            if hasattr(models, 'data') and len(models.data) > 0:
                model_count = len(models.data)
                self.log_test("List Models", True, f"Found {model_count} models", duration)
            else:
                self.log_test("List Models", False, "No models returned", duration)
        except Exception as e:
            self.log_test("List Models", False, f"Exception: {str(e)}", time.time() - start_time)
        
        # Test basic chat completion
        start_time = time.time()
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "user", "content": "Say 'Hello, World!' and nothing else."}
                ],
                max_tokens=10
            )
            duration = time.time() - start_time
            
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                self.log_test("Basic Chat Completion", True, f"Response: {content[:50]}...", duration)
            else:
                self.log_test("Basic Chat Completion", False, "No response content", duration)
        except Exception as e:
            self.log_test("Basic Chat Completion", False, f"Exception: {str(e)}", time.time() - start_time)
        
        # Test chat completion with system message
        start_time = time.time()
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What is 2+2?"}
                ],
                max_tokens=20
            )
            duration = time.time() - start_time
            
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                self.log_test("System Message Handling", True, f"Response: {content[:50]}...", duration)
            else:
                self.log_test("System Message Handling", False, "No response content", duration)
        except Exception as e:
            self.log_test("System Message Handling", False, f"Exception: {str(e)}", time.time() - start_time)
        
        # Test different models
        models_to_test = ["gpt-4", "gpt-3.5-turbo", "claude-3-sonnet"]
        for model in models_to_test:
            start_time = time.time()
            try:
                response = self.openai_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=5
                )
                duration = time.time() - start_time
                
                if response.choices and len(response.choices) > 0:
                    self.log_test(f"Model {model}", True, "Response received", duration)
                else:
                    self.log_test(f"Model {model}", False, "No response", duration)
            except Exception as e:
                self.log_test(f"Model {model}", False, f"Exception: {str(e)}", time.time() - start_time)
    
    async def test_error_handling(self):
        """Test error handling and edge cases."""
        print("\n⚠️  Testing Error Handling")
        print("-" * 40)
        
        # Test invalid model
        start_time = time.time()
        try:
            response = self.openai_client.chat.completions.create(
                model="invalid-model-name",
                messages=[{"role": "user", "content": "Test"}]
            )
            duration = time.time() - start_time
            self.log_test("Invalid Model Handling", False, "Should have raised an exception", duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Invalid Model Handling", True, f"Correctly raised: {type(e).__name__}", duration)
        
        # Test empty messages
        start_time = time.time()
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[]
            )
            duration = time.time() - start_time
            self.log_test("Empty Messages Handling", False, "Should have raised an exception", duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Empty Messages Handling", True, f"Correctly raised: {type(e).__name__}", duration)
        
        # Test invalid temperature
        start_time = time.time()
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": "Test"}],
                temperature=5.0  # Invalid temperature
            )
            duration = time.time() - start_time
            self.log_test("Invalid Temperature Handling", False, "Should have raised an exception", duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Invalid Temperature Handling", True, f"Correctly raised: {type(e).__name__}", duration)
    
    async def test_performance(self):
        """Test performance characteristics."""
        print("\n⚡ Testing Performance")
        print("-" * 40)
        
        # Test response time
        times = []
        for i in range(3):
            start_time = time.time()
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": f"Test message {i+1}"}],
                    max_tokens=10
                )
                duration = time.time() - start_time
                times.append(duration)
            except Exception as e:
                self.log_test(f"Performance Test {i+1}", False, f"Exception: {str(e)}", 0)
                return
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        if avg_time < 10.0:  # Reasonable response time
            self.log_test("Response Time Performance", True, 
                         f"Avg: {avg_time:.2f}s, Min: {min_time:.2f}s, Max: {max_time:.2f}s", avg_time)
        else:
            self.log_test("Response Time Performance", False, 
                         f"Too slow - Avg: {avg_time:.2f}s", avg_time)
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("🧪 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = self.results["passed"] + self.results["failed"]
        pass_rate = (self.results["passed"] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {self.results['passed']} ✅")
        print(f"Failed: {self.results['failed']} ❌")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        if self.results["errors"]:
            print("\n❌ FAILED TESTS:")
            for error in self.results["errors"]:
                print(f"   - {error}")
        
        if pass_rate >= 80:
            print(f"\n🎉 Overall Status: GOOD ({pass_rate:.1f}% pass rate)")
        elif pass_rate >= 60:
            print(f"\n⚠️  Overall Status: FAIR ({pass_rate:.1f}% pass rate)")
        else:
            print(f"\n💥 Overall Status: POOR ({pass_rate:.1f}% pass rate)")
    
    async def run_all_tests(self):
        """Run all test suites."""
        print("🚀 Starting PepGenX OpenAI Wrapper Tests")
        print("=" * 60)
        
        try:
            await self.test_health_endpoints()
            await self.test_authentication()
            self.test_openai_compatibility()
            await self.test_error_handling()
            await self.test_performance()
        finally:
            await self.http_client.aclose()
        
        self.print_summary()
        
        # Return exit code
        return 0 if self.results["failed"] == 0 else 1


async def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test PepGenX OpenAI Wrapper")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the wrapper")
    parser.add_argument("--api-key", default="sk-test-key", help="API key to use for testing")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    
    args = parser.parse_args()
    
    tester = WrapperTester(args.url, args.api_key)
    exit_code = await tester.run_all_tests()
    
    if args.json:
        print("\n" + json.dumps(tester.results, indent=2))
    
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
