#!/usr/bin/env python3
"""
Advanced multi-agent test for Context7 MCP stdio agent integration.
Tests Context7 agent working with other agents to solve complex problems.
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import run_supervised, load_app_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_context7_with_python_execution():
    """Test Context7 agent working with Python execution agent."""
    
    config_path = "config/azure_openai_reference.yaml"
    
    # Complex test: Get pandas documentation and implement data analysis
    test_query = """
    I need to analyze a dataset using pandas. Please:
    1. Get the latest pandas documentation for reading CSV files and basic data analysis
    2. Create Python code that demonstrates how to:
       - Read a CSV file
       - Display basic statistics (mean, median, std)
       - Filter data based on conditions
    3. Execute the code with sample data to verify it works
    """
    
    logger.info(f"Testing Context7 + Python execution with query: {test_query}")
    
    try:
        result = await run_multi_agent_system(
            user_question=test_query,
            config_path=config_path
        )
        
        logger.info("Context7 + Python execution test completed!")
        logger.info(f"Result: {result}")
        
        # Validation
        if result and len(result.strip()) > 0:
            print("✅ Context7 + Python execution test PASSED")
            
            response_lower = result.lower()
            expected_keywords = ['pandas', 'csv', 'read_csv', 'mean', 'median', 'filter']
            found_keywords = [kw for kw in expected_keywords if kw in response_lower]
            
            print(f"✅ Found {len(found_keywords)}/{len(expected_keywords)} expected keywords: {found_keywords}")
            
            if len(found_keywords) >= 3:
                print("✅ Response contains sufficient pandas-related content")
                return True
            else:
                print("⚠️  Response may not contain enough expected pandas content")
                return False
        else:
            print("❌ Context7 + Python execution test FAILED - Empty response")
            return False
            
    except Exception as e:
        logger.error(f"Context7 + Python execution test failed with error: {e}")
        print(f"❌ Context7 + Python execution test FAILED - Error: {e}")
        return False

async def test_context7_with_math_calculations():
    """Test Context7 agent working with math calculation agent."""
    
    config_path = "config/azure_openai_reference.yaml"
    
    # Complex test: Get NumPy documentation and perform mathematical operations
    test_query = """
    I need to understand NumPy array operations and perform some calculations:
    1. Get NumPy documentation for array creation and mathematical operations
    2. Calculate the result of: (25 * 4) + (15 * 3) - 10
    3. Explain how this calculation would be done using NumPy arrays
    """
    
    logger.info(f"Testing Context7 + Math agent with query: {test_query}")
    
    try:
        result = await run_multi_agent_system(
            user_question=test_query,
            config_path=config_path
        )
        
        logger.info("Context7 + Math agent test completed!")
        logger.info(f"Result: {result}")
        
        # Validation
        if result and len(result.strip()) > 0:
            print("✅ Context7 + Math agent test PASSED")
            
            response_lower = result.lower()
            expected_keywords = ['numpy', 'array', 'mathematical', 'calculation']
            found_keywords = [kw for kw in expected_keywords if kw in response_lower]
            
            print(f"✅ Found {len(found_keywords)}/{len(expected_keywords)} expected keywords: {found_keywords}")
            
            # Check if the calculation result is present (25*4 + 15*3 - 10 = 100 + 45 - 10 = 135)
            if '135' in result:
                print("✅ Correct calculation result found in response")
                return True
            else:
                print("⚠️  Expected calculation result (135) not found in response")
                return len(found_keywords) >= 2
        else:
            print("❌ Context7 + Math agent test FAILED - Empty response")
            return False
            
    except Exception as e:
        logger.error(f"Context7 + Math agent test failed with error: {e}")
        print(f"❌ Context7 + Math agent test FAILED - Error: {e}")
        return False

async def test_full_multi_agent_workflow():
    """Test a complete workflow involving Context7, Python execution, and math agents."""
    
    config_path = "config/azure_openai_reference.yaml"
    
    # Complex workflow test
    test_query = """
    Create a complete data science workflow:
    1. Get documentation for matplotlib and seaborn for data visualization
    2. Calculate the statistical values: mean of [10, 20, 30, 40, 50] and standard deviation
    3. Write and execute Python code that:
       - Creates sample data
       - Calculates basic statistics
       - Creates a simple plot (even if we can't display it)
    4. Provide a summary of the complete workflow
    """
    
    logger.info(f"Testing full multi-agent workflow with query: {test_query}")
    
    try:
        result = await run_multi_agent_system(
            user_question=test_query,
            config_path=config_path
        )
        
        logger.info("Full multi-agent workflow test completed!")
        logger.info(f"Result: {result}")
        
        # Validation
        if result and len(result.strip()) > 0:
            print("✅ Full multi-agent workflow test PASSED")
            
            response_lower = result.lower()
            expected_keywords = ['matplotlib', 'seaborn', 'statistics', 'mean', 'plot', 'data']
            found_keywords = [kw for kw in expected_keywords if kw in response_lower]
            
            print(f"✅ Found {len(found_keywords)}/{len(expected_keywords)} expected keywords: {found_keywords}")
            
            # Check for mean calculation (mean of [10,20,30,40,50] = 30)
            if '30' in result and 'mean' in response_lower:
                print("✅ Correct mean calculation found in response")
                return True
            else:
                print("⚠️  Expected mean calculation not clearly found")
                return len(found_keywords) >= 4
        else:
            print("❌ Full multi-agent workflow test FAILED - Empty response")
            return False
            
    except Exception as e:
        logger.error(f"Full multi-agent workflow test failed with error: {e}")
        print(f"❌ Full multi-agent workflow test FAILED - Error: {e}")
        return False

async def main():
    """Run all advanced Context7 multi-agent tests."""
    print("🚀 Starting Context7 MCP stdio agent advanced multi-agent tests...")
    print("=" * 70)
    
    # Check if config file exists
    config_path = Path("config/azure_openai_reference.yaml")
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return False
    
    test_results = []
    
    # Run tests
    print("\n📋 Test 1: Context7 + Python Execution Agent")
    print("-" * 50)
    result1 = await test_context7_with_python_execution()
    test_results.append(result1)
    
    print("\n📋 Test 2: Context7 + Math Calculation Agent")
    print("-" * 50)
    result2 = await test_context7_with_math_calculations()
    test_results.append(result2)
    
    print("\n📋 Test 3: Full Multi-Agent Workflow")
    print("-" * 50)
    result3 = await test_full_multi_agent_workflow()
    test_results.append(result3)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 ADVANCED TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All Context7 advanced multi-agent tests PASSED!")
        return True
    else:
        print("❌ Some Context7 advanced tests FAILED!")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
