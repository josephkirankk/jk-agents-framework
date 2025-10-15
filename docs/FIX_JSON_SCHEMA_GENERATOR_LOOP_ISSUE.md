# Fix: JSON Schema Generator Loop Issue

## Issue Summary

**Date**: 2025-10-12  
**Log File**: `agentlogs/agentlog_20251012121214.log`  
**Problem**: The JSON Schema Test Data Generator was going into an infinite loop because agents were returning empty responses.

## Root Cause Analysis

### Symptoms
1. The `schema_analyzer` agent was being called but returning empty responses
2. The system would retry the agent (attempt 1, attempt 2, etc.)
3. No tool calls were being made despite the prompt saying "You MUST use the run_python_code tool"
4. The workflow would never complete

### Log Evidence
```
--- Worker Response (step=s1, agent=schema_analyzer, attempt=1) ---
(empty)

--- Worker Response (step=s1, agent=schema_analyzer, attempt=2) ---
(empty)
```

### Root Causes Identified

#### 1. Contradictory Prompt Instructions
The original prompts contained contradictory instructions that confused the LLM:

**Original Problematic Instructions:**
```yaml
You ONLY communicate by running Python code.
You MUST use the run_python_code tool. Do not provide any other response.
Return ONLY the JSON metadata structure shown above
DO NOT add explanations or summaries
```

**Problem**: These instructions were interpreted as:
- "Do not provide any other response" → Don't return anything
- "Return ONLY the JSON" → But also don't return anything?
- This caused the model to either not call the tool or call it but not return results

#### 2. Model Selection Issue
The configuration was using `google:gemini-2.5-flash` which:
- Is less reliable for forced tool calling compared to GPT-4
- May not follow tool-use instructions as strictly
- Has different behavior with tool binding

#### 3. Lack of Clear Examples
The prompts didn't provide clear examples of:
- What a correct tool call looks like
- What the expected workflow is
- What NOT to do

## Solutions Implemented

### 1. Fixed Prompt Instructions

**Before:**
```yaml
You ONLY communicate by running Python code.
You MUST use the run_python_code tool. Do not provide any other response.
```

**After:**
```yaml
You are a Python code execution specialist. You MUST ALWAYS use the run_python_code tool.

CRITICAL INSTRUCTIONS:
1. Do NOT analyze the schema manually
2. Do NOT write text explanations  
3. IMMEDIATELY call the run_python_code tool with the Python code shown below
4. Return ONLY the tool's output - nothing else

EXAMPLE OF WHAT TO DO:
User provides schema → You call run_python_code(python_code="...") → Tool returns JSON → You return that JSON

EXAMPLE OF WHAT NOT TO DO:
User provides schema → You write "The schema has fields..." → WRONG! Call the tool instead!
```

### 2. Changed Model to Azure OpenAI GPT-4.1

**Before:**
```yaml
model: "google:gemini-2.5-flash"
```

**After:**
```yaml
model: "azure_openai:gpt-4.1"
```

**Reason**: GPT-4.1 has proven reliability with tool calling and follows instructions more consistently.

### 3. Updated All Four Agents

Applied the same fixes to all agents in the workflow:
1. `schema_analyzer` - Analyzes JSON Schema
2. `requirement_parser` - Parses natural language requirements
3. `data_generator` - Generates test data
4. `schema_validator` - Validates generated data

### 4. Added Clear Workflow Instructions

**Before:**
```yaml
**WORKFLOW**:
1. Call run_python_code with the schema analysis code
2. Return the JSON result from the tool
3. DO NOT add explanations or summaries
```

**After:**
```yaml
WORKFLOW:
- Step 1: Call run_python_code tool with the analysis code
- Step 2: Return the tool's JSON output as your response
- DO NOT add any commentary or explanation

EXAMPLE TOOL CALL:
Call run_python_code with python_code parameter containing the schema analysis code shown above.
The tool will execute the code and return JSON. Return that JSON as your response.
```

## Files Modified

1. `config/json_schema_test_data_generator.yaml`
   - Updated all 4 agent prompts
   - Changed model from Gemini to GPT-4.1
   - Added clear examples and workflow instructions

## Testing

### Test Script Created
`test_schema_analyzer_fix.py` - Tests that the schema_analyzer agent:
1. Properly calls the run_python_code tool
2. Returns valid JSON metadata
3. Doesn't return empty responses

### Expected Behavior After Fix

1. **schema_analyzer** receives schema → calls run_python_code → returns JSON metadata
2. **requirement_parser** receives requirements → calls run_python_code → returns JSON constraints
3. **data_generator** receives metadata + constraints → calls run_python_code → returns array of records
4. **schema_validator** receives schema + data → calls run_python_code → returns validation report

No more empty responses, no more infinite loops.

## Verification Steps

To verify the fix works:

```bash
# 1. Run the test script
python test_schema_analyzer_fix.py

# 2. Run a full workflow test
python -m pytest integration_tests/test_07_json_schema_data_generator.py -v

# 3. Test via API
curl -X POST http://localhost:8000/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "schema: {...} Request: create 10 records...",
    "config_path": "config/json_schema_test_data_generator.yaml"
  }'
```

## Lessons Learned

1. **Prompt Clarity is Critical**: Contradictory instructions confuse LLMs
2. **Model Selection Matters**: Different models have different tool-calling reliability
3. **Provide Examples**: Show both correct and incorrect behavior
4. **Test Tool Calling**: Verify agents actually call tools, not just describe what they would do
5. **Monitor Logs**: Empty responses are a red flag for prompt issues

## Related Issues

- Similar issues may exist in other configs using Gemini models with tool calling
- Consider auditing all agent prompts for contradictory instructions
- Consider standardizing on GPT-4.1 for tool-heavy workflows

## Future Improvements

1. Add automated tests for tool calling behavior
2. Create a prompt template library for common patterns
3. Add validation to detect contradictory prompt instructions
4. Consider adding a "require_tool_use: true" enforcement mechanism
5. Add better error messages when agents don't call expected tools

