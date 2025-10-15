"""
Test tool for storing large datasets to ChromaDB storage

This tool demonstrates how to explicitly store large data in the framework's
large data storage system, bypassing normal context limits.
"""

import json
import uuid
from typing import Dict, Any
from langchain_core.tools import tool
from app.memory.large_data_storage import LargeDataStorage

# Global storage instance (initialized by agent)
_storage_instance = None

def initialize_storage(storage_config: Dict[str, Any]):
    """Initialize the global storage instance"""
    global _storage_instance
    _storage_instance = LargeDataStorage(storage_config)
    return _storage_instance


@tool
def store_large_dataset_to_chromadb(dataset_json: str, description: str = "Large dataset") -> str:
    """
    Store a large dataset to ChromaDB/SQLite storage and return a reference.
    
    Args:
        dataset_json: JSON string of the dataset to store
        description: Description of the dataset
        
    Returns:
        JSON string with reference_id and storage info
    """
    global _storage_instance
    
    if _storage_instance is None:
        # Initialize with default config for testing
        _storage_instance = LargeDataStorage({
            "sqlite_path": "./integration_tests/temp/large_tool_data.db",
            "file_path": "./integration_tests/temp/large_tool_data_files/",
            "compression": True,
            "max_sqlite_size_mb": 50
        })
    
    try:
        # Parse the JSON to validate it
        data = json.loads(dataset_json)
        
        # Generate a reference ID
        reference_id = f"ref_{uuid.uuid4().hex[:12]}"
        
        # Store the data
        storage_info = _storage_instance.store_large_data(
            reference_id=reference_id,
            tool_name="store_large_dataset_to_chromadb",
            data=data,
            metadata={
                "description": description,
                "record_count": len(data) if isinstance(data, list) else None,
                "data_type": type(data).__name__
            }
        )
        
        # Return summary response
        result = {
            "status": "success",
            "reference_id": reference_id,
            "description": description,
            "size_mb": storage_info.size_mb,
            "size_bytes": storage_info.size_bytes,
            "storage_type": storage_info.storage_type,
            "record_count": len(data) if isinstance(data, list) else None,
            "message": f"✅ Dataset stored successfully! Reference ID: {reference_id}"
        }
        
        return json.dumps(result, indent=2)
        
    except json.JSONDecodeError as e:
        return json.dumps({
            "status": "error",
            "error": f"Invalid JSON: {str(e)}"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"Storage failed: {str(e)}"
        }, indent=2)


@tool
def retrieve_dataset_from_chromadb(reference_id: str) -> str:
    """
    Retrieve a previously stored dataset from ChromaDB storage.
    
    Args:
        reference_id: The reference ID returned when storing the dataset
        
    Returns:
        JSON string of the retrieved dataset
    """
    global _storage_instance
    
    if _storage_instance is None:
        return json.dumps({
            "status": "error",
            "error": "Storage not initialized"
        })
    
    try:
        data = _storage_instance.retrieve_large_data(reference_id)
        
        if data is None:
            return json.dumps({
                "status": "error",
                "error": f"No data found for reference {reference_id}"
            })
        
        return json.dumps({
            "status": "success",
            "reference_id": reference_id,
            "data": data
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"Retrieval failed: {str(e)}"
        }, indent=2)
