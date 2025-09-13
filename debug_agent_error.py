#!/usr/bin/env python3
"""
Debug script to isolate the 'function' object is not subscriptable error.
"""

import sys
import os
import asyncio
import traceback
import logging

# Add the current directory to Python path
sys.path.append('.')

from app.main import load_app_config
from app.agent_builder import build_react_agent

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s] %(name)s: %(message)s",
)

async def debug_agent_creation():
    """Debug the agent creation process step by step."""
    
    print("=== Debug Agent Creation ===")
    
    try:
        # Step 1: Load configuration
        print("Step 1: Loading configuration...")
        from pathlib import Path
        config_path = Path("config/pep_mcp_sample.yaml")
        app_cfg = load_app_config(config_path)
        print(f"✓ Configuration loaded successfully")
        print(f"  - Default model: {app_cfg.models.get('default')}")
        print(f"  - Number of agents: {len(app_cfg.agents)}")
        
        # Step 2: Find the restaurants_agent
        print("\nStep 2: Finding restaurants_agent...")
        target_agent = None
        for agent in app_cfg.agents:
            if agent.name == "restaurants_agent":
                target_agent = agent
                break
        
        if not target_agent:
            print("✗ restaurants_agent not found!")
            return
        
        print(f"✓ Found restaurants_agent")
        print(f"  - Model: {target_agent.model}")
        print(f"  - MCP servers: {list(target_agent.mcp_servers.keys())}")
        
        # Step 3: Build the agent
        print("\nStep 3: Building agent...")
        default_model = app_cfg.models.get("default", "openai:gpt-4o-mini")
        
        try:
            compiled, mcp_client = await build_react_agent(
                target_agent,
                default_model,
                business_context=app_cfg.business_context or "",
                original_user_question="test question",
                dependent_request_responses="",
                config_path=config_path,
                enable_llm_payload_logging=False,
            )
            print("✓ Agent built successfully!")
            print(f"  - Agent type: {type(compiled)}")
            print(f"  - MCP client: {type(mcp_client) if mcp_client else 'None'}")
            
        except Exception as e:
            print(f"✗ Agent building failed: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return
        
        # Step 4: Test a simple invocation
        print("\nStep 4: Testing simple invocation...")
        try:
            test_input = {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello, can you help me?"}
                ]
            }
            
            result = await compiled.ainvoke(test_input, config={"configurable": {"thread_id": "test-thread"}})
            print("✓ Simple invocation successful!")
            print(f"  - Result type: {type(result)}")
            
        except Exception as e:
            print(f"✗ Simple invocation failed: {e}")
            print("Full traceback:")
            traceback.print_exc()
            
    except Exception as e:
        print(f"✗ Debug failed: {e}")
        print("Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_agent_creation())
