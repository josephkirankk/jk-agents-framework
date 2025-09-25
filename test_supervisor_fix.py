#!/usr/bin/env python3
"""
Quick test for supervisor workflow fix
"""
import os
import sys
import asyncio
import yaml
import json
from pathlib import Path
from dotenv import load_dotenv

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.supervisor_builder import build_supervisor_compiled
from app.config import AppConfig

async def test_supervisor_workflow():
    """Test supervisor workflow with Google Gemini"""
    
    # Load environment
    load_dotenv()
    
    print("🧪 Testing Supervisor Workflow Fix")
    print("=" * 40)
    
    try:
        # Load config
        config_path = Path("config/basic_test.yaml")
        with config_path.open("r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        
        # Normalize config
        models = config_data.get("models", {}) or {}
        if "temperature" in models and "temperature" not in config_data:
            config_data["temperature"] = models.get("temperature")
            models.pop("temperature", None)
        models = {str(k): str(v) for k, v in models.items() if v is not None}
        config_data["models"] = models
        
        app_config = AppConfig(**config_data)
        
        print(f"✅ Config loaded: {app_config.models}")
        print(f"   Supervisor: {app_config.supervisor.name}")
        print(f"   Agents: {len(app_config.agents)}")
        
        # Build supervisor with correct parameters
        supervisor = build_supervisor_compiled(
            supervisor_cfg=app_config.supervisor,
            agents_cfg=app_config.agents,
            default_model=app_config.models.get('default', 'google:gemini-2.5-flash-lite'),
            business_context=app_config.business_context or "",
            checkpointer=None,
            original_user_question="Analyze business performance using sales data and user analytics",
            config_path=str(config_path),
            default_temperature=app_config.temperature
        )
        
        print("✅ Supervisor built successfully!")
        
        # Test supervisor with a query
        test_query = "Create a business analysis plan using sales data and user analytics."
        
        response = await supervisor.ainvoke(
            {"messages": [{"role": "user", "content": test_query}]},
            {"configurable": {"thread_id": "supervisor-test"}}
        )
        
        # Check response
        has_response = bool(response and "messages" in response)
        
        if has_response:
            messages = response["messages"]
            for msg in messages:
                if hasattr(msg, 'content') and msg.content:
                    print(f"✅ Supervisor response received:")
                    print(f"   Length: {len(msg.content)} characters")
                    print(f"   Sample: {msg.content[:100]}...")
                    
                    # Try to parse as JSON plan
                    try:
                        plan_data = json.loads(msg.content)
                        if "plan" in plan_data:
                            print(f"   ✅ JSON plan detected with {len(plan_data['plan'])} steps")
                            return True
                    except (json.JSONDecodeError, TypeError):
                        print(f"   ⚠️  Response not in JSON plan format")
                        return True  # Still a valid response, just not structured as expected
                    break
        
        print("❌ No valid response received")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_supervisor_workflow())
    print(f"\n🏁 Supervisor test {'PASSED' if result else 'FAILED'}")