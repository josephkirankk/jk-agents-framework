# OCR Fast Endpoint - Quick Reference Guide

## Endpoint Details
- **URL**: `POST /ocr/fast`
- **Content-Type**: `multipart/form-data`
- **Response**: JSON with structured cards, card IDs, and file metadata

## Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `files` | File[] | Yes | - | Multiple image files (JPG, PNG, WEBP, etc.) |
| `model` | string | No | `gemini/gemini-flash-latest` | LiteLLM model ID |
| `temperature` | float | No | `0.1` | Model temperature (0.0-1.0) |
| `structured_output` | bool | No | `true` | Return structured output |

## Response Structure

```typescript
interface OCRResponse {
  success: boolean;
  message: string;
  structured_cards: Array<{
    cardid: string;           // NEW: Unique card identifier (e.g., "card_abc12345")
    name: string | null;
    role: string | null;
    company: string | null;
    phone: string[] | null;
    email: string[] | null;
    address: string | null;
    website: string[] | null;
  }>;
  meta: Array<{              // NEW: File reference metadata
    [cardid: string]: {
      Refs: string[];        // List of filenames used for this card
    }
  }>;
  total_images: number;
  successful_count: number;
  failed_count: number;
  total_processing_time: number;
  summarization_time: number;
  model_used: string;
  timestamp: string;
}
```

## Usage Examples

### Example 1: Single Card (Front Only)

```bash
curl -X POST "http://localhost:8000/ocr/fast" \
  -F "files=@business_card.jpg" \
  -F "model=gemini/gemini-flash-latest"
```

**Response:**
```json
{
  "success": true,
  "structured_cards": [
    {
      "cardid": "card_a1b2c3d4",
      "name": "John Doe",
      "role": "CEO",
      "company": "Tech Corp",
      "phone": ["555-1234"],
      "email": ["john@techcorp.com"],
      "address": "123 Main St",
      "website": ["www.techcorp.com"]
    }
  ],
  "meta": [
    {
      "card_a1b2c3d4": {
        "Refs": ["business_card.jpg"]
      }
    }
  ]
}
```

### Example 2: Multiple Cards (Front + Back)

```bash
curl -X POST "http://localhost:8000/ocr/fast" \
  -F "files=@card1_front.jpg" \
  -F "files=@card1_back.jpg" \
  -F "files=@card2.jpg"
```

**Response:**
```json
{
  "success": true,
  "structured_cards": [
    {
      "cardid": "card_e5f6g7h8",
      "name": "Alice Smith",
      ...
    },
    {
      "cardid": "card_i9j0k1l2",
      "name": "Bob Johnson",
      ...
    }
  ],
  "meta": [
    {
      "card_e5f6g7h8": {
        "Refs": ["card1_front.jpg", "card1_back.jpg"]
      }
    },
    {
      "card_i9j0k1l2": {
        "Refs": ["card2.jpg"]
      }
    }
  ]
}
```

### Example 3: Python Client

```python
import requests

url = "http://localhost:8000/ocr/fast"

# Prepare files
files = [
    ("files", ("card_front.jpg", open("card_front.jpg", "rb"), "image/jpeg")),
    ("files", ("card_back.jpg", open("card_back.jpg", "rb"), "image/jpeg")),
]

# Request
response = requests.post(
    url,
    files=files,
    data={
        "model": "gemini/gemini-flash-latest",
        "temperature": 0.1
    }
)

# Parse response
result = response.json()
for card in result["structured_cards"]:
    print(f"Card ID: {card['cardid']}")
    print(f"Name: {card['name']}")
    print(f"Company: {card['company']}")
    
    # Find which files were used for this card
    for meta_entry in result["meta"]:
        if card["cardid"] in meta_entry:
            print(f"Source files: {meta_entry[card['cardid']]['Refs']}")
    print()
```

### Example 4: JavaScript/Node.js Client

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const form = new FormData();
form.append('files', fs.createReadStream('card1_front.jpg'));
form.append('files', fs.createReadStream('card1_back.jpg'));
form.append('model', 'gemini/gemini-flash-latest');
form.append('temperature', '0.1');

axios.post('http://localhost:8000/ocr/fast', form, {
  headers: form.getHeaders()
})
.then(response => {
  const data = response.data;
  
  data.structured_cards.forEach(card => {
    console.log(`Card ID: ${card.cardid}`);
    console.log(`Name: ${card.name}`);
    console.log(`Company: ${card.company}`);
    
    // Find source files
    const metaEntry = data.meta.find(m => card.cardid in m);
    if (metaEntry) {
      console.log(`Source files: ${metaEntry[card.cardid].Refs}`);
    }
    console.log();
  });
})
.catch(error => console.error(error));
```

## Key Features

### 🆔 Card ID (NEW)
- **Format**: `card_<8_hex_chars>`
- **Uniqueness**: Guaranteed unique per request using UUID
- **Location**: In each card object as `cardid` field
- **Usage**: Track and reference individual cards

### 📁 File Metadata (NEW)
- **Structure**: Array of `{cardid: {Refs: [filenames]}}`
- **Purpose**: Track which files were used for each card
- **Use Cases**:
  - Audit trail
  - Source verification
  - Front/back card association
  - Quality control

### 🔄 Backward Compatibility
- All existing fields preserved
- New fields are additive only
- `meta` defaults to empty array if not available
- Works with older clients without modification

## Common Use Cases

### Use Case 1: Batch Processing
Upload multiple cards and track each by ID:
```python
response = requests.post(url, files=files)
for card in response.json()["structured_cards"]:
    save_to_database(card["cardid"], card)
```

### Use Case 2: Quality Check
Verify which files contributed to each card:
```python
for meta_entry in response.json()["meta"]:
    card_id, refs = list(meta_entry.items())[0]
    if len(refs["Refs"]) > 1:
        print(f"Card {card_id} merged from {len(refs['Refs'])} files")
```

### Use Case 3: Re-processing
Use card IDs to track re-processing attempts:
```python
# First attempt
response1 = requests.post(url, files=[file1])
card_id = response1.json()["structured_cards"][0]["cardid"]

# Store card_id for later reference
# If quality is poor, reprocess with better image
response2 = requests.post(url, files=[better_file])
new_card_id = response2.json()["structured_cards"][0]["cardid"]

# Update records: old_card_id -> new_card_id
```

## Error Handling

### Empty Files
```json
{
  "detail": "No files provided. Please upload at least one image."
}
```

### Invalid File Type
```json
{
  "detail": "Invalid file type for example.pdf. Supported types: JPEG, PNG, WEBP, GIF, BMP"
}
```

### Processing Failures
```json
{
  "success": false,
  "message": "Processed 2 images: 1 successful, 1 failed.",
  "structured_cards": [...],
  "meta": [...],
  "failed_count": 1
}
```

## Performance Tips

1. **Batch Similar Cards**: Upload front and back of same card together
2. **Use Fast Model**: Default `gemini-flash-latest` is optimized for speed
3. **Parallel Requests**: Make multiple API calls for large batches
4. **Image Quality**: Higher quality images = better accuracy
5. **File Size**: Compress images before upload for faster processing

## Support

- **Documentation**: `/docs` endpoint for interactive API docs
- **Health Check**: `GET /health`
- **Version**: Check `timestamp` field in response for processing time

## Changelog

### v1.1.0 (Current)
- ✨ Added unique card ID generation (`cardid` field)
- ✨ Added file reference metadata (`meta` field)
- ✨ Enhanced LLM prompt for better card-to-file mapping
- 🔧 Improved backward compatibility
- 📝 Added comprehensive test suite

### v1.0.0 (Previous)
- Initial OCR fast endpoint
- Parallel image processing
- Structured card extraction
