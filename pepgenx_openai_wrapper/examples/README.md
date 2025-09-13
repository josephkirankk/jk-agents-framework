# PepGenX OpenAI Wrapper - Usage Examples

This directory contains comprehensive examples showing how to use the PepGenX OpenAI Wrapper in various scenarios.

## 📁 **Available Examples**

### **1. `simple_usage.py` - Basic Usage**
**Perfect for beginners!**

A minimal example showing the most basic usage of the wrapper as a drop-in OpenAI replacement.

```bash
python examples/simple_usage.py
```

**What it demonstrates:**
- Basic client setup
- Listing models
- Simple chat completion
- System message usage

### **2. `reference_usage.py` - Comprehensive Demo**
**Complete feature showcase!**

A comprehensive demonstration of all wrapper features and capabilities.

```bash
python examples/reference_usage.py
```

**What it demonstrates:**
- Health check endpoints
- All OpenAI API features
- Different models and parameters
- Error handling scenarios
- Authentication testing
- Performance testing
- Direct HTTP API calls

### **3. `langchain_integration.py` - LangChain Integration**
**Framework compatibility!**

Shows how to use the wrapper with LangChain, proving it works with popular AI frameworks.

```bash
# Install LangChain first
pip install langchain langchain-openai

python examples/langchain_integration.py
```

**What it demonstrates:**
- Basic LangChain chat
- System messages with LangChain
- Multi-turn conversations
- Prompt templates
- Different models with LangChain

## 🚀 **Quick Start**

1. **Start the wrapper server:**
   ```bash
   cd pepgenx_openai_wrapper
   python start.py
   ```

2. **Run any example:**
   ```bash
   # Start with the simple example
   python examples/simple_usage.py
   
   # Or try the comprehensive demo
   python examples/reference_usage.py
   ```

## 🔧 **Configuration**

All examples use these default settings:
- **Wrapper URL**: `http://127.0.0.1:8000`
- **API Key**: `sk-test-key1`

You can override these with environment variables:
```bash
export WRAPPER_URL="http://your-wrapper-host:8000"
export WRAPPER_API_KEY="your-api-key"
python examples/simple_usage.py
```

## 📋 **Prerequisites**

### **Basic Examples:**
```bash
pip install openai httpx
```

### **LangChain Example:**
```bash
pip install openai httpx langchain langchain-openai
```

### **All Dependencies:**
```bash
pip install -r requirements.txt
pip install langchain langchain-openai
```

## 🎯 **Usage Patterns**

### **Pattern 1: Direct OpenAI Library Usage**
```python
import openai
from openai import OpenAI

client = OpenAI(
    api_key="sk-test-key1",
    base_url="http://127.0.0.1:8000/v1"
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### **Pattern 2: LangChain Integration**
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    openai_api_key="sk-test-key1",
    openai_api_base="http://127.0.0.1:8000/v1",
    model_name="gpt-4"
)

response = llm([HumanMessage(content="Hello!")])
```

### **Pattern 3: Direct HTTP API**
```bash
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-test-key1" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4", "messages": [{"role": "user", "content": "Hello!"}]}'
```

## 🔍 **Troubleshooting**

### **Common Issues:**

1. **"Connection refused"**
   - Make sure the wrapper server is running: `python start.py`
   - Check the server is accessible at the configured URL

2. **"Invalid API key"**
   - Verify your API key matches one in your `.env` file
   - Check the `API_KEYS` configuration in your environment

3. **"PepGenX API unavailable"**
   - This is expected with test configuration
   - Configure real PepGenX API credentials for actual usage

4. **Import errors**
   - Install required dependencies: `pip install openai httpx`
   - For LangChain: `pip install langchain langchain-openai`

### **Debug Mode:**

Run examples with debug output:
```bash
export LOG_LEVEL=DEBUG
python examples/reference_usage.py
```

## 📚 **Next Steps**

1. **Start Simple**: Run `simple_usage.py` to verify basic functionality
2. **Explore Features**: Run `reference_usage.py` to see all capabilities
3. **Framework Integration**: Try `langchain_integration.py` for framework usage
4. **Build Your App**: Use these patterns in your own applications

## 🎉 **Success Indicators**

When examples run successfully, you should see:
- ✅ Health checks passing
- ✅ Models listed correctly
- ✅ Chat completions working
- ✅ Different models responding
- ✅ Error handling working properly

This confirms your PepGenX API is successfully wrapped and ready for use with any OpenAI-compatible application!
