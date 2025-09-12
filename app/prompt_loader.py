"""
Utility for loading prompts from files with proper error handling.

This module provides functionality to load prompts from external text files
while maintaining backward compatibility with direct text prompts.
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional

log = logging.getLogger("prompt_loader")


def load_prompt_content(
    prompt: Optional[str] = None,
    prompt_file: Optional[str] = None,
    config_dir: Optional[Path] = None,
) -> str:
    """
    Load prompt content from either direct text or file path.
    
    Args:
        prompt: Direct prompt text (optional)
        prompt_file: Path to prompt file relative to config directory (optional)
        config_dir: Directory containing the configuration file (for resolving relative paths)
        
    Returns:
        The prompt content as a string
        
    Raises:
        ValueError: If neither prompt nor prompt_file is provided, or if both are provided
        FileNotFoundError: If prompt_file is specified but the file doesn't exist
        UnicodeDecodeError: If the prompt file cannot be decoded as UTF-8
        
    Priority:
        If both prompt and prompt_file are provided, prompt_file takes precedence
        and a warning is logged.
    """
    if not prompt and not prompt_file:
        raise ValueError("Either 'prompt' or 'prompt_file' must be provided")
    
    # If both are provided, prefer prompt_file and log a warning
    if prompt and prompt_file:
        log.warning(
            "Both 'prompt' and 'prompt_file' provided. Using 'prompt_file' and ignoring 'prompt'."
        )
    
    # Load from file if prompt_file is specified
    if prompt_file:
        return _load_prompt_from_file(prompt_file, config_dir)
    
    # Use direct prompt text
    return prompt or ""


def _load_prompt_from_file(prompt_file: str, config_dir: Optional[Path] = None) -> str:
    """
    Load prompt content from a file.
    
    Args:
        prompt_file: Path to the prompt file (relative to config_dir if provided)
        config_dir: Base directory for resolving relative paths
        
    Returns:
        The file content as a string
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        UnicodeDecodeError: If the file cannot be decoded as UTF-8
    """
    # Resolve the file path
    if config_dir:
        file_path = config_dir / prompt_file
    else:
        file_path = Path(prompt_file)
    
    # Check if file exists
    if not file_path.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {file_path} "
            f"(resolved from: {prompt_file})"
        )
    
    # Check if it's actually a file
    if not file_path.is_file():
        raise ValueError(
            f"Prompt file path is not a file: {file_path}"
        )
    
    try:
        # Read the file with UTF-8 encoding (handles Windows encoding issues)
        with file_path.open("r", encoding="utf-8") as f:
            content = f.read()
        
        log.info(f"Successfully loaded prompt from file: {file_path}")
        return content
        
    except UnicodeDecodeError as e:
        log.error(f"Failed to decode prompt file {file_path} as UTF-8: {e}")
        raise UnicodeDecodeError(
            e.encoding,
            e.object,
            e.start,
            e.end,
            f"Cannot decode prompt file {file_path} as UTF-8. "
            f"Please ensure the file is saved with UTF-8 encoding."
        )
    except Exception as e:
        log.error(f"Unexpected error reading prompt file {file_path}: {e}")
        raise


def get_config_directory(config_path: Optional[Path] = None) -> Path:
    """
    Get the directory containing the configuration file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Directory containing the configuration file
    """
    if config_path:
        return config_path.parent
    
    # Default to config directory relative to this module
    return Path(__file__).resolve().parents[1] / "config"
