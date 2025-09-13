# PepGenX API Integration Documentation

## Overview

This document describes the integration of PepGenX API with secure configuration management using environment variables and dynamic OKTA token loading.

## Configuration Setup

### Environment Variables

The following environment variables have been added to the `.env` file:

```bash
# ============================================================================
# PEPGENX API CONFIGURATION
# ============================================================================
# PepGenX API endpoint and authentication details
PEPGENX_API_URL=https://apim-na.qa.mypepsico.com/cgf/pepgenx/v2/llm/aws-anthropic/generate-response
PEPGENX_PROJECT_ID=1d72f25f-d1db-4f2c-a295-412aae4fce2c
PEPGENX_TEAM_ID=6ad0c340-ce99-477c-9bff-d7e63bfa1104
PEPGENX_API_KEY=7079e28e-0f63-480d-b03e-85fe66359cfe
```

### OKTA Token Configuration

The system dynamically loads the authorization token from the `okta_token.json` file:

```json
{
  "access_token": "eyJraWQiOiJpUnFMWW9LMVZxU1lqRlNyWl9uZktDQThRV0J5blRQOFlsVDRUNnZ2UGwwIiwiYWxnIjoiUlMyNTYifQ...",
  "expires_at": 1757750162
}
```

## Security Benefits

1. **Separation of Concerns**: Sensitive data is separated from code
2. **Environment-Specific Configuration**: Different environments can use different configurations
3. **Dynamic Token Loading**: Tokens are loaded fresh from the token file on each execution
4. **Version Control Safety**: Sensitive data is not committed to version control

## Usage

### Basic Usage

```python
from scripts.antropic_test import main

# Run the basic test
main()
```

### Advanced Usage with Examples

```python
from scripts.pepgenx_example import main

# Run multiple examples
main()
```

## API Request Structure

### Headers

The API requires the following headers:

- `project_id`: Project identifier from environment variables
- `team_id`: Team identifier from environment variables  
- `x-pepgenx-apikey`: API key from environment variables
- `Authorization`: Bearer token loaded dynamically from OKTA token file
- `cookie`: Session cookies for authentication

### Payload

```python
payload = {
    "generation_model": "claude-3-7-sonnet",
    "custom_prompt": "Your prompt here",
    "system_prompt": 1
}
```

## Error Handling

The implementation includes comprehensive error handling for:

1. **Missing Environment Variables**: Validates all required configuration
2. **Token File Issues**: Handles missing or invalid token files
3. **API Request Errors**: Catches and reports HTTP request failures
4. **JSON Parsing Errors**: Handles malformed responses

## File Structure

```
scripts/
├── antropic_test.py      # Main test script with environment configuration
├── pepgenx_example.py    # Example script with multiple use cases
.env                      # Environment configuration file
okta_token.json          # Dynamic OKTA token file
```

## Dependencies

The following Python packages are required:

- `requests`: For HTTP API calls
- `python-dotenv`: For loading environment variables
- `json`: For parsing JSON responses (built-in)
- `pathlib`: For file path handling (built-in)

## Cross-Platform Compatibility

The implementation is designed to work on both Windows and macOS:

- Uses `pathlib.Path` for cross-platform file path handling
- Handles encoding issues with explicit UTF-8 encoding
- Compatible with both Windows and Unix-style path separators

## Best Practices

1. **Never commit sensitive data**: Keep `.env` file in `.gitignore`
2. **Regular token refresh**: Ensure OKTA tokens are refreshed before expiration
3. **Error logging**: Monitor API responses for debugging
4. **Environment validation**: Always validate required environment variables

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   - Check that all PEPGENX_* variables are set in `.env`
   - Ensure `.env` file is in the project root

2. **Token File Not Found**
   - Verify `okta_token.json` exists in the project root
   - Check that the token file contains valid JSON

3. **API Authentication Errors**
   - Verify the OKTA token is not expired
   - Check that all API credentials are correct

### Debug Mode

To enable verbose logging, modify the scripts to include debug information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Example Output

```
Successfully loaded access token from: c:\JK\dev\repo\jk-agents\okta_token.json
Making API request to: https://apim-na.qa.mypepsico.com/cgf/pepgenx/v2/llm/aws-anthropic/generate-response
Using project_id: 1d72f25f-d1db-4f2c-a295-412aae4fce2c
Using team_id: 6ad0c340-ce99-477c-9bff-d7e63bfa1104
Payload: {
  "generation_model": "claude-3-7-sonnet",
  "custom_prompt": "Bird dancing in the nest",
  "system_prompt": 1
}

Response Status Code: 200
Response JSON: {
  "response": "Generated content here..."
}
```
