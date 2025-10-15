# AI Use Case Brainstorming System - Configuration Documentation

## Overview

The **AI Use Case Brainstorming System** is an intelligent multi-agent configuration designed to help brainstorm, validate, and develop practical and creative AI use cases across industries and domains.

**Config File**: `config/ai_usecase_brainstorm.yaml`

## Key Features

### 🎯 Core Capabilities
- **Web Research**: Real-time search for current AI trends and implementations using Brave Search
- **Creative Ideation**: Generate innovative, practical AI use case ideas
- **Technical Validation**: Assess feasibility with Python code execution
- **Intelligent Synthesis**: Create clear, actionable final recommendations
- **Multi-Turn Conversations**: ChromaDB-backed memory for context continuity

### 🚀 Design Philosophy
- **Quick & Intelligent**: Responds rapidly with high-quality insights
- **Research-Backed**: Uses current data and real-world examples
- **Practical Focus**: Prioritizes implementable solutions with clear ROI
- **Creative Edge**: Balances innovation with feasibility
- **To-The-Point**: Lean workflows without unnecessary overhead

## Architecture

### Agent System

#### 1. **Brainstorm Coordinator** (Supervisor)
- **Role**: Strategic planning and workflow orchestration
- **Model**: Azure OpenAI GPT-4.1
- **Prompt**: `config/prompts/brainstorm_supervisor_prompt.txt`
- **Capabilities**:
  - Classifies request complexity (Simple/Research/Validated/Comprehensive)
  - Designs lean 1-5 step workflows
  - Optimizes for quick response times (30-60s per step)
  - Selects appropriate agents based on request type

#### 2. **Web Researcher**
- **Role**: Real-time AI/ML trend research and market intelligence
- **Model**: Azure OpenAI GPT-4.1
- **Agent Type**: ReAct (tool-calling)
- **Prompt**: `config/prompts/web_researcher_prompt.txt`
- **Tools**: Brave Search MCP (HTTP)
- **Focus**:
  - Current implementations and case studies
  - Emerging trends and technologies
  - Success metrics and ROI data
  - Technical stack information

#### 3. **Creative Thinker**
- **Role**: Generate innovative, practical AI use case ideas
- **Model**: Azure OpenAI GPT-4.1
- **Agent Type**: Normal (conversational)
- **Prompt**: `config/prompts/creative_thinker_prompt.txt`
- **Approach**:
  - Cross-domain fusion and problem inversion
  - Value-focused ideation with feasibility awareness
  - Structured use case format (Problem/Solution/Value/Tech/Edge)
  - Quality over quantity (3-7 well-crafted ideas)

#### 4. **Technical Validator**
- **Role**: Feasibility assessment and prototyping
- **Model**: Azure OpenAI GPT-4.1
- **Agent Type**: ReAct (tool-calling)
- **Prompt**: `config/prompts/technical_validator_prompt.txt`
- **Tools**: Python MCP, Analysis Functions
- **Capabilities**:
  - Technology Readiness Level (TRL) assessment
  - Resource estimation (time, team, budget)
  - Risk analysis and mitigation strategies
  - Proof-of-concept code generation

#### 5. **Synthesizer**
- **Role**: Final response creation and integration
- **Model**: Azure OpenAI GPT-4.1
- **Agent Type**: Normal (conversational)
- **Prompt**: `config/prompts/synthesizer_prompt.txt`
- **Output**:
  - Executive summary
  - Prioritized use case recommendations
  - Implementation roadmap (Quick Wins/Strategic/Future)
  - Actionable next steps

## Workflow Types

### Simple Ideation (1-2 steps, ~1-2 min)
**When**: Direct brainstorming, specific domain focus
```
creative_thinker → synthesizer
```

### Research-Backed Ideation (2-3 steps, ~2-3 min)
**When**: Need current trends, competitive analysis
```
web_researcher → creative_thinker → synthesizer
```

### Validated Concept (3-4 steps, ~3-4 min)
**When**: Technical feasibility check, prototyping needed
```
web_researcher → creative_thinker → technical_validator → synthesizer
```

### Comprehensive Ideation (4-5 steps, ~4-5 min)
**When**: Complex problems, deep analysis required
```
web_researcher → creative_thinker → technical_validator → web_researcher → synthesizer
```

## Memory System

### ChromaDB Configuration
- **Storage Path**: `./brainstorm_memory`
- **Collections**: 
  - `brainstorm_checkpoints`: Agent state persistence
  - `brainstorm_contexts`: Conversation history
- **Performance**:
  - L1 Cache: 5000 entries, 30-min TTL
  - Max Connections: 15
  - Batch Processing: Enabled (50 items)
  - Metrics: Enabled

### Conversation Memory
- **Enabled**: Yes
- **Max Conversations**: 20 concurrent sessions
- **Context Length**: 4000 tokens per session
- **Use Case**: Multi-turn brainstorming sessions with context awareness

## Setup & Prerequisites

### 1. Environment Variables (.env)
```bash
# Azure OpenAI (Required)
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_API_VERSION=2023-05-15

# Brave Search API (Required for web research)
BRAVE_API_KEY=your_brave_api_key_here
```

### 2. Brave Search MCP Server
```bash
# Option 1: Docker (Recommended)
docker run -p 8080:8080 -e BRAVE_API_KEY="your_key" brave/mcp-search-server

# Option 2: Node.js
git clone https://github.com/brave/mcp-brave-search
cd mcp-brave-search
npm install
npm start  # Runs on localhost:8080

# Get API Key: https://api.search.brave.com/app/keys
```

### 3. Deno (for Python MCP)
```bash
# macOS
brew install deno

# Windows
irm https://deno.land/install.ps1 | iex

# Linux
curl -fsSL https://deno.land/install.sh | sh
```

### 4. ChromaDB
```bash
# Should be available in your virtual environment
# If not: uv pip install chromadb
```

## Usage Examples

### Via Command Line
```bash
# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Simple ideation
python app/main.py "Generate AI use cases for healthcare" \
  --config config/ai_usecase_brainstorm.yaml

# Research-backed ideation
python app/main.py "What are the latest AI use cases in retail 2025?" \
  --config config/ai_usecase_brainstorm.yaml

# Technical validation
python app/main.py "AI use cases for predictive maintenance with feasibility analysis" \
  --config config/ai_usecase_brainstorm.yaml
```

### Via API Server
```bash
# Start the API server
./run_api_server.sh

# Simple request
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "query": "AI use cases for financial services",
    "config": "ai_usecase_brainstorm"
  }'

# With conversation continuity
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Now focus on fraud detection specifically",
    "config": "ai_usecase_brainstorm",
    "thread_id": "brainstorm-session-001"
  }'
```

### Example Queries

**Industry-Specific**:
- "AI use cases for manufacturing"
- "Healthcare AI applications in patient care"
- "Retail AI for customer experience"

**Technology-Specific**:
- "LLM use cases beyond chatbots"
- "Computer vision applications in quality control"
- "Generative AI for content creation"

**Problem-Oriented**:
- "AI solutions for reducing operational costs"
- "AI for improving customer satisfaction"
- "AI to automate manual processes"

**Validated Concepts**:
- "AI use cases for supply chain with technical feasibility"
- "Validate these AI ideas: [list your ideas]"
- "Can AI solve [specific problem]? Show me a prototype"

## Configuration Customization

### Adjust Temperature
```yaml
# In config/ai_usecase_brainstorm.yaml
temperature: 0.7  # Current: balanced (0.5-0.8)
# 0.3-0.5: More focused, less creative
# 0.8-1.0: More creative, less predictable
```

### Change Models
```yaml
models:
  default: "azure_openai:gpt-4.1"
  creative: "azure_openai:gpt-4o"  # Use GPT-4o for more creative thinking
  validator: "openai:gpt-4o-mini"  # Use cheaper model for validation
```

### Adjust Memory Settings
```yaml
memory:
  chromadb:
    l1_cache_size: 10000  # Increase for more caching
    l1_cache_ttl: 3600    # Longer TTL for extended sessions
```

### Modify Workflows
Edit `config/prompts/brainstorm_supervisor_prompt.txt` to:
- Add new workflow types
- Adjust step timeouts
- Change agent selection logic
- Modify planning principles

## Output Format

### Typical Response Structure
```
## AI Use Case Recommendations for [Domain]

### Executive Summary
[2-3 sentences with key takeaways]

### Top AI Use Case Recommendations

#### 1. [Use Case Name] - Priority: High
**What It Solves**: [Problem]
**How AI Helps**: [Solution]
**Value Proposition**: [Benefit]
**Feasibility**: Low/Medium/High
**Implementation**: [Getting started guide]
**Unique Advantage**: [Differentiation]

[Additional use cases...]

### Implementation Roadmap
**Quick Wins** (0-3 months): [...]
**Strategic Initiatives** (3-6 months): [...]
**Future Opportunities** (6+ months): [...]

### Key Insights
- [Critical insight from research/analysis]

### Next Steps
1. [Concrete action]
2. [Concrete action]
```

## Performance Characteristics

### Response Times
- **Simple Ideation**: 1-2 minutes
- **Research-Backed**: 2-3 minutes  
- **Validated Concept**: 3-4 minutes
- **Comprehensive**: 4-5 minutes

### Resource Usage
- **Memory**: ~100-200 MB (with ChromaDB)
- **API Calls**: 2-10 calls per request (depending on workflow)
- **Cache Hit Rate**: ~80% for repeated domains

## Troubleshooting

### Brave Search Not Working
```bash
# Check if server is running
curl http://localhost:8080/health

# Verify API key
echo $BRAVE_API_KEY

# Check MCP server logs
docker logs <container_id>
```

### Python MCP Issues
```bash
# Verify Deno installation
deno --version

# Test Python execution
deno run -N -R=node_modules -W=node_modules --node-modules-dir=auto \
  jsr:@pydantic/mcp-run-python stdio
```

### ChromaDB Connection Issues
```bash
# Check if port 8000 is available
lsof -i :8000

# Try different port in config
memory:
  chromadb:
    port: 8001  # Change if 8000 is in use
```

### Memory Not Persisting
- Check `./brainstorm_memory` directory exists and is writable
- Verify ChromaDB connection settings
- Check logs for memory-related errors

## Best Practices

### For Best Results
1. **Be Specific**: "AI for customer service chatbots" > "AI use cases"
2. **Provide Context**: Mention industry, constraints, or goals
3. **Use Multi-Turn**: Build on previous responses for deeper exploration
4. **Request Validation**: Add "with feasibility check" for technical validation
5. **Ask for Research**: Include "latest trends" or "real examples" for web research

### Prompt Engineering Tips
```
✅ Good: "AI use cases for predictive maintenance in manufacturing with 2025 examples"
❌ Generic: "Give me AI ideas"

✅ Good: "Can AI reduce customer support costs? Show feasibility and ROI"
❌ Vague: "AI for cost reduction"

✅ Good: "Validate these AI ideas for retail: [list]. Include implementation complexity"
❌ Unclear: "Are these good ideas?"
```

## Advanced Features

### Custom Tool Integration
Add domain-specific tools to agents:
```yaml
agents:
  - name: "technical_validator"
    python_tools:
      custom_tools:
        module_path: "tools.your_custom_tools"
        tool_names: ["industry_calculator", "compliance_checker"]
```

### External Knowledge Integration
Integrate domain-specific knowledge:
```yaml
business_context: |
  ... existing context ...
  
  **DOMAIN KNOWLEDGE:**
  - Industry: {{industry_name}}
  - Regulations: {{compliance_requirements}}
  - Budget Range: {{budget_constraint}}
```

### Multi-Language Support
Modify prompts for different languages by editing prompt files in `config/prompts/`.

## File Structure

```
config/
├── ai_usecase_brainstorm.yaml              # Main config
└── prompts/
    ├── brainstorm_supervisor_prompt.txt    # Supervisor orchestration
    ├── web_researcher_prompt.txt           # Research guidance
    ├── creative_thinker_prompt.txt         # Ideation framework
    ├── technical_validator_prompt.txt      # Validation criteria
    └── synthesizer_prompt.txt              # Final output format

brainstorm_memory/                          # ChromaDB storage (auto-created)
├── brainstorm_checkpoints/                 # Agent checkpoints
└── brainstorm_contexts/                    # Conversation history
```

## Version History

- **v1.0** (2025-01-15): Initial release
  - 4 specialized agents
  - Brave Search integration
  - Python MCP for validation
  - ChromaDB memory
  - Externalized prompts
  - 4 workflow types

## Contributing

To modify or extend this configuration:

1. **Edit Prompts**: Modify files in `config/prompts/`
2. **Test Changes**: Use temp config files for testing
3. **Update Docs**: Keep this README synchronized
4. **Version Control**: Track changes in git

## Support

For issues or questions:
- Check `temp_docs/` for additional documentation
- Review `final_docs/` for framework documentation
- See `examples/` for usage patterns
- Check API logs in `api_server.log`

---

**Last Updated**: January 15, 2025  
**Config Version**: 1.0  
**Framework**: JK-Agents v1.0.0
