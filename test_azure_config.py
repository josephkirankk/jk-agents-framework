#!/usr/bin/env python3
"""
Quick Azure OpenAI configuration test script
This script loads environment variables from .env.example and tests Azure OpenAI connectivity
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env.example
env_file = Path(__file__).parent / '.env.example'
if env_file.exists():
    print(f"📄 Loading environment variables from {env_file}")
    load_dotenv(env_file)
    print("✅ Environment variables loaded")
else:
    print("❌ .env.example file not found")
    sys.exit(1)

# Check Azure OpenAI configuration
azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
azure_deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT')
azure_api_key = os.getenv('AZURE_OPENAI_API_KEY')
azure_api_version = os.getenv('AZURE_OPENAI_API_VERSION')

print("\n🔍 Azure OpenAI Configuration Check:")
print(f"   AZURE_OPENAI_ENDPOINT: {azure_endpoint}")
print(f"   AZURE_OPENAI_DEPLOYMENT: {azure_deployment}")
print(f"   AZURE_OPENAI_API_KEY: {'[SET]' if azure_api_key and azure_api_key != 'xxx' else '[NOT SET]'}")
print(f"   AZURE_OPENAI_API_VERSION: {azure_api_version}")

if not azure_endpoint or not azure_deployment or not azure_api_key or azure_api_key == 'xxx':
    print("\n❌ Azure OpenAI configuration incomplete!")
    print("   The API key in .env.example is set to 'xxx' - you need to provide the actual API key")
    print("\n🔧 To fix this, you can either:")
    print("   1. Set environment variables in your shell:")
    print(f'      export AZURE_OPENAI_API_KEY="your-actual-api-key"')
    print("   2. Or create a .env file with the actual credentials")
    print("\n💡 For security, never commit real API keys to git!")
    sys.exit(1)

print("\n✅ Azure OpenAI configuration looks complete!")

# Test connectivity (optional - requires actual API key)
if azure_api_key and azure_api_key != 'xxx':
    try:
        from openai import AzureOpenAI
        
        print("\n🧪 Testing Azure OpenAI connection...")
        client = AzureOpenAI(
            api_key=azure_api_key,
            api_version=azure_api_version,
            azure_endpoint=azure_endpoint
        )
        
        # Simple test
        response = client.chat.completions.create(
            model=azure_deployment,
            messages=[{"role": "user", "content": "Say 'Hello from Azure OpenAI!'"}],
            max_tokens=20
        )
        
        print(f"✅ Connection successful!")
        print(f"   Response: {response.choices[0].message.content}")
        
    except ImportError:
        print("⚠️  OpenAI package not installed, skipping connection test")
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        print("   This might be due to invalid API key or network issues")

print("\n🎯 Configuration check complete!")
