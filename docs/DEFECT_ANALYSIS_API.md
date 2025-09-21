# Defect Analysis API Documentation

## Overview

The Defect Analysis API provides endpoints to analyze equipment defects using the integrated defect analysis pipeline. The API processes user input through three stages: intent extraction, vector search, and result aggregation.

## Endpoints

### 1. JSON Endpoint

**POST** `/defect-analysis`

Accepts JSON payload for defect analysis.

#### Request Body

```json
{
  "user_input": "The pump piston is not operating smoothly",
  "top_n": 10,
  "min_score": 0.6,
  "enable_logging": true,
  "enable_caching": true,
  "parallel_search": true
}
```

#### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `user_input` | string | Yes | - | Equipment issue description (1-1000 chars) |
| `top_n` | integer | No | 10 | Number of top results to return (1-50) |
| `min_score` | float | No | 0.6 | Minimum similarity score (0.0-1.0) |
| `enable_logging` | boolean | No | true | Enable detailed logging |
| `enable_caching` | boolean | No | true | Enable result caching |
| `parallel_search` | boolean | No | true | Enable parallel vector search |

### 2. Form Endpoint

**POST** `/defect-analysis/form`

Accepts form data for defect analysis.

#### Form Parameters

Same parameters as JSON endpoint, but submitted as form data.

## Response Format

Both endpoints return the same response structure:

```json
{
  "success": true,
  "original_input": "The pump piston is not operating smoothly",
  "intent_data": {
    "component": "Pump",
    "sub_component": "Pump piston",
    "related_component": "Unknown",
    "issue": "Not operating smoothly"
  },
  "total_unique_results": 3,
  "defects": [
    {
      "id": "def_001",
      "defect_code": "PUMP_001",
      "defect_text": "Pump piston malfunction",
      "score": 0.85,
      "subsystem": "Hydraulic",
      "severity": "Medium",
      "symptoms": ["Irregular operation", "Noise"],
      "detection_methods": ["Visual inspection", "Performance monitoring"],
      "tags": ["pump", "piston", "hydraulic"],
      "likely_root_causes": ["Worn seals", "Contaminated fluid"],
      "recommended_actions": ["Replace seals", "Change fluid"]
    }
  ],
  "root_causes": ["Worn seals", "Contaminated fluid"],
  "corrective_actions": ["Replace seals", "Change fluid"],
  "processing_time_ms": 1250.5,
  "error": null,
  "metadata": {
    "pipeline_version": "1.0.0",
    "agent_name": "jk_pilger_extract_intent_agent",
    "vector_search_config": {
      "top_n": 10,
      "min_score": 0.6,
      "parallel_search": true
    },
    "caching_enabled": true,
    "logging_enabled": true
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether the analysis was successful |
| `original_input` | string | Original user input |
| `intent_data` | object | Extracted intent information |
| `total_unique_results` | integer | Number of unique defects found |
| `defects` | array | List of matching defects with details |
| `root_causes` | array | Consolidated root causes |
| `corrective_actions` | array | Consolidated corrective actions |
| `processing_time_ms` | float | Total processing time in milliseconds |
| `error` | string | Error message if analysis failed |
| `metadata` | object | Additional metadata about the analysis |

## Usage Examples

### cURL Examples

#### JSON Request
```bash
curl -X POST http://localhost:8000/defect-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Pump cavitation issue",
    "top_n": 5,
    "min_score": 0.7
  }'
```

#### Form Request
```bash
curl -X POST http://localhost:8000/defect-analysis/form \
  -F "user_input=Motor bearing overheating" \
  -F "top_n=10" \
  -F "min_score=0.6"
```

### Python Examples

#### Using requests library
```python
import requests

# JSON request
response = requests.post(
    "http://localhost:8000/defect-analysis",
    json={
        "user_input": "Hydraulic system leak",
        "top_n": 8,
        "min_score": 0.5
    }
)

result = response.json()
print(f"Found {result['total_unique_results']} defects")
```

#### Using httpx (async)
```python
import httpx
import asyncio

async def analyze_defect():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/defect-analysis",
            json={"user_input": "Gear tooth broken"}
        )
        return response.json()

result = asyncio.run(analyze_defect())
```

### JavaScript Examples

#### Using fetch
```javascript
const response = await fetch('http://localhost:8000/defect-analysis', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    user_input: 'Bearing noise in motor',
    top_n: 10,
    min_score: 0.6
  })
});

const result = await response.json();
console.log(`Analysis completed: ${result.success}`);
```

## Error Handling

### Validation Errors

The API returns HTTP 422 for validation errors:

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "user_input"],
      "msg": "String should have at least 1 character",
      "input": ""
    }
  ]
}
```

### Processing Errors

When the analysis fails, the API returns a structured error response:

```json
{
  "success": false,
  "original_input": "Invalid input",
  "intent_data": {},
  "total_unique_results": 0,
  "defects": [],
  "root_causes": [],
  "corrective_actions": [],
  "processing_time_ms": 0.0,
  "error": "Agent invocation failed: Connection timeout",
  "metadata": {
    "pipeline_version": "1.0.0",
    "error_occurred": true
  }
}
```

## Pipeline Architecture

The defect analysis pipeline consists of three stages:

1. **Intent Extraction**: Uses `jk_pilger_extract_intent_agent` to extract structured intent from user input
2. **Vector Search**: Searches for similar defects in the vector database
3. **Result Aggregation**: Consolidates and deduplicates results

## Configuration

The pipeline can be configured through the request parameters:

- **top_n**: Controls how many results to return from vector search
- **min_score**: Sets the minimum similarity threshold
- **enable_logging**: Enables detailed logging for debugging
- **enable_caching**: Enables caching for repeated queries
- **parallel_search**: Enables parallel execution of vector searches

## Performance Considerations

- **Caching**: Enable caching for repeated queries to improve performance
- **Parallel Search**: Enable parallel search for faster vector operations
- **Batch Processing**: For multiple analyses, consider batching requests
- **Timeout**: The API has built-in timeouts for agent and vector search operations

## Integration Notes

- The API integrates with the existing jk-agents system
- Uses the same agent configuration from `config/jk-gemba.yaml`
- Requires vector database service running on `http://localhost:8010/`
- Supports multilingual input (English, Hindi, Urdu)

## Status Codes

- **200**: Successful analysis (check `success` field in response)
- **422**: Validation error in request parameters
- **500**: Internal server error

## Rate Limiting

Currently, no rate limiting is implemented. Consider implementing rate limiting for production use.

## Security

- Input validation is performed on all parameters
- No authentication is currently required
- Consider adding authentication for production deployment
