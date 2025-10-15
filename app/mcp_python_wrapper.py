#!/usr/bin/env python3
"""
MCP Python Wrapper with Auto-Storage Post-Processor

This wrapper intercepts run_python_code results and automatically stores
large datasets in the database, returning only previews to the LLM.

Architecture:
1. Wraps the Deno-based python_runner MCP server
2. Intercepts run_python_code tool results
3. Detects large JSON arrays/objects in the output
4. Automatically stores them in large_data_storage
5. Returns preview + reference ID instead of full data
"""

import asyncio
import json
import logging
import re
import sys
import uuid
import atexit
import signal
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

# MCP imports
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
)

# Import large data storage system
try:
    from app.memory.large_data_storage import LargeDataStorage
except ImportError:
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from app.memory.large_data_storage import LargeDataStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("python_wrapper")

# Add file handler for debugging
try:
    from pathlib import Path
    log_dir = Path("agentlogs/mcp_server_logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "python_wrapper.log")
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
except Exception as e:
    print(f"Warning: Could not set up file logging: {e}", file=sys.stderr)

# Initialize the MCP server
server = Server("python-wrapper-with-storage")

# Global variable to store the last retrieved dataset for automatic injection
_last_retrieved_dataset = None
_last_retrieved_reference_id = None

# Global storage instance
storage: Optional[LargeDataStorage] = None

def initialize_storage(config: Optional[Dict[str, Any]] = None):
    """Initialize the large data storage system"""
    global storage
    
    if config is None:
        # Use centralized database configuration from environment
        # LargeDataStorage will automatically load from database_config module
        storage = LargeDataStorage()
        logger.info("Python wrapper storage initialized with centralized config")
    else:
        # Use provided config
        storage = LargeDataStorage(config)
        logger.info(f"Python wrapper storage initialized with custom config: {config}")

    # Register cleanup handler to ensure data is persisted on exit
    def cleanup_storage():
        """Ensure database is flushed before process exit"""
        if storage and hasattr(storage, 'conn') and storage.conn:
            try:
                logger.info("Flushing database before exit...")
                storage.conn.execute("PRAGMA wal_checkpoint(FULL)")
                storage.conn.commit()
                storage.conn.close()
                logger.info("Database flushed successfully")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")

    atexit.register(cleanup_storage)

    # Handle SIGTERM gracefully
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, cleaning up...")
        cleanup_storage()
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    return storage


def extract_json_from_text(text: str) -> Optional[Any]:
    """
    Extract JSON data from Python execution result.
    Handles various formats:
    - Direct JSON array/object
    - JSON embedded in text
    - Python repr format
    """
    if not text or not isinstance(text, str):
        return None
    
    text = text.strip()
    
    # Try direct JSON parse first
    try:
        data = json.loads(text)
        # Only consider lists with multiple items or dicts as "large data"
        if isinstance(data, list) and len(data) > 5:
            return data
        elif isinstance(data, dict) and len(data) > 5:
            return data
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON in the text using regex
    # Look for arrays or objects
    patterns = [
        r'(\[[\s\S]*\])',  # Array
        r'(\{[\s\S]*\})',  # Object
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                data = json.loads(match.group(1))
                if isinstance(data, list) and len(data) > 5:
                    return data
                elif isinstance(data, dict) and len(data) > 5:
                    return data
            except json.JSONDecodeError:
                continue
    
    return None


def create_preview_response(dataset: Any, reference_id: str, description: str = "Generated dataset") -> str:
    """
    Create a TOKEN-OPTIMIZED preview response with reference ID.
    
    Token Optimization Strategy:
    - Only 2 items in preview (not 5) - saves ~60% tokens
    - Truncate individual items to 200 chars
    - Include summary stats instead of full data
    - Clear instructions for retrieval
    """
    if isinstance(dataset, list):
        # TOKEN OPTIMIZATION: Only show first 2 items, truncate each
        preview_items = []
        for item in dataset[:2]:
            item_str = json.dumps(item) if isinstance(item, (dict, list)) else str(item)
            if len(item_str) > 200:
                item_str = item_str[:197] + "..."
            preview_items.append(item_str)
        
        total_count = len(dataset)
        preview_type = "array"
        
        # Add smart summary
        if dataset and isinstance(dataset[0], dict):
            sample_keys = list(dataset[0].keys())[:10]
            schema_hint = f"Record schema: {sample_keys}"
        else:
            schema_hint = f"Item type: {type(dataset[0]).__name__ if dataset else 'unknown'}"
        
    elif isinstance(dataset, dict):
        # TOKEN OPTIMIZATION: Only show first 2 keys, truncate values
        preview_items = {}
        for i, (k, v) in enumerate(dataset.items()):
            if i >= 2:
                break
            v_str = json.dumps(v) if isinstance(v, (dict, list)) else str(v)
            if len(v_str) > 200:
                v_str = v_str[:197] + "..."
            preview_items[k] = v_str
        
        total_count = len(dataset)
        preview_type = "object"
        schema_hint = f"Keys ({len(dataset)} total)"
    else:
        preview_items = str(dataset)[:200]
        total_count = 1
        preview_type = "unknown"
        schema_hint = f"Type: {type(dataset).__name__}"
    
    # TOKEN-OPTIMIZED RESPONSE: Minimal, essential information only
    response = {
        "status": "stored",
        "reference_id": reference_id,
        "total_count": total_count,
        "type": preview_type,
        "preview": preview_items,
        "schema": schema_hint,
        "note": f"Full dataset stored. Use reference ID to retrieve."
    }
    
    return json.dumps(response, indent=2)


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools - just run_python_code for now"""
    return [
        Tool(
            name="run_python_code",
            description=(
                "Execute Python code with automatic large dataset storage and retrieval. "
                "If the code returns a large JSON array or object (>5 items), "
                "it will be automatically stored in the database and you'll receive "
                "a preview + reference ID instead of the full data. "
                "You can also provide a dataset_reference_id to automatically load "
                "a previously stored dataset into the 'data' variable before execution."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "python_code": {
                        "type": "string",
                        "description": "Python code to execute. If it returns a large dataset, it will be auto-stored."
                    },
                    "dataset_reference_id": {
                        "type": "string",
                        "description": "Optional: Reference ID of a dataset to load into the 'data' variable before execution (format: ref_xxxxxxxxxxxx)"
                    }
                },
                "required": ["python_code"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Handle tool execution with post-processing.
    
    This intercepts run_python_code results and automatically stores large datasets.
    """
    global storage
    
    if storage is None:
        initialize_storage()
    
    if name != "run_python_code":
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"Unknown tool: {name}"})
        )]
    
    python_code = arguments.get("python_code", "")
    dataset_reference_id = arguments.get("dataset_reference_id", None)

    # INSTRUMENTATION: Log all parameters received
    logger.info(f"=== run_python_code called ===")
    logger.info(f"  - python_code length: {len(python_code)} chars")
    logger.info(f"  - dataset_reference_id: {dataset_reference_id if dataset_reference_id else 'NOT PROVIDED'}")

    if not python_code:
        return [TextContent(
            type="text",
            text=json.dumps({"error": "No python_code provided"})
        )]

    # SMART AUTO-CORRECTION: Use AST-based analysis (no hardcoded variables)
    # Token-optimized, dynamic detection of dataset variables and anti-patterns
    logger.info(f"🔧 Smart code analysis...")
    try:
        from app.smart_code_analyzer import smart_auto_correct, get_analysis_stats
        
        # Get quick stats (token-optimized)
        stats = get_analysis_stats(python_code)
        logger.info(f"   Last line: {stats['last_line_preview']}")
        
        # Apply smart auto-correction
        corrected_code, was_fixed, fix_description = smart_auto_correct(python_code)
        
        if was_fixed:
            logger.warning(f"⚠️  {fix_description}")
            logger.info(f"✅ Auto-corrected: result = {stats['detected_dataset_var']}")
            python_code = corrected_code
        else:
            logger.info(f"   ✓ Code OK (detected var: {stats['detected_dataset_var']})")
    except Exception as e:
        logger.warning(f"   Smart analysis failed, skipping: {e}")

    try:
        # Retrieve dataset if reference ID is provided
        retrieved_data = None
        if dataset_reference_id:
            logger.info(f"🔍 Retrieving dataset {dataset_reference_id} for Python execution...")
            logger.info(f"   Using database: {storage.db_path}")
            try:
                import time
                t0 = time.perf_counter()
                retrieved_data = storage.retrieve_large_data(dataset_reference_id)
                retrieval_time = time.perf_counter() - t0

                # INSTRUMENTATION: Detailed retrieval info
                if isinstance(retrieved_data, list):
                    data_size = len(retrieved_data)
                    logger.info(f"✅ Successfully retrieved dataset {dataset_reference_id}")
                    logger.info(f"   - Type: list")
                    logger.info(f"   - Size: {data_size} items")
                    logger.info(f"   - Retrieval time: {retrieval_time:.3f}s")
                elif isinstance(retrieved_data, dict):
                    data_size = len(retrieved_data)
                    logger.info(f"✅ Successfully retrieved dataset {dataset_reference_id}")
                    logger.info(f"   - Type: dict")
                    logger.info(f"   - Size: {data_size} keys")
                    logger.info(f"   - Retrieval time: {retrieval_time:.3f}s")
                else:
                    logger.info(f"✅ Successfully retrieved dataset {dataset_reference_id}")
                    logger.info(f"   - Type: {type(retrieved_data).__name__}")
                    logger.info(f"   - Retrieval time: {retrieval_time:.3f}s")
            except Exception as e:
                logger.error(f"❌ Failed to retrieve dataset {dataset_reference_id}: {e}")
                logger.error(f"   Error type: {type(e).__name__}")
                import traceback
                logger.error(f"   Traceback: {traceback.format_exc()}")
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": f"Failed to retrieve dataset {dataset_reference_id}: {str(e)}"})
                )]
        else:
            logger.info(f"ℹ️  No dataset_reference_id provided - executing code without pre-loaded data")

        # Execute Python code directly in a restricted environment
        logger.info(f"⚙️  Executing Python code (length: {len(python_code)} chars)...")

        # Create a restricted globals dict for safety
        # Convert __builtins__ to dict if it's a module
        import builtins
        builtins_dict = builtins.__dict__ if hasattr(builtins, '__dict__') else builtins

        # Try to import pandas and numpy if available
        try:
            import pandas as pd
            import numpy as np
            pandas_available = True
            logger.info("pandas and numpy are available for Python execution")
        except ImportError:
            pd = None
            np = None
            pandas_available = False
            logger.warning("pandas/numpy not available - using standard library only")

        # Try to import jsonschema for validation
        try:
            import jsonschema
            jsonschema_available = True
            logger.info("jsonschema is available for Python execution")
        except ImportError:
            jsonschema = None
            jsonschema_available = False
            logger.warning("jsonschema not available - validation will not work")

        # Try to import faker for data generation
        try:
            from faker import Faker
            faker_available = True
            logger.info("faker is available for Python execution")
        except ImportError:
            Faker = None
            faker_available = False
            logger.warning("faker not available - realistic data generation may be limited")

        restricted_globals = {
            "__builtins__": builtins_dict,
            "json": json,
            "datetime": __import__("datetime"),
            "random": __import__("random"),
            "uuid": __import__("uuid"),
            "re": __import__("re"),
            "string": __import__("string"),
            "statistics": __import__("statistics"),
            "collections": __import__("collections"),
        }

        # Add pandas and numpy if available
        if pandas_available:
            restricted_globals["pd"] = pd
            restricted_globals["pandas"] = pd
            restricted_globals["np"] = np
            restricted_globals["numpy"] = np

        # Add jsonschema if available
        if jsonschema_available:
            restricted_globals["jsonschema"] = jsonschema

        # Add Faker if available
        if faker_available:
            restricted_globals["Faker"] = Faker

        # Inject retrieved dataset if available
        if retrieved_data is not None:
            restricted_globals["data"] = retrieved_data
            # INSTRUMENTATION: Detailed injection logging
            if isinstance(retrieved_data, list):
                logger.info(f"✅ Injected retrieved dataset into 'data' variable")
                logger.info(f"   - Variable name: 'data'")
                logger.info(f"   - Type: list")
                logger.info(f"   - Size: {len(retrieved_data)} items")
                logger.info(f"   - First item preview: {str(retrieved_data[0])[:100] if retrieved_data else 'N/A'}")
            elif isinstance(retrieved_data, dict):
                logger.info(f"✅ Injected retrieved dataset into 'data' variable")
                logger.info(f"   - Variable name: 'data'")
                logger.info(f"   - Type: dict")
                logger.info(f"   - Size: {len(retrieved_data)} keys")
            else:
                logger.info(f"✅ Injected retrieved dataset into 'data' variable ({type(retrieved_data).__name__})")
        else:
            logger.info(f"ℹ️  No data to inject - 'data' variable will not be available")
        
        # CRITICAL: Inject reference_id into execution context for validation output
        if dataset_reference_id:
            restricted_globals["reference_id"] = dataset_reference_id
            logger.info(f"✅ Injected reference_id into execution context: {dataset_reference_id}")

        # Execute the code and capture the result
        # We need to handle both assignment and expression evaluation
        # CRITICAL FIX: Use same dict for globals and locals to allow functions to call each other
        # When exec() has separate globals/locals, functions defined in code cannot call each other
        exec_namespace = dict(restricted_globals)  # Copy to avoid modifying original

        # Try to compile and execute
        import time
        exec_start = time.perf_counter()
        try:
            # First, try to compile as an expression (single value)
            code_obj = compile(python_code, '<string>', 'eval')
            dataset = eval(code_obj, exec_namespace, exec_namespace)
        except SyntaxError:
            # If that fails, it's a statement (assignments, loops, etc.)
            # Use same dict for both globals and locals so functions can call each other
            exec(python_code, exec_namespace, exec_namespace)

            # Get the result - look for common return patterns
            dataset = None

            # Check if there's a specific variable we should return
            if "result" in exec_namespace:
                dataset = exec_namespace["result"]
            elif "records" in exec_namespace:  # Common for data generation
                dataset = exec_namespace["records"]
            elif "all_records" in exec_namespace:  # Common for data generation
                dataset = exec_namespace["all_records"]
            elif "data" in exec_namespace and exec_namespace["data"] != retrieved_data:
                # Only use 'data' if it's not the injected dataset
                dataset = exec_namespace["data"]
            elif "output" in exec_namespace:
                dataset = exec_namespace["output"]
            elif "orders" in exec_namespace:
                dataset = exec_namespace["orders"]
            elif "products" in exec_namespace:
                dataset = exec_namespace["products"]
            elif "customers" in exec_namespace:
                dataset = exec_namespace["customers"]
            else:
                # Get the last non-None, non-module, non-function value
                for key, value in reversed(list(exec_namespace.items())):
                    # Skip if it's None, starts with _, is a module, or is a function
                    if value is None or key.startswith("_"):
                        continue
                    if hasattr(value, '__module__') or callable(value):
                        continue
                    # Skip if it's one of our injected modules
                    if key in ['json', 'datetime', 'random', 'uuid', 're', 'string', 'statistics', 
                               'collections', 'pd', 'pandas', 'np', 'numpy', 'jsonschema', 'Faker']:
                        continue
                    dataset = value
                    break

        exec_time = time.perf_counter() - exec_start
        logger.info(f"✅ Python execution completed in {exec_time:.3f}s")
        logger.info(f"   - Result type: {type(dataset).__name__}")
        if isinstance(dataset, (list, dict)):
            logger.info(f"   - Result size: {len(dataset)} items")

        # SAFETY: Convert pandas DataFrame to dict if returned
        try:
            import pandas as pd
            if isinstance(dataset, pd.DataFrame):
                logger.info(f"⚠️  DataFrame detected - converting to dict (shape: {dataset.shape})")
                dataset = dataset.to_dict('records')
            elif isinstance(dataset, pd.Series):
                logger.info(f"⚠️  Series detected - converting to list (length: {len(dataset)})")
                dataset = dataset.to_list()
        except ImportError:
            pass  # pandas not available, skip conversion

        # Check if dataset is large enough to store
        should_store = False
        if isinstance(dataset, list) and len(dataset) > 5:
            should_store = True
        elif isinstance(dataset, dict) and len(dataset) > 5:
            should_store = True

        if not should_store:
            # Small dataset or no dataset - return as-is
            logger.info("Small dataset or no dataset, returning original output")
            result_text = json.dumps(dataset) if dataset is not None else "No output"
            return [TextContent(type="text", text=result_text)]

        # Large dataset detected - store it automatically
        logger.info(f"Large dataset detected: {len(dataset)} items")

        # Generate reference ID
        reference_id = f"ref_{uuid.uuid4().hex[:12]}"

        # Store the dataset
        _ = storage.store_large_data(
            reference_id=reference_id,
            tool_name="run_python_code",
            data=dataset,
            metadata={
                "description": "Auto-stored from Python execution",
                "record_count": len(dataset) if isinstance(dataset, list) else len(dataset) if isinstance(dataset, dict) else None,
                "data_type": type(dataset).__name__,
                "stored_at": datetime.now().isoformat(),
                "auto_stored": True
            }
        )

        logger.info(f"Dataset stored with reference ID: {reference_id}")

        # Create and return preview response
        preview_response = create_preview_response(dataset, reference_id)

        return [TextContent(type="text", text=preview_response)]

    except Exception as e:
        logger.error(f"Error in Python wrapper: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"Wrapper error: {str(e)}"})
        )]


async def main():
    """Run the MCP wrapper server using stdin/stdout streams"""
    # Log environment variables for debugging
    import os
    logger.info("=" * 80)
    logger.info("Python Wrapper MCP Server Starting")
    logger.info(f"LARGE_DATA_DB_PATH env var: {os.getenv('LARGE_DATA_DB_PATH', 'NOT SET')}")
    logger.info(f"LARGE_DATA_FILES_PATH env var: {os.getenv('LARGE_DATA_FILES_PATH', 'NOT SET')}")
    logger.info("=" * 80)
    
    # Initialize storage with default config
    initialize_storage()
    
    # Log actual storage paths
    if storage:
        logger.info(f"Storage initialized:")
        logger.info(f"  Database path: {storage.db_path}")
        logger.info(f"  Files path: {storage.file_storage_path}")
    
    logger.info("Starting Python Wrapper MCP Server with auto-storage...")

    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="python-wrapper-with-storage",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())

