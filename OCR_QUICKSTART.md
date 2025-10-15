# OCR API Quick Start Guide

## 🚀 Get Started in 3 Steps

### 1. Start the OCR API

```bash
# Easy way (recommended)
./run_ocr_api.sh

# Or directly
uvicorn ocr_api:app --reload --port 8001
```

The API will start on **http://localhost:8001**

### 2. Test the API

```bash
# Health check
curl http://localhost:8001/health

# Process a visiting card
curl -X POST "http://localhost:8001/ocr/fast" \
  -F "files=@your_card.jpg" \
  -F "model=gemini/gemini-flash-latest"
```

### 3. View Documentation

Open in browser: **http://localhost:8001/docs**

---

## 📖 API Endpoints

### Health Check
```bash
GET http://localhost:8001/health
```

### OCR Processing
```bash
POST http://localhost:8001/ocr/fast
- files: image files (jpg, png, webp)
- model: "gemini/gemini-flash-latest" (default)
- temperature: 0.1 (default)
```

---

## 💡 Example Usage

### Single Card
```bash
curl -X POST "http://localhost:8001/ocr/fast" \
  -F "files=@card.jpg" \
  -F "model=gemini/gemini-flash-latest"
```

### Multiple Cards
```bash
curl -X POST "http://localhost:8001/ocr/fast" \
  -F "files=@card1_front.jpg" \
  -F "files=@card1_back.jpg" \
  -F "files=@card2.jpg"
```

### Python Example
```python
import requests

url = "http://localhost:8001/ocr/fast"

files = [
    ("files", ("card.jpg", open("card.jpg", "rb"), "image/jpeg"))
]

response = requests.post(url, files=files)
result = response.json()

for card in result["structured_cards"]:
    print(f"Card ID: {card['cardid']}")
    print(f"Name: {card['name']}")
    print(f"Company: {card['company']}")
    print()
```

---

## 🎯 Response Format

```json
{
  "success": true,
  "structured_cards": [
    {
      "cardid": "card_abc12345",
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
      "card_abc12345": {
        "Refs": ["card.jpg"]
      }
    }
  ],
  "total_images": 1,
  "successful_count": 1,
  "model_used": "gemini/gemini-flash-latest"
}
```

---

## 🔑 Key Features

✅ **Unique Card IDs**: Each card gets a unique identifier  
✅ **File Tracking**: Know which files contributed to each card  
✅ **Fast Processing**: Parallel image processing  
✅ **Multi-Language**: Supports multiple languages  
✅ **Front/Back Merge**: Automatically combines card sides  

---

## 🛠️ Configuration

### Environment Variables

Create `.env` file with:
```bash
GOOGLE_API_KEY=your_gemini_api_key
```

### Supported Models

- `gemini/gemini-flash-latest` (default, fastest)
- `gemini/gemini-pro-vision`
- `openai/gpt-4o`
- `openai/gpt-4o-mini`

---

## 📊 Testing

```bash
# Run tests
pytest test_ocr_api.py -v

# Run all OCR tests
python test_ocr_enhancement_simple.py
```

---

## 🐛 Troubleshooting

### API won't start
```bash
# Check if port 8001 is in use
lsof -i :8001

# Try different port
uvicorn ocr_api:app --port 8002
```

### Missing API key
```bash
# Set environment variable
export GOOGLE_API_KEY=your_key

# Or create .env file
echo "GOOGLE_API_KEY=your_key" > .env
```

### Import errors
```bash
# Install dependencies
pip install fastapi uvicorn pydantic python-dotenv

# Or use requirements
pip install -r requirements.txt
```

---

## 📚 Learn More

- **Module Docs**: See `ocr/README.md`
- **Full Summary**: See `OCR_REFACTOR_SUMMARY.md`
- **API Docs**: http://localhost:8001/docs

---

## 🎉 That's It!

You now have a lightweight, standalone OCR API running!

For more advanced usage, check the documentation files listed above.
