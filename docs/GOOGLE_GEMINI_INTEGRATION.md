# Google Gemini Integration Guide

This guide explains how to use Google Gemini models with full multimodal support in the JK-Agents system.

## Overview

The system now supports Google Gemini models with:
- ✅ **Full Multimodal Support**: Text, images, and file processing
- ✅ **Seamless Model Switching**: Configuration-based model selection
- ✅ **Multiple Gemini Models**: Support for different Gemini variants
- ✅ **Backward Compatibility**: Works alongside existing OpenAI, Azure, and Anthropic models

## Quick Start

### 1. Setup Google API Key

Add your Google API key to your `.env` file:

```env
# Google Gemini API Configuration
GOOGLE_API_KEY=your-google-api-key-here
```

### 2. Use Google Gemini Models

In your YAML configuration, use the `google:` prefix:

```yaml
models:
  default: "google:gemini-2.0-flash-exp"
  supervisor: "google:gemini-1.5-pro"

agents:
  - name: "multimodal_agent"
    model: "google:gemini-2.0-flash-exp"
    prompt: "You are a multimodal AI assistant..."
```

### 3. Test the Integration

```bash
# Test with the provided Gemini configuration
python -m app.main --config config/gemini-test.yaml --agent gemini_test_agent "Hello, test Google Gemini"

# Test multimodal capabilities
python -m app.main --config config/gemini-test.yaml --agent gemini_multimodal_agent "Analyze this content"
```

## Supported Models

The integration supports all Google Gemini models available through the API:

| Model ID | Description | Best For |
|----------|-------------|----------|
| `google:gemini-2.0-flash-exp` | Latest experimental model | General tasks, fast responses |
| `google:gemini-1.5-pro` | Production-ready model | Complex reasoning, analysis |
| `google:gemini-1.5-flash` | Fast, efficient model | Quick tasks, high throughput |

## Configuration Examples

### Basic Single-Agent Setup

```yaml
models:
  default: "google:gemini-2.0-flash-exp"

agents:
  - name: "gemini_assistant"
    model: "google:gemini-2.0-flash-exp"
    prompt: "You are a helpful AI assistant powered by Google Gemini."
```

### Multi-Provider Setup

```yaml
models:
  default: "google:gemini-2.0-flash-exp"
  supervisor: "anthropic:claude-sonnet-4"

agents:
  - name: "gemini_multimodal"
    model: "google:gemini-2.0-flash-exp"
    prompt: "Multimodal analysis agent..."
    
  - name: "claude_reasoning"
    model: "anthropic:claude-sonnet-4"
    prompt: "Advanced reasoning agent..."
    
  - name: "openai_coding"
    model: "openai:gpt-4o"
    prompt: "Code generation agent..."
```

### Multimodal Configuration

```yaml
agents:
  - name: "document_analyzer"
    model: "google:gemini-2.0-flash-exp"
    prompt: |
      You are a document analysis expert powered by Google Gemini.
      
      Capabilities:
      - Analyze text documents, PDFs, images
      - Extract key information and insights
      - Provide structured summaries
      - Answer questions about document content
      
      Always provide detailed, accurate analysis.
```

## Multimodal Features

Google Gemini models support processing multiple content types:

### Text Processing
- Natural language understanding
- Text analysis and summarization
- Question answering
- Content generation

### Image Analysis
- Image description and analysis
- Visual question answering
- Object detection and recognition
- Scene understanding

### Document Processing
- PDF text extraction
- Document structure analysis
- Multi-page document processing
- Table and chart analysis

## API Usage Examples

### Direct Agent Usage

```bash
# Text-only interaction
python -m app.main --config config/gemini-test.yaml --agent gemini_text_agent "Explain quantum computing"

# Multimodal interaction (when file upload is supported)
python -m app.main --config config/gemini-test.yaml --agent gemini_multimodal_agent "Analyze this image" --file image.jpg
```

### Supervised Multi-Agent

```bash
# Complex task with multiple agents
python -m app.main --config config/gemini-test.yaml "Create a comprehensive analysis of renewable energy trends"
```

## Rate Limits and Quotas

Google Gemini API has rate limits:

### Free Tier Limits
- **Requests per minute**: 15 requests/minute
- **Requests per day**: 1,500 requests/day
- **Tokens per minute**: 32,000 tokens/minute

### Best Practices
1. **Use appropriate models**: Choose the right model for your task
2. **Implement retry logic**: The system automatically retries on rate limits
3. **Monitor usage**: Track your API usage in Google AI Studio
4. **Consider paid tiers**: For production use, consider upgrading

## Troubleshooting

### Common Issues

#### 1. API Key Not Found
```
GOOGLE_API_KEY not found in environment
```
**Solution**: Add your API key to the `.env` file

#### 2. Rate Limit Exceeded
```
429 You exceeded your current quota
```
**Solution**: Wait for the rate limit to reset or upgrade your plan

#### 3. Model Not Found
```
Unable to infer model provider for model='google:...'
```
**Solution**: Ensure you're using the correct `google:` prefix

### Debug Mode

Enable detailed logging:

```bash
export LANGCHAIN_VERBOSE=true
python -m app.main --config config/gemini-test.yaml "your query"
```

## Integration Architecture

The Google Gemini integration uses a custom model factory pattern:

1. **Model Detection**: System detects `google:` prefix in model IDs
2. **Model Creation**: Creates `ChatGoogleGenerativeAI` instances
3. **LangGraph Integration**: Passes model instances to `create_react_agent`
4. **Seamless Operation**: Works transparently with existing system

## Next Steps

1. **Set up your API key** in the `.env` file
2. **Try the example configuration** in `config/gemini-test.yaml`
3. **Experiment with multimodal features** using file uploads
4. **Integrate with your existing workflows** by adding `google:` models to your configurations

For more advanced usage and API reference, see the [Google AI documentation](https://ai.google.dev/gemini-api/docs).
