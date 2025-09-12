#!/usr/bin/env python3
"""
Test script to verify LLM payload logging with actual agent execution.
This will make a real LLM call to test the logging functionality.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.main import load_app_config
from app.direct_agent_logger import create_direct_agent_logger
from app.agent_builder import build_react_agent


async def test_actual_llm_logging():
    """Test the LLM payload logging with actual agent execution."""
    
    print("🚀 Testing LLM Payload Logging with Actual Agent Execution")
    print("=" * 60)
    
    # Load configuration
    config_path = "config/pep_mcp_sample.yaml"
    try:
        app_cfg = load_app_config(Path(config_path))
        print(f"✅ Loaded configuration from {config_path}")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return
    
    # Find the restaurants agent
    agent_name = "restaurants_agent"
    target_agent = next((a for a in app_cfg.agents if a.name == agent_name), None)
    if not target_agent:
        print(f"❌ Agent '{agent_name}' not found in configuration")
        return
    
    print(f"✅ Found agent: {agent_name}")
    
    # Create logger
    user_input = "Find 2 pizza restaurants"
    logger = create_direct_agent_logger(
        agent_name=agent_name,
        user_input=user_input,
        business_context=app_cfg.business_context or ""
    )
    
    print(f"✅ Created logger for agent: {agent_name}")
    print(f"📝 Standard log file: {logger.get_log_file_path()}")
    print(f"📊 LLM payload log file: {logger.get_llm_payload_log_path()}")
    
    # Build agent with LLM payload logging enabled
    try:
        default_model = app_cfg.models.get("default", "azure_openai:gpt-4.1")
        compiled, mcp_client = await build_react_agent(
            target_agent,
            default_model,
            business_context=app_cfg.business_context or "",
            original_user_question=user_input,
            dependent_request_responses="",
            config_path=config_path,
            enable_llm_payload_logging=True,
            llm_payload_logger=logger.get_llm_payload_logger(),
        )
        print(f"✅ Built agent with LLM payload logging enabled")
        
        # Log the agent request
        system_context = (
            "Business context:\n"
            f"{app_cfg.business_context or ''}\n\n"
            "Previous step results:\n(none)"
        )
        
        logger.log_agent_request(
            compiled_agent=compiled,
            system_context=system_context,
            user_task=user_input
        )
        
        print(f"✅ Logged agent request details")
        
        # Execute agent with a simple query
        print(f"\n🔄 Executing agent with query: '{user_input}'")
        print(f"⚠️  This will make actual LLM API calls and may incur costs")
        
        # Ask for confirmation
        response = input("Continue with actual LLM execution? (y/N): ")
        if response.lower() != 'y':
            print("❌ Skipping actual LLM execution")
            return
        
        # Create state for agent execution
        state = {
            "messages": [
                {"role": "system", "content": system_context},
                {"role": "user", "content": user_input},
            ]
        }
        config = {"configurable": {"thread_id": "test-thread"}}
        
        try:
            # Execute the agent
            print("🚀 Calling agent...")
            out = await compiled.ainvoke(state, config=config)
            
            msgs = out.get("messages", [])
            if msgs:
                last_msg = msgs[-1]
                text = getattr(last_msg, "content", "")
                print(f"✅ Agent response: {text[:200]}...")
            else:
                text = ""
                print("❌ No response from agent")
            
            # Log the response
            logger.log_agent_response(response_text=text, raw_output=out)
            
            print(f"\n📊 Execution completed!")
            
        except Exception as e:
            print(f"❌ Error during agent execution: {e}")
            import traceback
            traceback.print_exc()
        
        # Check log files
        print(f"\n📁 Checking log files...")
        
        # Check standard log
        standard_log = logger.get_log_file_path()
        if Path(standard_log).exists():
            print(f"✅ Standard log file exists: {standard_log}")
            with open(standard_log, 'r') as f:
                content = f.read()
                print(f"   Size: {len(content)} characters")
        else:
            print(f"❌ Standard log file not found")
        
        # Check LLM payload log
        payload_log = logger.get_llm_payload_log_path()
        if Path(payload_log).exists():
            print(f"✅ LLM payload log file exists: {payload_log}")
            with open(payload_log, 'r') as f:
                log_data = json.load(f)
                entries = log_data.get('entries', [])
                print(f"   Entries: {len(entries)}")
                
                if entries:
                    print(f"   📋 Log entries found:")
                    for i, entry in enumerate(entries):
                        print(f"     {i+1}. {entry['interaction_type']} at {entry['timestamp']}")
                        if 'request' in entry:
                            req = entry['request']
                            print(f"        Messages: {len(req.get('messages', []))}")
                            print(f"        Tools: {len(req.get('tools', []))}")
                            print(f"        Model: {req.get('model_params', {}).get('model_name', 'unknown')}")
                        if 'response' in entry and entry['response'].get('usage'):
                            usage = entry['response']['usage']
                            print(f"        Usage: {usage}")
                else:
                    print(f"   ❌ No log entries found")
        else:
            print(f"❌ LLM payload log file not found")
        
        # Clean up
        if mcp_client:
            try:
                await mcp_client.close()
            except AttributeError:
                pass
        
        print(f"\n✅ Test completed!")
        
    except Exception as e:
        print(f"❌ Error during agent building: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_actual_llm_logging())
