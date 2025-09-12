# Google Models Listing Program

This program lists all available Google models using multiple approaches based on the latest technical documentation from Google's Gen AI SDK.

## Features

- **Multiple SDK Support**: Uses both the new Google Gen AI SDK and LangChain integration
- **Comprehensive Listing**: Lists models with detailed information including token limits and supported actions
- **Error Handling**: Robust error handling with detailed logging
- **Multiple Output Formats**: Console table display and JSON export
- **Async Support**: Both synchronous and asynchronous model listing

## Installation

### Option 1: Install specific requirements
```bash
pip install -r google_models_requirements.txt
```

### Option 2: Install individual packages
```bash
# New unified Google Gen AI SDK (recommended)
pip install google-genai

# LangChain integration (for compatibility)
pip install langchain-google-genai

# HTTP clients
pip install aiohttp requests

# Utilities
pip install python-dotenv
```

## Setup

1. **Get a Google API Key**:
   - Go to [Google AI Studio](https://aistudio.google.com/)
   - Create a new API key
   - Or use your existing Gemini API key

2. **Set Environment Variable**:
   ```bash
   # Windows
   set GOOGLE_API_KEY=your_api_key_here
   # or
   set GEMINI_API_KEY=your_api_key_here

   # Linux/Mac
   export GOOGLE_API_KEY=your_api_key_here
   # or
   export GEMINI_API_KEY=your_api_key_here
   ```

3. **Or create a .env file**:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

## Usage

### Basic Usage
```bash
python list_google_models.py
```

### Using Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install requirements
pip install -r google_models_requirements.txt

# Run the program
python list_google_models.py
```

## Output

The program will:

1. **Display models in console tables** for each method:
   - Google Gen AI SDK (Synchronous)
   - Google Gen AI SDK (Asynchronous)
   - LangChain Google GenAI
   - Direct API Calls

2. **Save detailed results to JSON** file with timestamp

3. **Generate log file** with detailed execution information

4. **Show summary** with total unique models found

## Sample Output

```
Google Models Listing Program
==================================================

================================================================================
GOOGLE GEN AI SDK (SYNCHRONOUS)
================================================================================
Model Name                               Version         SDK                 
--------------------------------------------------------------------------------
gemini-2.5-flash                        001             google-genai        
gemini-2.5-pro                          001             google-genai        
gemini-2.0-flash                        001             google-genai        
imagen-3.0-generate-002                  002             google-genai        
veo-2.0-generate-001                     001             google-genai        
--------------------------------------------------------------------------------
Total models: 5

================================================================================
SUMMARY
================================================================================
Total unique models found: 15
Methods that returned results: 4
Results saved to: google_models_20250826_143022.json
Log file: google_models_list_20250826_143022.log
```

## Model Information Included

For each model, the program retrieves:

- **Name**: Full model identifier
- **Display Name**: Human-readable name
- **Description**: Model description
- **Version**: Model version
- **Input Token Limit**: Maximum input tokens
- **Output Token Limit**: Maximum output tokens
- **Supported Actions**: Available operations (generate, embed, etc.)
- **SDK**: Which SDK/method was used to retrieve the information

## Troubleshooting

### Common Issues

1. **"No API key found"**:
   - Ensure you've set the `GOOGLE_API_KEY` or `GEMINI_API_KEY` environment variable
   - Check that the API key is valid and active

2. **"404 models/model-name is not found"**:
   - This error occurs when using an incorrect model name
   - Use this program to get the correct model names
   - Refer to the generated JSON file for exact model identifiers

3. **Import errors**:
   - Install missing packages: `pip install -r google_models_requirements.txt`
   - Ensure you're using the correct virtual environment

4. **API rate limits**:
   - The program includes proper error handling for rate limits
   - Check the log file for detailed error information

### Recommended Models (as of latest documentation)

- **General Text & Multimodal**: `gemini-2.5-flash`
- **Coding & Complex Reasoning**: `gemini-2.5-pro`
- **Image Generation**: `imagen-3.0-generate-002`
- **Video Generation**: `veo-2.0-generate-001`

### Deprecated Models to Avoid

- `gemini-1.5-flash` (and variants)
- `gemini-1.5-pro`
- `gemini-pro`

## Files Generated

- `google_models_YYYYMMDD_HHMMSS.json`: Complete model data in JSON format
- `google_models_list_YYYYMMDD_HHMMSS.log`: Detailed execution log

## Technical Details

The program uses four different approaches to ensure comprehensive model discovery:

1. **Google Gen AI SDK (Sync)**: `client.models.list()`
2. **Google Gen AI SDK (Async)**: `client.aio.models.list()`
3. **LangChain Integration**: `genai.list_models()`
4. **Direct API**: `https://generativelanguage.googleapis.com/v1beta/models`

This multi-approach strategy ensures you get the most complete and up-to-date list of available models.
