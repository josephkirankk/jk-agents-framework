#!/usr/bin/env python3
"""
Direct test of the API function to isolate the error.
"""

import asyncio
import sys
import traceback
from pathlib import Path

sys.path.append('.')

from app.main import load_app_config
from app.api import run_direct_agent_with_files

async def test_api_direct():
    """Test the API function directly."""
    print("=== Testing API Function Directly ===")
    
    try:
        # Load configuration
        config_path = Path("config/pep_mcp_sample.yaml")
        app_cfg = load_app_config(config_path)
        print("✓ Configuration loaded")
        
        # Test parameters
        agent_name = "restaurants_agent"
        user_input = "what is the chain id for restaurant which have taco in the name. order it by the menu score and include menu score in the result. i want the score for all the categories. include the number of outlets for it as well. check the summary correctly"
        file_ids = []
        file_info = []
        
        print(f"Testing agent: {agent_name}")
        print(f"Input length: {len(user_input)} characters")
        
        # Call the function directly
        result = await run_direct_agent_with_files(
            agent_name=agent_name,
            user_input=user_input,
            app_cfg=app_cfg,
            file_ids=file_ids,
            file_info=file_info,
            config_path=str(config_path)
        )
        
        print("✓ API function completed successfully!")
        print(f"Result: {result.get('success', False)}")
        if result.get('response'):
            print(f"Response length: {len(result['response'])} characters")
        
    except Exception as e:
        print(f"✗ API function failed: {e}")
        print("Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_direct())
