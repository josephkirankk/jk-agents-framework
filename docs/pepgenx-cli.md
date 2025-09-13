# PepGenX CLI Tool

A command-line interface for testing PepGenX API endpoints. This tool allows you to list available models and test them with custom prompts.

## Setup

### Prerequisites

1. Python 3.7+ with required packages:
   ```bash
   pip install requests python-dotenv
   ```

2. Valid OKTA token file (`okta_token.json`) in the project root
3. Configured `.env` file with PepGenX credentials

### Environment Configuration

The tool requires these environment variables in your `.env` file:

```bash
# Required
PEPGENX_API_BASE=https://apim-na.qa.mypepsico.com/cgf/pepgenx
PEPGENX_PROJECT_ID=your-project-id
PEPGENX_TEAM_ID=your-team-id
PEPGENX_API_KEY=your-api-key

# Optional
PEPGENX_USER_ID=cli-user
OKTA_TOKEN_FILE=okta_token.json
```

### OKTA Token

The tool expects an `okta_token.json` file in the project root with the format:
```json
{
  "access_token": "your-bearer-token-here",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

## Usage

### List Available Models

```bash
python scripts/pepgenx_cli.py list
```

This will display all available models with their providers and restriction status:

### Show System Prompts

```bash
python scripts/pepgenx_cli.py prompts
```

This will display all available system prompts with their descriptions:

```
✅ Found 15 models:
--------------------------------------------------------------------------------
Model Name                     Provider        Restricted
--------------------------------------------------------------------------------
gpt-4o                        openai          
gpt-4o-mini                   openai          
claude-3-5-sonnet             aws-anthropic   
llama-3.3-70b-instruct        aws-meta        ✓
nova-lite                     aws-nova
--------------------------------------------------------------------------------

```
Available System Prompts:
================================================================================
1: Content Safety Analyzer - Analyzes prompts against 16 content guidelines
2: Adobe Firefly Image Optimizer - Refines prompts for image generation (DEFAULT) ⭐
3: PepsiCo ESG Assistant - Expert for Environmental/Social/Governance queries
4: System Prompt Generator - Creates detailed system prompts for LLMs
5: Prompt Enhancer - Improves clarity, tone, and effectiveness
6: Tool-Aware Assistant - AI assistant with external tool access
7: Prompt Adaptation Expert - Adapts prompts between different AI models
================================================================================
```

### Test a Model

```bash
# Basic test with defaults
python scripts/pepgenx_cli.py test --model gpt-4o

# Custom user prompt
python scripts/pepgenx_cli.py test --model claude-3-5-sonnet --user-prompt "Explain quantum physics"

# Custom system prompt and user prompt
python scripts/pepgenx_cli.py test --model gpt-4o --system-prompt 1 --user-prompt "What is 2+2?"
```

### Command Options

#### `list` command
- No additional options required
- Lists all available models from the API

#### `prompts` command
- No additional options required
- Shows all available system prompts with descriptions

#### `test` command
- `--model, -m` (required): Model name to test
- `--system-prompt, -s` (optional): System prompt ID (default: 2 - Adobe Firefly Image Optimizer)
- `--user-prompt, -u` (optional): User prompt text (default: "Hello, how are you?")

## System Prompts Explained

Each system prompt ID corresponds to a specific AI assistant persona optimized for different tasks:

### **1 - Content Safety Analyzer**
- Analyzes user prompts against 16 strict content guidelines
- Checks for IP violations, sports teams, public figures, illegal content
- Provides content categorization and violation severity assessment
- **Use for**: Content moderation and safety compliance

### **2 - Adobe Firefly Image Optimizer** ⭐ *(Default)*
- Refines prompts for Adobe Firefly text-to-image generation
- Focuses on clear, minimalistic designs with vivid descriptions
- Removes unnecessary words, incorporates recommended colors
- Avoids text/numbers in images, uses descriptive language
- **Use for**: Image generation and creative visual tasks

### **3 - PepsiCo ESG Assistant**
- Expert assistant for Environmental, Social, and Governance queries
- Provides structured answers about PepsiCo's ESG performance
- References specific documents with page numbers and footnotes
- **Use for**: ESG-related questions and corporate sustainability topics

### **4 - System Prompt Generator**
- Creates detailed system prompts for language models
- Includes reasoning before conclusions, clear formatting guidelines
- **Use for**: Meta-prompting and creating prompts for other AI systems

### **5 - Prompt Enhancer**
- General prompt improvement specialist
- Enhances clarity, tone, and effectiveness while preserving intent
- **Use for**: General assistance and prompt optimization

### **6 - Tool-Aware Assistant**
- AI assistant with external tool access capabilities
- Analyzes queries and determines if tools are needed
- **Use for**: Complex tasks requiring external data or tools

### **7 - Prompt Adaptation Expert**
- Adapts prompts between different AI models
- Makes minimal necessary changes for model compatibility
- **Use for**: Cross-model prompt optimization

## Examples

```bash
# List all models
python scripts/pepgenx_cli.py list

# Show system prompts
python scripts/pepgenx_cli.py prompts

# Test OpenAI GPT-4o with default prompts
python scripts/pepgenx_cli.py test --model gpt-4o

# Test Anthropic Claude with custom prompt
python scripts/pepgenx_cli.py test --model claude-3-5-sonnet --user-prompt "Write a haiku about AI"

# Test with specific system prompt
python scripts/pepgenx_cli.py test --model gpt-4o-mini --system-prompt 1 --user-prompt "Calculate 15 * 23"

# Test reasoning model
python scripts/pepgenx_cli.py test --model o1-mini --user-prompt "Solve this logic puzzle: If all roses are flowers and some flowers are red, can we conclude that some roses are red?"
```

## Provider Auto-Detection

The tool automatically detects the correct provider endpoint based on the model name:

- **OpenAI**: `gpt-*`, `gpt4*`, `gpt5*` → `/v2/llm/openai/generate-response`
- **Anthropic**: `claude-*`, `claude3*`, `claude4*` → `/v2/llm/aws-anthropic/generate-response`
- **Meta**: `llama-*`, `llama3*`, `llama4*` → `/v2/llm/aws-meta/generate-response`
- **Nova**: `nova-*`, `nova*` → `/v2/llm/aws-nova/generate-response`
- **Databricks**: `databricks*` → `/v2/llm/databricks/generate-response`

## Output Format

### Successful Response
```
Testing model: gpt-4o
Provider: openai
URL: https://apim-na.qa.mypepsico.com/cgf/pepgenx/v2/llm/openai/generate-response
System prompt: 2
User prompt: Hello, how are you?
------------------------------------------------------------
Status Code: 200
✅ Response: Hello! I'm doing well, thank you for asking. I'm here and ready to help you with any questions or tasks you might have. How are you doing today?
```

### Error Response
```
Testing model: invalid-model
Provider: openai
URL: https://apim-na.qa.mypepsico.com/cgf/pepgenx/v2/llm/openai/generate-response
System prompt: 2
User prompt: Hello, how are you?
------------------------------------------------------------
Status Code: 400
❌ Error Response: {"error": "Invalid model specified"}
```

## Troubleshooting

### Common Issues

1. **Missing environment variables**
   ```
   Error: Missing required environment variables: PEPGENX_PROJECT_ID, PEPGENX_TEAM_ID
   ```
   - Check your `.env` file and ensure all required variables are set

2. **OKTA token file not found**
   ```
   Error loading OKTA token: OKTA token file not found: okta_token.json
   ```
   - Ensure `okta_token.json` exists in the project root
   - Check the `OKTA_TOKEN_FILE` environment variable if using a different filename

3. **Invalid access token**
   ```
   Status Code: 401
   ❌ Error Response: {"error": "Unauthorized"}
   ```
   - Your OKTA token may have expired
   - Refresh your token using the OKTA authentication flow

4. **Model not found**
   ```
   Status Code: 400
   ❌ Error Response: {"error": "Invalid model specified"}
   ```
   - Use `python scripts/pepgenx_cli.py list` to see available models
   - Check the model name spelling

## Windows Usage

On Windows, activate your virtual environment first:

```cmd
# Activate virtual environment
.venv\Scripts\activate

# Run the CLI
python scripts\pepgenx_cli.py list
python scripts\pepgenx_cli.py test --model gpt-4o --user-prompt "Hello world"
```
