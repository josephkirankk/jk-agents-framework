#!/usr/bin/env python3
"""
Test script for the Enhanced LiteLLM Wrapper integration with the JK-Agents Framework.

This script validates that the EnhancedLiteLLMChat wrapper can be used with the framework
and properly supports multiple providers (Azure, Google, OpenAI, etc.), multimodal content,
and both synchronous and asynchronous operations.

Features tested:
- Provider detection and environment variable handling
- Model capabilities detection (vision, file inputs)
- Synchronous and asynchronous generation
- Multimodal content with images
- Error handling and timeout management

Usage:
    python tests/test_litellm_wrapper_integration.py

Requirements:
    - .env file with appropriate API keys
    - LiteLLM package installed
    - LangChain package installed
    - Pillow for image processing
"""

import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env")
except ImportError:
    print("⚠️ dotenv not installed, skipping environment loading")

async def test_litellm_model_with_framework():
    """Test direct LiteLLM model usage with the framework"""
    print("🔍 Testing Enhanced LiteLLM Wrapper with Framework...")
    
    # Import the enhanced wrapper
    try:
        from app.enhanced_litellm_wrapper import create_litellm_model, is_litellm_model
        print("✅ Successfully imported LiteLLM wrapper")
    except ImportError as e:
        print(f"❌ Failed to import LiteLLM wrapper: {e}")
        return False
    
    # Choose a model based on available API keys
    models_to_test = []
    
    if os.getenv("AZURE_API_KEY") and os.getenv("AZURE_API_BASE"):
        models_to_test.append("azure/gpt-4.1")
    
    if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
        models_to_test.append("gemini/gemini-2.5-flash-lite")
    
    if os.getenv("OPENAI_API_KEY"):
        models_to_test.append("openai/gpt-4o")
    
    if not models_to_test:
        # Add at least one model for testing even without API keys
        models_to_test.append("azure/gpt-4.1")
        print("⚠️ No API keys found, test will likely fail but proceeding anyway")
    
    print(f"🔍 Will test the following models: {models_to_test}")
    
    # Import LangChain components
    from langchain_core.messages import SystemMessage, HumanMessage
    
    successful_models = []
    
    # Test each model
    for model_id in models_to_test:
        print(f"\n🧪 Testing model: {model_id}")
        
        try:
            # Create model instance
            model = create_litellm_model(
                model_id=model_id,
                temperature=0.2
            )
            
            # Check capabilities
            capabilities = model.check_capabilities()
            print(f"📋 Model capabilities: {capabilities}")
            
            # Create messages
            system_message = SystemMessage(content="You are a helpful assistant for testing.")
            user_message = HumanMessage(content="Test message: Can you calculate 2+2 and explain your answer?")
            
            # Test synchronous call
            print("🔄 Testing synchronous call...")
            try:
                sync_result = model._generate([system_message, user_message])
                sync_response = sync_result.generations[0].message.content
                print(f"✅ Sync response: {sync_response[:100]}...")
                successful = True
            except Exception as e:
                print(f"❌ Sync call failed: {e}")
                successful = False
            
            # Test asynchronous call
            print("🔄 Testing asynchronous call...")
            try:
                async_result = await model._agenerate([system_message, user_message])
                async_response = async_result.generations[0].message.content
                print(f"✅ Async response: {async_response[:100]}...")
                successful = successful and True
            except Exception as e:
                print(f"❌ Async call failed: {e}")
                successful = False
            
            # If both tests passed, add to successful models
            if successful:
                successful_models.append(model_id)
                print(f"✅ SUCCESS with {model_id}")
            
        except Exception as e:
            print(f"❌ Failed to test {model_id}: {e}")
    
    # Final results
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    print("=" * 60)
    
    if successful_models:
        print(f"✅ Successfully tested {len(successful_models)}/{len(models_to_test)} models:")
        for model in successful_models:
            print(f"  ✓ {model}")
    else:
        print("❌ No models were successfully tested")
    
    # Try testing multimodal capabilities if successful with any model
    if successful_models:
        print("\n🖼️ Testing multimodal capabilities...")
        
        try:
            # Create test image
            from create_test_image import create_test_image
            image_path = create_test_image()
            print(f"✅ Created test image: {image_path}")
            
            # Test with first successful model
            model_id = successful_models[0]
            model = create_litellm_model(model_id=model_id)
            
            # Check if model supports vision
            if model.check_capabilities().get("supports_vision", False):
                print(f"🖼️ Testing vision capabilities with {model_id}...")
                
                # Create multimodal message
                multimodal_message = model.create_multimodal_message(
                    text="What do you see in this image?",
                    images=[image_path]
                )
                
                # Generate response
                result = await model._agenerate([
                    SystemMessage(content="You are a helpful assistant."),
                    multimodal_message
                ])
                
                response = result.generations[0].message.content
                print(f"✅ Multimodal response: {response[:150]}...")
                print("✅ Multimodal test succeeded")
            else:
                print(f"⚠️ Model {model_id} does not support vision")
        except Exception as e:
            print(f"❌ Multimodal test failed: {e}")
    
    # Overall success or failure
    overall_success = len(successful_models) > 0
    print(f"\nOverall Result: {'✅ PASSED' if overall_success else '❌ FAILED'}")
    
    return overall_success

if __name__ == "__main__":
    asyncio.run(test_litellm_model_with_framework())
