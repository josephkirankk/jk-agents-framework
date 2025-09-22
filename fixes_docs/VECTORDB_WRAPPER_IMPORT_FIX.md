# VectorDB Wrapper Import Fix

## Problem
When trying to run the `vectordb_wrapper/examples.py` file directly using:
```bash
python.exe .\vectordb_wrapper\examples.py
```

The following error occurred:
```
ImportError: attempted relative import with no known parent package
```

## Root Cause
The `examples.py` file was using relative imports (e.g., `from .client import VectorDBClient`), but when a Python file is run directly (not as a module), Python doesn't treat it as part of a package, causing relative imports to fail.

## Solution
Modified the `examples.py` file to handle both execution methods:

1. **As a module** (recommended): `python -m vectordb_wrapper.examples`
2. **Direct execution**: `python vectordb_wrapper/examples.py`

### Implementation
Added a try-except block that:
1. First attempts relative imports (when run as a module)
2. Falls back to absolute imports with path manipulation (when run directly)

```python
try:
    # Try relative imports first (when run as module)
    from .client import VectorDBClient
    from .models import SearchRequest, UpsertRequest
    from .decorators import vectordb_wrapper, log_vectordb_operations
    from .utils import format_search_results, setup_logging
except ImportError:
    # Fall back to absolute imports (when run directly)
    # Add parent directory to Python path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from vectordb_wrapper.client import VectorDBClient
    from vectordb_wrapper.models import SearchRequest, UpsertRequest
    from vectordb_wrapper.decorators import vectordb_wrapper, log_vectordb_operations
    from vectordb_wrapper.utils import format_search_results, setup_logging
```

## Usage
Both methods now work correctly:

### Method 1: Run as Module (Recommended)
```bash
python -m vectordb_wrapper.examples
```

### Method 2: Direct Execution
```bash
python vectordb_wrapper/examples.py
```

## Testing Results
Both execution methods successfully run all examples:
- Basic search example
- Basic upsert example
- Decorated search example
- Comprehensive example with health check, upsert, and search
- Error handling example

The VectorDB wrapper is connecting to `http://localhost:8010/` and all operations are working correctly.

## Files Modified
- `vectordb_wrapper/examples.py`: Added flexible import handling

## Date
2025-09-22
