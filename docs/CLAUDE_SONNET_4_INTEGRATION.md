# Claude Sonnet 4 Integration Guide

## Overview

The JK-Agents system now supports **Claude Sonnet 4** integration, enabling you to leverage Anthropic's most advanced AI model alongside existing Azure OpenAI and local models. This integration provides access to Claude Sonnet 4's exceptional reasoning capabilities, creative problem-solving, and advanced analysis features.

## Features

### 🧠 Advanced Reasoning
- Complex logical analysis and multi-step reasoning
- Strategic planning and problem decomposition
- Pattern recognition and insight generation

### 🎨 Creative Capabilities
- Original content creation and storytelling
- Innovative problem-solving approaches
- Design thinking and ideation

### 📊 Analytical Excellence
- Deep data analysis and statistical reasoning
- Business intelligence and strategic insights
- Trend analysis and forecasting

### 🔄 Multi-Provider Support
- Seamless integration with existing Azure OpenAI models
- Intelligent model selection based on task requirements
- Fallback and redundancy options

## Quick Start

### 1. Install Dependencies

The Claude Sonnet 4 integration requires the `langchain-anthropic` package:

```bash
pip install langchain-anthropic>=0.3.0
```

### 2. Set Up API Key

Add your Anthropic API key to your environment:

```bash
# In .env file
ANTHROPIC_API_KEY=sk-ant-api03-your-api-key-here
```

Or set as environment variable:

```bash
export ANTHROPIC_API_KEY=sk-ant-api03-your-api-key-here
```

### 3. Configure Models

Use the `anthropic:` prefix in your YAML configuration:

```yaml
models:
  default: "anthropic:claude-sonnet-4-20250514"
  supervisor: "anthropic:claude-sonnet-4-20250514"
  backup: "azure_openai:gpt-4.1"

agents:
  - name: "claude_reasoning_agent"
    model: "anthropic:claude-sonnet-4-20250514"
    description: "Advanced reasoning using Claude Sonnet 4"
    prompt: |
      You are Claude Sonnet 4, an advanced AI assistant...
```

### 4. Test the Integration

```bash
# Test via API
curl -X POST "http://localhost:8000/worker" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "claude_reasoning_agent",
    "input": "Analyze the implications of quantum computing on cryptography",
    "config_path": "config/claude-sonnet-4-demo.yaml"
  }'

# Test via CLI
python -m app.main --config config/claude-sonnet-4-demo.yaml \
  "What are the key factors driving renewable energy adoption?"
```

## Model Naming Convention

### Supported Claude Models

```yaml
# Claude 4 Models (Latest)
"anthropic:claude-sonnet-4-20250514"
"anthropic:claude-opus-4-20250514"

# Claude 3.5 Models
"anthropic:claude-3-5-sonnet-20241022"
"anthropic:claude-3-5-haiku-20241022"

# Claude 3 Models
"anthropic:claude-3-opus-20240229"
"anthropic:claude-3-sonnet-20240229"
"anthropic:claude-3-haiku-20240307"
```

### Model Selection Guidelines

- **Claude Sonnet 4**: Best for complex reasoning, analysis, and creative tasks
- **Claude Opus 4**: Maximum capability for the most challenging problems
- **Azure OpenAI**: Reliable for consistent, predictable operations
- **Local Models**: Fast development and testing

## Configuration Examples

### Multi-Provider Setup

```yaml
models:
  # Primary: Claude Sonnet 4 for advanced tasks
  default: "anthropic:claude-sonnet-4-20250514"
  supervisor: "anthropic:claude-sonnet-4-20250514"
  
  # Backup: Azure OpenAI for reliability
  reliable: "azure_openai:gpt-4.1"
  
  # Local: LM Studio for development
  local: "openai:google/gemma-3n-e4b"

agents:
  - name: "claude_analyst"
    model: "anthropic:claude-sonnet-4-20250514"
    description: "Advanced analysis with Claude Sonnet 4"
    
  - name: "azure_processor"
    model: "azure_openai:gpt-4.1"
    description: "Reliable processing with Azure OpenAI"
    
  - name: "local_tester"
    model: "openai:google/gemma-3n-e4b"
    description: "Fast local testing"
```

### Specialized Claude Agents

```yaml
agents:
  - name: "claude_creative_writer"
    model: "anthropic:claude-sonnet-4-20250514"
    description: "Creative content generation"
    prompt: |
      You are Claude Sonnet 4 in creative mode...
      
  - name: "claude_data_scientist"
    model: "anthropic:claude-sonnet-4-20250514"
    description: "Advanced data analysis"
    prompt: |
      You are Claude Sonnet 4 in analyst mode...
      
  - name: "claude_strategist"
    model: "anthropic:claude-sonnet-4-20250514"
    description: "Strategic planning and insights"
    prompt: |
      You are Claude Sonnet 4 in strategic mode...
```

## Environment Configuration

### Required Variables

```bash
# Anthropic API Configuration
ANTHROPIC_API_KEY=sk-ant-api03-your-api-key-here
# ANTHROPIC_BASE_URL=https://api.anthropic.com  # Optional

# Multi-provider setup (optional)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-azure-key
OPENAI_API_KEY=sk-your-openai-key  # For regular OpenAI
```

### Provider Selection Logic

1. **`anthropic:*`** models → Always use Anthropic Claude API
2. **`azure_openai:*`** models → Always use Azure OpenAI
3. **`openai:*`** models → Use OpenAI API or local server (if OPENAI_BASE_URL set)

## Best Practices

### 1. Task-Appropriate Model Selection

```yaml
# Use Claude Sonnet 4 for:
- Complex reasoning and analysis
- Creative problem-solving
- Strategic planning
- Advanced data interpretation

# Use Azure OpenAI for:
- Consistent, reliable operations
- Standard data processing
- Predictable formatting tasks

# Use local models for:
- Development and testing
- High-frequency, simple tasks
- Privacy-sensitive operations
```

### 2. Prompt Engineering for Claude

```yaml
prompt: |
  You are Claude Sonnet 4, leveraging your advanced reasoning capabilities.
  
  Key strengths to utilize:
  - Multi-step logical analysis
  - Creative problem-solving
  - Detailed explanations
  - Strategic thinking
  
  When approaching this task:
  1. Break down complex problems systematically
  2. Provide clear reasoning chains
  3. Consider multiple perspectives
  4. Synthesize insights effectively
```

### 3. Error Handling and Fallbacks

```yaml
models:
  primary: "anthropic:claude-sonnet-4-20250514"
  fallback: "azure_openai:gpt-4.1"
  
# Configure agents with fallback models for reliability
```

## Troubleshooting

### Common Issues

1. **API Key Error**: Ensure `ANTHROPIC_API_KEY` is set correctly
2. **Model Not Found**: Verify model name spelling and availability
3. **Rate Limits**: Implement appropriate retry logic and delays
4. **Network Issues**: Check connectivity to api.anthropic.com

### Debug Mode

```bash
# Enable detailed logging
export LANGCHAIN_VERBOSE=true
python -m app.main --config your-config.yaml "your query"
```

## Performance Considerations

- **Claude Sonnet 4**: Higher latency but superior quality for complex tasks
- **Azure OpenAI**: Balanced performance and reliability
- **Local Models**: Fastest response times for simple tasks

## Security Notes

- Store API keys securely (environment variables, not in code)
- Use different keys for development and production
- Monitor API usage and costs
- Implement proper access controls

## Example Use Cases

### 1. Advanced Data Analysis
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Analyze this sales data and provide strategic recommendations",
    "config_path": "config/claude-sonnet-4-demo.yaml"
  }'
```

### 2. Creative Content Generation
```bash
curl -X POST "http://localhost:8000/worker" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "claude_creative_agent",
    "input": "Create a compelling product launch strategy",
    "config_path": "config/claude-sonnet-4-demo.yaml"
  }'
```

### 3. Complex Problem Solving
```bash
python -m app.main --config config/claude-sonnet-4-demo.yaml \
  "Design a sustainable supply chain optimization strategy"
```

## Next Steps

1. **Experiment** with different Claude models for your use cases
2. **Optimize** prompts for Claude's reasoning capabilities
3. **Monitor** performance and costs across providers
4. **Scale** successful configurations to production

For more examples, see `config/claude-sonnet-4-demo.yaml` and the API documentation.
