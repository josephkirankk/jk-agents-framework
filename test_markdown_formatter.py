#!/usr/bin/env python3
"""
Test script to verify the Markdown formatting functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.markdown_formatter import format_result_as_markdown, format_direct_agent_result

def test_markdown_formatter():
    """Test the Markdown formatter with sample data."""
    
    # Test case 1: Multi-step execution result
    sample_result = {
        "plan": {
            "goal": "Get weather and news for NYC",
            "plan": [
                {
                    "id": "s1",
                    "agent": "search_agent", 
                    "task": "Get weather for NYC",
                    "depends_on": [],
                    "verify": "Check weather data is current"
                },
                {
                    "id": "s2",
                    "agent": "search_agent",
                    "task": "Get news for NYC", 
                    "depends_on": ["s1"],
                    "verify": "Check news is current"
                }
            ]
        },
        "final_result": {
            "s1": {
                "summary": "Weather: 72°F, sunny conditions",
                "raw": "Current weather in NYC is 72°F with sunny conditions. Visit https://weather.com for details."
            },
            "s2": {
                "summary": "Latest news from major NYC outlets",
                "raw": "Breaking news from NYC today includes city council updates. See https://ny1.com for more."
            }
        },
        "status": "completed"
    }
    
    user_query = "What's the weather and news in NYC today?"
    
    print("=== Testing Multi-Step Result Formatting ===")
    markdown_output = format_result_as_markdown(sample_result, user_query)
    print(markdown_output)
    print("\n" + "="*50 + "\n")
    
    # Test case 2: Direct agent result
    print("=== Testing Direct Agent Result Formatting ===")
    agent_response = "The compound interest formula is A = P(1 + r/n)^(nt). For example, $1000 at 5% for 3 years yields $1161.62."
    direct_output = format_direct_agent_result(agent_response, "math_agent", "How do I calculate compound interest?")
    print(direct_output)
    print("\n" + "="*50 + "\n")

    # Test case 3: Single step result
    print("=== Testing Single Step Result Formatting ===")
    single_step_result = {
        "plan": {
            "goal": "Calculate math problem",
            "plan": [
                {
                    "id": "s1",
                    "agent": "math_agent",
                    "task": "Calculate 19 * 37",
                    "depends_on": []
                }
            ]
        },
        "final_result": {
            "s1": {
                "summary": "19 * 37 = 703", 
                "raw": "The calculation of 19 multiplied by 37 equals 703."
            }
        },
        "status": "completed"
    }
    
    single_output = format_result_as_markdown(single_step_result, "What is 19 times 37?")
    print(single_output)

if __name__ == "__main__":
    test_markdown_formatter()
