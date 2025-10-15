"""
File Retrieval Tools for Agents

Provides 4 distinct tools for file management:
1. get_file_metadata - Get metadata only (no content)
2. get_file_content - Get text file content  
3. get_image_base64 - Get image as base64 (for vision models)
4. list_available_files - List all files in thread

IMPORTANT: Tools return minimal data to avoid bloating LangGraph message history.
Image base64 content should only be retrieved when needed for vision processing.
"""
import base64
import logging
from typing import Dict, List, Optional, Any
from langchain_core.tools import tool

log = logging.getLogger(__name__)


@tool
def get_file_metadata(reference_id: str) -> Dict[str, Any]:
    """
    Get file metadata without retrieving actual content.
    Use this first to check file type before retrieving content.
    
    Args:
        reference_id: The unique file reference ID (e.g., "file_abc123def456")
        
    Returns:
        Dictionary containing:
        - success: bool - Whether the file was found
        - reference_id: str - The reference ID
        - filename: str - Original filename
        - mime_type: str - MIME type
        - size_bytes: int - File size in bytes
        - is_image: bool - Whether it's an image
        - is_text: bool - Whether it's a text file
        - compression: dict - Compression info if available
        
    Example:
        >>> meta = get_file_metadata("file_abc123")
        >>> if meta["is_image"]:
        ...     # Use get_image_base64() to get the image
        >>> elif meta["is_text"]:
        ...     # Use get_file_content() to get the text
    """
    try:
        from app.file_storage_manager import get_file_storage_manager
        
        manager = get_file_storage_manager()
        metadata = manager.get_file_metadata(reference_id)
        
        if not metadata:
            return {
                "success": False,
                "reference_id": reference_id,
                "error": f"File not found: {reference_id}"
            }
        
        log.info(f"Retrieved metadata for {reference_id} ({metadata['filename']})")
        
        return {
            "success": True,
            **metadata
        }
        
    except Exception as e:
        log.error(f"Error retrieving metadata for {reference_id}: {e}")
        return {
            "success": False,
            "reference_id": reference_id,
            "error": str(e)
        }


@tool
def get_file_content(reference_id: str) -> Dict[str, Any]:
    """
    Get text file content by reference ID.
    Only use this for text files (not images).
    
    Args:
        reference_id: The unique file reference ID
        
    Returns:
        Dictionary containing:
        - success: bool
        - reference_id: str
        - filename: str
        - content: str - The text content
        - error: str - If failed
        
    Example:
        >>> result = get_file_content("file_abc123")
        >>> if result["success"]:
        ...     print(result["content"])
    """
    try:
        from app.file_storage_manager import get_file_storage_manager
        
        manager = get_file_storage_manager()
        
        # Get metadata first to check if it's a text file
        metadata = manager.get_file_metadata(reference_id)
        if not metadata:
            return {
                "success": False,
                "reference_id": reference_id,
                "error": f"File not found: {reference_id}"
            }
        
        if not metadata["is_text"]:
            return {
                "success": False,
                "reference_id": reference_id,
                "error": f"File {metadata['filename']} is not a text file. Use get_image_base64() for images."
            }
        
        # Get raw content
        content_bytes = manager.get_file_content_raw(reference_id)
        if content_bytes is None:
            return {
                "success": False,
                "reference_id": reference_id,
                "error": "Failed to retrieve file content"
            }
        
        try:
            content = content_bytes.decode('utf-8', errors='ignore')
        except Exception as e:
            content = f"Error decoding text: {e}"
        
        return {
            "success": True,
            "reference_id": reference_id,
            "filename": metadata["filename"],
            "content": content
        }
        
    except Exception as e:
        log.error(f"Error retrieving file content for {reference_id}: {e}")
        return {
            "success": False,
            "reference_id": reference_id,
            "error": str(e)
        }


@tool
def get_image_base64(reference_id: str) -> Dict[str, Any]:
    """
    Get image file as base64 string for vision model processing.
    Only use this when you need to analyze an image with vision capabilities.
    
    WARNING: This returns large base64 data. Only call when absolutely necessary.
    The result will be used for vision processing and then removed from history.
    
    Args:
        reference_id: The unique file reference ID
        
    Returns:
        Dictionary containing:
        - success: bool
        - reference_id: str
        - filename: str  
        - base64_content: str - The base64-encoded image
        - mime_type: str
        - size_bytes: int
        - error: str - If failed
        
    Example:
        >>> result = get_image_base64("file_abc123")
        >>> if result["success"]:
        ...     # Process image with vision model
        ...     analyze_image(result["base64_content"])
    """
    try:
        from app.file_storage_manager import get_file_storage_manager
        
        manager = get_file_storage_manager()
        
        # Get metadata first to check if it's an image
        metadata = manager.get_file_metadata(reference_id)
        if not metadata:
            return {
                "success": False,
                "reference_id": reference_id,
                "error": f"File not found: {reference_id}"
            }
        
        if not metadata["is_image"]:
            return {
                "success": False,
                "reference_id": reference_id,
                "error": f"File {metadata['filename']} is not an image. Use get_file_content() for text files."
            }
        
        # Get base64 content
        base64_content = manager.get_file_content_base64(reference_id)
        if base64_content is None:
            return {
                "success": False,
                "reference_id": reference_id,
                "error": "Failed to retrieve image content"
            }
        
        return {
            "success": True,
            "reference_id": reference_id,
            "filename": metadata["filename"],
            "base64_content": base64_content,
            "mime_type": metadata["mime_type"],
            "size_bytes": metadata["size_bytes"]
        }
        
    except Exception as e:
        log.error(f"Error retrieving image base64 for {reference_id}: {e}")
        return {
            "success": False,
            "reference_id": reference_id,
            "error": str(e)
        }


@tool
def list_available_files() -> Dict[str, Any]:
    """
    List all files available in the current thread context.
    
    This tool shows metadata about uploaded files without retrieving their content.
    Use this to see what files are available before calling get_file_content().
    The thread_id is automatically extracted from the LangGraph execution context.
        
    Returns:
        Dictionary containing:
        - success: bool
        - files: list - List of file metadata dicts
        - count: int - Number of files
        - total_size_bytes: int - Total size of all files
        
    Example:
        >>> result = list_available_files()
        >>> for file in result["files"]:
        ...     print(f"{file['filename']}: {file['reference_id']}")
    """
    try:
        from app.file_storage_manager import get_file_storage_manager
        from langgraph.checkpoint.base import empty_checkpoint
        from langchain_core.runnables import RunnableConfig
        import inspect
        
        # Try to extract thread_id from the execution context
        thread_id = None
        
        # Method 1: Check if we're in a LangGraph context by inspecting the call stack
        for frame_info in inspect.stack():
            frame = frame_info.frame
            # Look for 'config' in local variables
            if 'config' in frame.f_locals:
                config = frame.f_locals['config']
                if isinstance(config, dict) and 'configurable' in config:
                    thread_id = config['configurable'].get('thread_id')
                    if thread_id:
                        break
                elif hasattr(config, 'get'):
                    configurable = config.get('configurable', {})
                    if isinstance(configurable, dict):
                        thread_id = configurable.get('thread_id')
                        if thread_id:
                            break
        
        if not thread_id:
            # Fallback: list all files (not ideal but prevents complete failure)
            log.warning("thread_id not found in execution context, returning all files")
            manager = get_file_storage_manager()
            # Get all files from all threads
            all_files = []
            for tid in list(manager._thread_index.keys()):
                all_files.extend(manager.list_files(tid))
            
            return {
                "success": True,
                "files": all_files,
                "count": len(all_files),
                "total_size_bytes": sum(f["size_bytes"] for f in all_files),
                "warning": "Showing files from all threads (thread context not available)"
            }
        
        manager = get_file_storage_manager()
        files = manager.list_files(thread_id)
        
        total_size = sum(f["size_bytes"] for f in files)
        
        log.info(f"Listed {len(files)} files for thread {thread_id}")
        
        return {
            "success": True,
            "files": files,
            "count": len(files),
            "total_size_bytes": total_size,
            "thread_id": thread_id
        }
        
    except Exception as e:
        log.error(f"Error listing files: {e}")
        import traceback
        log.error(f"Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def get_file_metadata(reference_id: str) -> Dict[str, Any]:
    """
    Get metadata about a file without retrieving its content.
    
    This is useful for checking file properties before deciding whether to retrieve it.
    
    Args:
        reference_id: The unique file reference ID
        
    Returns:
        Dictionary containing file metadata (without content)
        
    Example:
        >>> meta = get_file_metadata("file_abc123def456")
        >>> if meta["mime_type"].startswith("image/"):
        ...     # It's an image, retrieve it
        ...     content = get_file_content(meta["reference_id"])
    """
    try:
        from app.file_storage_manager import get_file_storage_manager
        
        manager = get_file_storage_manager()
        file_ref = manager.get_file(reference_id)
        
        if not file_ref:
            return {
                "success": False,
                "reference_id": reference_id,
                "error": f"File not found: {reference_id}"
            }
        
        return {
            "success": True,
            **file_ref.to_dict()
        }
        
    except Exception as e:
        log.error(f"Error getting file metadata {reference_id}: {e}")
        return {
            "success": False,
            "reference_id": reference_id,
            "error": str(e)
        }


# Tool registry for the python tool loader
def load_tools_from_config(tool_names: List[str]) -> List[Any]:
    """Load specific tools by name for the python tool loader."""
    available_tools = {
        "get_file_metadata": get_file_metadata,
        "get_file_content": get_file_content,
        "get_image_base64": get_image_base64,
        "list_available_files": list_available_files
    }
    
    tools = []
    for name in tool_names:
        if name in available_tools:
            tools.append(available_tools[name])
        else:
            log.warning(f"Tool '{name}' not found in file_retrieval_tools")
    
    return tools

# Tool definitions for LangChain/LangGraph
FILE_RETRIEVAL_TOOLS = [
    get_file_metadata,
    get_file_content,
    get_image_base64,
    list_available_files
]
