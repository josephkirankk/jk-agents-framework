"""
Custom exceptions for VectorDB wrapper.

This module defines custom exception classes for handling various error
conditions that can occur when interacting with the VectorDB API.
"""

from typing import Optional
import httpx


class VectorDBError(Exception):
    """Base exception for VectorDB-related errors."""
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None,
        response: Optional[httpx.Response] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response
    
    def __str__(self) -> str:
        if self.status_code:
            return f"VectorDB Error ({self.status_code}): {self.message}"
        return f"VectorDB Error: {self.message}"


class VectorDBConnectionError(VectorDBError):
    """Exception raised when connection to VectorDB API fails."""
    pass


class VectorDBValidationError(VectorDBError):
    """Exception raised when request/response validation fails."""
    pass


class VectorDBTimeoutError(VectorDBError):
    """Exception raised when requests timeout."""
    pass


class VectorDBAuthenticationError(VectorDBError):
    """Exception raised when authentication fails."""
    pass


class VectorDBNotFoundError(VectorDBError):
    """Exception raised when requested resource is not found."""
    pass


class VectorDBRateLimitError(VectorDBError):
    """Exception raised when rate limit is exceeded."""
    pass
