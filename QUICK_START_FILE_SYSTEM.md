# Quick Start - File Reference System

## Bug Fixed ✅

**Issue:** `AttributeError: module 'datetime' has no attribute 'now'`

**Root Cause:** Line 1221 in `api.py` had `import datetime` inside the `root()` function, which shadowed the `datetime` class imported at the top of the file.

**Fix:** Removed the redundant `import datetime` statement from the root endpoint function.

**File Modified:** `/Users/A80997271/Documents/projects/jk-agents-framework/api.py` (line 1221)

## How to Test

### Step 1: Start API Server

Open a terminal and run:

```bash
cd /Users/A80997271/Documents/projects/jk-agents-framework
python api.py
```

**Expected output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Test the File Upload

Open **another terminal** and run:

```bash
cd /Users/A80997271/Documents/projects/jk-agents-framework
bash run_complete_test.sh
```

**OR** run the curl command directly:

```bash
curl --location 'http://localhost:8000/v1/query' \
  --form 'question="Extract complete data including company research"' \
  --form 'config_name="visiting_card_extractor.yaml"' \
  --form 'file=@"/Users/A80997271/Downloads/WhatsApp Image 2025-09-30 at 09.36.21.jpeg"' \
  --form 'file=@"/Users/A80997271/Downloads/WhatsApp Image 2025-09-30 at 09.36.21 (1).jpeg"'
```

### Step 3: Verify Success

**What to look for:**

✅ **Files stored with reference IDs:**
```json
{
  "metadata": {
    "files_uploaded": 2,
    "file_info": [
      {
        "reference_id": "file_abc123def456",
        "filename": "WhatsApp Image 2025-09-30 at 09.36.21.jpeg",
        "size_bytes": 125684,
        "mime_type": "image/jpeg"
      }
    ]
  }
}
```

✅ **OCR agent successfully processes images** (NOT "Please provide the image")

✅ **Extracted data includes:**
- Contact information (name, title, company)
- Phone numbers (normalized to E.164)
- Email addresses (validated)
- Company research data

## Troubleshooting

### Issue: API Server Won't Start

**Check:**
```bash
# Make sure no other process is using port 8000
lsof -ti:8000 | xargs kill -9

# Try starting again
python api.py
```

### Issue: Files Not Found

**Check file paths:**
```bash
ls -lh "/Users/A80997271/Downloads/WhatsApp Image 2025-09-30 at 09.36.21.jpeg"
ls -lh "/Users/A80997271/Downloads/WhatsApp Image 2025-09-30 at 09.36.21 (1).jpeg"
```

If files don't exist, update the paths in your curl command.

### Issue: OCR Agent Says "Please provide the image"

**This means files are NOT being retrieved.**

**Debug steps:**
1. Check logs for "Stored file with reference_id="
2. Check if OCR agent has file retrieval tools configured
3. Verify agent prompt includes FILE ACCESS PRIORITY section

**Check configuration:**
```bash
# Verify OCR agent has file tools
grep -A5 "python_tools:" config/visiting_card_extractor.yaml
```

**Should see:**
```yaml
python_tools:
  file_access:
    module_path: "tools.file_retrieval_tools"
    tool_names: ["get_file_content", "list_available_files", "get_file_metadata"]
```

### Issue: Connection Refused

**The API server isn't running.**

```bash
# Check if running
curl http://localhost:8000/

# If not, start it
python api.py
```

## What Should Happen (Success Flow)

### 1. Files Uploaded
```
INFO:api:[12345678] Processing 2 uploaded files
INFO:api:Stored file WhatsApp Image... with reference_id=file_abc123
INFO:api:Stored file WhatsApp Image... with reference_id=file_def456
```

### 2. Reference IDs in Context
```
Enhanced input includes:
**ATTACHED FILES (Reference IDs):**
- WhatsApp Image... (reference_id: file_abc123, type: image/jpeg, size: 125684 bytes)
- WhatsApp Image... (reference_id: file_def456, type: image/jpeg, size: 98234 bytes)
```

### 3. OCR Agent Retrieves Files
```
INFO:planner_executor:Step ocr_extraction started
[OCR agent sees reference IDs]
[OCR agent calls: get_file_content("file_abc123")]
[OCR agent receives base64-encoded image data]
[OCR agent performs vision analysis]
```

### 4. OCR Results Returned
```json
{
  "raw_text": "John Smith\nSenior Software Engineer\nTechCorp Solutions...",
  "structured_fields": {
    "name": "John Smith",
    "job_title": "Senior Software Engineer",
    "company": "TechCorp Solutions",
    ...
  }
}
```

### 5. Remaining Agents Process
- Contact Parser: Normalizes phone/email/URLs
- Company Research: Searches Brave for company info
- Aggregator: Combines all data into final JSON

### 6. Final Response
```json
{
  "success": true,
  "response": "<structured JSON with all extracted data>",
  "metadata": {
    "total_steps": 4,
    "files_uploaded": 2,
    "file_info": [...]
  }
}
```

## Quick Reference

### File Storage Manager
```python
from app.file_storage_manager import get_file_storage_manager

manager = get_file_storage_manager()

# Store file
ref_id = manager.store_file(filename, content, mime_type, thread_id)

# Retrieve file
file_ref = manager.get_file(ref_id)
content = file_ref.content

# List thread files
files = manager.list_files(thread_id)

# Stats
stats = manager.get_stats()
```

### File Retrieval Tools (for agents)
```python
# List available files
list_available_files()
# Returns: [{reference_id, filename, mime_type, size}...]

# Get file content
get_file_content("file_abc123")
# Returns: {success, content, content_type, ...}

# Get metadata only
get_file_metadata("file_abc123")
# Returns: {reference_id, filename, mime_type, size, uploaded_at}
```

## Performance Expectations

| Operation | Expected Time |
|-----------|---------------|
| File upload (2 images, ~250KB total) | < 1 second |
| File storage (in memory) | < 10ms |
| File retrieval by agent | < 10ms |
| OCR processing (Google Gemini) | 5-15 seconds |
| Contact normalization | 2-5 seconds |
| Company research (Brave Search) | 10-30 seconds |
| Data aggregation | 1-3 seconds |
| **Total workflow** | **20-50 seconds** |

## Success Indicators

✅ No "Please provide the image" messages  
✅ Files stored with reference IDs in metadata  
✅ OCR results contain actual text from images  
✅ Contact data normalized (E.164 phones, validated emails)  
✅ Company research completed with sources  
✅ Final JSON matches schema  

## Next Steps

1. ✅ **Test with your images** - Run the complete test
2. ✅ **Verify OCR works** - Check for actual extracted text
3. ✅ **Review results** - Validate JSON structure
4. 📝 **Document findings** - Note any issues
5. 🚀 **Production use** - Deploy if tests pass

## Support

- **Documentation**: `docs/FILE_REFERENCE_SYSTEM.md`
- **Implementation**: `docs/FILE_REFERENCE_IMPLEMENTATION_SUMMARY.md`
- **Test Suite**: `test_file_reference_system.py`
- **Config Example**: `config/visiting_card_extractor.yaml`

---

**File Reference System Status:** ✅ READY FOR TESTING
