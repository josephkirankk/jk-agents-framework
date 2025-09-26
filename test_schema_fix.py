#!/usr/bin/env python3
"""
Quick test to verify that the Gemini schema filtering fix works
"""
import os
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import AppConfig
from app.main import load_app_config
from app.agent_builder import build_react_agent

async def test_schema_filtering():
    """Test that schema filtering works without warnings"""
    
    # Load the python_exec_agent config
    config_path = "config/python_exec_agent_working.yaml"
    print(f"Loading config from: {config_path}")
    
    try:
        app_cfg = load_app_config(Path(config_path))
        print(f"✓ Config loaded successfully")
        
        # Find the python_exec_agent
        python_agent = None
        for agent in app_cfg.agents:
            if agent.name == "python_exec_agent":
                python_agent = agent
                break
        
        if python_agent is None:
            print("✗ python_exec_agent not found in config")
            return False
            
        print(f"✓ Found python_exec_agent")
        
        # Build the agent - this should trigger schema filtering
        default_model = app_cfg.models.get("default", "openai:gpt-4o-mini")
        
        print(f"Building agent with model: {python_agent.model}")
        compiled_agent, mcp_client = await build_react_agent(
            python_agent,
            default_model,
            business_context=app_cfg.business_context or "",
            original_user_question="test",
            dependent_request_responses="",
            config_path=config_path,
            enable_llm_payload_logging=False,
            default_temperature=app_cfg.temperature,
        )
        
        print("✓ Agent built successfully without errors")
        
        # Clean up
        if mcp_client:
            from app.mcp_loader import close_mcp_client
            await close_mcp_client(mcp_client)
        
        print("✓ Test completed successfully - no schema filtering warnings should appear above")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_schema_filtering())
    sys.exit(0 if success else 1)