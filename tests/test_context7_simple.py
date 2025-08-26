#!/usr/bin/env python3
"""
Simple test for Context7 MCP stdio agent integration.
Tests basic functionality of retrieving library documentation.
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

async def test_context7_simple():
    """Test Context7 agent with a simple documentation request."""

    config_path = "config/azure_openai_reference.yaml"

    # Test 1: Basic library documentation request
    test_query = "Show me how to use FastAPI to create a simple REST API with a GET endpoint"

    logger.info(f"Testing Context7 agent with query: {test_query}")

    try:
        # Load configuration and run supervised
        app_cfg = load_app_config(Path(config_path))
        result = await run_supervised(test_query, app_cfg)
        
        logger.info("Test completed successfully!")
        logger.info(f"Result: {result}")
        
        # Basic validation
        if result and len(result.strip()) > 0:
            print("✅ Context7 agent test PASSED")
            print(f"Response length: {len(result)} characters")
            
            # Check if response contains expected elements
            response_lower = result.lower()
            if any(keyword in response_lower for keyword in ['fastapi', 'api', 'endpoint', 'get']):
                print("✅ Response contains relevant FastAPI content")
            else:
                print("⚠️  Response may not contain expected FastAPI content")
                
            return True
        else:
            print("❌ Context7 agent test FAILED - Empty response")
            return False
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        print(f"❌ Context7 agent test FAILED - Error: {e}")
        return False

async def test_context7_library_resolution():
    """Test Context7 agent's library resolution capability."""

    config_path = "config/azure_openai_reference.yaml"

    # Test 2: Library resolution and documentation
    test_query = "Find documentation for the requests library in Python and show me how to make a POST request with JSON data"

    logger.info(f"Testing Context7 library resolution with query: {test_query}")

    try:
        # Load configuration and run supervised
        app_cfg = load_app_config(Path(config_path))
        result = await run_supervised(test_query, app_cfg)
        
        logger.info("Library resolution test completed!")
        logger.info(f"Result: {result}")
        
        # Validation
        if result and len(result.strip()) > 0:
            print("✅ Context7 library resolution test PASSED")
            
            response_lower = result.lower()
            if any(keyword in response_lower for keyword in ['requests', 'post', 'json']):
                print("✅ Response contains relevant requests library content")
            else:
                print("⚠️  Response may not contain expected requests content")
                
            return True
        else:
            print("❌ Context7 library resolution test FAILED - Empty response")
            return False
            
    except Exception as e:
        logger.error(f"Library resolution test failed with error: {e}")
        print(f"❌ Context7 library resolution test FAILED - Error: {e}")
        return False

async def main():
    """Run all simple Context7 tests."""
    print("🚀 Starting Context7 MCP stdio agent simple tests...")
    print("=" * 60)
    
    # Check if config file exists
    config_path = Path("config/azure_openai_reference.yaml")
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return False
    
    test_results = []
    
    # Run tests
    print("\n📋 Test 1: Basic FastAPI documentation request")
    print("-" * 40)
    result1 = await test_context7_simple()
    test_results.append(result1)
    
    print("\n📋 Test 2: Library resolution and documentation")
    print("-" * 40)
    result2 = await test_context7_library_resolution()
    test_results.append(result2)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All Context7 simple tests PASSED!")
        return True
    else:
        print("❌ Some Context7 tests FAILED!")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
