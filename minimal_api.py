#!/usr/bin/env python3
"""
Minimal API for JK-Agents Framework
This module provides a basic API with only essential functionality.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("minimal_api")

# Create FastAPI app
app = FastAPI(
    title="Minimal JK-Agents Framework API",
    description="Simplified API for JK-Agents Framework",
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
        "version": "1.0.0"
    }

# Minimal multimodal endpoint
@app.post("/multimodal")
async def multimodal_endpoint(
    model: str = Form(..., description="Model ID"),
    prompt: str = Form(..., description="Text prompt"),
    files: List[UploadFile] = File(default=[], description="Optional files")
):
    """
    Basic multimodal endpoint.
    """
    return {
        "success": True,
        "request_received": True,
        "model": model,
        "prompt": prompt,
        "files_count": len(files),
        "files": [f.filename for f in files]
    }

# Echo endpoint for debugging
@app.post("/echo")
async def echo(message: str = Form(...)):
    """
    Echo back the message.
    """
    return {"message": message}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Minimal API server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
