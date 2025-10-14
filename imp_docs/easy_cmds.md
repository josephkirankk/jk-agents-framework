# Quick Commands

## API Server Management

### Kill and Restart API Server

```bash
# Option 1: Kill by port and restart
kill -9 $(lsof -t -i :8000) && python api.py

# Option 2: Kill by process name  
pkill -f "python api.py" || true

# Option 3: Using virtual environment
source .venv/bin/activate && python api.py
```

### Test Commands

```bash
# Test agent continuity (recommended)
source .venv/bin/activate && python tests/test_agent_continuity.py

# Test working summarization system
source .venv/bin/activate && python tests/test_dynamic_summarization_working.py

# Test conversation continuity fix
source .venv/bin/activate && python tests/test_conversation_fix.py

# Test turn tracking implementation
source .venv/bin/activate && python tests/test_turn_tracking.py
```