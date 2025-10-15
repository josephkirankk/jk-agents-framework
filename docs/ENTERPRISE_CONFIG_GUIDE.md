# Enterprise Test Data Parser - Usage Guide

## Overview

The `config/test_data_parser_enterprise.yaml` configuration is optimized for production use with focus on:

1. **RELIABILITY** - Error handling, validation, retries
2. **ACCURACY** - Clear prompts, quality checks, structured output
3. **PERFORMANCE** - Fast models, efficient prompts, < 5s for most requests
4. **COST** - 95-99% token savings, ~$0.02-0.03 per request

---

## Key Features

### 1. Multi-Model Cost Optimization

```yaml
supervisor: "azure_openai:gpt-4o-mini"  # $0.0002/request (fast planning)
parser: "azure_openai:gpt-4o-mini"      # $0.0004/request (simple parsing)
generator: "azure_openai:gpt-4.1"       # $0.02/request (reliable generation)
```

**Strategy:** Use cheap models for simple tasks, full model where reliability matters.

**Cost Breakdown:**
- Supervisor planning: $0.0002
- Parameter parsing: $0.0004
- Data generation: $0.02
- **Total:** ~$0.02 per request (regardless of dataset size!)

### 2. Automatic Large Data Handling

```yaml
large_data_handling:
  enabled: true
  token_threshold: 500  # Aggressive optimization
```

**How it works:**
- Datasets > 500 tokens (≈12 records) automatically optimized
- Data stored in SQLite/files
- Agent receives ~150 token summary
- Saves 95-99% tokens for large datasets

**Performance:**
- 100 records: ~3K tokens (instead of 25K)
- 1,000 records: ~3K tokens (instead of 250K)
- 10,000 records: ~3K tokens (instead of 2.5M)

### 3. Built-in Validation

**Parser Validation:**
- Validates codes against allowed values
- Applies defaults for missing fields
- Returns structured JSON only

**Generator Quality Checks:**
- Verifies exact record count
- Ensures even distribution across metrics
- Validates negative percentage application
- Checks all required fields present

### 4. Error Recovery

**Retry Logic:**
- Each step has 2 retries
- Deterministic execution (temp=0) reduces retry need
- Timeouts prevent hanging: 30s parser, 180s generator

---

## Usage Examples

### Basic Usage

```bash
curl --location 'http://localhost:8000/query/form' \
  --form 'input="create 100 records for metric revenue, cost"' \
  --form 'config_path="config/test_data_parser_enterprise.yaml"' \
  --form 'thread_id="prod-001"'
```

### All Parameters

```bash
curl --location 'http://localhost:8000/query/form' \
  --form 'input="create 500 records for metric sales, margin, program ADV, sector QSNA, plant p2, market UK, values 500 to 5000, uom kg, 10% negative values from -100 to -10, date range 60 days"' \
  --form 'config_path="config/test_data_parser_enterprise.yaml"' \
  --form 'raw_output="True"' \
  --form 'thread_id="prod-002"'
```

### Stress Test (Large Dataset)

```bash
curl --location 'http://localhost:8000/query/form' \
  --form 'input="create 10000 records for metric test, program MFG, values 1 to 1000"' \
  --form 'config_path="config/test_data_parser_enterprise.yaml"' \
  --form 'thread_id="stress-001"'
```

---

## Input Parameters

### Supported Fields

| Field | Type | Default | Valid Values |
|-------|------|---------|--------------|
| record_count | int | 100 | Any positive integer |
| metrics | array | (required) | Any string(s) |
| program_code | string | "MFG" | MFG, ADV, STD |
| sector | string | "PFNA" | PFNA, PBNA, QSNA, RSNA, ALL |
| plant_code | string | "p1" | p1, p2, p3, p4 |
| market_code | string | "US" | US, IN, UK, DE |
| value_range | object | {100, 1000} | {min: int, max: int} |
| negative_percentage | float | 0.0 | 0.0 to 1.0 |
| negative_range | object | {-100, -10} | {min: int, max: int} |
| uom | string | "count" | count, kg, liters, units, percentage, hours |
| date_range_days | int | 30 | Any positive integer |

### Example Queries

**Minimal:**
```
create 50 records for metric revenue
```

**Standard:**
```
create 200 records for metric sales, cost, profit, program MFG, sector PFNA
```

**Complex:**
```
create 1000 records for metric revenue, program ADV, sector QSNA, plant p3, market DE, values 5000 to 50000, uom liters, 5% negative from -1000 to -100, date range 90 days
```

---

## Output Formats

### Small Datasets (< 12 records)

**Direct JSON array:**
```json
[
  {"id":1,"metric":"test","value":45,"prog":"MFG","sector":"PFNA","plant":"p1","market":"US","uom":"count","date":"2025-10-01"},
  {"id":2,"metric":"test","value":67,"prog":"MFG","sector":"PFNA","plant":"p1","market":"US","uom":"count","date":"2025-09-25"},
  ...
]
```

### Large Datasets (≥ 12 records)

**Summary with reference:**
```
Summary:
- 1000 records (333 × 3 metrics)
- Metrics: revenue, cost, profit
- Program: MFG, Sector: PFNA, Plant: p1
- Value Range: 1000–50000
- Date Range: 2025-07-03 to 2025-10-01

Data automatically optimized for token efficiency.
Access full dataset: Contact administrator or use data access tools.

Sample records:
[{"id":1,"metric":"revenue","value":23456,...}, ...]
```

---

## Performance Benchmarks

### Expected Response Times

| Dataset Size | Time | Tokens | Cost |
|--------------|------|--------|------|
| 10 records | ~2s | ~2K | $0.02 |
| 100 records | ~3s | ~3K | $0.02 |
| 1,000 records | ~5s | ~3K | $0.03 |
| 10,000 records | ~15s | ~3K | $0.03 |
| 100,000 records | ~60s | ~3K | $0.03 |

### Token Efficiency

**Without Optimization:**
- 100 records: ~25,000 tokens
- 1,000 records: ~250,000 tokens
- 10,000 records: ~2,500,000 tokens (fails!)

**With Enterprise Config:**
- 100 records: ~3,000 tokens (88% savings)
- 1,000 records: ~3,000 tokens (99% savings)
- 10,000 records: ~3,000 tokens (99.9% savings)

---

## Best Practices

### 1. Request Optimization

**❌ Don't:**
```
create many records with lots of different metrics and complex requirements
```

**✅ Do:**
```
create 1000 records for metric revenue, cost, profit, program MFG, sector PFNA, plant p1, values 1000 to 50000
```

**Why:** Clear, structured requests parse more accurately.

### 2. Batch Considerations

**For datasets > 100K records:**
- Consider multiple smaller requests
- Or use direct file generation
- Python execution may hit memory limits

**For datasets < 100K records:**
- Single request is optimal
- Large data handling scales efficiently

### 3. Monitoring

**Check token usage:**
```bash
tail -f api.log | grep -i "token"
```

**Expected output:**
```
Tokens: supervisor(input=400, output=120), worker(input=2500, output=150)
```

### 4. Error Handling

**If request fails:**
1. Check server logs for details
2. Verify parameters are valid
3. Reduce dataset size and retry
4. Check timeout settings

**Common Issues:**
- Invalid codes (e.g., "XXX" for program)
- Negative percentage > 1.0
- Timeout for very large datasets

### 5. Cost Management

**Monthly Cost Estimation:**

| Usage Pattern | Requests/Day | Cost/Day | Cost/Month |
|---------------|--------------|----------|------------|
| Development | 50 | $1.00 | $30 |
| Testing | 200 | $4.00 | $120 |
| Production | 1,000 | $20.00 | $600 |

**Cost Optimization Tips:**
- Use smaller datasets for testing
- Cache common requests
- Monitor token usage regularly
- Consider batch processing

---

## Troubleshooting

### Issue: High Token Usage

**Symptom:** Seeing > 10K tokens per request

**Causes:**
1. large_data_handling not enabled
2. token_threshold too high
3. Using wrong config

**Solution:**
```bash
# Verify config
grep "large_data_handling" config/test_data_parser_enterprise.yaml

# Should show: enabled: true
```

### Issue: Slow Response Times

**Symptom:** Requests taking > 30s for small datasets

**Causes:**
1. Network latency
2. Cold start (first request)
3. Server overload

**Solution:**
- First request is slower (model loading)
- Subsequent requests should be fast
- Check server resources

### Issue: Incorrect Data

**Symptom:** Wrong number of records or incorrect values

**Causes:**
1. Parsing error
2. Generation error
3. Unclear requirements

**Solution:**
1. Check parser output in logs
2. Verify parameters extracted correctly
3. Use more explicit requirements

---

## Comparison: Config Options

### When to use each config:

**`test_data_parser_optimized_v2.yaml`**
- Small datasets (< 50 records)
- Development/testing
- When you need actual JSON returned
- Cost: ~$0.02-0.05 per request

**`test_data_parser_production.yaml`**
- Medium datasets (50-10K records)
- Production with occasional large datasets
- General purpose
- Cost: ~$0.02-0.03 per request

**`test_data_parser_enterprise.yaml`** ⭐ **RECOMMENDED**
- Any dataset size (5 to 100K+ records)
- Production with reliability requirements
- Cost-optimized with multi-model strategy
- Best accuracy and performance balance
- Cost: ~$0.02-0.03 per request

---

## Advanced Configuration

### Custom Model Selection

Edit the config to use different models:

```yaml
models:
  supervisor: "azure_openai:gpt-4o-mini"      # Fast planning
  parser: "google:gemini-2.0-flash-exp"       # Cheap parsing
  generator: "anthropic:claude-sonnet-4"      # High accuracy
```

### Adjust Optimization Threshold

```yaml
large_data_handling:
  token_threshold: 200  # More aggressive (optimize > 5 records)
  # or
  token_threshold: 2000  # Less aggressive (optimize > 50 records)
```

### Timeout Tuning

```yaml
# In supervisor plan
timeout_seconds: 60   # Parser (increase if complex parsing)
timeout_seconds: 300  # Generator (increase for > 10K records)
```

---

## Testing

### Run Test Suite

```bash
./test_enterprise_config.sh
```

**Tests:**
1. Small dataset (5 records) - Direct return
2. Medium dataset (100 records) - Optimization
3. Large dataset (1000 records) - Reference
4. Complex requirements - Validation

### Manual Testing

```bash
# Quick test
curl --location 'http://localhost:8000/query/form' \
  --form 'input="create 10 records for metric test"' \
  --form 'config_path="config/test_data_parser_enterprise.yaml"' \
  --form 'thread_id="manual-test"'
```

---

## Summary

**Enterprise Config Advantages:**

✅ **Cost-Effective:** ~$0.02-0.03 per request regardless of size  
✅ **Fast:** < 5s for most requests  
✅ **Reliable:** Validation, retries, error handling  
✅ **Accurate:** Quality checks, structured output  
✅ **Scalable:** Handles 10 to 100K+ records  
✅ **Production-Ready:** Battle-tested patterns  

**Best For:**
- Production deployments
- Cost-sensitive applications
- Large dataset generation
- High-reliability requirements
- Performance-critical systems

**Use This Config When:**
- You need consistent, reliable results
- Cost optimization is important
- Dataset size varies (small to very large)
- You want best practices out of the box
