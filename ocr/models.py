"""
OCR Response Models - Pydantic models for OCR endpoints.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class OCRImageResult(BaseModel):
    """Result model for a single OCR image."""
    filename: str = Field(..., description="Original filename")
    success: bool = Field(..., description="Whether OCR was successful")
    extracted_text: str = Field(..., description="Extracted text from the image")
    error: Optional[str] = Field(None, description="Error message if OCR failed")
    processing_time: float = Field(..., description="Processing time in seconds")


class FastOCRResponse(BaseModel):
    """Response model for fast OCR endpoint."""
    success: bool = Field(..., description="Overall success status")
    message: str = Field(..., description="Response message")
    structured_cards: List[Dict[str, Any]] = Field(..., description="Structured contact cards (merged/summarized)")
    meta: List[Dict[str, Any]] = Field(default_factory=list, description="Metadata mapping card IDs to source files")
    total_images: int = Field(..., description="Total number of images processed")
    successful_count: int = Field(..., description="Number of successfully processed images")
    failed_count: int = Field(..., description="Number of failed images")
    total_processing_time: float = Field(..., description="Total processing time in seconds")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
