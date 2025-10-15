#!/bin/bash
# Test the Schema-Agnostic Test Data Generator with Product Inventory schema

cd "$(dirname "$0")/.."
source .venv/bin/activate

echo "================================================================================"
echo "Testing Schema-Agnostic Test Data Generator with Product Inventory Schema"
echo "================================================================================"
echo ""

# Get the absolute path to the project root
PROJECT_ROOT="$(pwd)"

# Create a temporary Python script that uses the Product Inventory schema
cat > /tmp/test_product_inventory.py << EOF
#!/usr/bin/env python3
import asyncio
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, '$PROJECT_ROOT')

from app.config import AppConfig
from app.main import build_agents_map
import yaml

# Product Inventory Schema
PRODUCT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "ProductInventory",
    "description": "Schema for product inventory management",
    "type": "object",
    "properties": {
        "product_id": {
            "type": "string",
            "description": "Unique product identifier",
            "pattern": "^PROD-[0-9]{6}$"
        },
        "product_name": {
            "type": "string",
            "description": "Name of the product",
            "minLength": 3,
            "maxLength": 100
        },
        "category": {
            "type": "string",
            "description": "Product category",
            "enum": ["Electronics", "Clothing", "Food", "Books", "Toys"]
        },
        "price": {
            "type": "number",
            "description": "Product price in USD",
            "minimum": 0.01,
            "maximum": 10000.00
        },
        "quantity": {
            "type": "integer",
            "description": "Quantity in stock",
            "minimum": 0,
            "maximum": 10000
        },
        "in_stock": {
            "type": "boolean",
            "description": "Whether the product is in stock"
        },
        "warehouse_location": {
            "type": "string",
            "description": "Warehouse location code",
            "enum": ["WH-A", "WH-B", "WH-C", "WH-D"]
        }
    },
    "required": [
        "product_id",
        "product_name",
        "category",
        "price",
        "quantity",
        "in_stock",
        "warehouse_location"
    ],
    "additionalProperties": False
}

REQUIREMENTS = "Generate 50 products with 10 products in each category (Electronics, Clothing, Food, Books, Toys). Ensure realistic prices and quantities."

# Fixed plan
FIXED_PLAN = {
    "goal": f"Generate test data for Product Inventory schema with requirements: {REQUIREMENTS}",
    "plan": [
        {
            "id": "s1",
            "agent": "schema_analyzer",
            "task": f"Analyze the JSON Schema: {json.dumps(PRODUCT_SCHEMA)}",
            "depends_on": [],
            "verify": None,
            "timeout_seconds": 120,
            "retry": 1
        },
        {
            "id": "s2",
            "agent": "requirement_parser",
            "task": f"Parse requirements: {REQUIREMENTS}",
            "depends_on": [],
            "verify": None,
            "timeout_seconds": 120,
            "retry": 1
        },
        {
            "id": "s3",
            "agent": "data_generator",
            "task": "Generate test data using schema from s1 and constraints from s2",
            "depends_on": ["s1", "s2"],
            "verify": None,
            "timeout_seconds": 120,
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

async def main():
    print("\n[Step 1] Loading configuration...")
    config_path = Path('$PROJECT_ROOT') / "config" / "json_schema_test_data_generator.yaml"
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    
    app_config = AppConfig.from_dict(config_data)
    
    print("\n[Step 2] Building agents...")
    agents_map = await build_agents_map(config_data)
    
    print("\n[Step 3] Executing plan...")
    from app.planner_executor import execute_plan, Plan, PlanStep
    
    plan_obj = Plan(
        goal=FIXED_PLAN['goal'],
        plan=[PlanStep(**step) for step in FIXED_PLAN['plan']]
    )
    
    class MockSupervisor:
        def __init__(self, plan):
            self.plan = plan
            self._model_id = "fixed_plan"
            self._rendered_prompt = "Using fixed plan"
        
        async def ainvoke(self, state, config=None):
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
            class MockMessage:
                def __init__(self, content):
                    self.content = content
            return {"messages": [MockMessage(json.dumps(plan_dict))]}
    
    mock_supervisor = MockSupervisor(plan_obj)
    
    result = await execute_plan(
        supervisor_compiled=mock_supervisor,
        agents_map=agents_map,
        user_input=REQUIREMENTS,
        business_context="",
        default_model_for_verifier="openai:gpt-4o-mini"
    )
    
    print("\n[Step 4] Extracting reference ID...")
    import re
    ref_id = None
    if "steps" in result and "s3" in result["steps"]:
        s3_output = result["steps"]["s3"].get("raw", "")
        ref_match = re.search(r'ref_[a-f0-9]{12}', s3_output)
        if ref_match:
            ref_id = ref_match.group(0)
            print(f"✅ Reference ID found: {ref_id}")
    
    if ref_id:
        print("\n[Step 5] Verifying database...")
        from app.memory.large_data_storage import LargeDataStorage
        storage = LargeDataStorage()
        data = storage.retrieve_large_data(ref_id)
        
        print(f"✅ Dataset found in database")
        print(f"   Reference ID: {ref_id}")
        print(f"   Data type: {type(data).__name__}")
        print(f"   Record count: {len(data) if isinstance(data, (list, dict)) else 'N/A'}")
        
        if isinstance(data, list) and len(data) == 50:
            print(f"\n✅ SUCCESS: 50 products generated!")
            
            # Verify categories
            categories = {}
            for record in data:
                cat = record.get('category', 'Unknown')
                categories[cat] = categories.get(cat, 0) + 1
            
            print(f"\nCategory distribution:")
            for cat, count in sorted(categories.items()):
                print(f"  {cat}: {count} products")
            
            print(f"\nSample products:")
            for i, record in enumerate(data[:3]):
                print(f"\n{i+1}. {json.dumps(record, indent=2)}")
            
            return True
        else:
            print(f"\n⚠️  WARNING: Expected 50 records, got {len(data) if isinstance(data, list) else 'N/A'}")
            return False
    else:
        print(f"\n❌ ERROR: No reference ID found")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
EOF

# Run the test
python /tmp/test_product_inventory.py
exit_code=$?

# Cleanup
rm /tmp/test_product_inventory.py

exit $exit_code

