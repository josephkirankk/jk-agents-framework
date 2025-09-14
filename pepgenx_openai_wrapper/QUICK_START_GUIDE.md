# PepGenX OpenAI Wrapper - Quick Start Guide

## 🚀 **Get Started in 5 Minutes**

Transform your PepGenX API into an OpenAI-compatible service that works with any OpenAI application.

## 📋 **Prerequisites**

- Python 3.8 or higher
- PepGenX API credentials
- OKTA authentication token

## ⚡ **Quick Setup**

### **Step 1: Install Dependencies**

```bash
cd pepgenx_openai_wrapper
pip install -r requirements.txt
```

### **Step 2: Configure Environment**

Create `.env` file:
```bash
# Copy the example and edit with your credentials
cp .env.example .env
```

Edit `.env` with your actual credentials:
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

# Server Configuration
HOST=127.0.0.1
PORT=8000
LOG_LEVEL=INFO
```

### **Step 3: Create OKTA Token File**

Create `okta_token.json`:
```json
{
  "access_token": "your-okta-access-token",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "your-scope"
}
```

### **Step 4: Start the Wrapper**

```bash
python start.py
```

You should see:
```
🚀 Starting PepGenX OpenAI Wrapper
✅ All dependencies available!
✅ Environment validation passed!
✅ Authentication system ready
🌟 Starting server...
INFO: Uvicorn running on http://127.0.0.1:8000
```

### **Step 5: Test the Wrapper**

```bash
# Test health endpoint
curl http://127.0.0.1:8000/health/

# Test models endpoint
curl -H "Authorization: Bearer sk-wrapper-key1" \
     http://127.0.0.1:8000/v1/models
```

## 🎯 **Usage Examples**

### **Python with OpenAI Library**

```python
import openai

# Configure client to use your wrapper
client = openai.OpenAI(
    api_key="sk-wrapper-key1",  # Your wrapper API key
    base_url="http://127.0.0.1:8000/v1"  # Your wrapper URL
)

# Use exactly like OpenAI API!
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"}
    ],
    max_tokens=100
)

print(response.choices[0].message.content)
```

### **cURL Command**

```bash
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-wrapper-key1" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "Hello, world!"}
    ],
    "max_tokens": 50
  }'
```

## 🔧 **Configuration Options**

### **Environment Variables**

| Variable | Description | Default |
|----------|-------------|---------|
| `PEPGENX_API_URL` | PepGenX API endpoint | Required |
| `PEPGENX_PROJECT_ID` | Your project ID | Required |
| `PEPGENX_TEAM_ID` | Your team ID | Required |
| `PEPGENX_API_KEY` | Your PepGenX API key | Required |
| `OKTA_TOKEN_FILE` | Path to OKTA token file | Required |
| `API_KEYS` | Comma-separated wrapper API keys | Required |
| `HOST` | Server host | `127.0.0.1` |
| `PORT` | Server port | `8000` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FORMAT` | Log format (json/text) | `json` |
| `RATE_LIMIT_PER_MINUTE` | Rate limit per minute | `100` |
| `CORS_ORIGINS` | CORS allowed origins | `*` |

### **Supported Models**

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

## 🏥 **Health Checks**

Monitor your wrapper with these endpoints:

```bash
# Basic health check
curl http://127.0.0.1:8000/health/

# Liveness probe (for Kubernetes)
curl http://127.0.0.1:8000/health/live

# Readiness probe (for Kubernetes)
curl http://127.0.0.1:8000/health/ready

# Prometheus metrics
curl http://127.0.0.1:8000/metrics
```

## 🐳 **Docker Deployment**

### **Build and Run**

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

### **Docker Compose**

```bash
# Start with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## 🔍 **Troubleshooting**

### **Common Issues**

1. **"Environment validation failed"**
   - Check your `.env` file has all required variables
   - Verify OKTA token file exists and is valid

2. **"PepGenX API unavailable"**
   - Verify `PEPGENX_API_URL` is correct
   - Check network connectivity
   - Ensure OKTA token is valid

3. **"Invalid API key"**
   - Use one of the keys from your `API_KEYS` configuration
   - Include `Bearer ` prefix in Authorization header

4. **"Permission denied"**
   - Check OKTA token permissions
   - Verify PepGenX API key has required access

### **Debug Mode**

Enable debug logging:
```bash
LOG_LEVEL=DEBUG python start.py
```

## 📚 **Next Steps**

1. **Integration**: See `INTEGRATION_GUIDE.md` for detailed integration examples
2. **API Reference**: Check `docs/API_DOCUMENTATION.md` for complete API details
3. **Production**: Read `DEPLOYMENT_GUIDE.md` for production deployment
4. **Examples**: Run `examples/reference_usage.py` for comprehensive examples

## 🎉 **You're Ready!**

Your PepGenX API is now accessible as an OpenAI-compatible service. Any application that works with OpenAI will now work with PepGenX through this wrapper!
