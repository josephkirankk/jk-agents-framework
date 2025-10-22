# API Integration Tests - Quick Start Guide

## 🚀 Fastest Way to Run Tests

### Option 1: Automated (Recommended)
```bash
cd /Users/A80997271/Documents/projects/jk-agents-core
bash integration_tests/run_api_tests.sh
```
**Does everything**: Starts server, runs tests, cleans up

### Option 2: Quick Validation
```bash
cd /Users/A80997271/Documents/projects/jk-agents-core/integration_tests
../.venv/bin/python verify_api_fix.py
```
**Fast check**: Validates API fix is working (< 30 seconds)

---

## 📊 Current Status (2025-10-16)

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Passing | 3/8 | 37.5% |
| ❌ Failing | 5/8 | 62.5% |
| **Infrastructure** | **3/3** | **100%** ✅ |

---

## ✅ What's Working

1. **Health Checks** - `/health` endpoint ✅
2. **Memory Stats** - `/memory/stats` endpoint ✅
3. **Error Handling** - Proper 422 responses ✅
4. **JSON Requests** - API accepts JSON correctly ✅
5. **Performance Tracking** - Monitoring functional ✅

---

## ⚠️ Known Issues

**LLM Integration** (5 tests failing):
- Empty responses from LLM
- Error: `'str' object has no attribute 'invoke'`
- **Not an API problem** - supervisor/LLM configuration issue

**Next step**: Debug supervisor object initialization

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `run_api_tests.sh` | Automated test runner |
| `verify_api_fix.py` | Quick API validation |
| `API_TESTS_README.md` | Full documentation |
| `test_09_api_critical_flows.py` | Test suite |

---

## 🆘 Troubleshooting

### Port 8000 in use
```bash
lsof -ti :8000 | xargs kill -9
```

### API not responding
```bash
curl http://localhost:8000/health
```

### Check logs
```bash
tail -f logs/api_test.log
```

---

## 📖 Full Documentation

See `API_TESTS_README.md` for complete guide (460+ lines)

---

**Last Updated**: 2025-10-16  
**Test Duration**: ~11 seconds  
**Status**: Infrastructure Validated ✅
