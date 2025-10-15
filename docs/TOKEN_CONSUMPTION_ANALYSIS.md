# Token Consumption Analysis and Fix

**Date**: 2025-10-12  
**Issue**: Extremely high token consumption (115,521 input tokens for 4 agents)  
**Status**: 🔍 INVESTIGATING

---

## Current Token Usage (Before Fix)

From `agentlogs/agentlog_20251012144149.log`:

```
LLM calls: total=5, supervisor=1, worker=4
Tokens: 
  - supervisor(input=0, output=0, total=0)
  - worker(input=115521, output=1583, total=117104)
  - overall(input=115521, output=1583, total=117104)
```

### Per-Agent Breakdown

| Step | Agent | Payload Size | Estimated Tokens | Actual Input Tokens |
|------|-------|--------------|------------------|---------------------|
| s1 | schema_analyzer | 3,431 chars | ~857 | Unknown |
| s2 | requirement_parser | 3,429 chars | ~857 | Unknown |
| s3 | data_generator | 7,327 chars | ~1,831 | Unknown |
| s4 | schema_validator | 7,076 chars | ~1,769 | Unknown |

**Total Estimated from Payload**: ~5,314 tokens  
**Actual Total**: 115,521 tokens  
**Discrepancy**: **21.7x higher than expected!**

---

## Root Cause Analysis

### Issue 1: Full Raw Responses Passed to Dependent Steps

**Location**: `app/planner_executor.py`, line 794

```python
def _format_dependent_request_responses(depends_on: Optional[List[str]]) -> str:
    ...
    for sid, info in step_results.items():
        if sid in dep_set:
            task = info.get('request', '')
            response = info.get('raw', '')  # ❌ PROBLEM: Full raw response!
            lines.append(f"User Agent : {task}")
            lines.append(f"Agent Response : {response}")
```

**Impact**:
- Step s3 depends on s1 and s2, so it receives their full raw responses
- Step s4 depends on s1 and s3, so it receives their full raw responses
- The raw response from s3 includes:
  - Explanatory text (~200 words)
  - Markdown table with sample records (~500 chars)
  - Reference ID information
  - Total: ~1,500+ characters per response

### Issue 2: Summary Too Large

**Location**: `app/planner_executor.py`, line 1043

```python
summary = (wtext[:1200] + "...") if len(wtext) > 1200 else wtext
```

**Impact**:
- Summary is truncated to 1200 characters
- For context with multiple dependencies, this adds up quickly
- 1200 chars ≈ 300 tokens per step
- With 2-3 dependencies, that's 600-900 tokens just for context

### Issue 3: No Special Handling for Reference IDs

**Problem**:
- When data is stored with a reference ID, the agent still generates a verbose response
- The response includes sample data, explanations, and formatting
- This verbose response gets passed to subsequent steps
- The reference ID alone would be sufficient (e.g., "Data stored: ref_xxx")

### Issue 4: Cumulative Context Growth

**Dependency Chain**:
```
s1 (schema_analyzer)
  ↓
s2 (requirement_parser)
  ↓
s3 (data_generator) ← receives context from s1, s2
  ↓
s4 (schema_validator) ← receives context from s1, s3
```

**Token Growth**:
- s1: 857 tokens (base prompt)
- s2: 857 tokens (base prompt)
- s3: 857 (base) + 1200 (s1 context) + 1200 (s2 context) = **3,257 tokens**
- s4: 857 (base) + 1200 (s1 context) + 1500 (s3 context with table) = **3,557 tokens**

**But wait!** The actual tokens are much higher. Let me check if there's response duplication...

### Issue 5: Possible Response Duplication

Looking at the log, step s4 made **6 tool calls** (multiple retries due to errors). Each retry likely includes the full context again, multiplying the token consumption.

**Estimated Token Consumption with Retries**:
- s4 base: 3,557 tokens
- s4 with 6 calls: 3,557 × 6 = **21,342 tokens**

If similar retries happened in other steps, this could explain the 115k tokens.

---

## Proposed Solutions

### Solution 1: Use Summary Instead of Raw Response ✅

**Change**: `app/planner_executor.py`, line 794

```python
# Before
response = info.get('raw', '')

# After
response = info.get('output_summary', '')
```

**Impact**: Reduces context from full response to 1200-char summary

### Solution 2: Reduce Summary Size ✅

**Change**: `app/planner_executor.py`, line 1043

```python
# Before
summary = (wtext[:1200] + "...") if len(wtext) > 1200 else wtext

# After
summary = (wtext[:400] + "...") if len(wtext) > 400 else wtext
```

**Impact**: Reduces summary from 1200 chars (~300 tokens) to 400 chars (~100 tokens)

### Solution 3: Smart Summary for Reference IDs ✅

**Change**: `app/planner_executor.py`, after line 1043

```python
# Detect reference IDs and create ultra-compact summary
import re
ref_match = re.search(r'ref_[a-f0-9]{12}', wtext)
if ref_match:
    ref_id = ref_match.group(0)
    # Extract record count if present
    count_match = re.search(r'(\d+)\s+records?', wtext, re.IGNORECASE)
    if count_match:
        count = count_match.group(1)
        summary = f"✓ Data generated and stored: {ref_id} ({count} records)"
    else:
        summary = f"✓ Data stored: {ref_id}"
```

**Impact**: Reduces reference ID responses from ~1500 chars to ~50 chars

### Solution 4: Prevent Context Duplication on Retries ✅

**Change**: Ensure context is only built once per step, not per retry

**Impact**: Eliminates token multiplication from retries

---

## Expected Token Reduction

### Before Fix
- s1: 857 tokens
- s2: 857 tokens
- s3: 857 + 1200 + 1200 = 3,257 tokens
- s4: 857 + 1200 + 1500 = 3,557 tokens (× 6 retries = 21,342)
- **Total: ~26,313 tokens** (without accounting for all retries)

### After Fix (Conservative Estimate)
- s1: 857 tokens
- s2: 857 tokens
- s3: 857 + 400 + 400 = 1,657 tokens
- s4: 857 + 400 + 50 = 1,307 tokens (× 6 retries = 7,842)
- **Total: ~11,213 tokens**

**Expected Reduction**: ~57% reduction (26,313 → 11,213)

### After Fix (Optimistic with Retry Fix)
- s1: 857 tokens
- s2: 857 tokens
- s3: 1,657 tokens
- s4: 1,307 tokens
- **Total: ~4,678 tokens**

**Expected Reduction**: ~82% reduction (26,313 → 4,678)

---

## Implementation Plan

1. ✅ **Analyze logs** - Identify root causes
2. ⏳ **Implement fixes** - Modify planner_executor.py
3. ⏳ **Test** - Run test and compare token usage
4. ⏳ **Verify** - Ensure functionality remains intact
5. ⏳ **Document** - Update documentation with results

---

## Files to Modify

1. **`app/planner_executor.py`**
   - Line 794: Use `output_summary` instead of `raw`
   - Line 1043: Reduce summary size from 1200 to 400 chars
   - After line 1043: Add smart summary for reference IDs

---

## Success Criteria

- ✅ Token consumption reduced by at least 50%
- ✅ Large datasets never included in full in agent responses
- ✅ Only reference IDs and small previews appear in responses
- ✅ All functionality remains intact (900 records generated, validated, stored)
- ✅ Documentation updated with token optimization details

---

## RESULTS - FIXES IMPLEMENTED ✅

### Token Consumption Comparison

| Metric | Before Fix | After Fix | Reduction |
|--------|------------|-----------|-----------|
| Worker Input Tokens | 115,521 | 9,014 | 106,507 (92.2%) |
| Worker Output Tokens | 1,583 | 1,616 | -33 (-2.1%) |
| Total Worker Tokens | 117,104 | 10,630 | 106,474 (90.9%) |

### What Was Fixed

**CRITICAL DISCOVERY**: The token optimization in `app/planner_executor.py` was working correctly, but the schema_validator agent was calling `retrieve_large_dataset` tool, which returned the FULL dataset (3600 records) in the response, causing massive token consumption!

1. **✅ Use Summary Instead of Raw Response** (Already implemented)
   - Changed line 794 to use `output_summary` instead of `raw`
   - Impact: Reduced context from full response (~1500 chars) to summary (~400 chars)

2. **✅ Reduce Summary Size** (Already implemented)
   - Changed line 1043 to reduce summary from 1200 chars to 400 chars
   - Impact: 67% reduction in summary size

3. **✅ Smart Summary for Reference IDs** (Already implemented)
   - Added special handling for responses containing reference IDs
   - Detects pattern: `ref_[a-f0-9]{12}`
   - Extracts record count from "Total records: X" pattern
   - Creates ultra-compact summary: "✓ Data generated and stored: ref_xxx (N records)"
   - Impact: Reduced reference ID responses from ~1500 chars to ~50 chars (97% reduction)

4. **✅ Removed large_data_storage Server from schema_validator** (NEW FIX!)
   - Removed `large_data_storage` MCP server from schema_validator's available tools
   - Prevents calling `retrieve_large_dataset` which returns full datasets
   - Only `python_runner` server available now
   - Impact: Prevented 3600-record dataset from being included in conversation history

5. **✅ Updated schema_validator Prompt** (NEW FIX!)
   - Added explicit examples of CORRECT and WRONG ways to access data
   - Added ⚠️ warnings about what NOT to do
   - Made it clear to use ONLY `run_python_code` with `dataset_reference_id`
   - Impact: Reduced agent confusion and retry attempts

### Files Modified

- **`app/planner_executor.py`**
  - Lines 772-803: Updated `_format_dependent_request_responses()` to use `output_summary`
  - Lines 1043-1068: Added smart summary logic with reference ID detection

- **`config/json_schema_test_data_generator.yaml`**
  - Lines 1126-1190: Added "CRITICAL: How to Access Large Datasets" section
  - Lines 1216-1237: Updated Critical Rules with explicit warnings
  - Lines 1239-1250: Removed `large_data_storage` server from schema_validator

### Verification

Test run with StudentExamRecord schema (3600 records):
- ✅ All 3600 records generated correctly
- ✅ Data persisted to database
- ✅ Reference ID: ref_f66541e74b1d
- ✅ Token consumption: 9,014 tokens (92.2% reduction)
- ✅ All functionality intact
- ✅ No import errors for jsonschema
- ✅ Validation completed: 3600 valid, 0 invalid

### Success Criteria Met

- ✅ Token consumption reduced by 92.2% (target was 50% - EXCEEDED by 84%!)
- ✅ Large datasets never included in full in agent responses
- ✅ Only reference IDs and small previews appear in responses
- ✅ All functionality remains intact (3600 records generated, validated, stored)
- ✅ Documentation updated with token optimization details
- ✅ No import errors for jsonschema library

---

**Status**: ✅ COMPLETE - 92.2% token reduction achieved!

