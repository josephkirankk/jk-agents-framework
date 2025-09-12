# Google Gemini API Testing Guide

Complete guide for testing the JK-Agents system with Google Gemini models using curl scripts and automated testing.

## 🎯 Overview

This guide provides comprehensive testing scripts for the Google Gemini integration, including:
- **Text Processing**: Basic conversation and analysis
- **CSV Analysis**: Data insights and business intelligence
- **Image Analysis**: Visual content understanding and OCR
- **Multimodal Processing**: Combined analysis of multiple file types
- **Supervised Multi-Agent**: Complex task coordination

## 🚀 Quick Setup

### 1. Start the API Server
```bash
uvicorn app.api:app --reload
```

### 2. Verify Google API Key
Ensure your `.env` file contains:
```env
GOOGLE_API_KEY=your-google-api-key-here
```

### 3. Test Basic Connectivity
```bash
curl -X GET "http://localhost:8000/health"
```

Expected response:
```json
{"status": "healthy", "timestamp": "2025-01-23T20:32:00Z"}
```

## 📋 Available Testing Scripts

| Script | Platform | Description |
|--------|----------|-------------|
| `scripts/test_gemini_api.sh` | Linux/macOS | Bash script with curl commands |
| `scripts/test_gemini_api.bat` | Windows | Batch script with curl commands |
| `scripts/test_gemini_api.py` | Cross-platform | Python automated testing |

## 🧪 Core Test Examples

### Text Processing Test
```bash
curl -X POST "http://localhost:8000/worker" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "gemini_test_agent",
    "input": "Hello, confirm you are running on Google Gemini and describe your capabilities",
    "config_path": "config/gemini-test.yaml"
  }'
```

### CSV Analysis Test
```bash
curl -X POST "http://localhost:8000/worker/upload" \
  -F "agent_name=gemini_csv_analyst" \
  -F "input=Analyze this customer data and provide business insights with recommendations" \
  -F "config_path=config/gemini-test.yaml" \
  -F "files=@customer_data.csv"
```

### Image Analysis Test
```bash
curl -X POST "http://localhost:8000/worker/upload" \
  -F "agent_name=gemini_image_analyzer" \
  -F "input=Analyze this image in detail, extract any text, and describe what you see" \
  -F "config_path=config/gemini-test.yaml" \
  -F "files=@your_image.jpg"
```

### Multimodal Analysis Test
```bash
curl -X POST "http://localhost:8000/worker/upload" \
  -F "agent_name=gemini_multimodal_agent" \
  -F "input=Analyze both the CSV data and image together, finding connections and insights" \
  -F "config_path=config/gemini-test.yaml" \
  -F "files=@data.csv" \
  -F "files=@chart.png"
```

### Supervised Multi-Agent Test
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Create a comprehensive business intelligence report using Google Gemini agents",
    "config_path": "config/gemini-test.yaml"
  }'
```

## 📊 Expected Results

### Successful Text Response
```json
{
  "success": true,
  "response": "Yes, I am running on Google Gemini 2.0 Flash Lite. My capabilities include:\n- Multimodal analysis of text, images, and documents\n- Data analysis and insights\n- Natural language processing\n- Visual content understanding...",
  "agent_name": "gemini_test_agent"
}
```

### CSV Analysis Response
```json
{
  "success": true,
  "response": "## Customer Data Analysis\n\n### Data Overview\n- 10 customers analyzed\n- Age range: 25-45 years\n- Geographic distribution: 5 major cities\n\n### Key Insights\n1. **High-value customers**: Premium segment shows 89% satisfaction\n2. **Spending patterns**: Fashion category leads with $78.50 average order\n3. **Retention opportunity**: 30% haven't purchased in 30+ days\n\n### Recommendations\n1. Target premium customers with exclusive offers\n2. Re-engage inactive customers with personalized campaigns\n3. Expand fashion inventory based on demand...",
  "agent_name": "gemini_csv_analyst"
}
```

### Image Analysis Response
```json
{
  "success": true,
  "response": "## Image Analysis\n\n### Visual Description\nThe image shows a business chart with quarterly sales data. I can see:\n- Bar chart with 4 quarters of data\n- Y-axis shows revenue in thousands\n- Upward trend from Q1 to Q4\n- Title reads 'Quarterly Sales Performance 2024'\n\n### Extracted Text\n- Q1: $125K\n- Q2: $180K\n- Q3: $220K\n- Q4: $285K\n\n### Insights\n- 128% growth from Q1 to Q4\n- Consistent upward trajectory\n- Strong Q4 performance suggests seasonal factors...",
  "agent_name": "gemini_image_analyzer"
}
```

## 🔧 Troubleshooting

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Connection refused | Server not running | Start with `uvicorn app.api:app --reload` |
| Agent not found | Wrong agent name | Check `config/gemini-test.yaml` for valid names |
| File not found | Incorrect file path | Verify file exists and path is correct |
| Rate limit exceeded | API quota reached | Wait or upgrade Google API plan |
| Invalid API key | Wrong/missing key | Check `GOOGLE_API_KEY` in `.env` |

### Debug Commands

Check server status:
```bash
curl -X GET "http://localhost:8000/health"
```

Test configuration:
```bash
curl -X POST "http://localhost:8000/worker" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "gemini_test_agent",
    "input": "What model are you running on?",
    "config_path": "config/gemini-test.yaml"
  }'
```

## 📁 Test Files

### Provided Files
- `customer_data.csv` - Customer demographics and behavior
- `sample_sales_data.csv` - Sales transactions and performance

### Optional Test Files
Create these for comprehensive testing:
- `test_image.jpg` - Any image for visual analysis
- `chart.png` - Business chart or graph
- `document.jpg` - Document image for OCR testing

## 🎯 Success Criteria

Your Google Gemini integration is working correctly when:

✅ **Health Check**: API returns 200 OK  
✅ **Model Confirmation**: Agents confirm running on Google Gemini  
✅ **Text Processing**: Natural language responses with insights  
✅ **CSV Analysis**: Data structure analysis with business recommendations  
✅ **Image Analysis**: Detailed visual descriptions with text extraction  
✅ **Multimodal**: Combined analysis of different file types  
✅ **Supervision**: Multi-agent coordination for complex tasks  

## 🚀 Next Steps

1. **Run the tests** using your preferred script
2. **Customize prompts** for your specific use cases
3. **Add your own data** files for testing
4. **Integrate with your workflows** using the API patterns
5. **Scale up** with production API keys and configurations

## 📚 Additional Resources

- [Google Gemini Integration Documentation](docs/GOOGLE_GEMINI_INTEGRATION.md)
- [File Upload API Guide](docs/FILE_UPLOAD_API.md)
- [Testing Scripts README](scripts/README.md)
- [Google AI API Documentation](https://ai.google.dev/gemini-api/docs)

---

**Ready to test your Google Gemini integration!** 🎉

Start with the health check, then try the basic text processing test, and gradually work through the more complex multimodal scenarios.
