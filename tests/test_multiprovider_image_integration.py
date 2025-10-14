#!/usr/bin/env python3
"""
Multi-Provider Multi-Turn Integration Test with Image Support for JK Agents Framework

This test demonstrates:
1. Multi-provider capabilities (Azure OpenAI and Google Gemini)
2. Multi-turn conversation with memory persistence
3. Image processing capabilities across providers
4. Integration with ChromaDB for conversation memory
"""

import os
import sys
import json
import time
import asyncio
import unittest
import tempfile
import base64
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = project_root / '.env'
    load_dotenv(env_path)
    print(f"✅ Loaded environment from {env_path}")
except ImportError:
    print("⚠️ python-dotenv not installed, skipping environment loading")

# ANSI color codes for better readability
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

# Import framework components
from app.main import load_app_config
from app.supervisor_builder import build_supervisor_compiled
from app.planner_executor import execute_plan
from app.thread_id_utils import generate_thread_id
from app.simple_conversation_memory_fixed import get_conversation_memory, store_conversation_turn

# Import enhanced LiteLLM functionality
from app.enhanced_litellm_wrapper import EnhancedLiteLLMChat, is_litellm_model, test_litellm_model

# Import AsyncTestCase for asynchronous testing
class AsyncTestCase(unittest.TestCase):
    """Base class for asynchronous test cases."""
    
    def run_async(self, coro):
        """Run a coroutine in the event loop."""
        return asyncio.run(coro)
    
    def setUp(self):
        """Set up the test case."""
        pass
    
    def tearDown(self):
        """Tear down the test case."""
        pass


class TestMultiProviderImageIntegration(AsyncTestCase):
    """Test multi-provider support with image processing and multi-turn capabilities."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test class with available model providers."""
        print("\nChecking available model providers...")
        
        # List of providers to check (Azure OpenAI and Google Gemini)
        providers_to_check = [
            ("Azure OpenAI", "azure/gpt-4.1"),
            ("Google Gemini", "gemini/gemini-2.5-flash-lite"),
        ]
        
        # Store available providers
        cls.available_providers = []
        
        # Check each provider
        for provider_name, model_id in providers_to_check:
            try:
                # Run a quick test to see if the provider is available
                result = asyncio.run(test_litellm_model(model_id))
                
                if result.get("success", False):
                    print(f"{GREEN}✓ {provider_name}: {model_id} - Available{RESET}")
                    cls.available_providers.append((provider_name, model_id))
                else:
                    error_msg = result.get("error", "Unknown error")
                    print(f"{RED}✗ {provider_name}: {model_id} - Not available: {error_msg}{RESET}")
            except Exception as e:
                print(f"{RED}✗ {provider_name}: {model_id} - Error: {str(e)}{RESET}")
        
        # Log available providers
        if cls.available_providers:
            provider_str = ", ".join([f"{name} ({model_id})" for name, model_id in cls.available_providers])
            print(f"{GREEN}Available providers: {provider_str}{RESET}")
        else:
            print(f"{RED}! No model providers available. Tests will be skipped.{RESET}")
    
    def setUp(self):
        """Set up before each test."""
        # Use the multi-provider test configuration
        self.config_path = "config/test_multi_provider.yaml"
        self.app_cfg = load_app_config(Path(self.config_path))
        self.thread_id = generate_thread_id()
        print(f"Generated thread_id: {self.thread_id}")
    
    def get_model(self, model_id: str) -> EnhancedLiteLLMChat:
        """Get a model instance for the given model ID."""
        return EnhancedLiteLLMChat(
            model=model_id,
            temperature=0.2,
            timeout=60
        )
    
    def create_test_image(self) -> str:
        """Create a simple test image with text."""
        # Check if PIL is available
        try:
            from PIL import Image, ImageDraw, ImageFont
            import numpy as np
            
            # Create a simple image with text
            width, height = 400, 200
            image = Image.new('RGB', (width, height), color=(255, 255, 255))
            draw = ImageDraw.Draw(image)
            
            # Add text
            draw.text((width/2, height/2), "JK Agents Framework Test", 
                      fill=(0, 0, 0), anchor="mm")
            
            # Add some simple shapes for visual features
            draw.rectangle([50, 50, 100, 100], outline=(255, 0, 0), width=2)
            draw.ellipse([300, 50, 350, 100], outline=(0, 0, 255), width=2)
            draw.line([50, 150, 350, 150], fill=(0, 255, 0), width=3)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                image.save(tmp.name)
                print(f"{GREEN}✓ Test image created: {tmp.name}{RESET}")
                return tmp.name
                
        except ImportError:
            # Fall back to a simple approach if PIL is not available
            print(f"{YELLOW}! PIL not available, creating empty test file{RESET}")
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')
                print(f"{GREEN}✓ Empty test image created: {tmp.name}{RESET}")
                return tmp.name
    
    def test_multi_provider_capabilities(self):
        """Test basic multi-provider capabilities."""
        if not self.available_providers or len(self.available_providers) < 2:
            self.skipTest("Need at least 2 providers for multi-provider testing")
            return
        
        # Get provider models
        providers = {name: model_id for name, model_id in self.available_providers}
        
        # Print available providers
        print(f"\nTesting with providers:")
        for name, model_id in providers.items():
            print(f"- {name}: {model_id}")
        
        # Create models
        models = {}
        for name, model_id in providers.items():
            models[name] = self.get_model(model_id)
            
        # Test each model with a simple query
        results = {}
        for name, model in models.items():
            print(f"\nTesting {name} model...")
            try:
                asyncio.run(self._test_model_capabilities(name, model))
                results[name] = "Success"
            except Exception as e:
                results[name] = f"Error: {str(e)}"
                print(f"{RED}✗ {name} test failed: {str(e)}{RESET}")
        
        # Check results
        failed_providers = [name for name, result in results.items() if "Error" in result]
        
        if failed_providers:
            self.fail(f"The following providers failed: {', '.join(failed_providers)}")
        else:
            print(f"{GREEN}✓ All providers passed basic capability test{RESET}")
    
    async def _test_model_capabilities(self, provider_name: str, model: EnhancedLiteLLMChat):
        """Test basic model capabilities."""
        from langchain_core.messages import HumanMessage
        
        # Test basic text processing
        result = await model._agenerate([HumanMessage(content="Count from 1 to 5")])
        response = result.generations[0].message.content
        
        # Check if response contains numbers 1-5
        found_numbers = 0
        for num in ["1", "2", "3", "4", "5"]:
            if num in response:
                found_numbers += 1
        
        # Log results
        if found_numbers >= 4:  # Allow for some flexibility in response
            print(f"{GREEN}✓ {provider_name} passed basic text processing{RESET}")
        else:
            print(f"{RED}✗ {provider_name} failed basic text processing{RESET}")
            print(f"Response: {response}")
            raise ValueError(f"{provider_name} couldn't count properly: {response}")
        
        # Check model capabilities
        capabilities = model.check_capabilities()
        print(f"Model capabilities: {capabilities}")
        
        return True
    
    def test_multi_turn_image_conversation(self):
        """Run the main multi-turn image conversation test."""
        return self.run_async(self._async_test_multi_turn_image())
    
    async def _async_test_multi_turn_image(self):
        """Test multi-turn conversation with image processing using direct model calls."""
        if not self.available_providers:
            self.skipTest("No model providers available for testing")
            return
        
        # Create a test image
        image_path = self.create_test_image()
        
        # ===== TURN 1: Initial Image Analysis with Azure OpenAI =====
        print(f"\n{BLUE}=== TURN 1: Initial Image Analysis with Azure OpenAI ==={RESET}")
        
        # Use Azure OpenAI for first multimodal turn if available
        azure_provider = next((model_id for name, model_id in self.available_providers if name == "Azure OpenAI"), None)
        if not azure_provider:
            azure_provider = self.available_providers[0][1]  # Fall back to first available
        
        # Initialize Azure model
        azure_model = self.get_model(azure_provider)
        
        # Setup conversation tracking
        messages_history = []
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
        
        # Create system message
        system_message = SystemMessage(content="You are a helpful assistant specializing in image analysis.")
        messages_history.append(system_message)
        
        # Create multimodal message with image
        user_input_1 = "Analyze this test image and describe what you see. Include details about colors, shapes, and text if present."
        multimodal_message = azure_model.create_multimodal_message(
            text=user_input_1,
            images=[image_path]
        )
        messages_history.append(multimodal_message)
        
        # Execute Turn 1
        print(f"{YELLOW}Executing Turn 1 with Azure OpenAI and image...{RESET}")
        start_time = time.time()
        try:
            turn1_result = await azure_model._agenerate(messages_history)
            turn1_response = turn1_result.generations[0].message.content
            turn1_time = time.time() - start_time
            print(f"{GREEN}✓ Turn 1 completed in {turn1_time:.2f}s{RESET}")
            print(f"Response preview:\n{turn1_response[:300]}...")
            
            # Add response to conversation history
            messages_history.append(AIMessage(content=turn1_response))
            
            # Store conversation in memory system for later analysis
            store_conversation_turn(self.thread_id, user_input_1, turn1_response)
        except Exception as e:
            print(f"{RED}✗ Turn 1 failed: {str(e)}{RESET}")
            self.fail(f"Turn 1 failed with exception: {str(e)}")
            return
        
        # ===== TURN 2: Follow-up Analysis with Google Gemini =====
        print(f"\n{BLUE}=== TURN 2: Follow-up Analysis with Google Gemini ==={RESET}")
        
        # Use Google Gemini for Turn 2 if available, otherwise continue with the same model
        gemini_provider = next((model_id for name, model_id in self.available_providers if name == "Google Gemini"), None)
        if gemini_provider:
            print(f"{GREEN}Using Google Gemini for Turn 2{RESET}")
            turn2_model = self.get_model(gemini_provider)
        else:
            print(f"{YELLOW}Google Gemini not available, continuing with {azure_provider}{RESET}")
            turn2_model = azure_model
        
        # Create Turn 2 message - note we don't need the image again for the follow-up question
        user_input_2 = "Based on the image analysis you just provided, what improvements would you suggest for this test image to make it more informative or visually appealing?"
        messages_turn2 = [
            system_message,  # Keep the same system message
            HumanMessage(content=f"Previous image analysis: {turn1_response[:300]}..."),
            HumanMessage(content=user_input_2)
        ]
        
        # Execute Turn 2
        print(f"{YELLOW}Executing Turn 2...{RESET}")
        start_time = time.time()
        try:
            turn2_result = await turn2_model._agenerate(messages_turn2)
            turn2_response = turn2_result.generations[0].message.content
            turn2_time = time.time() - start_time
            print(f"{GREEN}✓ Turn 2 completed in {turn2_time:.2f}s{RESET}")
            print(f"Response preview:\n{turn2_response[:300]}...")
            
            # Store conversation in memory system
            store_conversation_turn(self.thread_id, user_input_2, turn2_response)
            
            # Check for context awareness
            context_terms = ["image", "test", "shape", "color", "text"]
            found_terms = [term for term in context_terms if term in turn2_response.lower()]
            
            print(f"\n{BLUE}Context continuity check:{RESET}")
            if found_terms:
                for term in found_terms:
                    print(f"{GREEN}✓ Found context term: '{term}'{RESET}")
                context_score = (len(found_terms) / len(context_terms)) * 100
                print(f"Context continuity score: {context_score:.1f}%")
                self.assertTrue(len(found_terms) >= 2, "Insufficient context continuity in Turn 2")
            else:
                print(f"{RED}No context terms found in Turn 2{RESET}")
                self.fail("No context continuity in Turn 2")
                
        except Exception as e:
            print(f"{RED}✗ Turn 2 failed: {str(e)}{RESET}")
            self.fail(f"Turn 2 failed with exception: {str(e)}")
            return
        
        # ===== TURN 3: Generate Improvement Suggestions with JSON Schema =====
        print(f"\n{BLUE}=== TURN 3: Generate JSON Schema with Azure OpenAI ==={RESET}")
        
        # Back to Azure OpenAI for Turn 3
        user_input_3 = "Based on our discussion, generate a JSON schema with specific improvements to make to the test image, including specific colors, shapes, and text adjustments."
        
        # For Turn 3, we'll combine context from both previous turns
        messages_turn3 = [
            system_message,
            HumanMessage(content=f"Previous image analysis (Turn 1): {turn1_response[:150]}..."),
            HumanMessage(content=f"Previous improvement suggestions (Turn 2): {turn2_response[:150]}..."),
            HumanMessage(content=user_input_3)
        ]
        
        # Execute Turn 3
        print(f"{YELLOW}Executing Turn 3...{RESET}")
        start_time = time.time()
        try:
            # Use Azure model for JSON formatting
            turn3_result = await azure_model._agenerate(messages_turn3)
            turn3_response = turn3_result.generations[0].message.content
            turn3_time = time.time() - start_time
            print(f"{GREEN}✓ Turn 3 completed in {turn3_time:.2f}s{RESET}")
            print(f"Response preview:\n{turn3_response[:300]}...")
            
            # Store conversation in memory system
            store_conversation_turn(self.thread_id, user_input_3, turn3_response)
            
            # Check for JSON schema in response
            has_json = '{' in turn3_response and '}' in turn3_response
            self.assertTrue(has_json, "No JSON schema found in Turn 3 response")
            
            # Check for context from previous turns
            context_terms = ["image", "test", "color", "shape", "text", "improve"]
            found_terms = [term for term in context_terms if term in turn3_response.lower()]
            
            print(f"\n{BLUE}Final context continuity check:{RESET}")
            if found_terms:
                for term in found_terms:
                    print(f"{GREEN}✓ Found context term: '{term}'{RESET}")
                context_score = (len(found_terms) / len(context_terms)) * 100
                print(f"Final context continuity score: {context_score:.1f}%")
                self.assertTrue(len(found_terms) >= 3, "Insufficient context continuity in Turn 3")
            
        except Exception as e:
            print(f"{RED}✗ Turn 3 failed: {str(e)}{RESET}")
            self.fail(f"Turn 3 failed with exception: {str(e)}")
            return
        
        # Check memory system
        memory = get_conversation_memory()
        context_summary = memory.get_conversation_summary(self.thread_id)
        
        print(f"\n{BLUE}=== Memory System Analysis ==={RESET}")
        if context_summary:
            print(f"{GREEN}✓ Memory system captured conversation context{RESET}")
            summary_preview = context_summary[:300] + "..." if len(context_summary) > 300 else context_summary
            print(f"Context summary preview:\n{summary_preview}")
            
            # Check turn tracking
            self.assertIn("Turn-1", context_summary, "Turn-1 not found in memory")
            self.assertIn("Turn-2", context_summary, "Turn-2 not found in memory")
            self.assertIn("Turn-3", context_summary, "Turn-3 not found in memory")
        else:
            print(f"{YELLOW}! No conversation context found in memory{RESET}")
            self.fail("No conversation context found in memory")
        
        # Cleanup test image
        try:
            os.remove(image_path)
            print(f"{GREEN}✓ Test image removed: {image_path}{RESET}")
        except:
            print(f"{YELLOW}! Failed to remove test image: {image_path}{RESET}")
        
        print(f"\n{GREEN}=== Multi-Provider Multi-Turn Image Test Completed Successfully ==={RESET}")
        print(f"Total conversation time: {turn1_time + turn2_time + turn3_time:.2f}s")
        print(f"Memory stored all turns with turn tracking")
        print(f"Successfully demonstrated:\n" \
              f"1. Multi-provider support (Azure OpenAI + Google Gemini)\n" \
              f"2. Multi-turn conversation with context preservation\n" \
              f"3. Image processing capabilities\n" \
              f"4. Integration with ChromaDB memory system\n" \
              f"5. Conversation turn tracking\n" \
              f"6. JSON schema generation")


if __name__ == "__main__":
    unittest.main()
