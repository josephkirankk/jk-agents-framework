"""
Utility functions for VectorDB wrapper.

This module provides utility functions for common operations
like configuration loading, data validation, and response formatting.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from .models import SearchRequest, UpsertRequest, DefectData
from .exceptions import VectorDBValidationError


logger = logging.getLogger(__name__)


def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    
    Returns:
        Dictionary containing configuration values
    """
    config = {
        "base_url": os.getenv("VECTORDB_BASE_URL", "http://localhost:8010"),
        "timeout": float(os.getenv("VECTORDB_TIMEOUT", "30.0")),
        "max_retries": int(os.getenv("VECTORDB_MAX_RETRIES", "3")),
        "log_level": os.getenv("VECTORDB_LOG_LEVEL", "INFO"),
        "enable_logging": os.getenv("VECTORDB_ENABLE_LOGGING", "true").lower() == "true"
    }
    
    logger.debug(f"Loaded VectorDB configuration: {config}")
    return config


def validate_search_params(
    query: str,
    top_n: Optional[int] = None,
    min_score: Optional[float] = None
) -> SearchRequest:
    """
    Validate and create a SearchRequest from parameters.
    
    Args:
        query: Search query string
        top_n: Number of results to return
        min_score: Minimum similarity score
        
    Returns:
        Validated SearchRequest object
        
    Raises:
        VectorDBValidationError: If validation fails
    """
    try:
        params = {"query": query}
        
        if top_n is not None:
            params["top_n"] = top_n
            
        if min_score is not None:
            params["min_score"] = min_score
            
        return SearchRequest.model_validate(params)
        
    except Exception as e:
        raise VectorDBValidationError(f"Invalid search parameters: {str(e)}") from e


def validate_defect_data(data: Dict[str, Any]) -> DefectData:
    """
    Validate and create a DefectData object from dictionary.
    
    Args:
        data: Dictionary containing defect data
        
    Returns:
        Validated DefectData object
        
    Raises:
        VectorDBValidationError: If validation fails
    """
    try:
        return DefectData.model_validate(data)
    except Exception as e:
        raise VectorDBValidationError(f"Invalid defect data: {str(e)}") from e


def create_upsert_request(
    defect_code: str,
    defect_text: str,
    subsystem: str,
    **kwargs
) -> UpsertRequest:
    """
    Create an UpsertRequest with required and optional parameters.
    
    Args:
        defect_code: Unique defect identifier
        defect_text: Description of the defect
        subsystem: Subsystem code
        **kwargs: Additional optional parameters
        
    Returns:
        UpsertRequest object
        
    Raises:
        VectorDBValidationError: If validation fails
    """
    try:
        data = {
            "defect_code": defect_code,
            "defect_text": defect_text,
            "subsystem": subsystem,
            **kwargs
        }
        
        return UpsertRequest.model_validate(data)
        
    except Exception as e:
        raise VectorDBValidationError(f"Invalid upsert request: {str(e)}") from e


def format_search_results(results: List[Dict[str, Any]]) -> str:
    """
    Format search results for display.
    
    Args:
        results: List of search result dictionaries
        
    Returns:
        Formatted string representation of results
    """
    if not results:
        return "No results found."
    
    formatted = []
    for i, result in enumerate(results, 1):
        defect = result.get("defect", {})
        score = result.get("score", 0.0)
        
        formatted.append(f"""
Result {i}:
  Score: {score:.1%}
  Code: {defect.get('defect_code', 'N/A')}
  Text: {defect.get('defect_text', 'N/A')}
  Subsystem: {defect.get('subsystem', 'N/A')}
  Severity: {defect.get('severity', 'N/A')}
  Symptoms: {', '.join(defect.get('symptoms', []))}
  Tags: {', '.join(defect.get('tags', []))}
""".strip())
    
    return "\n\n".join(formatted)


def save_results_to_file(
    results: List[Dict[str, Any]], 
    filename: str,
    format_type: str = "json"
) -> Path:
    """
    Save search results to a file.
    
    Args:
        results: List of search result dictionaries
        filename: Output filename
        format_type: Output format ('json' or 'txt')
        
    Returns:
        Path to the saved file
        
    Raises:
        VectorDBValidationError: If format is unsupported
    """
    filepath = Path(filename)
    
    try:
        if format_type.lower() == "json":
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
                
        elif format_type.lower() == "txt":
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(format_search_results(results))
                
        else:
            raise VectorDBValidationError(f"Unsupported format: {format_type}")
        
        logger.info(f"Results saved to {filepath}")
        return filepath
        
    except Exception as e:
        raise VectorDBValidationError(f"Failed to save results: {str(e)}") from e


def setup_logging(log_level: str = "INFO") -> None:
    """
    Setup logging configuration for VectorDB wrapper.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Set specific logger levels
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    logger.info(f"VectorDB logging configured with level: {log_level}")


def get_client_info() -> Dict[str, str]:
    """
    Get information about the VectorDB client.

    Returns:
        Dictionary with client information
    """
    return {
        "name": "VectorDB Python Client",
        "version": "1.0.0",
        "description": "Python client for VectorDB API service",
        "base_url": os.getenv("VECTORDB_BASE_URL", "http://localhost:8010")
    }


async def upsert_json_defects(json_string: str, base_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to upsert defects from JSON string.

    This is a simple wrapper that creates a VectorDBClient and calls
    the upsert_json_defects method. Follows KISS principles.

    Args:
        json_string: JSON string containing defects array
        base_url: Optional base URL for VectorDB API

    Returns:
        Dictionary with summary of upsert operations

    Example:
        json_data = '{"defects": [{"defect_code": "TEST.001", ...}]}'
        result = await upsert_json_defects(json_data)
        print(f"Upserted {result['successful_upserts']} defects")
    """
    from .client import VectorDBClient

    async with VectorDBClient(base_url=base_url) as client:
        return await client.upsert_json_defects(json_string)


def upsert_json_defects_sync(json_string: str, base_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Synchronous wrapper for upsert_json_defects.

    This function runs the async upsert_json_defects in a new event loop,
    making it usable in synchronous code. Ultimate KISS principle.

    Args:
        json_string: JSON string containing defects array
        base_url: Optional base URL for VectorDB API

    Returns:
        Dictionary with summary of upsert operations

    Example:
        json_data = '{"defects": [{"defect_code": "TEST.001", ...}]}'
        result = upsert_json_defects_sync(json_data)
        print(f"Upserted {result['successful_upserts']} defects")
    """
    import asyncio

    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, we need to use a different approach
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    upsert_json_defects(json_string, base_url)
                )
                return future.result()
        else:
            # Loop exists but not running, we can use it
            return loop.run_until_complete(upsert_json_defects(json_string, base_url))
    except RuntimeError:
        # No event loop exists, create a new one
        return asyncio.run(upsert_json_defects(json_string, base_url))
