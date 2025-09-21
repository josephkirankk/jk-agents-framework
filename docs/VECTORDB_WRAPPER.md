# VectorDB Wrapper Documentation

## Overview

The VectorDB Wrapper is a Python client library for interacting with the VectorDB API service. It provides a clean, type-safe interface for searching and upserting defects in the ontology database with comprehensive error handling and validation.

## Features

- **Type-Safe**: Built with Pydantic models for request/response validation
- **Async Support**: Full asynchronous support using httpx
- **Error Handling**: Comprehensive error handling with custom exceptions
- **Retry Logic**: Automatic retry on connection failures
- **Logging**: Detailed logging with configurable levels
- **Decorators**: Convenient decorators for common operations
- **Cross-Platform**: Works on Windows and macOS

## Installation

The VectorDB wrapper is included in the JK-Agents framework. Ensure you have the required dependencies:

```bash
pip install httpx pydantic
```

## Configuration

Add the VectorDB API base URL to your `.env` file:

```env
# VectorDB API Configuration
VECTORDB_BASE_URL=http://localhost:8010
```

## Quick Start

### Basic Usage

```python
import asyncio
from vectordb_wrapper import VectorDBClient, SearchRequest, UpsertRequest

async def main():
    async with VectorDBClient() as client:
        # Health check
        health = await client.health_check()
        print(f"API Status: {health.status}")

        # Search for defects
        search_request = SearchRequest(
            query="motor bearing failure",
            top_n=5,
            min_score=0.7
        )

        response = await client.search(search_request)
        print(f"Found {response.total_results} results")

        for result in response.results:
            defect = result.defect
            print(f"- {defect.defect_code}: {defect.defect_text} (Score: {result.score:.1%})")

asyncio.run(main())
```

### JSON Upsert (KISS Principle)

The simplest way to upsert defects from JSON:

```python
from vectordb_wrapper import upsert_json_defects_sync

# Your JSON string with defects
json_data = '''
{
  "defects": [
    {
      "defect_code": "PLG.HYD.PMP.PISTON_STUCK",
      "defect_text": "Hydraulic pump piston not moving uniformly",
      "subsystem": "PMP",
      "severity": "Medium",
      "symptoms": ["Uneven piston movement", "Reduced pump output"],
      "tags": ["hydraulic pump", "piston", "loading"]
    }
  ]
}
'''

# One line of code - KISS!
result = upsert_json_defects_sync(json_data)
print(f"Upserted {result['successful_upserts']} defects")
```

### Using Decorators

```python
from vectordb_wrapper import vectordb_wrapper, VectorDBClient, SearchRequest

@vectordb_wrapper(log_requests=True, log_responses=True)
async def search_defects(client: VectorDBClient, query: str):
    request = SearchRequest(query=query, top_n=5)
    return await client.search(request)

# Usage
result = await search_defects("pump failure")
```

## API Reference

### VectorDBClient

The main client class for interacting with the VectorDB API.

#### Constructor

```python
VectorDBClient(
    base_url: Optional[str] = None,
    timeout: float = 30.0,
    max_retries: int = 3,
    headers: Optional[Dict[str, str]] = None
)
```

**Parameters:**
- `base_url`: Base URL for the VectorDB API (defaults to `VECTORDB_BASE_URL` env var)
- `timeout`: Request timeout in seconds
- `max_retries`: Maximum number of retry attempts
- `headers`: Additional headers to include in requests

#### Methods

##### health_check()

Check the health status of the VectorDB API.

```python
async def health_check() -> HealthResponse
```

**Returns:** `HealthResponse` with status information

##### search(request)

Search for defects using natural language query (POST method).

```python
async def search(request: SearchRequest) -> SearchResponse
```

**Parameters:**
- `request`: SearchRequest object with query parameters

**Returns:** `SearchResponse` with search results

##### search_get(query, top_n, min_score)

Search for defects using GET method (convenience method).

```python
async def search_get(
    query: str, 
    top_n: int = 5, 
    min_score: float = 0.7
) -> SearchResponse
```

**Parameters:**
- `query`: Search query in natural language
- `top_n`: Number of results to return (1-50)
- `min_score`: Minimum similarity score (0.0-1.0)

**Returns:** `SearchResponse` with search results

##### upsert(request)

Create or update a defect in the vector database.

```python
async def upsert(request: UpsertRequest) -> UpsertResponse
```

**Parameters:**
- `request`: UpsertRequest object with defect data

**Returns:** `UpsertResponse` with operation result

##### upsert_json_defects(json_string)

Parse JSON string containing defects and upsert them to the database.

```python
async def upsert_json_defects(json_string: str) -> Dict[str, Any]
```

**Parameters:**
- `json_string`: JSON string containing defects array

**Returns:** Dictionary with summary of upsert operations including:
- `total_defects`: Total number of defects in JSON
- `successful_upserts`: Number of successful upserts
- `failed_upserts`: Number of failed upserts
- `results`: List of upsert results
- `errors`: List of errors (if any)

### Utility Functions

#### upsert_json_defects(json_string, base_url)

Async convenience function to upsert defects from JSON string.

```python
from vectordb_wrapper import upsert_json_defects

result = await upsert_json_defects(json_string)
print(f"Upserted {result['successful_upserts']} defects")
```

#### upsert_json_defects_sync(json_string, base_url)

Synchronous wrapper for JSON upsert (KISS principle - simplest usage).

```python
from vectordb_wrapper import upsert_json_defects_sync

result = upsert_json_defects_sync(json_string)
print(f"Upserted {result['successful_upserts']} defects")
```

**JSON Format Expected:**
```json
{
  "defects": [
    {
      "defect_code": "REQUIRED.CODE",
      "defect_text": "Required description",
      "subsystem": "REQUIRED",
      "severity": "Medium",
      "typical_frequency": "Unknown",
      "symptoms": ["symptom1", "symptom2"],
      "detection_methods": ["method1"],
      "early_warning_signals": ["signal1"],
      "tags": ["tag1", "tag2"],
      "likely_root_causes": ["cause1"],
      "recommended_actions": ["action1"]
    }
  ]
}
```

### Data Models

#### SearchRequest

```python
class SearchRequest(BaseModel):
    query: str  # Search query (required)
    top_n: int = 5  # Number of results (1-50)
    min_score: float = 0.7  # Minimum similarity score (0.0-1.0)
```

#### SearchResponse

```python
class SearchResponse(BaseModel):
    query: str  # Original search query
    total_results: int  # Total number of results
    execution_time_ms: float  # Execution time in milliseconds
    results: List[SearchResult]  # Search results
```

#### UpsertRequest

```python
class UpsertRequest(BaseModel):
    defect_code: str  # Unique defect identifier (required)
    defect_text: str  # Description of the defect (required)
    subsystem: str  # Subsystem code (required)
    severity: str = "Medium"  # Severity level
    typical_frequency: str = "Unknown"  # How often this occurs
    symptoms: List[str] = []  # List of symptoms
    detection_methods: List[str] = []  # Detection methods
    early_warning_signals: List[str] = []  # Early warning signals
    tags: List[str] = []  # Tags for categorization
    likely_root_causes: List[str] = []  # Likely root causes
    recommended_actions: List[str] = []  # Recommended actions
```

#### UpsertResponse

```python
class UpsertResponse(BaseModel):
    success: bool  # Whether the operation was successful
    message: str  # Response message
    defect_code: str  # Defect code that was processed
    operation: str  # Operation performed (created/updated)
```

### Decorators

#### @vectordb_wrapper

Decorator that wraps functions with VectorDB client functionality.

```python
@vectordb_wrapper(
    base_url: Optional[str] = None,
    timeout: float = 30.0,
    max_retries: int = 3,
    log_requests: bool = True,
    log_responses: bool = True,
    raise_on_error: bool = True
)
```

#### @log_vectordb_operations

Decorator that logs VectorDB operations with configurable detail level.

```python
@log_vectordb_operations(
    log_level: int = logging.INFO,
    include_request_data: bool = False,
    include_response_data: bool = False
)
```

## Error Handling

The wrapper provides comprehensive error handling with custom exceptions:

- `VectorDBError`: Base exception for VectorDB-related errors
- `VectorDBConnectionError`: Connection failures
- `VectorDBValidationError`: Request/response validation failures
- `VectorDBTimeoutError`: Request timeouts
- `VectorDBAuthenticationError`: Authentication failures
- `VectorDBNotFoundError`: Resource not found
- `VectorDBRateLimitError`: Rate limit exceeded

```python
from vectordb_wrapper.exceptions import VectorDBError, VectorDBConnectionError

try:
    async with VectorDBClient() as client:
        response = await client.search(request)
except VectorDBConnectionError as e:
    print(f"Connection failed: {e}")
except VectorDBError as e:
    print(f"API error: {e}")
```

## Examples

### Complete Search Example

```python
import asyncio
from vectordb_wrapper import VectorDBClient, SearchRequest

async def search_example():
    async with VectorDBClient() as client:
        # Create search request
        request = SearchRequest(
            query="hydraulic pump cavitation",
            top_n=3,
            min_score=0.6
        )
        
        # Perform search
        response = await client.search(request)
        
        print(f"Query: {response.query}")
        print(f"Found {response.total_results} results in {response.execution_time_ms}ms")
        
        for i, result in enumerate(response.results, 1):
            defect = result.defect
            print(f"\nResult {i} (Score: {result.score:.1%}):")
            print(f"  Code: {defect.defect_code}")
            print(f"  Text: {defect.defect_text}")
            print(f"  Subsystem: {defect.subsystem}")
            print(f"  Severity: {defect.severity}")
            print(f"  Symptoms: {', '.join(defect.symptoms)}")
            print(f"  Tags: {', '.join(defect.tags)}")

asyncio.run(search_example())
```

### Complete Upsert Example

```python
import asyncio
from vectordb_wrapper import VectorDBClient, UpsertRequest

async def upsert_example():
    async with VectorDBClient() as client:
        # Create upsert request
        request = UpsertRequest(
            defect_code="EX.PUMP.SEAL.LEAK.001",
            defect_text="Pump seal leakage causing fluid loss",
            subsystem="PMP",
            severity="High",
            typical_frequency="Medium",
            symptoms=["visible fluid leakage", "reduced pressure"],
            detection_methods=["visual inspection", "pressure monitoring"],
            early_warning_signals=["slight pressure drop"],
            tags=["pump", "seal", "leakage"],
            likely_root_causes=["seal wear", "contamination"],
            recommended_actions=["replace seal", "check fluid"]
        )
        
        # Perform upsert
        response = await client.upsert(request)
        
        print(f"Success: {response.success}")
        print(f"Message: {response.message}")
        print(f"Defect Code: {response.defect_code}")
        print(f"Operation: {response.operation}")

asyncio.run(upsert_example())
```

## Testing

Run the test suite to verify the wrapper works with your VectorDB API:

```bash
# Set the base URL (optional, defaults to http://localhost:8010)
export VECTORDB_BASE_URL=http://localhost:8010

# Run tests
python test_vectordb_wrapper.py
```

The test suite includes:
- Health check verification
- Upsert functionality testing
- Search (POST and GET) testing
- Decorator functionality testing
- Error handling validation
- Request validation testing

## Logging

The VectorDB wrapper includes two types of logging:

### Standard Application Logging

Configure standard logging for the VectorDB wrapper:

```python
from vectordb_wrapper.utils import setup_logging

# Setup logging with INFO level
setup_logging("INFO")

# Or use DEBUG for more detailed logs
setup_logging("DEBUG")
```

### Vector Operations Logging

**NEW**: Comprehensive logging for all vector operations (search and upsert) with detailed performance metrics.

#### Features
- **Automatic logging** of all search and upsert operations
- **Timestamped log files** in format: `vector_<YYYYMMDDHHMMSS>.json`
- **Detailed performance metrics** including execution time and API response time
- **Cross-platform compatibility** with proper encoding for Windows/macOS
- **JSON format** for easy parsing and analysis

#### Log Directory Structure
```
vectordb_wrapper/
├── vectorlogs/
│   ├── vector_20250921110907.json
│   ├── vector_20250921111205.json
│   └── ...
└── [other files]
```

#### Configuration
```bash
# Enable/disable vector logging (default: enabled)
export VECTORDB_VECTOR_LOGGING=true
```

#### Example Log Entry
```json
{
  "timestamp": "2025-09-21T11:09:07.123456",
  "operation_type": "search",
  "operation_start": "2025-09-21T11:09:07.123456",
  "operation_end": "2025-09-21T11:09:07.234567",
  "execution_time_ms": 111.111,
  "input_parameters": {
    "query": "hydraulic pump failure",
    "top_n": 5,
    "min_score": 0.7
  },
  "success": true,
  "result": {
    "query": "hydraulic pump failure",
    "results_count": 3,
    "results": [...]
  },
  "performance_metrics": {
    "api_response_time_ms": 95.5,
    "results_count": 3
  }
}
```

#### Usage
Vector logging is automatic - no code changes required:

```python
from vectordb_wrapper import VectorDBClient, SearchRequest

async with VectorDBClient() as client:
    # This operation will be automatically logged
    request = SearchRequest(query="pump failure", top_n=5)
    response = await client.search(request)
```

For detailed information, see [Vector Logging Documentation](VECTOR_LOGGING.md).

## Utilities

The wrapper includes utility functions for common operations:

```python
from vectordb_wrapper.utils import (
    validate_search_params,
    validate_defect_data,
    create_upsert_request,
    format_search_results,
    save_results_to_file
)

# Validate search parameters
request = validate_search_params("motor failure", top_n=5, min_score=0.7)

# Format results for display
formatted = format_search_results(response.results)
print(formatted)

# Save results to file
filepath = save_results_to_file(response.results, "search_results.json")
```

## Best Practices

1. **Use Context Managers**: Always use `async with` for proper resource cleanup
2. **Handle Exceptions**: Implement proper error handling for production use
3. **Configure Timeouts**: Set appropriate timeouts for your use case
4. **Enable Logging**: Use logging to monitor API interactions
5. **Validate Input**: Use Pydantic models for type safety
6. **Test Thoroughly**: Use the provided test suite to verify functionality

## Troubleshooting

### Common Issues

1. **Connection Refused**: Ensure the VectorDB API server is running on the specified URL
2. **Timeout Errors**: Increase the timeout value or check network connectivity
3. **Validation Errors**: Verify request data matches the expected schema
4. **Import Errors**: Ensure all dependencies are installed

### Debug Mode

Enable debug logging for detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will show detailed HTTP request/response information and help diagnose issues.
