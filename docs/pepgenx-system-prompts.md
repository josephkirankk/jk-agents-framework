# PepGenX System Prompts Reference

This document explains what each system prompt number means in the PepGenX API and when to use them.

## Quick Reference

| ID | Name | Best For |
|----|------|----------|
| 1 | Content Safety Analyzer | Content moderation, safety compliance |
| 2 | Adobe Firefly Image Optimizer ⭐ | Image generation, creative visuals (DEFAULT) |
| 3 | PepsiCo ESG Assistant | ESG queries, sustainability topics |
| 4 | System Prompt Generator | Meta-prompting, creating AI instructions |
| 5 | Prompt Enhancer | General assistance, prompt improvement |
| 6 | Tool-Aware Assistant | Complex tasks requiring external tools |
| 7 | Prompt Adaptation Expert | Cross-model prompt optimization |

## Detailed Descriptions

### 1 - Content Safety Analyzer

**Purpose**: Analyzes user prompts against comprehensive content guidelines

**Key Features**:
- Checks against 16 strict content guidelines
- Identifies IP violations, sports teams, public figures
- Detects illegal content, violence, discrimination
- Provides content categorization and severity assessment
- Returns safety recommendations and modifications

**Use Cases**:
- Content moderation before publishing
- Safety compliance checking
- Risk assessment for user-generated content
- Corporate content review workflows

**Example Usage**:
```bash
python scripts/pepgenx_cli.py test --model gpt-4o --system-prompt 1 --user-prompt "Review this content for safety issues"
```

### 2 - Adobe Firefly Image Optimizer ⭐ (DEFAULT)

**Purpose**: Refines prompts specifically for Adobe Firefly text-to-image generation

**Key Features**:
- Optimizes for clear, minimalistic designs
- Removes unnecessary words and fillers
- Incorporates recommended color palettes
- Avoids text/numbers in generated images
- Uses vivid, descriptive language
- Maintains U.S. cultural context

**Use Cases**:
- Image generation and creative visuals
- Marketing material creation
- Design concept development
- Visual content optimization

**Example Usage**:
```bash
python scripts/pepgenx_cli.py test --model gpt-4o --system-prompt 2 --user-prompt "Create a modern logo design with blue and green colors"
```

### 3 - PepsiCo ESG Assistant

**Purpose**: Expert assistant for Environmental, Social, and Governance queries

**Key Features**:
- Provides structured ESG performance answers
- References specific documents with page numbers
- Includes footnotes and supplementary materials
- Maintains conversational, professional tone
- Shares relevant graphs and charts
- Employee-focused engagement

**Use Cases**:
- ESG reporting and metrics
- Sustainability questions
- Corporate responsibility inquiries
- Environmental impact assessments

**Example Usage**:
```bash
python scripts/pepgenx_cli.py test --model gpt-4o --system-prompt 3 --user-prompt "What are PepsiCo's carbon emission reduction targets?"
```

### 4 - System Prompt Generator

**Purpose**: Creates detailed system prompts for language models

**Key Features**:
- Generates structured AI instructions
- Includes reasoning before conclusions
- Adds [CONTEXT] placeholders
- Provides clear formatting guidelines
- Preserves user content and examples
- Optimizes for task completion

**Use Cases**:
- Meta-prompting and AI instruction creation
- Building custom AI assistants
- Prompt engineering and optimization
- Creating specialized AI workflows

**Example Usage**:
```bash
python scripts/pepgenx_cli.py test --model gpt-4o --system-prompt 4 --user-prompt "Create a system prompt for a customer service chatbot"
```

### 5 - Prompt Enhancer

**Purpose**: General prompt improvement specialist

**Key Features**:
- Enhances clarity, tone, and effectiveness
- Preserves original intent
- Improves prompt structure
- Optimizes for better AI responses
- Simple, straightforward approach

**Use Cases**:
- General assistance tasks
- Prompt optimization
- Communication improvement
- Writing enhancement

**Example Usage**:
```bash
python scripts/pepgenx_cli.py test --model gpt-4o --system-prompt 5 --user-prompt "Help me improve this prompt: 'Write something about dogs'"
```

### 6 - Tool-Aware Assistant

**Purpose**: AI assistant with external tool access capabilities

**Key Features**:
- Analyzes queries for tool requirements
- Selects appropriate external tools
- Prioritizes accuracy and completeness
- Falls back to internal knowledge when needed
- Optimizes for complex, multi-step tasks

**Use Cases**:
- Complex tasks requiring external data
- Multi-tool workflows
- Research and analysis tasks
- Data integration projects

**Example Usage**:
```bash
python scripts/pepgenx_cli.py test --model gpt-4o --system-prompt 6 --user-prompt "Analyze current market trends and provide recommendations"
```

### 7 - Prompt Adaptation Expert

**Purpose**: Adapts prompts between different AI models

**Key Features**:
- Makes minimal necessary changes
- Adjusts for model-specific requirements
- Handles instruction style differences
- Optimizes tone and formatting
- Preserves core functionality

**Use Cases**:
- Cross-model prompt optimization
- AI system migration
- Multi-provider workflows
- Prompt compatibility testing

**Example Usage**:
```bash
python scripts/pepgenx_cli.py test --model claude-3-5-sonnet --system-prompt 7 --user-prompt "Adapt this GPT-4 prompt for Claude: [your prompt here]"
```

## Choosing the Right System Prompt

### For Creative Tasks
- **System Prompt 2** (Adobe Firefly) - Image generation, visual content
- **System Prompt 5** (Prompt Enhancer) - General creative writing

### For Business Tasks
- **System Prompt 3** (ESG Assistant) - Sustainability, corporate responsibility
- **System Prompt 1** (Content Safety) - Content review, compliance

### For Technical Tasks
- **System Prompt 4** (System Prompt Generator) - AI development, prompt engineering
- **System Prompt 6** (Tool-Aware Assistant) - Complex analysis, research
- **System Prompt 7** (Prompt Adaptation) - Cross-platform optimization

### For General Use
- **System Prompt 2** (Default) - Most versatile for general tasks
- **System Prompt 5** (Prompt Enhancer) - Simple assistance and improvement

## CLI Commands

```bash
# Show all system prompts
python scripts/pepgenx_cli.py prompts

# Test with specific system prompt
python scripts/pepgenx_cli.py test --model gpt-4o --system-prompt 1 --user-prompt "Your prompt here"

# Use default system prompt (2)
python scripts/pepgenx_cli.py test --model gpt-4o --user-prompt "Your prompt here"
```
