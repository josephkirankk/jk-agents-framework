"""
OCR API - Lightweight FastAPI application for OCR processing only.

This is a standalone API focused solely on OCR functionality,
separate from the main multi-agent system.
"""

import asyncio
import logging
import mimetypes
import os
import time
from datetime import datetime, timezone
from typing import List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import OCR module
from ocr import FastOCRResponse, process_image_ocr, summarize_visiting_cards

# --- Detail logging setup for OCR ---
OCR_LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'ocr_log')
os.makedirs(OCR_LOG_DIR, exist_ok=True)
log_timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
log_path = os.path.join(OCR_LOG_DIR, f'ocr_{log_timestamp}.log')
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_path, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("ocr_api")
log.info(f'OCR API logging to: {log_path}')

# Create FastAPI app
app = FastAPI(
    title="OCR API",
    description="Lightweight OCR API for visiting card processing",
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


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "ocr-api",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health - Health check",
            "ocr_fast": "/ocr/fast - Fast OCR for visiting cards",
            "docs": "/docs - Interactive API documentation",
        },
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ocr-api",
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
    }


@app.post("/ocr/fast", response_model=FastOCRResponse)
async def fast_ocr_endpoint(
    files: List[UploadFile] = File(
        ...,
        description="Visiting card images to process (supports jpg, png, jpeg, webp, etc.)"
    ),
    temperature: float = Form(
        0.1,
        description="Model temperature (0.0 to 1.0, lower is more deterministic)"
    ),
    structured_output: bool = Form(
        True,
        description="Return structured output with metadata"
    )
):
    """
    Fast OCR endpoint for visiting cards (business cards).
    
    Optimized for extracting structured information from visiting cards,
    including front and back sides. Processes multiple cards in parallel.
    
    Features:
    - Specialized for visiting cards
    - Extracts structured contact information
    - Handles front and back sides
    - Parallel processing for speed
    - Multi-language support
    - Unique card IDs and file reference tracking
    
    Args:
        files: List of visiting card images
        model: LiteLLM model identifier (default: gemini/gemini-flash-latest)
        temperature: Model temperature for deterministic output
        structured_output: Return structured JSON response
    
    Returns:
        FastOCRResponse with structured contact information,
        card IDs, and file reference metadata
    """
    start_time = time.time()
    
    try:
        model = "gemini/gemini-flash-latest"  # Hardcoded for all code paths
        # Validate files
        if not files or len(files) == 0:
            raise HTTPException(
                status_code=400,
                detail="No files provided. Please upload at least one image."
            )
        
        log.info(f"Starting fast OCR for {len(files)} images using {model}")
        
        # Validate file types
        valid_image_types = [
            'image/jpeg', 'image/jpg', 'image/png',
            'image/webp', 'image/gif', 'image/bmp'
        ]
        
        for file in files:
            mime_type = file.content_type or mimetypes.guess_type(file.filename)[0]
            if mime_type not in valid_image_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type for {file.filename}. "
                           f"Supported types: JPEG, PNG, WEBP, GIF, BMP"
                )
        
        # Process all images in parallel for maximum speed
        tasks = []
        model = "gemini/gemini-flash-latest"  # Hardcoded server-side, not exposed
        for file in files:
            # Read file content
            file_content = await file.read()
            mime_type = file.content_type or mimetypes.guess_type(file.filename)[0]
            
            # Create OCR task
            task = process_image_ocr(
                image_data=file_content,
                filename=file.filename,
                mime_type=mime_type,
                model=model,
                temperature=temperature
            )
            tasks.append(task)
        
        # Execute all OCR tasks in parallel
        log.info(f"Processing {len(tasks)} images in parallel...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions from gather
        processed_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                # If task raised an exception, create error result
                log.error(f"Task {idx} raised exception: {result}")
                processed_results.append({
                    "filename": files[idx].filename if idx < len(files) else f"image_{idx}",
                    "success": False,
                    "extracted_text": "",
                    "error": str(result),
                    "processing_time": 0.0
                })
            else:
                processed_results.append(result)
        
        # Calculate statistics
        total_processing_time = time.time() - start_time
        successful_count = sum(1 for r in processed_results if r["success"])
        failed_count = len(processed_results) - successful_count
        
        log.info(
            f"✅ Fast OCR completed: {successful_count}/{len(processed_results)} successful, "
            f"total time: {total_processing_time:.2f}s"
        )
        
        # Summarize all OCR results into structured format
        structured_cards = []
        meta = []
        summarization_time = 0.0
        
        if successful_count > 0:
            log.info("Starting final summarization to combine and structure cards...")
            summary_result = await summarize_visiting_cards(
                ocr_results=processed_results,
                model=model,
                temperature=0.0
            )
            
            if summary_result["success"]:
                structured_cards = summary_result["structured_cards"]
                meta = summary_result.get("meta", [])
                summarization_time = summary_result["processing_time"]
                log.info(f"✅ Structured {len(structured_cards)} unique card(s)")
            else:
                log.warning(f"⚠️ Summarization failed: {summary_result.get('error')}")
        
        # Update total processing time to include summarization
        total_time_with_summary = total_processing_time + summarization_time
        
        # Build response
        # Log removed fields for auditing
        log.info(f"summarization_time: {round(summarization_time, 2)}")
        log.info(f"model_used: {model}")
        response = FastOCRResponse(
            success=successful_count > 0,
            message=f"Processed {len(processed_results)} images: "
                   f"{successful_count} successful, {failed_count} failed. "
                   f"Structured {len(structured_cards)} card(s).",
            structured_cards=structured_cards,
            meta=meta,
            total_images=len(processed_results),
            successful_count=successful_count,
            failed_count=failed_count,
            total_processing_time=round(total_time_with_summary, 2),
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error in fast OCR endpoint: {e}")
        import traceback
        log.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Fast OCR processing failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    # Run on a different port than main API (8001 vs 8000)
    uvicorn.run(app, host="0.0.0.0", port=8001)
