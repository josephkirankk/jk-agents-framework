"""
Decorators for VectorDB wrapper functionality.

This module provides decorators for wrapping functions with VectorDB
functionality, including error handling, logging, and retry logic.
"""

import functools
import logging
import time
from typing import Callable, Any, Optional, Dict

from .client import VectorDBClient
from .exceptions import VectorDBError, VectorDBConnectionError


logger = logging.getLogger(__name__)


def vectordb_wrapper(
    base_url: Optional[str] = None,
    timeout: float = 30.0,
    max_retries: int = 3,
    log_requests: bool = True,
    log_responses: bool = True,
    raise_on_error: bool = True
):
    """
    Decorator that wraps functions with VectorDB client functionality.
    
    This decorator automatically creates a VectorDB client instance and
    provides it to the wrapped function, along with error handling,
    logging, and retry logic.
    
    Args:
        base_url: Base URL for the VectorDB API
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        log_requests: Whether to log request details
        log_responses: Whether to log response details
        raise_on_error: Whether to raise exceptions on errors
        
    Returns:
        Decorated function with VectorDB client functionality
        
    Example:
        @vectordb_wrapper(base_url="http://localhost:8010")
        async def search_defects(client, query: str):
            request = SearchRequest(query=query)
            return await client.search(request)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Create VectorDB client
            async with VectorDBClient(
                base_url=base_url,
                timeout=timeout,
                max_retries=max_retries
            ) as client:
                
                try:
                    if log_requests:
                        logger.info(f"Executing {func.__name__} with VectorDB client")
                        logger.debug(f"Function args: {args}, kwargs: {kwargs}")
                    
                    # Call the wrapped function with client as first argument
                    result = await func(client, *args, **kwargs)
                    
                    execution_time = time.time() - start_time
                    
                    if log_responses:
                        logger.info(
                            f"Successfully executed {func.__name__} "
                            f"in {execution_time:.2f}s"
                        )
                        logger.debug(f"Function result: {result}")
                    
                    return result
                    
                except VectorDBError as e:
                    execution_time = time.time() - start_time
                    logger.error(
                        f"VectorDB error in {func.__name__} "
                        f"after {execution_time:.2f}s: {str(e)}"
                    )
                    
                    if raise_on_error:
                        raise
                    return None
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    logger.error(
                        f"Unexpected error in {func.__name__} "
                        f"after {execution_time:.2f}s: {str(e)}"
                    )
                    
                    if raise_on_error:
                        raise VectorDBError(f"Unexpected error: {str(e)}") from e
                    return None
        
        return wrapper
    return decorator


def retry_on_connection_error(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator that retries function execution on connection errors.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except VectorDBConnectionError as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Connection error in {func.__name__} "
                            f"(attempt {attempt + 1}/{max_retries + 1}): {str(e)}"
                        )
                        if delay > 0:
                            import asyncio
                            await asyncio.sleep(delay * (attempt + 1))  # Exponential backoff
                    else:
                        logger.error(
                            f"All retry attempts failed for {func.__name__}: {str(e)}"
                        )
                        raise
                        
                except Exception as e:
                    # Don't retry on non-connection errors
                    raise
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def log_vectordb_operations(
    log_level: int = logging.INFO,
    include_request_data: bool = False,
    include_response_data: bool = False
):
    """
    Decorator that logs VectorDB operations with configurable detail level.
    
    Args:
        log_level: Logging level to use
        include_request_data: Whether to include request data in logs
        include_response_data: Whether to include response data in logs
        
    Returns:
        Decorated function with logging
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Log function start
            logger.log(log_level, f"Starting VectorDB operation: {func.__name__}")
            
            if include_request_data:
                logger.log(log_level, f"Request data - args: {args}, kwargs: {kwargs}")
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.log(
                    log_level, 
                    f"VectorDB operation {func.__name__} completed "
                    f"successfully in {execution_time:.2f}s"
                )
                
                if include_response_data:
                    logger.log(log_level, f"Response data: {result}")
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.log(
                    logging.ERROR,
                    f"VectorDB operation {func.__name__} failed "
                    f"after {execution_time:.2f}s: {str(e)}"
                )
                raise
        
        return wrapper
    return decorator
