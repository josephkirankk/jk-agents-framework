# Placeholder Replacement Fix

## Issue Description

The placeholders `{{ontology}}` and `{{user_input}}` in the Pilger agent prompt were not being replaced with actual data, causing the agent to receive literal placeholder text instead of the DefectAnalysisPipeline results.

## Root Cause Analysis

The issue was in the prompt file `config/prompts/gemba-d-r-c-v11.txt`. The prompt contained example placeholders in the documentation section:

```
- **Defect codes**: `{{PREFIX}}.{{SUBSYS}}.{{COMPONENT}}.{{DEFECT}}`
- **Root cause codes**: `RC.{{CATEGORY}}.{{CAUSE}}`
- **Corrective action codes**: `CA.{{CATEGORY}}.{{ACTION}}`
```

These were meant to be documentation examples, but Jinja2 template engine was trying to resolve them as actual template variables, causing the error:

```
jinja2.exceptions.UndefinedError: 'PREFIX' is undefined
```

When the enhanced placeholder system failed, it fell back to legacy rendering, which also failed for the same reason. The final fallback used raw prompt replacement, which didn't process the `{{ontology}}` and `{{user_input}}` placeholders.

## Solution

### 1. Fixed Prompt File Template Syntax

Updated `config/prompts/gemba-d-r-c-v11.txt` to escape the example placeholders:

**Before:**
```
- **Defect codes**: `{{PREFIX}}.{{SUBSYS}}.{{COMPONENT}}.{{DEFECT}}`
- **Root cause codes**: `RC.{{CATEGORY}}.{{CAUSE}}`
- **Corrective action codes**: `CA.{{CATEGORY}}.{{ACTION}}`
```

**After:**
```
- **Defect codes**: `{{"{{PREFIX}}.{{SUBSYS}}.{{COMPONENT}}.{{DEFECT}}"}}`
- **Root cause codes**: `RC.{{"{{CATEGORY}}.{{CAUSE}}"}}`
- **Corrective action codes**: `CA.{{"{{CATEGORY}}.{{ACTION}}"}}`
```

This tells Jinja2 to render these as literal text rather than trying to resolve them as variables.

### 2. Fixed Test Script

Updated `test_pilger_placeholders.py` to handle the correct return signature from `load_and_build_agent_with_placeholders`:

**Before:**
```python
agent, mcp_client = await load_and_build_agent_with_placeholders(...)
```

**After:**
```python
agent, mcp_client, direct_logger = await load_and_build_agent_with_placeholders(...)
```

## Verification

### 1. Test Results
All placeholder tests now pass:
```
✅ PASSED: Prompt File Content
✅ PASSED: Configuration Consistency  
✅ PASSED: Placeholder Passing
📊 Overall: 3/3 tests passed
```

### 2. API Endpoint Testing
The `/defect-analysis-with-pilger/form` endpoint now works correctly:

**CURL Command:**
```bash
curl --location 'http://localhost:8000/defect-analysis-with-pilger/form' \
--form 'user_input="rack पट्टी के बोल्ट लूज हो गए हैं, उसको टाइट करना पड़ेगा।"' \
--form 'top_n="5"' \
--form 'min_score="0.7"'
```

**Result:** Returns successful response with proper defect analysis and Pilger processing results.

### 3. Log Verification
The agent logs now show:
- `{{ontology}}` replaced with complete DefectAnalysisPipeline JSON data
- `{{user_input}}` replaced with actual user input text
- No template errors or undefined variable issues

## Impact

✅ **Fixed:** Placeholder replacement now works correctly
✅ **Fixed:** Pilger agent receives actual data instead of placeholder text  
✅ **Fixed:** Enhanced defect analysis API endpoint functions properly
✅ **Fixed:** No breaking changes to existing functionality
✅ **Fixed:** Cross-platform compatibility maintained

## Files Modified

1. `config/prompts/gemba-d-r-c-v11.txt` - Escaped example placeholders
2. `test_pilger_placeholders.py` - Fixed return value unpacking

## Testing

Run the verification test:
```bash
.venv/Scripts/python.exe test_pilger_placeholders.py
```

Test the API endpoint:
```bash
curl --location 'http://localhost:8000/defect-analysis-with-pilger/form' \
--form 'user_input="test input"' \
--form 'top_n="5"' \
--form 'min_score="0.7"'
```
