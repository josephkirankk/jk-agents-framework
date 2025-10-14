"""
Fast OCR Tool for Visiting Cards

This tool is a specialized wrapper around process_images_with_vision that:
1. Hardcodes the Gemini 2.0 Flash Experimental model for speed
2. Uses an optimized prompt for visiting card extraction
3. Removes the need for agents to specify model_name parameter

This ensures consistent, fast OCR extraction without allowing model switching.
"""

import logging
from typing import List
from langchain_core.tools import tool

log = logging.getLogger(__name__)


@tool
def extract_visiting_card_text_fast(
    file_reference_ids: List[str]
) -> str:
    """
    Fast OCR extraction for visiting card images using Google Gemini 2.0 Flash.
    
    This tool processes visiting card images and extracts all visible text
    including names, titles, companies, contact information, and addresses.
    
    The tool automatically uses the fastest available vision model (Gemini 2.0 Flash)
    and requires NO model selection from the agent.
    
    Args:
        file_reference_ids: List of image reference IDs to process
        
    Returns:
        Structured YAML output with extracted text and contact details for each card
        
    Example:
        >>> result = extract_visiting_card_text_fast(
        ...     file_reference_ids=["file_abc123", "file_def456"]
        ... )
    """
    try:
        from app.file_storage_manager import get_file_storage_manager
        from app.enhanced_litellm_wrapper import create_litellm_model
        from langchain_core.messages import HumanMessage, SystemMessage
        
        # Hardcoded optimal configuration for fast OCR
        FAST_OCR_MODEL = "gemini/gemini-flash-latest"
        
        FAST_OCR_PROMPT = """Extract ALL text from this visiting card image.

Identify and list:
- Full name (person's name)
- Job title / designation
- Company / organization name
- Phone numbers (all formats)
- Email addresses
- Website URLs
- Physical address (complete)
- Any other visible text (taglines, services, etc.)

Be thorough and accurate. Extract everything you can see clearly."""
        
        if not file_reference_ids:
            return "ERROR: No file reference IDs provided. Please provide visiting card image reference IDs."
        
        log.info(f"Fast OCR extraction for {len(file_reference_ids)} images using {FAST_OCR_MODEL}")
        
        file_manager = get_file_storage_manager()
        
        # Retrieve images
        images_data = []
        for ref_id in file_reference_ids:
            file_ref = file_manager.get_file(ref_id)
            if not file_ref:
                log.warning(f"File not found: {ref_id}")
                continue
            
            if not file_ref.is_image():
                log.warning(f"File {ref_id} is not an image, skipping")
                continue
            
            base64_content = file_manager.get_file_content_base64(ref_id)
            if base64_content:
                images_data.append({
                    "reference_id": ref_id,
                    "filename": file_ref.filename,
                    "mime_type": file_ref.mime_type,
                    "base64": base64_content
                })
                log.info(f"Retrieved image {file_ref.filename} for vision processing")
        
        if not images_data:
            return "ERROR: No valid images found for the provided reference IDs"
        
        # Create vision model
        try:
            model = create_litellm_model(model_id=FAST_OCR_MODEL, temperature=0.1)
        except Exception as e:
            log.error(f"Failed to create model {FAST_OCR_MODEL}: {e}")
            return f"ERROR: Failed to create vision model: {e}"
        
        # Process each image
        results = []
        for idx, img_data in enumerate(images_data, 1):
            try:
                content = [
                    {"type": "text", "text": f"{FAST_OCR_PROMPT}\n\nImage: {img_data['filename']}"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{img_data['mime_type']};base64,{img_data['base64']}"
                        }
                    }
                ]
                
                messages = [
                    SystemMessage(content="You are a vision analysis assistant. Provide clear, structured output."),
                    HumanMessage(content=content)
                ]
                
                log.info(f"Processing image {idx}/{len(images_data)} with {FAST_OCR_MODEL}")
                response = model.invoke(messages)
                
                response_text = response.content if hasattr(response, 'content') else str(response)
                
                results.append(f"part {idx}:")
                results.append(f"  file: {img_data['filename']}")
                results.append(f"  reference_id: {img_data['reference_id']}")
                results.append(f"  output: |")
                for line in response_text.split('\n'):
                    results.append(f"    {line}")
                
                log.info(f"✅ Processed {img_data['filename']} successfully")
                
            except Exception as e:
                log.error(f"Error processing image {img_data['filename']}: {e}")
                results.append(f"part {idx}:")
                results.append(f"  file: {img_data['filename']}")
                results.append(f"  reference_id: {img_data['reference_id']}")
                results.append(f"  output: |")
                results.append(f"    ERROR: Failed to process image - {str(e)}")
        
        output = "----------------VALID YAML OUTPUT--------------\n"
        output += "\n".join(results)
        
        log.info(f"✅ Fast OCR extraction complete for {len(images_data)} images")
        return output
        
    except Exception as e:
        log.error(f"Error in fast OCR extraction: {e}")
        import traceback
        log.error(traceback.format_exc())
        return f"ERROR: Fast OCR extraction failed - {str(e)}"
