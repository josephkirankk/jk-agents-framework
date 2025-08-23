"""
Python Function Tools for JK Agents
===================================

This module contains custom Python function tools that can be integrated
with the agent system through YAML configuration.

Each function is designed to be used as a LangChain tool with proper
type hints, docstrings, and error handling following the latest patterns.
"""

import json
import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel, Field

# Import LangChain tool decorators and base classes
from langchain_core.tools import tool, BaseTool


# =============================================================================
# Simple Function Tools using @tool decorator
# =============================================================================

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


@tool
def generate_random_data(
    size: int, min_val: int = 0, max_val: int = 100
) -> List[int]:
    """Generate a list of random integers.

    Args:
        size: Number of random integers to generate
        min_val: Minimum value for random integers (default: 0)
        max_val: Maximum value for random integers (default: 100)

    Returns:
        List of random integers
    """
    if size <= 0:
        return []
    return [random.randint(min_val, max_val) for _ in range(size)]


@tool
def format_currency(amount: float, currency: str = "USD") -> str:
    """Format a number as currency.

    Args:
        amount: The amount to format
        currency: Currency code (default: USD)

    Returns:
        Formatted currency string
    """
    return f"{currency} {amount:,.2f}"


@tool
def calculate_business_days(start_date: str, end_date: str) -> int:
    """Calculate number of business days between two dates.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        Number of business days
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        # Calculate business days (excluding weekends)
        business_days = 0
        current = start
        while current <= end:
            if current.weekday() < 5:  # Monday = 0, Sunday = 6
                business_days += 1
            current += timedelta(days=1)

        return business_days
    except ValueError:
        return -1  # Invalid date format


# =============================================================================
# Advanced Function Tools with Custom Schemas
# =============================================================================

class DataAnalysisInput(BaseModel):
    """Input schema for data analysis tool."""
    data: List[float] = Field(description="List of numerical data points")
    analysis_type: str = Field(
        description="Type of analysis: 'basic', 'statistical', or 'advanced'",
        default="basic"
    )


@tool("data_analyzer", args_schema=DataAnalysisInput, return_direct=False)
def analyze_data(
    data: List[float], analysis_type: str = "basic"
) -> Dict[str, Any]:
    """Perform statistical analysis on numerical data.

    Args:
        data: List of numerical data points
        analysis_type: Type of analysis to perform

    Returns:
        Dictionary containing analysis results
    """
    if not data:
        return {"error": "No data provided"}

    # Basic statistics
    result = {
        "count": len(data),
        "sum": sum(data),
        "mean": sum(data) / len(data),
        "min": min(data),
        "max": max(data),
        "range": max(data) - min(data)
    }

    if analysis_type in ["statistical", "advanced"]:
        # Add standard deviation and variance
        mean = result["mean"]
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        result.update({
            "variance": variance,
            "std_dev": math.sqrt(variance),
            "median": sorted(data)[len(data) // 2]
        })

    if analysis_type == "advanced":
        # Add quartiles and outlier detection
        sorted_data = sorted(data)
        n = len(sorted_data)
        q1 = sorted_data[n // 4]
        q3 = sorted_data[3 * n // 4]
        iqr = q3 - q1

        outliers = [
            x for x in data if x < q1 - 1.5 * iqr or x > q3 + 1.5 * iqr
        ]

        result.update({
            "q1": q1,
            "q3": q3,
            "iqr": iqr,
            "outliers": outliers,
            "outlier_count": len(outliers)
        })

    return result


# =============================================================================
# Class-based Tools using BaseTool
# =============================================================================

class TextProcessorInput(BaseModel):
    """Input schema for text processor tool."""
    text: str = Field(description="Text to process")
    operation: str = Field(
        description=(
            "Operation to perform: 'word_count', 'char_count', "
            "'summary','char_count_of_a', or 'clean'"
        )
    )


class TextProcessorTool(BaseTool):
    """Advanced text processing tool with multiple operations."""

    name: str = "text_processor"
    description: str = (
        "Process text with various operations like counting, "
        "cleaning, and summarizing"
    )
    args_schema: Optional[type] = TextProcessorInput

    def _run(self, text: str, operation: str) -> Dict[str, Any]:
        """Execute the text processing operation."""
        if not text:
            return {"error": "No text provided"}

        if operation == "word_count":
            words = text.split()
            avg_length = (
                sum(len(word) for word in words) / len(words)
                if words else 0
            )
            return {
                "word_count": len(words),
                "unique_words": len(set(word.lower() for word in words)),
                "average_word_length": avg_length
            }

        elif operation == "char_count":
            return {
                "total_chars": len(text),
                "chars_no_spaces": len(text.replace(" ", "")),
                "lines": len(text.split("\n")),
                "paragraphs": len([
                    p for p in text.split("\n\n") if p.strip()
                ])
            }
        
        elif operation == "char_count_of_a":
            return {
                "total_chars": len(text),
                "chars_no_spaces": len(text.replace(" ", "")),
                "lines": len(text.split("\n")),
                "paragraphs": len([p for p in text.split("\n\n") if p.strip()]),
                "count_of_a": text.count("a")
            }


        elif operation == "clean":
            # Basic text cleaning
            import re
            cleaned = re.sub(r'\s+', ' ', text.strip())
            cleaned = re.sub(r'[^\w\s.,!?-]', '', cleaned)
            return {
                "original_length": len(text),
                "cleaned_text": cleaned,
                "cleaned_length": len(cleaned),
                "chars_removed": len(text) - len(cleaned)
            }

        elif operation == "summary":
            # Simple text summary (first and last sentences)
            sentences = [s.strip() for s in text.split('.') if s.strip()]
            if len(sentences) <= 2:
                summary = text
            else:
                summary = f"{sentences[0]}. ... {sentences[-1]}."

            return {
                "original_length": len(text),
                "summary": summary,
                "summary_length": len(summary),
                "compression_ratio": (
                    len(summary) / len(text) if text else 0
                ),
                "sentence_count": len(sentences)
            }

        else:
            return {"error": f"Unknown operation: {operation}"}


# =============================================================================
# Factory Functions for Tool Creation
# =============================================================================

def get_all_function_tools():
    """Get all function-based tools defined in this module.

    Returns:
        List of LangChain tools
    """
    return [
        calculate_percentage,
        generate_random_data,
        format_currency,
        calculate_business_days,
        analyze_data,
        TextProcessorTool()
    ]


def get_tool_by_name(tool_name: str):
    """Get a specific tool by name.

    Args:
        tool_name: Name of the tool to retrieve

    Returns:
        The tool instance or None if not found
    """
    tools = get_all_function_tools()
    for tool_instance in tools:
        if tool_instance.name == tool_name:
            return tool_instance
    return None


# =============================================================================
# Tool Registry for Dynamic Loading
# =============================================================================

TOOL_REGISTRY = {
    "calculate_percentage": calculate_percentage,
    "generate_random_data": generate_random_data,
    "format_currency": format_currency,
    "calculate_business_days": calculate_business_days,
    "data_analyzer": analyze_data,
    "text_processor": TextProcessorTool()
}


def load_tools_from_config(tool_names: List[str]):
    """Load specific tools from the registry.

    Args:
        tool_names: List of tool names to load

    Returns:
        List of tool instances
    """
    tools = []
    for name in tool_names:
        if name in TOOL_REGISTRY:
            tools.append(TOOL_REGISTRY[name])
        else:
            print(f"Warning: Tool '{name}' not found in registry")
    return tools
