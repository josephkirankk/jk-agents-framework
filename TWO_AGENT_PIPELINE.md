# Two-Agent Pipeline: Test Data Generator

## Overview

The `test_data_parser_simple.yaml` configuration now implements a **two-agent pipeline** that:

1. **Parses** natural language requirements into structured parameters
2. **Generates** actual test data records based on those parameters

## Architecture

```
User Query
    ↓
Supervisor (creates 2-step plan)
    ↓
┌─────────────────────────────────────────┐
│ Step 1: requirement_parser              │
│ - Extracts parameters from NL query     │
│ - Returns JSON specification            │
└─────────────────────────────────────────┘
    ↓ (parameters)
┌─────────────────────────────────────────┐
│ Step 2: data_generator                  │
│ - Takes parameters from Step 1          │
│ - Generates N test records              │
│ - Returns JSON array of records         │
└─────────────────────────────────────────┘
    ↓
Final Output: Array of test data records
```

## Agents

### 1. requirement_parser
**Purpose:** Extract parameters from natural language

**Input:** 
```
"create 100 records for metric abcd, xyz, program MFG, sector PFNA, 
plant p1, values 100 to 10000, uom count, 10% negative from -10 to -100"
```

**Output:**
```json
{
  "record_count": 100,
  "metrics": ["abcd", "xyz"],
  "program_code": "MFG",
  "sector": "PFNA",
  "plant_code": "p1",
  "market_code": "US",
  "value_range": {"min": 100, "max": 10000},
  "negative_percentage": 0.1,
  "negative_range": {"min": -10, "max": -100},
  "uom": "count",
  "date_range_days": 30
}
```

### 2. data_generator
**Purpose:** Generate actual test data records

**Input:** Parameters from requirement_parser

**Output:**
```json
{
  "total_records": 100,
  "parameters": {...},
  "records": [
    {
      "record_id": 1,
      "metric": "abcd",
      "value": 5432,
      "program_code": "MFG",
      "sector": "PFNA",
      "plant_code": "p1",
      "market_code": "US",
      "uom": "count",
      "date": "2025-09-15"
    },
    // ... 99 more records
  ]
}
```

## Features

### ✅ Parameter Extraction
- Record count
- Multiple metrics
- Program codes (MFG, ADV, STD)
- Sectors (PFNA, PBNA, QSNA, RSNA, ALL)
- Plants (p1, p2, p3, p4)
- Markets (US, IN, UK, DE)
- Value ranges (min/max)
- Negative value percentage and ranges
- Units of measure
- Date ranges

### ✅ Data Generation
- Random values within specified ranges
- Negative values distributed according to percentage
- Random dates within date range
- Proper distribution across multiple metrics
- Sequential record IDs
- All required fields populated

## Usage

### Basic Example
```bash
curl --location 'http://localhost:8000/query/form' \
  --form 'input="create 10 records for metric test"' \
  --form 'config_path="config/test_data_parser_simple.yaml"'
```

**Output:** 10 test data records with default parameters

### Complex Example
```bash
curl --location 'http://localhost:8000/query/form' \
  --form 'input="create 100 records for metric abcd, xyz, program MFG, sector PFNA, plant p1, values 100 to 10000, uom count, 10% negative from -10 to -100"' \
  --form 'config_path="config/test_data_parser_simple.yaml"'
```

**Output:** 100 records split between metrics "abcd" and "xyz" with:
- 90 positive values (100-10000)
- 10 negative values (-100 to -10)
- All other parameters as specified

### With raw_output
```bash
curl --location 'http://localhost:8000/query/form' \
  --form 'input="create 10 records for metric sales"' \
  --form 'config_path="config/test_data_parser_simple.yaml"' \
  --form 'raw_output="True"'
```

**Output:** Raw JSON array without conversational wrapper

## Testing

Run the provided test script:
```bash
./test_two_agent_pipeline.sh
```

This will:
- Test single metric generation
- Test multiple metrics
- Test negative values
- Save outputs to `/tmp/test*.json`

## Configuration Details

**File:** `config/test_data_parser_simple.yaml`

**Supervisor:**
- Creates 2-step sequential plan
- Step 1 depends on: []
- Step 2 depends on: [Step 1]
- Timeout: 60s for parsing, 120s for generation

**Agents:**
1. `requirement_parser` (react agent with Python tool)
2. `data_generator` (react agent with Python tool)

Both use the same MCP server configuration:
```yaml
mcp_servers:
  python_runner:
    transport: "stdio"
    command: "deno"
    args: [run, -N, -R=node_modules, -W=node_modules, 
           --node-modules-dir=auto, jsr:@pydantic/mcp-run-python, stdio]
```

## Advantages of Two-Agent Approach

1. **Modularity:** Each agent has a single responsibility
2. **Reusability:** Parser can be used for parameter validation only
3. **Debuggability:** Easy to inspect intermediate parameters
4. **Extensibility:** Can add more agents (e.g., data validator, formatter)
5. **Maintainability:** Changes to parsing logic don't affect generation

## Output Format

### Standard Output (raw_output=False)
Conversational response with records embedded

### Raw Output (raw_output=True)
Direct JSON structure:
```json
{
  "total_records": N,
  "parameters": {...},
  "records": [...]
}
```

## Performance

- **Parsing:** ~2-3 seconds
- **Generation (10 records):** ~3-5 seconds
- **Generation (100 records):** ~8-12 seconds
- **Total for 100 records:** ~10-15 seconds

## Troubleshooting

### Server needs restart after config changes
```bash
# Restart the API server to reload configuration
```

### Memory logs not created
Memory logs only appear for multi-turn conversations with the same thread_id. Single requests don't generate logs.

### Negative values not appearing
Check that:
- `negative_percentage` is properly extracted (0.1 for 10%)
- `negative_range` has valid min/max values
- Total records > 0

## Next Steps

Potential enhancements:
1. Add data validation agent
2. Add data formatting agent (CSV, Excel, etc.)
3. Add data persistence agent (save to database/file)
4. Add more constraint types (time-series, relationships, etc.)
