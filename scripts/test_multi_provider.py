#!/usr/bin/env python3
"""
Multi-Provider Configuration Test Script

This script helps validate your multi-provider OpenAI configuration
by testing different providers and model combinations.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import load_app_config


def test_environment_config():
    """Test environment variable configuration."""
    print("🔧 Testing Environment Configuration")
    print("=" * 50)
    
    # Load .env file
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded .env from: {env_path}")
    else:
        print(f"⚠️  No .env file found at: {env_path}")
    
    # Check OpenAI configuration
    openai_key = os.getenv("OPENAI_API_KEY")
    openai_base = os.getenv("OPENAI_BASE_URL")
    
    print(f"\n📡 OpenAI Configuration:")
    print(f"  API Key: {'✅ Set' if openai_key else '❌ Not set'}")
    print(f"  Base URL: {openai_base if openai_base else '❌ Not set (will use default)'}")
    
    # Check Azure OpenAI configuration
    azure_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    azure_version = os.getenv("AZURE_OPENAI_API_VERSION")
    
    print(f"\n☁️  Azure OpenAI Configuration:")
    print(f"  API Key: {'✅ Set' if azure_key else '❌ Not set'}")
    print(f"  Endpoint: {azure_endpoint if azure_endpoint else '❌ Not set'}")
    print(f"  Deployment: {azure_deployment if azure_deployment else '❌ Not set'}")
    print(f"  API Version: {azure_version if azure_version else '❌ Not set'}")
    
    # Determine provider configuration
    print(f"\n🎯 Provider Selection Logic:")
    is_azure = bool(azure_key and azure_endpoint)
    has_base_url = bool(openai_base)
    
    if is_azure and not has_base_url:
        print("  📋 Mode: Azure OpenAI (auto-conversion enabled)")
        print("  📝 openai: models will be converted to azure_openai:")
    elif has_base_url:
        print(f"  🏠 Mode: Local/Custom OpenAI-compatible server")
        print(f"  📝 openai: models will use: {openai_base}")
        if is_azure:
            print("  📝 azure_openai: models will use Azure OpenAI")
    elif openai_key:
        print("  🌐 Mode: Regular OpenAI API")
        print("  📝 openai: models will use OpenAI API")
    else:
        print("  ❌ No valid configuration found!")
    
    return is_azure, has_base_url, bool(openai_key)


def test_config_loading(config_path=None):
    """Test loading and parsing of YAML configuration."""
    print(f"\n📄 Testing Configuration Loading")
    print("=" * 50)
    
    try:
        if config_path:
            config_file = Path(config_path)
        else:
            config_file = Path(__file__).parent.parent / "config" / "multi_provider_example.yaml"
        
        if not config_file.exists():
            print(f"❌ Config file not found: {config_file}")
            return None
            
        print(f"📂 Loading config: {config_file}")
        app_config = load_app_config(config_file)
        
        print(f"✅ Configuration loaded successfully!")
        print(f"\n📊 Model Configuration:")
        for key, model in app_config.models.items():
            provider = "Azure OpenAI" if model.startswith("azure_openai:") else "OpenAI/Local"
            print(f"  {key}: {model} ({provider})")
        
        print(f"\n👥 Agents Configuration:")
        for agent in app_config.agents:
            model = agent.model or app_config.models.get("default", "Not specified")
            provider = "Azure OpenAI" if model.startswith("azure_openai:") else "OpenAI/Local"
            print(f"  {agent.name}: {model} ({provider})")
        
        return app_config
        
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return None


def test_model_provider_mapping(app_config):
    """Test how models are mapped to providers."""
    print(f"\n🗺️  Testing Model-to-Provider Mapping")
    print("=" * 50)
    
    if not app_config:
        print("❌ No configuration to test")
        return
    
    # Test different model types
    test_models = [
        "openai:gpt-4o-mini",
        "openai:google/gemma-3n-e4b", 
        "azure_openai:gpt-4o-mini",
        "azure_openai:custom-deployment"
    ]
    
    for model in test_models:
        if model.startswith("azure_openai:"):
            provider = "Azure OpenAI"
            requirements = "Requires AZURE_OPENAI_* environment variables"
        else:
            if os.getenv("OPENAI_BASE_URL"):
                provider = f"Local server ({os.getenv('OPENAI_BASE_URL')})"
                requirements = "Requires OPENAI_BASE_URL and local server running"
            else:
                provider = "OpenAI API"
                requirements = "Requires OPENAI_API_KEY"
        
        print(f"  {model}")
        print(f"    → Provider: {provider}")
        print(f"    → Requirements: {requirements}")


def main():
    """Main test function."""
    print("🚀 Multi-Provider OpenAI Configuration Test")
    print("=" * 60)
    
    # Test environment configuration
    is_azure, has_base_url, has_openai_key = test_environment_config()
    
    # Test configuration loading
    config_path = sys.argv[1] if len(sys.argv) > 1 else None
    app_config = test_config_loading(config_path)
    
    # Test model mapping
    test_model_provider_mapping(app_config)
    
    # Provide recommendations
    print(f"\n💡 Recommendations")
    print("=" * 50)
    
    if not (is_azure or has_base_url or has_openai_key):
        print("❌ No providers configured! Please set up at least one provider in your .env file.")
    elif is_azure and has_base_url:
        print("✅ Multi-provider setup detected! You can use both Azure OpenAI and local models.")
        print("   💡 Use azure_openai: prefix for Azure models, openai: prefix for local models.")
    elif is_azure and not has_base_url:
        print("⚠️  Azure-only setup detected. openai: models will auto-convert to azure_openai:.")
        print("   💡 Add OPENAI_BASE_URL to enable local models alongside Azure.")
    elif has_base_url:
        print("✅ Local server setup detected!")
        print("   💡 Make sure your local server (LM Studio, Ollama, etc.) is running.")
    else:
        print("✅ OpenAI API setup detected!")
        print("   💡 Consider adding Azure OpenAI or local models for more flexibility.")
    
    print(f"\n🧪 Next Steps:")
    print("1. Test with a simple query:")
    print("   python -m app.main --agent test_agent 'Hello, test my configuration'")
    print("2. Try the multi-provider example:")
    print("   python -m app.main --config config/multi_provider_example.yaml 'Test query'")
    print("3. Check the documentation: docs/MULTI_PROVIDER_SETUP.md")


if __name__ == "__main__":
    main()
