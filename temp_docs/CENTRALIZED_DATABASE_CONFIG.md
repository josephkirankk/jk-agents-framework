# Centralized Database Configuration

## Overview

All database paths in the JK Agents framework are now centralized and loaded from environment variables through the `app.database_config` module. This eliminates hardcoded paths and ensures consistency across the entire codebase.

## Key Features

✅ **Single Source of Truth**: All database paths defined in `.env` file  
✅ **Automatic Loading**: Components automatically load paths from environment  
✅ **Test Mode Support**: Separate paths for testing to avoid conflicts  
✅ **Override Support**: Custom paths can still be provided when needed  
✅ **Backward Compatible**: Existing code continues to work with fallbacks  
✅ **Cross-Platform**: Works on both Windows and macOS

## Environment Variables

### Production Paths

Add these to your `.env` file (already in `.env.example`):

```bash
# Base directory for all database files
DB_BASE_PATH=./data

# Large data storage database (SQLite)
LARGE_DATA_DB_PATH=./data/large_data_storage.db

# Large data file storage directory
LARGE_DATA_FILES_PATH=./data/large_files

# ChromaDB persistent storage path
CHROMADB_PATH=./data/chromadb

# Large data storage configuration
LARGE_DATA_COMPRESSION_ENABLED=true
LARGE_DATA_MAX_SQLITE_SIZE_MB=50
LARGE_DATA_TOKEN_THRESHOLD=1000
```

### Test Paths

Separate paths for testing (automatically used in test mode):

```bash
# Test database paths (used during testing)
TEST_DB_BASE_PATH=./test_data
TEST_LARGE_DATA_DB_PATH=./test_data/large_data_storage.db
TEST_LARGE_DATA_FILES_PATH=./test_data/large_files
TEST_CHROMADB_PATH=./test_data/chromadb
```

## Usage

### Using Default Configuration (Recommended)

All storage systems now automatically load configuration from environment:

```python
# app/memory/large_data_storage.py - No config needed!
from app.memory.large_data_storage import LargeDataStorage

# Automatically loads from environment
storage = LargeDataStorage()
```

```python
# core/large_data_storage.py - No config needed!
from core.large_data_storage import LargeDataStorage

# Automatically loads from environment
storage = LargeDataStorage()
```

```python
# ChromaDB backend - Automatically loads path
from app.memory.chromadb_backend import ChromaDBBackend

backend = ChromaDBBackend()
await backend.initialize({})  # Path loaded from env
```

### Using Custom Configuration (Optional)

You can still override with custom paths when needed:

```python
# Custom config for app.memory.LargeDataStorage
custom_config = {
    "sqlite_path": "./custom/path/db.db",
    "file_path": "./custom/path/files/",
    "compression": True,
    "max_sqlite_size_mb": 100
}
storage = LargeDataStorage(custom_config)
```

```python
# Custom config for core.LargeDataStorage
storage = LargeDataStorage(
    storage_path="./custom/db.db",
    file_storage_path="./custom/files/",
    compression_enabled=True
)
```

### Using Test Mode

For testing, use test mode to avoid conflicts with production data:

```python
from app.database_config import get_database_config

# Get test mode configuration
test_config = get_database_config(is_test_mode=True)

# Use with storage
storage = LargeDataStorage(test_config.get_large_data_config())
```

### Direct Access to Configuration

```python
from app.database_config import (
    get_database_config,
    get_large_data_config,
    get_chromadb_path
)

# Get full configuration object
config = get_database_config()
print(config.paths.base_path)
print(config.paths.large_data_db)
print(config.paths.chromadb)

# Get specific configs
large_data_cfg = get_large_data_config(format="app")  # or "core"
chromadb_path = get_chromadb_path()
```

## Architecture

### Module Structure

```
app/
├── database_config.py          # Centralized configuration module
├── memory/
│   ├── large_data_storage.py   # Uses database_config
│   └── chromadb_backend.py     # Uses database_config
└── mcp_large_data_server.py    # Uses database_config
    mcp_python_wrapper.py        # Uses database_config

core/
└── large_data_storage.py        # Uses database_config
```

### Configuration Flow

```
.env file
    ↓
database_config.py (loads & validates)
    ↓
Components automatically load
    - app.memory.large_data_storage
    - core.large_data_storage
    - app.memory.chromadb_backend
    - MCP servers
```

## Migration Guide

### Before (Hardcoded Paths)

```python
# Old way - hardcoded paths everywhere
storage = LargeDataStorage({
    "sqlite_path": "./data/large_data_storage.db",
    "file_path": "./data/large_files/",
    "compression": True
})
```

### After (Centralized Config)

```python
# New way - automatic from environment
storage = LargeDataStorage()  # That's it!
```

### Updating Existing Code

1. **Simple case** - Just remove the config parameter:
   ```python
   # Before
   storage = LargeDataStorage(config)
   
   # After
   storage = LargeDataStorage()  # Loads from env
   ```

2. **Custom paths needed** - Keep the config but simplify:
   ```python
   # Before
   config = {
       "sqlite_path": os.getenv("LARGE_DATA_SQLITE_PATH", "./data/large_data_storage.db"),
       "file_path": os.getenv("LARGE_DATA_FILE_PATH", "./data/large_files/"),
       "compression": os.getenv("LARGE_DATA_COMPRESSION", "true").lower() == "true"
   }
   storage = LargeDataStorage(config)
   
   # After
   storage = LargeDataStorage()  # Much simpler!
   ```

3. **Test mode** - Use test configuration:
   ```python
   # Before
   storage = LargeDataStorage({
       "sqlite_path": "./test_data/db.db",
       "file_path": "./test_data/files/"
   })
   
   # After
   from app.database_config import get_database_config
   config = get_database_config(is_test_mode=True)
   storage = LargeDataStorage(config.get_large_data_config())
   ```

## Benefits

### 1. **Consistency**
All components use the same database paths - no more scattered databases in different locations.

### 2. **Easy Configuration**
Change one `.env` file instead of updating code in multiple places.

### 3. **Environment-Specific**
Different paths for development, testing, and production without code changes.

### 4. **Maintainability**
Single module to maintain database configuration logic.

### 5. **Testing**
Separate test paths prevent conflicts with production data.

### 6. **Debugging**
Easy to see where databases are located by checking one configuration file.

## Files Updated

### Core Files
- ✅ `app/database_config.py` - New centralized config module
- ✅ `app/memory/large_data_storage.py` - Uses centralized config
- ✅ `core/large_data_storage.py` - Uses centralized config
- ✅ `app/memory/chromadb_backend.py` - Uses centralized config
- ✅ `app/mcp_large_data_server.py` - Uses centralized config
- ✅ `app/mcp_python_wrapper.py` - Uses centralized config
- ✅ `.env.example` - Updated with database path variables

### Demo/Example Files
All demo and example files can now be simplified to use `LargeDataStorage()` without config.

## Testing

Run the comprehensive test suite:

```bash
cd /path/to/jk-agents-core
source .venv/bin/activate
python temp_tests/test_centralized_database_config.py
```

The test suite verifies:
- ✅ Configuration module loads correctly
- ✅ Default paths work
- ✅ Test mode paths work
- ✅ Environment variable overrides work
- ✅ Both storage implementations work
- ✅ ChromaDB backend works
- ✅ Data can be stored and retrieved

## Troubleshooting

### Issue: Database not found

**Cause**: Environment variables not loaded

**Solution**: Ensure `.env` file exists and is loaded:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Issue: Permission denied

**Cause**: Database directory doesn't exist or no write permission

**Solution**: Directories are auto-created, but check permissions:
```bash
ls -la data/
chmod -R 755 data/
```

### Issue: Test data conflicts with production

**Cause**: Not using test mode

**Solution**: Use test mode for testing:
```python
from app.database_config import get_database_config
config = get_database_config(is_test_mode=True)
```

### Issue: Custom path not working

**Cause**: Config not passed correctly

**Solution**: Verify config format matches the storage type:
```python
# For app.memory.LargeDataStorage
config = {
    "sqlite_path": "...",
    "file_path": "...",
    "compression": True
}

# For core.LargeDataStorage  
storage = LargeDataStorage(
    storage_path="...",
    file_storage_path="..."
)
```

## Best Practices

1. **Use Default Configuration**: Let components load from environment automatically
2. **Use Test Mode**: Always use `is_test_mode=True` for tests
3. **Set Environment Variables**: Define paths in `.env` file, not in code
4. **Don't Hardcode**: Avoid hardcoding database paths in your code
5. **Check Existence**: Directories are auto-created, but verify permissions
6. **Document Changes**: Update `.env.example` when adding new database paths

## Future Enhancements

Potential improvements for future versions:

- [ ] Configuration validation on startup
- [ ] Database migration support
- [ ] Automatic backup configuration
- [ ] Multi-environment profiles (dev/staging/prod)
- [ ] Configuration hot-reloading
- [ ] Database health checks

## Related Documentation

- [Large Data Storage System](../docs/LARGE_DATA_HANDLING_DEEP_DIVE.md)
- [ChromaDB Memory System](../docs/CHROMADB_MEMORY_COMPREHENSIVE_ANALYSIS.md)
- [MCP Server Configuration](../README_LARGE_DATA_MCP.md)

## Summary

The centralized database configuration system provides:
- **Single source of truth** for all database paths
- **Automatic loading** from environment variables
- **Test mode support** to avoid conflicts
- **Backward compatibility** with existing code
- **Easy maintenance** and debugging

Simply use `LargeDataStorage()` without any config, and paths will be loaded automatically from your `.env` file!
