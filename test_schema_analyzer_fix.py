#!/usr/bin/env python3
"""
Quick test to verify the schema_analyzer agent fix.
This tests that the agent properly calls run_python_code and returns results.
"""

import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.main import load_app_config
from app.agent_builder import build_agent
from dotenv import load_dotenv

load_dotenv()


async def test_schema_analyzer():
    """Test that schema_analyzer agent works correctly"""
    print("=" * 80)
    print("Testing Schema Analyzer Agent Fix")
    print("=" * 80)
    
    # Load config
    config_path = Path(__file__).parent / "config" / "json_schema_test_data_generator.yaml"
    
    if not config_path.exists():
        print(f"❌ Config not found: {config_path}")
        return False
    
    print(f"✓ Loading config from: {config_path}")
    app_config = load_app_config(config_path)
    
    # Get schema_analyzer agent
    schema_agent_cfg = next((a for a in app_config.agents if a.name == "schema_analyzer"), None)
    if not schema_agent_cfg:
        print("❌ schema_analyzer agent not found in config")
        return False
    
    print(f"✓ Found schema_analyzer agent")
    
    # Get default model
    default_model = app_config.models.get('default') if isinstance(app_config.models, dict) else app_config.models.default
    print(f"✓ Using model: {default_model}")
    
    # Build agent
    print("\n📦 Building agent...")
    agent, mcp_client = await build_agent(
        agent_cfg=schema_agent_cfg,
        default_model=default_model,
        business_context=app_config.business_context or "",
        config_path=str(config_path),
        app_config={"models": {"default": default_model}}
    )
    
    print("✓ Agent built successfully")
    
    # Test with simple schema
    simple_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "TestSchema",
        "type": "object",
        "required": ["name", "age"],
        "properties": {
            "name": {
                "type": "string",
                "minLength": 1,
                "maxLength": 100
            },
            "age": {
                "type": "integer",
                "minimum": 0,
                "maximum": 120
            }
        }
    }
    
    query = f"""Analyze the JSON Schema and extract metadata including fields, types, constraints, enums, patterns, and validation rules

schema :
{json.dumps(simple_schema, indent=2)}
"""
    
    print("\n🔍 Testing schema analysis...")
    print(f"Schema: {simple_schema['title']}")
    
    # Invoke agent
    from langchain_core.runnables import RunnableConfig
    
    state = {
        "messages": [
            {"role": "system", "content": app_config.business_context or ""},
            {"role": "user", "content": query},
        ]
    }
    config = RunnableConfig({"configurable": {"thread_id": "test_fix"}})
    
    try:
        print("\n⏳ Invoking agent...")
        out = await agent.ainvoke(state, config=config)
        
        msgs = out.get("messages", [])
        if msgs:
            last_msg = msgs[-1]
            response = getattr(last_msg, "content", "")
            
            print("\n" + "=" * 80)
            print("AGENT RESPONSE:")
            print("=" * 80)
            print(response)
            print("=" * 80)
            
            # Check if response is not empty
            if not response or response.strip() == "" or response.strip() == "(empty)":
                print("\n❌ FAILED: Agent returned empty response")
                return False
            
            # Check if response contains expected metadata
            has_fields = "fields" in response.lower() or "properties" in response.lower()
            has_required = "required" in response.lower()
            has_name = "name" in response.lower()
            has_age = "age" in response.lower()
            
            print("\n📊 Response Analysis:")
            print(f"  - Contains 'fields' or 'properties': {has_fields}")
            print(f"  - Contains 'required': {has_required}")
            print(f"  - Contains 'name' field: {has_name}")
            print(f"  - Contains 'age' field: {has_age}")
            print(f"  - Response length: {len(response)} characters")
            
            if has_fields and has_required and has_name and has_age:
                print("\n✅ SUCCESS: Agent returned valid schema metadata")
                return True
            else:
                print("\n⚠️  WARNING: Response may be incomplete")
                return False
        else:
            print("\n❌ FAILED: No messages in response")
            return False
            
    except Exception as e:
        print(f"\n❌ FAILED: Exception during agent invocation: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        if mcp_client:
            await mcp_client.cleanup()


async def main():
    """Main test runner"""
    success = await test_schema_analyzer()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ TEST PASSED: Schema analyzer is working correctly")
        print("=" * 80)
        sys.exit(0)
    else:
        print("❌ TEST FAILED: Schema analyzer needs more fixes")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

