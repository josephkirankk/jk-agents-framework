#!/usr/bin/env python3
"""
Azure OpenAI Integration Test for JK-Agents Framework

This script tests the Azure OpenAI integration specifically, including:
1. Basic model functionality
2. Multi-turn conversation with context preservation
3. Proper configuration handling
"""

import os
import sys
import time
import json
import asyncio
import unittest
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ANSI colors for output
GREEN = "\033[92m"
YELLOW = "\033[93m" 
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"{GREEN}✓ Loaded environment from {env_path}{RESET}")
    else:
        print(f"{YELLOW}! No .env file found at {env_path}{RESET}")
except ImportError:
    print(f"{YELLOW}! dotenv not installed, using system environment{RESET}")

# Ensure Azure OpenAI compatibility
if os.getenv('AZURE_OPENAI_API_VERSION') and not os.getenv('OPENAI_API_VERSION'):
    os.environ['OPENAI_API_VERSION'] = os.getenv('AZURE_OPENAI_API_VERSION')
    print(f"{GREEN}✓ Set OPENAI_API_VERSION from AZURE_OPENAI_API_VERSION for compatibility{RESET}")

# Import framework components
from app.thread_id_utils import generate_thread_id
from app.enhanced_litellm_wrapper import test_litellm_model, EnhancedLiteLLMChat

class AsyncTestCase(unittest.TestCase):
    """Custom TestCase class that supports async test methods."""
    def run_async(self, coro):
        """Run an async coroutine and handle any exceptions."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)

class TestAzureOpenAI(AsyncTestCase):
    """Test Azure OpenAI integration with JK-Agents Framework."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests."""
        # Check for Azure OpenAI configuration
        cls.azure_api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_API_KEY")
        cls.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("AZURE_API_BASE")
        cls.azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION") or os.getenv("AZURE_API_VERSION")
        
        cls.has_azure = bool(cls.azure_api_key and cls.azure_endpoint)
        
        if cls.has_azure:
            print(f"{GREEN}✓ Azure OpenAI configuration found:{RESET}")
            print(f"  - API Key: {cls.azure_api_key[:4]}...{cls.azure_api_key[-4:]}")
            print(f"  - Endpoint: {cls.azure_endpoint}")
            print(f"  - API Version: {cls.azure_api_version}")
            
            # Define Azure model to test
            cls.azure_model = "azure/gpt-4.1"
        else:
            print(f"{RED}✗ Azure OpenAI configuration not found{RESET}")
            print("Required environment variables:")
            print("  - AZURE_OPENAI_API_KEY or AZURE_API_KEY")
            print("  - AZURE_OPENAI_ENDPOINT or AZURE_API_BASE")
            print("  - AZURE_OPENAI_API_VERSION or AZURE_API_VERSION")
    
    def test_azure_model_availability(self):
        """Test that Azure OpenAI model is available and responding."""
        return self.run_async(self._async_test_azure_model())
    
    async def _async_test_azure_model(self):
        """Test Azure OpenAI model response."""
        if not self.has_azure:
            self.skipTest("Azure OpenAI configuration not found")
            return
        
        print(f"\n{BLUE}=== Testing Azure OpenAI Model ==={RESET}")
        start_time = time.time()
        
        try:
            # Simple test query
            result = await test_litellm_model(
                self.azure_model, 
                "Please calculate the square root of 144 and explain your calculation."
            )
            
            elapsed = time.time() - start_time
            if result.get("success", False):
                print(f"{GREEN}✓ Azure OpenAI test successful ({elapsed:.2f}s){RESET}")
                print(f"Response: {result['response'][:150]}...")
                
                # Verify expected content in response
                self.assertTrue(result["success"])
                self.assertIn("12", result["response"], "Expected square root of 144 (12) in response")
            else:
                error = result.get("error", "Unknown error")
                print(f"{RED}✗ Azure OpenAI test failed: {error}{RESET}")
                self.fail(f"Azure OpenAI test failed: {error}")
        except Exception as e:
            print(f"{RED}✗ Exception during Azure OpenAI test: {str(e)}{RESET}")
            self.fail(f"Exception: {str(e)}")
    
    def test_azure_multi_turn_conversation(self):
        """Test multi-turn conversation with Azure OpenAI."""
        return self.run_async(self._async_test_azure_multi_turn())
    
    async def _async_test_azure_multi_turn(self):
        """Test multi-turn conversation with Azure OpenAI."""
        if not self.has_azure:
            self.skipTest("Azure OpenAI configuration not found")
            return
        
        print(f"\n{BLUE}=== Testing Azure OpenAI Multi-Turn Conversation ==={RESET}")
        
        # Create chat model instance
        model = EnhancedLiteLLMChat(model=self.azure_model, temperature=0.2)
        
        # Generate unique conversation ID
        thread_id = generate_thread_id()
        print(f"Conversation ID: {thread_id}")
        
        # TURN 1: Ask for a data structure
        print(f"\n{BLUE}Turn 1: Request data structure{RESET}")
        messages_1 = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Create a JSON object with information about 3 planets: Earth, Mars, and Jupiter. Include diameter, distance from sun, and one interesting fact for each."}
        ]
        
        start_time = time.time()
        try:
            # Execute turn 1
            result_1 = await model.ainvoke(messages_1)
            elapsed_1 = time.time() - start_time
            
            content_1 = result_1.content
            print(f"{GREEN}✓ Turn 1 completed ({elapsed_1:.2f}s){RESET}")
            print(f"Response:\n{content_1[:300]}...")
            
            # Validate JSON in response
            self.assertIsNotNone(content_1)
            self.assertTrue("Earth" in content_1)
            self.assertTrue("Mars" in content_1)
            self.assertTrue("Jupiter" in content_1)
            
            # Extract JSON from response for validation
            try:
                json_content = self._extract_json(content_1)
                print(f"{GREEN}✓ Valid JSON detected{RESET}")
            except Exception as e:
                print(f"{YELLOW}! Could not extract valid JSON: {str(e)}{RESET}")
                
        except Exception as e:
            print(f"{RED}✗ Error in Turn 1: {str(e)}{RESET}")
            self.fail(f"Turn 1 failed with exception: {str(e)}")
            return
            
        # TURN 2: Build on previous response
        print(f"\n{BLUE}Turn 2: Build on previous data{RESET}")
        
        messages_2 = messages_1 + [
            {"role": "assistant", "content": content_1},
            {"role": "user", "content": "Add one moon for each planet with its diameter."}
        ]
        
        start_time = time.time()
        try:
            # Execute turn 2
            result_2 = await model.ainvoke(messages_2)
            elapsed_2 = time.time() - start_time
            
            content_2 = result_2.content
            print(f"{GREEN}✓ Turn 2 completed ({elapsed_2:.2f}s){RESET}")
            print(f"Response:\n{content_2[:300]}...")
            
            # Check for context continuity
            planets = ["Earth", "Mars", "Jupiter"]
            continuity_score = 0
            
            for planet in planets:
                if planet in content_2:
                    print(f"{GREEN}✓ Context continuity: '{planet}' from Turn 1 found in Turn 2{RESET}")
                    continuity_score += 1
                else:
                    print(f"{YELLOW}✗ '{planet}' from Turn 1 not found in Turn 2{RESET}")
            
            # Calculate and display continuity percentage
            continuity_percentage = (continuity_score / len(planets)) * 100
            print(f"\nContext continuity score: {continuity_percentage:.1f}%")
            
            # Test should pass if at least one planet was carried over
            self.assertGreater(continuity_score, 0, "No planets from Turn 1 referenced in Turn 2")
            
            # Look for moon information (shows new information was added)
            moon_references = ["Moon", "Phobos", "Ganymede", "Io", "Europa", "moon"]
            moon_found = any(moon.lower() in content_2.lower() for moon in moon_references)
            self.assertTrue(moon_found, "No moon information found in Turn 2")
            
        except Exception as e:
            print(f"{RED}✗ Error in Turn 2: {str(e)}{RESET}")
            self.fail(f"Turn 2 failed with exception: {str(e)}")
            
        print(f"\n{GREEN}===== Azure OpenAI Multi-Turn Test Completed Successfully ====={RESET}")
    
    def _extract_json(self, text):
        """Extract JSON from text response."""
        import re
        import json
        
        # First look for JSON blocks in markdown
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if json_match:
            json_str = json_match.group(1)
            return json.loads(json_str)
        
        # Then try to find JSON objects with curly braces
        json_match = re.search(r'(\{[\s\S]*\})', text)
        if json_match:
            json_str = json_match.group(1)
            return json.loads(json_str)
        
        raise ValueError("No JSON found in response")

if __name__ == "__main__":
    unittest.main()
