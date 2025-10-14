#!/usr/bin/env python3
"""
Simplified test for multi-model integration in JK-Agents Framework.

This test focuses on direct model calling rather than full agent workflow,
making it more resilient to API changes and clearer to understand.
"""

import os
import sys
import time
import asyncio
import unittest
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ANSI color codes for better readability
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = project_root / '.env'
    load_dotenv(env_path)
    print(f"{GREEN}✓ Loaded environment from {env_path}{RESET}")
except ImportError:
    print(f"{YELLOW}! dotenv not installed, using system environment{RESET}")

# Fix compatibility variables
if os.getenv('AZURE_OPENAI_API_VERSION') and not os.getenv('OPENAI_API_VERSION'):
    os.environ['OPENAI_API_VERSION'] = os.getenv('AZURE_OPENAI_API_VERSION')
    print(f"{GREEN}✓ Set OPENAI_API_VERSION from AZURE_OPENAI_API_VERSION for compatibility{RESET}")

# Import test utilities
from app.thread_id_utils import generate_thread_id
from app.enhanced_litellm_wrapper import test_litellm_model, EnhancedLiteLLMChat

class AsyncTestCase(unittest.TestCase):
    """Custom TestCase class that supports async test methods."""
    def run_async(self, coro):
        """Run an async coroutine and handle any exceptions."""
        import asyncio  # Import here to ensure it's available
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)

class TestMultiModelSimple(AsyncTestCase):
    """Test class for simplified multi-model integration testing."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests."""
        # Check for required environment variables
        cls.has_azure = bool(os.getenv("AZURE_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY"))
        cls.has_google = bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))
        cls.has_openai = bool(os.getenv("OPENAI_API_KEY"))
        cls.has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
        
        # Available models
        cls.available_models = {}
        if cls.has_azure:
            cls.available_models["azure"] = "azure/gpt-4.1"
            print(f"{GREEN}✓ Azure OpenAI API key found{RESET}")
        if cls.has_openai:
            cls.available_models["openai"] = "openai/gpt-4o-mini"
            print(f"{GREEN}✓ OpenAI API key found{RESET}")
        if cls.has_google:
            cls.available_models["google"] = "gemini/gemini-2.5-flash-lite"
            print(f"{GREEN}✓ Google Gemini API key found{RESET}")
        if cls.has_anthropic:
            cls.available_models["anthropic"] = "anthropic/claude-3-sonnet"
            print(f"{GREEN}✓ Anthropic Claude API key found{RESET}")
            
        # Set primary and secondary models
        cls.models = list(cls.available_models.values())
        cls.primary_model = cls.models[0] if cls.models else None
        cls.secondary_model = cls.models[1] if len(cls.models) > 1 else cls.primary_model
        
        if not cls.models:
            print(f"{RED}! No API keys found - tests will be limited{RESET}")
    
    def test_model_availability(self):
        """Test that models are available and responding."""
        return self.run_async(self._async_test_model_availability())
        
    async def _async_test_model_availability(self):
        """Test that models are available and responding."""
        if not self.available_models:
            self.skipTest("No models available to test")
            return
            
        print(f"\n{BLUE}=== Testing Model Availability ==={RESET}")
        
        for provider, model in self.available_models.items():
            print(f"\n{BLUE}Testing {provider} model: {model}{RESET}")
            start_time = time.time()
            
            try:
                result = await test_litellm_model(model, "What is 2+2?")
                
                elapsed = time.time() - start_time
                if result.get("success", False):
                    print(f"{GREEN}✓ Success in {elapsed:.2f}s{RESET}")
                    print(f"Response: {result['response'][:100]}...")
                    self.assertTrue(result["success"])
                    self.assertIn("4", result["response"])
                else:
                    print(f"{RED}✗ Failed: {result.get('error', 'Unknown error')}{RESET}")
                    self.fail(f"Model {model} test failed")
            except Exception as e:
                print(f"{RED}✗ Error: {str(e)}{RESET}")
                self.fail(f"Exception testing {model}: {str(e)}")
    
    def test_multi_turn_conversation(self):
        """Test multi-turn conversation with context preservation."""
        return self.run_async(self._async_test_multi_turn_conversation())
        
    async def _async_test_multi_turn_conversation(self):
        """Test multi-turn conversation with context preservation using direct model calls."""
        if not self.primary_model:
            self.skipTest("No models available for multi-turn test")
            return
            
        print(f"\n{BLUE}=== Testing Multi-Turn Conversation ==={RESET}")
        print(f"Using model: {self.primary_model}")
        
        # Create a chat model instance
        model = EnhancedLiteLLMChat(model=self.primary_model, temperature=0.2)
        
        # Generate a unique conversation ID
        thread_id = generate_thread_id()
        print(f"Conversation ID: {thread_id}")
        
        # Turn 1: Ask about fruits
        print(f"\n{BLUE}Turn 1: Ask about fruits{RESET}")
        messages_1 = [
            {"role": "system", "content": "You are a helpful assistant that provides accurate information."},
            {"role": "user", "content": "List 3 fruits with their colors."}
        ]
        
        start_time = time.time()
        try:
            result_1 = await model.ainvoke(messages_1)
            elapsed = time.time() - start_time
            print(f"{GREEN}✓ Response received in {elapsed:.2f}s{RESET}")
            
            # Extract content
            content_1 = result_1.content
            print(f"Response:\n{content_1}")
            
            # Simple validation
            self.assertIsNotNone(content_1)
            self.assertTrue(len(content_1) > 0)
            
            # Check for fruit names
            fruit_names = ["apple", "banana", "orange", "grape", "strawberry", "blueberry", 
                          "watermelon", "peach", "mango", "pear", "pineapple"]
            found_fruits = [fruit for fruit in fruit_names if fruit.lower() in content_1.lower()]
            
            print(f"Found fruits: {', '.join(found_fruits)}")
            self.assertTrue(len(found_fruits) >= 1, "No fruits found in response")
            
        except Exception as e:
            print(f"{RED}✗ Error in Turn 1: {str(e)}{RESET}")
            self.fail(f"Turn 1 failed with exception: {str(e)}")
            return
            
        # Turn 2: Ask about the fruit prices (referencing Turn 1)
        print(f"\n{BLUE}Turn 2: Ask about fruit prices{RESET}")
        messages_2 = messages_1 + [
            {"role": "assistant", "content": content_1},
            {"role": "user", "content": "What's the average price for each of these fruits?"}
        ]
        
        start_time = time.time()
        try:
            result_2 = await model.ainvoke(messages_2)
            elapsed = time.time() - start_time
            print(f"{GREEN}✓ Response received in {elapsed:.2f}s{RESET}")
            
            # Extract content
            content_2 = result_2.content
            print(f"Response:\n{content_2}")
            
            # Simple validation
            self.assertIsNotNone(content_2)
            self.assertTrue(len(content_2) > 0)
            
            # Check for fruit name references (context continuity)
            continuity_score = 0
            for fruit in found_fruits:
                if fruit.lower() in content_2.lower():
                    print(f"{GREEN}✓ Continuity: '{fruit}' from Turn 1 referenced in Turn 2{RESET}")
                    continuity_score += 1
                else:
                    print(f"{YELLOW}✗ '{fruit}' from Turn 1 not found in Turn 2{RESET}")
                    
            # Calculate continuity percentage
            if found_fruits:
                continuity_percentage = (continuity_score / len(found_fruits)) * 100
                print(f"\nContext continuity score: {continuity_percentage:.1f}%")
                
            # At least one fruit should be referenced
            self.assertGreater(continuity_score, 0, "No fruits from Turn 1 referenced in Turn 2")
            
        except Exception as e:
            print(f"{RED}✗ Error in Turn 2: {str(e)}{RESET}")
            self.fail(f"Turn 2 failed with exception: {str(e)}")
            
        print(f"\n{GREEN}===== Multi-Turn Test Completed Successfully ====={RESET}")

if __name__ == "__main__":
    unittest.main()
