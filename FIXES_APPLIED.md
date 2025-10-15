# Fixes Applied to test_data_parser_simple.yaml

## Date: 2025-10-01

## Issues Fixed

### 1. ✅ Missing Supervisor Section
**Problem:** Configuration was missing required `supervisor` field causing Pydantic validation error:
```
Field required [type=missing, input_value={}, input_type=dict]
```

**Solution:** Added complete supervisor configuration:
```yaml
supervisor:
  name: "supervisor"
  model: "azure_openai:gpt-4.1"
  prompt: |
    # Supervisor prompt that orchestrates the requirement_parser agent
    # Creates simple JSON plan with single step
```

### 2. ✅ MCP Connection Closed Error
**Problem:** MCP Python runner was starting but immediately closing with error:
```
ExceptionGroup('unhandled errors in a TaskGroup', [McpError('Connection closed')])
```

**Root Cause:** The agent prompt contained an extremely long embedded Python template (~5000+ chars) that was:
- Too complex for reliable parsing
- Causing the MCP server to crash or timeout
- Making the LLM response unpredictable

**Solution:** Simplified the prompt from 5000+ characters to 1841 characters by:
1. Removing the long embedded Python code template
2. Providing concise extraction guidelines instead
3. Giving a minimal Python structure example
4. Letting the LLM generate the actual parsing code

**Before:** Long embedded template with complete parsing logic
**After:** Simple guidelines with minimal example structure

### 3. ✅ MCP Server Configuration
**Confirmed Working Configuration:**
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

## Test Results

### Simple Query Test
```bash
curl --location 'http://localhost:8000/query/form' \
  --form 'input="create 10 records for metric test"' \
  --form 'config_path="config/test_data_parser_simple.yaml"'
```

**Result:** ✅ SUCCESS
```json
{
  "record_count": 10,
  "metrics": ["test"],
  "program_code": "MFG",
  "sector": "PFNA",
  "plant_code": "p1",
  ...
}
```

### Complex Query Test
```bash
curl --location 'http://localhost:8000/query/form' \
  --form 'input="create 100 records for metric abcd, xyz, program MFG, sector PFNA, plant p1, values 100 to 10000, uom count, 10% negative from -10 to -100"'
```

**Result:** ✅ SUCCESS
```json
{
  "record_count": 100,
  "metrics": ["abcd", "xyz", ...],
  "program_code": "MFG",
  "sector": "PFNA",
  "plant_code": "p1",
  "value_range": {"min": 100, "max": 10000},
  "negative_percentage": 0.1,
  "negative_range": {"min": -100, "max": -10},
  "uom": "count",
  ...
}
```

## Memory Logging Note

Memory logs are only created when there's conversation history to log. For new thread IDs with no prior conversation, no log file is generated. This is expected behavior.

To see memory logs:
1. Make multiple requests with the same `thread_id`
2. Check `memory_logs/` directory for logs with that thread ID
3. Or check logs with pattern: `memory_thread-<uuid>_*.log`

## Performance Impact

- **Before fix:** MCP connection error, no response
- **After fix:** ~3-5 second response time with correct JSON parsing
- **Prompt size reduction:** 5000+ chars → 1841 chars (63% reduction)

## Working MCP Configuration Reference

This configuration is confirmed working and should be used for all Python execution agents:

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

**Note:** Despite the deprecation warning from the package, it works correctly with this configuration.
