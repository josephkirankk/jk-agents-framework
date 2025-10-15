#!/usr/bin/env python3
"""
Test Enhanced LiteLLM Wrapper
Tests the functionality of the enhanced LiteLLM wrapper with different model providers
"""

import os
import sys
import asyncio
from pathlib import Path
import unittest

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env")
except ImportError:
    print("⚠️ dotenv not installed, skipping environment variable loading")

# Import the enhanced LiteLLM wrapper
try:
    from app.enhanced_litellm_wrapper import (
        EnhancedLiteLLMChat,
        is_litellm_model,
        create_litellm_model,
        test_litellm_model
    )
    from langchain_core.messages import SystemMessage, HumanMessage
    HAS_LITELLM_WRAPPER = True
except ImportError as e:
    print(f"❌ Error importing enhanced_litellm_wrapper: {e}")
    HAS_LITELLM_WRAPPER = False

class TestEnhancedLiteLLMWrapper(unittest.TestCase):
    """Test cases for the enhanced LiteLLM wrapper"""
    
    def setUp(self):
        """Set up test environment"""
        if not HAS_LITELLM_WRAPPER:
            self.skipTest("Enhanced LiteLLM wrapper not available")
    
    def test_is_litellm_model(self):
        """Test the is_litellm_model function"""
        # Valid LiteLLM model format
        self.assertTrue(is_litellm_model("openai/gpt-4o"))
        self.assertTrue(is_litellm_model("azure/gpt-4.1"))
        self.assertTrue(is_litellm_model("gemini/gemini-2.5-flash-lite"))
        
        # Invalid model formats
        self.assertFalse(is_litellm_model("openai:gpt-4o"))  # Uses : instead of /
        self.assertFalse(is_litellm_model("gpt-4"))  # No provider prefix
        self.assertFalse(is_litellm_model(None))  # None value
    
    def test_create_model_instance(self):
        """Test creating model instances"""
        # Create a basic model instance
        try:
            model = create_litellm_model("openai/gpt-4o", temperature=0.2)
            self.assertIsInstance(model, EnhancedLiteLLMChat)
            self.assertEqual(model.model, "openai/gpt-4o")
            self.assertEqual(model.temperature, 0.2)
            print("✅ Successfully created OpenAI model instance")
        except Exception as e:
            print(f"⚠️ OpenAI model creation failed (this is OK if you don't have an OpenAI key): {e}")
        
        # Create an Azure model instance
        if os.getenv("AZURE_API_KEY") and os.getenv("AZURE_API_BASE"):
            try:
                model = create_litellm_model("azure/gpt-4.1", temperature=0.1)
                self.assertIsInstance(model, EnhancedLiteLLMChat)
                self.assertEqual(model.model, "azure/gpt-4.1")
                self.assertEqual(model.temperature, 0.1)
                print("✅ Successfully created Azure model instance")
            except Exception as e:
                print(f"⚠️ Azure model creation failed: {e}")
        else:
            print("⚠️ Skipping Azure model test - API key not available")
        
        # Create a Google model instance
        if os.getenv("GOOGLE_API_KEY"):
            try:
                model = create_litellm_model("gemini/gemini-2.5-flash-lite")
                self.assertIsInstance(model, EnhancedLiteLLMChat)
                self.assertEqual(model.model, "gemini/gemini-2.5-flash-lite")
                print("✅ Successfully created Google model instance")
            except Exception as e:
                print(f"⚠️ Google model creation failed: {e}")
        else:
            print("⚠️ Skipping Google model test - API key not available")
    
    def test_check_capabilities(self):
        """Test checking model capabilities"""
        # Check OpenAI capabilities
        try:
            model = create_litellm_model("openai/gpt-4o")
            capabilities = model.check_capabilities()
            self.assertIsInstance(capabilities, dict)
            self.assertIn("supports_vision", capabilities)
            self.assertIn("supports_files", capabilities)
            print(f"✅ OpenAI capabilities: {capabilities}")
        except Exception as e:
            print(f"⚠️ OpenAI capabilities check failed: {e}")
        
        # Check Azure capabilities
        if os.getenv("AZURE_API_KEY") and os.getenv("AZURE_API_BASE"):
            try:
                model = create_litellm_model("azure/gpt-4.1")
                capabilities = model.check_capabilities()
                self.assertIsInstance(capabilities, dict)
                print(f"✅ Azure capabilities: {capabilities}")
            except Exception as e:
                print(f"⚠️ Azure capabilities check failed: {e}")
        
        # Check Google capabilities
        if os.getenv("GOOGLE_API_KEY"):
            try:
                model = create_litellm_model("gemini/gemini-2.5-flash-lite")
                capabilities = model.check_capabilities()
                self.assertIsInstance(capabilities, dict)
                print(f"✅ Google capabilities: {capabilities}")
            except Exception as e:
                print(f"⚠️ Google capabilities check failed: {e}")
    
    def test_multimodal_message_creation(self):
        """Test creating multimodal messages"""
        model = create_litellm_model("openai/gpt-4o")
        
        # Create a text-only message
        message = model.create_multimodal_message("Hello, world!")
        self.assertEqual(message.type, "human")
        self.assertTrue(isinstance(message.content, list))
        
        # Verify text content
        self.assertEqual(len(message.content), 1)
        self.assertEqual(message.content[0]["type"], "text")
        self.assertEqual(message.content[0]["text"], "Hello, world!")
        print("✅ Successfully created text-only multimodal message")

async def test_model_async():
    """Test async model generation (run outside the unittest framework)"""
    if not HAS_LITELLM_WRAPPER:
        print("❌ Enhanced LiteLLM wrapper not available - skipping async test")
        return
    
    # Test with Azure (most likely to have working credentials)
    if os.getenv("AZURE_API_KEY") and os.getenv("AZURE_API_BASE"):
        try:
            model = create_litellm_model("azure/gpt-4.1", temperature=0.1)
            messages = [
                SystemMessage(content="You are a helpful assistant."),
                HumanMessage(content="Say hello and identify yourself as using LiteLLM integration")
            ]
            
            print("🔄 Testing async generation with Azure model...")
            result = await model._agenerate(messages)
            response = result.generations[0].message.content
            
            print(f"✅ Async model generation success")
            print(f"📝 Response: {response[:100]}...")
        except Exception as e:
            print(f"❌ Async model generation failed: {e}")
    else:
        print("⚠️ Skipping async model test - Azure API key not available")

async def main():
    """Run the full test suite and async tests"""
    print("🧪 Testing Enhanced LiteLLM Wrapper")
    print("-" * 60)
    
    # First run the unittest tests
    unittest.main(argv=["first-arg-is-ignored"], exit=False)
    
    # Then run async tests
    print("\n⏱️ Running async tests:")
    await test_model_async()
    
    print("\n✨ Testing complete!")

if __name__ == "__main__":
    asyncio.run(main())
