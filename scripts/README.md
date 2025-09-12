# Google Gemini API Testing Scripts

This directory contains comprehensive testing scripts for the JK-Agents API with Google Gemini models. These scripts test text processing, CSV analysis, image analysis, and multimodal capabilities.

## 📁 Files Overview

| File | Description | Platform |
|------|-------------|----------|
| `test_gemini_api.sh` | Bash script with curl commands | Linux/macOS |
| `test_gemini_api.bat` | Batch script with curl commands | Windows |
| `test_gemini_api.py` | Python automated testing script | Cross-platform |
| `README.md` | This documentation file | All |

## 🚀 Quick Start

### Prerequisites

1. **Start the FastAPI server:**
   ```bash
   uvicorn app.api:app --reload
   ```

2. **Set your Google API key in `.env`:**
   ```env
   GOOGLE_API_KEY=your-google-api-key-here
   ```

3. **Ensure test files are available:**
   - `customer_data.csv` (provided)
   - `sample_sales_data.csv` (provided)
   - Optional: Add test images (`test_image.jpg`, `chart.png`, etc.)

### Running Tests

#### Option 1: Bash Script (Linux/macOS)
```bash
chmod +x scripts/test_gemini_api.sh
./scripts/test_gemini_api.sh
```

#### Option 2: Batch Script (Windows)
```cmd
scripts\test_gemini_api.bat
```

#### Option 3: Python Script (Automated)
```bash
python scripts/test_gemini_api.py
```

## 🧪 Test Categories

### 1. Basic Text Processing
Tests basic text analysis and conversation capabilities with Google Gemini models.

**Example curl:**
```bash
curl -X POST "http://localhost:8000/worker" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "gemini_test_agent",
    "input": "Hello, can you confirm you are running on Google Gemini?",
    "config_path": "config/gemini-test.yaml"
  }'
```

### 2. CSV Data Analysis
Tests CSV file upload and analysis capabilities with specialized data analysis agents.

**Example curl:**
```bash
curl -X POST "http://localhost:8000/worker/upload" \
  -F "agent_name=gemini_csv_analyst" \
  -F "input=Analyze this customer data and provide business insights" \
  -F "config_path=config/gemini-test.yaml" \
  -F "files=@customer_data.csv"
```

### 3. Image Analysis
Tests image upload and analysis capabilities including OCR, object detection, and chart analysis.

**Example curl:**
```bash
curl -X POST "http://localhost:8000/worker/upload" \
  -F "agent_name=gemini_image_analyzer" \
  -F "input=Analyze this image and describe what you see" \
  -F "config_path=config/gemini-test.yaml" \
  -F "files=@image.jpg"
```

### 4. Multimodal Analysis
Tests combined analysis of multiple file types (CSV + images) for comprehensive insights.

**Example curl:**
```bash
curl -X POST "http://localhost:8000/worker/upload" \
  -F "agent_name=gemini_multimodal_agent" \
  -F "input=Analyze both the data and image together" \
  -F "config_path=config/gemini-test.yaml" \
  -F "files=@data.csv" \
  -F "files=@chart.png"
```

### 5. Supervised Multi-Agent
Tests the supervisor system that coordinates multiple Gemini agents for complex tasks.

**Example curl:**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Create a comprehensive business analysis using available data",
    "config_path": "config/gemini-test.yaml"
  }'
```

## 📊 Available Agents

The `config/gemini-test.yaml` configuration includes these specialized agents:

| Agent Name | Model | Specialization |
|------------|-------|----------------|
| `gemini_multimodal_agent` | gemini-2.0-flash-lite-001 | General multimodal analysis |
| `gemini_csv_analyst` | gemini-2.0-flash-lite-001 | CSV data analysis |
| `gemini_image_analyzer` | gemini-2.0-flash-lite-001 | Image analysis and OCR |
| `gemini_text_agent` | gemini-2.0-flash-lite-001 | Text processing |
| `gemini_test_agent` | gemini-2.0-flash-lite-001 | Integration testing |

## 📁 Test Files

### Provided CSV Files
- **`customer_data.csv`**: Customer demographics and behavior data
- **`sample_sales_data.csv`**: Sales transaction data with products and regions

### Image Files (Optional)
Add these files to test image analysis:
- `test_image.jpg` - General image for analysis
- `chart.png` - Chart or graph for data extraction
- `document.jpg` - Document image for OCR testing

## 🔧 Troubleshooting

### Common Issues

#### Connection Refused
```
curl: (7) Failed to connect to localhost port 8000: Connection refused
```
**Solution:** Start the FastAPI server first:
```bash
uvicorn app.api:app --reload
```

#### Agent Not Found
```json
{"error": "Agent 'agent_name' not found in config"}
```
**Solution:** Check the agent name matches those in `config/gemini-test.yaml`

#### File Not Found
```
curl: (26) Failed to open/read local data from file/path
```
**Solution:** Ensure file paths are correct and files exist

#### Rate Limit Exceeded
```json
{"error": "429 You exceeded your current quota"}
```
**Solution:** Wait for rate limits to reset or upgrade your Google API plan

#### Invalid API Key
```json
{"error": "Invalid API key"}
```
**Solution:** Check your `GOOGLE_API_KEY` in the `.env` file

### Debug Mode

Enable verbose logging:
```bash
export LANGCHAIN_VERBOSE=true
uvicorn app.api:app --reload
```

## 📈 Expected Results

### Successful Response Format
```json
{
  "success": true,
  "response": "I am running on Google Gemini 2.0 Flash Lite. I can analyze text, images, and CSV data...",
  "agent_name": "gemini_test_agent",
  "raw_output": {...}
}
```

### CSV Analysis Response
- Data structure analysis
- Statistical insights
- Business recommendations
- Data quality assessment

### Image Analysis Response
- Detailed image description
- Text extraction (OCR)
- Object identification
- Context and insights

## 🎯 Performance Tips

1. **Use appropriate agents** for specific tasks
2. **Limit CSV file size** to avoid token limits (first 100 rows shown)
3. **Optimize image sizes** for faster processing
4. **Monitor API quotas** to avoid rate limiting
5. **Use batch requests** for multiple files when possible

## 📚 Additional Resources

- [Google Gemini Integration Guide](../docs/GOOGLE_GEMINI_INTEGRATION.md)
- [File Upload API Documentation](../docs/FILE_UPLOAD_API.md)
- [Google AI Documentation](https://ai.google.dev/gemini-api/docs)

## ✅ Success Indicators

When tests pass successfully, you should see:
- ✅ Health check returns 200 OK
- ✅ Agents respond with Google Gemini confirmation
- ✅ CSV files are analyzed with insights
- ✅ Images are described accurately
- ✅ Multimodal analysis combines data sources
- ✅ Supervisor coordinates multiple agents

Ready to test your Google Gemini integration! 🚀
