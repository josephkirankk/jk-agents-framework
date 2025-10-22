# Serper MCP Quick Start Guide

## 🚀 Quick Setup (5 minutes)

### 1. Get Your API Key
Visit https://serper.dev and sign up for a free API key.

### 2. Add to Environment
```bash
# Edit .env file
echo "SERPER_API_KEY=your-api-key-here" >> .env
```

### 3. Verify Configuration
```bash
# Run quick test
python temp_tests/test_serper_final.py
```

**Expected:**
```
✓ ALL CHECKS PASSED!
```

### 4. Try It Out
```bash
# Simple search example
python examples/deep_agent_serper_example.py --query "AI agents"

# Interactive mode
python examples/deep_agent_serper_example.py --mode interactive
```

---

## 📋 What You Get

### Two Powerful Tools

**1. google_search**
- Google web search results
- Advanced search operators
- Rich metadata (knowledge graph, related searches)

**2. scrape**
- Extract web page content
- Get clean text and markdown
- Preserve document structure

---

## 💻 Quick Examples

### Python Code

```python
from pathlib import Path
from app.main import load_app_config
from app.agent_builder import build_agent

# Load Serper config
config_path = Path("config/deep_agent_advanced_serpapi.yaml")
app_config = load_app_config(config_path)

# Build agent
agent, mcp_client = await build_agent(
    agent_cfg=app_config.agents[0],
    default_model=app_config.models.default,
    config_path=str(config_path),
    app_config=app_config.model_dump()
)

# Search
result = await agent.ainvoke({
    "messages": [("user", "Search for Python tutorials")]
})
```

### Command Line

```bash
# Simple search
python examples/deep_agent_serper_example.py --query "machine learning"

# Research with scraping
python examples/deep_agent_serper_example.py --mode scrape

# Multi-turn conversation
python examples/deep_agent_serper_example.py --mode multiturn

# Interactive session
python examples/deep_agent_serper_example.py --mode interactive
```

---

## 🔍 Query Examples

### Basic Searches
```
"Search for latest AI news"
"Find information about quantum computing"
"Look up Python documentation"
```

### Advanced Searches
```
"Search for 'machine learning' site:arxiv.org"
"Find 'neural networks' filetype:pdf"
"Search for AI articles after:2024-01-01"
```

### Search + Scrape
```
"Search for Python tutorials and scrape the top result"
"Find latest AI news and extract content from the best article"
```

### Research Tasks
```
"Research quantum computing and save to /research.md"
"Find information about LLMs, summarize, and create a report"
```

---

## 🛠️ Troubleshooting

### Problem: API Key Error
```
Error: SERPER_API_KEY environment variable is required
```
**Solution:** Add key to `.env` file

### Problem: npx Not Found
```
Error: npx not found
```
**Solution:** Install Node.js: `brew install node`

### Problem: Timeout
```
Error: MCP server initialization timed out
```
**Solution:** Check internet connection, wait for package download

---

## 📚 Resources

- **Full Guide**: `temp_docs/SERPER_MCP_INTEGRATION_GUIDE.md`
- **Config File**: `config/deep_agent_advanced_serpapi.yaml`
- **Tests**: `temp_tests/test_serper_*.py`
- **Examples**: `examples/deep_agent_serper_example.py`
- **Serper Docs**: https://serper.dev/docs

---

## ✅ Verification Checklist

- [ ] SERPER_API_KEY in .env file
- [ ] Node.js/npx installed
- [ ] Configuration test passes
- [ ] Can run example script

---

## 🎯 Common Use Cases

### 1. Real-time Information Retrieval
```python
"What are the latest developments in AI?"
```

### 2. Research Tasks
```python
"Research renewable energy trends and create a summary"
```

### 3. Content Extraction
```python
"Scrape content from https://example.com/article"
```

### 4. Competitive Analysis
```python
"Search for competitors in the AI space and analyze their offerings"
```

### 5. Fact-Checking
```python
"Verify: Is Python the most popular programming language?"
```

---

**Ready to go! 🚀**

Run: `python temp_tests/test_serper_final.py` to verify your setup.
