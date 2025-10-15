# Troubleshooting: No Files Being Uploaded

## Problem
API log shows: `files: 0` - No files are being uploaded to the system.

## Root Cause Analysis

Looking at your console output:
```
INFO:api:v1/query endpoint called with config: visiting_card_extractor.yaml, files: 0
```

**The issue is**: NO FILES WERE INCLUDED IN YOUR REQUEST!

The agent correctly reports:
```
No visiting card images or reference IDs were provided. OCR data extraction requires access to relevant files.
```

## Solution

### Method 1: Use the Test Script (RECOMMENDED)

I've created a test script for you. Use it like this:

```bash
# Navigate to project directory
cd /Users/A80997271/Documents/projects/jk-agents-framework

# Make sure you have your visiting card images
# Place them in the project directory or use full paths

# Run the test script
./test_visiting_card.sh card1.jpg card2.jpg
```

### Method 2: Correct Curl Command

If you prefer using curl directly, here's the CORRECT format:

```bash
curl -X POST http://localhost:8000/v1/query \
  -F "question=Extract complete data including company research" \
  -F "config_name=visiting_card_extractor.yaml" \
  -F "file=@/path/to/card1.jpg" \
  -F "file=@/path/to/card2.jpg"
```

**IMPORTANT**: Note the `-F "file=@..."` syntax - the `@` is REQUIRED!

### Method 3: Test with Python

```python
import requests

url = "http://localhost:8000/v1/query"

files = [
    ('file', ('card1.jpg', open('/path/to/card1.jpg', 'rb'), 'image/jpeg')),
    ('file', ('card2.jpg', open('/path/to/card2.jpg', 'rb'), 'image/jpeg'))
]

data = {
    'question': 'Extract complete data including company research',
    'config_name': 'visiting_card_extractor.yaml'
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

## How to Verify Files Are Being Uploaded

### 1. Check API Logs
When files ARE uploaded correctly, you'll see:

```
INFO:api:v1/query endpoint called with config: visiting_card_extractor.yaml, files: 2
INFO:app.file_storage_manager:Compressing image card1.jpg (204,354 bytes)
INFO:app.file_storage_manager:Compressed card1.jpg: 204,354 -> 52,180 bytes (74.5% reduction)
INFO:app.file_storage_manager:Stored file: card1.jpg (reference_id=file_abc123, size=52,180 bytes)
```

### 2. Check Enhanced Input
The enhanced input passed to agents should show:

```
**ATTACHED FILES (Reference IDs):**
- card1.jpg (reference_id: file_abc123, type: image/jpeg, size: 52180 bytes)
- card2.jpg (reference_id: file_def456, type: image/jpeg, size: 45920 bytes)
```

### 3. Check Tool Calls
When the OCR agent retrieves files, you'll see:

```
INFO:tools.file_retrieval_tools:Retrieved file content: file_abc123 (card1.jpg)
INFO:tools.file_retrieval_tools:Retrieved file content: file_def456 (card2.jpg)
```

## Common Mistakes

### ❌ WRONG: Missing @ symbol
```bash
curl -F "file=/path/to/image.jpg"  # WRONG!
```

### ✅ CORRECT: With @ symbol
```bash
curl -F "file=@/path/to/image.jpg"  # CORRECT!
```

### ❌ WRONG: File doesn't exist
```bash
curl -F "file=@nonexistent.jpg"
# Error: curl: (26) Failed to open/read local data from file/application
```

### ✅ CORRECT: Check file exists first
```bash
ls -lh card.jpg  # Verify file exists and size
curl -F "file=@card.jpg"
```

### ❌ WRONG: Using POST endpoint instead of v1/query
```bash
curl -X POST http://localhost:8000/query  # Wrong endpoint
```

### ✅ CORRECT: Use v1/query endpoint
```bash
curl -X POST http://localhost:8000/v1/query  # Correct
```

## Complete Working Example

```bash
#!/bin/bash

# 1. Verify API is running
curl -s http://localhost:8000/health || echo "API is not running!"

# 2. Verify files exist
ls -lh "WhatsApp Image 2025-09-30 at 09.36.21.jpeg"
ls -lh "WhatsApp Image 2025-09-30 at 09.36.21 (1).jpeg"

# 3. Make request with files
curl -X POST http://localhost:8000/v1/query \
  -F "question=Extract complete data including company research" \
  -F "config_name=visiting_card_extractor.yaml" \
  -F "file=@WhatsApp Image 2025-09-30 at 09.36.21.jpeg" \
  -F "file=@WhatsApp Image 2025-09-30 at 09.36.21 (1).jpeg" \
  | python3 -m json.tool
```

## Expected Success Flow

When everything works correctly, you'll see this sequence:

1. **File Upload**
   ```
   INFO: v1/query endpoint called with config: visiting_card_extractor.yaml, files: 2
   INFO: Compressing image ... (204,354 bytes)
   INFO: Compressed ...: 204,354 -> 52,180 bytes (74.5% reduction)
   INFO: Stored file: ... (reference_id=file_abc123)
   ```

2. **Enhanced Input Creation**
   ```
   User input includes:
   **ATTACHED FILES (Reference IDs):**
   - file1.jpg (reference_id: file_abc123, ...)
   ```

3. **OCR Agent Retrieves Files**
   ```
   INFO: Retrieved file content: file_abc123 (file1.jpg)
   Tool returned base64 content for vision analysis
   ```

4. **Vision Analysis**
   ```
   LLM processes images with GPT-4o vision
   Extracts: Name, Title, Company, Phone, Email, etc.
   ```

5. **Success**
   ```
   Step ocr_extraction completed successfully
   Step contact_normalization completed successfully
   Step company_research completed successfully
   Step data_aggregation completed successfully
   ```

## If Files Still Not Working

### Check 1: API Server is Running
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

### Check 2: Files Are Readable
```bash
# Check file permissions
ls -l card.jpg
# Should show: -rw-r--r-- (readable)

# Try reading file
file card.jpg
# Should show: JPEG image data...
```

### Check 3: Correct Content-Type
```bash
# Test with explicit content-type
curl -X POST http://localhost:8000/v1/query \
  -F "question=Test" \
  -F "config_name=visiting_card_extractor.yaml" \
  -F "file=@card.jpg;type=image/jpeg"
```

### Check 4: File Size Not Too Large
```bash
# Check file size
du -h card.jpg
# Should be < 10MB for reasonable performance
```

### Check 5: API Endpoint Correct
```bash
# Verify endpoint accepts files
curl -X OPTIONS http://localhost:8000/v1/query
```

## Debug Mode

To see exactly what's being sent:

```bash
curl -X POST http://localhost:8000/v1/query \
  -F "question=Test" \
  -F "config_name=visiting_card_extractor.yaml" \
  -F "file=@card.jpg" \
  -v 2>&1 | grep -A 20 "POST /v1/query"
```

This will show the full request including multipart boundaries.

## Still Having Issues?

1. **Check API Logs**: Look for the line that says `files: X`
   - If X = 0: Files are not being uploaded (fix your curl command)
   - If X > 0: Files are uploaded, issue is elsewhere

2. **Check File Paths**: Make sure paths are correct
   ```bash
   # Use absolute paths to be sure
   curl -F "file=@/Users/you/full/path/to/card.jpg"
   ```

3. **Check File Format**: Only JPG/PNG are tested
   ```bash
   file card.jpg  # Should show "JPEG image data"
   ```

4. **Test with Simple Image First**:
   ```bash
   # Create a simple test image
   convert -size 800x600 xc:white -pointsize 72 -annotate +50+300 'TEST CARD' test.jpg
   
   # Try with test image
   curl -X POST http://localhost:8000/v1/query \
     -F "question=Extract text" \
     -F "config_name=visiting_card_extractor.yaml" \
     -F "file=@test.jpg"
   ```

## Summary

**The issue in your log was simple**: You ran the API request **WITHOUT ANY FILES**.

**The fix**: Use the test script or correct curl syntax with `-F "file=@path/to/image.jpg"`

**After fixing**, you should see:
- `files: 2` (or however many files you upload)
- Compression logs showing images being processed
- OCR agent successfully retrieving and analyzing images