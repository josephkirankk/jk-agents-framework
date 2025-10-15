# Data Generation Fix - Complete Report

## Executive Summary

**Problem**: Only 1 record was being generated instead of 900 records in the Schema-Agnostic Test Data Generator.

**Root Cause**: The LLM was adding preview expressions like `records[:5]` or `json.dumps(records)` at the end of the generated Python code, which caused only a subset of the data to be returned.

**Solution**: Implemented automatic code correction in the Python wrapper (`app/mcp_python_wrapper.py`) to detect and fix these issues before execution.

**Result**: ✅ **900 records successfully generated and persisted** with correct data structure.

---

## Problem Analysis

### Step 1: Initial Investigation

The test execution showed:
- Agent claimed: "Total records: 900"
- Database contained: Only 1 record (dict) or 7 records (list)
- Expected: List of 900 dicts

### Step 2: Enhanced Logging

Modified `app/planner_executor.py` to save the full Python code to debug files in `agentlogs/python_code_debug/`.

**Key Finding**: The generated Python code ended with problematic expressions:

```python
# Example 1: Slice expression
records = []
for i in range(900):
    records.append(record)
records[:5]  # ← WRONG! Returns only 5 records

# Example 2: JSON string conversion
records = []
for i in range(900):
    records.append(record)
json.dumps(records)  # ← WRONG! Returns a string, not a list

# Example 3: Bare expression
records = []
for i in range(900):
    records.append(record)
records  # ← WRONG! Expression not captured by exec()
```

### Step 3: Root Cause Identification

**Primary Issue**: The LLM consistently ignored prompt instructions and added preview/conversion lines.

**Secondary Issue**: Python's `exec()` function doesn't capture the value of bare expressions. When the code ends with `records`, the value is not stored in `local_vars` and cannot be retrieved.

**Why Prompt-Based Fixes Failed**:
- Added multiple warnings in the prompt
- Added explicit examples showing correct vs. incorrect code
- Added CRITICAL warnings at the top of the prompt
- **Result**: LLM continued to ignore instructions

**Conclusion**: Prompt-based approach was insufficient. Required code-level intervention.

---

## Solution Implemented

### Automatic Code Correction in Python Wrapper

**File**: `app/mcp_python_wrapper.py`

**Location**: Lines 255-301 (in `handle_call_tool` function)

**Logic**:
1. Extract the last line of the Python code
2. Check if it matches problematic patterns:
   - `records[:...]` (slice/index)
   - `json.dumps(records)` (JSON string conversion)
   - `str(records)` (string conversion)
   - `records` (bare expression)
3. If matched, replace with `result = records`
4. The `result` variable is then captured by the existing `exec()` logic (line 414)

**Code**:
```python
# FIX: Auto-correct common LLM mistakes in data generation code
logger.info(f"🔧 Checking Python code for common LLM mistakes...")
lines = python_code.strip().split('\n')
if lines:
    last_line = lines[-1].strip()
    logger.info(f"   Last line of code: {last_line}")
    
    fixed = False
    if re.match(r'^records\s*\[.*\].*$', last_line):
        # Last line is records[:5] or records[0] or similar
        logger.warning(f"⚠️  Detected slice/index on last line: {last_line}")
        lines[-1] = "result = records"
        python_code = '\n'.join(lines)
        fixed = True
    elif re.match(r'^json\.dumps\s*\(.*records.*\).*$', last_line):
        # Last line is json.dumps(records) or similar
        logger.warning(f"⚠️  Detected json.dumps on last line: {last_line}")
        lines[-1] = "result = records"
        python_code = '\n'.join(lines)
        fixed = True
    elif re.match(r'^str\s*\(.*records.*\).*$', last_line):
        # Last line is str(records) or similar
        logger.warning(f"⚠️  Detected str() on last line: {last_line}")
        lines[-1] = "result = records"
        python_code = '\n'.join(lines)
        fixed = True
    elif last_line == "records":
        # Last line is just "records" - expression not captured by exec()
        logger.warning(f"⚠️  Detected bare 'records' expression on last line")
        lines[-1] = "result = records"
        python_code = '\n'.join(lines)
        fixed = True
    
    if fixed:
        logger.info(f"✅ Auto-corrected Python code to return full dataset")
```

### Enhanced Logging

**File**: `app/mcp_python_wrapper.py`

**Addition**: File-based logging to `agentlogs/mcp_server_logs/python_wrapper.log`

**Purpose**: Debug MCP server behavior (MCP servers run in separate processes, so stdout/stderr is not visible in main logs)

**Code** (lines 46-61):
```python
# Add file handler for debugging
try:
    from pathlib import Path
    log_dir = Path("agentlogs/mcp_server_logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "python_wrapper.log")
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
except Exception as e:
    print(f"Warning: Could not set up file logging: {e}", file=sys.stderr)
```

### Debug File Saving

**File**: `app/planner_executor.py`

**Addition**: Save full Python code to debug files (lines 1076-1093)

**Purpose**: Capture the exact code generated by the LLM for analysis

**Code**:
```python
# Save full Python code to debug file for analysis
try:
    debug_dir = Path("agentlogs/python_code_debug")
    debug_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    debug_file = debug_dir / f"code_{step.id}_{timestamp}.py"
    debug_file.write_text(code, encoding='utf-8')
    log_lines.append(f"   Full code saved to: {debug_file}")
except Exception as e:
    log_lines.append(f"   Warning: Could not save debug code: {e}")
```

---

## Verification

### Test Execution

**Command**: `python tests/run_with_fixed_plan.py`

**Result**:
```
✅ Reference ID found: ref_e7170d965b1c

[Step 6] Verifying database...
✅ Dataset found in database
   Reference ID: ref_e7170d965b1c
   Metadata: {
  "description": "Auto-stored from Python execution",
  "record_count": 900,
  "data_type": "list",
  "stored_at": "2025-10-12T14:20:19.558311",
  "auto_stored": true
}
   Data type: list
   Record count: 900

✅ SUCCESS: 900 records generated!
```

### Database Verification

**Query Results**:
- ✅ Data type: `list` (not `dict`)
- ✅ Record count: 900 (not 1 or 7)
- ✅ Unique students: 100
- ✅ Subjects: ['Chemistry', 'Maths', 'Physics']
- ✅ Years: [2023, 2024, 2025]
- ✅ Structure: 100 students × 3 subjects × 3 years = 900 records

**Sample Records**:
```json
{
  "student_name": "Walter Foster",
  "student_id": "STUV0VKH6",
  "student_class": 5,
  "subject": "Maths",
  "marks": 36,
  "exam_quarter": "Q1",
  "exam_year": 2023
}
```

### MCP Server Logs

**Evidence of Auto-Correction**:
```
2025-10-12 14:18:17,155 - python_wrapper - INFO - 🔧 Checking Python code for common LLM mistakes...
2025-10-12 14:18:17,155 - python_wrapper - INFO -    Last line of code: records[:5]  # Preview first 5 records
2025-10-12 14:18:17,155 - python_wrapper - WARNING - ⚠️  Detected slice/index on last line: records[:5]
2025-10-12 14:18:17,155 - python_wrapper - WARNING -    Replacing with: result = records
2025-10-12 14:18:17,155 - python_wrapper - INFO - ✅ Auto-corrected Python code to return full dataset
2025-10-12 14:18:17,156 - python_wrapper - INFO -    Original last line: records[:5]
2025-10-12 14:18:17,156 - python_wrapper - INFO -    Fixed last line: result = records
```

---

## Summary

### What Was Fixed

| Component | Issue | Fix | Status |
|-----------|-------|-----|--------|
| Data generation | Only 1-7 records generated | Auto-correct Python code | ✅ FIXED |
| Data type | Sometimes `dict` instead of `list` | Auto-correct `json.dumps()` | ✅ FIXED |
| Code execution | Bare expressions not captured | Replace with assignment | ✅ FIXED |
| Logging | MCP server logs not visible | Add file handler | ✅ ADDED |
| Debugging | Can't see generated code | Save to debug files | ✅ ADDED |

### Final Status

✅ **ALL REQUIREMENTS MET**:
- ✅ Full Python code visible in logs (no truncation)
- ✅ 900 records generated (verified in database)
- ✅ Data type is `list` (not `dict`)
- ✅ 100 unique students with 9 records each (3 subjects × 3 years)
- ✅ All other components still working (persistence, workflow, etc.)

### Files Modified

1. `app/mcp_python_wrapper.py` - Auto-correction logic + file logging
2. `app/planner_executor.py` - Debug file saving
3. `config/json_schema_test_data_generator.yaml` - Enhanced prompt warnings (attempted but insufficient)

### Files Created

1. `docs/DATA_GENERATION_FIX.md` - This document
2. `agentlogs/python_code_debug/` - Debug directory for Python code
3. `agentlogs/mcp_server_logs/` - MCP server log directory

---

## Lessons Learned

1. **Prompt Engineering Has Limits**: Even with explicit warnings and examples, LLMs may not follow instructions consistently.

2. **Code-Level Fixes Are More Reliable**: Automatic code correction is more robust than relying on LLM behavior.

3. **Logging Is Critical**: MCP servers run in separate processes, so file-based logging is essential for debugging.

4. **Test Incrementally**: Each fix was tested immediately to verify it worked before proceeding.

5. **Document Everything**: Comprehensive documentation helps future debugging and maintenance.

---

## Recommendations

1. **Keep the Auto-Correction**: This fix should remain in place as a safety net.

2. **Monitor for New Patterns**: If the LLM starts using other problematic patterns, add them to the auto-correction logic.

3. **Consider Prompt Improvements**: While prompt-based fixes didn't work this time, continue refining prompts for better LLM behavior.

4. **Extend to Other Variables**: The auto-correction currently only handles `records`. Consider extending to other common variable names (`data`, `results`, etc.).

5. **Add Unit Tests**: Create unit tests for the auto-correction logic to ensure it continues working.

---

**Date**: 2025-10-12  
**Author**: Augment Agent  
**Status**: ✅ COMPLETE

