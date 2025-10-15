# Quick Start: Super Integrated Test

## 🚀 Run in 3 Steps

### 1. Prerequisites Check
```bash
# Ensure you have Azure OpenAI credentials in .env
cat .env | grep AZURE_OPENAI

# Install dependencies if needed
pip install -r requirements.txt
pip install chromadb

# Verify Deno is installed
deno --version
```

### 2. Run the Test
```bash
cd /Users/A80997271/Documents/projects/jk-agents-core/integration_tests
python test_00_super_integrated.py
```

### 3. Check Results
- ✅ Exit code 0 = All tests passed
- ❌ Exit code 1 = Some tests failed
- 📊 Performance metrics printed at end

## 📋 What Gets Tested

**7 Comprehensive Phases:**
1. ⚙️  System Initialization (Config, Memory, Models)
2. 🤖 Single Agent Execution (Normal & React agents)
3. 🎯 Supervisor Orchestration (Planning & Execution)
4. 💾 Multi-turn Memory (Conversations & Threads)
5. 🔧 Advanced Features (Files, Tools, Complex tasks)
6. 🌐 API Integration (Health, Memory endpoints)
7. 🧹 Cleanup & Verification (Resource cleanup)

## ⏱️ Expected Runtime
- **Full test:** ~45-60 seconds
- **Critical phases only:** ~20-30 seconds

## 🔍 Quick Troubleshooting

**Issue:** `ChromaDB not available`  
**Fix:** `pip install chromadb`

**Issue:** `Azure OpenAI credentials not configured`  
**Fix:** Add credentials to `.env` file

**Issue:** `deno: command not found`  
**Fix:** Install from https://deno.land/

**Issue:** `API not available` (Phase 6)  
**Note:** This is expected if API server isn't running - test continues

## 📖 Full Documentation
See `README_SUPER_TEST.md` for complete details.

## 💡 Pro Tips

**Save output to file:**
```bash
python test_00_super_integrated.py 2>&1 | tee test_results.log
```

**Run from any directory:**
```bash
python /path/to/jk-agents-core/integration_tests/test_00_super_integrated.py
```

**Check test is executable:**
```bash
chmod +x test_00_super_integrated.py
./test_00_super_integrated.py
```

---

**Happy Testing! 🎉**
