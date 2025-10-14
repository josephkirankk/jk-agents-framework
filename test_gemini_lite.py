#!/usr/bin/env python3
"""Test if google/gemini-2.5-flash-lite model works with LiteLLM."""

import os
from dotenv import load_dotenv
load_dotenv()

def test_gemini_lite_model():
    """Test the google/gemini-2.5-flash-lite model."""
    
    print("\n" + "="*80)
    print("TESTING GOOGLE/GEMINI-2.5-FLASH-LITE MODEL")
    print("="*80 + "\n")
    
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ No GOOGLE_API_KEY or GEMINI_API_KEY found in environment")
        print("   Please set one of these environment variables")
        return
    
    print(f"✅ API Key found: {api_key[:10]}...")
    print()
    
    # Test different model name variants
    model_variants = [
        "google/gemini-2.5-flash-lite",
        "gemini/gemini-2.5-flash-lite", 
        "gemini-2.5-flash-lite",
        "google/gemini-2.0-flash-exp",  # Alternative known working model
        "gemini/gemini-2.0-flash-exp",
    ]
    
    print("Testing model variants:\n")
    
    for model_name in model_variants:
        try:
            print(f"Testing: {model_name}")
            
            from app.enhanced_litellm_wrapper import create_litellm_model
            model = create_litellm_model(model_id=model_name, temperature=0.1)
            
            print(f"  ✅ Model created successfully")
            print(f"  Capabilities: {model.check_capabilities()}")
            
            # Try a simple invoke
            from langchain_core.messages import HumanMessage
            try:
                result = model.invoke([HumanMessage(content="Say 'test ok' if you receive this")])
                response = result.content if hasattr(result, 'content') else str(result)
                print(f"  ✅ Model invoked successfully")
                print(f"  Response: {response[:100]}...")
            except Exception as invoke_err:
                print(f"  ⚠️  Model created but invoke failed: {invoke_err}")
            
            print()
            
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            print()
    
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)
    print("\nBased on the test results above, update your config to use a working model.")
    print("Most reliable options:")
    print("  - azure_openai:gpt-4o (if Azure OpenAI is configured)")
    print("  - openai:gpt-4o (if OpenAI API key is available)")
    print("  - google:gemini-2.0-flash-exp (if Google API key is available)")
    print()

if __name__ == "__main__":
    test_gemini_lite_model()