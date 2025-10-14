# File Reference System Fix - Quick Summary

## Problem
The visiting card extractor was not able to access uploaded files. Files were stored correctly but the multimodal OCR agent couldn't retrieve them.

## Root Causes Identified

1. **Missing `@tool` Decorator** - File retrieval functions weren't registered as LangChain tools
2. **Wrong Model Choice** - Gemini has inconsistent function calling support  
3. **Unclear Prompts** - Agent wasn't explicitly told to use tools

## Changes Made

### 1. `tools/file_retrieval_tools.py`
```python
# Added LangChain tool decorator
from langchain_core.tools import tool

@tool  # ← Added this
def get_file_content(reference_id: str) -> Dict[str, Any]:
    """Retrieve file content by reference ID."""
    # ... implementation

@tool  # ← Added this
def list_available_files(thread_id: Optional[str] = None) -> Dict[str, Any]:
    """List all files available in the current thread context."""
    # ... implementation

@tool  # ← Added this
def get_file_metadata(reference_id: str) -> Dict[str, Any]:
    """Get metadata about a file without retrieving its content."""
    # ... implementation

# Added tool loader for python_tools config
def load_tools_from_config(tool_names: List[str]) -> List[Any]:
    available_tools = {
        "get_file_content": get_file_content,
        "list_available_files": list_available_files,
        "get_file_metadata": get_file_metadata
    }
    return [available_tools[name] for name in tool_names if name in available_tools]
```

### 2. `config/visiting_card_extractor.yaml`

**Changed Model:**
```yaml
# Before:
multimodal: "google:gemini-2.5-flash-lite"

# After:
multimodal: "azure_openai:gpt-4o"  # Better function calling + vision
```

**Enhanced Prompt:**
```yaml
**FILE ACCESS INSTRUCTIONS:**
YOU MUST use the file retrieval tools to access image files:

1. **Check User Input**: Look for "**ATTACHED FILES (Reference IDs):**" section
2. **Call list_available_files()**: Use this tool first to see all available files  
3. **Call get_file_content(reference_id)**: For EACH image, call this tool with the reference_id
4. **Process Vision**: You'll receive base64-encoded image content - analyze it

**CRITICAL INSTRUCTIONS:**
- DO NOT ask users to upload files - they are ALREADY uploaded!
- DO NOT generate fake/example data - ALWAYS retrieve and analyze actual files
- MUST use the get_file_content tool for EACH reference_id provided
- The tool returns a dictionary with 'content' field containing base64 image data
- After retrieving file content, analyze the image to extract text, logos, and layout
```

## How It Works Now

### Architecture Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. API Layer (api.py)                                       │
│    - User uploads files via multipart/form-data             │
│    - Files stored in FileStorageManager (in-memory)         │
│    - Each file gets unique reference_id (e.g., file_abc123) │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Only metadata passed to agent
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Enhanced Input (context)                                 │
│    **ATTACHED FILES (Reference IDs):**                      │
│    - card.jpg (reference_id: file_abc123, size: 200KB)     │
│                                                              │
│    **IMPORTANT**: Use get_file_content(reference_id) tool  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Agent sees reference IDs
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Agent Decision (multimodal_ocr_agent)                    │
│    - Agent reads: "I see file_abc123 is attached"          │
│    - Agent decides: "I need to retrieve this file"         │
│    - Agent calls: get_file_content("file_abc123")          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Tool execution
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Tool Retrieval (file_retrieval_tools.py)                │
│    @tool                                                     │
│    def get_file_content(reference_id):                      │
│        file_manager = get_file_storage_manager()            │
│        file_ref = file_manager.get_file(reference_id)       │
│        return {                                              │
│            "content": file_ref.get_base64_content(),  ←──── │
│            "mime_type": "image/jpeg"                         │
│        }                                                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Base64 image returned
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Vision Processing (GPT-4o)                               │
│    - Agent receives base64 image content                    │
│    - GPT-4o's vision API analyzes the image                 │
│    - Extracts text, logos, layout information               │
│    - Returns structured OCR data                            │
└─────────────────────────────────────────────────────────────┘
```

## Key Benefits

### ✅ Memory Efficient
- Only metadata in context (not full file content)
- Files stay in FileStorageManager
- Large files don't bloat conversation history

### ✅ Tool-Based Access
- Files retrieved on-demand via function calling
- Multiple agents can access same files
- Proper error handling and logging

### ✅ Reliable Function Calling
- GPT-4o has excellent tool calling support
- Tools properly registered with @tool decorator
- Explicit prompts guide correct usage

## Testing

```bash
# Test with single image
curl -X POST http://localhost:8000/v1/query \
  -F "question=Extract contact info" \
  -F "file=@card.jpg" \
  -F "config_name=visiting_card_extractor.yaml"

# Test with multiple images
curl -X POST http://localhost:8000/v1/query \
  -F "question=Extract complete data including company research" \
  -F "file=@card_front.jpg" \
  -F "file=@card_back.jpg" \
  -F "config_name=visiting_card_extractor.yaml"
```

**Expected in logs:**
```
✅ Loaded 3 Python function tools
✅ Stored file card.jpg with reference_id=file_abc123
✅ Retrieved file content: file_abc123 (card.jpg)
✅ Tool call: get_file_content with args: {'reference_id': 'file_abc123'}
```

## Files Modified

1. **tools/file_retrieval_tools.py** - Added @tool decorators
2. **config/visiting_card_extractor.yaml** - Changed to GPT-4o, enhanced prompts  
3. **fixes_docs/file_reference_system_fix_20250930.md** - Full documentation

## Critical Insight

**Never embed file content in context!**  
Only pass reference IDs → Agents use tools to retrieve → Keeps context lean and efficient.

This is the correct architecture for handling files in multi-agent systems.