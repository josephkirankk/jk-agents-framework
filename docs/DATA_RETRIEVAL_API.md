# Large Data Retrieval REST API

**Date**: 2025-10-12  
**Status**: ✅ COMPLETE  
**Version**: 1.0.0

---

## Overview

The Large Data Retrieval API provides REST endpoints to retrieve stored JSON data from the SQLite database based on reference IDs. This API allows external applications to access large datasets that were generated and stored by the Schema-Agnostic Test Data Generator system.

---

## API Endpoints

### 1. Health Check

**Endpoint**: `GET /health`

**Description**: Check if the API server is running and healthy.

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "litellm_available": true,
  "memory_available": true
}
```

**Example**:
```bash
curl http://localhost:8000/health
```

---

### 2. Retrieve Data by Reference ID

**Endpoint**: `GET /api/data/{reference_id}`

**Description**: Retrieve stored JSON data from the SQLite database by reference ID.

**Path Parameters**:
- `reference_id` (required): Reference ID in format `ref_[a-f0-9]{12}` (e.g., `ref_fd05f4970f14`)

**Query Parameters**:
- `thread_id` (optional): Thread ID for filtering by specific thread/session

**Response Format**:
```json
{
  "status": "success",
  "reference_id": "ref_fd05f4970f14",
  "data": [...],  // The actual stored dataset (complete raw JSON)
  "metadata": {
    "tool_name": "run_python_code",
    "storage_type": "sqlite",
    "content_type": "json",
    "size_bytes": 444240,
    "compressed": true,
    "created_at": "2025-10-12 10:01:52",
    "access_count": 2,
    "description": "Auto-stored from Python execution",
    "record_count": 2400,
    "data_type": "list",
    "stored_at": "2025-10-12T15:31:52.827455",
    "auto_stored": true
  }
}
```

**Example - Basic Retrieval**:
```bash
curl http://localhost:8000/api/data/ref_fd05f4970f14
```

**Example - With Thread ID Filter**:
```bash
curl "http://localhost:8000/api/data/ref_fd05f4970f14?thread_id=abc123"
```

**Example - Save to File**:
```bash
curl http://localhost:8000/api/data/ref_fd05f4970f14 -o data.json
```

**Example - Extract Only Data Field**:
```bash
curl -s http://localhost:8000/api/data/ref_fd05f4970f14 | jq '.data' > raw_data.json
```

**Error Responses**:

- **400 Bad Request** - Invalid reference ID format:
  ```json
  {
    "detail": "Invalid reference ID format. Expected: ref_[a-f0-9]{12}, got: invalid_ref"
  }
  ```

- **404 Not Found** - Reference ID not found:
  ```json
  {
    "detail": "Reference ID 'ref_000000000000' not found in database"
  }
  ```

- **404 Not Found** - Thread ID mismatch:
  ```json
  {
    "detail": "Reference ID 'ref_fd05f4970f14' not found for thread_id 'xyz789'"
  }
  ```

- **500 Internal Server Error** - Database or decompression errors:
  ```json
  {
    "detail": "Internal server error: <error message>"
  }
  ```

---

### 3. List All Datasets

**Endpoint**: `GET /api/data`

**Description**: List all stored datasets with their metadata (without the actual data).

**Query Parameters**:
- `limit` (optional): Maximum number of datasets to return (default: 50)
- `offset` (optional): Offset for pagination (default: 0)

**Response Format**:
```json
{
  "status": "success",
  "total_count": 83,
  "limit": 50,
  "offset": 0,
  "datasets": [
    {
      "reference_id": "ref_fd05f4970f14",
      "tool_name": "run_python_code",
      "storage_type": "sqlite",
      "content_type": "json",
      "size_bytes": 444240,
      "created_at": "2025-10-12 10:01:52",
      "access_count": 2,
      "metadata": {
        "description": "Auto-stored from Python execution",
        "record_count": 2400,
        "data_type": "list",
        "stored_at": "2025-10-12T15:31:52.827455",
        "auto_stored": true
      }
    },
    ...
  ]
}
```

**Example - List First 10 Datasets**:
```bash
curl "http://localhost:8000/api/data?limit=10"
```

**Example - Pagination**:
```bash
curl "http://localhost:8000/api/data?limit=10&offset=20"
```

**Example - Get All Reference IDs**:
```bash
curl -s "http://localhost:8000/api/data?limit=1000" | jq '.datasets[].reference_id'
```

---

## Starting the API Server

### Method 1: Direct Execution

```bash
cd /path/to/jk-agents-core
source .venv/bin/activate
python litellm_api.py
```

The server will start on `http://localhost:8000`

### Method 2: Background Process

```bash
cd /path/to/jk-agents-core
source .venv/bin/activate
nohup python litellm_api.py > api_server.log 2>&1 &
```

### Method 3: Using uvicorn Directly

```bash
cd /path/to/jk-agents-core
source .venv/bin/activate
uvicorn litellm_api:app --host 0.0.0.0 --port 8000 --reload
```

---

## Database Structure

The API retrieves data from the `large_tool_data` table in `data/large_data_storage.db`:

```sql
CREATE TABLE large_tool_data (
    reference_id TEXT PRIMARY KEY,
    tool_name TEXT NOT NULL,
    storage_type TEXT NOT NULL,
    storage_location TEXT,
    data_blob BLOB,
    data_hash TEXT,
    size_bytes INTEGER,
    size_category TEXT,
    content_type TEXT,
    compressed BOOLEAN DEFAULT 0,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Data Processing

### Decompression

If the data is compressed (indicated by `compressed: true` in metadata), the API automatically decompresses it using gzip before returning.

### Deserialization

The API deserializes data based on the `content_type`:
- `json`: Parses as JSON and returns as structured data
- `text`: Returns as plain text string
- Other: Returns as UTF-8 decoded string

### Access Tracking

Each time data is retrieved, the API:
1. Increments the `access_count` field
2. Updates the `last_accessed` timestamp

---

## Usage Examples

### Python

```python
import requests
import json

# Retrieve data
response = requests.get('http://localhost:8000/api/data/ref_fd05f4970f14')
data = response.json()

print(f"Status: {data['status']}")
print(f"Reference ID: {data['reference_id']}")
print(f"Record count: {len(data['data'])}")
print(f"First record: {json.dumps(data['data'][0], indent=2)}")

# Save raw data to file
with open('output.json', 'w') as f:
    json.dump(data['data'], f, indent=2)
```

### JavaScript/Node.js

```javascript
const axios = require('axios');
const fs = require('fs');

async function retrieveData(referenceId) {
  const response = await axios.get(`http://localhost:8000/api/data/${referenceId}`);
  const { status, reference_id, data, metadata } = response.data;
  
  console.log(`Status: ${status}`);
  console.log(`Reference ID: ${reference_id}`);
  console.log(`Record count: ${data.length}`);
  
  // Save to file
  fs.writeFileSync('output.json', JSON.stringify(data, null, 2));
}

retrieveData('ref_fd05f4970f14');
```

### cURL + jq

```bash
# Get complete data
curl -s http://localhost:8000/api/data/ref_fd05f4970f14 | jq '.'

# Get only the data array
curl -s http://localhost:8000/api/data/ref_fd05f4970f14 | jq '.data'

# Get metadata only
curl -s http://localhost:8000/api/data/ref_fd05f4970f14 | jq '.metadata'

# Count records
curl -s http://localhost:8000/api/data/ref_fd05f4970f14 | jq '.data | length'

# Get first 5 records
curl -s http://localhost:8000/api/data/ref_fd05f4970f14 | jq '.data[:5]'

# Filter records by field
curl -s http://localhost:8000/api/data/ref_fd05f4970f14 | jq '.data[] | select(.student_class == 5)'
```

---

## Testing

Run the test suite to verify the API is working correctly:

```bash
cd /path/to/jk-agents-core
source .venv/bin/activate
python tests/test_data_api.py
```

**Expected Output**:
```
================================================================================
TEST SUMMARY
================================================================================
✅ Passed: 4
❌ Failed: 0
Total: 4
================================================================================
```

---

## Security Considerations

### Current Implementation

- **No Authentication**: The API currently has no authentication mechanism
- **No Rate Limiting**: No rate limiting is implemented
- **CORS**: Allows all origins (`allow_origins=["*"]`)

### Recommendations for Production

1. **Add Authentication**: Implement API key or OAuth2 authentication
2. **Add Rate Limiting**: Use middleware to limit requests per IP/user
3. **Restrict CORS**: Limit allowed origins to specific domains
4. **Add HTTPS**: Use SSL/TLS certificates for encrypted communication
5. **Add Input Validation**: Validate all query parameters
6. **Add Logging**: Log all API requests for auditing

---

## Troubleshooting

### Port Already in Use

If you get "address already in use" error:

```bash
# Kill existing process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn litellm_api:app --port 8001
```

### Database Not Found

Ensure the database exists:

```bash
ls -la data/large_data_storage.db
```

If missing, run the data generator to create it:

```bash
python tests/run_with_fixed_plan.py
```

### Empty Response

Check server logs:

```bash
tail -f /tmp/api_server.log
```

---

## Files Modified

- **`litellm_api.py`**: Added data retrieval endpoints
- **`tests/test_data_api.py`**: Test suite for API endpoints

---

## Future Enhancements

1. **Streaming Support**: Stream large datasets instead of loading all in memory
2. **Filtering**: Add query parameters to filter data (e.g., by field values)
3. **Pagination**: Add pagination for large datasets
4. **Export Formats**: Support CSV, Excel, Parquet export formats
5. **Compression**: Option to return compressed data for bandwidth savings
6. **Caching**: Add caching layer for frequently accessed datasets
7. **WebSocket Support**: Real-time data updates via WebSockets

---

**Author**: Augment Agent  
**Date**: 2025-10-12  
**Status**: ✅ COMPLETE

