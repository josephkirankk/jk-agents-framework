"""
Config Model Format Handler for JK-Agents Framework

This module provides utilities for handling various model format specifications
and ensuring consistent integration between different providers and notations.
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple, List

log = logging.getLogger("config_model_format")

# Model format patterns
GOOGLE_PATTERN = r'^google:([^:]+)(?::([0-9.]+))?$'
LITELLM_PATTERN = r'^([^/]+)/([^:]+)(?::([0-9.]+))?$'

def parse_model_id(model_id: str) -> Dict[str, Any]:
    """
    Parse a model ID in any supported format and return structured information.
    
    Supports:
    - Google format: "google:model-name:temperature"
    - LiteLLM format: "provider/model-name:temperature"
    
    Returns a dictionary with:
    - provider: The model provider (e.g., "google", "openai", "azure")
    - model_name: The base model name without provider prefix
    - temperature: Optional temperature value if specified
    - original_format: The format of the original string ("google", "litellm")
    """
    if not isinstance(model_id, str):
        return {
            "provider": None,
            "model_name": None,
            "temperature": None,
            "original_format": None
        }
    
    # Try Google format
    google_match = re.match(GOOGLE_PATTERN, model_id)
    if google_match:
        model_name, temperature = google_match.groups()
        return {
            "provider": "google",
            "model_name": model_name,
            "temperature": float(temperature) if temperature else None,
            "original_format": "google"
        }
    
    # Try LiteLLM format
    litellm_match = re.match(LITELLM_PATTERN, model_id)
    if litellm_match:
        provider, model_name, temperature = litellm_match.groups()
        return {
            "provider": provider,
            "model_name": model_name,
            "temperature": float(temperature) if temperature else None,
            "original_format": "litellm"
        }
    
    # No recognized format
    return {
        "provider": None,
        "model_name": model_id,  # Treat the whole string as a model name
        "temperature": None,
        "original_format": "unknown"
    }

def convert_to_litellm_format(model_info: Dict[str, Any]) -> str:
    """
    Convert parsed model info to LiteLLM format: provider/model-name
    """
    if not model_info.get("provider") or not model_info.get("model_name"):
        return model_info.get("model_name", "")
    
    provider = model_info["provider"]
    model_name = model_info["model_name"]
    
    # Special case for google
    if provider == "google":
        # Use "gemini" provider for Gemini models in LiteLLM
        if "gemini" in model_name:
            provider = "gemini"
    
    # Build the model ID
    return f"{provider}/{model_name}"

def convert_model_id(model_id: str, target_format: str = "litellm") -> str:
    """
    Convert a model ID between different formats.
    
    Args:
        model_id: Original model ID in any format
        target_format: Target format, one of "litellm" or "google"
        
    Returns:
        Model ID in the target format
    """
    # Parse the model ID
    model_info = parse_model_id(model_id)
    
    if target_format == "litellm":
        # Convert to LiteLLM format
        return convert_to_litellm_format(model_info)
    elif target_format == "google" and model_info.get("provider"):
        # Convert to Google format
        return f"google:{model_info['model_name']}"
    else:
        # Return as-is if format not recognized
        return model_id

def normalize_model_config(app_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize model configuration in a config dictionary.
    Ensures consistent model format across the framework.
    
    Args:
        app_config: Application configuration dictionary with models section
        
    Returns:
        Updated configuration with normalized model formats
    """
    if not app_config or not isinstance(app_config, dict):
        return app_config
    
    # Make a copy to avoid modifying the original
    config_copy = app_config.copy()
    
    # Determine the target format based on config
    litellm_enabled = config_copy.get("litellm", {}).get("enabled", False)
    target_format = "litellm" if litellm_enabled else "original"
    
    # Normalize models section
    models_config = config_copy.get("models", {})
    if isinstance(models_config, dict):
        for key in ["default", "supervisor"]:
            if key in models_config and isinstance(models_config[key], str):
                model_id = models_config[key]
                if target_format == "litellm":
                    model_info = parse_model_id(model_id)
                    if model_info["original_format"] == "google":
                        # Convert Google format to LiteLLM
                        models_config[key] = convert_to_litellm_format(model_info)
                        log.info(f"Converted {key} model from '{model_id}' to '{models_config[key]}'")
    
    return config_copy
