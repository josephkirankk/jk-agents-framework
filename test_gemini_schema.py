#!/usr/bin/env python3
"""
Test script to reproduce Google Gemini schema warnings
"""

import os
import logging
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.python_function_tools import count_csv_rows, analyze_data
from langgraph.prebuilt import create_react_agent

# Load environment variables
load_dotenv()

# Set up logging to capture warnings
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_gemini_with_tools():
    """Test Google Gemini with tools to reproduce schema warnings"""

    # Check if API key is set
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not set")
        return

    print("Testing Google Gemini with tools...")

    # Test schema filtering
    from app.gemini_schema_filter import apply_gemini_schema_filtering

    # Create tools list
    tools = [count_csv_rows, analyze_data]
    print(f"Original tools: {[tool.name for tool in tools]}")

    # Apply schema filtering
    filtered_tools = apply_gemini_schema_filtering(tools, "google:gemini-2.0-flash-lite-001")
    print(f"Filtered tools: {[tool.name for tool in filtered_tools]}")

    # Check if any tools were wrapped
    for i, (orig, filt) in enumerate(zip(tools, filtered_tools)):
        if orig != filt:
            print(f"Tool {i} ({orig.name}) was wrapped for Gemini compatibility")
        else:
            print(f"Tool {i} ({orig.name}) was not modified")

    # Create Gemini model
    model = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-lite-001",
        google_api_key=api_key,
        temperature=0.0,
    )

    print(f"Created model: {model}")

    # Create agent with filtered tools
    try:
        agent = create_react_agent(
            model=model,
            tools=filtered_tools,
            prompt="You are a helpful assistant with access to data analysis tools."
        )
        print("Agent created successfully")

        # Test with a simple query that should use tools
        response = agent.invoke({
            "messages": [("human", "Can you count the rows in this CSV: 'header1,header2\\nrow1,row2\\nrow3,row4'?")]
        })

        print("Response:", response)

    except Exception as e:
        print(f"Error creating or using agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gemini_with_tools()
