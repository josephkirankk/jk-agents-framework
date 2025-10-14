#!/usr/bin/env python3
"""
Test Azure OpenAI connection directly
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test environment variables
print("=== Environment Variables ===")
print(f"AZURE_OPENAI_ENDPOINT: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
print(f"AZURE_OPENAI_DEPLOYMENT: {os.getenv('AZURE_OPENAI_DEPLOYMENT')}")
print(f"AZURE_OPENAI_API_VERSION: {os.getenv('AZURE_OPENAI_API_VERSION')}")
print(f"AZURE_OPENAI_API_KEY length: {len(os.getenv('AZURE_OPENAI_API_KEY', ''))}")

# Test Azure OpenAI connection
try:
    from langchain_openai import AzureChatOpenAI
    
    print("\n=== Testing Azure OpenAI Connection ===")
    
    llm = AzureChatOpenAI(
        azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
        azure_deployment=os.getenv('AZURE_OPENAI_DEPLOYMENT'),
        api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
        api_key=os.getenv('AZURE_OPENAI_API_KEY'),
        temperature=0.1
    )
    
    print("✓ Azure OpenAI client created successfully")
    
    # Test a simple call
    response = llm.invoke("Say 'Hello World' in exactly 2 words.")
    print(f"✓ Azure OpenAI response: {response.content}")
    
except Exception as e:
    print(f"✗ Azure OpenAI connection failed: {e}")
    print(f"Error type: {type(e)}")
    
    # Additional debugging
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()
