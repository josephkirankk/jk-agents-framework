# URGENT FIX: Restart API Server

## Problem
Files ARE being uploaded (170KB, 204KB) but compression ISN'T running.
Result: 378,000 tokens (3x over 128k limit)

## Root Cause
**The API server is running with OLD code (before compression was added).**

The FileStorageManager singleton was created BEFORE you added the compression code, so it's using the old version without compression.

## Solution: RESTART THE API SERVER

### Step 1: Stop the Current API Server
```bash
# Find the process
ps aux | grep "api.py"

# Kill it (use the PID from above)
kill <PID>

# OR if running in terminal, press Ctrl+C
```

### Step 2: Restart with New Code
```bash
cd /Users/A80997271/Documents/projects/jk-agents-framework

# Activate virtual environment
source .venv/bin/activate

# Start API server
python api.py
```

### Step 3: Verify Compression is Working
After restarting, you should see these logs when uploading files:

```
INFO:app.file_storage_manager:FileStorageManager initialized (compression=True, max_dim=1536)
INFO:app.file_storage_manager:Compressing image WhatsApp Image 2025-09-30 at 09.36.21.jpeg (204,354 bytes)
INFO:app.file_storage_manager:Resized image from (2200, 1580) to (1536, 1102)
INFO:app.file_storage_manager:Compressed WhatsApp Image 2025-09-30 at 09.36.21.jpeg: 204,354 -> 52,180 bytes (74.5% reduction)
INFO:app.file_storage_manager:Stored file: WhatsApp Image 2025-09-30 at 09.36.21.jpeg (reference_id=file_abc123, size=52,180 bytes)
```

**KEY INDICATORS:**
- `FileStorageManager initialized (compression=True, max_dim=1536)` ← Should see this on startup
- `Compressing image ...` ← Should see this for each uploaded image
- File sizes should be ~50-60KB instead of 170-200KB

### Step 4: Test Again
```bash
curl -X POST http://localhost:8000/v1/query \
  -F "question=Extract complete data including company research" \
  -F "config_name=visiting_card_extractor.yaml" \
  -F "file=@WhatsApp Image 2025-09-30 at 09.36.21.jpeg" \
  -F "file=@WhatsApp Image 2025-09-30 at 09.36.21 (1).jpeg"
```

## Expected Results After Restart

### Before (Current - FAILING):
```
- File sizes: 170KB, 204KB (original)
- Tokens: 378,000 (3x over limit)
- Error: context_length_exceeded
```

### After (With Compression - SUCCESS):
```
- File sizes: ~50KB, ~60KB (compressed)
- Tokens: ~7,000 (well under limit)
- Success: OCR extraction completes
```

## If Compression Still Doesn't Work

### Check 1: Pillow is Installed
```bash
.venv/bin/python -c "import PIL; print(f'Pillow: {PIL.__version__}')"
# Should show: Pillow: 11.3.0 (or similar)
```

### Check 2: Compression Code is Present
```bash
ls -la app/image_compression.py
# Should exist and be ~4-5KB

head -20 app/image_compression.py
# Should show the compress_image function
```

### Check 3: FileStorageManager Uses Compression
```bash
grep -A 5 "_compress_if_image" app/file_storage_manager.py
# Should show the compression method
```

### Check 4: Test Compression Directly
```python
# Test in Python REPL
from app.image_compression import compress_image, should_compress_image

# Read a test image
with open('WhatsApp Image 2025-09-30 at 09.36.21.jpeg', 'rb') as f:
    img_bytes = f.read()

print(f"Original size: {len(img_bytes):,} bytes")

# Test if compression is needed
needs_compression = should_compress_image(img_bytes)
print(f"Needs compression: {needs_compression}")

# Compress
if needs_compression:
    compressed_bytes, fmt, metadata = compress_image(img_bytes)
    print(f"Compressed size: {len(compressed_bytes):,} bytes")
    print(f"Reduction: {metadata['compression_ratio_percent']}%")
```

## Alternative: Force Compression in API Code

If restart doesn't work, you can force it by modifying api.py:

```python
# In api.py, find the line that imports get_file_storage_manager
from app.file_storage_manager import get_file_storage_manager

# Change get_file_storage_manager() calls to:
from app.file_storage_manager import FileStorageManager
file_manager = FileStorageManager(compress_images=True, max_image_dimension=1536)
```

But this should NOT be necessary - restart should fix it.

## Checklist

- [ ] Stop current API server
- [ ] Verify all code changes are saved
- [ ] Restart API server
- [ ] Check startup logs for "FileStorageManager initialized (compression=True)"
- [ ] Upload files and check for "Compressing image" logs
- [ ] Verify compressed file sizes (~50-60KB instead of 170-200KB)
- [ ] Confirm token count is ~7k instead of 378k
- [ ] Test complete workflow succeeds

## Summary

**The fix is simple: RESTART THE API SERVER**

Your code changes are correct, but the running server has the old code in memory. After restarting, compression will work automatically and your token usage will drop from 378k to ~7k.