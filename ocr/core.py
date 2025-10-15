"""
OCR Core - Core OCR processing functions for visiting cards.

This module contains the business logic for OCR processing,
extracted from the main API for better separation of concerns.
"""

import base64
import json
import logging
import re
import time
import uuid
import os
from datetime import datetime
from typing import Dict, Any, List

# Setup for ocr_log (if not already set by API)
OCR_LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'ocr_log')
os.makedirs(OCR_LOG_DIR, exist_ok=True)
if not logging.getLogger().handlers:
    log_timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    log_path = os.path.join(OCR_LOG_DIR, f'ocr_{log_timestamp}.log')
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[logging.FileHandler(log_path, encoding='utf-8'), logging.StreamHandler()]
    )
    log = logging.getLogger(__name__)
else:
    log = logging.getLogger(__name__)


async def process_image_ocr(
    image_data: bytes,
    filename: str,
    mime_type: str,
    model: str = "gemini/gemini-flash-latest",
    temperature: float = 0.1
) -> Dict[str, Any]:
    """
    Process a single image for OCR using LiteLLM.
    
    Args:
        image_data: Raw image bytes
        filename: Original filename
        mime_type: MIME type of the image
        model: LiteLLM model to use
        temperature: Model temperature
    
    Returns:
        Dictionary with OCR results
    """
    start_time = time.time()
    
    try:
        from app.enhanced_litellm_wrapper import create_litellm_model
        from langchain_core.messages import HumanMessage, SystemMessage
        
        # Compact OCR prompt - essential info only for speed
        OCR_PROMPT = """Extract ONLY the essential information from this visiting card:

NAME: [full name]
ROLE: [job title/designation]
COMPANY: [company name]
PHONE: [phone number(s)]
EMAIL: [email address(es)]
ADDRESS: [complete business address]
WEBSITE: [website/URLs if present]

IMPORTANT:
- Extract text EXACTLY as shown
- If field not visible, write "Not found"
- Keep it concise - only core contact information
- For multiple values (phones/emails), separate with comma"""
        
        # Convert image to base64
        base64_content = base64.b64encode(image_data).decode('utf-8')
        
        # Create vision model
        vision_model = create_litellm_model(model_id=model, temperature=temperature)
        
        # Create multimodal message
        content = [
            {"type": "text", "text": f"{OCR_PROMPT}\n\nImage: {filename}"},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{base64_content}"
                }
            }
        ]
        
        messages = [
            SystemMessage(content="You are a fast, accurate OCR system for visiting cards. Extract only: Name, Role, Company, Phone, Email, Address, Website. Be concise and precise."),
            HumanMessage(content=content)
        ]
        
        # Process with LiteLLM (use ainvoke if available, otherwise invoke)
        log.info(f"Processing OCR for {filename} with {model}")
        
        # Try async first, fall back to sync
        try:
            response = await vision_model.ainvoke(messages)
        except (AttributeError, NotImplementedError):
            # If ainvoke is not available, use sync invoke in thread pool
            import asyncio
            response = await asyncio.to_thread(vision_model.invoke, messages)
        
        response_text = response.content if hasattr(response, 'content') else str(response)
        processing_time = time.time() - start_time
        
        log.info(f"✅ OCR completed for {filename} in {processing_time:.2f}s")
        
        return {
            "filename": filename,
            "success": True,
            "extracted_text": response_text,
            "error": None,
            "processing_time": round(processing_time, 2)
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        log.error(f"❌ OCR failed for {filename}: {e}")
        import traceback
        log.error(traceback.format_exc())
        
        return {
            "filename": filename,
            "success": False,
            "extracted_text": "",
            "error": str(e),
            "processing_time": round(processing_time, 2)
        }


async def summarize_visiting_cards(
    ocr_results: List[Dict[str, Any]],
    model: str = "gemini/gemini-flash-latest",
    temperature: float = 0.0
) -> Dict[str, Any]:
    """
    Summarize multiple OCR results into structured JSON format with card IDs and file references.
    
    Args:
        ocr_results: List of OCR results from individual images
        model: LiteLLM model to use
        temperature: Model temperature (0.0 for deterministic)
    
    Returns:
        Dictionary with structured contact cards, file mapping metadata, and card IDs
    """
    start_time = time.time()
    
    try:
        from app.enhanced_litellm_wrapper import create_litellm_model
        from langchain_core.messages import HumanMessage, SystemMessage
        
        # Combine all successful OCR results and track filenames
        combined_text = ""
        filename_list = []  # Track filenames for metadata
        
        for idx, result in enumerate(ocr_results, 1):
            if result["success"]:
                filename_list.append(result["filename"])
                combined_text += f"\n--- Image {idx}: {result['filename']} ---\n"
                combined_text += result["extracted_text"]
                combined_text += "\n"
        
        if not combined_text.strip():
            return {
                "success": False,
                "structured_cards": [],
                "meta": [],
                "error": "No successful OCR results to summarize",
                "processing_time": 0.0
            }
        
        # Summarization prompt with file reference tracking
        SUMMARY_PROMPT = f"""Analyze these visiting card OCR results and create a structured JSON output.

OCR RESULTS:
{combined_text}

Create a JSON object with two keys:
1. "cards": array of card objects (merge front/back of same card into ONE entry)
2. "file_mapping": array tracking which image numbers contribute to each card

Output format (JSON only, no markdown):
{{
  "cards": [
    {{
      "name": "Full Name",
      "role": "Job Title",
      "company": "Company Name",
      "phone": ["phone1", "phone2"],
      "email": ["email1@example.com"],
      "address": "Complete Address",
      "website": ["www.example.com"]
    }}
  ],
  "file_mapping": [
    {{
      "card_index": 0,
      "image_numbers": [1, 2]
    }}
  ]
}}

Rules:
- Each card gets a unique index (0, 1, 2, etc.)
- In file_mapping, list which image numbers (from OCR RESULTS) contribute to each card
- If front and back belong to same person, card_index should reference both image numbers
- Use arrays for multiple phones/emails/websites
- Use "null" for missing fields
- Return ONLY valid JSON, nothing else"""
        
        # Create LLM model
        llm = create_litellm_model(model_id=model, temperature=temperature)
        
        messages = [
            SystemMessage(content="You are a data structuring expert. Convert OCR text into clean JSON. Output ONLY valid JSON, no explanations."),
            HumanMessage(content=SUMMARY_PROMPT)
        ]
        
        log.info(f"Summarizing {len(ocr_results)} OCR results into structured format...")
        
        # Process with LLM
        try:
            response = await llm.ainvoke(messages)
        except (AttributeError, NotImplementedError):
            import asyncio
            response = await asyncio.to_thread(llm.invoke, messages)
        
        response_text = response.content if hasattr(response, 'content') else str(response)
        processing_time = time.time() - start_time
        
        # Try to parse JSON from response
        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response_text)
        if json_match:
            json_text = json_match.group(1)
        else:
            json_text = response_text
        
        # Clean up and parse
        json_text = json_text.strip()
        
        try:
            parsed_response = json.loads(json_text)
            
            # Handle both old and new formats for backward compatibility
            if isinstance(parsed_response, list):
                # Old format: just an array of cards
                cards_data = parsed_response
                file_mapping = []  # No mapping available in old format
            elif isinstance(parsed_response, dict) and "cards" in parsed_response:
                # New format: object with cards and file_mapping
                cards_data = parsed_response.get("cards", [])
                file_mapping = parsed_response.get("file_mapping", [])
            else:
                # Single card object
                cards_data = [parsed_response]
                file_mapping = []
            
            # Generate unique card IDs and add to cards
            structured_cards = []
            meta = []
            
            for idx, card in enumerate(cards_data):
                # Generate unique card ID
                card_id = f"card_{uuid.uuid4().hex[:8]}"
                
                # Add card_id to the card data
                card_with_id = {"cardid": card_id, **card}
                structured_cards.append(card_with_id)
                
                # Build metadata: map card_id to filenames
                # Find file mapping for this card
                refs = []
                for mapping in file_mapping:
                    if mapping.get("card_index") == idx:
                        # Get image numbers (1-indexed in prompt)
                        image_numbers = mapping.get("image_numbers", [])
                        # Convert to filenames (image_numbers are 1-indexed)
                        for img_num in image_numbers:
                            if 0 < img_num <= len(filename_list):
                                refs.append(filename_list[img_num - 1])
                
                # If no file mapping found, assume this card uses all files (fallback)
                if not refs and filename_list:
                    refs = filename_list.copy()
                
                # Create meta entry
                meta.append({card_id: {"Refs": refs}})
            
        except json.JSONDecodeError as e:
            log.error(f"Failed to parse JSON: {e}")
            log.error(f"Response was: {response_text[:500]}")
            return {
                "success": False,
                "structured_cards": [],
                "meta": [],
                "error": f"Failed to parse JSON: {str(e)}",
                "processing_time": round(processing_time, 2),
                "raw_response": response_text
            }
        
        log.info(f"✅ Summarization complete: {len(structured_cards)} card(s) structured in {processing_time:.2f}s")
        
        return {
            "success": True,
            "structured_cards": structured_cards,
            "meta": meta,
            "error": None,
            "processing_time": round(processing_time, 2)
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        log.error(f"❌ Summarization failed: {e}")
        import traceback
        log.error(traceback.format_exc())
        
        return {
            "success": False,
            "structured_cards": [],
            "meta": [],
            "error": str(e),
            "processing_time": round(processing_time, 2)
        }
