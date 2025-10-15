#!/usr/bin/env python3
"""
Test for environment variable conflicts
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=== Current Environment Configuration ===")
print(f"AZURE_OPENAI_ENDPOINT: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
print(f"AZURE_OPENAI_DEPLOYMENT: {os.getenv('AZURE_OPENAI_DEPLOYMENT')}")
print(f"AZURE_OPENAI_API_KEY: {'SET' if os.getenv('AZURE_OPENAI_API_KEY') else 'NOT SET'}")
print(f"OPENAI_BASE_URL: {os.getenv('OPENAI_BASE_URL')}")
print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY')}")

print("\n=== Potential Conflict Analysis ===")
if os.getenv('OPENAI_BASE_URL') and os.getenv('AZURE_OPENAI_ENDPOINT'):
    print("⚠️  CONFLICT DETECTED: Both OPENAI_BASE_URL and Azure OpenAI are configured")
    print("   This may cause the framework to use LM Studio instead of Azure OpenAI")
    print("   for models prefixed with 'openai:'")
else:
    print("✓ No obvious conflicts detected")

# Test what happens when we create different model types
try:
    from langchain_openai import ChatOpenAI, AzureChatOpenAI
    
    print("\n=== Testing Model Creation ===")
    
    # Test Azure OpenAI (should work)
    azure_llm = AzureChatOpenAI(
        azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
        azure_deployment=os.getenv('AZURE_OPENAI_DEPLOYMENT'),
        api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
        api_key=os.getenv('AZURE_OPENAI_API_KEY'),
        temperature=0.1
    )
    print("✓ AzureChatOpenAI created successfully")
    
    # Test regular OpenAI (might use LM Studio due to OPENAI_BASE_URL)
    if os.getenv('OPENAI_BASE_URL'):
        print(f"⚠️  OPENAI_BASE_URL is set to: {os.getenv('OPENAI_BASE_URL')}")
        print("   This will redirect openai: models to LM Studio")
        
        # Test if LM Studio is running
        import requests
        try:
            response = requests.get(f"{os.getenv('OPENAI_BASE_URL')}/models", timeout=2)
            print("✓ LM Studio is responding")
        except Exception as e:
            print(f"✗ LM Studio is NOT responding: {e}")
            print("   This could cause connection failures for openai: models")
    
except Exception as e:
    print(f"✗ Model creation failed: {e}")
