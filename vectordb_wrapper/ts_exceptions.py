"""
TsSearch Exceptions

This module contains custom exceptions for the TsSearch client.
"""

from typing import Optional, Any
import httpx


class TsSearchException(Exception):
    """Base exception for TsSearch operations."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[httpx.Response] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response


class TsSearchConnectionError(TsSearchException):
    """Exception raised when connection to TsSearch server fails."""
    pass


class TsSearchValidationError(TsSearchException):
    """Exception raised when request validation fails."""
    pass


class TsSearchServerError(TsSearchException):
    """Exception raised when TsSearch server returns an error."""
    pass


class TsSearchTimeoutError(TsSearchException):
    """Exception raised when request times out."""
    pass


class TsSearchNotFoundError(TsSearchException):
    """Exception raised when requested resource is not found."""
    pass
