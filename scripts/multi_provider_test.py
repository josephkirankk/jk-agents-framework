#!/usr/bin/env python3
"""
Multi-Provider Testing Script

This script provides a simple CLI utility for testing multiple LLM providers (OpenAI, Anthropic, Gemini)
through the LiteLLM integration. It allows testing with different file types and comparing responses.

Usage:
  python multi_provider_test.py --provider openai --text "Explain what a hash map is."
  python multi_provider_test.py --provider anthropic --text "Analyze this code" --file code.py
  python multi_provider_test.py --provider gemini --text "Describe this image" --image photo.jpg
"""

import argparse
import base64
import configparser
import logging
import mimetypes
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed, skipping .env loading")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("multi-provider-test")

# Try importing LiteLLM
try:
    import litellm
    from litellm import completion
    HAS_LITELLM = True
    # Try to import utility functions (may not exist in all versions)
    try:
        from litellm.utils import supports_vision
        HAS_SUPPORTS_VISION = True
    except ImportError:
        HAS_SUPPORTS_VISION = False
    
    # supports_file_inputs may not exist, so we'll handle this manually
    HAS_SUPPORTS_FILE_INPUTS = False
    
except ImportError as e:
    HAS_LITELLM = False
    print(f"Error: LiteLLM is not installed or has import issues: {e}")
    print("Please install with 'pip install litellm>=1.43.0'")
    sys.exit(1)


def create_b64_data_uri(path: Path) -> str:
    """
    Create a data:...;base64,<data> string for a local file.
    
    Args:
        path: Path to the file
        
    Returns:
        Base64 data URI string
    """
    data = path.read_bytes()
    mime, _ = mimetypes.guess_type(path.name)
    if not mime:
        # Safe fallback
        mime = "application/octet-stream"
    encoded = base64.b64encode(data).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def create_file_item(path_or_url: str) -> Dict[str, Any]:
    """
    Create a file content item for LiteLLM.
    
    Args:
        path_or_url: Path to file or URL
        
    Returns:
        File content item for LiteLLM
    """
    lower = path_or_url.lower()
    if lower.startswith(("http://", "https://", "gs://")):
        return {"type": "file", "file": {"file_id": path_or_url}}
    
    # Local file
    p = Path(path_or_url).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path_or_url}")
    return {"type": "file", "file": {"file_data": create_b64_data_uri(p)}}


def create_image_item(image_path_or_url: str) -> Dict[str, Any]:
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
    return {"type": "image_url", "image_url": {"url": create_b64_data_uri(p)}}


def build_message_content(
    text: str, 
    files: List[str] = None,
    images: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Build multimodal message content for LiteLLM.
    
    Args:
        text: Text content
        files: List of file paths or URLs
        images: List of image paths or URLs
        
    Returns:
        List of content items for LiteLLM
    """
    content = []
    
    # Add text content
    if text.strip():
        content.append({"type": "text", "text": text})
    
    # Add files
    if files:
        for file_path in files:
            content.append(create_file_item(file_path))
    
    # Add images
    if images:
        for image_path in images:
            content.append(create_image_item(image_path))
    
    return content


def load_config(path: str) -> configparser.ConfigParser:
    """
    Load configuration from file.
    
    Args:
        path: Path to config file
        
    Returns:
        ConfigParser object
    """
    config = configparser.ConfigParser()
    
    # Create default config if file doesn't exist
    if not os.path.exists(path):
        config["models"] = {
            "openai_model": "openai/gpt-4o",
            "azure_model": "azure/gpt-4.1",
            "anthropic_model": "anthropic/claude-3-5-sonnet-20240620",
            "gemini_model": "gemini/gemini-1.5-pro"
        }
        config["defaults"] = {
            "temperature": "0.2",
            "timeout": "60"
        }
        
        # Write default config
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            config.write(f)
    else:
        # Read existing config
        with open(path, "r", encoding="utf-8") as f:
            config.read_file(f)
    
    return config


def check_model_capabilities(model: str) -> Dict[str, bool]:
    """
    Check capabilities of a model.
    
    Args:
        model: Model name
        
    Returns:
        Dict of capabilities (supports_files, supports_images)
    """
    supports_files_flag = False
    supports_images_flag = False
    
    # Basic heuristics for model capabilities
    model_lower = model.lower()
    
    # Check for vision support
    if HAS_SUPPORTS_VISION:
        try:
            supports_images_flag = supports_vision(model)
        except Exception as e:
            log.debug(f"Error checking vision support: {e}")
    else:
        # Heuristic: most modern models support vision
        if any(x in model_lower for x in ["gpt-4", "claude-3", "gemini", "vision"]):
            supports_images_flag = True
    
    # File support heuristic (most models can handle text files)
    supports_files_flag = True  # Assume most models can handle file content
    
    return {
        "supports_files": supports_files_flag,
        "supports_images": supports_images_flag
    }


def run_model(
    model: str,
    texts: List[str],
    files: List[str] = None,
    images: List[str] = None,
    temperature: float = 0.2,
    timeout: int = 60
) -> str:
    """
    Run a model with text, files, and images.
    
    Args:
        model: Model name (e.g., "openai/gpt-4o")
        texts: List of text inputs
        files: List of file paths or URLs
        images: List of image paths or URLs
        temperature: Temperature for generation
        timeout: Timeout in seconds
        
    Returns:
        Model response
    """
    # Check API keys
    provider = model.split("/")[0] if "/" in model else model.split(":")[0]
    
    # Handle Azure OpenAI specifically - LiteLLM uses these specific variable names
    if provider.lower() == "azure":
        required_vars = ["AZURE_API_KEY", "AZURE_API_BASE"]
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            log.error(f"Missing Azure OpenAI environment variables: {', '.join(missing)}")
            return f"Error: Missing Azure OpenAI environment variables: {', '.join(missing)}"
    else:
        env_var = f"{provider.upper()}_API_KEY"
        if not os.getenv(env_var) and not os.getenv("OPENAI_API_KEY"):
            log.error(f"Missing API key: {env_var} not found in environment")
            return f"Error: {env_var} environment variable is not set"
    
    # Check model capabilities
    capabilities = check_model_capabilities(model)
    supports_files_flag = capabilities["supports_files"]
    supports_images_flag = capabilities["supports_images"]
    log.info(f"Model capabilities: supports_files={supports_files_flag}, supports_images={supports_images_flag}")
    
    # Filter content based on model capabilities
    used_files = files or []
    used_images = images or []
    
    if files and not supports_files_flag:
        log.warning(f"Model {model} does not support files. Files will be ignored.")
        used_files = []
    
    if images and not supports_images_flag:
        log.warning(f"Model {model} does not support images. Images will be ignored.")
        used_images = []
    
    # Build content
    content = build_message_content(
        text="\n".join(texts),
        files=used_files,
        images=used_images
    )
    
    # Call the model
    try:
        log.info(f"Calling model {model} with {len(content)} content items")
        
        response = completion(
            model=model,
            messages=[{"role": "user", "content": content}],
            temperature=temperature,
            timeout=timeout
        )
        
        # Return response content
        return response["choices"][0]["message"]["content"]
    
    except Exception as e:
        log.error(f"Model call failed: {e}")
        return f"Error calling model: {str(e)}"


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Multi-provider model testing with LiteLLM"
    )
    
    # Provider selection
    parser.add_argument(
        "--provider", 
        choices=["openai", "azure", "anthropic", "gemini"],
        default="openai", 
        help="Provider to use"
    )
    
    # Model override
    parser.add_argument(
        "--model", 
        help="Override model (e.g., openai/gpt-4-turbo)"
    )
    
    # Input content
    parser.add_argument(
        "--text", 
        action="append", 
        default=[],
        help="Text input (repeatable for multiple sections)"
    )
    parser.add_argument(
        "--file", 
        action="append", 
        default=[],
        help="File path or URL (repeatable)"
    )
    parser.add_argument(
        "--image", 
        action="append", 
        default=[],
        help="Image path or URL (repeatable)"
    )
    
    # Config
    parser.add_argument(
        "--config", 
        default=os.path.expanduser("~/.jkagents/config.ini"),
        help="Path to config.ini file"
    )
    
    # Model parameters
    parser.add_argument(
        "--temperature", 
        type=float, 
        help="Override temperature"
    )
    parser.add_argument(
        "--timeout", 
        type=int, 
        help="Override timeout"
    )
    
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()
    
    # Load config
    config = load_config(args.config)
    # Pick a default model per provider (overrideable via --model)
    if args.model:
        model = args.model
    elif args.provider == "openai":
        model = config.get("models", "openai_model", fallback="openai/gpt-4o")
    elif args.provider == "azure":
        model = config.get("models", "azure_model", fallback="azure/gpt-4")
    elif args.provider == "anthropic":
        model = config.get("models", "anthropic_model", fallback="anthropic/claude-3-5-sonnet-20240620")
    else:  # gemini
        model = config.get("models", "gemini_model", fallback="gemini/gemini-1.5-pro")
    
    # Get model parameters
    temperature = args.temperature
    if temperature is None:
        temperature = config.getfloat("defaults", "temperature", fallback=0.2)
    timeout = args.timeout
    if timeout is None:
        timeout = config.getint("defaults", "timeout", fallback=60)
    
    # Default text if none provided
    texts = args.text
    if not texts:
        texts = ["Please provide a concise explanation of the concept of a hash map."]
    
    # Run the model
    print(f"\n--- Running {model} ---")
    print(f"Files: {len(args.file)}, Images: {len(args.image)}")
    
    response = run_model(
        model=model,
        texts=texts,
        files=args.file,
        images=args.image,
        temperature=temperature,
        timeout=timeout
    )
    
    print("\n--- Response ---")
    print(response)
    print("\n--- End of Response ---")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
