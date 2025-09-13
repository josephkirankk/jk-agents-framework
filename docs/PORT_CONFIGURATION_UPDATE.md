# Port Configuration Update

## Overview

The JK-Agents system has been updated with new port configurations to avoid conflicts and improve clarity:

- **JK-Agents API**: Port 8000 (default)
- **PepGenX Wrapper**: Port 8080 (default)

## Changes Made

### 1. Code Changes

#### `app/agent_builder.py`
- Updated PepGenX base URL from `http://127.0.0.1:8000/v1` to `http://127.0.0.1:8080/v1`

#### `pepgenx_openai_wrapper/.env.example`
- Updated `OPENAI_WRAPPER_PORT` from 8000 to 8080

#### `pepgenx_openai_wrapper/app/core/config.py`
- Updated default port from 8000 to 8080

#### `pepgenx_openai_wrapper/docker-compose.yml`
- Updated port mapping from `8000:8000` to `8080:8080`
- Updated environment variable `OPENAI_WRAPPER_PORT` to 8080

#### `pepgenx_openai_wrapper/Dockerfile`
- Updated EXPOSE port from 8000 to 8080
- Updated health check URL to use port 8080
- Updated CMD to use port 8080

### 2. Documentation Updates

#### `docs/PEPGENX_MULTIMODAL_FIX.md`
- Updated curl examples to use port 8000 for JK-Agents API

## Starting the Services

### 1. Start PepGenX Wrapper (Port 8080)
```bash
cd pepgenx_openai_wrapper
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### 2. Start JK-Agents API (Port 8000)
```bash
python -m uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
```

## Testing the Configuration

### 1. Health Checks
```bash
# Test PepGenX Wrapper
curl -X GET http://localhost:8080/health

# Test JK-Agents API
curl -X GET http://localhost:8000/health
```

### 2. PepGenX Integration Test
```bash
curl --location 'http://localhost:8000/worker/upload' \
  --form 'agent_name="general_assistant"' \
  --form 'input="2 + 5 = ?"' \
  --form 'config_path="config\\pepgenx_simple_test.yaml"' \
  --form 'raw_output="True"'
```

## Environment Variables

### JK-Agents
- No changes needed - uses port 8000 by default

### PepGenX Wrapper
Update your `.env` file:
```bash
OPENAI_WRAPPER_PORT=8080
```

Or set environment variable:
```bash
export PEPGENX_WRAPPER_BASE_URL=http://127.0.0.1:8080/v1
```

## Docker Configuration

### PepGenX Wrapper
The docker-compose.yml has been updated to use port 8080:
```yaml
ports:
  - "8080:8080"
```

## Backward Compatibility

- Existing configurations will continue to work if you set the appropriate environment variables
- The default behavior has changed, so update your scripts and documentation accordingly

## Troubleshooting

### Port Already in Use
If you encounter port conflicts:

```bash
# Check what's using the port
netstat -ano | findstr :8080
netstat -ano | findstr :8000

# Kill processes if needed (Windows)
taskkill /PID <process_id> /F
```

### Connection Refused
Ensure both services are running on the correct ports:
- PepGenX Wrapper: http://localhost:8080
- JK-Agents API: http://localhost:8000

## Migration Guide

If you have existing deployments:

1. Update your PepGenX wrapper configuration to use port 8080
2. Update any scripts or documentation that reference the old ports
3. Update environment variables if using custom configurations
4. Test the integration to ensure everything works correctly

## Files Modified

- `app/agent_builder.py`
- `pepgenx_openai_wrapper/.env.example`
- `pepgenx_openai_wrapper/app/core/config.py`
- `pepgenx_openai_wrapper/docker-compose.yml`
- `pepgenx_openai_wrapper/Dockerfile`
- `docs/PEPGENX_MULTIMODAL_FIX.md`
- `docs/PORT_CONFIGURATION_UPDATE.md` (this file)
