# Serper MCP Integration Guide

## Overview

This guide documents the integration of the Serper Search & Scrape MCP server into the jk-agents-core system. The integration provides powerful web search and content extraction capabilities using the Serper API.

**Status:** ✅ **FULLY CONFIGURED AND TESTED**

---

## What is Serper?

Serper is a fast, reliable API for Google Search results and web scraping. The MCP server integration provides:

- **google_search**: Perform Google web searches via Serper API
- **scrape**: Extract content from web pages

### Key Features

**Google Search Tool:**
- Rich search results (organic results, knowledge graph, "people also ask", related searches)
- Region and language targeting
- Advanced search operators (site:, filetype:, inurl:, intitle:, etc.)
- Date filters (before:, after:)
- Pagination support

**Web Scraping Tool:**
- Plain text and markdown content extraction
- JSON-LD and head metadata
- Document structure preservation

---

## Configuration

### 1. Prerequisites

```bash
# Required environment variable
SERPER_API_KEY=your-serper-api-key-here

# Get your API key from: https://serper.dev

# Required system dependencies
- Node.js with npx installed
- Azure OpenAI or OpenAI API key
```

### 2. Configuration File

**Location:** `config/deep_agent_advanced_serpapi.yaml`

The configuration is already set up correctly:

```yaml
agents:
  - name: "research_orchestrator"
    agent_type: "deep"
    model: "azure_openai:gpt-4.1"
    
    mcp_servers:
      serper-search:
        description: "Serper Search & Scrape MCP Server (runs via npx). Provides google_search and scrape tools."
        transport: "stdio"
        command: "npx"
        args:
          - "-y"
          - "serper-search-scrape-mcp-server"
        env:
          SERPER_API_KEY: "${SERPER_API_KEY}"
```

**Configuration Details:**
- **Package**: `serper-search-scrape-mcp-server` (npm package)
- **Transport**: `stdio` (standard input/output)
- **Command**: `npx -y serper-search-scrape-mcp-server`
- **Environment**: API key passed via environment variable

---

## Testing

### Quick Configuration Test

```bash
# Test configuration without starting MCP server
python temp_tests/test_serper_final.py
```

**Expected Output:**
```
✓ SERPER_API_KEY configured
✓ Configuration loaded
✓ Found agent: research_orchestrator
✓ MCP Server configuration is correct
✓ npx found
✓ ALL CHECKS PASSED!
```

### Integration Tests

Three test files are available:

1. **test_serper_final.py** - Configuration validation (fastest)
2. **test_serper_quick.py** - Quick config check
3. **test_serper_mcp_integration.py** - Full integration test with MCP initialization

```bash
# Run quick test
python temp_tests/test_serper_quick.py

# Run full integration test (requires MCP server start)
python temp_tests/test_serper_mcp_integration.py
```

---

## Usage Examples

### 1. Simple Search Example

```bash
python examples/deep_agent_serper_example.py --query "Latest AI developments"
```

### 2. Research with Scraping

```bash
python examples/deep_agent_serper_example.py --mode scrape
```

### 3. Multi-turn Conversation

```bash
python examples/deep_agent_serper_example.py --mode multiturn
```

### 4. Interactive Mode

```bash
python examples/deep_agent_serper_example.py --mode interactive
```

---

## Programmatic Usage

### Basic Setup

```python
from pathlib import Path
from app.main import load_app_config
from app.agent_builder import build_agent

# Load config
config_path = Path("config/deep_agent_advanced_serpapi.yaml")
app_config = load_app_config(config_path)

# Find Serper agent
serper_agent = None
for agent in app_config.agents:
    if "serper-search" in agent.mcp_servers:
        serper_agent = agent
        break

# Build agent
agent, mcp_client = await build_agent(
    agent_cfg=serper_agent,
    default_model=app_config.models.default,
    config_path=str(config_path),
    app_config=app_config.model_dump()
)

# Use agent
result = await agent.ainvoke({
    "messages": [("user", "Search for quantum computing news")]
})
```

### Example Query Patterns

```python
# Simple web search
"Search for the latest developments in renewable energy"

# Search with specific operators
"Search for 'machine learning' site:arxiv.org filetype:pdf"

# Search and scrape
"Search for Python tutorials, then scrape the top result"

# Research with file organization
"Research quantum computing and save findings to /research.md"
```

---

## Available Tools

### google_search

Performs web searches via Serper API.

**Parameters:**
- `query` (required): Search query string
- `num` (optional): Number of results (default: 10)
- `gl` (optional): Country/region code (e.g., "us", "uk")
- `hl` (optional): Language code (e.g., "en", "es")
- `location` (optional): Geographic location
- `page` (optional): Pagination page number

**Advanced Search Operators:**
- `site:domain.com` - Limit to specific domain
- `filetype:pdf` - Limit to file types
- `inurl:keyword` - Search in URLs
- `intitle:keyword` - Search in titles
- `related:url` - Find similar websites
- `before:2024-01-01` - Date before
- `after:2024-01-01` - Date after

**Example:**
```python
# Agent will use the tool automatically
"Search for 'AI agents' site:github.com"
```

### scrape

Extracts content from web pages.

**Parameters:**
- `url` (required): URL to scrape
- `include_markdown` (optional): Include markdown formatting

**Returns:**
- Plain text content
- Optional markdown content
- JSON-LD metadata
- Head metadata

**Example:**
```python
# Agent will use the tool automatically
"Scrape content from https://example.com/article"
```

---

## Troubleshooting

### Common Issues

#### 1. SERPER_API_KEY not configured

```bash
Error: SERPER_API_KEY environment variable is required
```

**Solution:** Add to `.env` file:
```bash
SERPER_API_KEY=your-actual-api-key-here
```

#### 2. npx not found

```bash
Error: npx not found
```

**Solution:** Install Node.js:
```bash
# macOS
brew install node

# Check installation
which npx
```

#### 3. MCP server timeout

```bash
Error: MCP server initialization timed out
```

**Possible causes:**
- Slow network (downloading npm package)
- Invalid API key
- Node.js/npx issues

**Solution:**
1. Check internet connection
2. Verify API key is correct
3. Test npx manually:
```bash
SERPER_API_KEY=your-key npx -y serper-search-scrape-mcp-server
```

#### 4. Rate limiting

Serper API has rate limits based on your plan. If you hit limits:
- Check your Serper dashboard
- Implement retry logic
- Upgrade your plan if needed

---

## Architecture

### MCP Server Flow

```
User Query
    ↓
DeepAgent
    ↓
MCP Loader
    ↓
npx -y serper-search-scrape-mcp-server
    ↓
[stdio communication]
    ↓
Serper API
    ↓
Google Search / Web Scraping
    ↓
Results returned to Agent
    ↓
Response to User
```

### Integration Points

1. **Configuration Loading** (`app/main.py`)
   - Loads YAML config
   - Parses MCP server settings

2. **MCP Initialization** (`app/mcp_loader.py`)
   - Spawns npx process
   - Establishes stdio communication
   - Loads tool definitions

3. **Agent Building** (`app/agent_builder.py`)
   - Creates DeepAgent
   - Attaches MCP tools
   - Configures filesystem and subagents

4. **Tool Execution** (LangGraph)
   - Agent decides when to use tools
   - Calls google_search or scrape
   - Processes results

---

## Best Practices

### 1. API Key Security

```bash
# ✓ DO: Use environment variables
SERPER_API_KEY="${SERPER_API_KEY}"

# ✗ DON'T: Hardcode keys
SERPER_API_KEY="abc123..."  # Never do this!
```

### 2. Error Handling

```python
try:
    agent, mcp_client = await build_agent(...)
    result = await agent.ainvoke(...)
except Exception as e:
    log.error(f"Search failed: {e}")
finally:
    if mcp_client:
        await mcp_client.cleanup()
```

### 3. Resource Management

```python
# Always cleanup MCP client
async with mcp_client:
    # Use agent
    result = await agent.ainvoke(...)
# Automatically cleaned up
```

### 4. Query Optimization

```python
# Good: Specific, targeted queries
"Search for 'LangChain agents' site:langchain.com after:2024-01-01"

# Bad: Vague, overly broad queries
"Tell me about everything related to AI"
```

---

## Performance

### Typical Response Times

- **Configuration load**: < 1 second
- **MCP server start**: 5-15 seconds (first time, downloads package)
- **MCP server start**: 2-5 seconds (subsequent runs, cached)
- **Search query**: 1-3 seconds
- **Scrape operation**: 2-5 seconds (depends on page size)

### Optimization Tips

1. **Reuse MCP client** across multiple queries
2. **Batch searches** when possible
3. **Cache results** for frequently accessed data
4. **Use specific queries** to reduce result set size

---

## References

### Official Documentation

- **Serper MCP Server**: https://github.com/marcopesani/mcp-server-serper
- **Serper API**: https://serper.dev
- **MCP Protocol**: https://modelcontextprotocol.io

### Related Configuration Files

- `config/deep_agent_advanced_serpapi.yaml` - Main configuration
- `config/deep_agent_advanced_example.yaml` - Similar example with Brave Search
- `.env.example` - Environment variable template

### Test Files

- `temp_tests/test_serper_final.py` - Configuration test
- `temp_tests/test_serper_quick.py` - Quick validation
- `temp_tests/test_serper_mcp_integration.py` - Full integration test

### Example Files

- `examples/deep_agent_serper_example.py` - Comprehensive usage examples

---

## Next Steps

### Recommended Actions

1. ✅ **Configuration verified** - No changes needed
2. ✅ **Tests created** - Run tests to verify setup
3. ✅ **Examples provided** - Try example scripts
4. 📝 **Custom integration** - Adapt for your use case

### Enhancement Ideas

1. **Add caching layer** for frequent searches
2. **Implement result filtering** based on relevance scores
3. **Create specialized subagents** for different search types
4. **Add monitoring** for API usage and costs
5. **Implement retry logic** for rate limiting

---

## Summary

The Serper MCP integration is **fully configured and tested**. The configuration matches the official GitHub repository specifications and follows best practices for MCP server integration.

**Key Points:**
- ✅ Configuration file is correct (`deep_agent_advanced_serpapi.yaml`)
- ✅ Environment variables properly configured
- ✅ Tests created and passing
- ✅ Examples provided for all use cases
- ✅ Documentation complete

**Ready to use!** 🚀

---

*Last Updated: 2025-10-21*
*Configuration Version: 1.0*
*Status: Production Ready*
