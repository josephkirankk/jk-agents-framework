"""
Configuration placeholder provider for runtime/config variables.

This module provides a placeholder provider that loads configuration variables
from YAML files, enabling multi-environment setups and runtime variable injection.
"""

from __future__ import annotations
import logging
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Set, Optional
from .providers import PlaceholderProvider
from .exceptions import PlaceholderProviderError

log = logging.getLogger("config_provider")


class ConfigPlaceholderProvider(PlaceholderProvider):
    """Provider for configuration-based placeholders loaded from YAML files."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the config provider.
        
        Args:
            config_dir: Directory to search for config files (defaults to config/)
        """
        self._config_dir = config_dir or Path("config")
        self._config_vars: Dict[str, Any] = {}
        self._loaded_files: Set[str] = set()
        self._load_config_variables()
    
    def _load_config_variables(self) -> None:
        """Load configuration variables from YAML files."""
        if not self._config_dir.exists():
            log.warning(f"Config directory not found: {self._config_dir}")
            return
        
        # Load variables from standard config files
        config_files = [
            "vars.yaml",
            "vars.local.yaml", 
            "variables.yaml",
            "variables.local.yaml",
            "config.vars.yaml"
        ]
        
        for config_file in config_files:
            config_path = self._config_dir / config_file
            if config_path.exists():
                self._load_yaml_file(config_path)
        
        # Also check for environment-specific config files
        env = os.getenv("ENVIRONMENT", os.getenv("ENV", ""))
        if env:
            env_config_file = f"vars.{env}.yaml"
            env_config_path = self._config_dir / env_config_file
            if env_config_path.exists():
                self._load_yaml_file(env_config_path)
    
    def _load_yaml_file(self, file_path: Path) -> None:
        """Load variables from a YAML file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            
            if isinstance(data, dict):
                self._config_vars.update(data)
                self._loaded_files.add(str(file_path))
                log.debug(f"Loaded {len(data)} config variables from {file_path}")
            else:
                log.warning(f"Config file {file_path} does not contain a valid dictionary")
                
        except Exception as e:
            log.error(f"Failed to load config file {file_path}: {e}")
    
    def get_name(self) -> str:
        return "config"
    
    def get_supported_placeholders(self) -> Set[str]:
        """Get all available configuration placeholders."""
        return set(self._config_vars.keys())
    
    def can_provide(self, placeholder_name: str) -> bool:
        """Check if this provider can provide the given placeholder."""
        return placeholder_name in self._config_vars
    
    def get_placeholder_value(self, placeholder_name: str, context: Dict[str, Any]) -> Any:
        """
        Get the value for a configuration placeholder.
        
        Args:
            placeholder_name: Name of the placeholder
            context: Context data for resolution
            
        Returns:
            The placeholder value
            
        Raises:
            PlaceholderProviderError: If the provider cannot resolve the placeholder
        """
        if placeholder_name in self._config_vars:
            value = self._config_vars[placeholder_name]
            
            # If value is a callable, call it with context
            if callable(value):
                try:
                    return value(context)
                except Exception as e:
                    raise PlaceholderProviderError(
                        self.get_name(),
                        f"Config placeholder function failed: {str(e)}",
                        placeholder_name
                    )
            
            return value
        else:
            raise PlaceholderProviderError(
                self.get_name(),
                f"Config placeholder not found: {placeholder_name}",
                placeholder_name
            )
    
    def get_placeholder_documentation(self, placeholder_name: str) -> Optional[str]:
        """Get documentation for a specific placeholder."""
        if placeholder_name in self._config_vars:
            return f"Configuration variable: {placeholder_name} (loaded from {', '.join(self._loaded_files)})"
        return None
    
    def reload_config(self) -> None:
        """Reload configuration variables from files."""
        old_count = len(self._config_vars)
        self._config_vars.clear()
        self._loaded_files.clear()
        self._load_config_variables()
        new_count = len(self._config_vars)
        log.info(f"Reloaded config variables: {old_count} -> {new_count}")
    
    def add_config_variable(self, name: str, value: Any) -> None:
        """Add a configuration variable at runtime."""
        self._config_vars[name] = value
        log.debug(f"Added runtime config variable: {name}")
    
    def get_loaded_files(self) -> Set[str]:
        """Get the list of loaded configuration files."""
        return self._loaded_files.copy()
    
    def get_all_variables(self) -> Dict[str, Any]:
        """Get all loaded configuration variables."""
        return self._config_vars.copy()


# Integration function for the existing registry
def register_config_provider(registry=None) -> ConfigPlaceholderProvider:
    """
    Register the config provider with the default registry.
    
    Args:
        registry: Optional custom registry, uses default if None
        
    Returns:
        The registered ConfigPlaceholderProvider instance
    """
    if registry is None:
        from .registry import get_default_registry
        registry = get_default_registry()
    
    config_provider = ConfigPlaceholderProvider()
    registry.register_provider(config_provider)
    
    log.info(f"Registered config provider with {len(config_provider.get_supported_placeholders())} variables")
    return config_provider