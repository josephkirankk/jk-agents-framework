"""
Test the Schema-Agnostic Test Data Generator with a different schema
to verify the auto-correction fix works for other use cases.

This test uses a Product Inventory schema instead of StudentExamRecord.
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import AppConfig
from app.main import build_agents_map
import yaml


async def test_product_inventory_schema():
    """
    Test data generation with a Product Inventory schema.

    This verifies that the auto-correction fix works for schemas
    other than StudentExamRecord.
    """

    # Define a Product Inventory schema
    product_schema = {
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
    
    # Requirements: Generate 50 products across all categories
    requirements = "Generate 50 products with 10 products in each category (Electronics, Clothing, Food, Books, Toys). Ensure realistic prices and quantities."

    # Load configuration
    config_path = Path(__file__).parent.parent / "config" / "json_schema_test_data_generator.yaml"
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)

    # Build agents
    agents_map = build_agents_map(config_data)

    # Create fixed plan (same structure as run_with_fixed_plan.py)
    fixed_plan = {
        "plan": {
            "steps": [
                {
                    "id": "s1",
                    "agent": "schema_analyzer",
                    "task": f"Analyze the JSON Schema: {json.dumps(product_schema)}",
                    "depends_on": [],
                    "verify": None,
                    "timeout_seconds": 120,
                    "retry": 1
                },
                {
                    "id": "s2",
                    "agent": "requirement_parser",
                    "task": f"Parse requirements: {requirements}",
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
        },
        "steps": {},
        "final_result": {},
        "status": "in_progress"
    }

    print("\n" + "="*80)
    print("Testing Schema-Agnostic Test Data Generator")
    print("Schema: Product Inventory")
    print("="*80)

    # Execute the plan
    from app.planner_executor import execute_plan
    result = await execute_plan(fixed_plan, agents_map)
    
    # Extract results
    print("\n" + "="*80)
    print("Workflow Results")
    print("="*80)
    
    if "steps" in result:
        for step_id, step_result in result["steps"].items():
            print(f"\nStep {step_id}: {step_result.get('agent', 'unknown')}")
            print(f"  Status: {'✅ OK' if step_result.get('ok') else '❌ FAILED'}")
            if step_result.get('output_summary'):
                summary = step_result['output_summary'][:200]
                print(f"  Summary: {summary}...")
    
    # Check if data was generated
    if "final_result" in result and "s3" in result["final_result"]:
        s3_output = result["final_result"]["s3"]["raw"]
        
        # Look for reference ID
        import re
        ref_match = re.search(r'ref_[a-f0-9]{12}', s3_output)
        
        if ref_match:
            reference_id = ref_match.group(0)
            print(f"\n✅ Reference ID found: {reference_id}")
            
            # Verify the data in the database
            from app.memory.large_data_storage import LargeDataStorage
            
            storage = LargeDataStorage()
            try:
                data = storage.retrieve_large_data(reference_id)
                
                print(f"\n" + "="*80)
                print("Database Verification")
                print("="*80)
                print(f"Reference ID: {reference_id}")
                print(f"Data type: {type(data).__name__}")
                print(f"Record count: {len(data) if isinstance(data, (list, dict)) else 'N/A'}")
                
                if isinstance(data, list):
                    print(f"\n✅ Data is a list (correct)")
                    print(f"Expected records: 50")
                    print(f"Actual records: {len(data)}")
                    
                    if len(data) == 50:
                        print(f"✅ Record count matches!")
                        
                        # Verify categories
                        categories = {}
                        for record in data:
                            cat = record.get('category', 'Unknown')
                            categories[cat] = categories.get(cat, 0) + 1
                        
                        print(f"\nCategory distribution:")
                        for cat, count in sorted(categories.items()):
                            print(f"  {cat}: {count} products")
                        
                        # Show sample records
                        print(f"\nSample records:")
                        for i, record in enumerate(data[:3]):
                            print(f"\n{i+1}. {json.dumps(record, indent=2)}")
                        
                        return True
                    else:
                        print(f"⚠️  Record count mismatch!")
                        return False
                else:
                    print(f"❌ Data is {type(data).__name__}, expected list")
                    return False
                    
            except Exception as e:
                print(f"❌ Error retrieving data: {e}")
                return False
        else:
            print(f"❌ No reference ID found in output")
            return False
    else:
        print(f"❌ No data generation step found")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_product_inventory_schema())
    sys.exit(0 if success else 1)

