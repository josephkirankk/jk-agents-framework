# Python Function Tools Integration Guide

This guide explains how to add and use Python function-based tools in your JK Agents system using the latest LangChain patterns.

## Overview

Python function tools allow you to integrate custom Python functions directly into your agent workflows. These tools are defined using LangChain's `@tool` decorator and `BaseTool` class, providing seamless integration with your existing agent system.

## Key Features

- **Easy Integration**: Define tools using simple Python functions with decorators
- **Type Safety**: Full support for type hints and Pydantic schemas
- **Async Support**: Both synchronous and asynchronous tool execution
- **Flexible Loading**: Load specific tools or entire tool sets from modules
- **YAML Configuration**: Configure tools directly in your agent YAML files

## Tool Definition Patterns

### 1. Simple Function Tools with @tool Decorator

```python
from langchain_core.tools import tool

@tool
def calculate_percentage(value: float, total: float) -> float:
    """Calculate percentage of value relative to total.

    Args:
        value: The value to calculate percentage for
        total: The total value to calculate percentage against

    Returns:
        The percentage as a float (e.g., 25.5 for 25.5%)
    """
    if total == 0:
        return 0.0
    return (value / total) * 100
```

### 2. Advanced Tools with Custom Schemas

```python
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class DataAnalysisInput(BaseModel):
    """Input schema for data analysis tool."""
    data: List[float] = Field(description="List of numerical data points")
    analysis_type: str = Field(
        description="Type of analysis: 'basic', 'statistical', or 'advanced'",
        default="basic"
    )

@tool("data_analyzer", args_schema=DataAnalysisInput, return_direct=False)
def analyze_data(data: List[float], analysis_type: str = "basic") -> Dict[str, Any]:
    """Perform statistical analysis on numerical data."""
    # Implementation here
    pass
```

### 3. Class-Based Tools with BaseTool

```python
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class TextProcessorInput(BaseModel):
    """Input schema for text processor tool."""
    text: str = Field(description="Text to process")
    operation: str = Field(description="Operation to perform")

class TextProcessorTool(BaseTool):
    """Advanced text processing tool with multiple operations."""
    
    name: str = "text_processor"
    description: str = "Process text with various operations"
    args_schema: Optional[type] = TextProcessorInput
    
    def _run(self, text: str, operation: str) -> Dict[str, Any]:
        """Execute the text processing operation."""
        # Implementation here
        pass
```

## YAML Configuration

### Basic Configuration

Add Python function tools to your agent configuration:

```yaml
agents:
  - name: "my_agent"
    description: "Agent with Python function tools"
    model: "google:gemini-2.0-flash-exp"
    prompt: |
      You are a helpful assistant with access to Python function tools.
      Use these tools to help users with calculations and data analysis.
    python_tools:
      business_tools:
        module_path: "tools.python_function_tools"
        tool_names: ["calculate_percentage", "format_currency"]
        description: "Business calculation tools"
      data_tools:
        module_path: "tools.python_function_tools"
        tool_names: ["data_analyzer", "generate_random_data"]
        description: "Data analysis tools"
```

### Advanced Configuration Options

```yaml
python_tools:
  # Load specific tools by name
  specific_tools:
    module_path: "tools.python_function_tools"
    tool_names: ["calculate_percentage", "format_currency"]
    description: "Specific business tools"
  
  # Load a single function
  single_function:
    module_path: "tools.python_function_tools"
    function_name: "analyze_data"
    description: "Data analysis function"
  
  # Load all tools from module
  all_tools:
    module_path: "tools.python_function_tools"
    description: "All available tools"
```

## Creating Your Own Tool Module

### 1. Create the Module File

Create a new Python file (e.g., `tools/my_custom_tools.py`):

```python
"""
My Custom Tools Module
"""

from langchain_core.tools import tool, BaseTool
from typing import List, Dict, Any
from pydantic import BaseModel, Field

@tool
def my_custom_function(input_text: str) -> str:
    """My custom function that processes text.
    
    Args:
        input_text: Text to process
        
    Returns:
        Processed text
    """
    return f"Processed: {input_text.upper()}"

# Tool registry for easy loading
TOOL_REGISTRY = {
    "my_custom_function": my_custom_function,
}

def get_all_function_tools():
    """Get all tools from this module."""
    return list(TOOL_REGISTRY.values())

def load_tools_from_config(tool_names: List[str]):
    """Load specific tools by name."""
    return [TOOL_REGISTRY[name] for name in tool_names if name in TOOL_REGISTRY]
```

### 2. Update Your YAML Configuration

```yaml
python_tools:
  my_tools:
    module_path: "tools.my_custom_tools"
    tool_names: ["my_custom_function"]
    description: "My custom tools"
```

## Testing Your Tools

### 1. Run the Test Script

```bash
python test_python_tools.py
```

### 2. Test Individual Tools

```python
from tools.python_function_tools import calculate_percentage

# Test the tool
result = calculate_percentage.invoke({"value": 25, "total": 100})
print(f"Result: {result}")  # Output: Result: 25.0
```

### 3. Test with Agent

```bash
python -m app.main --config config/gemba_agents_v1.yaml --agent python_function_demo_agent --input "Calculate 30% of 150"
```

## Best Practices

### 1. Tool Design
- Use clear, descriptive function names
- Include comprehensive docstrings
- Add proper type hints for all parameters
- Handle edge cases and errors gracefully

### 2. Schema Definition
- Use Pydantic models for complex input schemas
- Provide clear field descriptions
- Set appropriate default values
- Validate input data

### 3. Error Handling
- Return meaningful error messages
- Use try-catch blocks for external operations
- Provide fallback values when appropriate

### 4. Performance
- Keep tool functions lightweight
- Use async functions for I/O operations
- Cache results when appropriate
- Avoid blocking operations

## Integration with Existing System

The Python function tools integrate seamlessly with your existing:

- **MCP Servers**: Python tools work alongside MCP servers
- **HTTP Tools**: Combine with HTTP-based tools
- **Agent Workflows**: Use in multi-agent scenarios
- **Prompt Templates**: Reference tools in agent prompts

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure your tool modules are in the Python path
2. **Schema Validation**: Check that input schemas match function signatures
3. **Tool Registration**: Verify tools are properly registered in TOOL_REGISTRY
4. **YAML Syntax**: Validate YAML configuration syntax

### Debug Mode

Enable debug logging to see tool loading details:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Examples

See the complete working examples in:
- `tools/python_function_tools.py` - Example tool implementations
- `config/gemba_agents_v1.yaml` - YAML configuration examples
- `test_python_tools.py` - Testing examples

## Next Steps

1. Create your own custom tool modules
2. Test tools individually before integration
3. Update your agent configurations
4. Test the complete agent workflow
5. Monitor tool performance and usage
