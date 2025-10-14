#!/usr/bin/env python3
"""
LiteLLM API for JK-Agents Framework
This module provides a dedicated API for LiteLLM multimodal functionality.
"""

import os
import logging
import tempfile
import mimetypes
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List

# Load environment variables
from dotenv import load_dotenv
load_dotenv()
print("✅ Loaded environment variables from .env file")

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware

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

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting LiteLLM API server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
