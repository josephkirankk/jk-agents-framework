# Google Models Listing Program

**Solve the "404 model not found" error once and for all!**

This comprehensive program lists all available Google models using the latest technical documentation and multiple SDK approaches. No more guessing model names or getting 404 errors.

## 🚀 Quick Start

### Windows Users
```batch
run_google_models_list.bat
```

### Linux/Mac Users
```bash
./run_google_models_list.sh
```

### Manual Installation
```bash
# Install dependencies
pip install google-genai aiohttp requests python-dotenv

# Set API key
export GOOGLE_API_KEY=your_api_key_here

# Run program
python list_google_models.py
```

## 🎯 Problem Solved

**Before**: Getting this error?
```
[WARNING] NotFound: 404 models/gemini-2.5-flash-lite-001 is not found
```

**After**: Get the exact model names:
```
✅ gemini-2.5-flash
✅ gemini-2.5-pro  
✅ imagen-3.0-generate-002
✅ veo-2.0-generate-001
```

## 📋 What You Get

### 🔍 Comprehensive Model Discovery
- **4 different approaches** to ensure complete coverage
- **Real-time data** from Google's APIs
- **Detailed model information** including token limits

### 📊 Multiple Output Formats
- **Console tables** for quick viewing
- **JSON files** for programmatic use
- **Detailed logs** for troubleshooting

### 🛡️ Robust Error Handling
- API key validation
- Network error recovery
- Rate limit handling
- Graceful degradation

## 📁 Files Overview

| File | Purpose |
|------|---------|
| `list_google_models.py` | Main program (requires API key) |
| `test_google_models_demo.py` | Demo with sample data (no API key) |
| `run_google_models_list.bat` | Windows launcher script |
| `run_google_models_list.sh` | Linux/Mac launcher script |
| `google_models_requirements.txt` | Specific dependencies |
| `GOOGLE_MODELS_USAGE.md` | Detailed usage guide |
| `docs/GOOGLE_MODELS_LISTING.md` | Technical documentation |

## 🎯 Current Recommended Models

Based on latest Google documentation:

### 🚀 **Primary Models**
- **`gemini-2.5-flash`** - General text & multimodal tasks
- **`gemini-2.5-pro`** - Coding & complex reasoning

### 🎨 **Specialized Models**  
- **`imagen-3.0-generate-002`** - Image generation
- **`veo-2.0-generate-001`** - Video generation

### ⚠️ **Deprecated (Avoid)**
- ❌ `gemini-1.5-flash` and variants
- ❌ `gemini-1.5-pro`
- ❌ `gemini-pro`

## 🔧 Technical Approaches

The program uses **4 different methods** to ensure comprehensive coverage:

1. **Google Gen AI SDK** (Sync) - `client.models.list()`
2. **Google Gen AI SDK** (Async) - `client.aio.models.list()`
3. **LangChain Integration** - `genai.list_models()`
4. **Direct API Calls** - REST endpoints

## 📊 Sample Output

```
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
```

## 🔑 API Key Setup

1. **Get API Key**: Visit [Google AI Studio](https://aistudio.google.com/)
2. **Set Environment Variable**:
   ```bash
   # Windows
   set GOOGLE_API_KEY=your_api_key_here
   
   # Linux/Mac  
   export GOOGLE_API_KEY=your_api_key_here
   ```
3. **Or create .env file**:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

## 🚨 Troubleshooting

### No API Key?
Run the demo version: `python test_google_models_demo.py`

### API Key Expired?
Get a new one from [Google AI Studio](https://aistudio.google.com/)

### Import Errors?
Install dependencies: `pip install -r google_models_requirements.txt`

### 404 Model Errors?
Use the exact model names from the program output!

## 💡 Integration Examples

### LangChain Usage
```python
from langchain_google_genai import ChatGoogleGenerativeAI

# Use correct model name from program output
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",  # ✅ Correct name
    google_api_key=api_key
)
```

### Direct SDK Usage
```python
from google import genai

client = genai.Client(api_key=api_key)
response = client.models.generate_content(
    model="gemini-2.5-flash",  # ✅ Correct name
    contents="Hello, world!"
)
```

## 📈 Generated Files

After running, you'll get:
- `google_models_YYYYMMDD_HHMMSS.json` - Complete model data
- `google_models_list_YYYYMMDD_HHMMSS.log` - Execution log

## 🔄 Maintenance

Run this program:
- **Monthly** to catch new models
- **When getting 404 errors** to verify model names
- **Before major deployments** to ensure model availability

## 📚 Documentation

- **Quick Start**: This file
- **Detailed Usage**: `GOOGLE_MODELS_USAGE.md`
- **Technical Docs**: `docs/GOOGLE_MODELS_LISTING.md`

## ✨ Features

- ✅ **Multiple SDK support** (Google Gen AI, LangChain, Direct API)
- ✅ **Comprehensive error handling** with detailed logging
- ✅ **Windows & Linux support** with launcher scripts
- ✅ **Demo mode** for testing without API key
- ✅ **JSON export** for programmatic use
- ✅ **Real-time model discovery** from Google's APIs
- ✅ **Token limit information** for capacity planning
- ✅ **Supported actions** for each model

---

**Never get a "404 model not found" error again!** 🎉
