# Phase 8 Test - Quick Start Guide

## 🚀 Quick Run

```bash
cd /Users/A80997271/Documents/projects/jk-agents-core/integration_tests
python test_00_super_integrated.py
```

**Phase 8 runs automatically** as part of the full test suite after Phases 1-7.

---

## ✅ Prerequisites Checklist

- [ ] `.env` file configured with Azure OpenAI credentials
- [ ] ChromaDB installed: `pip install chromadb`
- [ ] Temp directory writable: `./integration_tests/temp/`
- [ ] Python 3.8+ environment activated

---

## 📊 What Phase 8 Tests

1. **Generate 10,000 records** using Python MCP agent
2. **Verify storage** - Data saved to SQLite/filesystem, not bloating context
3. **Check context efficiency** - Response uses references, saves ~99% tokens
4. **Multi-turn conversation** - Agent remembers and accesses stored data
5. **Retrieve data** - Validate full dataset can be retrieved from storage

---

## 🎯 Success Criteria

Phase 8 passes when **all 5 sub-tests succeed**:

- ✅ Large dataset generated (10K records)
- ✅ Context efficient (<5K tokens vs. 50K+ without optimization)
- ✅ Data stored in SQLite with valid reference
- ✅ Multi-turn access works (agent remembers dataset)
- ✅ Data retrieval successful (can retrieve full 10K records)

---

## 📁 Key Files Modified/Created

| File | Change |
|------|--------|
| `app/memory/large_data_storage.py` | ➕ Added `list_references()` method (lines 337-362) |
| `integration_tests/test_00_super_integrated.py` | ➕ Added Phase 8 test function (lines 889-1132) |
| `integration_tests/test_00_super_integrated.py` | ✏️ Updated config with large_data_handling settings (lines 168-183) |
| `integration_tests/test_00_super_integrated.py` | ✏️ Integrated Phase 8 into main test runner (line 1244) |

---

## 🔍 Watch For

### Expected Behavior

- **Response length**: ~1,500-3,000 characters (summary + reference)
- **Storage location**: `./integration_tests/temp/large_tool_data.db`
- **Token savings**: 95-99% compared to full data
- **Generation time**: 2-5 seconds for 10K records

### Warning Signs

- ⚠️ Response > 50KB → Large data handling not working
- ⚠️ "No references found" → Storage not triggered or disabled
- ⚠️ Agent doesn't remember → Memory issues (check Phase 4)
- ⚠️ Retrieval returns None → Storage corruption or expiry

---

## 🛠️ Troubleshooting Commands

```bash
# Verify import works
python -c "from app.memory.large_data_storage import LargeDataStorage; print('✓ OK')"

# Check if large data config is in test
grep -A 10 "large_data_handling" integration_tests/test_00_super_integrated.py

# View storage after test
sqlite3 ./integration_tests/temp/large_tool_data.db "SELECT * FROM large_tool_data;"

# Check file storage
ls -lh ./integration_tests/temp/large_tool_data_files/
```

---

## 📖 Full Documentation

See `PHASE8_IMPLEMENTATION_SUMMARY.md` for:
- Detailed architecture
- Storage tiering strategy
- Database schema
- Performance metrics
- Future enhancements

---

## 🐛 Common Issues

### Issue: Import Error

```bash
# Solution: Verify Python path
export PYTHONPATH=/Users/A80997271/Documents/projects/jk-agents-core:$PYTHONPATH
```

### Issue: SQLite Database Locked

```bash
# Solution: Remove lock file
rm ./integration_tests/temp/large_tool_data.db-shm
rm ./integration_tests/temp/large_tool_data.db-wal
```

### Issue: Phase 8 Skipped

**Cause**: Earlier phase failed (Phase 1 or 2 are critical)

**Solution**: Check Phase 1-2 output, fix configuration/credentials

---

## 💡 Pro Tips

1. **Clean run**: Delete `./integration_tests/temp/` before test for fresh start
2. **Isolated test**: Watch Phase 8 with `2>&1 | grep -A 100 "Phase 8"`
3. **Debug mode**: Add `import pdb; pdb.set_trace()` in Phase 8 function
4. **Verify storage**: Check SQLite database after test with `sqlite3` command

---

## 📞 Need Help?

1. Check logs in `memory_logs/` directory
2. Review `PHASE8_IMPLEMENTATION_SUMMARY.md`
3. Verify Azure OpenAI credentials: `echo $AZURE_OPENAI_API_KEY`
4. Test ChromaDB: `python -c "import chromadb; print('✓ ChromaDB OK')"`

---

**Last Updated**: 2024  
**Status**: ✅ Ready for Execution
