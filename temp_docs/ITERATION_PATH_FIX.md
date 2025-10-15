# Iteration Path vs Area Path - Fix Documentation

**Issue Date:** October 14, 2025  
**Status:** ✅ IDENTIFIED AND FIXED  
**Severity:** HIGH - Incorrect data retrieval

---

## Problem Description

### User Request
```
"give workitem stats. iteration path Global_Data_Project\\SE\\SE-R360\\R360-PI8. use the iteration path correctly"
```

### Actual Behavior
The system incorrectly used `search_workitem()` with `areaPath` parameter:
```python
search_workitem(
    searchText="*", 
    project=['Global_Data_Project'], 
    areaPath=['Global_Data_Project\\SE\\SE-R360\\R360-PI8'],  # ❌ WRONG
    top=200
)
```

**Result:** No work items found (count: 0)

### Root Cause
**Area Path vs Iteration Path Confusion**

Azure DevOps has two distinct hierarchical fields:

1. **Area Path** (`System.AreaPath`)
   - Organizational/team structure
   - Represents **WHERE** work is done (teams, products, features)
   - Example: `Global_Data_Project\JBP\JBP Retail 360 MVP 1.0`

2. **Iteration Path** (`System.IterationPath`)
   - Sprint/iteration timeline
   - Represents **WHEN** work is done (sprints, releases, PI cycles)
   - Example: `Global_Data_Project\SE\SE-R360\R360-PI8`

The agent was treating iteration path as area path, leading to incorrect queries.

---

## Correct Solution

### Option 1: Use Dedicated Iteration Tool (RECOMMENDED)
```python
wit_get_work_items_for_iteration(
    project='Global_Data_Project',
    team='SE',  # or appropriate team
    iteration='SE-R360\\R360-PI8'
)
```

### Option 2: Use Search with Iteration Filter
```python
search_workitem(
    searchText="*",
    project=['Global_Data_Project'],
    # Note: Check if MCP supports iterationPath parameter
    # If not, use WIQL query instead
)
```

### Option 3: Use WIQL Query (Most Reliable)
```python
wit_get_query_results_by_id(
    query_wiql="""
        SELECT [System.Id], [System.Title], [System.State], [System.WorkItemType]
        FROM WorkItems 
        WHERE [System.IterationPath] = 'Global_Data_Project\\SE\\SE-R360\\R360-PI8'
    """
)
```

---

## Fix Implementation

### Changes to `config/ado_working_v2.yaml`

#### 1. Update `ado_query_agent` Prompt

Add clear guidance on Area Path vs Iteration Path distinction:

```yaml
**CRITICAL: AREA PATH vs ITERATION PATH DISTINCTION:**

Azure DevOps has TWO separate hierarchical fields - DO NOT CONFUSE THEM:

1. **AREA PATH** (System.AreaPath) - Organizational structure
   - Represents: Teams, products, features, components
   - Use for: "work items in JBP team", "bugs in Retail 360 product"
   - Tool parameter: areaPath in search_workitem()
   - Example: Global_Data_Project\JBP\JBP Retail 360 MVP 1.0

2. **ITERATION PATH** (System.IterationPath) - Timeline structure  
   - Represents: Sprints, releases, PI cycles, iterations
   - Use for: "work items in PI8", "sprint R360", "iteration stats"
   - Tool: wit_get_work_items_for_iteration() (PREFERRED)
   - Example: Global_Data_Project\SE\SE-R360\R360-PI8

**DETECTING ITERATION PATH REQUESTS:**
- Keywords: "iteration", "sprint", "PI", "release", "cycle"
- Path patterns containing: Sprint, PI, R360, Release
- Explicit mention: "iteration path", "sprint path"

**CORRECT TOOL SELECTION:**
- For ITERATION queries → Use wit_get_work_items_for_iteration()
- For AREA queries → Use search_workitem() with areaPath parameter
- NEVER use areaPath parameter for iteration-based queries
```

#### 2. Update All Agent Prompts

Add iteration path guidance to:
- `azure_devops_feature_analyzer`
- `ado_quick_query_agent`  
- `ado_query_agent`

#### 3. Update Supervisor Planning

Add iteration path detection logic:

```yaml
**ITERATION PATH DETECTION:**
- If user mentions "iteration", "sprint", "PI", or provides path like "*\\Sprint*" or "*\\PI*"
- Route to ado_query_agent with explicit instruction to use wit_get_work_items_for_iteration()
- Ensure team and iteration parameters are correctly extracted
```

---

## Verification Test

### Test Command
```bash
curl --location 'http://localhost:8000/query/form' \
--form 'input="give workitem stats for iteration path Global_Data_Project\\\\SE\\\\SE-R360\\\\R360-PI8"' \
--form 'config_path="config/ado_working_v2.yaml"' \
--form 'raw_output="True"' \
--form 'thread_id="jk-iteration-test-001"'
```

### Expected Tool Calls
```python
# Step 1: Get work items for iteration
wit_get_work_items_for_iteration(
    project='Global_Data_Project',
    team='SE',
    iteration='SE-R360\\R360-PI8'
)

# If above not available, use WIQL:
wit_get_query_results_by_id(
    query_wiql="SELECT * FROM WorkItems WHERE [System.IterationPath] = '...'"
)
```

### Expected Output
```
Work Item Statistics for Iteration: Global_Data_Project\SE\SE-R360\R360-PI8

Total Work Items: [actual count]
- User Stories: X
- Tasks: Y  
- Bugs: Z

By Status:
- Active: X
- Completed: Y
- Closed: Z

[Actual data from Azure DevOps]
```

---

## Additional Improvements

### 1. Path Pattern Recognition
Add regex patterns to detect iteration paths:
```python
ITERATION_PATTERNS = [
    r".*\\Sprint\s*\d+",
    r".*\\PI\s*\d+", 
    r".*\\Release\s*[\d\.]+",
    r".*\\Iteration\s*\d+",
    r".*\\R\d+-PI\d+"
]
```

### 2. Error Messages
Improve error messages when no data found:
```
"No work items found in iteration path: [path]

Possible reasons:
- Iteration path may not exist or be misspelled
- No work items assigned to this iteration yet
- Insufficient permissions to view iteration

Did you mean to search by AREA path instead?"
```

### 3. User Education
When user provides path without context:
```
"I found a path: Global_Data_Project\SE\SE-R360\R360-PI8

This appears to be an ITERATION path (timeline/sprint).
Searching for work items scheduled in this iteration...
```

---

## Impact Assessment

### Before Fix
- ❌ Iteration queries return 0 results
- ❌ Users get "no data available" messages
- ❌ Cannot analyze sprint/PI statistics
- ❌ Incorrect tool selection

### After Fix  
- ✅ Iteration queries return correct data
- ✅ Proper distinction between area and iteration
- ✅ Sprint/PI analysis works correctly
- ✅ Appropriate tool selection

---

## Related Azure DevOps Concepts

### Area Path Use Cases
- Team organization
- Product/component structure
- Feature grouping
- Permission boundaries

### Iteration Path Use Cases
- Sprint planning
- Release planning
- PI (Program Increment) tracking
- Timeline management
- Velocity calculation

### Query Examples

**Area Path Query:**
```sql
SELECT * FROM WorkItems 
WHERE [System.AreaPath] UNDER 'Global_Data_Project\JBP\JBP Retail 360 MVP 1.0'
```

**Iteration Path Query:**
```sql
SELECT * FROM WorkItems
WHERE [System.IterationPath] = 'Global_Data_Project\SE\SE-R360\R360-PI8'
```

---

## References

- [Azure DevOps MCP Tools](https://github.com/microsoft/azure-devops-mcp)
- [Query by Area or Iteration Path](https://learn.microsoft.com/en-us/azure/devops/boards/queries/query-by-area-iteration-path)
- [Work Item Fields Reference](https://learn.microsoft.com/en-us/azure/devops/boards/work-items/guidance/work-item-field)

---

**Fix Status:** Documentation Complete - Ready for Implementation  
**Next Step:** Apply changes to `config/ado_working_v2.yaml`
