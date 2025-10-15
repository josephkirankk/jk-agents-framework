#!/usr/bin/env python3
"""
Run the Schema-Agnostic Test Data Generator with a FIXED PLAN

This script bypasses the supervisor planning step and uses a hardcoded 4-step plan.
This is a workaround for the supervisor planning issue where the LLM generates data
instead of creating a plan.
"""

import asyncio
import json
import sys
import os
import uuid
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import AppConfig
from app.main import build_agents_map
import yaml

# Test schema
STUDENT_EXAM_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "StudentExamRecord",
    "description": "Schema for storing student exam data",
    "type": "object",
    "properties": {
        "student_name": {"type": "string", "description": "Full name of the student"},
        "student_id": {"type": "string", "description": "Unique identifier for the student"},
        "student_class": {
            "type": "integer",
            "description": "Class of the student from 1 to 10",
            "minimum": 1,
            "maximum": 10,
            "default": 1
        },
        "subject": {
            "type": "string",
            "description": "Subject name",
            "enum": ["Maths", "Physics", "Chemistry"],
            "default": "Maths"
        },
        "marks": {
            "type": "integer",
            "description": "Marks scored in the subject (1–100)",
            "minimum": 1,
            "maximum": 100,
            "default": 50
        },
        "exam_quarter": {
            "type": "string",
            "description": "Exam quarter",
            "enum": ["Q1", "Q2", "Q3", "Q4"],
            "default": "Q1"
        },
        "exam_year": {
            "type": "integer",
            "description": "Year of the exam in YYYY format",
            "minimum": 2000,
            "maximum": 2100,
            "default": 2025
        }
    },
    "required": [
        "student_name", "student_id", "student_class",
        "subject", "marks", "exam_quarter", "exam_year"
    ],
    "additionalProperties": False
}

# Test requirements
TEST_REQUIREMENTS = "create records for 100 students for class 5 for all the subjects per student for years 2023,2024,2025. ensure it looks real"


# FIXED PLAN - Hardcoded 4-step workflow
FIXED_PLAN = {
    "goal": "Generate test data for StudentExamRecord schema",
    "plan": [
        {
            "id": "s1",
            "agent": "schema_analyzer",
            "task": f"Analyze the JSON Schema: {json.dumps(STUDENT_EXAM_SCHEMA)}",
            "depends_on": [],
            "verify": None,
            "timeout_seconds": 90,
            "retry": 1
        },
        {
            "id": "s2",
            "agent": "requirement_parser",
            "task": f"Parse requirements: {TEST_REQUIREMENTS}",
            "depends_on": [],
            "verify": None,
            "timeout_seconds": 60,
            "retry": 1
        },
        {
            "id": "s3",
            "agent": "data_generator",
            "task": "Generate test data using schema from s1 and constraints from s2",
            "depends_on": ["s1", "s2"],
            "verify": None,
            "timeout_seconds": 180,
            "retry": 1
        },
        {
            "id": "s4",
            "agent": "schema_validator",
            "task": "Validate generated data from s3 against schema from s1",
            "depends_on": ["s1", "s3"],
            "verify": None,
            "timeout_seconds": 120,
            "retry": 1
        }
    ]
}


async def run_test():
    """Run the test data generator workflow with a fixed plan"""
    
    print("=" * 80)
    print("  Schema-Agnostic Test Data Generator - Fixed Plan Test")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Step 1: Load configuration
    print("[Step 1] Loading configuration...")
    config_path = "config/json_schema_test_data_generator.yaml"
    
    if not os.path.exists(config_path):
        print(f"❌ Configuration file not found: {config_path}")
        return 1
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    
    # Normalize config
    models = config_data.get("models", {}) or {}
    if "temperature" in models and "temperature" not in config_data:
        config_data["temperature"] = models.get("temperature")
        models.pop("temperature", None)
    models = {str(k): str(v) for k, v in models.items() if v is not None}
    config_data["models"] = models
    
    app_config = AppConfig(**config_data)
    
    print(f"✅ Configuration loaded")
    print(f"   Agents: {len(app_config.agents)}")
    print(f"   Default model: {app_config.models.get('default', 'N/A')}")
    
    # Step 2: Prepare user request
    print("\n[Step 2] Preparing user request...")
    schema_json = json.dumps(STUDENT_EXAM_SCHEMA, indent=2)
    user_request = f"""schema :
{schema_json}

Request : {TEST_REQUIREMENTS}"""
    
    print(f"✅ Request prepared")
    print(f"   Schema: StudentExamRecord")
    print(f"   Requirements: {TEST_REQUIREMENTS}")
    print(f"   Expected records: 900 (100 students × 3 subjects × 3 years)")
    
    # Step 3: Build agents
    print("\n[Step 3] Building agents...")
    
    thread_id = f"test_{uuid.uuid4().hex[:8]}"
    default_model = app_config.models.get('default', 'openai:gpt-4o-mini')
    
    try:
        # Build agents map
        agents_map, mcp_clients = await build_agents_map(
            app_config,
            user_input=user_request,
            config_path=config_path
        )
        
        print(f"✅ Agents built: {list(agents_map.keys())}")
        
    except Exception as e:
        print(f"❌ Failed to build agents: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Step 4: Execute workflow with FIXED PLAN
    print("\n[Step 4] Executing workflow with FIXED PLAN...")
    print(f"   Plan: {len(FIXED_PLAN['plan'])} steps")
    for step in FIXED_PLAN['plan']:
        print(f"     - {step['id']}: {step['agent']}")
    print("-" * 80)

    try:
        # Import the execute_plan function and Plan models
        from app.planner_executor import execute_plan, Plan, PlanStep

        # Create a Plan object from the fixed plan
        plan_obj = Plan(
            goal=FIXED_PLAN['goal'],
            plan=[PlanStep(**step) for step in FIXED_PLAN['plan']]
        )

        # Create a mock supervisor that just returns our fixed plan
        class MockSupervisor:
            def __init__(self, plan):
                self.plan = plan
                self._model_id = "fixed_plan"
                self._rendered_prompt = "Using fixed plan - no supervisor needed"

            async def ainvoke(self, state, config=None):
                # Return a mock response that will be parsed as our plan
                import json
                plan_dict = {
                    "goal": self.plan.goal,
                    "plan": [
                        {
                            "id": step.id,
                            "agent": step.agent,
                            "task": step.task,
                            "depends_on": step.depends_on or [],
                            "verify": step.verify,
                            "timeout_seconds": step.timeout_seconds,
                            "retry": step.retry or 0
                        }
                        for step in self.plan.plan
                    ]
                }
                # Return in the format expected by execute_plan
                class MockMessage:
                    def __init__(self, content):
                        self.content = content

                return {
                    "messages": [MockMessage(json.dumps(plan_dict))]
                }

        mock_supervisor = MockSupervisor(plan_obj)

        # Execute the plan using the standard execute_plan function
        result = await execute_plan(
            supervisor_compiled=mock_supervisor,
            agents_map=agents_map,
            user_input=user_request,
            business_context=app_config.business_context or "",
            default_model_for_verifier=default_model,
            agents_configs=app_config.agents,
            default_model=default_model,
            thread_id=thread_id,
        )
        
        print("-" * 80)
        print("\n[Step 5] Workflow execution complete!")
        
        # Display result
        print("\n" + "=" * 80)
        print("  Execution Result")
        print("=" * 80)
        
        if isinstance(result, dict):
            print(json.dumps(result, indent=2))
        else:
            print(result)
        
        # Check for reference ID
        result_str = str(result)
        if "ref_" in result_str:
            import re
            ref_ids = re.findall(r'ref_[a-f0-9]{12}', result_str)
            if ref_ids:
                print(f"\n✅ Reference ID found: {ref_ids[0]}")
                
                # Verify in database
                print("\n[Step 6] Verifying database...")
                import sqlite3
                
                db_path = "./data/large_data_storage.db"
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT reference_id, metadata, data_blob, compressed 
                        FROM large_tool_data 
                        WHERE reference_id = ?
                    """, (ref_ids[0],))
                    
                    db_result = cursor.fetchone()
                    if db_result:
                        ref_id, metadata_json, data_blob, compressed = db_result
                        metadata = json.loads(metadata_json)
                        
                        print(f"✅ Dataset found in database")
                        print(f"   Reference ID: {ref_id}")
                        print(f"   Metadata: {json.dumps(metadata, indent=2)}")
                        
                        # Decompress if needed
                        if compressed:
                            import gzip
                            data_blob = gzip.decompress(data_blob)
                        
                        # Parse data
                        data = json.loads(data_blob)
                        
                        print(f"   Data type: {type(data).__name__}")
                        
                        if isinstance(data, list):
                            print(f"   Record count: {len(data)}")
                            
                            if len(data) == 900:
                                print(f"\n✅ SUCCESS: 900 records generated!")
                            else:
                                print(f"\n⚠️  WARNING: Expected 900 records, got {len(data)}")
                        else:
                            print(f"\n❌ ERROR: Data is {type(data).__name__}, expected list")
                    else:
                        print(f"❌ Reference ID not found in database")
                    
                    conn.close()
                else:
                    print(f"❌ Database not found: {db_path}")
        else:
            print(f"\n⚠️  No reference ID found in result")
        
        # Close MCP clients
        if mcp_clients:
            print("\n[Step 7] Cleaning up MCP clients...")
            for client in mcp_clients:
                try:
                    await client.__aexit__(None, None, None)
                except:
                    pass
        
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return 0
        
    except Exception as e:
        print(f"\n❌ Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main entry point"""
    try:
        return asyncio.run(run_test())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

