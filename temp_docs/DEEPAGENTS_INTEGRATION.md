# DeepAgents Integration Guide

## Overview

DeepAgents is an advanced agentic framework built on LangChain and LangGraph that provides sophisticated capabilities for complex, multi-step tasks. This integration brings DeepAgents' powerful features into the jk-agents-core framework while maintaining full backward compatibility with existing agent types.

### Key Capabilities

- **🗂️ Virtual Filesystem**: Organize context and findings in files to prevent context window overflow
- **📋 Task Planning**: Built-in TodoListMiddleware for systematic task decomposition
- **🤖 Subagent Spawning**: Delegate subtasks to specialized agents with isolated contexts
- **💾 Long-term Memory**: Persistent memory across conversation threads via LangGraph Store
- **✋ Human-in-the-Loop**: Native tool approval workflows for sensitive operations

---

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Configuration Reference](#configuration-reference)
4. [Use Cases](#use-cases)
5. [Examples](#examples)
6. [Architecture](#architecture)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)
9. [API Reference](#api-reference)

---

## Installation

### 1. Install DeepAgents Package

The DeepAgents package is now included in `requirements.txt`:

```bash
# Install all dependencies including DeepAgents
uv pip install -r requirements.txt

# Or install DeepAgents specifically
uv pip install deepagents
```

### 2. Verify Installation

```python
python -c "from deepagents import create_deep_agent; print('✅ DeepAgents installed')"
```

---

## Quick Start

### Basic DeepAgent Configuration

Create a YAML configuration file:

```yaml
# config/my_deep_agent.yaml

models:
  default: "openai:gpt-4o"

agents:
  - name: "research_agent"
    agent_type: "deep"  # Use DeepAgent
    model: "openai:gpt-4o"
    description: "Research agent with context management"
    
    prompt: |
      You are a research assistant with advanced capabilities:
      - Virtual filesystem for organizing information
      - Task planning via todo list
      - Systematic approach to research
      
      Store findings in files and provide structured outputs.
    
    # DeepAgent-specific configuration
    deep_agent_config:
      enabled: true
      enable_filesystem: true   # Enable file operations
      enable_todolist: true      # Enable task planning
      enable_longterm_memory: false
      subagents: []  # No subagents in basic example
```

### Using the DeepAgent

```python
import asyncio
from app.agent_builder import build_agent
from app.config import load_config

async def main():
    # Load configuration
    config = load_config("config/my_deep_agent.yaml")
    
    # Build agent
    agent, _ = await build_agent(
        agent_cfg=config.agents[0],
        default_model="openai:gpt-4o"
    )
    
    # Invoke agent
    result = agent.invoke({
        "messages": [{"role": "user", "content": "Research AI agents"}]
    }, config={"configurable": {"thread_id": "session1"}})
    
    print(result["messages"][-1].content)

asyncio.run(main())
```

---

## Configuration Reference

### Agent Type

Set `agent_type: "deep"` to create a DeepAgent:

```yaml
agents:
  - name: "my_agent"
    agent_type: "deep"  # "react" | "normal" | "deep"
    # ... other configuration
```

### DeepAgent Configuration Block

```yaml
deep_agent_config:
  # Enable/disable DeepAgents features
  enabled: true  # Default: true
  
  # Middleware configuration
  enable_filesystem: true     # Virtual filesystem (default: true)
  enable_todolist: true       # Task planning (default: true)
  enable_longterm_memory: false  # Persistent memory (default: false)
  
  # Subagents for hierarchical task decomposition
  subagents:
    - name: "subagent_name"
      description: "What this subagent does"
      system_prompt: "Subagent system prompt"
      model: "openai:gpt-4o-mini"  # Optional: different model
      tools: []  # Optional: subset of parent tools
  
  # Human-in-the-loop configuration
  interrupt_on:
    tool_name:
      allowed_decisions: ["approve", "edit", "reject"]
  
  # Store configuration for long-term memory
  store_config: {}  # Optional: advanced store config
```

### Complete Example with Subagents

```yaml
agents:
  - name: "research_orchestrator"
    agent_type: "deep"
    model: "openai:gpt-4o"
    
    prompt: |
      You are a research orchestrator with specialized subagents.
      Delegate tasks strategically and organize findings.
    
    deep_agent_config:
      enabled: true
      enable_filesystem: true
      enable_todolist: true
      
      subagents:
        - name: "web-researcher"
          description: "Conducts web research on specific topics"
          system_prompt: "You are a web research specialist."
          model: "openai:gpt-4o-mini"
          tools: ["search"]
        
        - name: "data-analyzer"
          description: "Analyzes data and statistics"
          system_prompt: "You are a data analysis specialist."
          model: "openai:gpt-4o-mini"
          tools: ["python_exec"]
```

---

## Use Cases

### Use Case 1: Deep Code Analysis

**Problem**: Analyzing large codebases overwhelms single-agent context

**DeepAgent Solution**:
```yaml
- name: "code_analyst"
  agent_type: "deep"
  prompt: |
    Analyze codebases systematically:
    1. Create /file_structure.md for organization
    2. Spawn subagents for each module
    3. Store findings in /analysis/module_name.md
    4. Synthesize final report in /final_report.md
  
  deep_agent_config:
    enable_filesystem: true
    enable_todolist: true
    subagents:
      - name: "module-analyzer"
        description: "Analyzes individual code modules"
        system_prompt: "Focus on one module, analyze thoroughly"
```

**Benefits**: 
- 3-5x larger codebases can be analyzed
- Better organization of findings
- No context pollution between modules

### Use Case 2: Multi-Step Research

**Problem**: Research requires gathering → analysis → synthesis → critique cycles

**DeepAgent Solution**:
```yaml
- name: "research_specialist"
  agent_type: "deep"
  deep_agent_config:
    enable_filesystem: true
    subagents:
      - name: "researcher"
        description: "Gathers information"
      - name: "critic"
        description: "Critiques and validates findings"
      - name: "synthesizer"
        description: "Creates final report"
```

**Benefits**:
- Iterative refinement without context bleed
- Specialized focus per phase
- Higher quality outputs

### Use Case 3: Parallel Deep Investigations

**Problem**: Multiple independent topics need investigation

**DeepAgent Solution**: Spawn parallel subagents for each topic, aggregate results

**Benefits**: 2-3x faster for parallel-suitable tasks

---

## Examples

### Example 1: Basic Research Agent

See: [`examples/deep_agent_example.py`](../examples/deep_agent_example.py)

```python
# Run basic example
python examples/deep_agent_example.py --mode basic
```

### Example 2: Advanced with Subagents

```python
# Run advanced example
python examples/deep_agent_example.py --mode advanced
```

### Example 3: Comparison with ReAct

```python
# Compare DeepAgent vs ReAct
python examples/deep_agent_example.py --mode comparison
```

### Configuration Examples

- **Basic**: [`config/deep_agent_basic_example.yaml`](../config/deep_agent_basic_example.yaml)
- **Advanced**: [`config/deep_agent_advanced_example.yaml`](../config/deep_agent_advanced_example.yaml)

---

## Architecture

### Integration Architecture

```
┌─────────────────────────────────────────────────────────┐
│           jk-agents-core Framework                       │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  Agent Types:                                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐          │
│  │  ReAct   │  │  Normal  │  │  DeepAgent   │          │
│  │ (tools)  │  │  (chat)  │  │ (planning)   │          │
│  └──────────┘  └──────────┘  └──────────────┘          │
│       ▲            ▲               ▲                     │
│       └────────────┴───────────────┘                     │
│                    │                                     │
│           ┌────────▼────────┐                            │
│           │ Agent Builder   │                            │
│           │  (Factory)      │                            │
│           └────────┬────────┘                            │
│                    │                                     │
│         ┌──────────┼──────────┐                         │
│         │          │          │                         │
│  ┌──────▼───┐ ┌───▼────┐ ┌──▼──────┐                  │
│  │  Models  │ │ Tools  │ │ Memory  │                  │
│  └──────────┘ └────────┘ └─────────┘                  │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### DeepAgent Internal Architecture

```
┌────────────────────────────────────────────┐
│         DeepAgentAdapter                    │
├────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────────────────────────┐ │
│  │      DeepAgent (from package)        │ │
│  │  ┌────────────────────────────────┐  │ │
│  │  │  TodoListMiddleware (planning) │  │ │
│  │  └────────────────────────────────┘  │ │
│  │  ┌────────────────────────────────┐  │ │
│  │  │  FilesystemMiddleware (context)│  │ │
│  │  └────────────────────────────────┘  │ │
│  │  ┌────────────────────────────────┐  │ │
│  │  │  SubAgentMiddleware (spawning)│  │ │
│  │  │  ┌──────┐ ┌──────┐ ┌──────┐   │  │ │
│  │  │  │ Sub1 │ │ Sub2 │ │ Sub3 │   │  │ │
│  │  │  └──────┘ └──────┘ └──────┘   │  │ │
│  │  └────────────────────────────────┘  │ │
│  └──────────────────────────────────────┘ │
│                                             │
└────────────────────────────────────────────┘
```

### State Flow

```
User Input
    ↓
Framework State (messages)
    ↓
DeepAgentAdapter.invoke()
    ↓
DeepAgent Internal Processing
  ├─ TodoList: Create plan
  ├─ Filesystem: Store context
  ├─ Subagents: Delegate tasks
  └─ LLM: Generate responses
    ↓
Framework State (updated messages)
    ↓
Response to User
```

---

## Best Practices

### When to Use DeepAgents

✅ **Use DeepAgents for**:
- Complex multi-step reasoning (>5 steps)
- Large context management needs
- Tasks requiring subtask isolation
- Research and analysis workflows
- Long-running conversations

❌ **Use ReAct/Normal for**:
- Simple Q&A (<3 tool calls)
- Real-time responses (<2s)
- Straightforward retrieval
- Well-defined single-step tasks

### Filesystem Best Practices

```yaml
prompt: |
  Filesystem organization:
  - /research/: Raw research findings
  - /analysis/: Analysis results
  - /drafts/: Work in progress
  - /final_report.md: Final output
  
  Always:
  1. Create clear file structure early
  2. Use descriptive filenames
  3. Update files incrementally
  4. Reference files in responses
```

### Subagent Design

**Principles**:
1. **Focused Responsibility**: Each subagent has one clear purpose
2. **Clear Interface**: Description tells main agent when to use it
3. **Context Isolation**: Subagents don't see each other's work
4. **Appropriate Models**: Use cheaper models for simple subagents

**Example**:
```yaml
subagents:
  # Good: Focused, clear purpose
  - name: "fact-checker"
    description: "Verify factual claims using search"
    model: "openai:gpt-4o-mini"
  
  # Avoid: Too broad, unclear when to use
  - name: "helper"
    description: "Helps with various tasks"
```

### Performance Optimization

1. **Disable Unused Middleware**:
   ```yaml
   deep_agent_config:
     enable_todolist: false  # If planning not needed
   ```

2. **Use Appropriate Models**:
   ```yaml
   model: "openai:gpt-4o"  # Main agent
   subagents:
     - model: "openai:gpt-4o-mini"  # Subagents
   ```

3. **Limit Subagent Depth**: Avoid subagents spawning subagents

---

## Troubleshooting

### Common Issues

#### 1. ImportError: deepagents package not found

**Problem**: DeepAgents not installed

**Solution**:
```bash
uv pip install deepagents
```

#### 2. Agent creation fails with tool binding error

**Problem**: DeepAgent handles tool binding differently

**Solution**: This is handled automatically by the adapter. If you see this error, check that tools are valid LangChain tools.

#### 3. Subagent not being called

**Problem**: Description doesn't clearly indicate when to use

**Solution**: Improve subagent description:
```yaml
# Bad
description: "Research agent"

# Good
description: "Use for web research requiring 3+ searches on academic topics"
```

#### 4. Context window overflow despite using DeepAgent

**Problem**: Not using filesystem effectively

**Solution**:
```yaml
prompt: |
  CRITICAL: Store all research findings in files immediately.
  Do NOT keep large data in conversation context.
  
  Write to /findings/topic_name.md as you work.
```

#### 5. Slower than expected performance

**Problem**: DeepAgents adds overhead for planning and organization

**Solution**: 
- Use ReAct for simple tasks
- Disable unnecessary middleware
- Use faster models for subagents

### Debug Logging

Enable detailed logging:

```python
import logging
logging.getLogger("deep_agent_adapter").setLevel(logging.DEBUG)
logging.getLogger("deepagents").setLevel(logging.DEBUG)
```

---

## API Reference

### DeepAgentAdapter

Main adapter class for integrating DeepAgents.

```python
from app.deep_agent_adapter import DeepAgentAdapter

adapter = DeepAgentAdapter(
    model=model_instance,
    tools=tools_list,
    system_prompt="System prompt",
    deep_config=config_dict,
    checkpointer=checkpointer,
    agent_name="agent_name"
)
```

**Methods**:

- `invoke(state, config)`: Synchronous invocation
- `ainvoke(state, config)`: Async invocation
- `stream(state, config)`: Streaming results
- `get_state(config)`: Get current state
- `update_state(config, values)`: Update state

### Configuration Models

#### AgentConfig

```python
from app.config import AgentConfig, DeepAgentConfig

config = AgentConfig(
    name="agent_name",
    agent_type="deep",
    model="openai:gpt-4o",
    prompt="System prompt",
    deep_agent_config=DeepAgentConfig(...)
)
```

#### DeepAgentConfig

```python
from app.config import DeepAgentConfig, SubAgentConfig

deep_config = DeepAgentConfig(
    enabled=True,
    enable_filesystem=True,
    enable_todolist=True,
    enable_longterm_memory=False,
    subagents=[SubAgentConfig(...)],
    interrupt_on={"tool_name": {...}},
    store_config={...}
)
```

#### SubAgentConfig

```python
sub_config = SubAgentConfig(
    name="subagent_name",
    description="What this subagent does",
    system_prompt="Subagent prompt",
    model="openai:gpt-4o-mini",  # Optional
    tools=["tool1", "tool2"],     # Optional
)
```

---

## Migration Guide

### From ReAct to DeepAgent

**Before** (ReAct):
```yaml
- name: "research_agent"
  agent_type: "react"
  model: "openai:gpt-4o"
  prompt: "You are a research assistant."
```

**After** (DeepAgent):
```yaml
- name: "research_agent"
  agent_type: "deep"
  model: "openai:gpt-4o"
  prompt: |
    You are a research assistant with filesystem and planning.
    Store findings in /research/ directory.
  
  deep_agent_config:
    enable_filesystem: true
    enable_todolist: true
```

### Gradual Adoption

You can mix agent types in one configuration:

```yaml
agents:
  - name: "simple_agent"
    agent_type: "react"  # Existing agent, unchanged
  
  - name: "complex_agent"
    agent_type: "deep"   # New DeepAgent
    deep_agent_config:
      # ... configuration
```

---

## Additional Resources

- **DeepAgents GitHub**: https://github.com/langchain-ai/deepagents
- **Example Scripts**: `examples/deep_agent_example.py`
- **Configuration Examples**: `config/deep_agent_*.yaml`
- **Test Suite**: `temp_tests/test_deep_agent_integration.py`

---

## Support

For issues or questions:
1. Check this documentation
2. Review example configurations
3. Enable debug logging
4. Check DeepAgents documentation

**Integration Status**: ✅ Production Ready (v1.0)

**Backward Compatibility**: ✅ Full compatibility with existing agents

**Test Coverage**: ✅ Comprehensive test suite included
