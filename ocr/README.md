# OCR Module

Lightweight OCR module for visiting card processing, extracted from the main agent system for better modularity and maintainability.

## Structure

```
ocr/
├── __init__.py          # Module exports
├── models.py            # Pydantic models (FastOCRResponse, OCRImageResult)
├── core.py              # Core OCR processing logic
└── README.md            # This file
```

## Components

### models.py
- **OCRImageResult**: Result model for single image OCR
- **FastOCRResponse**: Complete response model with card IDs and metadata

### core.py
- **process_image_ocr()**: Process single image using LiteLLM vision models
- **summarize_visiting_cards()**: Combine multiple OCR results, generate card IDs, track file references

## Usage

### Standalone OCR API

Run the lightweight OCR API on port 8001:

```bash
# Start OCR API
uvicorn ocr_api:app --reload --host 0.0.0.0 --port 8001

# Or use Python directly
python ocr_api.py
```

### Programmatic Usage

```python
from ocr import process_image_ocr, summarize_visiting_cards, FastOCRResponse

# Process single image
result = await process_image_ocr(
    image_data=image_bytes,
    filename="card.jpg",
    mime_type="image/jpeg",
    model="gemini/gemini-flash-latest",
    temperature=0.1
)

# Summarize multiple results
summary = await summarize_visiting_cards(
    ocr_results=[result1, result2],
    model="gemini/gemini-flash-latest",
    temperature=0.0
)
```

## Dependencies

Minimal dependencies for OCR functionality:
- `fastapi` - Web framework
- `pydantic` - Data validation
- `litellm` - Multi-model LLM interface (via app.enhanced_litellm_wrapper)
- `langchain_core` - Message types

## Testing

```bash
# Run OCR API tests
pytest test_ocr_api.py -v

# Run unit tests
python test_ocr_enhancement_simple.py
```

## Design Principles

### KISS (Keep It Simple, Stupid)
- Single responsibility: OCR processing only
- Clear separation from main agent system
- Minimal dependencies
- Straightforward data flow

### Maintainability
- Well-documented code
- Type hints throughout
- Clear error handling
- Comprehensive logging

### Extensibility
- Modular design
- Easy to add new OCR models
- Pluggable components
- Configuration via parameters

### Performance
- Async/await for I/O operations
- Parallel image processing
- Efficient data structures
- Minimal overhead

## API Endpoints

When running ocr_api.py:

- `GET /` - API information
- `GET /health` - Health check
- `POST /ocr/fast` - Fast OCR for visiting cards
- `GET /docs` - Interactive API documentation

## Card ID Format

Each structured card gets a unique ID:
- Format: `card_<8_hex_chars>`
- Example: `card_abc12345`
- Generated using UUID4 for guaranteed uniqueness

## Metadata Format

File references tracked in `meta` field:
```json
{
  "meta": [
    {
      "card_abc12345": {
        "Refs": ["card_front.jpg", "card_back.jpg"]
      }
    }
  ]
}
```

## Environment Variables

Required for OCR functionality:
- `GOOGLE_API_KEY` - For Gemini models
- Or other LLM provider API keys as needed

## Migration from api.py

The OCR functionality was extracted from the main `api.py` to:
1. Reduce coupling between OCR and agent systems
2. Allow independent deployment/scaling of OCR service
3. Improve code maintainability
4. Enable faster iteration on OCR features

## Future Enhancements

- [ ] Support additional OCR models
- [ ] Batch processing optimization
- [ ] Caching layer for repeated requests
- [ ] Confidence scoring for extractions
- [ ] Multi-language OCR improvements
