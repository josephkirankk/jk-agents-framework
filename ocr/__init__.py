"""
OCR Module - Lightweight OCR processing for visiting cards.

This module provides OCR functionality independent from the main agent system.
"""

from .models import FastOCRResponse, OCRImageResult
from .core import process_image_ocr, summarize_visiting_cards

__all__ = [
    "FastOCRResponse",
    "OCRImageResult",
    "process_image_ocr",
    "summarize_visiting_cards",
]
