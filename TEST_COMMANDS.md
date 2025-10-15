# Test Commands for jk-agents-core

These commands are ready to copy-paste into your terminal.

## Prerequisites

Start the API server in a separate terminal:
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

---

## Test 1: Health Check

```bash
curl http://localhost:8000/health
```

Expected output: `{"status":"healthy"}` or similar

---

## Test 2: Small Dataset (No Optimization)

This should **NOT** trigger large_data_handling (< 500 tokens):

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "create 10 records for metric test, program MFG, sector PFNA, values 10 to 50",
    "config_name": "test_data_parser_enterprise.yaml"
  }'
```

Expected: Direct response with 10 records

---

## Test 3: Medium Dataset (Should Optimize)

This **SHOULD** trigger large_data_handling (1,000 records):

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "create 1000 records for metric revenue, cost, program MFG, sector PFNA, plant p1, values 100 to 500, uom count",
    "config_name": "test_data_parser_enterprise.yaml"
  }'
```

Expected: "Large Data Reference Created" message with optimization stats

---

## Test 4: Large Dataset (Definitely Optimizes)

This **DEFINITELY SHOULD** trigger large_data_handling (5,000 records):

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "create 5000 records for metric abcd, xyz, program MFG, sector PFNA, plant p1, values 10 to 100, uom count, 5 percent negative from -10 to 1",
    "config_name": "test_data_parser_enterprise.yaml"
  }'
```

Expected: "Large Data Reference Created" with reference_id and 3 dynamic tools

---

## Test 5: Very Large Dataset (Maximum Optimization)

This will show the full power of large_data_handling (50,000 records):

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "create 50000 records for metric abcd, xyz, qrs, program MFG, sector PFNA, plant p1, values 10 to 100, uom count, 5 percent negative from -10 to 1",
    "config_name": "test_data_parser_enterprise.yaml"
  }'
```

Expected: Massive token savings (250K → 200 tokens, ~$3.75 saved)

---

## Inspection Commands

### Check what's stored:
```bash
python3 inspect_storage_systems.py
```

### Check storage with SQLite directly:
```bash
sqlite3 ./data/large_tool_data.db "SELECT reference_id, tool_name, ROUND(size_bytes/1048576.0, 2) as size_mb, datetime(created_at) as created FROM large_tool_data ORDER BY created_at DESC LIMIT 10;"
```

### Count stored references:
```bash
sqlite3 ./data/large_tool_data.db "SELECT COUNT(*) as total_references FROM large_tool_data;"
```

### Check memory stats via API:
```bash
curl http://localhost:8000/memory/stats | jq
```

---

## Alternative: Use the Test Script

Run all tests automatically:
```bash
./test_system.sh
```

This will:
1. Check if server is running
2. Run 3 tests (small, medium, large datasets)
3. Show optimization results
4. Inspect storage automatically

---

## Troubleshooting

### Server not running?
```bash
# Start in one terminal
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### Wrong deployment error?
The config has been fixed to use `gpt-4.1`. Verify with:
```bash
grep "model:" config/test_data_parser_enterprise.yaml
```

Should show `azure_openai:gpt-4.1` everywhere.

### Check system status:
```bash
python3 verify_system.py
```

---

## Expected Results

### Small Dataset (10 records)
- Processing time: ~2-3 seconds
- Optimization: **NOT triggered**
- Output: Direct JSON with 10 records

### Medium Dataset (1,000 records)
- Processing time: ~5-10 seconds
- Optimization: **TRIGGERED**
- Token savings: ~10,000 tokens (~$0.15)
- Storage: SQLite (compressed)

### Large Dataset (5,000 records)
- Processing time: ~10-20 seconds
- Optimization: **TRIGGERED**
- Token savings: ~60,000 tokens (~$0.90)
- Storage: SQLite (compressed)

### Very Large Dataset (50,000 records)
- Processing time: ~30-60 seconds
- Optimization: **TRIGGERED**
- Token savings: ~250,000 tokens (~$3.75)
- Storage: SQLite or file system (depending on size)

---

## Understanding the Response

When large_data_handling triggers, you'll see:

```json
{
  "response": "✅ **Large Data Reference Created**\n\n**Reference ID**: `abc123def456`\n**Summary**: run_python_code returned 5,000 records with fields: id, metric, value, prog, sector, plant, market, uom, date...\n\n**Size Information**:\n• Category: MEDIUM\n• Size: 2.50 MB (62,500 tokens)\n• Storage: sqlite\n\n**Optimization Results**:\n• Tokens saved: 62,300\n• Cost saved: ~$0.9345\n• Compression: 2.5MB → 200 tokens\n\n**Available Data Access Tools**:\n1. `get_subset_abc123def456` - Get filtered subsets\n2. `search_data_abc123def456` - Search within data\n3. `get_stats_abc123def456` - Statistical summary"
}
```

The LLM can then use the 3 dynamic tools to explore the data without loading all 50,000 records!

---

**Documentation:**
- Quick Reference: `LARGE_DATA_QUICK_REF.md`
- Deep Dive: `LARGE_DATA_HANDLING_DEEP_DIVE.md`
- System Verification: `python3 verify_system.py`
- Storage Inspection: `python3 inspect_storage_systems.py`
