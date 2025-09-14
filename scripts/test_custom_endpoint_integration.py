#!/usr/bin/env python3
"""
Test script for Custom OpenAI Endpoint integration with JK-Agents.

This script tests the integration by making API calls to both the custom
OpenAI-compatible service and the JK-Agents API to ensure everything works.

Usage:
    python scripts/test_custom_endpoint_integration.py
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any

import requests

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class CustomEndpointIntegrationTester:
    """Test suite for custom OpenAI endpoint integration."""
    
    def __init__(self, service_url: str = "http://127.0.0.1:8080",
                 api_url: str = "http://127.0.0.1:8001"):
        self.service_url = service_url
        self.api_url = api_url
        # Use the correct API key for custom OpenAI service
        self.service_api_key = os.getenv("CUSTOM_OPENAI_API_KEY", "sk-test-key1")

        # Set environment variables for the test
        os.environ["OPENAI_BASE_URL"] = f"{service_url}/v1"
        os.environ["OPENAI_API_KEY"] = self.service_api_key
    
    def print_test(self, name: str, status: bool, details: str = "", 
                   duration: float = 0):
        """Print test result."""
        status_icon = "✅" if status else "❌"
        duration_str = f" ({duration:.2f}s)" if duration > 0 else ""
        print(f"{status_icon} {name}{duration_str}")
        if details:
            print(f"   {details}")
    
    def test_service_health(self) -> bool:
        """Test custom service health endpoint."""
        try:
            start_time = time.time()
            response = requests.get(f"{self.service_url}/health", timeout=5)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                self.print_test("Custom Service Health", True, 
                              f"Status: {response.status_code}", duration)
                return True
            else:
                self.print_test("Custom Service Health", False, 
                              f"Status: {response.status_code}", duration)
                return False
                
        except Exception as e:
            self.print_test("Custom Service Health", False, f"Error: {e}")
            return False
    
    def test_service_models_endpoint(self) -> bool:
        """Test custom service models endpoint."""
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.service_url}/v1/models",
                headers={"Authorization": f"Bearer {self.service_api_key}"},
                timeout=10
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                model_count = len(data.get("data", []))
                self.print_test("Custom Service Models", True, 
                              f"Found {model_count} models", duration)
                return True
            else:
                self.print_test("Custom Service Models", False, 
                              f"Status: {response.status_code}", duration)
                return False
                
        except Exception as e:
            self.print_test("Custom Service Models", False, f"Error: {e}")
            return False
    
    def test_service_chat_completion(self) -> bool:
        """Test custom service chat completion."""
        try:
            start_time = time.time()
            payload = {
                "model": "gpt-4",
                "messages": [
                    {"role": "user", "content": "Say 'Hello from custom service!'"}
                ],
                "max_tokens": 20
            }
            
            response = requests.post(
                f"{self.service_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.service_api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                self.print_test("Custom Service Chat", True, 
                              f"Response: {content[:50]}...", duration)
                return True
            else:
                self.print_test("Custom Service Chat", False, 
                              f"Status: {response.status_code}", duration)
                return False
                
        except Exception as e:
            self.print_test("Custom Service Chat", False, f"Error: {e}")
            return False
    
    def test_jk_agents_api_health(self) -> bool:
        """Test JK-Agents API health."""
        try:
            start_time = time.time()
            response = requests.get(f"{self.api_url}/health", timeout=5)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                self.print_test("JK-Agents API Health", True, 
                              f"Status: {response.status_code}", duration)
                return True
            else:
                self.print_test("JK-Agents API Health", False, 
                              f"Status: {response.status_code}", duration)
                return False
                
        except Exception as e:
            self.print_test("JK-Agents API Health", False, f"Error: {e}")
            return False
    
    def test_openai_model_creation(self) -> bool:
        """Test OpenAI model creation with custom endpoint."""
        try:
            start_time = time.time()
            
            # Import and test the model creation function
            from app.agent_builder import create_model_instance
            
            model_instance = create_model_instance("openai:gpt-4")
            duration = time.time() - start_time
            
            # Check if we got a proper model instance
            if hasattr(model_instance, '__class__'):
                model_type = type(model_instance).__name__
                self.print_test("OpenAI Model Creation", True, 
                              f"Created: {model_type}", duration)
                return True
            else:
                self.print_test("OpenAI Model Creation", False, 
                              f"Got: {type(model_instance)}", duration)
                return False
                
        except Exception as e:
            self.print_test("OpenAI Model Creation", False, f"Error: {e}")
            return False
    
    def test_jk_agents_with_custom_endpoint(self) -> bool:
        """Test JK-Agents API with custom OpenAI endpoint."""
        try:
            start_time = time.time()
            
            # Test with a simple worker request using custom endpoint
            payload = {
                "agent_name": "custom_assistant",
                "input": "Say hello and confirm you're working correctly",
                "config_path": "config/openai_custom_endpoint.yaml"
            }
            
            response = requests.post(
                f"{self.api_url}/worker",
                json=payload,
                timeout=60
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    response_text = data.get("response", "")
                    self.print_test("JK-Agents with Custom Endpoint", True, 
                                  f"Response: {response_text[:100]}...", duration)
                    return True
                else:
                    error = data.get("error", "Unknown error")
                    self.print_test("JK-Agents with Custom Endpoint", False, 
                                  f"Agent error: {error}", duration)
                    return False
            else:
                self.print_test("JK-Agents with Custom Endpoint", False, 
                              f"Status: {response.status_code}", duration)
                return False
                
        except Exception as e:
            self.print_test("JK-Agents with Custom Endpoint", False, f"Error: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all integration tests."""
        print("🧪 Custom OpenAI Endpoint Integration Test Suite")
        print("=" * 60)
        
        tests = [
            ("Custom Service Health", self.test_service_health),
            ("Custom Service Models", self.test_service_models_endpoint),
            ("Custom Service Chat", self.test_service_chat_completion),
            ("JK-Agents API Health", self.test_jk_agents_api_health),
            ("OpenAI Model Creation", self.test_openai_model_creation),
            ("JK-Agents Integration", self.test_jk_agents_with_custom_endpoint),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                self.print_test(test_name, False, f"Unexpected error: {e}")
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed}/{total} passed")
        
        if passed == total:
            print("🎉 All tests passed! Custom endpoint integration working!")
            return True
        else:
            print("❌ Some tests failed. Check configuration and services.")
            return False


def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test custom endpoint integration")
    parser.add_argument("--service-url", default="http://127.0.0.1:8080",
                       help="Custom service URL (default: http://127.0.0.1:8080)")
    parser.add_argument("--api-url", default="http://127.0.0.1:8001",
                       help="JK-Agents API URL (default: http://127.0.0.1:8001)")
    
    args = parser.parse_args()
    
    tester = CustomEndpointIntegrationTester(args.service_url, args.api_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
