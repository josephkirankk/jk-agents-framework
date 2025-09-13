#!/usr/bin/env python3
"""
Minimal test to isolate the API issue.
"""

import asyncio
import sys
import traceback
from pathlib import Path

sys.path.append('.')

from app.main import load_app_config

async def test_config_loading():
    """Test just the configuration loading."""
    print("=== Testing Configuration Loading ===")
    
    try:
        # Test configuration loading
        config_path = Path("config/pep_mcp_sample.yaml")
        print(f"Loading config from: {config_path}")
        app_cfg = load_app_config(config_path)
        print("✓ Configuration loaded successfully")
        
        # Check the model configuration
        default_model = app_cfg.models.get("default", "unknown")
        print(f"Default model: {default_model}")
        
        # Find the restaurants_agent
        target = next((a for a in app_cfg.agents if a.name == "restaurants_agent"), None)
        if target:
            print(f"✓ Found restaurants_agent")
            print(f"  Model: {target.model or default_model}")
            print(f"  MCP servers: {list(target.mcp_servers.keys())}")
        else:
            print("✗ restaurants_agent not found")
            
        return app_cfg
        
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        traceback.print_exc()
        return None

async def test_model_creation():
    """Test model creation in isolation."""
    print("\n=== Testing Model Creation ===")
    
    try:
        from app.agent_builder import create_model_instance
        
        model_id = "azure_openai:gpt-4.1"
        print(f"Testing model creation for: {model_id}")
        
        model_instance = create_model_instance(model_id)
        print(f"✓ Model instance created: {model_instance} (type: {type(model_instance)})")
        
        # Test if it's a string (should be for azure_openai)
        if isinstance(model_instance, str):
            print(f"✓ Model instance is a string: {model_instance}")
        else:
            print(f"✓ Model instance is an object: {type(model_instance)}")
            
        return model_instance
        
    except Exception as e:
        print(f"✗ Model creation failed: {e}")
        traceback.print_exc()
        return None

async def test_init_chat_model():
    """Test init_chat_model function."""
    print("\n=== Testing init_chat_model ===")
    
    try:
        from langchain.chat_models import init_chat_model
        
        model_id = "azure_openai:gpt-4.1"
        print(f"Testing init_chat_model with: {model_id}")
        
        actual_model = init_chat_model(model_id)
        print(f"✓ init_chat_model succeeded: {actual_model} (type: {type(actual_model)})")
        
        # Test if we can access attributes
        print(f"Model attributes: {dir(actual_model)[:5]}...")  # First 5 attributes
        
        return actual_model
        
    except Exception as e:
        print(f"✗ init_chat_model failed: {e}")
        traceback.print_exc()
        return None

async def main():
    """Run all tests."""
    print("=== Minimal API Issue Isolation Test ===\n")
    
    # Test 1: Configuration loading
    app_cfg = await test_config_loading()
    if not app_cfg:
        return
    
    # Test 2: Model creation
    model_instance = await test_model_creation()
    if model_instance is None:
        return
    
    # Test 3: init_chat_model
    actual_model = await test_init_chat_model()
    if actual_model is None:
        return
    
    print("\n✓ All tests passed! The issue might be elsewhere.")

if __name__ == "__main__":
    asyncio.run(main())
