# Python Execution Troubleshooting Guide

## Issue: Python Code Not Executed

### Problem Description
When using the `python_exec_agent`, the agent generates Python code in markdown format but doesn't actually execute it using the `run_python_code` tool.

### Root Cause Analysis

The primary issue is **model compatibility with function/tool calling**. Not all models properly support the function calling capabilities required for MCP tool execution.

#### Evidence from Logs
```json
// Problematic response - no tool calls made
{
  "content": "```python\nprint((124 * (6562 + 2777382)) / 45)\n```",
  "tool_calls": [],  // ← Empty array indicates no tools were called
  "usage_metadata": {
    "input_tokens": 793,
    "output_tokens": 32
  }
}
```

#### Working Response
```json
// Successful response with tool execution
{
  "tool_calls": [
    {
      "id": "call_GNMAPN5msstqd2CO7S7FV9Jq",
      "function": {
        "name": "run_python_code",
        "arguments": "{\"python_code\":\"result = 124 * (6562 + 2777382) / 45\\nresult\"}"
      }
    }
  ]
}
```

### Models with Poor Tool Calling Support

❌ **Avoid these models for tool-heavy agents:**
- `google/gemma-3-12b` (via OpenAI-compatible endpoints)
- Most Gemma family models
- Many open-source models accessed through OpenAI-compatible wrappers
- Smaller parameter models (< 7B parameters)

### Recommended Models for Tool Calling

✅ **Excellent tool calling support:**
- `azure_openai:gpt-4.1` - **Best choice for reliability**
- `azure_openai:gpt-4o` - Fast and reliable
- `openai:gpt-4o-mini` - Cost-effective option
- `google:gemini-2.0-flash-exp` - Good Google alternative
- `google:gemini-1.5-pro` - Robust for complex tasks

### Fix Implementation

#### 1. Update Model Configuration
```yaml
# Before (problematic)
- name: "python_exec_agent"
  model: "openai:google/gemma-3-12b"

# After (working)
- name: "python_exec_agent"
  model: "azure_openai:gpt-4.1"
```

#### 2. Verify MCP Server Setup
Ensure the MCP server is correctly configured:
```yaml
mcp_servers:
  python_runner:
    description: "Run Python code via Deno + @pydantic/mcp-run-python (stdio)"
    transport: "stdio"
    command: "deno"
    args:
      - "run"
      - "-N"
      - "-R=node_modules"
      - "-W=node_modules"
      - "--node-modules-dir=auto"
      - "jsr:@pydantic/mcp-run-python"
      - "stdio"
```

#### 3. Test MCP Server Manually
```bash
# Test if Deno and MCP server work
deno --version

# Test MCP server initialization
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "clientInfo": {"name": "test", "version": "1.0"}}}' | deno run -N -R=node_modules -W=node_modules --node-modules-dir=auto jsr:@pydantic/mcp-run-python stdio
```

### Diagnostic Steps

1. **Check Agent Logs**: Look for tool calls in the log files
   ```
   agentlog/direct_agentlog_YYYYMMDD_HHMMSS.log
   ```

2. **Examine LLM Payload**: Check if tools are being called
   ```
   logs/llm_payload_python_exec_agent_YYYYMMDD_HHMMSS.json
   ```

3. **Verify Tool Loading**: Look for this in console output:
   ```
   [INFO] mcp_loader: Loaded 1 tools from MCP servers: run_python_code
   ```

4. **Check Model Binding**: Ensure tools are bound to model:
   ```
   [INFO] agent_builder: Disabled parallel tool calls for agent python_exec_agent
   ```

### Prevention Guidelines

1. **Always use models with proven tool calling capabilities**
2. **Test new models with simple tool calls before production use**
3. **Monitor logs for empty tool_calls arrays**
4. **Use Azure OpenAI or OpenAI models for critical tool-dependent workflows**

### Quick Test Command
```bash
python -m app.main --agent python_exec_agent --config config/agents_test.yaml "2+2"
```

Expected output should show actual Python execution, not just markdown code.
