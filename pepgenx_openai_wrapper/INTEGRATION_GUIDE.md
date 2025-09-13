# PepGenX OpenAI Wrapper - Integration Guide

## 🚀 **Quick Start - Using PepGenX as OpenAI API**

This wrapper allows you to use PepGenX API with any OpenAI-compatible application or library.

## 📋 **Prerequisites**

1. **PepGenX API Access:**
   - PepGenX API URL
   - Project ID and Team ID
   - API Key
   - OKTA Token file

2. **Python Environment:**
   - Python 3.8+
   - Dependencies installed: `pip install -r requirements.txt`

## ⚙️ **Configuration**

### 1. **Environment Setup**

Create `.env` file:
```bash
# PepGenX API Configuration
PEPGENX_API_URL=https://your-pepgenx-api.com/generate
PEPGENX_PROJECT_ID=your-project-id
PEPGENX_TEAM_ID=your-team-id
PEPGENX_API_KEY=your-pepgenx-api-key

# OKTA Authentication
OKTA_TOKEN_FILE=path/to/your/okta_token.json

# Wrapper Configuration
API_KEYS=sk-your-key1,sk-your-key2,sk-your-key3
LOG_LEVEL=INFO
LOG_FORMAT=json
HOST=0.0.0.0
PORT=8000
```

### 2. **OKTA Token File**

Create `okta_token.json`:
```json
{
  "access_token": "your-okta-access-token",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "your-scope"
}
```

## 🏃 **Running the Wrapper**

### **Method 1: Direct Python**
```bash
python start.py
```

### **Method 2: Docker**
```bash
docker build -t pepgenx-wrapper .
docker run -p 8000:8000 --env-file .env pepgenx-wrapper
```

### **Method 3: Docker Compose**
```bash
docker-compose up -d
```

## 🔌 **Integration Examples**

### **1. OpenAI Python Library**

```python
import openai

# Configure client to use your wrapper
client = openai.OpenAI(
    api_key="sk-your-wrapper-key",  # From your API_KEYS config
    base_url="http://localhost:8000/v1"  # Your wrapper URL
)

# Use exactly like OpenAI API
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, world!"}
    ],
    max_tokens=100,
    temperature=0.7
)

print(response.choices[0].message.content)
```

### **2. LangChain Integration**

```python
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

# Use wrapper as OpenAI endpoint
llm = ChatOpenAI(
    openai_api_key="sk-your-wrapper-key",
    openai_api_base="http://localhost:8000/v1",
    model_name="gpt-4"
)

response = llm([HumanMessage(content="Hello, world!")])
print(response.content)
```

### **3. HTTP API Direct**

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-your-wrapper-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "Hello, world!"}
    ],
    "max_tokens": 100
  }'
```

### **4. JavaScript/Node.js**

```javascript
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: 'sk-your-wrapper-key',
  baseURL: 'http://localhost:8000/v1',
});

const response = await openai.chat.completions.create({
  model: 'gpt-4',
  messages: [
    { role: 'user', content: 'Hello, world!' }
  ],
  max_tokens: 100,
});

console.log(response.choices[0].message.content);
```

## 🔍 **Available Endpoints**

### **OpenAI-Compatible Endpoints:**
- `GET /v1/models` - List available models
- `POST /v1/chat/completions` - Chat completions

### **Health & Monitoring:**
- `GET /health/` - Basic health check
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /metrics` - Prometheus metrics
- `GET /docs` - Interactive API documentation

## 🎯 **Supported Models**

The wrapper supports these model names (all map to PepGenX):
- `gpt-4`
- `gpt-4-turbo`
- `gpt-4o`
- `gpt-4o-mini`
- `gpt-3.5-turbo`
- `gpt-5`
- `claude-3-sonnet`
- `claude-3-haiku`
- `claude-3-opus`

## 🔧 **Advanced Configuration**

### **Environment Variables:**
```bash
# Rate Limiting
RATE_LIMIT_PER_MINUTE=100

# CORS
CORS_ORIGINS=*

# Metrics
ENABLE_METRICS=true

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json  # json, text
```

### **Production Deployment:**
```bash
# Use production WSGI server
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 🚨 **Important Notes**

1. **API Keys:** Use strong, unique API keys for the wrapper
2. **OKTA Tokens:** Ensure tokens are refreshed before expiration
3. **Security:** Run behind HTTPS in production
4. **Monitoring:** Monitor health endpoints for service status
5. **Scaling:** Use load balancer for multiple instances

## 🎉 **Success!**

Your PepGenX API is now accessible as an OpenAI-compatible API! Any application that works with OpenAI will now work with PepGenX through this wrapper.
