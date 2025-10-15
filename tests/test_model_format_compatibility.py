#!/usr/bin/env python3
"""
Test script for model format compatibility in JK-Agents Framework
Verifies the seamless integration between different model format notations.
"""

import os
import sys
import yaml
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
    from app.config_model_format import parse_model_id, convert_to_litellm_format, normalize_model_config
    from app.agent_builder import create_model_instance
    HAS_MODEL_FORMAT = True
    print("✅ Successfully imported model format utilities")
except ImportError as e:
    HAS_MODEL_FORMAT = False
    print(f"❌ Failed to import model format utilities: {e}")

def test_model_format_parsing():
    """Test parsing different model format notations"""
    print("\n🧪 Testing Model Format Parsing")
    print("-" * 60)
    
    test_models = [
        "google:gemini-2.5-flash-lite",
        "google:gemini-2.5-flash-lite:0.2",
        "openai/gpt-4o",
        "openai/gpt-4o:0.1",
        "azure/gpt-4.1",
        "gemini/gemini-2.5-flash-lite",
        "anthropic/claude-3-5-sonnet",
        "regular-model-name"
    ]
    
    for model_id in test_models:
        model_info = parse_model_id(model_id)
        provider = model_info["provider"]
        model_name = model_info["model_name"]
        temperature = model_info["temperature"]
        original_format = model_info["original_format"]
        
        print(f"Model: {model_id}")
        print(f"  Provider: {provider}")
        print(f"  Name: {model_name}")
        print(f"  Temperature: {temperature}")
        print(f"  Format: {original_format}")
        print()
        
def test_format_conversion():
    """Test converting between different model formats"""
    print("\n🔄 Testing Format Conversion")
    print("-" * 60)
    
    # Test Google → LiteLLM format
    google_model = "google:gemini-2.5-flash-lite:0.2"
    model_info = parse_model_id(google_model)
    litellm_format = convert_to_litellm_format(model_info)
    
    print(f"Google format: {google_model}")
    print(f"LiteLLM format: {litellm_format}")
    print()
    
    # Test existing LiteLLM format
    litellm_model = "azure/gpt-4.1"
    model_info = parse_model_id(litellm_model)
    same_format = convert_to_litellm_format(model_info)
    
    print(f"Original LiteLLM format: {litellm_model}")
    print(f"After conversion: {same_format}")
    print()

def test_config_normalization():
    """Test normalizing configuration with different model formats"""
    print("\n📋 Testing Config Normalization")
    print("-" * 60)
    
    # Create test configs
    google_config = {
        "models": {
            "default": "google:gemini-2.5-flash-lite",
            "supervisor": "google:gemini-2.5-flash-lite"
        },
        "litellm": {
            "enabled": True,
            "multimodal_support": True
        }
    }
    
    azure_config = {
        "models": {
            "default": "azure/gpt-4.1",
            "supervisor": "azure/gpt-4.1"
        },
        "litellm": {
            "enabled": True
        }
    }
    
    # Test Google config normalization
    print("Google config before normalization:")
    print(f"  Default model: {google_config['models']['default']}")
    
    normalized_google = normalize_model_config(google_config)
    
    print("Google config after normalization:")
    print(f"  Default model: {normalized_google['models']['default']}")
    print()
    
    # Test Azure config normalization
    print("Azure config before normalization:")
    print(f"  Default model: {azure_config['models']['default']}")
    
    normalized_azure = normalize_model_config(azure_config)
    
    print("Azure config after normalization:")
    print(f"  Default model: {normalized_azure['models']['default']}")
    print()

def test_real_configs():
    """Test loading and normalizing real configuration files"""
    print("\n📄 Testing Real Configuration Files")
    print("-" * 60)
    
    config_dir = Path(__file__).parent.parent / "config"
    configs_to_test = [
        "python_exec_agent_working_google.yaml",
        "azure_openai_test.yaml",
        "litellm_multimodal_demo.yaml"
    ]
    
    for config_file in configs_to_test:
        config_path = config_dir / config_file
        if not config_path.exists():
            print(f"❌ Config file not found: {config_file}")
            continue
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                
            print(f"Testing config: {config_file}")
            print(f"  Original model: {config_data.get('models', {}).get('default', 'N/A')}")
            
            normalized = normalize_model_config(config_data)
            print(f"  Normalized model: {normalized.get('models', {}).get('default', 'N/A')}")
            print()
        except Exception as e:
            print(f"❌ Error processing {config_file}: {e}")
            print()

def test_model_instance_creation():
    """Test creating model instances with different formats"""
    print("\n🧠 Testing Model Instance Creation")
    print("-" * 60)
    
    # Only run if agent_builder is available
    if "create_model_instance" not in globals():
        print("❌ create_model_instance not available - skipping test")
        return
        
    test_models = [
        "google:gemini-2.5-flash-lite",
        "google:gemini-2.5-flash-lite:0.2",
        "azure/gpt-4.1",
        "openai/gpt-4o:0.1"
    ]
    
    for model_id in test_models:
        try:
            print(f"Creating model instance for: {model_id}")
            model_instance = create_model_instance(
                model_id=model_id,
                default_temperature=0.2
            )
            
            if model_instance == model_id:
                print(f"  ⚠️ Returned original model_id (no wrapper created)")
            else:
                print(f"  ✅ Created model instance: {type(model_instance).__name__}")
        except Exception as e:
            print(f"  ❌ Failed to create model: {e}")
        print()

def main():
    """Run all tests"""
    print("🚀 Testing Model Format Compatibility")
    print("=" * 60)
    
    if not HAS_MODEL_FORMAT:
        print("❌ Required modules not available")
        return 1
        
    # Run tests
    test_model_format_parsing()
    test_format_conversion()
    test_config_normalization()
    test_real_configs()
    test_model_instance_creation()
    
    print("=" * 60)
    print("✅ All tests completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
