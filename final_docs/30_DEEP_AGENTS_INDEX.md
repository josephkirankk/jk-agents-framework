# Deep Agents System - Complete Documentation Index

**Version:** 1.0  
**Last Updated:** October 2025  
**Status:** Production Ready

---

## 📚 Documentation Overview

This comprehensive documentation covers the Deep Agents system integrated into `jk-agents-core`. Deep Agents enable sophisticated multi-step reasoning, context management, and hierarchical task decomposition for complex AI workflows.

---

## 🗂️ Documentation Structure

### 1. [Overview and Architecture](./30_deep_agents_overview.md)

**What's Covered:**
- What are Deep Agents and when to use them
- System architecture and component relationships
- Core concepts (middleware, subagents, memory)
- High-level design patterns

**Recommended For:**
- First-time users
- Architects designing agent systems
- Anyone wanting to understand the system holistically

**Key Sections:**
- When to Use Deep Agents vs ReAct Agents
- Architecture diagrams (high-level and detailed)
- TodoList, Filesystem, and SubAgent middleware
- Memory hierarchy and state management

---

### 2. [Configuration Guide](./31_deep_agents_configuration.md)

**What's Covered:**
- Complete YAML configuration structure
- Memory and persistence options
- Subagent configuration patterns
- MCP server integration
- Complete real-world examples

**Recommended For:**
- Developers setting up Deep Agents
- DevOps configuring deployments
- Anyone working with YAML configurations

**Key Sections:**
- Basic vs Advanced configurations
- ChromaDB memory setup
- Multi-subagent systems
- Serper Search integration example
- Environment variable management

---

### 3. [Usage Examples](./32_deep_agents_examples.md)

**What's Covered:**
- Quick start code examples
- Basic usage patterns (multi-turn, streaming, filesystem)
- Real-world scenarios (research, code analysis, product research)
- Integration examples (FastAPI, CLI tools)
- Testing examples

**Recommended For:**
- Developers implementing Deep Agents
- Anyone learning by example
- Teams building specific use cases

**Key Sections:**
- Minimal working examples
- Multi-turn conversations
- Streaming responses
- Subagent delegation
- Web research workflows
- FastAPI and CLI integrations
- Unit testing patterns

---

### 4. [Advanced Features and Best Practices](./33_deep_agents_advanced.md)

**What's Covered:**
- Prompt engineering best practices
- Performance optimization strategies
- Complex multi-stage workflows
- Extension patterns (custom middleware, MCP servers)
- Troubleshooting guide
- Production deployment considerations

**Recommended For:**
- Advanced users optimizing systems
- Teams deploying to production
- Developers extending functionality
- Anyone solving complex problems

**Key Sections:**
- Effective prompt engineering
- Task decomposition strategies
- Model selection for cost optimization
- Multi-stage research pipelines
- Custom middleware development
- Custom MCP server creation
- Error handling and monitoring
- Rate limiting and health checks

---

## 🚀 Quick Navigation

### By Use Case

**I want to...**

| Goal | Documentation | Section |
|------|---------------|---------|
| Understand what Deep Agents are | [Overview](./30_deep_agents_overview.md) | What are Deep Agents? |
| Decide if I need Deep Agents | [Overview](./30_deep_agents_overview.md) | When to Use Deep Agents |
| Set up my first Deep Agent | [Configuration](./31_deep_agents_configuration.md) | Basic Configuration |
| See working code examples | [Examples](./32_deep_agents_examples.md) | Quick Start Examples |
| Configure memory persistence | [Configuration](./31_deep_agents_configuration.md) | Memory Configuration |
| Add subagents to my system | [Configuration](./31_deep_agents_configuration.md) | Subagent Configuration |
| Integrate Google Search | [Configuration](./31_deep_agents_configuration.md) | Serper Search MCP |
| Build a research agent | [Examples](./32_deep_agents_examples.md) | Web Research Assistant |
| Optimize performance | [Advanced](./33_deep_agents_advanced.md) | Performance Optimization |
| Write better prompts | [Advanced](./33_deep_agents_advanced.md) | Prompt Engineering |
| Deploy to production | [Advanced](./33_deep_agents_advanced.md) | Production Deployment |
| Extend functionality | [Advanced](./33_deep_agents_advanced.md) | Extension Patterns |
| Troubleshoot issues | [Advanced](./33_deep_agents_advanced.md) | Troubleshooting |

### By Role

**For Developers:**
1. Start: [Overview](./30_deep_agents_overview.md) → [Examples](./32_deep_agents_examples.md)
2. Deep Dive: [Configuration](./31_deep_agents_configuration.md)
3. Optimize: [Advanced](./33_deep_agents_advanced.md)

**For Architects:**
1. Start: [Overview](./30_deep_agents_overview.md) → Architecture
2. Design: [Configuration](./31_deep_agents_configuration.md) → Complete Examples
3. Scale: [Advanced](./33_deep_agents_advanced.md) → Production Deployment

**For DevOps:**
1. Start: [Configuration](./31_deep_agents_configuration.md) → Memory Configuration
2. Monitor: [Advanced](./33_deep_agents_advanced.md) → Monitoring and Logging
3. Deploy: [Advanced](./33_deep_agents_advanced.md) → Production Deployment

---

## 📦 Key Components Reference

### Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| `deep_agent_basic_example.yaml` | Simple single-agent setup | `config/` |
| `deep_agent_advanced_example.yaml` | Multi-subagent system | `config/` |
| `deep_agent_advanced_serpapi.yaml` | Production search agent | `config/` |
| `deep_agent_azure_test.yaml` | Azure OpenAI configuration | `config/` |

### Code Files

| File | Purpose | Location |
|------|---------|----------|
| `deep_agent_adapter.py` | Core adapter logic | `app/` |
| `config.py` | Configuration models | `app/` |
| `agent_builder.py` | Agent factory | `app/` |
| `deep_agent_example.py` | Basic examples | `examples/` |
| `deep_agent_serper_example.py` | Serper integration | `examples/` |

### Test Files

| File | Purpose | Location |
|------|---------|----------|
| `test_deep_agent_comprehensive.py` | Full test suite | `temp_tests/` |
| `test_deep_agent_integration.py` | Integration tests | `temp_tests/` |
| `test_deep_agent_simple.py` | Simple unit tests | `temp_tests/` |

---

## 💾 Memory and Storage

### Memory Locations

Deep Agents use multiple storage layers:

```
Project Root/
├── serp_memory/                    # ChromaDB checkpoints (default)
│   ├── <thread-id-1>/
│   │   └── chroma.sqlite3
│   ├── <thread-id-2>/
│   └── ...
│
├── longterm_store/                 # Long-term memory (if enabled)
│   └── chroma.sqlite3
│
└── agent_workspace/                # Optional workspace
    └── memories/
```

### Memory Types

| Type | Scope | Storage | Lifetime |
|------|-------|---------|----------|
| **Ephemeral** | Current turn | Memory | Single invocation |
| **Session** | Thread | ChromaDB checkpointer | Until thread expires |
| **Long-term** | Cross-thread | LangGraph Store | Permanent |

**Details:** See [Configuration Guide → Memory Configuration](./31_deep_agents_configuration.md#memory-configuration)

---

## 🔧 Installation and Setup

### Prerequisites

```bash
# Install Deep Agents package
uv pip install deepagents

# Or with pip
pip install deepagents
```

### Environment Variables

```bash
# .env file
OPENAI_API_KEY=your-key
# OR
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-instance.openai.azure.com

# Optional: Search capabilities
SERPER_API_KEY=your-serper-key
```

### Quick Start

```python
import asyncio
from app.agent_builder import build_agent
from app.config import AgentConfig, DeepAgentConfig

async def main():
    config = AgentConfig(
        name="my_agent",
        agent_type="deep",
        model="openai:gpt-4o-mini",
        prompt="You are a helpful assistant.",
        deep_agent_config=DeepAgentConfig(enabled=True),
        mcp_servers={}, http_tools={}, python_tools={},
    )
    
    agent, _ = await build_agent(
        agent_cfg=config,
        default_model="openai:gpt-4o-mini",
    )
    
    result = agent.invoke(
        {"messages": [("user", "Hello!")]},
        config={"configurable": {"thread_id": "test"}}
    )
    
    print(result["messages"][-1].content)

asyncio.run(main())
```

**Full Tutorial:** See [Examples → Quick Start](./32_deep_agents_examples.md#quick-start-examples)

---

## 🎯 Common Use Cases

### 1. Web Research Assistant

**Goal:** Search the web, scrape content, synthesize findings

**Configuration:** `deep_agent_advanced_serpapi.yaml`

**Features:**
- Google Search via Serper MCP
- Web scraping capabilities
- Multi-subagent analysis
- Organized file storage

**Example:** [Examples → Web Research](./32_deep_agents_examples.md#scenario-1-web-research-assistant)

---

### 2. Code Analysis System

**Goal:** Analyze codebases, find bugs, suggest optimizations

**Configuration:** Custom with specialized subagents

**Features:**
- Code reading subagent
- Bug detection subagent
- Performance optimizer subagent
- Multi-stage analysis pipeline

**Example:** [Examples → Code Analysis](./32_deep_agents_examples.md#scenario-2-code-analysis-assistant)

---

### 3. Product Research Agent

**Goal:** Research products, compare prices, find buying options

**Configuration:** `deep_agent_advanced_serpapi.yaml`

**Features:**
- Region-specific search (India, US, UK)
- Price comparison
- Review analysis
- Buy URL extraction

**Example:** [Examples → Product Research](./32_deep_agents_examples.md#scenario-3-product-research-agent)

---

### 4. Multi-Stage Research Pipeline

**Goal:** Complex research with discovery, analysis, synthesis, validation

**Configuration:** Custom multi-subagent system

**Features:**
- 5-stage pipeline
- Parallel subagent execution
- Quality-adaptive workflow
- Fact-checking validation

**Example:** [Advanced → Complex Scenarios](./33_deep_agents_advanced.md#scenario-1-multi-stage-research-pipeline)

---

## 📊 Comparison: Deep Agents vs ReAct Agents

| Feature | Deep Agents | ReAct Agents |
|---------|-------------|--------------|
| **Complexity** | Multi-step, complex tasks | Single-step, simple tasks |
| **Context Management** | Virtual filesystem | Message history only |
| **Planning** | TodoList middleware | No built-in planning |
| **Subagents** | Yes, with isolation | No |
| **Memory** | Session + Long-term | Session only |
| **Performance** | Slower (more capable) | Faster (simpler) |
| **Cost** | Higher (more tokens) | Lower |
| **Best For** | Research, analysis, multi-step | Q&A, tool calls |

**Decision Guide:** [Overview → When to Use](./30_deep_agents_overview.md#when-to-use-deep-agents)

---

## 🔍 Troubleshooting Quick Reference

| Issue | Quick Fix | Documentation |
|-------|-----------|---------------|
| Context limit exceeded | Use filesystem more aggressively | [Advanced → Troubleshooting](./33_deep_agents_advanced.md#issue-1-context-window-exceeded) |
| Subagent not called | Improve description clarity | [Advanced → Troubleshooting](./33_deep_agents_advanced.md#issue-2-subagent-not-called) |
| MCP connection failed | Verify environment variables | [Advanced → Troubleshooting](./33_deep_agents_advanced.md#issue-3-mcp-server-connection-failed) |
| Memory not persisting | Check ChromaDB config | [Advanced → Troubleshooting](./33_deep_agents_advanced.md#issue-4-memory-not-persisting) |
| Poor performance | Optimize model selection | [Advanced → Performance](./33_deep_agents_advanced.md#1-model-selection-strategy) |

---

## 🌟 Best Practices Summary

### Prompt Engineering
- ✅ Include explicit tool instructions with examples
- ✅ Define clear workflows (1, 2, 3...)
- ✅ Specify file organization patterns
- ✅ Add "Take ACTION immediately" directives
- ❌ Avoid vague descriptions

### Architecture
- ✅ Use subagents for specialized tasks
- ✅ Store large data in files, not messages
- ✅ Use stronger models for main orchestration
- ✅ Use cheaper models for simple subagents
- ❌ Don't try to fit everything in context

### Configuration
- ✅ Use ChromaDB for production persistence
- ✅ Set appropriate cache sizes
- ✅ Enable metrics and monitoring
- ✅ Use environment variables for secrets
- ❌ Don't hardcode API keys

**Full Guide:** [Advanced → Best Practices](./33_deep_agents_advanced.md#best-practices)

---

## 📚 Additional Resources

### Related Documentation

- [Agent System Module](./10_module_agent_system.md) - Overall agent architecture
- [Memory System Module](./10_module_memory_system.md) - Memory implementation details
- [MCP Tools Module](./10_module_mcp_tools.md) - MCP server integration
- [Configuration System](./21_configuration_system.md) - YAML configuration reference

### External Resources

- [DeepAgents Package](https://github.com/langchain-ai/deepagents) - Official repository
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/) - State management
- [LangChain Documentation](https://python.langchain.com/) - Tool integration
- [Serper API](https://serper.dev) - Search API provider

### Example Code

- `examples/deep_agent_example.py` - Basic usage
- `examples/deep_agent_serper_example.py` - Search integration
- `examples/deep_agent_brave_search_example.py` - Alternative search
- `temp_tests/test_deep_agent_comprehensive.py` - Complete test suite

---

## 🆘 Getting Help

### Documentation Issues

1. **Can't find what you need?**
   - Check the [Quick Navigation](#-quick-navigation) section
   - Use Ctrl+F to search within documents

2. **Something unclear?**
   - Review related sections in other documents
   - Check the [Examples](./32_deep_agents_examples.md) for practical code

3. **Found an error?**
   - Document the issue with specifics
   - Note which section and what was confusing

### Technical Issues

1. **Installation problems:**
   - Verify DeepAgents package: `pip show deepagents`
   - Check Python version: `python --version` (3.9+)

2. **Runtime errors:**
   - Enable debug logging: `logging.basicConfig(level=logging.DEBUG)`
   - Check [Troubleshooting](./33_deep_agents_advanced.md#troubleshooting)

3. **Configuration errors:**
   - Validate YAML syntax
   - Compare with working examples
   - Check environment variables

---

## 📝 Documentation Maintenance

**Last Review:** October 2025  
**Next Review:** Q1 2026  
**Maintainers:** Development Team

**Change Log:**
- **2025-10:** Initial comprehensive documentation created
- **2025-10:** Added Serper Search integration examples
- **2025-10:** Documented production deployment patterns

---

## ✅ Documentation Checklist

Use this to verify you have what you need:

- [ ] Read [Overview](./30_deep_agents_overview.md) for conceptual understanding
- [ ] Reviewed [Configuration](./31_deep_agents_configuration.md) for setup
- [ ] Tried [Quick Start Example](./32_deep_agents_examples.md#quick-start-examples)
- [ ] Configured memory persistence
- [ ] Set up environment variables
- [ ] Tested basic agent invocation
- [ ] Reviewed [Best Practices](./33_deep_agents_advanced.md#best-practices)
- [ ] Set up monitoring (for production)
- [ ] Configured error handling (for production)

---

**Ready to get started?** → [Overview and Architecture](./30_deep_agents_overview.md)

**Need examples?** → [Usage Examples](./32_deep_agents_examples.md)

**Going to production?** → [Advanced Features](./33_deep_agents_advanced.md)
