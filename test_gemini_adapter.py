#!/usr/bin/env python3
"""
Test script for the Google Gemini tool binding adapter.
This script tests if the custom adapter works with the Gemini model.
"""

import os
import logging
import asyncio
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log = logging.getLogger("gemini_adapter_test")

# Import the tool adapter functions
try:
    from app.enhanced_litellm_wrapper import (
        EnhancedLiteLLMChat, 
        get_tool_compatible_model, 
        get_fallback_tool_binding,
        create_litellm_model
    )
except ImportError as e:
    print(f"Import error: {e}")
    exit(1)

# Define a simple calculator tool for testing
from langchain_core.tools import Tool

def add_numbers(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b

def subtract_numbers(a: float, b: float) -> float:
    """Subtract the second number from the first."""
    return a - b

def multiply_numbers(a: float, b: float) -> float:
    """Multiply two numbers together."""
    return a * b

def divide_numbers(a: float, b: float) -> float:
    """Divide the first number by the second."""
    if b == 0:
        return "Error: Cannot divide by zero"
    return a / b

# Create tools
tools = [
    Tool.from_function(
        func=add_numbers,
        name="add",
        description="Add two numbers together",
    ),
    Tool.from_function(
        func=subtract_numbers,
        name="subtract",
        description="Subtract the second number from the first",
    ),
    Tool.from_function(
        func=multiply_numbers,
        name="multiply",
        description="Multiply two numbers together",
    ),
    Tool.from_function(
        func=divide_numbers,
        name="divide",
        description="Divide the first number by the second",
    ),
]

async def test_gemini_adapter():
    """Test the Gemini adapter with tool binding."""
    log.info("Testing Gemini adapter with tool binding")
    
    # Create the LiteLLM model
    model_instance = create_litellm_model(
        model_id="gemini/gemini-2.5-flash-lite",
        temperature=0.2
    )
    
    log.info(f"Created model instance: {model_instance.model}")
    
    # Try to bind tools directly (should raise NotImplementedError)
    log.info("Testing direct tool binding (should fail)...")
    try:
        # This will fail and trigger our adapter
        bound_model = model_instance.bind_tools(tools)
        log.info("Direct binding unexpectedly worked!")
    except Exception as e:
        log.info(f"Direct binding failed as expected: {e}")
    
    # Use our adapter
    log.info("Testing adapter for tool binding...")
    try:
        # Use the custom adapter
        bound_model = get_tool_compatible_model(model_instance, tools)
        log.info(f"Adapter created bound model: {type(bound_model)}")
        
        # Test with a simple prompt that requires tool use
        from langchain_core.messages import HumanMessage
        
        # Test message
        message = HumanMessage(content="Calculate 23 + 45 and then divide the result by 2")
        
        log.info("Sending request to the bound model...")
        response = await bound_model.ainvoke([message])
        
        log.info(f"Response: {response}")
        return {
            "success": True,
            "model_type": str(type(bound_model)),
            "response": response
        }
    
    except Exception as e:
        log.error(f"Adapter failed: {e}")
        import traceback
        log.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    # Check if GOOGLE_API_KEY is set
    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        print("Error: GOOGLE_API_KEY or GEMINI_API_KEY environment variable is not set.")
        print("Please set it in your .env file or environment variables.")
        exit(1)
    
    # Run the test
    result = asyncio.run(test_gemini_adapter())
    
    if result["success"]:
        print("\n✅ Test completed successfully!")
    else:
        print(f"\n❌ Test failed: {result.get('error', 'Unknown error')}")
