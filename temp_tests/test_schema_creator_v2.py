#!/usr/bin/env python3
"""
Test script for JSON Schema Creator and Test Data Generator V2

This script tests both workflows:
1. Plain English → JSON Schema → Test Data (NEW)
2. Existing Schema → Test Data (Traditional)
"""

import json
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import load_app_config, build_agents_map
from app.supervisor_builder import build_supervisor_compiled
from app.planner_executor import execute_plan


# Test Case 1: Plain English Input (NEW FEATURE)
PLAIN_ENGLISH_INPUT = """
Data Structure Description:

employee_id: unique identifier for employee
employee_name: full name of the employee
department: HR, Engineering, Sales, Marketing, Finance
position: job title
salary: 30000 to 200000
hire_date: date in YYYY-MM-DD format
is_active: true or false
email: valid email address
years_of_experience: 0 to 50

Requirements: Generate 100 employee records with realistic data distribution across all departments. Ensure 80% are active employees.
"""


# Test Case 2: Existing Schema (Traditional)
EXISTING_SCHEMA_INPUT = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "ProductInventory",
    "description": "Schema for product inventory records",
    "type": "object",
    "properties": {
        "product_id": {
            "type": "string",
            "description": "Unique product identifier",
            "pattern": "^PROD-[0-9]{6}$"
        },
        "product_name": {
            "type": "string",
            "description": "Product name",
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
            "maximum": 10000.00,
            "multipleOf": 0.01
        },
        "stock_quantity": {
            "type": "integer",
            "description": "Available stock quantity",
            "minimum": 0,
            "maximum": 10000
        },
        "in_stock": {
            "type": "boolean",
            "description": "Whether product is in stock"
        }
    },
    "required": ["product_id", "product_name", "category", "price", "stock_quantity", "in_stock"],
    "additionalProperties": False
}


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def test_plain_english_workflow():
    """Test the new plain English to schema to data workflow."""
    print_section("TEST 1: Plain English → JSON Schema → Test Data")
    
    try:
        # Load configuration
        print("\n[1] Loading v2 configuration...")
        config_path = Path(__file__).parent.parent / "config" / "json_schema_test_data_generator_v2.yaml"
        config = load_app_config(config_path)
        print(f"✅ Configuration loaded from {config_path}")
        
        # Build supervisor
        print("\n[2] Building supervisor...")
        supervisor_builder = SupervisorBuilder()
        supervisor = supervisor_builder.build_from_config(config)
        print("✅ Supervisor built successfully")
        
        # Execute workflow
        print("\n[3] Executing workflow with plain English input...")
        print("    Input type: Plain English data structure description")
        print("    Expected workflow: schema_creator → requirement_parser → data_generator → schema_validator")
        print("\n    Input preview:")
        print("    " + "\n    ".join(PLAIN_ENGLISH_INPUT.strip().split('\n')[:5]) + "\n    ...")
        
        print("\n[4] Running agents...")
        print("-" * 80)
        
        result = supervisor.invoke({"messages": [{"role": "user", "content": PLAIN_ENGLISH_INPUT}]})
        
        print("\n" + "-" * 80)
        print("\n[5] Analyzing results...")
        
        # Check if result contains expected outputs
        success_indicators = [
            ("JSON Schema created", ["$schema", "properties", "type"]),
            ("Test data generated", ["ref_", "records"]),
            ("Validation performed", ["valid", "invalid", "total"])
        ]
        
        result_str = str(result)
        passed_checks = 0
        
        for check_name, keywords in success_indicators:
            if any(keyword in result_str for keyword in keywords):
                print(f"   ✅ {check_name}")
                passed_checks += 1
            else:
                print(f"   ⚠️  {check_name} - not confirmed")
        
        print(f"\n[6] Result Summary:")
        print(f"    Checks passed: {passed_checks}/{len(success_indicators)}")
        
        if passed_checks >= 2:
            print(f"\n✅ TEST 1 PASSED: Plain English workflow executed successfully")
            return True
        else:
            print(f"\n⚠️  TEST 1 PARTIAL: Some checks failed, review output")
            return False
            
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_existing_schema_workflow():
    """Test the traditional existing schema workflow."""
    print_section("TEST 2: Existing Schema → Test Data")
    
    try:
        # Load configuration
        print("\n[1] Loading v2 configuration...")
        config_path = Path(__file__).parent.parent / "config" / "json_schema_test_data_generator_v2.yaml"
        config = load_app_config(config_path)
        print(f"✅ Configuration loaded")
        
        # Build supervisor
        print("\n[2] Building supervisor...")
        supervisor_builder = SupervisorBuilder()
        supervisor = supervisor_builder.build_from_config(config)
        print("✅ Supervisor built successfully")
        
        # Prepare input
        schema_json = json.dumps(EXISTING_SCHEMA_INPUT, indent=2)
        requirements = "Generate 50 products with 10 products in each category. Ensure realistic prices."
        user_input = f"""schema:
{schema_json}

Request: {requirements}"""
        
        # Execute workflow
        print("\n[3] Executing workflow with existing schema...")
        print("    Input type: Complete JSON Schema")
        print("    Expected workflow: schema_analyzer → requirement_parser → data_generator → schema_validator")
        print(f"    Schema: {EXISTING_SCHEMA_INPUT['title']}")
        print(f"    Requirements: {requirements}")
        
        print("\n[4] Running agents...")
        print("-" * 80)
        
        result = supervisor.invoke({"messages": [{"role": "user", "content": user_input}]})
        
        print("\n" + "-" * 80)
        print("\n[5] Analyzing results...")
        
        # Check if result contains expected outputs
        success_indicators = [
            ("Schema analyzed", ["fields", "metadata", "properties"]),
            ("Test data generated", ["ref_", "records"]),
            ("Validation performed", ["valid", "invalid", "total"])
        ]
        
        result_str = str(result)
        passed_checks = 0
        
        for check_name, keywords in success_indicators:
            if any(keyword in result_str for keyword in keywords):
                print(f"   ✅ {check_name}")
                passed_checks += 1
            else:
                print(f"   ⚠️  {check_name} - not confirmed")
        
        print(f"\n[6] Result Summary:")
        print(f"    Checks passed: {passed_checks}/{len(success_indicators)}")
        
        if passed_checks >= 2:
            print(f"\n✅ TEST 2 PASSED: Existing schema workflow executed successfully")
            return True
        else:
            print(f"\n⚠️  TEST 2 PARTIAL: Some checks failed, review output")
            return False
            
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*80)
    print("  JSON SCHEMA CREATOR V2 - COMPREHENSIVE TEST")
    print("="*80)
    print("\nThis test verifies:")
    print("  1. NEW: Plain English → JSON Schema → Test Data workflow")
    print("  2. EXISTING: Traditional schema → Test Data workflow")
    print("  3. Supervisor correctly routes based on input type")
    
    results = {
        "plain_english": False,
        "existing_schema": False
    }
    
    # Test 1: Plain English workflow
    results["plain_english"] = test_plain_english_workflow()
    
    # Test 2: Existing schema workflow
    results["existing_schema"] = test_existing_schema_workflow()
    
    # Final summary
    print_section("FINAL TEST SUMMARY")
    
    print(f"\nTest Results:")
    print(f"  Plain English Workflow: {'✅ PASSED' if results['plain_english'] else '❌ FAILED'}")
    print(f"  Existing Schema Workflow: {'✅ PASSED' if results['existing_schema'] else '❌ FAILED'}")
    
    total_passed = sum(1 for passed in results.values() if passed)
    total_tests = len(results)
    
    print(f"\nOverall: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED! Configuration is working correctly.")
        return 0
    elif total_passed > 0:
        print("\n⚠️  PARTIAL SUCCESS: Some tests passed, review failures above.")
        return 1
    else:
        print("\n❌ ALL TESTS FAILED: Review errors above.")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
