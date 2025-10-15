#!/usr/bin/env python3
"""
LiteLLM API for JK-Agents Framework
This module provides a dedicated API for LiteLLM multimodal functionality
and large data retrieval.
"""

import os
import logging
import tempfile
import mimetypes
import time
import uuid
import sqlite3
import json
import gzip
import re
from pathlib import Path
from typing import Dict, Any, Optional, List

# Load environment variables
from dotenv import load_dotenv
load_dotenv()
print("✅ Loaded environment variables from .env file")

from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Path as PathParam, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("litellm_api")

# Import LiteLLM functionality
try:
    from app.enhanced_litellm_wrapper import (
        EnhancedLiteLLMChat,
        is_litellm_model,
        create_litellm_model
    )
    HAS_LITELLM = True
    print("✅ Successfully imported LiteLLM wrapper")
except ImportError as e:
    HAS_LITELLM = False
    print(f"❌ Failed to import LiteLLM wrapper: {e}")

# Import simple conversation memory
try:
    from app.simple_conversation_memory_fixed import (
        inject_conversation_context,
        store_conversation_turn
    )
    HAS_MEMORY = True
    print("✅ Successfully imported conversation memory")
except ImportError as e:
    HAS_MEMORY = False
    print(f"❌ Failed to import conversation memory: {e}")

# Import centralized database configuration
try:
    from app.database_config import get_large_data_config
    HAS_DB_CONFIG = True
    print("✅ Successfully imported database configuration")
except ImportError as e:
    HAS_DB_CONFIG = False
    print(f"❌ Failed to import database configuration: {e}")

# Create FastAPI app
app = FastAPI(
    title="LiteLLM Multimodal API",
    description="API for multimodal LLM interactions using LiteLLM",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Check if the API is healthy."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "litellm_available": HAS_LITELLM,
        "memory_available": HAS_MEMORY
    }

@app.post("/multimodal")
async def multimodal_endpoint(
    model: str = Form(..., description="LiteLLM model ID (e.g., 'openai/gpt-4o')"),
    prompt: str = Form(..., description="Text prompt for the model"),
    thread_id: Optional[str] = Form(None, description="Optional thread ID for conversation continuity"),
    temperature: float = Form(0.2, description="Model temperature (0.0 to 1.0)"),
    files: List[UploadFile] = File(default=[], description="Optional files to upload"),
    system_message: Optional[str] = Form("You are a helpful assistant.", description="System message for the model")
):
    """
    Process multimodal requests with text, images, and other files.
    """
    if not HAS_LITELLM:
        raise HTTPException(
            status_code=501,
            detail="LiteLLM integration is not available"
        )

    # Simple check if files were uploaded
    log.info(f"Received {len(files)} files: {[f.filename for f in files]}")
    
    # For a minimal test, just echo back details
    if not is_litellm_model(model):
        return {
            "status": "error",
            "detail": f"Invalid model format: {model}. Use provider/model format."
        }
    
    # Process simple multimodal request
    try:
        # Generate thread ID if not provided
        actual_thread_id = thread_id or str(uuid.uuid4())
        
        # Process files
        temp_files = []
        image_paths = []
        document_paths = []
        
        for file in files:
            file_content = await file.read()
            temp_dir = Path(tempfile.mkdtemp())
            temp_path = temp_dir / file.filename
            temp_path.write_bytes(file_content)
            temp_files.append(temp_path)
            
            mime_type = file.content_type or mimetypes.guess_type(file.filename)[0]
            if mime_type and mime_type.startswith('image/'):
                image_paths.append(str(temp_path))
            else:
                document_paths.append(str(temp_path))
        
        # Create model
        model_instance = create_litellm_model(
            model_id=model,
            temperature=temperature
        )
        
        # Get capabilities
        capabilities = model_instance.check_capabilities()
        
        # Enhance with conversation context if available
        enhanced_prompt = prompt
        if HAS_MEMORY:
            enhanced_prompt = inject_conversation_context(prompt, actual_thread_id)
        
        # Create multimodal message
        multimodal_message = model_instance.create_multimodal_message(
            text=enhanced_prompt,
            images=image_paths if capabilities.get("supports_vision", False) else None,
            files=document_paths if capabilities.get("supports_files", False) else None
        )
        
        # Add system message
        from langchain_core.messages import SystemMessage
        messages = [SystemMessage(content=system_message), multimodal_message]
        
        # Generate response
        start_time = time.time()
        result = await model_instance._agenerate(messages)
        end_time = time.time()
        
        response = result.generations[0].message.content
        processing_time = round(end_time - start_time, 2)
        
        # Store conversation if memory available
        if HAS_MEMORY:
            store_conversation_turn(
                thread_id=actual_thread_id,
                user_input=prompt,
                assistant_response=response
            )
        
        # Clean up temp files
        for temp_file in temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    temp_file.parent.rmdir()
            except Exception as e:
                log.warning(f"Failed to clean up temp file: {e}")
        
        return {
            "success": True,
            "model": model,
            "response": response,
            "processing_time": processing_time,
            "thread_id": actual_thread_id,
            "capabilities": capabilities,
            "files_processed": len(files)
        }
        
    except Exception as e:
        log.error(f"Error processing multimodal request: {e}")
        import traceback
        log.error(traceback.format_exc())
        
        # Clean up temp files
        for temp_file in temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    temp_file.parent.rmdir()
            except:
                pass
                
        raise HTTPException(
            status_code=500,
            detail=f"Multimodal processing failed: {str(e)}"
        )

@app.get("/test-litellm/{model}")
async def test_litellm_model(model: str):
    """Test a LiteLLM model to verify it works."""
    if not HAS_LITELLM:
        raise HTTPException(
            status_code=501,
            detail="LiteLLM integration is not available"
        )
        
    if not is_litellm_model(model):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model format: {model}. Use provider/model format."
        )
    
    try:
        model_instance = create_litellm_model(
            model_id=model,
            temperature=0.2
        )
        
        capabilities = model_instance.check_capabilities()
        return {
            "success": True,
            "model": model,
            "capabilities": capabilities
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Model test failed: {str(e)}"
        )


# ============================================================================
# Large Data Retrieval API
# ============================================================================

def get_database_connection():
    """
    Get a connection to the large data storage database.
    
    Uses centralized database configuration from environment variables.
    Falls back to default path if configuration is not available.
    """
    # Get database path from centralized configuration
    if HAS_DB_CONFIG:
        try:
            config = get_large_data_config(format="app")
            db_path = config.get("sqlite_path", "./data/large_data_storage.db")
            log.info(f"Using database path from centralized config: {db_path}")
        except Exception as e:
            log.warning(f"Failed to get database path from config, using default: {e}")
            db_path = "./data/large_data_storage.db"
    else:
        # Fallback: Check environment variable or use default
        db_path = os.getenv("LARGE_DATA_DB_PATH", "./data/large_data_storage.db")
        log.info(f"Using database path from environment or default: {db_path}")
    
    # Ensure parent directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        log.info(f"Created database directory: {db_dir}")
    
    # Check if database exists
    if not os.path.exists(db_path):
        log.warning(f"Database not found at {db_path}, it will be created on first use")
    
    return sqlite3.connect(db_path, check_same_thread=False)


def validate_reference_id(reference_id: str) -> bool:
    """Validate reference ID format: ref_[a-f0-9]{12}"""
    pattern = r'^ref_[a-f0-9]{12}$'
    return bool(re.match(pattern, reference_id))


@app.get("/api/data/{reference_id}")
async def get_data_by_reference(
    reference_id: str = PathParam(..., description="Reference ID (format: ref_[a-f0-9]{12})"),
    thread_id: Optional[str] = Query(None, description="Optional thread ID for filtering")
):
    """
    Retrieve stored JSON data from the SQLite database by reference ID.

    Args:
        reference_id: Reference ID in format ref_[a-f0-9]{12} (e.g., ref_fd05f4970f14)
        thread_id: Optional thread ID for filtering by specific thread/session

    Returns:
        JSON response with status, reference_id, data, and metadata

    Raises:
        HTTPException 400: Invalid reference ID format
        HTTPException 404: Reference ID not found
        HTTPException 500: Database or decompression errors
    """
    # Validate reference ID format
    if not validate_reference_id(reference_id):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid reference ID format. Expected: ref_[a-f0-9]{{12}}, got: {reference_id}"
        )

    try:
        # Connect to database
        conn = get_database_connection()
        cursor = conn.cursor()

        # Query the large_tool_data table
        query = """
            SELECT
                reference_id,
                tool_name,
                storage_type,
                data_blob,
                compressed,
                content_type,
                size_bytes,
                metadata,
                created_at,
                access_count
            FROM large_tool_data
            WHERE reference_id = ?
        """

        cursor.execute(query, (reference_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            raise HTTPException(
                status_code=404,
                detail=f"Reference ID '{reference_id}' not found in database"
            )

        # Extract row data
        (ref_id, tool_name, storage_type, data_blob, compressed,
         content_type, size_bytes, metadata_json, created_at, access_count) = row

        # Parse metadata
        try:
            metadata = json.loads(metadata_json) if metadata_json else {}
        except json.JSONDecodeError:
            metadata = {}

        # Filter by thread_id if provided
        if thread_id:
            stored_thread_id = metadata.get("thread_id")
            if stored_thread_id and stored_thread_id != thread_id:
                conn.close()
                raise HTTPException(
                    status_code=404,
                    detail=f"Reference ID '{reference_id}' not found for thread_id '{thread_id}'"
                )

        # Decompress data if needed
        if compressed:
            try:
                data_bytes = gzip.decompress(data_blob)
            except Exception as e:
                conn.close()
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to decompress data: {str(e)}"
                )
        else:
            data_bytes = data_blob

        # Deserialize data based on content type
        try:
            if content_type == 'json':
                data_str = data_bytes.decode('utf-8')
                data = json.loads(data_str)
            elif content_type == 'text':
                data = data_bytes.decode('utf-8')
            else:
                data = data_bytes.decode('utf-8')
        except Exception as e:
            conn.close()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to deserialize data: {str(e)}"
            )

        # Update access count
        cursor.execute("""
            UPDATE large_tool_data
            SET access_count = access_count + 1,
                last_accessed = CURRENT_TIMESTAMP
            WHERE reference_id = ?
        """, (reference_id,))
        conn.commit()
        conn.close()

        # Build response
        response = {
            "status": "success",
            "reference_id": ref_id,
            "data": data,
            "metadata": {
                "tool_name": tool_name,
                "storage_type": storage_type,
                "content_type": content_type,
                "size_bytes": size_bytes,
                "compressed": bool(compressed),
                "created_at": created_at,
                "access_count": access_count + 1,
                **metadata  # Include original metadata
            }
        }

        return JSONResponse(content=response)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        log.error(f"Error retrieving data for reference_id {reference_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/api/data")
async def list_all_data(
    limit: int = Query(50, description="Maximum number of datasets to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    """
    List all stored datasets with their metadata.

    Args:
        limit: Maximum number of datasets to return (default: 50)
        offset: Offset for pagination (default: 0)

    Returns:
        JSON response with list of datasets and their metadata
    """
    try:
        conn = get_database_connection()
        cursor = conn.cursor()

        # Query all datasets with pagination
        query = """
            SELECT
                reference_id,
                tool_name,
                storage_type,
                content_type,
                size_bytes,
                metadata,
                created_at,
                access_count
            FROM large_tool_data
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """

        cursor.execute(query, (limit, offset))
        rows = cursor.fetchall()

        # Get total count
        cursor.execute("SELECT COUNT(*) FROM large_tool_data")
        total_count = cursor.fetchone()[0]

        conn.close()

        # Build response
        datasets = []
        for row in rows:
            (ref_id, tool_name, storage_type, content_type,
             size_bytes, metadata_json, created_at, access_count) = row

            try:
                metadata = json.loads(metadata_json) if metadata_json else {}
            except json.JSONDecodeError:
                metadata = {}

            datasets.append({
                "reference_id": ref_id,
                "tool_name": tool_name,
                "storage_type": storage_type,
                "content_type": content_type,
                "size_bytes": size_bytes,
                "created_at": created_at,
                "access_count": access_count,
                "metadata": metadata
            })

        return JSONResponse(content={
            "status": "success",
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "datasets": datasets
        })

    except Exception as e:
        log.error(f"Error listing datasets: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting LiteLLM API server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
