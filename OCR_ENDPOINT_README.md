# Fast OCR API Endpoint

## Overview

The `/ocr/fast` endpoint provides high-speed OCR (Optical Character Recognition) processing for multiple images using LiteLLM with Google's Gemini Flash model by default. It's designed for maximum speed and accuracy with structured output.

## Endpoint Details

- **URL**: `/ocr/fast`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Authentication**: None (uses API keys from environment variables)

## Features

✅ **Batch Processing** - Process multiple images in a single request  
✅ **Parallel Processing** - All images are processed concurrently for maximum speed  
✅ **Multiple Formats** - Supports JPEG, PNG, WEBP, GIF, BMP  
✅ **Structured Output** - Returns JSON with per-image results and metadata  
✅ **Multi-Provider Support** - Uses LiteLLM to support various AI providers  
✅ **Error Handling** - Individual image failures don't affect others  
✅ **Performance Metrics** - Returns processing time for each image and total

## Request Parameters

### Form Data

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `files` | File[] | Yes | - | Image files to process (one or more) |
| `model` | string | No | `gemini/gemini-flash-latest` | LiteLLM model identifier |
| `temperature` | float | No | `0.1` | Model temperature (0.0-1.0, lower = more deterministic) |
| `structured_output` | bool | No | `true` | Return structured JSON response |

### Supported Models

The endpoint supports any LiteLLM-compatible vision model:

- **Google Gemini** (recommended for speed):
  - `gemini/gemini-flash-latest` (default, fastest)
  - `gemini/gemini-pro-vision`
  
- **OpenAI**:
  - `openai/gpt-4o`
  - `openai/gpt-4o-mini`
  
- **Anthropic**:
  - `anthropic/claude-3-5-sonnet`

## Response Format

```json
{
  "success": true,
  "message": "Processed 2 images: 2 successful, 0 failed. Structured 1 card(s).",
  "structured_cards": [
    {
      "name": "Joseph Kiran (JK)",
      "role": "Chief Technology Strategist",
      "company": "Rayosense Technologies Private Limited.",
      "phone": ["810 698 8001"],
      "email": ["info@rayosense.com"],
      "address": "Kokapet Hyderabad, India",
      "website": ["www.rayosense.com"]
    }
  ],
  "total_images": 2,
  "successful_count": 2,
  "failed_count": 0,
  "total_processing_time": 11.45,
  "summarization_time": 6.7,
  "model_used": "gemini/gemini-flash-latest",
  "timestamp": "2025-09-30T19:14:21.123456Z"
}
```

## Usage Examples

### cURL

```bash
# Single image
curl -X POST http://localhost:8000/ocr/fast \
  -F "files=@image1.jpg"

# Multiple images with custom model
curl -X POST http://localhost:8000/ocr/fast \
  -F "files=@image1.jpg" \
  -F "files=@image2.png" \
  -F "files=@image3.jpg" \
  -F "model=openai/gpt-4o-mini" \
  -F "temperature=0.1"
```

### Python (requests)

```python
import requests

# Prepare files
files = [
    ('files', ('image1.jpg', open('image1.jpg', 'rb'), 'image/jpeg')),
    ('files', ('image2.png', open('image2.png', 'rb'), 'image/png')),
]

# Optional parameters
data = {
    'model': 'gemini/gemini-flash-latest',
    'temperature': 0.1,
    'structured_output': True
}

# Make request
response = requests.post(
    'http://localhost:8000/ocr/fast',
    files=files,
    data=data
)

# Process results
if response.status_code == 200:
    result = response.json()
    print(f"Processed {result['total_images']} images")
    print(f"Structured {len(result['structured_cards'])} card(s)")
    
    for card in result['structured_cards']:
        print(f"\n{card.get('name', 'Unknown')} - {card.get('company', 'N/A')}")
        print(f"  Role: {card.get('role', 'N/A')}")
        print(f"  Email: {', '.join(card.get('email', []))}")
        print(f"  Phone: {', '.join(card.get('phone', []))}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
```

### JavaScript (fetch)

```javascript
const formData = new FormData();
formData.append('files', fileInput1.files[0]);
formData.append('files', fileInput2.files[0]);
formData.append('model', 'gemini/gemini-flash-latest');
formData.append('temperature', '0.1');

fetch('http://localhost:8000/ocr/fast', {
  method: 'POST',
  body: formData
})
  .then(response => response.json())
  .then(data => {
    console.log('OCR Results:', data);
    console.log(`Structured ${data.structured_cards.length} card(s)`);
    data.structured_cards.forEach(card => {
      console.log(`${card.name} - ${card.company}`);
      console.log(`  Email: ${card.email?.join(', ') || 'N/A'}`);
      console.log(`  Phone: ${card.phone?.join(', ') || 'N/A'}`);
    });
  })
  .catch(error => console.error('Error:', error));
```

### Python (test script included)

Use the included test script:

```bash
# Basic usage
python test_ocr_endpoint.py

# Or in Python interactive mode
from test_ocr_endpoint import test_ocr_endpoint_with_images

test_ocr_endpoint_with_images([
    'path/to/image1.jpg',
    'path/to/image2.png'
])
```

## Performance

### Speed Benchmarks

With Gemini Flash (default):
- **Single image**: ~1-2 seconds
- **3 images (parallel)**: ~2-3 seconds
- **10 images (parallel)**: ~3-5 seconds

The endpoint processes all images in parallel, so processing multiple images is nearly as fast as processing one.

### Optimization Tips

1. **Use Gemini Flash** (default) - It's the fastest model for OCR
2. **Batch multiple images** - Parallel processing makes this efficient
3. **Lower temperature** (0.1) - More deterministic, slightly faster
4. **Optimize image size** - Resize very large images before upload for faster processing

## Error Handling

The endpoint handles errors gracefully:

### Individual Image Failures

If some images fail during processing, successfully processed images will still be included in the structured output:

```json
{
  "success": true,
  "message": "Processed 2 images: 1 successful, 1 failed. Structured 1 card(s).",
  "structured_cards": [
    {
      "name": "John Doe",
      "role": "CEO",
      "company": "Example Corp",
      "phone": ["+1-555-1234"],
      "email": ["john@example.com"],
      "address": "123 Main St, City, State",
      "website": ["www.example.com"]
    }
  ],
  "total_images": 2,
  "successful_count": 1,
  "failed_count": 1,
  "total_processing_time": 5.2,
  "summarization_time": 3.1,
  "model_used": "gemini/gemini-flash-latest",
  "timestamp": "2025-09-30T19:14:21.123456Z"
}
```

### Complete Failures

If the entire request fails:

```json
{
  "detail": "Fast OCR processing failed: <error message>"
}
```

HTTP status codes:
- `200` - Success (even if some images failed)
- `400` - Bad request (invalid parameters, no files, etc.)
- `500` - Server error

## Environment Setup

### Required Environment Variables

The endpoint uses LiteLLM, which requires appropriate API keys:

```bash
# For Gemini (default model)
export GOOGLE_API_KEY="your-google-api-key"
# or
export GEMINI_API_KEY="your-gemini-api-key"

# For OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# For Anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### Installation

Ensure LiteLLM is installed:

```bash
pip install litellm
```

## Implementation Details

### Architecture

The endpoint follows the same pattern as `extract_visiting_card_text_fast`:

1. **Image Upload** - Receives multiple images via multipart/form-data
2. **Parallel Processing** - Creates async tasks for each image
3. **LiteLLM Integration** - Uses `create_litellm_model()` with vision support
4. **Structured Response** - Returns standardized JSON with per-image results

### Key Functions

- `process_image_ocr()` - Processes a single image using LiteLLM
- `fast_ocr_endpoint()` - Main endpoint handler with parallel processing

### Code Location

- Endpoint implementation: `api.py` (line ~2255)
- Models: `api.py` (line ~907)
- Helper function: `api.py` (line ~1208)

## Testing

### Run the API Server

```bash
python -m uvicorn api:app --reload
```

### Test with the Included Script

```bash
python test_ocr_endpoint.py
```

### Interactive Testing

Visit the auto-generated API docs:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Troubleshooting

### "Could not connect to API server"
- Make sure the server is running: `python -m uvicorn api:app --reload`
- Check the port (default: 8000)

### "Invalid file type"
- Ensure images are in supported formats: JPEG, PNG, WEBP, GIF, BMP
- Check the file extension and MIME type

### "Failed to create vision model"
- Verify API keys are set in environment variables
- Check that LiteLLM is installed: `pip install litellm`

### Slow processing
- Use Gemini Flash (default model) for fastest results
- Consider reducing image sizes before upload
- Check your internet connection speed

### Model not found
- Verify the model identifier format: `provider/model`
- Ensure you have valid API keys for the provider
- Check LiteLLM documentation for supported models

## Related Features

This endpoint is similar to:
- `extract_visiting_card_text_fast` tool - Same underlying technology
- `/multimodal` endpoint - More flexible but slower
- `/worker/upload` endpoint - General file processing

## API Documentation

Full API documentation is available at:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)
- http://localhost:8000/ (Endpoint listing)

## Future Enhancements

Potential improvements:
- [ ] Support for PDF files
- [ ] Batch size limits and pagination
- [ ] Webhook callbacks for long-running batches
- [ ] OCR result caching
- [ ] Language detection and translation
- [ ] Confidence scores per extracted text
- [ ] Image preprocessing options

## License

Part of the jk-agents-framework project.
