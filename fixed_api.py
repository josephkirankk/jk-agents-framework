"""
Fixed API for JK-Agents Framework
This module provides a streamlined API with only essential functionality.
"""

import os
import logging
import base64
import mimetypes
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env")
except ImportError:
    # python-dotenv not installed, skip loading
    print("⚠️ dotenv not installed, skipping environment loading")

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

# Import enhanced LiteLLM functionality
try:
    from app.enhanced_litellm_wrapper import (
        EnhancedLiteLLMChat, 
        is_litellm_model, 
        create_litellm_model
    )
    HAS_ENHANCED_LITELLM = True
    print("✅ Enhanced LiteLLM wrapper loaded successfully")
except ImportError as e:
    HAS_ENHANCED_LITELLM = False
    print(f"❌ Enhanced LiteLLM import error: {e}")

# Import simple conversation memory
try:
    from app.simple_conversation_memory_fixed import inject_conversation_context, store_conversation_turn
    HAS_CONVERSATION_MEMORY = True
    print("✅ Conversation memory loaded successfully")
except ImportError as e:
    HAS_CONVERSATION_MEMORY = False
    print(f"❌ Conversation memory import error: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("fixed_api")

# Create FastAPI app
app = FastAPI(
    title="JK-Agents Framework API",
    description="API for JK-Agents Framework with multimodal support",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Check if the API server is healthy.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "server_time": datetime.now(timezone.utc).isoformat(),
        "enhanced_litellm": HAS_ENHANCED_LITELLM,
        "conversation_memory": HAS_CONVERSATION_MEMORY
    }

def generate_thread_id():
    """Generate a unique thread ID for conversation tracking."""
    return str(uuid.uuid4())

@app.post("/multimodal")
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
    if not HAS_ENHANCED_LITELLM:
        raise HTTPException(
            status_code=501,
            detail="Enhanced LiteLLM is not available. Please install litellm package."
        )
    
    try:
        # Validate model format
        if not is_litellm_model(model):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid LiteLLM model format: {model}. Use format: provider/model (e.g., 'openai/gpt-4o')"
            )
        
        # Get or create thread ID
        actual_thread_id = thread_id or generate_thread_id()
        log.info(f"Processing multimodal request with model {model}, thread: {actual_thread_id}")
        
        # Process uploaded files
        temp_files = []
        image_paths = []
        document_paths = []
        file_info = []
        
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
        enhanced_prompt = prompt
        if HAS_CONVERSATION_MEMORY:
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
        start_time = time.time()
        result = await model_instance._agenerate(messages)
        end_time = time.time()
        
        response_content = result.generations[0].message.content
        processing_time = round(end_time - start_time, 2)
        
        # Store conversation turn
        if HAS_CONVERSATION_MEMORY:
            store_conversation_turn(
                thread_id=actual_thread_id,
                user_input=prompt,
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
        import traceback
        log.error(traceback.format_exc())
        
        raise HTTPException(
            status_code=500,
            detail=f"Multimodal processing failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Fixed API server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
