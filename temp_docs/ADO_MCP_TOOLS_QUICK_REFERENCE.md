# Azure DevOps MCP Tools - Quick Reference

**Version:** 2.0 | **Date:** October 14, 2024 | **Config:** `config/ado_working_v2.yaml`

---

## Overview

This document provides a quick reference for all Azure DevOps MCP tools integrated into the jk-agents-core framework.

**Key Principles:**
- ✅ READ-ONLY access (no create/update/delete)
- ✅ Batch processing: Max 200 items, 2-second delays
- ✅ Real data only - no fictional data
- ✅ Complete datasets with pagination

---

## Tool Categories

### 1. Work Item Management

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `wit_my_work_items()` | Get your assigned work items | None |
| `wit_get_work_item(id)` | Get single work item | id, fields[], expand (use EITHER fields OR expand) |
| `wit_get_work_items_batch_by_ids(ids)` | Batch get work items | ids (max 50 per batch) |
| `wit_get_work_items_for_iteration()` | Get iteration work items | project, team, iteration |
| `wit_list_backlogs()` | List team backlogs | project, team |
| `wit_list_backlog_work_items()` | Get backlog work items | project, team, category |
| `wit_list_work_item_comments(id)` | Get work item comments | id |
| `wit_get_query()` | Get saved query | query_id_or_path |
| `wit_get_query_results_by_id()` | Execute saved query | query_id |

**Critical API Constraint:** When using `wit_get_work_item()`, use EITHER `fields` OR `expand` parameter, NEVER both.

### 2. Core Services

| Tool | Purpose | Parameters |
|------|---------|------------|
| `core_list_projects()` | List all projects | None |
| `core_list_project_teams(project)` | List teams | project |
| `core_get_identity_ids(uniqueNames)` | Resolve user identities | uniqueNames[] |
| `work_list_team_iterations()` | List team iterations | project, team |

### 3. Search Operations

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `search_workitem()` | Search work items | organization, project, search_text, areaPath[], workItemType[], top |
| `search_code()` | Search code | organization, project, search_text |
| `search_wiki()` | Search wiki | organization, project, search_text |

**Tag Search Pattern:** `searchText="tags:<TAG> t:\"<Work Item Type>\""`  
**Example:** `tags:PI17 t:"User Story"`

### 4. Repository Management

| Tool | Purpose |
|------|---------|
| `repo_list_repos_by_project(project)` | List repositories |
| `repo_list_pull_requests_by_project(project)` | List all PRs |
| `repo_list_pull_requests_by_repo(repository_id)` | List repo PRs |
| `repo_get_pull_request_by_id()` | Get PR details |
| `repo_list_branches_by_repo(repository_id)` | List branches |
| `repo_list_my_branches_by_repo(repository_id)` | List my branches |
| `repo_list_pull_request_threads()` | Get PR threads |

### 5. Build/Pipeline Management

| Tool | Purpose |
|------|---------|
| `build_get_definitions(project)` | List build definitions |
| `build_get_builds(project)` | List builds |
| `build_get_status(project, build_id)` | Get build status |
| `build_get_log(project, build_id)` | Get build logs |
| `build_get_changes(project, build_id)` | Get build changes |

### 6. Test & Release Management

| Tool | Purpose |
|------|---------|
| `testplan_list_test_plans(project)` | List test plans |
| `testplan_list_test_cases(project, plan_id)` | List test cases |
| `testplan_show_test_results_from_build_id()` | Get test results |
| `release_get_definitions(project)` | List release definitions |
| `release_get_releases(project)` | List releases |

### 7. Wiki & Security

| Tool | Purpose |
|------|---------|
| `wiki_list_wikis()` | List wikis |
| `wiki_get_page_content()` | Get wiki page |
| `advsec_get_alerts(repository_id)` | Get security alerts |

---

## Critical Distinctions

### Area Path vs Iteration Path

**DO NOT CONFUSE THESE TWO FIELDS:**

| Field | Purpose | Example Path | Use For | Correct Tool |
|-------|---------|--------------|---------|--------------|
| **Area Path** | Organizational structure | `Global_Data_Project\JBP\JBP Retail 360 MVP 1.0` | "Work items in JBP team" | `search_workitem(areaPath=[...])` |
| **Iteration Path** | Timeline structure | `Global_Data_Project\SE\SE-R360\R360-PI8` | "Work items in PI8" | `wit_get_work_items_for_iteration()` |

**Common Keywords:**
- **Area Path**: "team", "project area", "component", "product"
- **Iteration Path**: "sprint", "PI", "iteration", "release", "cycle"

**Examples:**
```python
# CORRECT: Area path query
search_workitem(areaPath=['Global_Data_Project\\JBP\\JBP Retail 360 MVP 1.0'])

# CORRECT: Iteration path query
wit_get_work_items_for_iteration(project='Global_Data_Project', team='SE', iteration='R360-PI8')

# WRONG: Don't use areaPath for iteration queries
search_workitem(areaPath=['Global_Data_Project\\SE\\SE-R360\\R360-PI8'])  # ❌
```

---

## Agent Tool Usage Patterns

### Pattern 1: Simple Query (ado_quick_query_agent)
```
User: "Get my work items"
Tool: wit_my_work_items()
Output: Direct formatted response
```

### Pattern 2: Feature Analysis (azure_devops_feature_analyzer)
```
1. search_workitem(searchText="feature", top=200)
2. wit_get_work_items_batch_by_ids([...]) - batches of 50
3. wit_list_work_item_comments(id)
4. run_python_code() - calculate metrics
5. Generate structured report
```

### Pattern 3: Iteration Stats (ado_query_agent)
```
User: "Stats for iteration path Global_Data_Project\\SE\\SE-R360\\R360-PI8"
Tool: wit_get_work_items_for_iteration(project='Global_Data_Project', team='SE', iteration='R360-PI8')
```

### Pattern 4: Complete Dataset Analysis
```
ado_query_agent:
  1. search_workitem(top=200) - first batch
  2. Wait 2 seconds
  3. Paginate for remaining data
  4. wit_get_work_items_batch_by_ids() - details in batches of 50

python_analysis_agent:
  5. run_python_code() - statistical analysis

report_generator_agent:
  6. Format executive summary
```

---

## Batch Processing Requirements

**ADO System Protection:**
- ✅ Max 200 items per `search_workitem()` call
- ✅ Max 50 IDs per `wit_get_work_items_batch_by_ids()` call
- ✅ 2-second delays between consecutive API calls
- ✅ Pagination for datasets > 200 items
- ✅ Exponential backoff on throttling: 2s, 4s, 8s

**Example:**
```python
# Batch 1
results1 = search_workitem(top=200)
time.sleep(2)

# Batch 2
results2 = search_workitem(top=200, skip=200)
time.sleep(2)

# Get details in batches of 50
ids_batch1 = work_item_ids[:50]
details1 = wit_get_work_items_batch_by_ids(ids_batch1)
time.sleep(2)

ids_batch2 = work_item_ids[50:100]
details2 = wit_get_work_items_batch_by_ids(ids_batch2)
```

---

## Common Use Cases

### 1. Get My Work Items
```python
wit_my_work_items()
```

### 2. Get Work Items for Sprint
```python
wit_get_work_items_for_iteration(
    project='Global_Data_Project',
    team='SE',
    iteration='R360-PI8'
)
```

### 3. Search by Area Path
```python
search_workitem(
    organization='PepsiCoIT',
    project=['Global_Data_Project'],
    searchText='*',
    areaPath=['Global_Data_Project\\JBP\\JBP Retail 360 MVP 1.0'],
    top=200
)
```

### 4. Search by Tag
```python
search_workitem(
    organization='PepsiCoIT',
    project=['Global_Data_Project'],
    searchText='tags:PI17 t:"User Story"',
    areaPath=['Global_Data_Project\\JBP\\JBP Retail 360 MVP 1.0'],
    top=200
)
```

### 5. Get Build Status
```python
build_get_status(project='Global_Data_Project', build_id=456)
```

### 6. List Pull Requests
```python
repo_list_pull_requests_by_project(project='Global_Data_Project')
```

---

## Error Handling

| Error Type | Solution |
|------------|----------|
| Authentication errors | Run `az login` and verify Azure DevOps access |
| Permission errors | Check PAT token has read permissions |
| Not found errors | Verify project/team/work item exists |
| Empty searchText error | Use `searchText="*"` for broad searches |
| Throttling | Implement 2-second delays and exponential backoff |

---

## Configuration

**MCP Server Setup:**
```yaml
mcp_servers:
  azure_devops:
    transport: "stdio"
    command: "npx"
    args: ["-y", "@azure-devops/mcp", "PepsiCoIT", "-d", "core", "work", "work-items", "repositories", "pipelines", "wiki", "search", "-a", "env"]
    env:
      AZURE_DEVOPS_EXT_PAT: "${AZURE_DEVOPS_EXT_PAT}"
```

**Prerequisites:**
- Node.js 20+
- Azure CLI (`az login`)
- Azure DevOps PAT token with read permissions

---

## Quick Troubleshooting

**Q: Search returns no results?**  
A: Check searchText is not empty. Use `searchText="*"` for broad searches.

**Q: "Too many requests" error?**  
A: Implement 2-second delays between API calls.

**Q: Can't get work items for iteration?**  
A: Use `wit_get_work_items_for_iteration()`, NOT `search_workitem(areaPath=[iteration_path])`.

**Q: Batch call fails?**  
A: Check batch size ≤ 50 IDs for `wit_get_work_items_batch_by_ids()`.

---

## Summary

**Key Takeaways:**
1. Use correct tool for area vs iteration queries
2. Implement batch processing with delays
3. Never use `fields` and `expand` parameters together
4. Tag search: `tags:<TAG> t:"<Type>"`
5. Max 200 items for search, max 50 IDs for batch
6. 2-second delays between consecutive calls
7. Real data only - no fictional data

**Documentation Sources:**
- Config: `config/ado_working_v2.yaml`
- ADO MCP Docs: `external_docs/ado_mcp_docs.txt`
- Official: https://github.com/microsoft/azure-devops-mcp
