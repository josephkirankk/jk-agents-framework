#!/usr/bin/env python3
"""
Test script to verify LLM payload logging through the API endpoint.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.api import run_direct_agent_api
from app.main import load_app_config


async def test_api_logging():
    """Test the LLM payload logging through the API."""
    
    print("🚀 Testing LLM Payload Logging via API")
    print("=" * 40)
    
    # Load configuration
    config_path = "config/pep_mcp_sample.yaml"
    try:
        app_cfg = load_app_config(Path(config_path))
        print(f"✅ Loaded configuration from {config_path}")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return
    
    # Test API call
    agent_name = "restaurants_agent"
    user_input = "Find pizza restaurants with menu score 80-100"
    
    print(f"🔄 Testing API call for agent: {agent_name}")
    print(f"   User input: {user_input}")
    
    try:
        # Call the API function directly (without actual LLM execution)
        result = await run_direct_agent_api(
            agent_name=agent_name,
            user_input=user_input,
            app_cfg=app_cfg,
            config_path=config_path
        )
        
        print(f"✅ API call completed successfully")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Agent: {result.get('agent_name', 'unknown')}")
        print(f"   Standard log: {result.get('log_file', 'not provided')}")
        print(f"   LLM payload log: {result.get('llm_payload_log_file', 'not provided')}")
        
        # Check if log files exist
        standard_log = result.get('log_file')
        payload_log = result.get('llm_payload_log_file')
        
        if standard_log and Path(standard_log).exists():
            print(f"✅ Standard log file exists: {standard_log}")
            with open(standard_log, 'r') as f:
                content = f.read()
                print(f"   Size: {len(content)} characters")
        else:
            print(f"❌ Standard log file not found or not provided")
        
        if payload_log and Path(payload_log).exists():
            print(f"✅ LLM payload log file exists: {payload_log}")
            with open(payload_log, 'r') as f:
                log_data = json.load(f)
            
            entries = log_data.get('entries', [])
            print(f"   Agent name: {log_data.get('agent_name', 'unknown')}")
            print(f"   Created at: {log_data.get('created_at', 'unknown')}")
            print(f"   Entries: {len(entries)}")
            
            if entries:
                print(f"   📋 Sample entry types:")
                for entry in entries[:3]:  # Show first 3 entries
                    print(f"     - {entry['interaction_type']}")
            else:
                print(f"   ℹ️  No entries (expected since we skipped execution)")
        else:
            print(f"❌ LLM payload log file not found or not provided")
        
        print(f"\n✅ API logging test completed!")
        
    except Exception as e:
        print(f"❌ Error during API test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_api_logging())
