# Submit Selection API Documentation

## Overview

The Submit Selection API endpoint (`/submit-selection`) receives user selections from the Enhanced Defect Analysis Page, including the selected defect and associated root cause-corrective action pairs. It validates the data, saves it to a JSON file, and returns a confirmation response.

## Implementation Details

### Endpoint
- **URL**: `POST /submit-selection`
- **Content-Type**: `application/json`
- **Response Model**: `SubmitSelectionResponse`

### Features
- ✅ Complete request validation using Pydantic models
- ✅ ISO 8601 timestamp validation
- ✅ Business logic validation (unique pair IDs, primary pairs, etc.)
- ✅ Automatic JSON file saving with timestamp-based naming
- ✅ Comprehensive error handling
- ✅ Proper HTTP status codes and error responses

### File Storage
- **Directory**: `user_responses/` (created automatically if not exists)
- **Filename Format**: `submit_YYYYMMDDHHMMSS.json`
- **Encoding**: UTF-8 with proper Unicode support
- **Format**: Pretty-printed JSON with 2-space indentation

### Validation Rules

#### Required Fields
- `timestamp` - Must be valid ISO 8601 format
- `original_input` - The original user input text
- `selected_defect` - Complete defect object with all sub-fields
- `selected_pairs` - Non-empty array of root cause-corrective action pairs
- `analysis_metadata` - Complete metadata object with all sub-fields

#### Optional Fields
- `remarks` - Optional string, max 500 characters, automatically trimmed

#### Business Logic Validation
- `confidence_score` must be between 0.0 and 1.0
- `selected_pairs` must contain at least one pair
- `pair_id` must be unique within the selected_pairs array
- `total_pairs_selected` must match actual array length
- At least one pair should have both `is_primary: true` for root_cause and corrective_action

### Response Formats

#### Success Response (200 OK)
```json
{
  "status": "success",
  "message": "Selection submitted successfully",
  "submission_id": "submit_20240115103045",
  "timestamp": "2024-01-15T10:30:45.123Z",
  "processed_pairs": 2
}
```

#### Validation Error (422 Unprocessable Entity)
```json
{
  "detail": [
    {
      "loc": ["selected_pairs"],
      "msg": "At least one pair should have both is_primary: true",
      "type": "value_error"
    }
  ]
}
```

#### Bad Request Error (400 Bad Request)
```json
{
  "detail": {
    "status": "error",
    "error_code": "INVALID_REQUEST",
    "message": "Invalid timestamp format. Must be ISO 8601 format.",
    "details": {
      "field": "timestamp",
      "issue": "Invalid ISO 8601 format"
    }
  }
}
```

#### Internal Server Error (500 Internal Server Error)
```json
{
  "detail": {
    "status": "error",
    "error_code": "INTERNAL_ERROR",
    "message": "Internal server error occurred",
    "timestamp": "2024-01-15T10:30:45.123Z"
  }
}
```

## Data Models

### Main Request Model
```python
class SubmitSelectionRequest(BaseModel):
    timestamp: str
    original_input: str
    remarks: Optional[str] = None  # max 500 chars
    selected_defect: SelectedDefect
    selected_pairs: List[SelectedPair]  # min 1 item
    analysis_metadata: AnalysisMetadata
```

### Nested Models
- `SelectedDefect`: Contains defect code, text, confidence score, mapping status, curator action
- `SelectedPair`: Contains root cause and corrective action objects plus pair ID
- `RootCause`: Contains code, text, and is_primary flag
- `CorrectiveAction`: Contains code, text, and is_primary flag
- `AnalysisMetadata`: Contains agent name, config path, submission source, total pairs count

## Testing

Use the provided test script to verify the endpoint:

```bash
python test_submit_selection.py
```

The test script covers:
- ✅ Valid request submission
- ✅ Invalid timestamp format
- ✅ Empty selected_pairs validation
- ✅ Mismatched total_pairs_selected validation
- ✅ File saving verification

## Integration Notes

### Frontend Integration
The endpoint is designed to be called from the `handleSubmitSelection` function in `EnhancedDefectAnalysisPage.js`:

```javascript
const response = await fetch('/submit-selection', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': 'true'
  },
  body: JSON.stringify(submissionData)
});
```

### Error Handling
The frontend should handle different HTTP status codes:
- `200`: Success - show confirmation message
- `400`: Bad request - show validation error
- `422`: Validation error - show field-specific errors
- `500`: Server error - show generic error message

### File Management
- Files are saved in the `user_responses/` directory
- Each submission creates a new file with timestamp-based naming
- Files contain the original request data plus submission metadata
- No automatic cleanup - implement as needed for your use case

## Security Considerations

- ✅ Input validation prevents injection attacks
- ✅ Text fields are properly handled for XSS prevention
- ✅ File paths are safely constructed using pathlib
- ✅ Error messages don't expose sensitive information
- ⚠️ Consider implementing rate limiting for production use
- ⚠️ Consider authentication/authorization as needed

## Performance Notes

- Response time: < 1 second for normal requests
- File I/O is synchronous but fast for JSON data
- Memory usage is minimal for typical request sizes
- Consider async file I/O for high-volume scenarios

## Example Usage

See the test script `test_submit_selection.py` for complete examples of valid and invalid requests.
