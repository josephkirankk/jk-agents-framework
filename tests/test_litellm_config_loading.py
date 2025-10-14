#!/usr/bin/env python3
"""
Test LiteLLM Configuration Loading
This script tests loading the LiteLLM multimodal configurations to identify any issues
"""

import os
import sys
import yaml
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env")
except ImportError:
    print("⚠️ dotenv not installed, skipping environment variable loading")

def load_yaml_config(config_path):
    """Load a YAML configuration file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return True, config
    except Exception as e:
        return False, str(e)

def test_config_loading():
    """Test loading various LiteLLM configurations."""
    print("🧪 Testing LiteLLM Configuration Loading")
    print("-" * 60)
    
    config_dir = Path(__file__).parent.parent / "config"
    configs_to_test = [
        "litellm_multimodal_demo.yaml",
        "gemini_multimodal_example.yaml", 
        "multi_provider_agent.yaml",
    ]
    
    results = {}
    
    for config_file in configs_to_test:
        config_path = config_dir / config_file
        if not config_path.exists():
            results[config_file] = {
                "success": False,
                "error": f"File not found: {config_path}"
            }
            continue
            
        success, data = load_yaml_config(config_path)
        results[config_file] = {
            "success": success,
            "error": None if success else data,
            "data": data if success else None
        }
        
    # Print results
    print("\n🔍 Configuration Loading Results:")
    for config_file, result in results.items():
        status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
        print(f"{config_file}: {status}")
        if not result["success"]:
            print(f"  Error: {result['error']}")
        else:
            # Validate basic structure
            data = result["data"]
            model_config = data.get("models", {})
            default_model = model_config.get("default", "")
            
            print(f"  Default Model: {default_model}")
            
            # Check for LiteLLM configuration
            litellm_config = data.get("litellm", {})
            litellm_enabled = litellm_config.get("enabled", False)
            multimodal_support = litellm_config.get("multimodal_support", False)
            
            print(f"  LiteLLM Enabled: {litellm_enabled}")
            print(f"  Multimodal Support: {multimodal_support}")
            
            # Check conversation memory
            memory_config = data.get("conversation_memory", {})
            memory_enabled = memory_config.get("enabled", False)
            
            print(f"  Memory Enabled: {memory_enabled}")
        print()
        
    # Overall summary
    success_count = sum(1 for r in results.values() if r["success"])
    print(f"Summary: {success_count}/{len(configs_to_test)} configurations loaded successfully")
    
    # Environment variables
    print("\n🔐 API Key Environment Variables:")
    key_vars = [
        "OPENAI_API_KEY",
        "AZURE_API_KEY",
        "AZURE_OPENAI_API_KEY",
        "GOOGLE_API_KEY",
        "ANTHROPIC_API_KEY"
    ]
    
    for var in key_vars:
        value = os.getenv(var)
        if value:
            print(f"  {var}: ✅ Set (value hidden)")
        else:
            print(f"  {var}: ❌ Not set")
            
    return results

if __name__ == "__main__":
    results = test_config_loading()
    sys.exit(0 if all(r["success"] for r in results.values()) else 1)
