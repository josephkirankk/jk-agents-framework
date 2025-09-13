# PepGenX OpenAI Wrapper API Documentation

This document provides comprehensive API documentation for the PepGenX OpenAI Wrapper, including all endpoints, request/response formats, and usage examples.

## Base URL

```
http://localhost:8000
```

## Authentication

All API endpoints (except health checks) require authentication using OpenAI-style API keys in the Authorization header:

```
Authorization: Bearer sk-your-api-key-here
```

## OpenAI-Compatible Endpoints

### Chat Completions

Create a chat completion using the OpenAI-compatible format.

**Endpoint:** `POST /v1/chat/completions`

**Headers:**
- `Authorization: Bearer sk-your-api-key`
- `Content-Type: application/json`

**Request Body:**

```json
{
  "model": "gpt-4",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user", 
      "content": "What is the capital of France?"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 150,
  "top_p": 1.0,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0,
  "stop": null,
  "stream": false
}
```

**Response:**

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1703123456,
  "model": "gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The capital of France is Paris."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 8,
    "total_tokens": 28
  },
  "system_fingerprint": "pepgenx-wrapper-1703123456"
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Model to use (e.g., "gpt-4", "gpt-3.5-turbo") |
| `messages` | array | Yes | Array of message objects |
| `temperature` | number | No | Sampling temperature (0-2) |
| `max_tokens` | integer | No | Maximum tokens to generate |
| `top_p` | number | No | Nucleus sampling parameter (0-1) |
| `frequency_penalty` | number | No | Frequency penalty (-2 to 2) |
| `presence_penalty` | number | No | Presence penalty (-2 to 2) |
| `stop` | string/array | No | Stop sequences |
| `stream` | boolean | No | Stream response (not yet implemented) |

### List Models

Get a list of available models.

**Endpoint:** `GET /v1/models`

**Headers:**
- `Authorization: Bearer sk-your-api-key`

**Response:**

```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-4",
      "object": "model",
      "created": 1677610602,
      "owned_by": "pepgenx-wrapper"
    },
    {
      "id": "gpt-4-turbo",
      "object": "model", 
      "created": 1677610602,
      "owned_by": "pepgenx-wrapper"
    }
  ]
}
```

## Health Check Endpoints

### Basic Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1703123456,
  "version": "1.0.0",
  "service": "pepgenx-openai-wrapper"
}
```

### Readiness Check

**Endpoint:** `GET /health/ready`

**Response:**
```json
{
  "status": "ready",
  "timestamp": 1703123456,
  "checks": {
    "auth": {
      "okta_token_file": "valid",
      "api_keys_configured": "count: 3",
      "token_cache": "active"
    },
    "pepgenx_api": {
      "status": "healthy",
      "response_time_ms": 150.5,
      "api_accessible": true
    },
    "config": {
      "pepgenx_api_url": true,
      "pepgenx_project_id": true,
      "pepgenx_team_id": true,
      "pepgenx_api_key": true,
      "okta_token_file": true,
      "api_keys_count": 3
    }
  }
}
```

### Liveness Check

**Endpoint:** `GET /health/live`

**Response:**
```json
{
  "status": "alive",
  "timestamp": 1703123456
}
```

### Detailed Health Check

**Endpoint:** `GET /health/detailed`

**Headers:**
- `Authorization: Bearer sk-your-api-key`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1703123456,
  "version": "1.0.0",
  "service": "pepgenx-openai-wrapper",
  "details": {
    "system": {
      "log_level": "INFO",
      "log_format": "json",
      "host": "0.0.0.0",
      "port": 8000,
      "metrics_enabled": true,
      "rate_limit_rpm": 60
    },
    "auth": {
      "okta_token_file": "valid",
      "api_keys_configured": "count: 3",
      "token_cache": "active"
    },
    "pepgenx_api": {
      "status": "healthy",
      "response_time_ms": 150.5,
      "api_accessible": true,
      "error": null
    },
    "config": {
      "pepgenx_api_url": "https://api.pepgenx.com/generate",
      "pepgenx_project_id": "proj_abc...",
      "pepgenx_team_id": "team_xyz...",
      "okta_token_file": "/app/okta_token.json",
      "api_keys_configured": 3,
      "cors_origins": ["*"],
      "http_timeout": 30,
      "http_max_retries": 3,
      "cache_ttl": 300
    }
  }
}
```

## Error Responses

All endpoints return OpenAI-compatible error responses:

```json
{
  "error": {
    "message": "Invalid API key",
    "type": "authentication_error",
    "code": "401"
  }
}
```

**Error Types:**
- `invalid_request_error` (400) - Invalid request parameters
- `authentication_error` (401) - Invalid or missing API key
- `permission_error` (403) - Insufficient permissions
- `not_found_error` (404) - Endpoint not found
- `rate_limit_exceeded` (429) - Rate limit exceeded
- `api_error` (500/502/503) - Server or backend errors

## Model Mapping

The wrapper maps OpenAI model names to PepGenX models:

| OpenAI Model | PepGenX Model |
|--------------|---------------|
| `gpt-4` | `gpt-4` |
| `gpt-4-turbo` | `gpt-4-turbo` |
| `gpt-4o` | `gpt-4o` |
| `gpt-4o-mini` | `gpt-4o-mini` |
| `gpt-3.5-turbo` | `gpt-3.5-turbo` |
| `gpt-5` | `gpt-5` |
| `claude-3-sonnet` | `claude-3-sonnet` |
| `claude-3-haiku` | `claude-3-haiku` |
| `claude-3-opus` | `claude-3-opus` |

## Message Roles

Supported message roles in chat completions:

- `system` - System instructions
- `user` - User messages
- `assistant` - Assistant responses
- `developer` - Developer instructions (treated as system)

## Rate Limiting

The API implements rate limiting with the following headers:

- `X-RateLimit-Limit` - Requests per minute limit
- `X-RateLimit-Remaining` - Remaining requests in current window
- `X-RateLimit-Reset` - Unix timestamp when limit resets

## Request/Response Headers

**Request Headers:**
- `Authorization` - Bearer token authentication
- `Content-Type` - Must be `application/json`
- `X-Request-ID` - Optional request correlation ID

**Response Headers:**
- `X-Request-ID` - Request correlation ID
- `X-Powered-By` - Service identifier
- `X-Response-Time` - Response time in milliseconds
- `X-RateLimit-*` - Rate limiting information

## Usage Examples

### Python with OpenAI Library

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-your-api-key-here",
    base_url="http://localhost:8000/v1"
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

### cURL

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Authorization: Bearer sk-your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

### JavaScript/Node.js

```javascript
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: 'sk-your-api-key-here',
  baseURL: 'http://localhost:8000/v1'
});

const response = await openai.chat.completions.create({
  model: 'gpt-4',
  messages: [
    { role: 'user', content: 'Hello!' }
  ]
});

console.log(response.choices[0].message.content);
```

## Monitoring and Metrics

### Metrics Endpoint

**Endpoint:** `GET /metrics`

Returns Prometheus-formatted metrics:

```
# HELP pepgenx_wrapper_requests_total Total number of requests
# TYPE pepgenx_wrapper_requests_total counter
pepgenx_wrapper_requests_total 42

# HELP pepgenx_wrapper_request_duration_seconds Request duration
# TYPE pepgenx_wrapper_request_duration_seconds histogram
pepgenx_wrapper_request_duration_seconds_bucket{le="0.1"} 10
pepgenx_wrapper_request_duration_seconds_bucket{le="0.5"} 35
pepgenx_wrapper_request_duration_seconds_bucket{le="1.0"} 40
pepgenx_wrapper_request_duration_seconds_bucket{le="+Inf"} 42
```

### Basic Metrics

**Endpoint:** `GET /health/metrics`

**Response:**
```json
{
  "timestamp": 1703123456,
  "uptime_seconds": 3600,
  "requests_total": 42,
  "requests_errors": 2,
  "response_time_avg": 0.25,
  "pepgenx_api_calls": 40,
  "active_connections": 5
}
```

## WebSocket Support

WebSocket support for streaming responses is planned for future releases.

## Limitations

- Streaming responses not yet implemented
- Function calling not yet supported
- Image inputs not yet supported
- Audio inputs/outputs not yet supported

## Support

For API support:
- Check `/health/detailed` for system status
- Review application logs
- Consult the interactive documentation at `/docs`
