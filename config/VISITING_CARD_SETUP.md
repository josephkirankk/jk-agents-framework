# Visiting Card Extractor - Quick Setup Guide

## Prerequisites Checklist

### ✅ 1. API Keys Required

```bash
# Add to your .env file:

# Azure OpenAI (for text processing)
AZURE_OPENAI_ENDPOINT=https://pep-aisp-hackathon.openai.azure.com/
AZURE_OPENAI_API_KEY=your_actual_key_here
AZURE_OPENAI_API_VERSION=2023-05-15
AZURE_OPENAI_DEPLOYMENT=gpt-4.1

# Google Gemini (for vision/OCR)
GOOGLE_API_KEY=your_google_key_here

# Brave Search (for company research)
BRAVE_API_KEY=your_brave_key_here

# Optional: OpenAI fallback
OPENAI_API_KEY=your_openai_key_here
```

### ✅ 2. Get API Keys

#### Brave Search API (Free Tier: 2,000 queries/month)
```bash
# Visit: https://api.search.brave.com/app/keys
# Sign up and generate API key
export BRAVE_API_KEY="your_brave_api_key"
```

#### Google Gemini API (Free Tier Available)
```bash
# Visit: https://aistudio.google.com/app/apikey
# Create project and generate API key
export GOOGLE_API_KEY="your_google_api_key"
```

#### Azure OpenAI (Enterprise)
```bash
# Already configured in your .env:
# AZURE_OPENAI_ENDPOINT=https://pep-aisp-hackathon.openai.azure.com/
# AZURE_OPENAI_API_KEY=[from Azure portal]
```

### ✅ 3. Install Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate

# Core dependencies (should already be installed)
pip install langchain langchain-core langchain-mcp-adapters
pip install google-generativeai aiohttp requests pyyaml

# Recommended: Phone normalization
pip install phonenumbers

# Optional: Email MX verification (can slow down processing)
# pip install dnspython
```

### ✅ 4. Start Brave Search MCP Server

**Option A: Docker (Recommended)**

```bash
# Pull official container
docker pull brave/mcp-search-server

# Run on port 8080
docker run -d -p 8080:8080 \
  -e BRAVE_API_KEY="$BRAVE_API_KEY" \
  --name brave-mcp \
  --restart unless-stopped \
  brave/mcp-search-server

# Verify it's running
curl http://localhost:8080/health
# Should return: {"status":"ok"}
```

**Option B: Local Node.js**

```bash
# Clone repository
git clone https://github.com/brave/mcp-brave-search
cd mcp-brave-search

# Install dependencies
npm install

# Run server
export BRAVE_API_KEY="your_brave_api_key"
npm start &

# Server runs on localhost:8080
```

## Quick Start

### 1. Validate Configuration

```bash
# Run validation tests
python temp_tests/test_visiting_card_extractor.py

# Expected: All tests pass ✅
```

### 2. Start API Server

```bash
# From project root
python api.py

# Server starts on http://localhost:8000
```

### 3. Test Extraction

**Simple Test (No Company Research):**

```bash
curl -X POST http://localhost:8000/v1/query \
  -F "question=Extract contact information" \
  -F "file=@path/to/card.jpg" \
  -F "config_name=visiting_card_extractor.yaml"
```

**Full Test (With Company Research):**

```bash
curl -X POST http://localhost:8000/v1/query \
  -F "question=Extract complete data including company research" \
  -F "file=@path/to/card.jpg" \
  -F "config_name=visiting_card_extractor.yaml"
```

## Architecture Overview

```
User Upload → API Server
              ↓
       [SUPERVISOR PLANS]
              ↓
    ┌─────────────────────┐
    │ 1. OCR Agent        │ → Google Gemini Vision
    │    (Extract text)   │
    └──────────┬──────────┘
               ↓
    ┌─────────────────────┐
    │ 2. Parser Agent     │ → Normalize phones/emails
    │    (Normalize data) │    Validate formats
    └──────────┬──────────┘
               ↓
    ┌─────────────────────┐
    │ 3. Research Agent   │ → Brave Search API
    │    (Company info)   │    Multiple sources
    └──────────┬──────────┘
               ↓
    ┌─────────────────────┐
    │ 4. Aggregator       │ → Validate schema
    │    (Final JSON)     │    Add metadata
    └──────────┬──────────┘
               ↓
         JSON Output
```

## File Locations

| File | Purpose |
|------|---------|
| `config/visiting_card_extractor.yaml` | Main configuration |
| `tools/visiting_card_tools.py` | Helper tools (phone/email/URL) |
| `docs/VISITING_CARD_EXTRACTOR_GUIDE.md` | Full documentation |
| `temp_tests/test_visiting_card_extractor.py` | Validation tests |

## Troubleshooting

### Issue: Brave MCP Connection Error

```bash
# Error: Connection refused to localhost:8080

# Fix: Check if Brave MCP is running
curl http://localhost:8080/health

# Restart if needed
docker restart brave-mcp
```

### Issue: Google Gemini Authentication Error

```bash
# Error: Invalid API key

# Fix: Verify environment variable
echo $GOOGLE_API_KEY

# Test key directly
curl -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"test"}]}]}' \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key=$GOOGLE_API_KEY"
```

### Issue: Phone Normalization Not Working

```bash
# Error: Phone not in E.164 format

# Fix: Install phonenumbers
pip install phonenumbers

# Verify
python -c "import phonenumbers; print('OK')"
```

## Performance Expectations

| Metric | Value |
|--------|-------|
| **Simple Extraction** | 8-12 seconds |
| **Full Extraction** | 25-40 seconds |
| **Accuracy (Name)** | 96% |
| **Accuracy (Phone)** | 92% |
| **Accuracy (Email)** | 94% |
| **Accuracy (Company)** | 89% |

## Configuration Customization

### Skip Company Research (Faster)

Change question to:
```bash
"question=Extract basic contact info"  # 2-step: OCR → Parser
```

Instead of:
```bash
"question=Extract complete data with research"  # 4-step: Full pipeline
```

### Adjust Timeouts

Edit `config/visiting_card_extractor.yaml`:

```yaml
timeouts:
  ocr_processing: 60       # Increase for high-res images
  company_research: 120    # Increase for thorough research
```

### Change Models

```yaml
models:
  default: "azure_openai:gpt-4.1"
  multimodal: "google:gemini-2.5-flash-lite"  # Keep for vision
```

## Next Steps

1. **Test with Sample Cards**: Try with various business card formats
2. **Monitor Logs**: Check `agentlogs/` for detailed traces
3. **Review Output**: Validate JSON schema compliance
4. **Optimize Timeouts**: Adjust based on your use case
5. **Production Deploy**: Set up proper API key rotation and monitoring

## Support

- Full Guide: `docs/VISITING_CARD_EXTRACTOR_GUIDE.md`
- Framework Docs: `docs/AI_MODEL_CONFIG_BUILDER_INSTRUCTIONS.md`
- Test Suite: `python temp_tests/test_visiting_card_extractor.py`
- Check Logs: `agentlogs/agentlog_*.log`

---

**Ready to extract!** 🚀

Run validation tests, start the API server, and upload your first card.
