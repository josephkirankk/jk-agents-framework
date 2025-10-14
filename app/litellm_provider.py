"""
LiteLLM Provider Integration

This module provides integration with LiteLLM to support multiple LLM providers including:
- OpenAI (and compatible endpoints)
- Anthropic
- Google Gemini
- and others supported by LiteLLM

It handles file attachments, multimodal content, and provider-specific configurations.
"""

import logging
import os
import json
import base64
import mimetypes
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

# Import error handling to make dependencies optional
try:
    import litellm
    from litellm import completion
    from litellm.utils import supports_file_inputs, supports_vision
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False
    
log = logging.getLogger("litellm_provider")

class LiteLLMProvider:
    """
    Integration with LiteLLM for supporting multiple model providers.
    """
    
    def __init__(self):
        """Initialize the LiteLLM provider."""
        if not HAS_LITELLM:
            log.error("LiteLLM is not installed. Please install with 'pip install litellm>=1.43.0'")
            raise ImportError("LiteLLM is not installed")
        
        self._check_environment_variables()
        
    def _check_environment_variables(self):
        """Check for required environment variables and log warnings if missing."""
        # Check for OpenAI API key
        if not os.getenv("OPENAI_API_KEY"):
            log.warning("OPENAI_API_KEY not set in environment. OpenAI models may not work.")
            
        # Check for Anthropic API key
        if not os.getenv("ANTHROPIC_API_KEY"):
            log.warning("ANTHROPIC_API_KEY not set in environment. Anthropic models may not work.")
            
        # Check for Google Gemini API key
        if not os.getenv("GEMINI_API_KEY"):
            log.warning("GEMINI_API_KEY not set in environment. Google Gemini models may not work.")
    
    def create_b64_data_uri(self, path: Union[str, Path]) -> str:
        """
        Create a data:...;base64,<data> string for a local file.
        
        Args:
            path: Path to the file
            
        Returns:
            Base64 data URI string
        """
        if isinstance(path, str):
            path = Path(path)
            
        data = path.read_bytes()
        mime, _ = mimetypes.guess_type(path.name)
        if not mime:
            # Safe fallback
            mime = "application/octet-stream"
        encoded = base64.b64encode(data).decode("utf-8")
        return f"data:{mime};base64,{encoded}"
    
    def create_file_content_item(self, file_path_or_url: str) -> Dict[str, Any]:
        """
        Create a file content item for LiteLLM.
        
        Args:
            file_path_or_url: Path to file or URL
            
        Returns:
            File content item for LiteLLM
        """
        lower = file_path_or_url.lower()
        if lower.startswith(("http://", "https://", "gs://")):
            return {"type": "file", "file": {"file_id": file_path_or_url}}
        
        # Local file
        p = Path(file_path_or_url).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"File not found: {file_path_or_url}")
        return {"type": "file", "file": {"file_data": self.create_b64_data_uri(p)}}
    
    def create_image_content_item(self, image_path_or_url: str) -> Dict[str, Any]:
        """
        Create an image content item for LiteLLM.
        
        Args:
            image_path_or_url: Path to image or URL
            
        Returns:
            Image content item for LiteLLM
        """
        if image_path_or_url.lower().startswith(("http://", "https://")):
            return {"type": "image_url", "image_url": {"url": image_path_or_url}}
        
        # Local file
        p = Path(image_path_or_url).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"Image not found: {image_path_or_url}")
        return {"type": "image_url", "image_url": {"url": self.create_b64_data_uri(p)}}
    
    def build_message_content(
        self, 
        text: str, 
        files: List[Dict[str, Any]] = None,
        images: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Build a multimodal message content array for LiteLLM.
        
        Args:
            text: Text content
            files: List of file information dicts
            images: List of image information dicts
            
        Returns:
            List of content items for LiteLLM
        """
        content = []
        
        # Add text content
        if text:
            content.append({"type": "text", "text": text})
        
        # Add files
        if files:
            for file_info in files:
                file_path = file_info.get("file_path")
                file_id = file_info.get("file_id")
                
                if file_id:
                    content.append({"type": "file", "file": {"file_id": file_id}})
                elif file_path:
                    content.append(self.create_file_content_item(file_path))
        
        # Add images
        if images:
            for image_info in images:
                image_path = image_info.get("image_path")
                image_url = image_info.get("image_url")
                
                if image_url:
                    content.append({"type": "image_url", "image_url": {"url": image_url}})
                elif image_path:
                    content.append(self.create_image_content_item(image_path))
        
        return content
    
    def check_model_capabilities(self, model: str) -> Dict[str, bool]:
        """
        Check the capabilities of a model.
        
        Args:
            model: Model identifier (e.g., "openai/gpt-4o", "anthropic/claude-3-5-sonnet")
            
        Returns:
            Dictionary of capability flags
        """
        supports_files = False
        supports_images = False
        
        try:
            # Check if model supports file inputs
            supports_files = supports_file_inputs(model)
            
            # Check if model supports vision
            supports_images = supports_vision(model)
        except Exception as e:
            log.warning(f"Error checking model capabilities for {model}: {str(e)}")
        
        return {
            "supports_files": supports_files,
            "supports_images": supports_images
        }
    
    async def call_model(
        self,
        model: str,
        system_message: str,
        user_text: str,
        files: List[Dict[str, Any]] = None,
        images: List[Dict[str, Any]] = None,
        temperature: float = 0.2,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Call a model using LiteLLM with support for multimodal content.
        
        Args:
            model: Model identifier (e.g., "openai/gpt-4o", "anthropic/claude-3-5-sonnet")
            system_message: System message
            user_text: User text message
            files: List of file information dicts
            images: List of image information dicts
            temperature: Temperature setting (0.0 to 1.0)
            timeout: Timeout in seconds
            
        Returns:
            LiteLLM response
        """
        log.info(f"Calling model {model} via LiteLLM")
        files = files or []
        images = images or []
        
        # Check model capabilities
        capabilities = self.check_model_capabilities(model)
        supports_files = capabilities["supports_files"]
        supports_images = capabilities["supports_images"]
        
        # Log capabilities for debugging
        log.info(f"Model {model} capabilities: supports_files={supports_files}, supports_images={supports_images}")
        
        # Filter content based on model capabilities
        filtered_files = files if supports_files else []
        filtered_images = images if supports_images else []
        
        if (files and not supports_files) or (images and not supports_images):
            log.warning(
                f"Model {model} has limited multimodal support. "
                f"Files supported: {supports_files}, Images supported: {supports_images}. "
                f"Some content may be ignored."
            )
        
        # Build user message content
        user_message_content = self.build_message_content(
            text=user_text,
            files=filtered_files,
            images=filtered_images
        )
        
        # Create messages array
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message_content}
        ]
        
        # Call LiteLLM
        try:
            response = completion(
                model=model,
                messages=messages,
                temperature=temperature,
                timeout=timeout
            )
            
            # Get the response content
            response_content = response["choices"][0]["message"]["content"]
            
            return {
                "success": True,
                "content": response_content,
                "model": model,
                "raw_response": response
            }
            
        except Exception as e:
            log.error(f"Error calling model {model} via LiteLLM: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "model": model
            }
