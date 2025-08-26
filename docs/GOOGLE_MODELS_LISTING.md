# Google Models Listing Program

A comprehensive program to list all available Google models using the latest technical documentation and multiple SDK approaches.

## Overview

This program addresses the common issue of using incorrect model names (like `gemini-2.5-flash-lite-001`) that result in 404 errors. It provides an authoritative list of all available Google models using multiple approaches to ensure completeness.

## Error Context

The program was created to solve this common error:
```
[WARNING] langchain_google_genai.chat_models: Retrying langchain_google_genai.chat_models._achat_with_retry.<locals>._achat_with_retry in 8.0 seconds as it raised NotFound: 404 models/gemini-2.5-flash-lite-001 is not found for API version v1beta, or is not supported for generateContent. Call ListModels to see the list of available models and their supported methods.
```

## Features

### Multiple SDK Support
- **Google Gen AI SDK** (new unified SDK) - Synchronous and Asynchronous
- **LangChain Google GenAI** integration
- **Direct API calls** to Google's REST endpoints

### Comprehensive Information
For each model, the program retrieves:
- Full model identifier (e.g., `models/gemini-2.5-flash`)
- Display name and description
- Version information
- Token limits (input/output)
- Supported actions/methods
- SDK source

### Robust Error Handling
- API key validation
- Rate limit handling
- Network error recovery
- Detailed logging

### Multiple Output Formats
- Console table display
- JSON export with timestamps
- Detailed log files

## Files

### Main Program
- `list_google_models.py` - Main program requiring valid API key
- `test_google_models_demo.py` - Demo version with sample data

### Configuration
- `google_models_requirements.txt` - Specific requirements
- `GOOGLE_MODELS_USAGE.md` - Detailed usage instructions

### Documentation
- `docs/GOOGLE_MODELS_LISTING.md` - This file

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r google_models_requirements.txt
   ```

2. **Set API key**:
   ```bash
   # Windows
   set GOOGLE_API_KEY=your_api_key_here
   
   # Linux/Mac
   export GOOGLE_API_KEY=your_api_key_here
   ```

3. **Run the program**:
   ```bash
   python list_google_models.py
   ```

4. **View demo** (no API key required):
   ```bash
   python test_google_models_demo.py
   ```

## Current Recommended Models

Based on the latest Google documentation:

### Text and Multimodal
- **`gemini-2.5-flash`** - Fast and efficient for general tasks
- **`gemini-2.5-pro`** - Advanced for coding and complex reasoning

### Specialized Models
- **`imagen-3.0-generate-002`** - Image generation
- **`veo-2.0-generate-001`** - Video generation

### Acceptable Alternatives
- `gemini-2.0-flash` - Previous generation fast model
- `gemini-2.0-pro` - Previous generation advanced model

### Deprecated Models (Avoid)
- `gemini-1.5-flash` and variants
- `gemini-1.5-pro`
- `gemini-pro`

## Technical Implementation

### SDK Approaches

1. **Google Gen AI SDK (Recommended)**
   ```python
   from google import genai
   client = genai.Client(api_key=api_key)
   for model in client.models.list():
       print(model.name)
   ```

2. **LangChain Integration**
   ```python
   import google.generativeai as genai
   genai.configure(api_key=api_key)
   for model in genai.list_models():
       print(model.name)
   ```

3. **Direct API Calls**
   ```python
   url = "https://generativelanguage.googleapis.com/v1beta/models"
   response = requests.get(url, params={'key': api_key})
   ```

### Error Handling Strategy

The program implements comprehensive error handling:
- API key validation and expiration detection
- Network timeout and retry logic
- Rate limit handling
- Graceful degradation when SDKs are unavailable

### Output Format

#### Console Display
```
================================================================================
GOOGLE GEN AI SDK (SYNCHRONOUS)
================================================================================
Model Name                               Version         SDK                 
--------------------------------------------------------------------------------
gemini-2.5-flash                        001             google-genai        
gemini-2.5-pro                          001             google-genai        
--------------------------------------------------------------------------------
Total models: 2
```

#### JSON Export
```json
{
  "google_genai_sdk": [
    {
      "name": "models/gemini-2.5-flash",
      "display_name": "Gemini 2.5 Flash",
      "description": "Fast and efficient model",
      "version": "001",
      "input_token_limit": 1048576,
      "output_token_limit": 8192,
      "supported_actions": ["generateContent", "embedContent"],
      "sdk": "google-genai"
    }
  ]
}
```

## Troubleshooting

### Common Issues

1. **API Key Expired**
   - Error: `API key expired. Please renew the API key.`
   - Solution: Get a new API key from [Google AI Studio](https://aistudio.google.com/)

2. **Model Not Found (404)**
   - Error: `404 models/model-name is not found`
   - Solution: Use this program to get correct model names

3. **Import Errors**
   - Error: `No module named 'google.genai'`
   - Solution: `pip install google-genai`

4. **Rate Limits**
   - Error: `429 Too Many Requests`
   - Solution: The program includes automatic retry logic

### Validation

To validate the program works correctly:

1. Run the demo version: `python test_google_models_demo.py`
2. Check the generated JSON file for expected structure
3. Verify log files contain detailed execution information

## Integration

### Using Results in Your Code

```python
import json

# Load the generated model list
with open('google_models_20250826_101552.json', 'r') as f:
    models = json.load(f)

# Get all available model names
model_names = []
for method_models in models.values():
    for model in method_models:
        model_names.append(model['name'])

# Use correct model name
correct_model = "models/gemini-2.5-flash"  # From the list
```

### LangChain Integration

```python
from langchain_google_genai import ChatGoogleGenerativeAI

# Use correct model name from the program output
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",  # Correct name without 'models/' prefix
    google_api_key=api_key
)
```

## Maintenance

The program should be run periodically to:
- Detect new model releases
- Identify deprecated models
- Update token limits and capabilities
- Verify API changes

Recommended frequency: Monthly or when encountering new model errors.

## Support

For issues or questions:
1. Check the generated log files for detailed error information
2. Verify API key validity at [Google AI Studio](https://aistudio.google.com/)
3. Review the latest Google Gen AI SDK documentation
4. Run the demo version to verify program functionality
