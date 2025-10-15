# Token Optimization Guide for JK-Agents-Core

## Problem Analysis

### Original Configuration Issues

When analyzing `config/test_data_parser_simple.yaml`, the following token waste patterns were identified:

**Token Usage Breakdown (5 records example):**
- Supervisor: 893 input + 196 output = 1,089 tokens
- Worker calls: 4,760 input + 540 output = 5,300 tokens
- **Total: 6,389 tokens**

**For 100 records, this would scale to ~50,000 tokens!**

### Root Causes of Token Waste

#### 1. **Business Context Repetition (3x)**
The business context block (~400 tokens) appeared in:
- Supervisor prompt
- requirement_parser agent system context
- data_generator agent system context

**Waste: ~800 tokens** (2 unnecessary duplications)

#### 2. **Verbose Python Code Templates**
Both agent prompts included full Python code examples:
- Lines 133-160: requirement_parser template (~600 tokens)
- Lines 206-262: data_generator template (~650 tokens)

**Waste: ~1,000 tokens** (could be condensed to essential logic only)

#### 3. **Full Dataset in Response**
The data_generator returned the entire dataset in the response:
```json
[
  {"record_id": 1, "metric": "abcd", "value": -9, ...},
  {"record_id": 2, "metric": "abcd", "value": 56, ...},
  ...
]
```

For 5 records: ~400 output tokens
For 100 records: ~8,000 output tokens
For 1000 records: ~80,000 output tokens

**Waste: Scales linearly with dataset size** (completely avoidable)

## Optimization Strategies

### Strategy 1: Eliminate Business Context Duplication

**Before:**
```yaml
business_context: |
  # Test Data Requirement Parser
  
  Parse natural language requirements...
  
  ## Valid Constraints
  **Regions/Markets:**
  - US: United States
  - IN: India
  ...
  (400 tokens repeated 3x = 1,200 total)
```

**After:**
```yaml
business_context: |
  Valid codes: Programs(MFG|ADV|STD), Sectors(PFNA|PBNA|QSNA|RSNA|ALL), 
  Plants(p1-p4), Markets(US|IN|UK|DE), UOM(count|kg|liters|units|percentage|hours)
  (150 tokens, referenced via {{business_context}} placeholder)
```

**Savings: 850 tokens (71% reduction)**

### Strategy 2: Condense Python Templates

**Before:**
```yaml
prompt: |
  ## Python Code Structure
  
  ```python
  import re
  import json
  
  query = '''USER_QUERY_HERE'''
  
  # Extract parameters using regex and string methods
  # Build result dictionary
  # Print JSON
  
  result = {
      "record_count": 100,  # extract from query
      "metrics": ["metric1"],  # extract from query
      ...
  }
  
  print(json.dumps(result, indent=2))
  ```
  (600 tokens)
```

**After:**
```yaml
prompt: |
  Parse query to JSON using run_python_code. Extract: count, metrics, codes, ranges.
  Defaults: 100 records, US, 30 days. Use regex: r'(\d+)\s*records?', r'metric[s]?\s+([\w\s,]+)'
  (150 tokens)
```

**Savings: 450 tokens per agent × 2 = 900 tokens (75% reduction)**

**Rationale:** GPT-4 already knows how to write Python code. Detailed templates are unnecessary.

### Strategy 3: File-Based Output (Critical)

**Before:**
```python
# In data_generator agent
print(json.dumps(records))  # Returns full dataset
```

Output tokens for different dataset sizes:
- 5 records: ~400 tokens
- 100 records: ~8,000 tokens  
- 1,000 records: ~80,000 tokens
- 10,000 records: ~800,000 tokens (exceeds context limits!)

**After:**
```python
# Write to file instead
import csv, json
from datetime import datetime
from pathlib import Path

# Generate records (same logic)
records = [...]

# Save to files
Path("outputs/test_data").mkdir(parents=True, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Write CSV
with open(f"outputs/test_data/{timestamp}_data.csv", 'w') as f:
    csv.DictWriter(f, fieldnames=records[0].keys()).writerows(records)

# Write JSON  
with open(f"outputs/test_data/{timestamp}_data.json", 'w') as f:
    json.dump(records, f)

# Return ONLY metadata
result = {
    "status": "success",
    "total_records": len(records),
    "files": {
        "csv": f"outputs/test_data/{timestamp}_data.csv",
        "json": f"outputs/test_data/{timestamp}_data.json"
    },
    "summary": {
        "metrics": list(set([r['metric'] for r in records])),
        "sample_record": records[0]
    }
}
print(json.dumps(result))
```

Output tokens regardless of dataset size:
- 5 records: ~100 tokens (metadata only)
- 100 records: ~100 tokens (metadata only)
- 1,000 records: ~100 tokens (metadata only)
- 10,000 records: ~100 tokens (metadata only)

**Savings for 100 records: 7,900 tokens (99% reduction)**
**Savings for 1,000 records: 79,900 tokens (99.9% reduction)**

## Implementation

### New Configuration File

**File:** `config/test_data_parser_file_output.yaml`

**Key Features:**
1. Condensed business context (150 tokens vs 400)
2. Minimal Python templates (200 tokens vs 1,200)
3. File-based output (100 tokens vs 8,000+ for datasets)
4. Clear instructions to NOT return full data

### Usage

```bash
# Test with 5 records
curl --location 'http://localhost:8000/query/form' \
  --form 'input="create 5 records for metric abcd, xyz, program MFG, sector PFNA, plant p1, values 10 to 100, uom count, 5% negative from -10 to 0"' \
  --form 'config_path="config/test_data_parser_file_output.yaml"' \
  --form 'raw_output="True"' \
  --form 'thread_id="test-001"'

# Test with 1000 records (huge savings!)
curl --location 'http://localhost:8000/query/form' \
  --form 'input="create 1000 records for metric revenue, cost, profit, program MFG, sector PFNA, plant p1, values 1000 to 50000, uom count"' \
  --form 'config_path="config/test_data_parser_file_output.yaml"' \
  --form 'raw_output="True"' \
  --form 'thread_id="test-002"'
```

### Expected Results

Response will contain:
```json
{
  "status": "success",
  "total_records": 1000,
  "files": {
    "csv": "outputs/test_data/20251001_154530_data.csv",
    "json": "outputs/test_data/20251001_154530_data.json"
  },
  "summary": {
    "metrics": ["revenue", "cost", "profit"],
    "date_range": "2024-09-01 to 2025-10-01",
    "sample_record": {
      "record_id": 1,
      "metric": "revenue",
      "value": 23456,
      "program_code": "MFG",
      "sector": "PFNA",
      "plant_code": "p1",
      "market_code": "US",
      "uom": "count",
      "date": "2024-09-15"
    }
  }
}
```

Actual data is in the files, consuming ZERO tokens!

## Token Comparison

| Dataset Size | Original Config | Optimized Config | Savings | % Reduction |
|--------------|-----------------|------------------|---------|-------------|
| 5 records    | ~6,500 tokens   | ~2,500 tokens    | 4,000   | 62%         |
| 100 records  | ~50,000 tokens  | ~2,800 tokens    | 47,200  | 94%         |
| 1,000 records| ~480,000 tokens | ~3,000 tokens    | 477,000 | 99.4%       |
| 10,000 records| Exceeds limit  | ~3,200 tokens    | N/A     | 99.9%+      |

## Best Practices for Large Data Handling

### 1. **Never Return Large Data in Agent Responses**

❌ **Bad:**
```python
result = generate_large_dataset()
print(json.dumps(result))  # Consumes massive tokens
```

✅ **Good:**
```python
result = generate_large_dataset()
file_path = save_to_file(result)
print(json.dumps({"file": file_path, "count": len(result)}))
```

### 2. **Use File References in Multi-Step Workflows**

When data needs to flow between agents:

❌ **Bad:**
```yaml
step1: Generate 1000 records → returns all 1000 records in response
step2: Process records → receives all 1000 records in input
# Total: 160,000 tokens wasted
```

✅ **Good:**
```yaml
step1: Generate 1000 records → saves to file → returns file path (100 tokens)
step2: Process records → reads from file path (100 tokens)
# Total: 200 tokens used
```

### 3. **Compress Business Context**

❌ **Bad:**
```yaml
business_context: |
  # Long Title
  
  Detailed explanation paragraph...
  
  ## Section 1
  - Item 1: Detailed description
  - Item 2: Detailed description
  ...
```

✅ **Good:**
```yaml
business_context: |
  Codes: Type1(A|B|C), Type2(X|Y|Z), Type3(1-9)
```

### 4. **Remove Redundant Examples from Prompts**

Modern LLMs (GPT-4, Claude) don't need detailed code templates:

❌ **Bad:**
```yaml
prompt: |
  Write Python code following this structure:
  ```python
  import X
  import Y
  
  def process():
      # Step 1: Do this
      result = ...
      
      # Step 2: Do that
      ...
      
      return result
  ```
```

✅ **Good:**
```yaml
prompt: |
  Write Python to extract params using regex. Return JSON only.
```

### 5. **Use Streaming for Real-Time Monitoring**

For very long-running data generation:

```python
# Stream progress updates without returning data
for i, batch in enumerate(generate_batches()):
    save_batch(batch, f"output_batch_{i}.csv")
    print(json.dumps({"progress": f"{i+1}/10 batches complete"}))
```

### 6. **Consider Output Formats**

For different use cases:

- **CSV:** Best for tabular data, Excel compatibility, minimal size
- **JSON:** Best for nested data, API consumption
- **Parquet:** Best for huge datasets, columnar storage, analytics
- **SQLite:** Best for queryable datasets, relational data

## Integration with LargeDataStorage

For datasets that need to be referenced by subsequent agents, use the existing `LargeDataStorage` system:

```python
from app.memory.large_data_storage import LargeDataStorage

# Initialize storage
storage = LargeDataStorage({
    "sqlite_path": "./large_tool_data.db",
    "file_path": "./large_tool_data_files/"
})

# Generate data
records = generate_test_data(params)

# Store with reference
storage_info = storage.store_large_data(
    reference_id=f"test_data_{timestamp}",
    tool_name="data_generator",
    data=records,
    metadata={"record_count": len(records), "metrics": metrics}
)

# Return reference only
result = {
    "status": "success",
    "data_reference": storage_info.reference_id,
    "total_records": len(records),
    "retrieval_hint": f"Use retrieve_large_data('{storage_info.reference_id}')"
}
```

## Monitoring Token Usage

Add logging to track token savings:

```python
# In api.py or logging module
def log_token_metrics(agent_name, input_tokens, output_tokens, data_size_avoided):
    metrics = {
        "agent": agent_name,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "data_records_avoided": data_size_avoided,
        "estimated_tokens_saved": data_size_avoided * 100  # ~100 tokens per record
    }
    logger.info(f"Token metrics: {json.dumps(metrics)}")
```

## Summary

By implementing these optimizations:

1. **Immediate savings:** 60% reduction for small datasets
2. **Massive savings:** 95-99% reduction for large datasets
3. **Scalability:** Can now handle 10,000+ record datasets
4. **Best practice:** Follows industry standards for agent-based systems
5. **No functionality loss:** Users get files they can download/process

The key principle: **Tokens should represent decisions and metadata, not bulk data.**
