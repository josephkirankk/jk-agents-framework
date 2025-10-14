"""
Multimodal API endpoint implementation for the JK-Agents Framework.
This module provides a dedicated API endpoint for handling multimodal requests
with LiteLLM integration supporting various providers including OpenAI,
Google Gemini, Azure OpenAI, and Anthropic.
"""

import os
import logging
import json
import mimetypes
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Form, File, UploadFile, HTTPException

# Import LiteLLM wrapper
from app.enhanced_litellm_wrapper import (
    EnhancedLiteLLMChat, 
    is_litellm_model,
    create_litellm_model
)

# Import conversation memory functionality
from app.simple_conversation_memory_fixed import (
    inject_conversation_context, 
    store_conversation_turn
)

# Configure logging
log = logging.getLogger("multimodal_endpoint")

# Create router
router = APIRouter()

@router.post("/multimodal")
async def multimodal_endpoint(
    model: str = Form(..., description="LiteLLM model ID (e.g., 'openai/gpt-4o', 'gemini/gemini-2.5-flash-lite')"),
    prompt: str = Form(..., description="Text prompt for the model"),
    thread_id: Optional[str] = Form(None, description="Optional thread ID for conversation continuity"),
    temperature: float = Form(0.2, description="Model temperature (0.0 to 1.0)"),
    files: List[UploadFile] = File(default=[], description="Optional files to upload (images, documents)"),
    system_message: Optional[str] = Form("You are a helpful assistant.", description="System message for the model")
):
    """
    Enhanced multimodal endpoint using LiteLLM with support for images, files, and conversation continuity.
    
    Supports all LiteLLM providers:
    - OpenAI: openai/gpt-4o, openai/gpt-4o-mini  
    - Google Gemini: gemini/gemini-2.5-flash-lite, google/gemini-2.5-flash-lite
    - Anthropic: anthropic/claude-3-5-sonnet
    - Azure OpenAI: azure/gpt-4.1
    """
    # Validate model format
    if not is_litellm_model(model):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid LiteLLM model format: {model}. Use format: provider/model (e.g., 'openai/gpt-4o')"
        )
    
    # Get or create thread ID
    from app.thread_id_utils import get_or_create_thread_id
    actual_thread_id = get_or_create_thread_id(thread_id)
    log.info(f"Processing multimodal request with model {model}, thread: {actual_thread_id}")
    
    # Process uploaded files
    temp_files = []
    image_paths = []
    document_paths = []
    file_info = []
    
    try:
        for file in files:
            # Save file to temporary location
            file_content = await file.read()
            import tempfile
            temp_dir = Path(tempfile.mkdtemp())
            temp_file_path = temp_dir / file.filename
            temp_file_path.write_bytes(file_content)
            temp_files.append(temp_file_path)
            
            # Categorize file type
            mime_type = file.content_type or mimetypes.guess_type(file.filename)[0]
            
            if mime_type and mime_type.startswith('image/'):
                image_paths.append(str(temp_file_path))
                file_info.append({
                    "filename": file.filename,
                    "type": "image",
                    "mime_type": mime_type,
                    "size": len(file_content)
                })
            else:
                document_paths.append(str(temp_file_path))
                file_info.append({
                    "filename": file.filename,
                    "type": "document",
                    "mime_type": mime_type,
                    "size": len(file_content)
                })
            
            log.info(f"Processed file: {file.filename} ({mime_type})")
        
        # Create enhanced LiteLLM model
        model_instance = create_litellm_model(
            model_id=model,
            temperature=temperature,
            timeout=60
        )
        
        # Check model capabilities
        capabilities = model_instance.check_capabilities()
        log.info(f"Model capabilities: {capabilities}")
        
        # Inject conversation context if thread exists
        enhanced_prompt = inject_conversation_context(actual_thread_id, prompt)
        
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
        import time
        start_time = time.time()
        result = await model_instance._agenerate(messages)
        end_time = time.time()
        
        response_content = result.generations[0].message.content
        processing_time = round(end_time - start_time, 2)
        
        # Store conversation turn
        store_conversation_turn(
            thread_id=actual_thread_id,
            user_message=prompt,
            assistant_response=response_content
        )
        
        # Clean up temporary files
        for temp_file in temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    temp_file.parent.rmdir()
            except Exception as e:
                log.warning(f"Failed to clean up temp file {temp_file}: {e}")
        
        return {
            "success": True,
            "response": response_content,
            "model": model,
            "thread_id": actual_thread_id,
            "processing_time": processing_time,
            "capabilities": capabilities,
            "files_processed": len(files),
            "file_info": file_info,
            "conversation_context_used": enhanced_prompt != prompt
        }
        
    except Exception as e:
        # Clean up temporary files in case of error
        for temp_file in temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    temp_file.parent.rmdir()
            except:
                pass
        
        log.error(f"Error in multimodal endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Multimodal processing failed: {str(e)}"
        )
