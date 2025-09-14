# Custom OpenAI Endpoint Integration with JK-Agents

This document describes how to integrate custom OpenAI-compatible services (like PepGenX, LM Studio, or other OpenAI-compatible APIs) with the JK-Agents framework.

## Overview

The custom endpoint integration allows you to use any OpenAI-compatible service alongside standard providers (OpenAI, Azure OpenAI, Google Gemini, Anthropic) in your JK-Agents configurations. The integration is completely decoupled - your custom service runs separately and JK-Agents connects to it using the standard OpenAI client.

## Architecture

```
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│   JK-Agents     │    │  Custom OpenAI       │    │   Backend API   │
│   Framework     │───▶│  Compatible Service  │───▶│   (Optional)    │
│                 │    │  (Port 8080)         │    │                 │
└─────────────────┘    └──────────────────────┘    └─────────────────┘
```

- **JK-Agents Framework**: Uses standard OpenAI client to connect to custom service
- **Custom OpenAI Service**: Any OpenAI-compatible API (PepGenX wrapper, LM Studio, etc.)
- **Backend API**: Optional backend service (e.g., PepGenX API, local models, etc.)

## Setup Instructions

### 1. Configure Your Custom Service

Set up your OpenAI-compatible service (examples):

**For PepGenX Wrapper:**
```bash
cd pepgenx_openai_wrapper
cp .env.example .env
# Edit .env with your PepGenX API credentials
# Create okta_token.json with your OKTA token
```

**For LM Studio:**
```bash
# Start LM Studio server on port 1234
# Load your preferred model
```

**For Other Services:**
```bash
# Follow your service's setup instructions
# Ensure it provides OpenAI-compatible endpoints
```

### 2. Set Environment Variables

Configure JK-Agents to use your custom endpoint:

```bash
# Point OpenAI client to your custom service
export OPENAI_BASE_URL="http://127.0.0.1:8080/v1"
export OPENAI_API_KEY="sk-test-key1"
```

### 3. Configure Agents

Use standard `openai:` prefix in your YAML configuration:

```yaml
models:
  default: "openai:gpt-4"
  supervisor: "openai:claude-3-sonnet"

agents:
  - name: "custom_assistant"
    model: "openai:gpt-4"
    prompt: "You are a helpful assistant."
```

## Quick Start

### Option 1: Automated Startup

Use the provided startup script:

```bash
python scripts/start_with_custom_endpoint.py \
  --service-dir pepgenx_openai_wrapper \
  --service-port 8080 \
  --api-port 8001
```

### Option 2: Manual Startup

Start services manually:

```bash
# Terminal 1: Start your custom service
cd your_custom_service
python start.py

# Terminal 2: Set environment and start JK-Agents
export OPENAI_BASE_URL="http://127.0.0.1:8080/v1"
export OPENAI_API_KEY="sk-test-key1"
uvicorn app.api:app --host 0.0.0.0 --port 8001 --reload
```

## Testing the Integration

Run the integration test suite:

```bash
python scripts/test_custom_endpoint_integration.py
```

## Usage Examples

### Basic Agent Query

```bash
curl -X POST "http://localhost:8001/worker" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "custom_assistant",
    "input": "Explain quantum computing",
    "config_path": "config/openai_custom_endpoint.yaml"
  }'
```

### Python Integration

```python
import requests

response = requests.post("http://localhost:8001/worker", json={
    "agent_name": "custom_assistant",
    "input": "What are the benefits of AI?",
    "config_path": "config/openai_custom_endpoint.yaml"
})

result = response.json()
print(result["response"])
```

## Configuration Examples

### Mixed Provider Setup

```yaml
models:
  # Custom endpoint (will use OPENAI_BASE_URL if set)
  default: "openai:gpt-4"
  supervisor: "openai:claude-3-sonnet"
  
  # Standard providers as fallbacks
  azure_fallback: "azure_openai:gpt-4.1"
  google_fallback: "google:gemini-2.0-flash-exp"

agents:
  - name: "custom_primary"
    model: "openai:gpt-4"  # Uses custom endpoint
    
  - name: "azure_fallback"
    model: "azure_openai:gpt-4.1"  # Uses Azure
```

## Supported Custom Services

### PepGenX OpenAI Wrapper
- **Setup**: Configure `.env` and `okta_token.json`
- **Models**: gpt-4, claude-3-sonnet, gemini-pro, etc.
- **Port**: Default 8080

### LM Studio
- **Setup**: Start LM Studio server
- **Models**: Any loaded local model
- **Port**: Default 1234
- **Base URL**: `http://127.0.0.1:1234/v1`

### Other OpenAI-Compatible Services
- **Ollama**: Local model serving
- **Text Generation WebUI**: Local model interface
- **Custom Wrappers**: Any service implementing OpenAI API spec

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure custom service is running on correct port
   - Check `OPENAI_BASE_URL` environment variable

2. **Authentication Errors**
   - Verify `OPENAI_API_KEY` matches service configuration
   - Check service authentication requirements

3. **Model Not Found**
   - Verify model name is supported by your service
   - Check service's `/v1/models` endpoint

### Debug Commands

```bash
# Check service health
curl http://localhost:8080/health

# List available models
curl -H "Authorization: Bearer sk-test-key1" \
     http://localhost:8080/v1/models

# Test chat completion
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer sk-test-key1" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4", "messages": [{"role": "user", "content": "Hello"}]}'
```

## Benefits

- **Zero Code Changes**: JK-Agents requires no modifications
- **Standard Interface**: Uses familiar OpenAI API patterns
- **Provider Flexibility**: Switch between services easily
- **Fallback Support**: Mix custom and standard providers
- **Complete Decoupling**: Services run independently

## Security Notes

- Custom service handles its own authentication
- JK-Agents only needs the service API key
- Network traffic is HTTP by default (use HTTPS in production)
- Credentials stay within each service's configuration

## Next Steps

1. **Production**: Configure HTTPS and proper authentication
2. **Monitoring**: Set up logging and health checks
3. **Scaling**: Consider load balancing for high traffic
4. **Custom Models**: Add new model mappings as needed
