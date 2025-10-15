#!/usr/bin/env python3
"""
Test script for dual format support in JK-Agents Framework.
Verifies that both Google format (google:model) and LiteLLM format (provider/model) 
work seamlessly within the framework.
"""

import os
import sys
import yaml
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

# Import from framework
try:
    from app.main import load_app_config
    from app.agent_builder import create_model_instance
    HAS_FRAMEWORK = True
    print("✅ Successfully imported framework modules")
except ImportError as e:
    HAS_FRAMEWORK = False
    print(f"❌ Failed to import framework modules: {e}")

async def test_config_with_format(format_name, model_format, expected_type):
    """Test framework with a specific model format"""
    print(f"\n🔍 Testing {format_name} Format")
    print("-" * 60)
    
    # Create a minimal test config
    config_data = {
        "models": {
            "default": model_format,
            "supervisor": model_format
        },
        "litellm": {
            "enabled": True,
            "multimodal_support": True
        }
    }
    
    # Save the test config
    test_dir = Path("temp_tests")
    test_dir.mkdir(exist_ok=True)
    
    config_path = test_dir / f"test_{format_name.lower()}_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)
    
    print(f"Created test config at {config_path}")
    
    try:
        # Load the config using the framework's loader
        config = load_app_config(config_path)
        print(f"✅ Successfully loaded configuration")
        print(f"  Default model: {config.models.get('default')}")
        
        # Create a model instance
        model_instance = create_model_instance(
            model_id=config.models.get("default"),
            default_temperature=0.2,
            app_config=config.dict()
        )
        
        model_type = type(model_instance).__name__
        print(f"✅ Created model instance: {model_type}")
        
        if expected_type in model_type:
            print(f"✅ Model instance is correct type ({expected_type})")
        else:
            print(f"❌ Expected {expected_type}, got {model_type}")
            
        return True
    except Exception as e:
        print(f"❌ Failed to use {format_name} format: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Testing Dual Format Support")
    print("=" * 60)
    
    if not HAS_FRAMEWORK:
        print("❌ Required framework modules not available")
        return 1
    
    # Test Google format
    google_success = await test_config_with_format(
        "Google", 
        "google:gemini-2.5-flash-lite", 
        "EnhancedLiteLLMChat"
    )
    
    # Test LiteLLM format
    litellm_success = await test_config_with_format(
        "LiteLLM",
        "gemini/gemini-2.5-flash-lite",
        "EnhancedLiteLLMChat"
    )
    
    # Test Azure format
    azure_success = await test_config_with_format(
        "Azure",
        "azure/gpt-4.1",
        "EnhancedLiteLLMChat"
    )
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 DUAL FORMAT SUPPORT SUMMARY:")
    print("=" * 60)
    print(f"Google Format: {'✅ PASS' if google_success else '❌ FAIL'}")
    print(f"LiteLLM Format: {'✅ PASS' if litellm_success else '❌ FAIL'}")
    print(f"Azure Format: {'✅ PASS' if azure_success else '❌ FAIL'}")
    
    all_success = google_success and litellm_success and azure_success
    print(f"\nOverall Result: {'✅ ALL FORMATS SUPPORTED' if all_success else '❌ SOME FORMATS FAILED'}")
    
    return 0 if all_success else 1

if __name__ == "__main__":
    asyncio.run(main())
