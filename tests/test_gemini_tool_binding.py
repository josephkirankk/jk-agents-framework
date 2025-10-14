#!/usr/bin/env python3
"""
Test Google Gemini tool binding implementation for jk-agents-framework.
This test verifies that:
1. The custom tool binding adapter works correctly with Google Gemini models
2. Tools can be invoked successfully from Gemini models
3. The adapter correctly handles different tool signatures and return values
4. The fallback mechanisms work when needed
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent  # Go up one level to project root
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / '.env')
    print("✅ Loaded environment variables from .env")
except ImportError:
    print("⚠️ dotenv not installed, skipping environment loading")

# Import framework components
from app.enhanced_litellm_wrapper import (
    EnhancedLiteLLMChat, 
    get_tool_compatible_model, 
    get_fallback_tool_binding,
    create_litellm_model
)

# Import tool creation utilities
from langchain_core.tools import Tool, StructuredTool
from langchain.agents import AgentType, initialize_agent, AgentExecutor
from langchain_core.messages import HumanMessage

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("gemini_tool_binding_test")

# ANSI colors for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

# Define sample tools for testing
def add_numbers(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b

def multiply_numbers(a: float, b: float) -> float:
    """Multiply two numbers together."""
    return a * b

def calculate_square_root(number: float) -> float:
    """Calculate the square root of a number."""
    if number < 0:
        return f"Error: Cannot calculate square root of negative number {number}"
    return number ** 0.5

def fetch_weather(location: str) -> str:
    """Get the current weather for a location (simulated)."""
    weather_data = {
        "new york": "Sunny, 72°F",
        "london": "Rainy, 62°F",
        "tokyo": "Clear, 78°F",
        "sydney": "Partly Cloudy, 65°F",
        "paris": "Overcast, 58°F"
    }
    
    location = location.lower()
    if location in weather_data:
        return weather_data[location]
    
    return f"Weather data not available for {location}"

def create_test_tools():
    """Create a set of test tools."""
    tools = [
        Tool.from_function(
            func=add_numbers,
            name="add",
            description="Add two numbers together",
        ),
        Tool.from_function(
            func=multiply_numbers,
            name="multiply",
            description="Multiply two numbers together",
        ),
        StructuredTool.from_function(
            func=calculate_square_root,
            name="square_root",
            description="Calculate the square root of a number",
        ),
        Tool.from_function(
            func=fetch_weather,
            name="get_weather",
            description="Get the current weather for a city",
        ),
    ]
    
    return tools

async def test_tool_binding_direct():
    """Test the tool binding implementation directly."""
    print(f"\n{BLUE}=== Testing Direct Tool Binding ==={RESET}")
    
    # Check if Google API key is available
    google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not google_api_key:
        print(f"{YELLOW}⚠️ Skipping test_tool_binding_direct: No Google API key found{RESET}")
        return False
    
    # Create tools
    tools = create_test_tools()
    print(f"Created {len(tools)} test tools")
    
    try:
        # Create Gemini model with LiteLLM
        model_id = "gemini/gemini-2.5-flash-lite"
        print(f"Creating LiteLLM model: {model_id}")
        
        litellm_model = create_litellm_model(model_id, temperature=0.2)
        
        # Test the adapter directly
        print(f"Testing get_tool_compatible_model adapter...")
        adapted_model = get_tool_compatible_model(litellm_model, tools)
        
        print(f"Model type after adaptation: {type(adapted_model).__name__}")
        
        # Test the adapted model with a tool-using query
        user_message = HumanMessage(content="Calculate 25 multiplied by 6, then find the square root of the result")
        
        print(f"\nSending test query to adapted model: \"{user_message.content}\"")
        start_time = time.time()
        
        response = await adapted_model.ainvoke([user_message])
        
        elapsed_time = time.time() - start_time
        print(f"Response received in {elapsed_time:.2f}s")
        
        # Display the response
        tool_calls = getattr(response, "tool_calls", [])
        if tool_calls:
            print(f"\n{GREEN}Tool calls found in response:{RESET}")
            for tool_call in tool_calls:
                print(f"- Tool: {tool_call['name']}")
                print(f"  Args: {tool_call['args']}")
        else:
            print(f"\n{YELLOW}No explicit tool calls in response format{RESET}")
        
        print(f"\n{GREEN}Response Content:{RESET}")
        response_content = getattr(response, "content", str(response))
        print(response_content)
        
        # Check for expected content in the response
        success = False
        if "150" in str(response) and ("12.2" in str(response) or "12.25" in str(response)):
            print(f"\n{GREEN}✓ Expected calculation results found in response{RESET}")
            success = True
        else:
            print(f"\n{YELLOW}⚠️ Expected calculation results not found in response{RESET}")
            success = False
        
        return success
    
    except Exception as e:
        print(f"\n{RED}Error in direct tool binding test: {str(e)}{RESET}")
        import traceback
        print(traceback.format_exc())
        return False

async def test_fallback_tool_binding():
    """Test the fallback tool binding mechanism."""
    print(f"\n{BLUE}=== Testing Fallback Tool Binding ==={RESET}")
    
    # Check if Google API key is available
    google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not google_api_key:
        print(f"{YELLOW}⚠️ Skipping test_fallback_tool_binding: No Google API key found{RESET}")
        return False
    
    # Create tools
    tools = create_test_tools()
    print(f"Created {len(tools)} test tools")
    
    try:
        # Create Gemini model with LiteLLM
        model_id = "gemini/gemini-2.5-flash-lite"
        print(f"Creating LiteLLM model: {model_id}")
        
        litellm_model = create_litellm_model(model_id, temperature=0.2)
        
        # Force using the fallback mechanism by simulating a failure
        print(f"Testing get_fallback_tool_binding adapter...")
        fallback_model = get_fallback_tool_binding(litellm_model, tools)
        
        print(f"Model type after fallback: {type(fallback_model).__name__}")
        
        # Test the fallback model with a tool-using query
        input_data = "What's the weather in London and New York? Then add 25 and 17."
        
        print(f"\nSending test query to fallback model: \"{input_data}\"")
        start_time = time.time()
        
        # For fallback model (Chain-style interface)
        response = await fallback_model.ainvoke({"input": input_data})
        
        elapsed_time = time.time() - start_time
        print(f"Response received in {elapsed_time:.2f}s")
        
        # Display the response
        print(f"\n{GREEN}Response:{RESET}")
        print(response)
        
        # Check for expected content in the response
        success = False
        response_str = str(response)
        
        # Check if response mentions weather information and calculation
        weather_terms = ["weather", "london", "new york", "rainy", "sunny"]
        calculation_terms = ["add", "25", "17", "42", "sum"]
        
        has_weather = any(term in response_str.lower() for term in weather_terms)
        has_calculation = any(term in response_str.lower() for term in calculation_terms)
        
        if has_weather and has_calculation:
            print(f"{GREEN}✓ Response contains expected information about weather and calculation{RESET}")
            success = True
        else:
            missing = []
            if not has_weather:
                missing.append("weather information")
            if not has_calculation:
                missing.append("calculation")
            
            print(f"{YELLOW}⚠️ Response is missing expected content: {', '.join(missing)}{RESET}")
            success = False
        
        return success
    
    except Exception as e:
        print(f"\n{RED}Error in fallback tool binding test: {str(e)}{RESET}")
        import traceback
        print(traceback.format_exc())
        return False

async def test_api_with_tool_binding():
    """Test the tool binding implementation through the API."""
    print(f"\n{BLUE}=== Testing API with Tool Binding ==={RESET}")
    
    # Check if the API server is running
    import requests
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=3)
        if response.status_code != 200:
            print(f"{YELLOW}⚠️ API server not available at http://localhost:8000/health{RESET}")
            print(f"{YELLOW}Please start the API server with 'python fixed_api.py'{RESET}")
            return False
        
        print(f"{GREEN}✓ API server is running{RESET}")
    except requests.exceptions.ConnectionError:
        print(f"{YELLOW}⚠️ API server not available at http://localhost:8000/health{RESET}")
        print(f"{YELLOW}Please start the API server with 'python fixed_api.py'{RESET}")
        return False
    
    # Check if Google API key is available
    google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not google_api_key:
        print(f"{YELLOW}⚠️ Skipping API test: No Google API key found{RESET}")
        return False
    
    try:
        # Use the multimodal endpoint which uses LiteLLM
        url = "http://localhost:8000/multimodal"
        
        # Create form data with Gemini model and test query
        data = {
            "model": "gemini/gemini-2.5-flash-lite",  # Use LiteLLM format
            "prompt": "Calculate the square root of 144, then add 5 to the result",
            "temperature": 0.2,
            "system_message": "You are a helpful assistant skilled at mathematics. Use step-by-step reasoning."
        }
        
        print(f"Sending request to {url} with Gemini model...")
        response = requests.post(url, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n{GREEN}API call succeeded!{RESET}")
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Check for expected calculation in the response
            success = False
            if "12" in result["response"] and "17" in result["response"]:
                print(f"{GREEN}✓ Expected calculation results found in response{RESET}")
                success = True
            else:
                print(f"{YELLOW}⚠️ Expected calculation results not found in response{RESET}")
                success = False
            
            return success
        else:
            print(f"{RED}API call failed with status {response.status_code}{RESET}")
            print(f"Error: {response.text}")
            return False
    
    except Exception as e:
        print(f"{RED}Error in API test: {str(e)}{RESET}")
        import traceback
        print(traceback.format_exc())
        return False

async def main():
    """Main test runner."""
    print(f"{BLUE}Testing Google Gemini Tool Binding Implementation{RESET}")
    
    # Run tests
    direct_test_success = await test_tool_binding_direct()
    fallback_test_success = await test_fallback_tool_binding()
    api_test_success = await test_api_with_tool_binding()
    
    # Display overall results
    print(f"\n{BLUE}=== Test Results ==={RESET}")
    print(f"Direct Tool Binding Test: {GREEN}PASS{RESET}" if direct_test_success else f"{RED}FAIL{RESET}")
    print(f"Fallback Tool Binding Test: {GREEN}PASS{RESET}" if fallback_test_success else f"{RED}FAIL{RESET}")
    print(f"API with Tool Binding Test: {GREEN}PASS{RESET}" if api_test_success else f"{RED}FAIL{RESET}")
    
    overall_success = direct_test_success and fallback_test_success and api_test_success
    
    if overall_success:
        print(f"\n{GREEN}✅ All tests passed successfully!{RESET}")
        print(f"{GREEN}The Google Gemini tool binding implementation is working correctly.{RESET}")
    else:
        print(f"\n{RED}❌ Some tests failed{RESET}")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
