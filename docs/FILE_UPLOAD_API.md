# File Upload API Documentation

This document describes the file upload functionality for the JK-Agents system, which allows you to upload files and send them to AI models for analysis.

## Overview

The file upload API enables you to:
- Upload multiple files (images, documents, etc.) to OpenAI/Azure OpenAI
- Attach files to agent requests for multimodal analysis
- Get text responses that incorporate file content analysis
- Support both vision models (for images) and document analysis

## Supported File Types

### Images (Vision Models)
- **PNG** (.png)
- **JPEG** (.jpeg, .jpg) 
- **WEBP** (.webp)
- **GIF** (.gif, non-animated)

### Documents (Assistants API)
- **PDF** (.pdf)
- **Text files** (.txt, .md)
- **JSON/JSONL** (.json, .jsonl)
- **CSV** (.csv)
- **Other document formats**

## File Size Limits

- **Individual files**: Up to 512 MB
- **Total request payload**: Up to 50 MB for vision models
- **Images**: Up to 20 MB per image (Azure OpenAI)
- **Organization storage**: Up to 1 TB total

## API Endpoints

### File Upload Worker Endpoint

**POST** `/worker/upload`

Upload files and execute an agent with file attachments.

#### Request Format

**Content-Type**: `multipart/form-data`

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `agent_name` | string | Yes | Name of the agent to execute |
| `input` | string | Yes | User question or prompt |
| `config_path` | string | No | Path to configuration file |
| `files` | file[] | Yes | Array of files to upload |

#### Example Request (cURL)

```bash
curl -X POST "http://localhost:8000/worker/upload" \
  -F "agent_name=python_exec_agent" \
  -F "input=Analyze this image and tell me what you see" \
  -F "config_path=config/gemba-predictive-v1.yaml" \
  -F "files=@image.jpg" \
  -F "files=@document.pdf"
```

#### Example Request (Python)

```python
import requests

url = "http://localhost:8000/worker/upload"

# Form data
data = {
    "agent_name": "python_exec_agent",
    "input": "Analyze these files and provide insights",
    "config_path": "config/gemba-predictive-v1.yaml"
}

# Files to upload
files = [
    ("files", ("image.jpg", open("image.jpg", "rb"), "image/jpeg")),
    ("files", ("data.csv", open("data.csv", "rb"), "text/csv"))
]

response = requests.post(url, data=data, files=files)
result = response.json()

print(f"Success: {result['success']}")
print(f"Response: {result['response']}")
```

#### Response Format

```json
{
  "success": true,
  "response": "Based on the uploaded image, I can see...",
  "agent_name": "python_exec_agent",
  "metadata": {
    "agent_name": "python_exec_agent",
    "model_used": "azure_openai:gpt-4.1",
    "business_context": true,
    "files_uploaded": 2,
    "file_info": [
      {
        "filename": "image.jpg",
        "file_id": "file-abc123",
        "mime_type": "image/jpeg",
        "purpose": "vision",
        "size": 1024000
      }
    ]
  }
}
```

## Configuration

### Environment Variables

The system automatically detects and uses the appropriate OpenAI client based on environment variables:

#### Azure OpenAI (Recommended)
```bash
# Option 1: API Key Authentication
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"
export AZURE_OPENAI_API_KEY="your-api-key"

# Option 2: Token-based Authentication (More Secure)
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"
# No API key needed - uses Azure CLI authentication
```

#### Regular OpenAI
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

### Agent Configuration

Ensure your agents are configured to handle multimodal inputs. Example configuration:

```yaml
agents:
  - name: "vision_agent"
    description: "Analyzes images and documents"
    model: "azure_openai:gpt-4.1"  # Vision-capable model
    prompt: |
      You are a helpful assistant that can analyze images and documents.
      When files are attached, analyze them thoroughly and provide detailed insights.
      
      For images: Describe what you see, identify objects, text, and any notable features.
      For documents: Summarize content, extract key information, and answer questions.
```

## How It Works

1. **File Upload**: Files are uploaded to OpenAI/Azure OpenAI using the Files API
2. **File Processing**: Each file gets a unique file ID and is categorized by type
3. **Message Construction**: The system creates multimodal messages with file references
4. **Agent Execution**: The agent processes the enhanced input with file attachments
5. **Response Generation**: The AI model analyzes files and generates a comprehensive response

## Error Handling

Common error scenarios and responses:

### File Upload Errors
```json
{
  "success": false,
  "error": "Failed to upload file image.jpg: File size exceeds limit"
}
```

### Agent Not Found
```json
{
  "success": false,
  "error": "Agent 'invalid_agent' not found. Available agents: python_exec_agent, vision_agent"
}
```

### Configuration Errors
```json
{
  "success": false,
  "error": "Failed to load config from invalid_path.yaml: File not found"
}
```

## Best Practices

1. **File Size**: Keep files under recommended limits for better performance
2. **File Types**: Use appropriate file types for your use case
3. **Clear Prompts**: Provide specific instructions about what you want analyzed
4. **Error Handling**: Always check the `success` field in responses
5. **Cleanup**: Files are automatically managed by OpenAI's retention policies

## Testing

Use the provided test script to verify functionality:

```bash
python test_file_upload.py
```

This will test both file upload and regular endpoints to ensure everything works correctly.
