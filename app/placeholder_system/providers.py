"""
Placeholder providers for the JK-Agents framework.

This module contains the base PlaceholderProvider class and built-in providers
for system, agent, context, and user-defined placeholders.
"""

from __future__ import annotations
import logging
import os
import platform
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, Set, Optional, List
from pathlib import Path

try:
    from .exceptions import PlaceholderProviderError
except ImportError:
    from exceptions import PlaceholderProviderError

log = logging.getLogger("placeholder_providers")


class PlaceholderProvider(ABC):
    """
    Abstract base class for placeholder providers.
    
    Providers are responsible for resolving specific types of placeholders
    and can be registered with the PlaceholderRegistry.
    """
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the name of this provider."""
        pass
    
    @abstractmethod
    def get_supported_placeholders(self) -> Set[str]:
        """Get the set of placeholder names this provider supports."""
        pass
    
    @abstractmethod
    def can_provide(self, placeholder_name: str) -> bool:
        """Check if this provider can provide the given placeholder."""
        pass
    
    @abstractmethod
    def get_placeholder_value(self, placeholder_name: str, context: Dict[str, Any]) -> Any:
        """
        Get the value for a placeholder.
        
        Args:
            placeholder_name: Name of the placeholder
            context: Context data for resolution
            
        Returns:
            The placeholder value
            
        Raises:
            PlaceholderProviderError: If the provider cannot resolve the placeholder
        """
        pass
    
    def get_placeholder_documentation(self, placeholder_name: str) -> Optional[str]:
        """
        Get documentation for a specific placeholder.
        
        Args:
            placeholder_name: Name of the placeholder
            
        Returns:
            Documentation string or None if not available
        """
        return None
    
    def validate_context(self, context: Dict[str, Any]) -> bool:
        """
        Validate that the context contains required data for this provider.
        
        Args:
            context: Context data to validate
            
        Returns:
            True if context is valid, False otherwise
        """
        return True


class SystemPlaceholderProvider(PlaceholderProvider):
    """Provider for system-level placeholders like timestamps, platform info, etc."""
    
    def get_name(self) -> str:
        return "system"
    
    def get_supported_placeholders(self) -> Set[str]:
        return {
            # Core datetime placeholders
            "timestamp",
            "datetime",  # ISO format with timezone
            "datetime_local",  # Local timezone ISO format
            "datetime_utc",  # UTC timezone ISO format
            "date",
            "time", 
            "time_24h",  # 24-hour format
            "time_12h",  # 12-hour format with AM/PM
            
            # Formatted datetime options
            "date_iso",     # ISO date: 2025-09-24
            "date_us",      # US format: 09/24/2025
            "date_eu",      # EU format: 24/09/2025
            "date_long",    # Long format: September 24, 2025
            "date_short",   # Short format: Sep 24, 2025
            
            # Timestamp variants
            "timestamp_unix",  # Unix timestamp
            "timestamp_ms",    # Milliseconds since epoch
            
            # Day/Week/Month/Year components
            "year",
            "month",
            "month_name",
            "month_short",
            "day",
            "day_name",
            "day_short",
            "week_number",
            "quarter",
            
            # System info
            "platform",
            "python_version",
            "working_directory",
            "user_home",
            "hostname",
        }
    
    def can_provide(self, placeholder_name: str) -> bool:
        return placeholder_name in self.get_supported_placeholders()
    
    def get_placeholder_value(self, placeholder_name: str, context: Dict[str, Any]) -> Any:
        try:
            now = datetime.now()
            
            # Core datetime placeholders
            if placeholder_name == "timestamp":
                return now.isoformat()
            elif placeholder_name == "datetime":
                return now.astimezone().isoformat()  # With timezone
            elif placeholder_name == "datetime_local":
                return now.astimezone().isoformat()
            elif placeholder_name == "datetime_utc":
                return datetime.now(timezone.utc).isoformat()
            elif placeholder_name == "date":
                return now.strftime("%Y-%m-%d")
            elif placeholder_name == "time":
                return now.strftime("%H:%M:%S")
            elif placeholder_name == "time_24h":
                return now.strftime("%H:%M:%S")
            elif placeholder_name == "time_12h":
                return now.strftime("%I:%M:%S %p")
                
            # Formatted date options
            elif placeholder_name == "date_iso":
                return now.strftime("%Y-%m-%d")
            elif placeholder_name == "date_us":
                return now.strftime("%m/%d/%Y")
            elif placeholder_name == "date_eu":
                return now.strftime("%d/%m/%Y")
            elif placeholder_name == "date_long":
                return now.strftime("%B %d, %Y")
            elif placeholder_name == "date_short":
                return now.strftime("%b %d, %Y")
                
            # Timestamp variants
            elif placeholder_name == "timestamp_unix":
                return int(now.timestamp())
            elif placeholder_name == "timestamp_ms":
                return int(now.timestamp() * 1000)
                
            # Date/time components
            elif placeholder_name == "year":
                return now.year
            elif placeholder_name == "month":
                return now.month
            elif placeholder_name == "month_name":
                return now.strftime("%B")
            elif placeholder_name == "month_short":
                return now.strftime("%b")
            elif placeholder_name == "day":
                return now.day
            elif placeholder_name == "day_name":
                return now.strftime("%A")
            elif placeholder_name == "day_short":
                return now.strftime("%a")
            elif placeholder_name == "week_number":
                return now.isocalendar()[1]
            elif placeholder_name == "quarter":
                return (now.month - 1) // 3 + 1
                
            # System info
            elif placeholder_name == "platform":
                return platform.system()
            elif placeholder_name == "python_version":
                return platform.python_version()
            elif placeholder_name == "working_directory":
                return str(Path.cwd())
            elif placeholder_name == "user_home":
                return str(Path.home())
            elif placeholder_name == "hostname":
                return platform.node()
            else:
                raise PlaceholderProviderError(
                    self.get_name(),
                    f"Unsupported placeholder: {placeholder_name}",
                    placeholder_name
                )
        except Exception as e:
            raise PlaceholderProviderError(
                self.get_name(),
                f"Failed to resolve {placeholder_name}: {str(e)}",
                placeholder_name
            )
    
    def get_placeholder_documentation(self, placeholder_name: str) -> Optional[str]:
        docs = {
            # Core datetime placeholders
            "timestamp": "Current timestamp in ISO format (YYYY-MM-DDTHH:MM:SS)",
            "datetime": "Current datetime with timezone in ISO format",
            "datetime_local": "Current datetime in local timezone ISO format",
            "datetime_utc": "Current datetime in UTC timezone ISO format",
            "date": "Current date in YYYY-MM-DD format",
            "time": "Current time in HH:MM:SS format (24-hour)",
            "time_24h": "Current time in 24-hour format (HH:MM:SS)",
            "time_12h": "Current time in 12-hour format with AM/PM",
            
            # Formatted date options
            "date_iso": "Current date in ISO format (YYYY-MM-DD)",
            "date_us": "Current date in US format (MM/DD/YYYY)",
            "date_eu": "Current date in European format (DD/MM/YYYY)",
            "date_long": "Current date in long format (e.g., 'September 24, 2025')",
            "date_short": "Current date in short format (e.g., 'Sep 24, 2025')",
            
            # Timestamp variants
            "timestamp_unix": "Current Unix timestamp (seconds since epoch)",
            "timestamp_ms": "Current timestamp in milliseconds since epoch",
            
            # Date/time components
            "year": "Current year as integer",
            "month": "Current month as integer (1-12)",
            "month_name": "Current month full name (e.g., 'September')",
            "month_short": "Current month short name (e.g., 'Sep')",
            "day": "Current day of month as integer",
            "day_name": "Current day full name (e.g., 'Tuesday')",
            "day_short": "Current day short name (e.g., 'Tue')",
            "week_number": "Current ISO week number (1-53)",
            "quarter": "Current quarter of the year (1-4)",
            
            # System info
            "platform": "Operating system platform (Windows, Darwin, Linux, etc.)",
            "python_version": "Python version string",
            "working_directory": "Current working directory path",
            "user_home": "User home directory path",
            "hostname": "System hostname",
        }
        return docs.get(placeholder_name)


class AgentPlaceholderProvider(PlaceholderProvider):
    """Provider for agent-specific placeholders."""
    
    def get_name(self) -> str:
        return "agent"
    
    def get_supported_placeholders(self) -> Set[str]:
        return {
            "agent_name",
            "agent_description",
            "agent_model",
            "mcpservers",
        }
    
    def can_provide(self, placeholder_name: str) -> bool:
        return placeholder_name in self.get_supported_placeholders()
    
    def get_placeholder_value(self, placeholder_name: str, context: Dict[str, Any]) -> Any:
        try:
            if placeholder_name == "agent_name":
                return context.get("agent_name", "")
            elif placeholder_name == "agent_description":
                return context.get("agent_description", "")
            elif placeholder_name == "agent_model":
                return context.get("agent_model", "")
            elif placeholder_name == "mcpservers":
                return context.get("mcpservers", "(no MCP servers configured)")
            else:
                raise PlaceholderProviderError(
                    self.get_name(),
                    f"Unsupported placeholder: {placeholder_name}",
                    placeholder_name
                )
        except Exception as e:
            raise PlaceholderProviderError(
                self.get_name(),
                f"Failed to resolve {placeholder_name}: {str(e)}",
                placeholder_name
            )
    
    def get_placeholder_documentation(self, placeholder_name: str) -> Optional[str]:
        docs = {
            "agent_name": "Name of the current agent",
            "agent_description": "Description of the current agent",
            "agent_model": "Model used by the current agent",
            "mcpservers": "Summary of available MCP servers for the agent",
        }
        return docs.get(placeholder_name)


class ContextPlaceholderProvider(PlaceholderProvider):
    """Provider for context-specific placeholders."""
    
    def get_name(self) -> str:
        return "context"
    
    def get_supported_placeholders(self) -> Set[str]:
        return {
            "business_context",
            "businessContext",  # Backward compatibility
            "original_user_question",
            "dependent_request_responses",
            "agents",
        }
    
    def can_provide(self, placeholder_name: str) -> bool:
        return placeholder_name in self.get_supported_placeholders()
    
    def get_placeholder_value(self, placeholder_name: str, context: Dict[str, Any]) -> Any:
        try:
            if placeholder_name in ("business_context", "businessContext"):
                return context.get("business_context", "")
            elif placeholder_name == "original_user_question":
                return context.get("original_user_question", "")
            elif placeholder_name == "dependent_request_responses":
                return context.get("dependent_request_responses", "")
            elif placeholder_name == "agents":
                return context.get("agents", "")
            else:
                raise PlaceholderProviderError(
                    self.get_name(),
                    f"Unsupported placeholder: {placeholder_name}",
                    placeholder_name
                )
        except Exception as e:
            raise PlaceholderProviderError(
                self.get_name(),
                f"Failed to resolve {placeholder_name}: {str(e)}",
                placeholder_name
            )
    
    def get_placeholder_documentation(self, placeholder_name: str) -> Optional[str]:
        docs = {
            "business_context": "Business context for the current session",
            "businessContext": "Business context for the current session (legacy)",
            "original_user_question": "The original question asked by the user",
            "dependent_request_responses": "Responses from previous agent steps",
            "agents": "List of available agents (for supervisor)",
        }
        return docs.get(placeholder_name)


class UserPlaceholderProvider(PlaceholderProvider):
    """Provider for user-defined custom placeholders."""
    
    def __init__(self):
        super().__init__()
        self._custom_placeholders: Dict[str, Any] = {}
    
    def get_name(self) -> str:
        return "user"
    
    def get_supported_placeholders(self) -> Set[str]:
        return set(self._custom_placeholders.keys())
    
    def can_provide(self, placeholder_name: str) -> bool:
        return placeholder_name in self._custom_placeholders
    
    def get_placeholder_value(self, placeholder_name: str, context: Dict[str, Any]) -> Any:
        if placeholder_name in self._custom_placeholders:
            value = self._custom_placeholders[placeholder_name]
            # If value is callable, call it with context
            if callable(value):
                try:
                    return value(context)
                except Exception as e:
                    raise PlaceholderProviderError(
                        self.get_name(),
                        f"Custom placeholder function failed: {str(e)}",
                        placeholder_name
                    )
            return value
        else:
            raise PlaceholderProviderError(
                self.get_name(),
                f"Custom placeholder not found: {placeholder_name}",
                placeholder_name
            )
    
    def add_placeholder(self, name: str, value: Any, documentation: Optional[str] = None) -> None:
        """
        Add a custom placeholder.
        
        Args:
            name: Placeholder name
            value: Placeholder value (can be callable)
            documentation: Optional documentation string
        """
        self._custom_placeholders[name] = value
        if documentation:
            self._documentation = getattr(self, '_documentation', {})
            self._documentation[name] = documentation
        log.debug(f"Added custom placeholder: {name}")
    
    def remove_placeholder(self, name: str) -> None:
        """Remove a custom placeholder."""
        if name in self._custom_placeholders:
            del self._custom_placeholders[name]
            if hasattr(self, '_documentation') and name in self._documentation:
                del self._documentation[name]
            log.debug(f"Removed custom placeholder: {name}")
    
    def clear_placeholders(self) -> None:
        """Clear all custom placeholders."""
        self._custom_placeholders.clear()
        if hasattr(self, '_documentation'):
            self._documentation.clear()
        log.debug("Cleared all custom placeholders")
    
    def get_placeholder_documentation(self, placeholder_name: str) -> Optional[str]:
        if hasattr(self, '_documentation'):
            return self._documentation.get(placeholder_name)
        return f"Custom user-defined placeholder: {placeholder_name}"
