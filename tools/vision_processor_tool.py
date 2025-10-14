"""
Vision Processor Tool

This tool takes image reference IDs and calls a vision model directly,
bypassing the agent's message history to prevent token bloat.

The tool retrieves images, sends them to the vision model, and returns
structured output WITHOUT storing base64 content in the agent's conversation.
"""

import logging
from typing import Dict, Any, List
from langchain_core.tools import tool

log = logging.getLogger(__name__)


@tool
def process_images_with_vision(
    prompt: str,
    model_name: str,
    file_reference_ids: List[str]
) -> str:
    """
    Process images using a vision model and return structured output.
    
    This tool retrieves images by reference ID, sends them to a vision model,
    and returns the analysis WITHOUT storing base64 content in message history.
    
    Args:
        prompt: The prompt/instructions for the vision model
        model_name: The vision model to use (e.g., "azure_openai:gpt-4o", "openai/gpt-4o")
        file_reference_ids: List of image reference IDs to process
        
    Returns:
        Structured YAML output with results for each image
        
    Example:
        >>> result = process_images_with_vision(
        ...     prompt="Extract all text from this visiting card",
        ...     model_name="azure_openai:gpt-4o",
        ...     file_reference_ids=["file_abc123", "file_def456"]
        ... )
    """
    try:
        from app.file_storage_manager import get_file_storage_manager
        from app.enhanced_litellm_wrapper import create_litellm_model
        from langchain_core.messages import HumanMessage, SystemMessage
        
        if not file_reference_ids:
            return "ERROR: No file reference IDs provided"
        
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
        
        # Convert model name format if needed
        # Handle various format conversions:
        # - azure_openai:model -> azure/model
        # - google:model -> gemini/model
        # - openai:model -> openai/model
        # - provider/model -> provider/model (already correct)
        
        litellm_model_name = model_name
        
        if model_name.startswith("azure_openai:"):
            # Convert azure_openai:gpt-4o -> azure/gpt-4o
            model_part = model_name.split(":", 1)[1]
            litellm_model_name = f"azure/{model_part}"
            log.info(f"Converted model name: {model_name} -> {litellm_model_name}")
        
        elif model_name.startswith("google:"):
            # Convert google:gemini-2.5-flash -> gemini/gemini-2.5-flash
            model_part = model_name.split(":", 1)[1]
            # If model doesn't start with 'gemini-', add it
            if not model_part.startswith("gemini-"):
                litellm_model_name = f"gemini/gemini-{model_part}"
            else:
                litellm_model_name = f"gemini/{model_part}"
            log.info(f"Converted model name: {model_name} -> {litellm_model_name}")
        
        elif model_name.startswith("openai:"):
            # Convert openai:gpt-4o -> openai/gpt-4o
            model_part = model_name.split(":", 1)[1]
            litellm_model_name = f"openai/{model_part}"
            log.info(f"Converted model name: {model_name} -> {litellm_model_name}")
        
        elif "/" in model_name:
            # Already in provider/model format - but check for google/ -> gemini/ conversion
            if model_name.startswith("google/"):
                # LiteLLM uses gemini/ not google/ for Gemini models
                model_part = model_name.split("/", 1)[1]
                litellm_model_name = f"gemini/{model_part}"
                log.info(f"Converted google/ to gemini/: {model_name} -> {litellm_model_name}")
            else:
                log.info(f"Model name already in correct format: {model_name}")
        
        else:
            # No provider prefix, assume it's a model name and use as-is
            log.warning(f"Model name '{model_name}' has no provider prefix. Using as-is, but this may fail.")
        
        # Create vision model
        try:
            model = create_litellm_model(model_id=litellm_model_name, temperature=0.1)
        except Exception as e:
            log.error(f"Failed to create model {litellm_model_name}: {e}")
            return f"ERROR: Failed to create vision model: {e}"
        
        # Process each image separately to get structured output per image
        results = []
        
        for idx, img_data in enumerate(images_data, 1):
            try:
                # Build multimodal message for this image
                content = [
                    {"type": "text", "text": f"{prompt}\n\nImage: {img_data['filename']}"},
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
                
                # Call vision model
                log.info(f"Processing image {idx}/{len(images_data)} with {model_name}")
                response = model.invoke(messages)
                
                # Extract response content
                response_text = response.content if hasattr(response, 'content') else str(response)
                
                # Add to results in YAML format
                results.append(f"part {idx}:")
                results.append(f"  file: {img_data['filename']}")
                results.append(f"  reference_id: {img_data['reference_id']}")
                results.append(f"  output: |")
                # Indent each line of the output
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
        
        # Format final output
        output = "----------------VALID YAML OUTPUT--------------\n"
        output += "\n".join(results)
        
        log.info(f"✅ Vision processing complete for {len(images_data)} images. "
                f"Output size: ~{len(output)} chars (~{len(output)//4} tokens)")
        
        return output
        
    except Exception as e:
        log.error(f"Error in process_images_with_vision: {e}")
        import traceback
        log.error(traceback.format_exc())
        return f"ERROR: Vision processing failed - {str(e)}"