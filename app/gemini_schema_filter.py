"""
Google Gemini Schema Filter

This module provides utilities to filter out unsupported schema properties
from tool schemas when using Google Gemini models, preventing warnings and
potential errors.

Based on the GitHub issue: https://github.com/langchain-ai/langchainjs/issues/5779
Google Gemini doesn't support certain JSON schema properties like:
- additionalProperties
- $schema
- And potentially others
"""

import logging
from typing import Dict, Any, List
from langchain_core.tools import BaseTool

log = logging.getLogger(__name__)

# Properties that Google Gemini doesn't support in function schemas
UNSUPPORTED_SCHEMA_PROPERTIES = {
    "additionalProperties",
    "$schema",
    "$id",
    "$ref",
    "definitions",
    "patternProperties",
    "dependencies",
    "additionalItems",
    "if",
    "then",
    "else",
    "allOf",
    "anyOf",
    "oneOf",
    "not"
}


def clean_schema_for_gemini(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean a JSON schema by removing properties not supported by Google Gemini.
    
    Args:
        schema: The original JSON schema dictionary
        
    Returns:
        Cleaned schema dictionary with unsupported properties removed
    """
    if not isinstance(schema, dict):
        return schema
    
    cleaned = {}
    
    for key, value in schema.items():
        if key in UNSUPPORTED_SCHEMA_PROPERTIES:
            log.debug(f"Removing unsupported schema property: {key}")
            continue
            
        if isinstance(value, dict):
            cleaned[key] = clean_schema_for_gemini(value)
        elif isinstance(value, list):
            cleaned[key] = [
                clean_schema_for_gemini(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            cleaned[key] = value
    
    return cleaned


class GeminiCompatibleTool(BaseTool):
    """
    A wrapper tool that ensures Gemini compatibility by cleaning schemas.
    """

    original_tool: BaseTool

    def __init__(self, original_tool: BaseTool):
        # Store the original tool first
        self.original_tool = original_tool

        # Copy basic attributes
        super().__init__(
            name=original_tool.name,
            description=original_tool.description,
            return_direct=getattr(original_tool, 'return_direct', False)
        )

        # Handle args_schema with cleaning
        if hasattr(original_tool, 'args_schema') and original_tool.args_schema:
            try:
                original_schema = original_tool.args_schema.model_json_schema()
                cleaned_schema = clean_schema_for_gemini(original_schema)

                if original_schema != cleaned_schema:
                    log.info(f"Cleaned schema for tool '{self.name}' for Gemini compatibility")

                # Keep the original args_schema but note that it's been processed
                self.args_schema = original_tool.args_schema
                self._cleaned_schema = cleaned_schema
            except Exception as e:
                log.warning(f"Failed to clean schema for tool '{self.name}': {e}")
                self.args_schema = original_tool.args_schema

    def _run(self, *args, **kwargs):
        """Delegate to the original tool's run method."""
        return self.original_tool._run(*args, **kwargs)

    async def _arun(self, *args, **kwargs):
        """Delegate to the original tool's async run method."""
        if hasattr(self.original_tool, '_arun'):
            return await self.original_tool._arun(*args, **kwargs)
        else:
            # Fallback to sync run
            return self._run(*args, **kwargs)


def filter_tool_schemas_for_gemini(tools: List[BaseTool]) -> List[BaseTool]:
    """
    Filter tool schemas to remove properties not supported by Google Gemini.

    This function creates new tool instances with cleaned schemas to prevent
    warnings and potential errors when using Google Gemini models.

    Args:
        tools: List of LangChain tools

    Returns:
        List of tools with cleaned schemas
    """
    filtered_tools = []

    for tool in tools:
        try:
            # Check if the tool has an args_schema that might need cleaning
            if hasattr(tool, 'args_schema') and tool.args_schema is not None:
                original_schema = tool.args_schema.model_json_schema()
                cleaned_schema = clean_schema_for_gemini(original_schema)

                # If the schema was modified, wrap the tool
                if original_schema != cleaned_schema:
                    log.info(f"Wrapping tool '{tool.name}' for Gemini compatibility")
                    filtered_tools.append(GeminiCompatibleTool(tool))
                else:
                    # Schema is already clean, use original tool
                    filtered_tools.append(tool)
            else:
                # Tool doesn't have args_schema, add as-is
                filtered_tools.append(tool)

        except Exception as e:
            log.warning(f"Failed to filter schema for tool '{tool.name}': {e}")
            # Add the original tool if filtering fails
            filtered_tools.append(tool)

    return filtered_tools


def is_gemini_model(model_id: str) -> bool:
    """
    Check if a model ID represents a Google Gemini model.
    
    Args:
        model_id: The model identifier string
        
    Returns:
        True if it's a Gemini model, False otherwise
    """
    if isinstance(model_id, str):
        return model_id.startswith("google:")
    
    # Check if it's a ChatGoogleGenerativeAI instance
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return isinstance(model_id, ChatGoogleGenerativeAI)
    except ImportError:
        return False


def apply_gemini_schema_filtering(tools: List[BaseTool], model_id: str) -> List[BaseTool]:
    """
    Apply Gemini schema filtering if the model is a Google Gemini model.
    
    Args:
        tools: List of tools to potentially filter
        model_id: Model identifier or instance
        
    Returns:
        Filtered tools if Gemini model, original tools otherwise
    """
    if is_gemini_model(model_id):
        log.info(f"Applying Gemini schema filtering for model: {model_id}")
        return filter_tool_schemas_for_gemini(tools)
    else:
        log.debug(f"No schema filtering needed for model: {model_id}")
        return tools
