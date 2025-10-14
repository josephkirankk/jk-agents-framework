#!/usr/bin/env python3
"""
Quick test to verify Azure OpenAI configuration
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

print("🧪 Quick Azure OpenAI Configuration Test")
print("=" * 50)

# Try to load .env first, then .env.example as fallback
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    print("📄 Loading environment variables from .env")
    load_dotenv(env_file)
else:
    env_example_file = Path(__file__).parent / '.env.example'
    if env_example_file.exists():
        print("📄 Loading environment variables from .env.example")
        load_dotenv(env_example_file)
        # Check if API key needs to be set
        if os.getenv('AZURE_OPENAI_API_KEY') == 'xxx':
            print("⚠️  Warning: AZURE_OPENAI_API_KEY is set to placeholder 'xxx'")
            print("   You need to set the actual API key as an environment variable")
            print("   or in a .env file (which is gitignored)")
    else:
        print("❌ No .env or .env.example file found")

# Check environment variables
azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
azure_deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT') 
azure_api_key = os.getenv('AZURE_OPENAI_API_KEY')
azure_api_version = os.getenv('AZURE_OPENAI_API_VERSION')

print(f"\n📋 Azure OpenAI Configuration:")
print(f"   AZURE_OPENAI_ENDPOINT: {azure_endpoint}")
print(f"   AZURE_OPENAI_DEPLOYMENT: {azure_deployment}")
print(f"   AZURE_OPENAI_API_KEY: {'[SET]' if azure_api_key and azure_api_key != 'xxx' else '[NOT SET]'}")
print(f"   AZURE_OPENAI_API_VERSION: {azure_api_version}")

if azure_api_key and azure_api_key != 'xxx':
    print("\n✅ Azure OpenAI configuration appears complete!")
    
    # Test the agent creation
    try:
        sys.path.append(os.path.dirname(__file__))
        from app.agent_builder import create_react_agent
        
        print("\n🤖 Testing agent creation with Azure OpenAI...")
        
        # Simple test config
        config = {
            'models': {
                'default': 'azure_openai:gpt-4.1'
            },
            'agents': [{
                'name': 'test_agent',
                'model': 'azure_openai:gpt-4.1',
                'prompt': 'You are a test agent.',
                'description': 'Simple test agent'
            }]
        }
        
        # Try to create the agent
        agent = create_react_agent(
            config=config,
            agent_name='test_agent'
        )
        
        print("✅ Agent created successfully with Azure OpenAI!")
        print("   Your configuration is working correctly.")
        
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        print("   This might indicate an issue with the API key or configuration")
        
else:
    print("\n❌ Azure OpenAI configuration incomplete!")
    print("\n🔧 To fix this issue:")
    print("1. Set the API key as an environment variable:")
    print("   export AZURE_OPENAI_API_KEY='your-actual-api-key'")
    print("\n2. Or create a .env file (gitignored) with:")
    print("   AZURE_OPENAI_ENDPOINT=https://pep-aisp-hackathon.openai.azure.com/")
    print("   AZURE_OPENAI_DEPLOYMENT=gpt-4.1")
    print("   AZURE_OPENAI_API_KEY=your-actual-api-key")
    print("   AZURE_OPENAI_API_VERSION=2023-05-15")
    print("\n3. Then run the test again:")
    print("   python test_advanced_memory_agent.py")

print("\n🎯 Test complete!")
