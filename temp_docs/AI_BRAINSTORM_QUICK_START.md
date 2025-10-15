# AI Use Case Brainstorming - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Prerequisites Check
```bash
# Check if you're in the right directory
pwd  # Should show: .../jk-agents-core

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Verify config exists
ls config/ai_usecase_brainstorm.yaml
ls config/prompts/brainstorm*.txt
```

### 2. Environment Setup
Add to your `.env` file:
```bash
# Azure OpenAI (Required)
AZURE_OPENAI_API_KEY=your_azure_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_API_VERSION=2023-05-15

# Brave Search (Required for web research)
BRAVE_API_KEY=your_brave_key

# Get Brave key: https://api.search.brave.com/app/keys
```

### 3. Start Brave Search MCP (Terminal 1)
```bash
# Option A: Docker (easiest)
docker run -p 8080:8080 -e BRAVE_API_KEY="$BRAVE_API_KEY" brave/mcp-search-server

# Option B: Clone and run
git clone https://github.com/brave/mcp-brave-search
cd mcp-brave-search
npm install
npm start
```

### 4. Test the Config (Terminal 2)
```bash
# Simple test - creative thinking only (no research)
python app/main.py "Generate 3 AI use cases for education" \
  --config config/ai_usecase_brainstorm.yaml

# Research-backed test (requires Brave Search running)
python app/main.py "What are the latest AI use cases in healthcare 2025?" \
  --config config/ai_usecase_brainstorm.yaml
```

## 📝 Example Queries

### Industry-Focused
```bash
python app/main.py "AI use cases for manufacturing" \
  --config config/ai_usecase_brainstorm.yaml

python app/main.py "Financial services AI applications" \
  --config config/ai_usecase_brainstorm.yaml

python app/main.py "Retail AI for customer experience" \
  --config config/ai_usecase_brainstorm.yaml
```

### Technology-Focused
```bash
python app/main.py "LLM use cases beyond chatbots" \
  --config config/ai_usecase_brainstorm.yaml

python app/main.py "Computer vision applications in quality control" \
  --config config/ai_usecase_brainstorm.yaml
```

### Problem-Oriented
```bash
python app/main.py "AI solutions to reduce operational costs" \
  --config config/ai_usecase_brainstorm.yaml

python app/main.py "Can AI improve supply chain efficiency? Show feasibility" \
  --config config/ai_usecase_brainstorm.yaml
```

## 🔧 Troubleshooting

### "Connection refused on port 8080"
**Solution**: Brave Search MCP not running
```bash
# Check if it's running
curl http://localhost:8080/health

# Start it (see step 3 above)
```

### "BRAVE_API_KEY not set"
**Solution**: Add to `.env` file
```bash
echo 'BRAVE_API_KEY=your_key_here' >> .env
source .env  # Reload environment
```

### "ChromaDB connection failed"
**Solution**: Port 8000 might be in use
```bash
# Option 1: Change port in config
# Edit config/ai_usecase_brainstorm.yaml line 51:
# port: 8001  # Change from 8000

# Option 2: Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### "Prompt file not found"
**Solution**: Check prompt files exist
```bash
ls config/prompts/brainstorm*.txt
ls config/prompts/web_researcher*.txt
ls config/prompts/creative_thinker*.txt
ls config/prompts/technical_validator*.txt
ls config/prompts/synthesizer*.txt
```

## 🎯 Understanding the Workflow

### What Happens When You Run a Query?

1. **Supervisor Analyzes** → Classifies your request (Simple/Research/Validated/Comprehensive)
2. **Creates Plan** → Designs 1-5 step workflow
3. **Executes Agents** → Runs web_researcher, creative_thinker, technical_validator as needed
4. **Synthesizes** → Combines insights into final response

### Workflow Types

| Type | Steps | Time | When Used |
|------|-------|------|-----------|
| **Simple** | 1-2 | ~1-2 min | Direct brainstorming |
| **Research** | 2-3 | ~2-3 min | Need current trends |
| **Validated** | 3-4 | ~3-4 min | Need feasibility check |
| **Comprehensive** | 4-5 | ~4-5 min | Complex analysis |

## 📊 Expected Output Format

```markdown
## AI Use Case Recommendations for [Domain]

### Executive Summary
[2-3 sentences with key insights]

### Top AI Use Case Recommendations

#### 1. [Use Case Name] - Priority: High
**What It Solves**: [Problem]
**How AI Helps**: [Solution]
**Value Proposition**: [Measurable benefit]
**Feasibility**: Low/Medium/High
**Implementation**: [How to start]
**Unique Advantage**: [What makes it special]

[2-3 more use cases...]

### Implementation Roadmap
**Quick Wins** (0-3 months): [...]
**Strategic Initiatives** (3-6 months): [...]

### Next Steps
1. [Concrete action]
2. [Concrete action]
```

## 🔄 Multi-Turn Conversations

Use thread IDs for context continuity:
```bash
# First query
python app/main.py "AI use cases for e-commerce" \
  --config config/ai_usecase_brainstorm.yaml \
  --thread-id shopping-session-1

# Follow-up query (remembers context)
python app/main.py "Focus on personalization specifically" \
  --config config/ai_usecase_brainstorm.yaml \
  --thread-id shopping-session-1

# Another follow-up
python app/main.py "Show me technical feasibility for the personalization use case" \
  --config config/ai_usecase_brainstorm.yaml \
  --thread-id shopping-session-1
```

## ⚙️ API Server Usage

### Start Server
```bash
./run_api_server.sh
# Server runs on http://localhost:8000
```

### Make Requests
```bash
# Simple request
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "query": "AI use cases for healthcare",
    "config": "ai_usecase_brainstorm"
  }'

# With thread ID for continuity
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Focus on diagnostics",
    "config": "ai_usecase_brainstorm",
    "thread_id": "health-session-1"
  }'
```

## 🎨 Customization Tips

### Adjust Creativity Level
Edit `config/ai_usecase_brainstorm.yaml`:
```yaml
temperature: 0.7  # Current
# 0.3-0.5: More focused, conservative
# 0.8-1.0: More creative, experimental
```

### Use Different Models
```yaml
models:
  creative: "openai:gpt-4o"  # More creative
  validator: "openai:gpt-4o-mini"  # Cost-effective
```

### Modify Agent Prompts
Edit files in `config/prompts/`:
- `creative_thinker_prompt.txt` - Change ideation approach
- `technical_validator_prompt.txt` - Adjust validation criteria
- `synthesizer_prompt.txt` - Modify output format

## 📚 Learn More

- **Full Documentation**: `temp_docs/AI_USECASE_BRAINSTORM_CONFIG_README.md`
- **Framework Docs**: `final_docs/README.md`
- **Configuration Guide**: `docs/CONFIGURATION_GUIDE.md`

## 🎉 Success Checklist

- [ ] `.env` file configured with API keys
- [ ] Brave Search MCP running on port 8080
- [ ] Virtual environment activated
- [ ] YAML config validates successfully
- [ ] All prompt files present
- [ ] First test query runs successfully

---

**Ready to brainstorm?** Start with a simple query and explore! 🚀

```bash
python app/main.py "AI use cases for your_industry_here" \
  --config config/ai_usecase_brainstorm.yaml
```
