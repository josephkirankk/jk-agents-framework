# Google Gemini Vision Fix - Quick Reference

## 🎯 Problem
`google/gemini-2.5-flash-lite` model failing with "LLM Provider NOT provided" error

## ✅ Solution
Vision processor tool now converts `google/` → `gemini/` automatically

---

## 📝 What Was Fixed

### File: `tools/vision_processor_tool.py`
**Added:** Automatic conversion of `google/` prefix to `gemini/` for LiteLLM compatibility

### File: `config/visiting_card_extractor.yaml`
**Updated:** Added model recommendations in prompt

---

## 🚀 Quick Usage

### These All Work Now:
```python
# Any of these formats will work:
model_name = "google/gemini-2.5-flash-lite"  # ✅ Now converted to gemini/
model_name = "google:gemini-2.0-flash-exp"   # ✅ Converted to gemini/
model_name = "gemini/gemini-2.5-flash-lite"  # ✅ Already correct
model_name = "azure_openai:gpt-4o"           # ✅ Works
model_name = "openai:gpt-4o"                 # ✅ Works
```

### Run Visiting Card Extraction:
```bash
jk-agents run config/visiting_card_extractor.yaml \
  --question "extract card details" \
  --file card.jpg
```

---

## 🧪 Verified Tests

```
✅ Conversion logic: google/ → gemini/
✅ Real model invocation with Gemini
✅ All format variations working
✅ Production ready
```

---

## 📊 Model Recommendations

**Best for Production:**
1. `azure_openai:gpt-4o` (if Azure configured)
2. `openai:gpt-4o` (if OpenAI key available)
3. `google:gemini-2.0-flash-exp` (if Google key available)

**Lightweight Option:**
- `gemini/gemini-2.5-flash-lite` (now working!)

---

## 🔧 Technical Note

**Why the conversion?**
- LiteLLM uses `gemini/` for Google AI Studio API (GOOGLE_API_KEY)
- `google/` routes to Vertex AI (needs GCP credentials)
- Most users have AI Studio keys, not Vertex setup

---

**Status:** ✅ Fixed and tested  
**Date:** 2025-09-30