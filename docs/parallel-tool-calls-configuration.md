# Parallel Tool Calls Configuration

## Overview

The JK Agents Framework now supports configurable parallel tool calls to address compatibility issues with certain AI providers, particularly Google Gemini models. Parallel tool calls allow an LLM to invoke multiple tools simultaneously, but this feature is not supported by all providers.

## Configuration Options

You can configure parallel tool calls at three levels:

1. **Agent Level** (highest priority)
2. **Application Level** (medium priority)
3. **Auto-detection** (lowest priority, based on model provider)

### Agent Level Configuration

Configure parallel tool calls for individual agents in your YAML config:

```yaml
agents:
  - name: my_agent
    model: google:gemini-2.5-flash
    parallel_tool_calls_enabled: false  # Explicitly disable for this agent
    prompt: "You are a helpful assistant."
    mcp_servers:
      python_runner:
        transport: stdio
        command: deno

  - name: openai_agent
    model: openai:gpt-4o
    parallel_tool_calls_enabled: true   # Explicitly enable for this agent
    prompt: "You are a helpful assistant."
```

### Application Level Configuration

Set a global default for all agents in your application:

```yaml
models:
  default: "openai:gpt-4o"
  supervisor: "openai:gpt-4o"

# Global setting - applies to all agents unless overridden
parallel_tool_calls_enabled: false

supervisor:
  name: supervisor
  model: openai:gpt-4o
  prompt: "You are a supervisor."

agents:
  - name: agent1
    # Will inherit the global setting (false)
    prompt: "You are agent 1."
  
  - name: agent2  
    parallel_tool_calls_enabled: true  # Override global setting
    prompt: "You are agent 2."
```

### Auto-detection (Default Behavior)

When neither agent-level nor application-level settings are provided, the framework automatically detects the appropriate setting based on the model provider:

- **Google Gemini models**: `parallel_tool_calls=false` (disabled)
- **All other models**: `parallel_tool_calls=true` (enabled)

Supported model prefixes for auto-detection:
- `google:*` → parallel tool calls disabled
- `openai:*` → parallel tool calls enabled
- `anthropic:*` → parallel tool calls enabled
- `azure_openai:*` → parallel tool calls enabled

## Configuration Priority

The configuration follows this priority order:

1. **Agent-specific setting** (`agents[].parallel_tool_calls_enabled`)
2. **App-wide setting** (`parallel_tool_calls_enabled`)
3. **Auto-detection** (based on model provider)

## Example Configurations

### Mixed Environment (Google + OpenAI)

```yaml
models:
  default: "openai:gpt-4o"
  supervisor: "google:gemini-2.5-flash"

# No global setting - let auto-detection handle it

supervisor:
  name: supervisor
  model: google:gemini-2.5-flash  # Auto-detected: disabled
  prompt: "You are a supervisor."

agents:
  - name: gemini_agent
    model: google:gemini-2.5-flash  # Auto-detected: disabled
    prompt: "You are powered by Gemini."
    
  - name: openai_agent
    model: openai:gpt-4o           # Auto-detected: enabled
    prompt: "You are powered by OpenAI."
```

### Force Enable for All Models

```yaml
# Override auto-detection for all agents
parallel_tool_calls_enabled: true

models:
  default: "google:gemini-2.5-flash"

supervisor:
  name: supervisor
  prompt: "You are a supervisor."

agents:
  - name: gemini_agent
    # Will use global setting: enabled (despite being Gemini)
    prompt: "You are a Gemini agent with parallel calls enabled."
```

### Force Disable for All Models

```yaml
# Disable parallel tool calls globally
parallel_tool_calls_enabled: false

models:
  default: "openai:gpt-4o"

supervisor:
  name: supervisor
  prompt: "You are a supervisor."

agents:
  - name: openai_agent
    # Will use global setting: disabled (despite being OpenAI)
    prompt: "You are an OpenAI agent with parallel calls disabled."
```

## Logging

The framework logs the parallel tool calls decision for each agent during initialization:

```
INFO: Parallel tool calls for agent my_agent: False (agent=None, app=False, autodetect=False)
INFO: Parallel tool calls for agent openai_agent: True (agent=True, app=False, autodetect=True)
```

The log shows:
- Final decision (`True` or `False`)
- Agent-level setting (`None` if not specified)
- App-level setting (`None` if not specified) 
- Auto-detected value based on model provider

## Troubleshooting

### Google Gemini Errors

If you encounter errors with Google Gemini models related to parallel tool calls, ensure the setting is disabled:

1. **Agent-level override**: Add `parallel_tool_calls_enabled: false` to the agent config
2. **App-level setting**: Add `parallel_tool_calls_enabled: false` to the root config
3. **Verify auto-detection**: Check logs to confirm the setting is `False`

### Performance Considerations

- **Enabled**: Tools can run in parallel, potentially faster execution
- **Disabled**: Tools run sequentially, may be slower but more compatible

Choose based on your provider capabilities and performance requirements.