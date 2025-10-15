#!/bin/bash

# Azure OpenAI Environment Setup Script
# This script helps set up the necessary environment variables for Azure OpenAI

echo "🔧 Setting up Azure OpenAI Environment for Ray-11 Memory Testing"
echo "================================================================"

# Check if environment variables are already set
if [[ -n "$AZURE_OPENAI_ENDPOINT" && -n "$AZURE_OPENAI_API_KEY" ]]; then
    echo "✅ Azure OpenAI credentials already configured:"
    echo "   AZURE_OPENAI_ENDPOINT: $AZURE_OPENAI_ENDPOINT"
    echo "   AZURE_OPENAI_API_KEY: [HIDDEN]"
    echo ""
else
    echo "❌ Azure OpenAI credentials not found in environment"
    echo ""
    echo "Please set the following environment variables:"
    echo "   export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com'"
    echo "   export AZURE_OPENAI_API_KEY='your-api-key'"
    echo ""
    echo "You can also add them to your ~/.zshrc file for persistence:"
    echo "   echo 'export AZURE_OPENAI_ENDPOINT=\"https://your-resource.openai.azure.com\"' >> ~/.zshrc"
    echo "   echo 'export AZURE_OPENAI_API_KEY=\"your-api-key\"' >> ~/.zshrc"
    echo "   source ~/.zshrc"
    echo ""
    echo "After setting the credentials, run this script again to verify."
    exit 1
fi

# Verify DATABASE_URL is set
if [[ -z "$DATABASE_URL" ]]; then
    echo "🔧 Setting DATABASE_URL for memory testing..."
    export DATABASE_URL='postgresql://jkagent_user:securepassword@localhost:5432/conversations'
    echo "   DATABASE_URL: $DATABASE_URL"
else
    echo "✅ DATABASE_URL already set: $DATABASE_URL"
fi

echo ""
echo "🧪 Testing Azure OpenAI connection..."

# Test connection using a simple Python script
python3 << 'EOF'
import os
try:
    from openai import AzureOpenAI
    
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-10-21",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    
    # Test with a simple completion
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Adjust if your deployment name is different
        messages=[{"role": "user", "content": "Say 'Connection test successful'"}],
        max_tokens=10
    )
    
    print(f"✅ Azure OpenAI connection successful!")
    print(f"   Response: {response.choices[0].message.content}")
    
except ImportError:
    print("❌ OpenAI package not found. Installing...")
    os.system("pip install openai")
    print("Please run this script again after installation.")
except Exception as e:
    print(f"❌ Azure OpenAI connection failed: {e}")
    print("   Please check your credentials and endpoint URL")
    exit(1)
EOF

if [[ $? -eq 0 ]]; then
    echo ""
    echo "🎯 Environment is ready for Ray-11 memory testing!"
    echo "   You can now run: python test_ray11_memory.py"
else
    echo ""
    echo "❌ Setup failed. Please check your Azure OpenAI credentials."
fi