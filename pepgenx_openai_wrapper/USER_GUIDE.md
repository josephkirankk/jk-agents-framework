# PepGenX OpenAI Wrapper - Complete User Guide

## 🎯 **What is This?**

The PepGenX OpenAI Wrapper transforms your PepGenX API into an OpenAI-compatible service. This means **any application that works with OpenAI will now work with PepGenX** - without changing a single line of code!

## ⚡ **Quick Start (5 Minutes)**

### **Step 1: Setup**
```bash
cd pepgenx_openai_wrapper
pip install -r requirements.txt
cp .env.example .env
```

### **Step 2: Configure**
Edit `.env` with your credentials:
```bash
# PepGenX API Configuration
PEPGENX_API_URL=https://your-pepgenx-api.com/generate
PEPGENX_PROJECT_ID=your-project-id
PEPGENX_TEAM_ID=your-team-id
PEPGENX_API_KEY=your-pepgenx-api-key

# OKTA Authentication
OKTA_TOKEN_FILE=okta_token.json

# Wrapper API Keys (comma-separated)
API_KEYS=sk-wrapper-key1,sk-wrapper-key2,sk-wrapper-key3
```

Create `okta_token.json`:
```json
{
  "access_token": "your-okta-access-token",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### **Step 3: Start Server**
```bash
python start.py
```

### **Step 4: Use Like OpenAI**
```python
import openai
from openai import OpenAI

client = OpenAI(
    api_key="sk-wrapper-key1",  # From your .env
    base_url="http://127.0.0.1:8000/v1"
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

**🎉 Done! Your PepGenX API now works exactly like OpenAI!**

## 🔧 **Configuration Reference**

### **Required Environment Variables**
```bash
PEPGENX_API_URL=https://your-pepgenx-api.com/generate
PEPGENX_PROJECT_ID=your-project-id
PEPGENX_TEAM_ID=your-team-id
PEPGENX_API_KEY=your-pepgenx-api-key
OKTA_TOKEN_FILE=okta_token.json
API_KEYS=sk-key1,sk-key2,sk-key3
```

### **Optional Settings**
```bash
HOST=127.0.0.1              # Server host
PORT=8000                   # Server port
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json             # json or text
RATE_LIMIT_PER_MINUTE=100   # Rate limiting
CORS_ORIGINS=*              # CORS settings
ENABLE_METRICS=true         # Prometheus metrics
```

### **OKTA Token File Format**
```json
{
  "access_token": "your-okta-access-token",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "your-scope"
}
```

## 🎯 **Usage Examples**

### **1. Basic OpenAI Library Usage**
```python
import openai
from openai import OpenAI

client = OpenAI(
    api_key="sk-wrapper-key1",
    base_url="http://127.0.0.1:8000/v1"
)

# Simple chat
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "What is Python?"}
    ],
    max_tokens=100
)

print(response.choices[0].message.content)
```

### **2. With System Messages**
```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "Write a Python hello world program."}
    ],
    max_tokens=150,
    temperature=0.7
)
```

### **3. Multi-turn Conversation**
```python
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "My name is Alice."},
    {"role": "assistant", "content": "Hello Alice! Nice to meet you."},
    {"role": "user", "content": "What's my name?"}
]

response = client.chat.completions.create(
    model="gpt-4",
    messages=messages
)
```

### **4. LangChain Integration**
```python
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

llm = ChatOpenAI(
    openai_api_key="sk-wrapper-key1",
    openai_api_base="http://127.0.0.1:8000/v1",
    model_name="gpt-4"
)

response = llm([HumanMessage(content="Hello from LangChain!")])
print(response.content)
```

### **5. Direct HTTP API**
```bash
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-wrapper-key1" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "Hello via HTTP!"}
    ],
    "max_tokens": 50
  }'
```

### **6. JavaScript/Node.js**
```javascript
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: 'sk-wrapper-key1',
  baseURL: 'http://127.0.0.1:8000/v1',
});

const response = await openai.chat.completions.create({
  model: 'gpt-4',
  messages: [{ role: 'user', content: 'Hello from JavaScript!' }],
});

console.log(response.choices[0].message.content);
```

## 🤖 **Supported Models**

All these model names work with the wrapper:
- `gpt-4`
- `gpt-4-turbo`
- `gpt-4o`
- `gpt-4o-mini`
- `gpt-3.5-turbo`
- `gpt-5`
- `claude-3-sonnet`
- `claude-3-haiku`
- `claude-3-opus`

## 🏥 **Health & Monitoring**

### **Health Check Endpoints**
```bash
# Basic health
curl http://127.0.0.1:8000/health/

# Kubernetes liveness probe
curl http://127.0.0.1:8000/health/live

# Kubernetes readiness probe
curl http://127.0.0.1:8000/health/ready

# Prometheus metrics
curl http://127.0.0.1:8000/metrics

# Interactive API docs
open http://127.0.0.1:8000/docs
```

### **Example Health Response**
```json
{
  "status": "healthy",
  "timestamp": 1234567890,
  "version": "1.0.0",
  "service": "pepgenx-openai-wrapper"
}
```

## 🐳 **Docker Deployment**

### **Docker Compose (Recommended)**
```bash
# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop service
docker-compose down
```

### **Direct Docker**
```bash
# Build image
docker build -t pepgenx-wrapper .

# Run container
docker run -d \
  --name pepgenx-wrapper \
  -p 8000:8000 \
  --env-file .env \
  pepgenx-wrapper
```

### **Production Deployment**
```bash
# Use production WSGI server
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 🧪 **Testing & Validation**

### **Run Examples**
```bash
# Basic usage example
python examples/simple_usage.py

# Comprehensive feature demo
python examples/reference_usage.py

# LangChain integration test
python examples/langchain_integration.py
```

### **Run Test Suite**
```bash
python test_wrapper.py --url http://127.0.0.1:8000 --api-key sk-wrapper-key1
```

### **Manual Testing**
```bash
# Test health
curl http://127.0.0.1:8000/health/

# Test models
curl -H "Authorization: Bearer sk-wrapper-key1" \
     http://127.0.0.1:8000/v1/models

# Test chat completion
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-wrapper-key1" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4", "messages": [{"role": "user", "content": "Test"}]}'
```

## 🔍 **Troubleshooting**

### **Common Issues & Solutions**

1. **"Connection refused"**
   ```bash
   # Make sure server is running
   python start.py
   ```

2. **"Invalid API key"**
   ```bash
   # Check API key matches .env configuration
   # Use one of the keys from API_KEYS
   ```

3. **"Environment validation failed"**
   ```bash
   # Check all required variables in .env
   # Verify OKTA token file exists
   ```

4. **"PepGenX API unavailable"**
   ```bash
   # This is expected with test configuration
   # Configure real PepGenX credentials for production
   ```

5. **Import errors**
   ```bash
   pip install -r requirements.txt
   pip install openai  # For examples
   ```

### **Debug Mode**
```bash
LOG_LEVEL=DEBUG python start.py
```

### **Check Configuration**
```bash
python -c "
from app.core.config import settings
print('PepGenX URL:', settings.pepgenx_api_url)
print('API Keys:', len(settings.api_keys_list))
print('OKTA Token File:', settings.okta_token_file)
"
```

## 📚 **Additional Resources**

- **[Quick Start Guide](QUICK_START_GUIDE.md)** - 5-minute setup
- **[Integration Guide](INTEGRATION_GUIDE.md)** - Detailed integration examples
- **[Examples Directory](examples/)** - Code examples and patterns
- **[API Documentation](docs/API_DOCUMENTATION.md)** - Complete API reference
- **[Testing Results](TESTING_RESULTS.md)** - Comprehensive test results

## 🎉 **Success!**

Once everything is working, you'll have:
- ✅ PepGenX API accessible via OpenAI format
- ✅ Any OpenAI app works with PepGenX
- ✅ Production-ready with monitoring
- ✅ Enterprise security and authentication
- ✅ Framework compatibility (LangChain, etc.)

**Your PepGenX API is now a drop-in replacement for OpenAI!** 🚀
