"""
Standalone Multimodal API server for testing the multimodal endpoint.
"""

import os
import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env")
except ImportError:
    print("⚠️ dotenv not installed, skipping environment loading")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("multimodal_api")

# Create FastAPI app
app = FastAPI(
    title="JK-Agents Multimodal API",
    description="API server for multimodal processing with JK-Agents Framework",
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

# Import and include the multimodal endpoint router
try:
    from app.multimodal_endpoint import router as multimodal_router
    app.include_router(multimodal_router)
    log.info("Multimodal endpoint loaded successfully")
except ImportError as e:
    log.error(f"Failed to import multimodal endpoint: {e}")
    raise

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Check if the API server is healthy.
    """
    from datetime import datetime
    return {
        "status": "healthy", 
        "version": "1.0.0",
        "server_time": datetime.now().isoformat()
    }

# Error handler
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    log.error(f"Unhandled exception: {str(exc)}")
    return {"error": str(exc)}

if __name__ == "__main__":
    # Check required dependencies
    try:
        import litellm
        from langchain_core.messages import SystemMessage, HumanMessage
        # LiteLLM doesn't have __version__, just check it's imported
        print(f"✅ LiteLLM imported successfully")
    except ImportError as e:
        print(f"❌ Missing required dependency: {e}")
        print("Please install with: pip install litellm langchain-core")
        exit(1)
    
    # Start server
    print("🚀 Starting Multimodal API server...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
