# Curl Commands for Consolidated Responses API

## Basic Usage

### 1. Get All Submissions (No Filters)
```bash
curl -X POST "http://127.0.0.1:8000/consolidated-responses" \
     -H "Content-Type: application/json" \
     -d "{}"
```

### 2. Get Submissions from Today
```bash
curl -X POST "http://127.0.0.1:8000/consolidated-responses" \
     -H "Content-Type: application/json" \
     -d '{"start_date": "2025-09-20T00:00:00Z"}'
```

### 3. Get Submissions for Specific Date Range
```bash
curl -X POST "http://127.0.0.1:8000/consolidated-responses" \
     -H "Content-Type: application/json" \
     -d '{"start_date": "2025-09-20T00:00:00Z", "end_date": "2025-09-20T23:59:59Z"}'
```

### 4. Get Submissions with Only End Date
```bash
curl -X POST "http://127.0.0.1:8000/consolidated-responses" \
     -H "Content-Type: application/json" \
     -d '{"end_date": "2025-09-20T23:59:59Z"}'
```

## Error Testing

### 5. Test Invalid Date Format
```bash
curl -X POST "http://127.0.0.1:8000/consolidated-responses" \
     -H "Content-Type: application/json" \
     -d '{"start_date": "invalid-date"}'
```

### 6. Test Invalid Date Range (start > end)
```bash
curl -X POST "http://127.0.0.1:8000/consolidated-responses" \
     -H "Content-Type: application/json" \
     -d '{"start_date": "2025-09-21T00:00:00Z", "end_date": "2025-09-20T00:00:00Z"}'
```

## Windows Command Prompt Versions

### 1. Get All Submissions (Windows)
```cmd
curl -X POST "http://127.0.0.1:8000/consolidated-responses" -H "Content-Type: application/json" -d "{}"
```

### 2. Get Submissions from Today (Windows)
```cmd
curl -X POST "http://127.0.0.1:8000/consolidated-responses" -H "Content-Type: application/json" -d "{\"start_date\": \"2025-09-20T00:00:00Z\"}"
```

### 3. Get Submissions for Date Range (Windows)
```cmd
curl -X POST "http://127.0.0.1:8000/consolidated-responses" -H "Content-Type: application/json" -d "{\"start_date\": \"2025-09-20T00:00:00Z\", \"end_date\": \"2025-09-20T23:59:59Z\"}"
```

## Advanced Usage with Verbose Output

### Get All Submissions with Detailed Response Info
```bash
curl -X POST "http://127.0.0.1:8000/consolidated-responses" \
     -H "Content-Type: application/json" \
     -d '{}' \
     -w "\nStatus Code: %{http_code}\nResponse Time: %{time_total}s\nResponse Size: %{size_download} bytes\n" \
     -v
```

### Pretty Print JSON Response (requires jq)
```bash
curl -X POST "http://127.0.0.1:8000/consolidated-responses" \
     -H "Content-Type: application/json" \
     -d '{}' \
     -s | jq '.'
```

### Save Response to File
```bash
curl -X POST "http://127.0.0.1:8000/consolidated-responses" \
     -H "Content-Type: application/json" \
     -d '{}' \
     -o consolidated_responses.json
```

## Testing Different Date Formats

### ISO 8601 with Timezone
```bash
curl -X POST "http://127.0.0.1:8000/consolidated-responses" \
     -H "Content-Type: application/json" \
     -d '{"start_date": "2025-09-20T05:00:00Z", "end_date": "2025-09-20T10:00:00Z"}'
```

### Recent Submissions (Last Hour)
```bash
# Note: You'll need to replace with actual current timestamp
curl -X POST "http://127.0.0.1:8000/consolidated-responses" \
     -H "Content-Type: application/json" \
     -d '{"start_date": "2025-09-20T08:00:00Z"}'
```

## Quick Test Commands

### Test Server Health First
```bash
curl -X GET "http://127.0.0.1:8000/health"
```

### Test API Root
```bash
curl -X GET "http://127.0.0.1:8000/"
```

### Test with Timeout
```bash
curl -X POST "http://127.0.0.1:8000/consolidated-responses" \
     -H "Content-Type: application/json" \
     -d '{}' \
     --max-time 30
```

## Response Format

The API returns a JSON response with the following structure:
```json
{
  "status": "success",
  "message": "Successfully retrieved X submissions",
  "query_metadata": {
    "query_timestamp": "2025-09-20T10:30:45.123Z",
    "start_date_filter": "2025-09-20T00:00:00Z",
    "end_date_filter": "2025-09-20T23:59:59Z",
    "directory_exists": true,
    "total_files_found": 41,
    "files_processed": 5,
    "files_skipped": 36,
    "processing_time_ms": 45
  },
  "submissions": [...],
  "total_count": 5
}
```
