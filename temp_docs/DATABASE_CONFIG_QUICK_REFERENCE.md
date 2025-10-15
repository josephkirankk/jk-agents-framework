# Database Configuration Quick Reference

## TL;DR

All database paths are now centralized in `.env` file. Just use components without config:

```python
from app.memory.large_data_storage import LargeDataStorage

storage = LargeDataStorage()  # Automatically loads from .env
```

## Environment Variables (.env)

```bash
# Production paths
DB_BASE_PATH=./data
LARGE_DATA_DB_PATH=./data/large_data_storage.db
LARGE_DATA_FILES_PATH=./data/large_files
CHROMADB_PATH=./data/chromadb

# Test paths  
TEST_DB_BASE_PATH=./test_data
TEST_LARGE_DATA_DB_PATH=./test_data/large_data_storage.db
TEST_LARGE_DATA_FILES_PATH=./test_data/large_files
TEST_CHROMADB_PATH=./test_data/chromadb

# Configuration
LARGE_DATA_COMPRESSION_ENABLED=true
LARGE_DATA_MAX_SQLITE_SIZE_MB=50
LARGE_DATA_TOKEN_THRESHOLD=1000
```

## Common Usage

### Production Use
```python
# Automatically uses production paths from .env
from app.memory.large_data_storage import LargeDataStorage
storage = LargeDataStorage()
```

### Testing
```python
# Use test paths to avoid conflicts
from app.database_config import get_database_config
config = get_database_config(is_test_mode=True)
storage = LargeDataStorage(config.get_large_data_config())
```

### Custom Path Override
```python
# Override when needed (e.g., specific demo)
storage = LargeDataStorage({
    "sqlite_path": "./demo_data/db.db",
    "file_path": "./demo_data/files/"
})
```

## Core Components

| Component | Import | Usage |
|-----------|--------|-------|
| App Storage | `from app.memory.large_data_storage import LargeDataStorage` | `LargeDataStorage()` |
| Core Storage | `from core.large_data_storage import LargeDataStorage` | `LargeDataStorage()` |
| ChromaDB | `from app.memory.chromadb_backend import ChromaDBBackend` | Auto-loads path |
| Config Module | `from app.database_config import get_database_config` | `get_database_config()` |

## Configuration Functions

```python
from app.database_config import (
    get_database_config,      # Get full config object
    get_large_data_config,    # Get storage config dict
    get_chromadb_path,        # Get ChromaDB path
    reset_database_config     # Reset (testing)
)

# Get full config
config = get_database_config()
config = get_database_config(is_test_mode=True)  # Test mode

# Get specific configs
large_data = get_large_data_config(format="app")   # app.memory format
large_data = get_large_data_config(format="core")  # core format
chromadb = get_chromadb_path()

# Override paths
config.override_path("large_data_db", "./custom/db.db")
```

## Migration Checklist

- [x] Update `.env` file with database paths
- [x] Remove hardcoded paths from code
- [x] Use `LargeDataStorage()` without config
- [x] Use test mode in tests
- [x] Run test suite to verify

## Testing

```bash
# Run centralized config tests
python temp_tests/test_centralized_database_config.py

# All tests should pass ✓
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Database not found | Check `.env` file exists and is loaded |
| Permission denied | Run `chmod -R 755 data/` |
| Test/prod conflict | Use `is_test_mode=True` for tests |
| Custom path not working | Verify config format matches storage type |

## Before/After Examples

### Before (Hardcoded)
```python
storage = LargeDataStorage({
    "sqlite_path": "./data/large_data_storage.db",
    "file_path": "./data/large_files/",
    "compression": True,
    "max_sqlite_size_mb": 50
})
```

### After (Centralized)
```python
storage = LargeDataStorage()  # Done!
```

## Files Changed

**Created:**
- `app/database_config.py` - Centralized config module

**Updated:**
- `app/memory/large_data_storage.py`
- `core/large_data_storage.py`
- `app/memory/chromadb_backend.py`
- `app/mcp_large_data_server.py`
- `app/mcp_python_wrapper.py`
- `.env.example`

**Tested:**
- `temp_tests/test_centralized_database_config.py`

## Benefits

✅ Single source of truth  
✅ No hardcoded paths  
✅ Easy environment switching  
✅ Test mode support  
✅ Backward compatible  
✅ Cross-platform (Windows/macOS)

---

**For full documentation, see:** [CENTRALIZED_DATABASE_CONFIG.md](./CENTRALIZED_DATABASE_CONFIG.md)
