#!/usr/bin/env python3
"""
MCP Server for Large Data Handling

Provides tools for storing and retrieving large datasets efficiently:
1. Store large datasets in database-backed storage (SQLite + file system)
2. Retrieve datasets by reference ID
3. List stored datasets
4. Get storage statistics
5. Automatic cleanup of expired data

This prevents flooding the LLM context with large datasets by storing them
in the database and returning only references and previews.
"""

import asyncio
import json
import logging
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
    Resource,
    Tool,
    TextContent,
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
logger = logging.getLogger("large_data_server")

# Initialize the MCP server
server = Server("large-data-storage")

# Global storage instance
storage: Optional[LargeDataStorage] = None

def initialize_storage(config: Optional[Dict[str, Any]] = None):
    """Initialize the large data storage system"""
    global storage
    
    if config is None:
        # Use centralized database configuration from environment
        # LargeDataStorage will automatically load from database_config module
        storage = LargeDataStorage()
        logger.info("Large data storage initialized with centralized config")
    else:
        # Use provided config
        storage = LargeDataStorage(config)
        logger.info(f"Large data storage initialized with custom config: {config}")

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


@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available large data storage resources."""
    return [
        Resource(
            uri="storage://stats",
            name="Storage Statistics",
            description="Get comprehensive statistics about large data storage usage",
            mimeType="application/json",
        ),
        Resource(
            uri="storage://references",
            name="Stored References",
            description="List all stored data references with metadata",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read large data storage resources."""
    global storage
    
    if storage is None:
        initialize_storage()
    
    if uri == "storage://stats":
        stats = storage.get_storage_stats()
        return json.dumps(stats, indent=2)
    
    elif uri == "storage://references":
        references = storage.list_references(limit=100)
        return json.dumps(references, indent=2, default=str)
    
    else:
        raise ValueError(f"Unknown resource URI: {uri}")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available large data storage tools."""
    return [
        Tool(
            name="store_large_dataset",
            description="Store a large dataset in database-backed storage and return a reference ID. "
                       "Use this to avoid flooding the LLM context with large data. "
                       "Returns a preview (first 5 records), total count, and reference ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset": {
                        "type": "string",
                        "description": "JSON string of the dataset to store (array or object)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the dataset for future reference"
                    },
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the tool that generated this data (optional)",
                        "default": "manual_storage"
                    }
                },
                "required": ["dataset", "description"],
            },
        ),
        Tool(
            name="retrieve_large_dataset",
            description="Retrieve a previously stored dataset using its reference ID. "
                       "Returns the complete dataset. Use sparingly to avoid context overflow.",
            inputSchema={
                "type": "object",
                "properties": {
                    "reference_id": {
                        "type": "string",
                        "description": "The reference ID returned when storing the dataset"
                    }
                },
                "required": ["reference_id"],
            },
        ),
        Tool(
            name="get_dataset_preview",
            description="Get a preview of a stored dataset without retrieving the full data. "
                       "Returns metadata, size info, and a sample of the data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "reference_id": {
                        "type": "string",
                        "description": "The reference ID of the dataset"
                    },
                    "sample_size": {
                        "type": "integer",
                        "description": "Number of sample records to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["reference_id"],
            },
        ),
        Tool(
            name="list_stored_datasets",
            description="List all stored datasets with their metadata and reference IDs",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of datasets to return (default: 50)",
                        "default": 50
                    }
                },
            },
        ),
        Tool(
            name="get_storage_statistics",
            description="Get comprehensive statistics about storage usage, including total size, "
                       "number of datasets, and storage breakdown by type",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="cleanup_expired_datasets",
            description="Clean up expired datasets to free storage space. "
                       "Datasets expire after 48 hours by default.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution requests."""
    global storage
    
    if storage is None:
        initialize_storage()
    
    try:
        if name == "store_large_dataset":
            return await store_large_dataset(arguments)
        elif name == "retrieve_large_dataset":
            return await retrieve_large_dataset(arguments)
        elif name == "get_dataset_preview":
            return await get_dataset_preview(arguments)
        elif name == "list_stored_datasets":
            return await list_stored_datasets(arguments)
        elif name == "get_storage_statistics":
            return await get_storage_statistics(arguments)
        elif name == "cleanup_expired_datasets":
            return await cleanup_expired_datasets(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        error_response = {
            "status": "error",
            "error": str(e),
            "tool": name
        }
        return [TextContent(type="text", text=json.dumps(error_response, indent=2))]


async def store_large_dataset(arguments: dict) -> list[TextContent]:
    """Store a large dataset and return preview + reference ID"""
    global storage
    
    dataset_json = arguments.get("dataset", "")
    description = arguments.get("description", "")
    tool_name = arguments.get("tool_name", "manual_storage")
    
    try:
        # Parse the dataset
        dataset = json.loads(dataset_json)
        
        # Generate reference ID
        reference_id = f"ref_{uuid.uuid4().hex[:12]}"
        
        # Store the dataset
        storage_info = storage.store_large_data(
            reference_id=reference_id,
            tool_name=tool_name,
            data=dataset,
            metadata={
                "description": description,
                "record_count": len(dataset) if isinstance(dataset, list) else None,
                "data_type": type(dataset).__name__,
                "stored_at": datetime.now().isoformat()
            }
        )
        
        # Create preview
        if isinstance(dataset, list):
            preview = dataset[:5]
            total_count = len(dataset)
        elif isinstance(dataset, dict):
            preview = {k: dataset[k] for k in list(dataset.keys())[:5]}
            total_count = len(dataset)
        else:
            preview = str(dataset)[:500]
            total_count = 1
        
        # Return summary response
        result = {
            "status": "success",
            "reference_id": reference_id,
            "description": description,
            "preview": preview,
            "total_count": total_count,
            "size_mb": round(storage_info.size_mb, 2),
            "size_bytes": storage_info.size_bytes,
            "storage_type": storage_info.storage_type,
            "compressed": storage_info.compressed,
            "message": f"✅ Dataset stored successfully! Use reference_id '{reference_id}' to retrieve it later."
        }
        
        logger.info(f"Stored dataset {reference_id}: {total_count} records, {storage_info.size_mb:.2f}MB")

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except json.JSONDecodeError as e:
        error_response = {
            "status": "error",
            "error": f"Invalid JSON: {str(e)}"
        }
        return [TextContent(type="text", text=json.dumps(error_response, indent=2))]


async def retrieve_large_dataset(arguments: dict) -> list[TextContent]:
    """Retrieve a complete dataset by reference ID"""
    global storage

    reference_id = arguments.get("reference_id", "")

    if not reference_id:
        error_response = {
            "status": "error",
            "error": "reference_id is required"
        }
        return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

    data = storage.retrieve_large_data(reference_id)

    if data is None:
        error_response = {
            "status": "error",
            "error": f"No dataset found for reference_id: {reference_id}"
        }
        return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

    result = {
        "status": "success",
        "reference_id": reference_id,
        "data": data
    }

    logger.info(f"Retrieved dataset {reference_id}")

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def get_dataset_preview(arguments: dict) -> list[TextContent]:
    """Get a preview of a dataset without retrieving full data"""
    global storage

    reference_id = arguments.get("reference_id", "")
    sample_size = arguments.get("sample_size", 5)

    if not reference_id:
        error_response = {
            "status": "error",
            "error": "reference_id is required"
        }
        return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

    # Get metadata from storage
    cursor = storage.conn.execute("""
        SELECT tool_name, size_bytes, size_category, storage_type,
               content_type, compressed, metadata, created_at, access_count
        FROM large_tool_data
        WHERE reference_id = ?
    """, (reference_id,))

    row = cursor.fetchone()
    if not row:
        error_response = {
            "status": "error",
            "error": f"No dataset found for reference_id: {reference_id}"
        }
        return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

    tool_name, size_bytes, size_category, storage_type, content_type, compressed, metadata_json, created_at, access_count = row
    metadata = json.loads(metadata_json)

    # Retrieve data for preview
    data = storage.retrieve_large_data(reference_id)

    # Create preview
    if isinstance(data, list):
        preview = data[:sample_size]
        total_count = len(data)
    elif isinstance(data, dict):
        preview = {k: data[k] for k in list(data.keys())[:sample_size]}
        total_count = len(data)
    else:
        preview = str(data)[:500]
        total_count = 1

    result = {
        "status": "success",
        "reference_id": reference_id,
        "metadata": {
            "description": metadata.get("description", ""),
            "tool_name": tool_name,
            "size_mb": round(size_bytes / (1024 * 1024), 2),
            "size_bytes": size_bytes,
            "size_category": size_category,
            "storage_type": storage_type,
            "content_type": content_type,
            "compressed": bool(compressed),
            "created_at": created_at,
            "access_count": access_count,
            "record_count": metadata.get("record_count")
        },
        "preview": preview,
        "total_count": total_count,
        "sample_size": sample_size
    }

    logger.info(f"Retrieved preview for dataset {reference_id}")

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def list_stored_datasets(arguments: dict) -> list[TextContent]:
    """List all stored datasets"""
    global storage

    limit = arguments.get("limit", 50)

    references = storage.list_references(limit=limit)

    result = {
        "status": "success",
        "total_datasets": len(references),
        "datasets": references
    }

    logger.info(f"Listed {len(references)} datasets")

    return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]


async def get_storage_statistics(arguments: dict) -> list[TextContent]:
    """Get comprehensive storage statistics"""
    global storage

    stats = storage.get_storage_stats()

    result = {
        "status": "success",
        "statistics": stats
    }

    logger.info("Retrieved storage statistics")

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def cleanup_expired_datasets(arguments: dict) -> list[TextContent]:
    """Clean up expired datasets"""
    global storage

    cleanup_result = storage.cleanup_expired_data()

    result = {
        "status": "success",
        "cleaned_records": cleanup_result["cleaned_records"],
        "cleaned_files": cleanup_result["cleaned_files"],
        "message": f"✅ Cleaned up {cleanup_result['cleaned_records']} expired datasets"
    }

    logger.info(f"Cleaned up {cleanup_result['cleaned_records']} expired datasets")

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def main():
    """Run the MCP server using stdin/stdout streams"""
    # Initialize storage with default config
    initialize_storage()

    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="large-data-storage",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
