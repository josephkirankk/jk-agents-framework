"""
Custom exceptions for the placeholder system.

This module defines specific exceptions that can occur during placeholder
processing, providing clear error messages and context for debugging.
"""

from typing import Optional, Any


class PlaceholderError(Exception):
    """Base exception for all placeholder-related errors."""
    
    def __init__(self, message: str, placeholder_name: Optional[str] = None, **kwargs):
        super().__init__(message)
        self.placeholder_name = placeholder_name
        self.context = kwargs


class PlaceholderNotFoundError(PlaceholderError):
    """Raised when a required placeholder is not found in any provider."""
    
    def __init__(self, placeholder_name: str, available_placeholders: Optional[list] = None):
        message = f"Placeholder '{placeholder_name}' not found"
        if available_placeholders:
            message += f". Available placeholders: {', '.join(sorted(available_placeholders))}"
        super().__init__(message, placeholder_name)
        self.available_placeholders = available_placeholders or []


class PlaceholderValidationError(PlaceholderError):
    """Raised when placeholder validation fails."""
    
    def __init__(self, placeholder_name: str, value: Any, validation_message: str):
        message = f"Validation failed for placeholder '{placeholder_name}': {validation_message}"
        super().__init__(message, placeholder_name)
        self.value = value
        self.validation_message = validation_message


class PlaceholderTransformationError(PlaceholderError):
    """Raised when placeholder transformation fails."""
    
    def __init__(self, placeholder_name: str, value: Any, transformation_error: str):
        message = f"Transformation failed for placeholder '{placeholder_name}': {transformation_error}"
        super().__init__(message, placeholder_name)
        self.value = value
        self.transformation_error = transformation_error


class PlaceholderProviderError(PlaceholderError):
    """Raised when a placeholder provider encounters an error."""
    
    def __init__(self, provider_name: str, error_message: str, placeholder_name: Optional[str] = None):
        message = f"Provider '{provider_name}' error"
        if placeholder_name:
            message += f" for placeholder '{placeholder_name}'"
        message += f": {error_message}"
        super().__init__(message, placeholder_name)
        self.provider_name = provider_name
        self.error_message = error_message


class PlaceholderRegistrationError(PlaceholderError):
    """Raised when placeholder registration fails."""
    
    def __init__(self, placeholder_name: str, reason: str):
        message = f"Failed to register placeholder '{placeholder_name}': {reason}"
        super().__init__(message, placeholder_name)
        self.reason = reason
