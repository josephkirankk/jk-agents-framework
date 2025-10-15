# ADO Iteration Path Query Fix - Enhanced Version 2

**Date:** October 14, 2024  
**Issue:** Agent still using wrong tool despite initial fix  
**Status:** ✅ ENHANCED FIX APPLIED

---

## The Persistent Problem

### Your Latest Log Shows:
```
Tool Calls:
1. search_workitem(searchText="", project=['Global_Data_Project'], 
   areaPath=['Global_Data_Project\\SE\\SE-R360\\R360-PI8'], top=200)
   → Error: ExceptionGroup('unhandled errors in a TaskGroup'...

2. search_workitem(searchText="*", project=['Global_Data_Project'], 
   areaPath=['Global_Data_Project\\SE\\SE-R360\\R360-PI8'], top=200)
   → {"count":0,"results":[],"infoCode":0,"facets":{}}
```

### What's Wrong:
- ❌ Agent is STILL using `search_workitem()`
- ❌ Agent is passing **iteration path** to **areaPath** parameter
- ❌ This is EXACTLY what should NOT happen

### Why First Fix Failed:
The instructions were buried too deep in the prompt. The agent wasn't seeing the critical decision logic early enough.

---

## Enhanced Fix - Version 2

### Solution: Move Critical Logic to TOP

I've added a **MANDATORY FIRST STEP** section at the very beginning of the execution approach that the agent MUST read before calling any tool.

### New Structure in Config (Lines 823-854)

```yaml
EXECUTION APPROACH:

========================================
MANDATORY FIRST STEP - READ THIS BEFORE ANY TOOL CALL
========================================

**STOP! BEFORE CALLING ANY TOOL, ANSWER THIS QUESTION:**

Does the user's request contain ANY of these keywords or patterns?
- "iteration path"
- "iteration"
- "sprint"  
- "PI" (like "PI8", "R360-PI8")
- Path containing: SE-R360, R360-PI, Sprint, Iteration

✅ IF YES (ITERATION QUERY):
   YOU MUST USE: wit_get_work_items_for_iteration(project, team, iteration)
   
   Example for "iteration path Global_Data_Project\\SE\\SE-R360\\R360-PI8":
   
   wit_get_work_items_for_iteration(
       project='Global_Data_Project',
       team='SE',
       iteration='R360-PI8'
   )
   
   ❌ DO NOT use search_workitem()
   ❌ DO NOT use areaPath parameter
   ❌ DO NOT pass iteration path to areaPath

❌ IF NO (AREA QUERY):
   THEN use: search_workitem(areaPath=[...], searchText='*', ...)

========================================
```

### Added Final Verification Section (Lines 972-993)

Before the OUTPUT FORMAT, added a checklist:

```yaml
========================================
FINAL VERIFICATION BEFORE EXECUTING
========================================

Before you call any tool, verify:

✅ If user said "iteration path" or provided path like "..\\SE-R360\\R360-PI8":
   - Confirm you are calling: wit_get_work_items_for_iteration()
   - Confirm you extracted: project, team, iteration from path
   - Confirm you are NOT calling: search_workitem()

✅ If calling search_workitem():
   - Confirm searchText is NOT empty (use "*" for broad search)
   - Confirm you are NOT putting iteration path in areaPath parameter
   - Confirm this is an AREA query, not ITERATION query

❌ NEVER do this:
   - search_workitem(areaPath=['..\\SE-R360\\R360-PI8'])  ← WRONG!
   - search_workitem(searchText="")  ← WILL ERROR!
   - Using search_workitem for iteration queries ← WRONG TOOL!

========================================
```

---

## Why This Should Work Better

### 1. **Visual Prominence**
The `========` separators make the mandatory section stand out visually in the prompt.

### 2. **Position at Top**
The decision logic is now the FIRST thing in the EXECUTION APPROACH section, before any other instructions.

### 3. **Binary Decision**
Simple YES/NO question that forces the agent to classify the query type before proceeding.

### 4. **Explicit Example**
Shows exact example matching the user's actual request pattern.

### 5. **Multiple Negative Warnings**
Three explicit "DO NOT" statements about what NOT to do.

### 6. **Double Verification**
Second checkpoint before OUTPUT FORMAT serves as final verification.

---

## What the Agent Should Do Now

### User Request:
```
"Give workitem stats. iteration path Global_Data_Project\\SE\\SE-R360\\R360-PI8"
```

### Agent's Mental Process (Following New Instructions):

**Step 1: Read MANDATORY FIRST STEP**
- Question: Does request contain "iteration path", "iteration", "PI", etc.?
- Answer: YES - user said "iteration path"

**Step 2: Classify as ITERATION QUERY**
- Instructions say: "YOU MUST USE: wit_get_work_items_for_iteration()"

**Step 3: Extract Parameters**
- Path: `Global_Data_Project\\SE\\SE-R360\\R360-PI8`
- Project: `Global_Data_Project`
- Team: `SE`
- Iteration: `R360-PI8`

**Step 4: FINAL VERIFICATION**
- ✅ User said "iteration path" → confirmed calling wit_get_work_items_for_iteration()
- ✅ Extracted project, team, iteration
- ✅ NOT calling search_workitem()

**Step 5: Execute Correct Tool**
```python
wit_get_work_items_for_iteration(
    project='Global_Data_Project',
    team='SE',
    iteration='R360-PI8'
)
```

---

## Comparison: Wrong vs Right

### ❌ WRONG (What Was Happening):
```python
# Call 1: Empty searchText - ERROR
search_workitem(
    searchText="",  # WRONG - causes error
    project=['Global_Data_Project'],
    areaPath=['Global_Data_Project\\SE\\SE-R360\\R360-PI8'],  # WRONG - iteration path in areaPath
    top=200
)

# Call 2: Still using search_workitem - ZERO RESULTS
search_workitem(
    searchText="*",
    project=['Global_Data_Project'],
    areaPath=['Global_Data_Project\\SE\\SE-R360\\R360-PI8'],  # STILL WRONG
    top=200
)
# Result: {"count":0,"results":[]} - No data found
```

### ✅ RIGHT (What Should Happen):
```python
# Correct tool for iteration queries
wit_get_work_items_for_iteration(
    project='Global_Data_Project',
    team='SE',
    iteration='R360-PI8'
)
# Result: Returns actual work items from that iteration
```

---

## Testing the Enhanced Fix

### Test Command:
```bash
python run_agent.py --config config/ado_working_v2.yaml --user-input "Give workitem stats. iteration path Global_Data_Project\\SE\\SE-R360\\R360-PI8. use the iteration path correctly"
```

### What to Look For in Logs:

**✅ SUCCESS Indicators:**
- Tool call: `wit_get_work_items_for_iteration('Global_Data_Project', 'SE', 'R360-PI8')`
- NO calls to `search_workitem()` for this query
- NO `areaPath` parameter used
- Results returned (or "no items found" if iteration is empty)

**❌ FAILURE Indicators:**
- Tool call: `search_workitem(areaPath=[...])` 
- Error: ExceptionGroup
- Result: count=0, results=[]
- Agent using wrong tool again

---

## Additional Safeguards Added

### 1. Keyword Detection List
Expanded to catch all iteration-related terms:
- "iteration path"
- "iteration"
- "sprint"
- "PI"
- Path patterns: SE-R360, R360-PI, Sprint, Iteration

### 2. Explicit DO NOT List
Clear warnings about what never to do:
- ❌ DO NOT use search_workitem() for iteration queries
- ❌ DO NOT use areaPath parameter for iteration paths
- ❌ DO NOT pass iteration path to areaPath
- ❌ DO NOT use empty searchText

### 3. Verification Checklist
Before executing, agent must confirm:
- Which tool is being called
- Why that tool was selected
- That parameters are correctly extracted
- That wrong approaches are being avoided

---

## Root Cause Analysis

### Why Did First Fix Not Work?

**Problem 1: Prompt Structure**
- Instructions were buried in middle of long prompt
- Agent may have skipped or not prioritized critical section
- No clear visual separation

**Problem 2: No Forcing Function**
- No explicit "STOP and answer this first" instruction
- Agent could proceed to tool selection without classification
- No verification checkpoint before execution

**Problem 3: Competing Instructions**
- Multiple sections about batch processing, error handling, etc.
- Critical tool selection guidance got lost among other information
- No clear priority hierarchy

### How Enhanced Fix Addresses These:

**Solution 1: Visual Prominence**
- `========` separators create clear visual boundaries
- "MANDATORY FIRST STEP" in caps draws attention
- Positioned at very top of EXECUTION APPROACH

**Solution 2: Binary Decision**
- Simple YES/NO question forces classification
- Explicit "IF YES do this, IF NO do that" logic
- No ambiguity about which tool to use

**Solution 3: Multiple Checkpoints**
- Mandatory first step at beginning
- Detailed guidance in middle sections
- Final verification before execution
- Redundant reinforcement of critical rules

---

## Files Modified

### config/ado_working_v2.yaml

**Lines 823-854:** Added MANDATORY FIRST STEP section
- Visual separators with `========`
- Binary decision question
- Explicit keyword detection
- Tool selection with example
- Three "DO NOT" warnings

**Lines 972-993:** Added FINAL VERIFICATION section
- Pre-execution checklist
- Confirmation requirements
- Wrong approach warnings
- Visual separators

---

## Expected Outcome

After this enhanced fix:

1. **Agent reads MANDATORY FIRST STEP** before any tool call
2. **Agent classifies query** as ITERATION or AREA based on keywords
3. **Agent selects correct tool** immediately based on classification
4. **Agent extracts parameters** correctly from iteration path
5. **Agent verifies** at final checkpoint before execution
6. **Agent calls** `wit_get_work_items_for_iteration()` with correct params
7. **System returns** actual work items from that iteration

---

## If This Still Doesn't Work

If the agent still uses the wrong tool after this fix, possible issues:

### 1. Model/Configuration Issue
- Check if correct config file is being loaded
- Verify no caching of old prompts
- Ensure model is reading full prompt

### 2. MCP Server Issue
- Verify `wit_get_work_items_for_iteration()` tool is available
- Check MCP server has `-d work` domain enabled
- Test tool availability with direct call

### 3. Supervisor Routing Issue
- Check if supervisor is routing to correct agent
- Verify ado_query_agent is being called
- Review supervisor's routing logic

### Debug Steps:
```bash
# 1. Verify config is valid YAML
python -c "import yaml; print(yaml.safe_load(open('config/ado_working_v2.yaml')))"

# 2. Check MCP server tools
npx -y @azure-devops/mcp PepsiCoIT -d core work work-items --list-tools

# 3. Test with verbose logging
python run_agent.py --config config/ado_working_v2.yaml --verbose --user-input "test query"
```

---

## Summary

**Changes Made:**
1. ✅ Added MANDATORY FIRST STEP at top of EXECUTION APPROACH
2. ✅ Added binary decision question with keywords
3. ✅ Added explicit example matching user's query pattern
4. ✅ Added visual separators for prominence
5. ✅ Added FINAL VERIFICATION checkpoint before execution
6. ✅ Added multiple DO NOT warnings
7. ✅ Enhanced with redundant safeguards

**Expected Result:**
Agent now has multiple checkpoints forcing correct tool selection:
- Mandatory classification at start
- Detailed guidance in middle
- Final verification before execution
- Clear wrong approach warnings throughout

**Status:** ✅ ENHANCED FIX READY FOR TESTING

**Test:** Run same query and check if `wit_get_work_items_for_iteration()` is called.
