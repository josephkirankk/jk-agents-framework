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
import csv
import io
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


@tool
def count_csv_rows(csv_content: str, include_header: bool = True) -> int:
    """Count the number of rows in CSV content. Empty lines are ignored.

    Args:
        csv_content: CSV content as a string.
        include_header: Whether to include the first row (header) in the count. Defaults to True.

    Returns:
        Integer count of rows.
    """
    if not csv_content or not csv_content.strip():
        return 0
    try:
        sample = csv_content[:2048]
        try:
            dialect = csv.Sniffer().sniff(sample)
        except Exception:
            dialect = csv.excel
        reader = csv.reader(io.StringIO(csv_content), dialect)
        count = 0
        for row in reader:
            if any(cell.strip() for cell in row):
                count += 1
        if not include_header and count > 0:
            count -= 1
        return count
    except Exception:
        # Fallback: line-based counting if parsing fails
        lines = [ln for ln in csv_content.splitlines() if ln.strip()]
        if not include_header and lines:
            return max(len(lines) - 1, 0)
        return len(lines)


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
        count_csv_rows,
        analyze_data,
        generate_business_data,
        create_summary_statistics,
        generate_insights,
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


@tool
def generate_business_data(
    num_records: int = 100, 
    company_name: str = "TechCorp",
    year: int = 2025
) -> Dict[str, Any]:
    """Generate sample business data for demonstration.

    Args:
        num_records: Number of data records to generate
        company_name: Name of the company for the data
        year: Year for the data generation

    Returns:
        Dictionary containing generated business data
    """
    import csv
    import io
    from datetime import datetime, timedelta
    
    if num_records <= 0:
        return {"error": "Number of records must be positive"}
    
    # Generate sample business data
    data = {
        "company": company_name,
        "year": year,
        "generated_at": datetime.now().isoformat(),
        "records": [],
        "metadata": {
            "total_records": num_records,
            "data_types": ["sales", "revenue", "customers", "products"]
        }
    }
    
    # Generate sample records
    departments = ["Sales", "Marketing", "Engineering", "Support", "Operations"]
    regions = ["North", "South", "East", "West", "Central"]
    
    for i in range(num_records):
        record = {
            "id": i + 1,
            "department": random.choice(departments),
            "region": random.choice(regions),
            "sales": round(random.uniform(1000, 50000), 2),
            "revenue": round(random.uniform(10000, 200000), 2),
            "customers": random.randint(1, 500),
            "month": random.randint(1, 12),
            "quarter": random.choice(["Q1", "Q2", "Q3", "Q4"])
        }
        data["records"].append(record)
    
    return data


@tool
def create_summary_statistics(business_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create summary statistics from business data.

    Args:
        business_data: Business data dictionary from generate_business_data

    Returns:
        Dictionary containing summary statistics
    """
    if "records" not in business_data:
        return {"error": "Invalid business data format"}
    
    records = business_data["records"]
    if not records:
        return {"error": "No records found in business data"}
    
    # Calculate statistics
    sales_data = [r["sales"] for r in records]
    revenue_data = [r["revenue"] for r in records]
    customer_data = [r["customers"] for r in records]
    
    summary = {
        "company": business_data.get("company", "Unknown"),
        "analysis_date": datetime.now().isoformat(),
        "total_records": len(records),
        "sales_stats": {
            "total": round(sum(sales_data), 2),
            "average": round(sum(sales_data) / len(sales_data), 2),
            "min": round(min(sales_data), 2),
            "max": round(max(sales_data), 2)
        },
        "revenue_stats": {
            "total": round(sum(revenue_data), 2),
            "average": round(sum(revenue_data) / len(revenue_data), 2),
            "min": round(min(revenue_data), 2),
            "max": round(max(revenue_data), 2)
        },
        "customer_stats": {
            "total": sum(customer_data),
            "average": round(sum(customer_data) / len(customer_data), 1),
            "min": min(customer_data),
            "max": max(customer_data)
        },
        "department_breakdown": {},
        "region_breakdown": {}
    }
    
    # Department breakdown
    departments = {}
    for record in records:
        dept = record["department"]
        if dept not in departments:
            departments[dept] = {"sales": 0, "revenue": 0, "customers": 0, "count": 0}
        departments[dept]["sales"] += record["sales"]
        departments[dept]["revenue"] += record["revenue"]
        departments[dept]["customers"] += record["customers"]
        departments[dept]["count"] += 1
    
    for dept, data in departments.items():
        summary["department_breakdown"][dept] = {
            "total_sales": round(data["sales"], 2),
            "total_revenue": round(data["revenue"], 2),
            "total_customers": data["customers"],
            "record_count": data["count"],
            "avg_sales": round(data["sales"] / data["count"], 2),
            "avg_revenue": round(data["revenue"] / data["count"], 2)
        }
    
    # Region breakdown
    regions = {}
    for record in records:
        region = record["region"]
        if region not in regions:
            regions[region] = {"sales": 0, "revenue": 0, "customers": 0, "count": 0}
        regions[region]["sales"] += record["sales"]
        regions[region]["revenue"] += record["revenue"]
        regions[region]["customers"] += record["customers"]
        regions[region]["count"] += 1
    
    for region, data in regions.items():
        summary["region_breakdown"][region] = {
            "total_sales": round(data["sales"], 2),
            "total_revenue": round(data["revenue"], 2),
            "total_customers": data["customers"],
            "record_count": data["count"],
            "avg_sales": round(data["sales"] / data["count"], 2),
            "avg_revenue": round(data["revenue"] / data["count"], 2)
        }
    
    return summary


@tool
def generate_insights(summary_stats: Dict[str, Any], threshold_revenue: float = 100000) -> Dict[str, Any]:
    """Generate business insights from summary statistics.

    Args:
        summary_stats: Summary statistics from create_summary_statistics
        threshold_revenue: Revenue threshold for insights

    Returns:
        Dictionary containing business insights
    """
    if "sales_stats" not in summary_stats:
        return {"error": "Invalid summary statistics format"}
    
    insights = {
        "company": summary_stats.get("company", "Unknown"),
        "insights_generated_at": datetime.now().isoformat(),
        "key_insights": [],
        "recommendations": [],
        "performance_indicators": {}
    }
    
    sales_stats = summary_stats["sales_stats"]
    revenue_stats = summary_stats["revenue_stats"]
    
    # Performance indicators
    insights["performance_indicators"] = {
        "revenue_per_customer": round(revenue_stats["total"] / summary_stats["customer_stats"]["total"], 2),
        "sales_per_customer": round(sales_stats["total"] / summary_stats["customer_stats"]["total"], 2),
        "avg_deal_size": round(revenue_stats["average"], 2)
    }
    
    # Key insights
    if revenue_stats["total"] > threshold_revenue * summary_stats["total_records"] / 100:
        insights["key_insights"].append(
            f"Strong revenue performance: Total revenue of {format_currency(revenue_stats['total'])} "
            f"exceeds industry benchmarks."
        )
    
    # Department insights
    if "department_breakdown" in summary_stats:
        dept_breakdown = summary_stats["department_breakdown"]
        top_dept = max(dept_breakdown.items(), key=lambda x: x[1]["total_revenue"])
        insights["key_insights"].append(
            f"Top performing department: {top_dept[0]} with "
            f"{format_currency(top_dept[1]['total_revenue'])} in revenue."
        )
        
        # Find underperforming departments
        avg_dept_revenue = revenue_stats["total"] / len(dept_breakdown)
        underperforming = [
            dept for dept, data in dept_breakdown.items()
            if data["total_revenue"] < avg_dept_revenue * 0.7
        ]
        
        if underperforming:
            insights["recommendations"].append(
                f"Focus improvement efforts on: {', '.join(underperforming)} - "
                "these departments are underperforming relative to company average."
            )
    
    # Region insights
    if "region_breakdown" in summary_stats:
        region_breakdown = summary_stats["region_breakdown"]
        top_region = max(region_breakdown.items(), key=lambda x: x[1]["total_revenue"])
        insights["key_insights"].append(
            f"Top performing region: {top_region[0]} with "
            f"{format_currency(top_region[1]['total_revenue'])} in revenue."
        )
    
    # Customer efficiency insights
    revenue_per_customer = insights["performance_indicators"]["revenue_per_customer"]
    if revenue_per_customer > 500:
        insights["key_insights"].append(
            f"High customer value: Average revenue per customer "
            f"({format_currency(revenue_per_customer)}) indicates strong customer relationships."
        )
    else:
        insights["recommendations"].append(
            "Consider customer value enhancement strategies to increase revenue per customer."
        )
    
    return insights


# =============================================================================
# Tool Registry for Dynamic Loading
# =============================================================================

TOOL_REGISTRY = {
    "calculate_percentage": calculate_percentage,
    "generate_random_data": generate_random_data,
    "format_currency": format_currency,
    "calculate_business_days": calculate_business_days,
    "count_csv_rows": count_csv_rows,
    "data_analyzer": analyze_data,
    "generate_business_data": generate_business_data,
    "create_summary_statistics": create_summary_statistics,
    "generate_insights": generate_insights,
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
