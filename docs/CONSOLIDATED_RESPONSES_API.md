# Consolidated Responses API Documentation

## Overview

The Consolidated Responses API endpoint (`/consolidated-responses`) retrieves all user submissions from the `user_responses/` directory with optional date filtering. This endpoint allows external systems to access consolidated user response data for analysis, reporting, or integration purposes.

## Implementation Details

### Endpoint
- **URL**: `POST /consolidated-responses`
- **Content-Type**: `application/json`
- **Response Model**: `ConsolidatedResponsesResponse`

### Features
- ✅ Retrieve all user submissions from JSON files
- ✅ Optional date range filtering (start_date and end_date)
- ✅ ISO 8601 timestamp validation
- ✅ Efficient filename-based filtering for performance
- ✅ Comprehensive error handling
- ✅ Detailed query metadata in response
- ✅ Sorted results (most recent first)

### Request Model

```python
class ConsolidatedResponsesRequest(BaseModel):
    start_date: Optional[str] = None  # ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
    end_date: Optional[str] = None    # ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
```

### Response Model

```python
class ConsolidatedResponsesResponse(BaseModel):
    status: str                        # Response status ("success" or "error")
    message: str                       # Response message
    query_metadata: Dict[str, Any]     # Metadata about the query
    submissions: List[Dict[str, Any]]  # List of all matching submissions
    total_count: int                   # Total number of submissions returned
```

## Usage Examples

### 1. Get All Submissions

```bash
curl -X POST "http://localhost:8000/consolidated-responses" \
     -H "Content-Type: application/json" \
     -d "{}"
```

### 2. Get Submissions from a Specific Date

```bash
curl -X POST "http://localhost:8000/consolidated-responses" \
     -H "Content-Type: application/json" \
     -d '{
       "start_date": "2025-09-20T00:00:00Z"
     }'
```

### 3. Get Submissions for a Date Range

```bash
curl -X POST "http://localhost:8000/consolidated-responses" \
     -H "Content-Type: application/json" \
     -d '{
       "start_date": "2025-09-20T00:00:00Z",
       "end_date": "2025-09-20T23:59:59Z"
     }'
```

## Response Examples

### Successful Response

```json
{
  "status": "success",
  "message": "Successfully retrieved 5 submissions",
  "query_metadata": {
    "query_timestamp": "2025-09-20T10:30:45.123Z",
    "start_date_filter": "2025-09-20T00:00:00Z",
    "end_date_filter": "2025-09-20T23:59:59Z",
    "directory_exists": true,
    "total_files_found": 10,
    "files_processed": 5,
    "files_skipped": 5,
    "processing_time_ms": 45
  },
  "submissions": [
    {
      "timestamp": "2025-09-20T08:07:31.595Z",
      "original_input": "मोल्ड अन इवन कूलिंग प्रॉब्लम.",
      "remarks": "",
      "selected_defect": {
        "defect_code": "PLG.CLB.COOLANT.CONTAM",
        "defect_text": "Coolant contamination",
        "confidence_score": 0.75,
        "mapping_status": "NEAR_MATCH:PLG.CLB.COOLANT.CONTAM",
        "curator_action": "REVIEW_REQUIRED"
      },
      "selected_pairs": [...],
      "analysis_metadata": {...},
      "submission_metadata": {...}
    }
  ],
  "total_count": 5
}
```

### Error Response (400 Bad Request)

```json
{
  "detail": {
    "status": "error",
    "error_code": "VALIDATION_ERROR",
    "message": "Date must be in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)",
    "timestamp": "2025-09-20T10:30:45.123Z"
  }
}
```

### Error Response (500 Internal Server Error)

```json
{
  "detail": {
    "status": "error",
    "error_code": "INTERNAL_ERROR",
    "message": "Failed to process consolidated responses request",
    "timestamp": "2025-09-20T10:30:45.123Z"
  }
}
```

## Query Metadata Fields

The `query_metadata` object contains the following information:

- `query_timestamp`: When the query was processed
- `start_date_filter`: Applied start date filter (if any)
- `end_date_filter`: Applied end date filter (if any)
- `directory_exists`: Whether the user_responses directory exists
- `total_files_found`: Total JSON files found in directory
- `files_processed`: Number of files successfully processed
- `files_skipped`: Number of files skipped (due to filters or errors)
- `processing_time_ms`: Total processing time in milliseconds

## Date Filtering Logic

1. **Filename-based filtering**: Initial filtering uses timestamps extracted from filenames (`submit_YYYYMMDDHHMMSS.json`)
2. **Content-based verification**: Files passing filename filter are read and processed
3. **Timezone handling**: All dates are converted to UTC for comparison
4. **Sorting**: Results are sorted by timestamp (most recent first)

## Validation Rules

- Date formats must be ISO 8601 compliant (YYYY-MM-DDTHH:MM:SSZ)
- If both dates provided, start_date must be <= end_date
- Invalid JSON files are skipped with logging
- Malformed filenames are skipped with logging

## Performance Considerations

- Efficient filename-based pre-filtering reduces I/O operations
- Files are processed sequentially to manage memory usage
- Processing time is tracked and reported in metadata
- Large datasets are handled gracefully without memory issues

## Testing

Use the provided test script to verify the endpoint:

```bash
python test_consolidated_responses.py
```

The test script covers:
- ✅ All submissions retrieval
- ✅ Date range filtering
- ✅ Invalid date format handling
- ✅ Invalid date range handling
- ✅ Performance measurement

## Integration Notes

- This endpoint is designed for external system integration
- Supports both programmatic access and manual testing
- Returns structured data suitable for further processing
- Includes comprehensive metadata for monitoring and debugging
- Compatible with existing authentication and CORS policies
