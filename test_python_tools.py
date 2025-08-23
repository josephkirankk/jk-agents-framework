#!/usr/bin/env python3
"""
Test script for Python function tools integration
================================================

This script demonstrates how to test the Python function tools
integration with the JK Agents system.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tools.python_function_tools import (
    get_all_function_tools,
    load_tools_from_config,
    TOOL_REGISTRY
)
from app.python_tool_loader import load_python_function_tools, validate_python_tools


def test_individual_tools():
    """Test individual Python function tools."""
    print("=" * 60)
    print("Testing Individual Python Function Tools")
    print("=" * 60)
    
    # Test calculate_percentage
    from tools.python_function_tools import calculate_percentage
    result = calculate_percentage.invoke({"value": 25, "total": 100})
    print(f"calculate_percentage(25, 100) = {result}")
    
    # Test format_currency
    from tools.python_function_tools import format_currency
    result = format_currency.invoke({"amount": 1234.56, "currency": "USD"})
    print(f"format_currency(1234.56, 'USD') = {result}")
    
    # Test generate_random_data
    from tools.python_function_tools import generate_random_data
    result = generate_random_data.invoke({"size": 5, "min_val": 1, "max_val": 10})
    print(f"generate_random_data(5, 1, 10) = {result}")
    
    # Test data_analyzer
    from tools.python_function_tools import analyze_data
    test_data = [1.0, 2.0, 3.0, 4.0, 5.0, 100.0]  # Include outlier
    result = analyze_data.invoke({
        "data": test_data, 
        "analysis_type": "advanced"
    })
    print(f"analyze_data({test_data}, 'advanced') = {result}")
    
    # Test text_processor
    from tools.python_function_tools import TextProcessorTool
    text_tool = TextProcessorTool()
    result = text_tool.invoke({
        "text": "Hello world! This is a test sentence.", 
        "operation": "word_count"
    })
    print(f"text_processor word_count = {result}")


def test_tool_registry():
    """Test the tool registry functionality."""
    print("\n" + "=" * 60)
    print("Testing Tool Registry")
    print("=" * 60)
    
    print(f"Available tools in registry: {list(TOOL_REGISTRY.keys())}")
    
    # Test loading specific tools
    specific_tools = load_tools_from_config([
        "calculate_percentage", 
        "format_currency", 
        "data_analyzer"
    ])
    print(f"Loaded {len(specific_tools)} specific tools")
    for tool in specific_tools:
        print(f"  - {tool.name}: {tool.description}")


def test_module_loading():
    """Test loading tools through the module loader."""
    print("\n" + "=" * 60)
    print("Testing Module Loading")
    print("=" * 60)
    
    # Test configuration similar to YAML
    config = {
        "business_tools": {
            "module_path": "tools.python_function_tools",
            "tool_names": ["calculate_percentage", "format_currency"],
            "description": "Business calculation tools"
        },
        "data_tools": {
            "module_path": "tools.python_function_tools", 
            "tool_names": ["data_analyzer", "generate_random_data"],
            "description": "Data analysis tools"
        }
    }
    
    tools = load_python_function_tools(config)
    validated_tools = validate_python_tools(tools)
    
    print(f"Loaded {len(validated_tools)} tools from configuration")
    for tool in validated_tools:
        print(f"  - {tool.name}: {tool.description}")


def test_all_tools():
    """Test getting all tools from the module."""
    print("\n" + "=" * 60)
    print("Testing All Tools Loading")
    print("=" * 60)
    
    all_tools = get_all_function_tools()
    print(f"Found {len(all_tools)} total tools:")
    
    for tool in all_tools:
        print(f"  - {tool.name}: {tool.description}")
        
        # Test tool attributes
        if hasattr(tool, 'args'):
            print(f"    Args schema: {tool.args}")


def test_tool_invocation():
    """Test invoking tools with different input formats."""
    print("\n" + "=" * 60)
    print("Testing Tool Invocation Formats")
    print("=" * 60)
    
    from tools.python_function_tools import calculate_percentage
    
    # Test with dict input
    result1 = calculate_percentage.invoke({"value": 50, "total": 200})
    print(f"Dict input: {result1}")
    
    # Test with ToolCall format (simulating model output)
    tool_call = {
        "name": "calculate_percentage",
        "args": {"value": 75, "total": 300},
        "id": "test_call_1",
        "type": "tool_call"
    }
    result2 = calculate_percentage.invoke(tool_call)
    print(f"ToolCall input: {result2}")


async def test_async_functionality():
    """Test async functionality if available."""
    print("\n" + "=" * 60)
    print("Testing Async Functionality")
    print("=" * 60)
    
    from tools.python_function_tools import calculate_percentage
    
    # Test async invocation
    try:
        result = await calculate_percentage.ainvoke({"value": 30, "total": 120})
        print(f"Async invocation result: {result}")
    except Exception as e:
        print(f"Async invocation failed: {e}")


def main():
    """Run all tests."""
    print("Python Function Tools Integration Test")
    print("=" * 60)
    
    try:
        # Run synchronous tests
        test_individual_tools()
        test_tool_registry()
        test_module_loading()
        test_all_tools()
        test_tool_invocation()
        
        # Run async tests
        asyncio.run(test_async_functionality())
        
        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
