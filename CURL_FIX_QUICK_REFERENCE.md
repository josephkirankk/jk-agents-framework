# Quick Reference: Curl Request Fix

## 🚨 **Original Issue**

Your curl request failed with these errors:
1. ❌ Typo: `"rpgram"` instead of `"program"`
2. ❌ Typo: `"Plat"` instead of `"plants"`
3. ❌ Data generation failed (Python import error)
4. ❌ Validation failed (no data found)

---

## ✅ **Quick Fix - Use This Curl Command**

```bash
curl --location 'http://localhost:8000/query/form' \
--form 'input="Generate 20 ProgramMetrics test records with the following requirements:
- Programs: prg1 and prg2 (mix of both)
- Sector: retail
- Plants: PLT-01 and PLT-02 (mix of both)
- All records must be schema-compliant"' \
--form 'config_path="config/json_schema_test_data_generator.yaml"' \
--form 'raw_output="False"' \
--form 'thread_id="test-'$(date +%s)'"'
```

**Why this works**:
- ✅ No typos
- ✅ Clear natural language
- ✅ Doesn't embed the entire schema
- ✅ Unique thread_id (timestamp-based)

---

## 🧪 **Test It**

### **Option 1: Use the Test Script**
```bash
./test_curl_request.sh
```

### **Option 2: Manual Test**
```bash
# 1. Start the API
python api.py --config config/json_schema_test_data_generator.yaml

# 2. In another terminal, run the curl command above

# 3. Check the logs
ls -lt agentlogs/ | head -1
```

---

## 📋 **What Changed**

| Original | Fixed |
|----------|-------|
| `"rpgram prg1 and prg2"` | `"program prg1 and prg2"` |
| `"in Plat PLT-01"` | `"for plants PLT-01"` |
| `"20 record"` | `"20 records"` |
| Embedded full schema | Natural language only |
| `thread_id="jk-pep-19"` | `thread_id="test-<timestamp>"` |

---

## 🔍 **Verify Success**

A successful response looks like:
```json
{
  "status": "success",
  "final_result": "Successfully generated and validated 20 ProgramMetrics records...",
  "dataset_reference_id": "ref_...",
  "validation_summary": {
    "total_records": 20,
    "valid_records": 20,
    "invalid_records": 0
  }
}
```

---

## 📚 **More Help**

- **Full troubleshooting**: See `TROUBLESHOOTING_CURL_ISSUES.md`
- **Documentation**: See `docs/JSON_SCHEMA_TEST_DATA_GENERATOR.md`
- **Quick start**: See `JSON_SCHEMA_DATA_GENERATOR_README.md`

---

## 🎯 **Alternative: Minimal Fixed Version**

If you prefer the original style with just typo fixes:

```bash
curl --location 'http://localhost:8000/query/form' \
--form 'input="Create 20 records with program prg1 and prg2 in retail sector for plants PLT-01 and PLT-02"' \
--form 'config_path="config/json_schema_test_data_generator.yaml"' \
--form 'raw_output="True"' \
--form 'thread_id="test-'$(date +%s)'"'
```

---

**Created**: 2025-10-08  
**Status**: Ready to use

