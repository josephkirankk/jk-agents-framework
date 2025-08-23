"""
Internal Logging Integration

This module integrates the internal LLM logging system with the existing
agent system by patching HTTP clients and providing context management.
"""

from __future__ import annotations
import logging
import functools
from typing import Dict, Any, Optional, Union, Callable
from contextlib import contextmanager
import uuid

# Import the internal logging components
from .internal_logger import get_internal_logger, LLMProvider
from .internal_logging_config import get_internal_logging_config
from .llm_interceptor import (
    get_intercepted_httpx_client,
    get_intercepted_async_httpx_client,
    set_agent_context_for_clients,
    wrap_aiohttp_session,
    InterceptedHttpxClient,
    InterceptedAsyncHttpxClient
)

log = logging.getLogger("internal_logging_integration")


class AgentLoggingContext:
    """Context manager for agent-specific logging."""
    
    def __init__(self, agent_name: str, user_input: str, correlation_id: Optional[str] = None):
        self.agent_name = agent_name
        self.user_input = user_input
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.internal_logger = get_internal_logger()
        
    def __enter__(self):
        """Enter the logging context."""
        # Set context for intercepted clients
        set_agent_context_for_clients(
            agent_name=self.agent_name,
            user_input=self.user_input,
            correlation_id=self.correlation_id
        )
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the logging context."""
        # Clear context for intercepted clients
        set_agent_context_for_clients("", "", None)


def with_internal_logging(agent_name: str, user_input: str, correlation_id: Optional[str] = None):
    """
    Decorator to add internal logging to agent functions.
    
    Usage:
        @with_internal_logging("my_agent", "user query")
        def my_agent_function():
            # Agent logic here
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with AgentLoggingContext(agent_name, user_input, correlation_id):
                return func(*args, **kwargs)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with AgentLoggingContext(agent_name, user_input, correlation_id):
                return await func(*args, **kwargs)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator


def patch_openai_clients():
    """Patch OpenAI clients to use intercepted HTTP clients."""
    try:
        # For now, skip complex patching and just log that we attempted it
        # The HTTP interception can be added later with more sophisticated approaches
        log.info("OpenAI client patching skipped - using manual logging approach")

    except Exception as e:
        log.error(f"Failed to patch OpenAI clients: {e}")


def patch_langchain_google_genai():
    """Patch LangChain Google GenAI clients for internal logging."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        import httpx
        
        # Store original method
        if not hasattr(ChatGoogleGenerativeAI, '_original_init'):
            ChatGoogleGenerativeAI._original_init = ChatGoogleGenerativeAI.__init__
        
        def patched_init(self, *args, **kwargs):
            # Call original init
            self._original_init(*args, **kwargs)
            
            # Replace HTTP client with intercepted version
            if hasattr(self, '_client') and hasattr(self._client, '_client'):
                if isinstance(self._client._client, httpx.Client):
                    self._client._client = get_intercepted_httpx_client()
                elif isinstance(self._client._client, httpx.AsyncClient):
                    self._client._client = get_intercepted_async_httpx_client()
        
        ChatGoogleGenerativeAI.__init__ = patched_init
        
        log.info("Successfully patched LangChain Google GenAI clients for internal logging")
        
    except ImportError:
        log.warning("LangChain Google GenAI library not available, skipping client patching")
    except Exception as e:
        log.error(f"Failed to patch LangChain Google GenAI clients: {e}")


def patch_aiohttp_sessions():
    """Patch aiohttp sessions used in MCP tools."""
    try:
        import aiohttp
        
        # Store original ClientSession
        if not hasattr(aiohttp, '_original_ClientSession'):
            aiohttp._original_ClientSession = aiohttp.ClientSession
        
        class InterceptedClientSession(aiohttp._original_ClientSession):
            """ClientSession with internal logging integration."""
            
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._intercepted_session = wrap_aiohttp_session(self)
            
            async def request(self, method, url, **kwargs):
                """Use intercepted session for requests."""
                return await self._intercepted_session.request(method, url, **kwargs)
        
        # Replace ClientSession with intercepted version
        aiohttp.ClientSession = InterceptedClientSession
        
        log.info("Successfully patched aiohttp ClientSession for internal logging")
        
    except ImportError:
        log.warning("aiohttp library not available, skipping session patching")
    except Exception as e:
        log.error(f"Failed to patch aiohttp sessions: {e}")


def initialize_internal_logging(config_file: Optional[str] = None):
    """
    Initialize the internal logging system and apply patches.
    
    Args:
        config_file: Optional path to configuration file
    """
    try:
        # Load configuration
        config = get_internal_logging_config(config_file)
        
        if not config.enabled:
            log.info("Internal LLM logging is disabled")
            return
        
        # Initialize logger
        internal_logger = get_internal_logger()
        
        # Apply patches to HTTP clients
        patch_openai_clients()
        patch_langchain_google_genai()
        patch_aiohttp_sessions()
        
        log.info(f"Internal LLM logging initialized successfully")
        log.info(f"Log directory: {config.log_directory}")
        log.info(f"Log level: {config.log_level.value}")
        log.info(f"Current log file: {internal_logger.get_current_log_file()}")
        
    except Exception as e:
        log.error(f"Failed to initialize internal logging: {e}")


def get_logging_stats() -> Dict[str, Any]:
    """Get statistics about the internal logging system."""
    try:
        internal_logger = get_internal_logger()
        config = get_internal_logging_config()
        
        stats = internal_logger.get_log_stats()
        stats.update({
            "config": {
                "enabled": config.enabled,
                "log_level": config.log_level.value,
                "max_file_size_mb": config.max_file_size_mb,
                "max_files": config.max_files,
                "compress_old_files": config.compress_old_files,
                "mask_sensitive_data": config.mask_sensitive_data
            }
        })
        
        return stats
        
    except Exception as e:
        log.error(f"Failed to get logging stats: {e}")
        return {"error": str(e)}


@contextmanager
def agent_logging_context(agent_name: str, user_input: str, correlation_id: Optional[str] = None):
    """
    Context manager for agent-specific logging.
    
    Usage:
        with agent_logging_context("my_agent", "user query") as ctx:
            # Agent logic here
            pass
    """
    with AgentLoggingContext(agent_name, user_input, correlation_id) as ctx:
        yield ctx


def log_agent_execution_start(agent_name: str, user_input: str, model: str, correlation_id: Optional[str] = None):
    """Log the start of agent execution."""
    try:
        internal_logger = get_internal_logger()
        
        # Create a manual log entry for agent execution start
        log_entry = {
            "log_type": "agent_execution_start",
            "timestamp": internal_logger._get_current_timestamp(),
            "agent_name": agent_name,
            "user_input": user_input,
            "model": model,
            "correlation_id": correlation_id or str(uuid.uuid4())
        }
        
        with internal_logger._lock:
            internal_logger._write_log_entry(log_entry)
            
    except Exception as e:
        log.error(f"Failed to log agent execution start: {e}")


def log_agent_execution_end(agent_name: str, success: bool, error_message: Optional[str] = None, correlation_id: Optional[str] = None):
    """Log the end of agent execution."""
    try:
        internal_logger = get_internal_logger()
        
        # Create a manual log entry for agent execution end
        log_entry = {
            "log_type": "agent_execution_end",
            "timestamp": internal_logger._get_current_timestamp(),
            "agent_name": agent_name,
            "success": success,
            "error_message": error_message,
            "correlation_id": correlation_id
        }
        
        with internal_logger._lock:
            internal_logger._write_log_entry(log_entry)
            
    except Exception as e:
        log.error(f"Failed to log agent execution end: {e}")


# Auto-initialize when module is imported
try:
    initialize_internal_logging()
except Exception as e:
    log.warning(f"Auto-initialization of internal logging failed: {e}")
