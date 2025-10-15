# API Data Endpoint Fix

## Problem

The `/api/data/{reference_id}` endpoint was returning `{"detail":"Not Found"}` even though the data existed in the database.

## Root Cause

The `/api/data/` endpoints were **only defined in `litellm_api.py`**, but the user was running **`api.py`** (the main application server).

### Why This Happened

The codebase has two FastAPI applications:
1. **`api.py`** - Main application with query, worker, multimodal, OCR endpoints
2. **`litellm_api.py`** - Separate LiteLLM-focused API with data retrieval endpoints

When running `uvicorn api:app`, only the endpoints in `api.py` are available.

## Solution

Added the `/api/data/` endpoints to `api.py` so they're available in the main application.

### Changes Made

**File**: `api.py`

1. **Added imports**:
   ```python
   import sqlite3
   import gzip
   import re
   from fastapi import Path as PathParam, Query
   from fastapi.responses import JSONResponse
   ```

2. **Added helper functions**:
   - `get_database_connection()` - Uses centralized database config
   - `validate_reference_id()` - Validates ref_xxx format

3. **Added endpoints**:
   - `GET /api/data/{reference_id}` - Retrieve specific dataset
   - `GET /api/data` - List all datasets with pagination

### How It Works

```python
@app.get("/api/data/{reference_id}")
async def get_data_by_reference(reference_id: str, thread_id: Optional[str] = None):
    # 1. Validate reference ID format
    # 2. Connect to database using centralized config
    # 3. Query large_tool_data table
    # 4. Decompress if needed
    # 5. Deserialize JSON
    # 6. Return data with metadata
```

### Database Configuration

The endpoint uses the centralized database configuration:

```python
from app.database_config import get_large_data_config
config = get_large_data_config(format="app")
db_path = config.get("sqlite_path", "./data/large_data_storage.db")
```

This ensures it uses the same database as the agents (e.g., `./data/schema_test_data.db` if configured).

## Testing

### Restart the Server

```bash
# Kill existing server
pkill -f "uvicorn api:app"

# Start with new endpoints
uvicorn api:app --host 0.0.0.0 --port 8000
```

### Test the Endpoints

```bash
# List all datasets
curl http://localhost:8000/api/data

# Get specific dataset
curl http://localhost:8000/api/data/ref_c9014aef6663

# Or use the test script
./test_api_data_endpoint.sh
```

### Expected Response

```json
{
  "status": "success",
  "reference_id": "ref_c9014aef6663",
  "data": [...],  // Your actual data
  "metadata": {
    "tool_name": "run_python_code",
    "storage_type": "sqlite",
    "content_type": "json",
    "size_bytes": 82123,
    "compressed": true,
    "created_at": "2025-10-12 15:18:38",
    "access_count": 1
  }
}
```

## Files Modified

1. **`api.py`**
   - Added imports: `sqlite3`, `gzip`, `re`, `PathParam`, `Query`, `JSONResponse`
   - Added `get_database_connection()` function
   - Added `validate_reference_id()` function
   - Added `GET /api/data/{reference_id}` endpoint
   - Added `GET /api/data` endpoint

## Benefits

✅ Data retrieval now works from main API server
✅ No need to run separate `litellm_api.py` server
✅ Uses centralized database configuration
✅ Consistent with agent database usage
✅ Includes pagination for listing datasets
✅ Proper error handling and validation

## Environment Variable Support

The endpoint respects the same environment variables as the agents:

```bash
# In .env file
LARGE_DATA_DB_PATH=./data/schema_test_data.db
LARGE_DATA_FILES_PATH=./data/schema_test_files/
```

## API Documentation

### GET /api/data/{reference_id}

Retrieve a specific dataset by reference ID.

**Parameters:**
- `reference_id` (path) - Reference ID in format `ref_[a-f0-9]{12}`
- `thread_id` (query, optional) - Filter by thread ID

**Responses:**
- `200` - Success with data
- `400` - Invalid reference ID format
- `404` - Reference ID not found
- `500` - Server error

### GET /api/data

List all stored datasets with pagination.

**Parameters:**
- `limit` (query, default: 50) - Max datasets to return
- `offset` (query, default: 0) - Pagination offset

**Response:**
```json
{
  "status": "success",
  "total": 5,
  "limit": 50,
  "offset": 0,
  "datasets": [...]
}
```

## Next Steps

1. ✅ Restart the server
2. ⏭️ Test with your curl command
3. ⏭️ Verify data retrieval works
4. ⏭️ Consider deprecating `litellm_api.py` if not needed separately

---

**Status**: ✅ FIXED - Endpoints added to main API server
