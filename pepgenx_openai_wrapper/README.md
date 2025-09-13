# PepGenX OpenAI Wrapper

A production-ready FastAPI wrapper that provides OpenAI-compatible API endpoints for the PepGenX AI platform, enabling seamless integration with existing OpenAI-based applications.

## Features

- **OpenAI API Compatibility**: Full compatibility with OpenAI Chat Completions API
- **Production Ready**: Comprehensive logging, monitoring, error handling, and security
- **Authentication**: Support for multiple API keys and OKTA token management
- **Docker Support**: Complete containerization with Docker and Docker Compose
- **Health Checks**: Comprehensive health and readiness endpoints
- **Monitoring**: Prometheus metrics and observability
- **CORS Support**: Configurable CORS for web applications
- **Rate Limiting**: Built-in rate limiting capabilities
- **Async/Await**: High-performance async implementation

## Quick Start

### Prerequisites

- Python 3.11+
- PepGenX API access credentials
- OKTA token file

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd pepgenx_openai_wrapper
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Create OKTA token file**:
   ```json
   {
     "access_token": "your-okta-access-token",
     "expires_in": 3600
   }
   ```

5. **Run the application**:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

### Docker Deployment

1. **Using Docker Compose** (Recommended):
   ```bash
   # Copy and configure environment
   cp .env.example .env
   # Edit .env with your settings
   
   # Start the service
   docker-compose up -d
   
   # View logs
   docker-compose logs -f pepgenx-wrapper
   ```

2. **Using Docker directly**:
   ```bash
   # Build the image
   docker build -t pepgenx-openai-wrapper .
   
   # Run the container
   docker run -d \
     --name pepgenx-wrapper \
     -p 8000:8000 \
     -v ./okta_token.json:/app/okta_token.json:ro \
     -v ./.env:/app/.env:ro \
     pepgenx-openai-wrapper
   ```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PEPGENX_API_URL` | PepGenX API endpoint URL | - | Yes |
| `PEPGENX_PROJECT_ID` | PepGenX project ID | - | Yes |
| `PEPGENX_TEAM_ID` | PepGenX team ID | - | Yes |
| `PEPGENX_API_KEY` | PepGenX API key | - | Yes |
| `OKTA_TOKEN_FILE` | Path to OKTA token JSON file | `okta_token.json` | Yes |
| `OPENAI_WRAPPER_API_KEYS` | Comma-separated API keys for clients | - | Yes |
| `OPENAI_WRAPPER_HOST` | Host to bind to | `0.0.0.0` | No |
| `OPENAI_WRAPPER_PORT` | Port to bind to | `8000` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `LOG_FORMAT` | Log format (json/text) | `json` | No |
| `CORS_ORIGINS` | CORS allowed origins | `*` | No |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | Rate limit per minute | `60` | No |
| `SECRET_KEY` | Secret key for JWT signing | - | Yes |

### OKTA Token File Format

```json
{
  "access_token": "your-okta-access-token-here",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

## API Usage

### OpenAI-Compatible Endpoints

The wrapper provides the following OpenAI-compatible endpoints:

- `POST /v1/chat/completions` - Create chat completion
- `GET /v1/models` - List available models

### Authentication

Use OpenAI-style API keys in the Authorization header:

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Authorization: Bearer sk-your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ]
  }'
```

### Example Usage with OpenAI Python Library

```python
from openai import OpenAI

# Configure client to use the wrapper
client = OpenAI(
    api_key="sk-your-api-key-here",
    base_url="http://localhost:8000/v1"
)

# Use exactly like OpenAI API
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

### Supported Models

The wrapper supports the following model mappings:

- `gpt-4` → PepGenX gpt-4
- `gpt-4-turbo` → PepGenX gpt-4-turbo
- `gpt-4o` → PepGenX gpt-4o
- `gpt-4o-mini` → PepGenX gpt-4o-mini
- `gpt-3.5-turbo` → PepGenX gpt-3.5-turbo
- `gpt-5` → PepGenX gpt-5
- `claude-3-sonnet` → PepGenX claude-3-sonnet
- `claude-3-haiku` → PepGenX claude-3-haiku
- `claude-3-opus` → PepGenX claude-3-opus

## Health Checks

### Available Endpoints

- `GET /health` - Basic health check
- `GET /health/ready` - Readiness check (validates all dependencies)
- `GET /health/live` - Liveness check (for Kubernetes)
- `GET /health/detailed` - Detailed health information (requires API key)
- `GET /health/metrics` - Basic metrics information

### Example Health Check

```bash
curl http://localhost:8000/health/ready
```

Response:
```json
{
  "status": "ready",
  "timestamp": 1703123456,
  "checks": {
    "auth": {"okta_token_file": "valid", "api_keys_configured": "count: 3"},
    "pepgenx_api": {"status": "healthy", "response_time_ms": 150.5},
    "config": {"pepgenx_api_url": true, "okta_token_file": true}
  }
}
```

## Monitoring

### Prometheus Metrics

When `ENABLE_METRICS=true`, the following metrics are available at `/metrics`:

- `pepgenx_wrapper_requests_total` - Total number of requests
- `pepgenx_wrapper_request_duration_seconds` - Request duration histogram
- `pepgenx_wrapper_pepgenx_api_calls_total` - Total PepGenX API calls
- `pepgenx_wrapper_errors_total` - Total number of errors

### Logging

The wrapper provides structured logging with:

- Request/response correlation IDs
- Sanitized request/response logging
- Error tracking with stack traces
- Performance metrics
- JSON or text format support

### Docker Compose Monitoring Stack

Enable monitoring with:

```bash
docker-compose --profile monitoring up -d
```

This starts:
- Prometheus (http://localhost:9091)
- Grafana (http://localhost:3000, admin/admin)

## Development

### Running Tests

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Code Quality

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Type checking
mypy app/

# Linting
flake8 app/ tests/
```

## Troubleshooting

### Common Issues

1. **OKTA Token Issues**:
   - Ensure `okta_token.json` exists and is readable
   - Check token expiration
   - Verify token format

2. **PepGenX API Connection**:
   - Verify API URL and credentials
   - Check network connectivity
   - Review PepGenX API logs

3. **Authentication Errors**:
   - Verify API keys in `OPENAI_WRAPPER_API_KEYS`
   - Check API key format (must start with `sk-`)

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python -m uvicorn app.main:app --reload
```

### Health Check Debugging

```bash
# Check detailed health status
curl -H "Authorization: Bearer sk-your-api-key" \
  http://localhost:8000/health/detailed
```

## Security Considerations

- Store API keys securely
- Use HTTPS in production
- Regularly rotate OKTA tokens
- Monitor access logs
- Implement proper network security
- Use non-root containers

## License

[Add your license information here]

## Support

For support and questions:
- Check the health endpoints for system status
- Review application logs
- Consult the API documentation at `/docs`
