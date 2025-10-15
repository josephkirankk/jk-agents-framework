#!/usr/bin/env python3
"""
Simplified test for dual format support in JK-Agents Framework.
Tests only the model creation functionality.
"""

import os
import sys
import yaml
import logging
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Configure minimal logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("test_simplified_format")

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env")
except ImportError:
    print("⚠️ dotenv not installed, skipping environment loading")

def test_both_model_formats():
    """Test both Google and LiteLLM model formats directly"""
    print("🧪 Testing Dual Format Support (Simplified)")
    print("=" * 60)

    # Import the required module
    try:
        from app.agent_builder import create_model_instance
        from app.enhanced_litellm_wrapper import is_litellm_model
        print("✅ Successfully imported model creation utilities")
    except ImportError as e:
        print(f"❌ Failed to import model utilities: {e}")
        return False
    
    # Test formats
    formats_to_test = [
        ("Google", "google:gemini-2.5-flash-lite"),
        ("LiteLLM", "gemini/gemini-2.5-flash-lite"),
        ("Azure", "azure/gpt-4.1"),
        ("OpenAI", "openai/gpt-4o")
    ]
    
    results = {}
    
    for format_name, model_id in formats_to_test:
        print(f"\n🔍 Testing {format_name} Format: {model_id}")
        print("-" * 60)
        
        # Check if LiteLLM recognizes the format
        is_litellm = is_litellm_model(model_id)
        print(f"Is LiteLLM model format: {is_litellm}")
        
        # Try to create model instance
        try:
            model_instance = create_model_instance(
                model_id=model_id,
                default_temperature=0.2
            )
            
            model_type = type(model_instance).__name__
            print(f"✅ Created model instance: {model_type}")
            
            # Check if it's a real model instance or just the model_id string
            if isinstance(model_instance, str):
                print(f"⚠️ Returned string, not model instance: {model_instance}")
                results[format_name] = False
            else:
                print(f"✅ Successfully created model instance")
                results[format_name] = True
        except Exception as e:
            print(f"❌ Failed to create model instance: {e}")
            results[format_name] = False
    
    # Print summary
    print("\n" + "=" * 60)
    print("📋 MODEL FORMAT SUPPORT SUMMARY:")
    print("=" * 60)
    
    all_success = True
    for format_name, success in results.items():
        print(f"{format_name} Format: {'✅ PASS' if success else '❌ FAIL'}")
        all_success = all_success and success
    
    print(f"\nOverall Result: {'✅ ALL FORMATS SUPPORTED' if all_success else '❌ SOME FORMATS FAILED'}")
    return all_success

if __name__ == "__main__":
    success = test_both_model_formats()
    sys.exit(0 if success else 1)
