# DeepAgents Quick Reference

## Installation

```bash
uv pip install deepagents
```

## Basic Configuration

```yaml
agents:
  - name: "my_agent"
    agent_type: "deep"
    model: "openai:gpt-4o"
    prompt: "Your system prompt with filesystem/planning instructions"
    
    deep_agent_config:
      enable_filesystem: true
      enable_todolist: true
      subagents: []
```

## With Subagents

```yaml
agents:
  - name: "orchestrator"
    agent_type: "deep"
    
    deep_agent_config:
      subagents:
        - name: "specialist1"
          description: "When to use this subagent"
          system_prompt: "What this subagent does"
          model: "openai:gpt-4o-mini"
```

## Decision Matrix

| Task Type | Agent Type | Why |
|-----------|------------|-----|
| Simple Q&A | `react` | Fast, direct |
| Complex research | `deep` | Planning, context mgmt |
| Multi-step analysis | `deep` | Subagents, organization |
| Basic chat | `normal` | No tools needed |
| Large codebase | `deep` | Filesystem, isolation |

## Common Patterns

### Research Agent
```yaml
deep_agent_config:
  enable_filesystem: true  # Store findings
  enable_todolist: true     # Plan research steps
  subagents:
    - name: "researcher"
      description: "Gather information"
    - name: "synthesizer"
      description: "Create final report"
```

### Code Analysis
```yaml
deep_agent_config:
  enable_filesystem: true  # Store per-file analysis
  subagents:
    - name: "module-analyzer"
      description: "Analyze individual modules"
```

## Filesystem Usage

```yaml
prompt: |
  File organization:
  - /research/: Findings
  - /analysis/: Analysis
  - /final_report.md: Output
  
  Always create files early, update incrementally.
```

## Performance Tips

1. **Disable unused features**:
   ```yaml
   enable_todolist: false  # If not needed
   ```

2. **Use appropriate models**:
   ```yaml
   model: "openai:gpt-4o"  # Main
   subagents:
     - model: "openai:gpt-4o-mini"  # Subs
   ```

3. **Limit subagent depth**: Don't nest subagents

## Troubleshooting

### ImportError
```bash
uv pip install deepagents
```

### Subagent not called
Improve description to be more specific about when to use it.

### Still hitting context limits
Ensure prompt emphasizes storing data in files, not conversation.

## Examples

```bash
# Basic
python examples/deep_agent_example.py --mode basic

# Advanced (with subagents)
python examples/deep_agent_example.py --mode advanced

# Comparison (ReAct vs Deep)
python examples/deep_agent_example.py --mode comparison
```

## Testing

```bash
# Run integration tests
pytest temp_tests/test_deep_agent_integration.py -v
```

## When to Use

**✅ Use DeepAgent**:
- Complex multi-step tasks
- Large context needs
- Need subtask isolation
- Research/analysis workflows

**❌ Use ReAct instead**:
- Simple tool calling
- Fast response required
- <3 tool calls
- Well-defined single task

## Full Documentation

See: `temp_docs/DEEPAGENTS_INTEGRATION.md`
