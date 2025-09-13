#!/usr/bin/env python3
"""
PepGenX OpenAI Wrapper - Reference Usage Examples

This script demonstrates how to use the PepGenX OpenAI Wrapper with various
scenarios and configurations. It shows all the ways you can interact with
the wrapper as if it were the OpenAI API.

Prerequisites:
1. Start the wrapper server: python start.py
2. Configure your .env file with proper credentials
3. Install dependencies: pip install openai httpx

Usage:
    python examples/reference_usage.py
"""

import asyncio
import json
import os
import sys
import time
from typing import List, Dict, Any

import httpx
import openai
from openai import OpenAI


class PepGenXWrapperDemo:
    """Comprehensive demonstration of PepGenX OpenAI Wrapper usage."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000", api_key: str = "sk-test-key1"):
        """Initialize the demo with wrapper configuration."""
        self.base_url = base_url
        self.api_key = api_key
        self.openai_client = OpenAI(
            api_key=api_key,
            base_url=f"{base_url}/v1"
        )
        
    def print_section(self, title: str):
        """Print a formatted section header."""
        print(f"\n{'='*60}")
        print(f"🚀 {title}")
        print(f"{'='*60}")
    
    def print_subsection(self, title: str):
        """Print a formatted subsection header."""
        print(f"\n{'─'*40}")
        print(f"📋 {title}")
        print(f"{'─'*40}")
    
    async def test_health_endpoints(self):
        """Test all health check endpoints."""
        self.print_section("HEALTH CHECK ENDPOINTS")
        
        endpoints = [
            ("/health/", "Basic Health Check"),
            ("/health/live", "Liveness Probe"),
            ("/health/ready", "Readiness Probe"),
            ("/metrics", "Prometheus Metrics")
        ]
        
        async with httpx.AsyncClient() as client:
            for endpoint, description in endpoints:
                self.print_subsection(description)
                try:
                    response = await client.get(f"{self.base_url}{endpoint}")
                    print(f"Status: {response.status_code}")
                    if response.status_code == 200:
                        if endpoint == "/metrics":
                            print("✅ Metrics endpoint accessible")
                        else:
                            data = response.json()
                            print(f"Response: {json.dumps(data, indent=2)}")
                    else:
                        print(f"❌ Unexpected status: {response.text}")
                except Exception as e:
                    print(f"❌ Error: {e}")
    
    def test_list_models(self):
        """Test the models endpoint."""
        self.print_section("LIST AVAILABLE MODELS")
        
        try:
            models = self.openai_client.models.list()
            print(f"✅ Found {len(models.data)} models:")
            for model in models.data:
                print(f"  • {model.id} (owned by: {model.owned_by})")
        except Exception as e:
            print(f"❌ Error listing models: {e}")
    
    def test_basic_chat_completion(self):
        """Test basic chat completion."""
        self.print_section("BASIC CHAT COMPLETION")
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "user", "content": "Hello! Please respond with a short greeting."}
                ],
                max_tokens=50,
                temperature=0.7
            )
            
            print("✅ Chat completion successful!")
            print(f"Model: {response.model}")
            print(f"Response: {response.choices[0].message.content}")
            print(f"Usage: {response.usage}")
            
        except Exception as e:
            print(f"❌ Error in chat completion: {e}")
    
    def test_system_message_handling(self):
        """Test system message handling."""
        self.print_section("SYSTEM MESSAGE HANDLING")
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful math tutor. Always explain your reasoning."},
                    {"role": "user", "content": "What is 15 + 27?"}
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            print("✅ System message handling successful!")
            print(f"Response: {response.choices[0].message.content}")
            
        except Exception as e:
            print(f"❌ Error with system message: {e}")
    
    def test_conversation_history(self):
        """Test multi-turn conversation."""
        self.print_section("MULTI-TURN CONVERSATION")
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "My name is Alice."},
            {"role": "assistant", "content": "Hello Alice! Nice to meet you."},
            {"role": "user", "content": "What's my name?"}
        ]
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=50
            )
            
            print("✅ Conversation history handling successful!")
            print(f"Response: {response.choices[0].message.content}")
            
        except Exception as e:
            print(f"❌ Error with conversation history: {e}")
    
    def test_different_models(self):
        """Test different model names."""
        self.print_section("DIFFERENT MODEL TESTING")
        
        models_to_test = ["gpt-4", "gpt-3.5-turbo", "claude-3-sonnet"]
        
        for model in models_to_test:
            self.print_subsection(f"Testing {model}")
            try:
                response = self.openai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": f"Say 'Hello from {model}' in a creative way."}
                    ],
                    max_tokens=30
                )
                
                print(f"✅ {model} successful!")
                print(f"Response: {response.choices[0].message.content}")
                
            except Exception as e:
                print(f"❌ Error with {model}: {e}")
    
    def test_parameter_variations(self):
        """Test different parameter combinations."""
        self.print_section("PARAMETER VARIATIONS")
        
        test_cases = [
            {
                "name": "High Temperature (Creative)",
                "params": {"temperature": 1.5, "max_tokens": 50}
            },
            {
                "name": "Low Temperature (Focused)",
                "params": {"temperature": 0.1, "max_tokens": 50}
            },
            {
                "name": "Top-p Sampling",
                "params": {"top_p": 0.8, "max_tokens": 50}
            },
            {
                "name": "With Penalties",
                "params": {
                    "frequency_penalty": 0.5,
                    "presence_penalty": 0.3,
                    "max_tokens": 50
                }
            }
        ]
        
        for test_case in test_cases:
            self.print_subsection(test_case["name"])
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "user", "content": "Write a short creative sentence about space."}
                    ],
                    **test_case["params"]
                )
                
                print(f"✅ {test_case['name']} successful!")
                print(f"Response: {response.choices[0].message.content}")
                
            except Exception as e:
                print(f"❌ Error with {test_case['name']}: {e}")
    
    def test_error_handling(self):
        """Test error handling scenarios."""
        self.print_section("ERROR HANDLING")
        
        error_tests = [
            {
                "name": "Invalid Model",
                "params": {"model": "invalid-model-name"}
            },
            {
                "name": "Empty Messages",
                "params": {"model": "gpt-4", "messages": []}
            },
            {
                "name": "Invalid Temperature",
                "params": {"model": "gpt-4", "temperature": 5.0}
            }
        ]
        
        for test in error_tests:
            self.print_subsection(test["name"])
            try:
                response = self.openai_client.chat.completions.create(
                    messages=[{"role": "user", "content": "Test"}],
                    max_tokens=10,
                    **test["params"]
                )
                print(f"❌ Expected error but got success: {response}")
            except Exception as e:
                print(f"✅ Correctly handled error: {type(e).__name__}: {e}")
    
    async def test_direct_http_api(self):
        """Test direct HTTP API calls."""
        self.print_section("DIRECT HTTP API CALLS")
        
        async with httpx.AsyncClient() as client:
            # Test chat completion via HTTP
            self.print_subsection("Chat Completion via HTTP")
            try:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4",
                        "messages": [
                            {"role": "user", "content": "Hello via HTTP!"}
                        ],
                        "max_tokens": 50
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print("✅ HTTP API call successful!")
                    print(f"Response: {data['choices'][0]['message']['content']}")
                else:
                    print(f"❌ HTTP error {response.status_code}: {response.text}")
                    
            except Exception as e:
                print(f"❌ HTTP API error: {e}")
    
    def test_authentication(self):
        """Test authentication scenarios."""
        self.print_section("AUTHENTICATION TESTING")
        
        # Test with invalid API key
        self.print_subsection("Invalid API Key")
        try:
            invalid_client = OpenAI(
                api_key="invalid-key",
                base_url=f"{self.base_url}/v1"
            )
            response = invalid_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=10
            )
            print(f"❌ Expected authentication error but got: {response}")
        except Exception as e:
            print(f"✅ Correctly rejected invalid API key: {type(e).__name__}")
    
    def performance_test(self):
        """Simple performance test."""
        self.print_section("PERFORMANCE TEST")
        
        num_requests = 3
        start_time = time.time()
        
        print(f"Making {num_requests} concurrent requests...")
        
        try:
            for i in range(num_requests):
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "user", "content": f"Request {i+1}: Say hello briefly."}
                    ],
                    max_tokens=20
                )
                print(f"✅ Request {i+1} completed")
            
            end_time = time.time()
            total_time = end_time - start_time
            avg_time = total_time / num_requests
            
            print(f"\n📊 Performance Results:")
            print(f"Total time: {total_time:.2f}s")
            print(f"Average per request: {avg_time:.2f}s")
            print(f"Requests per second: {num_requests/total_time:.2f}")
            
        except Exception as e:
            print(f"❌ Performance test error: {e}")
    
    async def run_all_tests(self):
        """Run all test scenarios."""
        print("🎯 PepGenX OpenAI Wrapper - Comprehensive Usage Demo")
        print("=" * 60)
        
        # Health checks
        await self.test_health_endpoints()
        
        # Basic functionality
        self.test_list_models()
        self.test_basic_chat_completion()
        self.test_system_message_handling()
        self.test_conversation_history()
        
        # Model variations
        self.test_different_models()
        self.test_parameter_variations()
        
        # Error handling
        self.test_error_handling()
        self.test_authentication()
        
        # HTTP API
        await self.test_direct_http_api()
        
        # Performance
        self.performance_test()
        
        print(f"\n{'='*60}")
        print("🎉 Demo completed! Check the results above.")
        print("💡 Tip: Start with QUICK_START_GUIDE.md for basic usage.")
        print(f"{'='*60}")


async def main():
    """Main function to run the demo."""
    # Configuration
    base_url = os.getenv("WRAPPER_URL", "http://127.0.0.1:8000")
    api_key = os.getenv("WRAPPER_API_KEY", "sk-test-key1")
    
    print(f"🔧 Configuration:")
    print(f"   Wrapper URL: {base_url}")
    print(f"   API Key: {api_key}")
    
    # Check if server is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health/", timeout=5.0)
            if response.status_code != 200:
                print(f"❌ Wrapper server not healthy: {response.status_code}")
                sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to wrapper server at {base_url}")
        print(f"   Error: {e}")
        print(f"   Make sure to start the server first: python start.py")
        sys.exit(1)
    
    # Run the demo
    demo = PepGenXWrapperDemo(base_url, api_key)
    await demo.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
