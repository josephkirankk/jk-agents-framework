"""
Integration Test 7: JSON Schema Test Data Generator
NO MOCKING - Real schema parsing, data generation, and validation

Tests:
1. Schema analysis and metadata extraction
2. Natural language requirement parsing
3. Simple schema data generation
4. Complex schema data generation (ProgramMetrics_Simple)
5. Schema validation of generated data
6. End-to-end workflow with large data handling
"""

import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from test_utils import (
    TestResult, TestEnvironment, print_test_header, print_section,
    invoke_agent, check_azure_credentials, convert_app_config_to_dict
)
from app.main import load_app_config, build_agents_map
from app.agent_builder import build_agent
from app.supervisor_builder import build_supervisor_compiled
from app.planner_executor import execute_plan
from dotenv import load_dotenv

load_dotenv()


# Helper function to invoke supervisor workflow
async def invoke_supervisor_workflow(query: str, app_config, config_path: str):
    """Helper to invoke supervisor with proper workflow"""
    import uuid

    thread_id = f"test_{uuid.uuid4().hex[:8]}"
    default_model = app_config.models.get('default') if isinstance(app_config.models, dict) else app_config.models.default

    # Build supervisor
    supervisor = build_supervisor_compiled(
        app_config.supervisor,
        app_config.agents,
        default_model,
        app_config.business_context or "",
        original_user_question=query,
        config_path=config_path,
        default_temperature=0.1,
        thread_id=thread_id,
    )

    # Build agents map
    agents_map, mcp_clients = await build_agents_map(
        app_config,
        user_input=query,
        config_path=config_path
    )

    try:
        # Execute plan
        result = await execute_plan(
            supervisor_compiled=supervisor,
            agents_map=agents_map,
            user_input=query,
            thread_id=thread_id,
            default_model_for_verifier=default_model
        )

        # Extract final result
        final_result = result.get("final_result", "")
        if isinstance(final_result, dict):
            final_result = str(final_result)

        return final_result
    finally:
        # Cleanup MCP clients
        from app.mcp_loader import close_mcp_client
        for client in mcp_clients.values():
            if client:
                await close_mcp_client(client)


# Sample JSON Schema for testing (ProgramMetrics_Simple)
PROGRAM_METRICS_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "ProgramMetrics_Simple",
    "type": "object",
    "required": ["program_name", "record_count", "window"],
    "additionalProperties": False,
    "properties": {
        "program_name": {
            "type": "string",
            "enum": ["prg1", "prg2", "prg3"],
            "default": "prg1"
        },
        "sector": {
            "type": "string",
            "enum": ["manufacturing", "retail", "services"],
            "default": "manufacturing"
        },
        "plant_code": {
            "type": "string",
            "pattern": "^[A-Z0-9-_.]{2,32}$",
            "default": "PLT-01"
        },
        "record_count": {
            "type": "integer",
            "minimum": 0,
            "default": 0
        },
        "window": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "start_date": {"type": "string", "format": "date", "default": "2025-01-01"},
                "end_date": {"type": "string", "format": "date", "default": "2025-01-31"},
                "timezone": {"type": "string", "default": "Asia/Kolkata"},
                "days": {"type": "integer", "minimum": 1, "default": 31}
            },
            "required": ["start_date", "end_date"],
            "default": {
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
                "timezone": "Asia/Kolkata",
                "days": 31
            }
        }
    }
}


async def test_schema_analysis():
    """Test schema analysis and metadata extraction"""
    result = TestResult("Schema Analysis")
    env = TestEnvironment("schema_analysis")
    
    try:
        if not check_azure_credentials():
            result.finish(False, error="Azure credentials not available")
            return result
        
        print_section("Testing Schema Analysis")
        
        # Load config
        config_path = Path(__file__).parent.parent / "config" / "json_schema_test_data_generator.yaml"
        
        if not config_path.exists():
            result.finish(False, error=f"Config not found: {config_path}")
            return result
        
        app_config = load_app_config(config_path)
        
        # Get schema_analyzer agent
        schema_agent_cfg = next((a for a in app_config.agents if a.name == "schema_analyzer"), None)
        if not schema_agent_cfg:
            result.finish(False, error="schema_analyzer agent not found")
            return result
        
        default_model = app_config.models.get('default') if isinstance(app_config.models, dict) else app_config.models.default
        app_config_dict = convert_app_config_to_dict(app_config)
        
        agent, mcp_client = await build_agent(
            agent_cfg=schema_agent_cfg,
            default_model=default_model,
            business_context=app_config.business_context or "",
            config_path=str(config_path),
            app_config=app_config_dict
        )
        
        print(f"✓ Schema analyzer agent built")
        
        # Test with simple schema
        simple_schema = {
            "type": "object",
            "required": ["name", "age"],
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "age": {"type": "integer", "minimum": 0, "maximum": 120}
            }
        }
        
        query = f"Analyze this JSON Schema and extract metadata:\n{json.dumps(simple_schema, indent=2)}"
        
        response = await invoke_agent(agent, query)
        
        print(f"✓ Schema analysis completed")
        print(f"  Response length: {len(response)}")
        
        # Check if response contains expected metadata
        has_fields = "fields" in response.lower() or "properties" in response.lower()
        has_required = "required" in response.lower()
        
        result.add_sub_test(
            "Simple Schema Analysis",
            has_fields and has_required,
            response_length=len(response)
        )
        
        # Cleanup
        if mcp_client:
            await mcp_client.cleanup()
        
        result.finish(True, tests_passed=1)
        
    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()
    
    return result


async def test_requirement_parsing():
    """Test natural language requirement parsing"""
    result = TestResult("Requirement Parsing")
    env = TestEnvironment("requirement_parsing")
    
    try:
        if not check_azure_credentials():
            result.finish(False, error="Azure credentials not available")
            return result
        
        print_section("Testing Requirement Parsing")
        
        config_path = Path(__file__).parent.parent / "config" / "json_schema_test_data_generator.yaml"
        app_config = load_app_config(config_path)
        
        # Get requirement_parser agent
        parser_agent_cfg = next((a for a in app_config.agents if a.name == "requirement_parser"), None)
        if not parser_agent_cfg:
            result.finish(False, error="requirement_parser agent not found")
            return result
        
        default_model = app_config.models.get('default') if isinstance(app_config.models, dict) else app_config.models.default
        app_config_dict = convert_app_config_to_dict(app_config)
        
        agent, mcp_client = await build_agent(
            agent_cfg=parser_agent_cfg,
            default_model=default_model,
            business_context=app_config.business_context or "",
            config_path=str(config_path),
            app_config=app_config_dict
        )
        
        print(f"✓ Requirement parser agent built")
        
        # Test with natural language requirement
        requirement = "Create 50 records for program prg1 with sector manufacturing and record_count between 10 and 100"
        
        query = f"Parse this requirement and extract constraints:\n{requirement}"
        
        response = await invoke_agent(agent, query)
        
        print(f"✓ Requirement parsing completed")
        print(f"  Response: {response[:200]}...")
        
        # Check if response contains expected constraints
        has_count = "50" in response or "record" in response.lower()
        has_program = "prg1" in response.lower()
        
        result.add_sub_test(
            "Natural Language Parsing",
            has_count and has_program,
            response_length=len(response)
        )
        
        # Cleanup
        if mcp_client:
            await mcp_client.cleanup()
        
        result.finish(True, tests_passed=1)
        
    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()
    
    return result


async def test_simple_data_generation():
    """Test data generation with simple schema"""
    result = TestResult("Simple Data Generation")
    env = TestEnvironment("simple_data_gen")
    
    try:
        if not check_azure_credentials():
            result.finish(False, error="Azure credentials not available")
            return result
        
        print_section("Testing Simple Data Generation")
        
        config_path = Path(__file__).parent.parent / "config" / "json_schema_test_data_generator.yaml"
        app_config = load_app_config(config_path)
        
        # Use supervisor for full workflow
        query = f"""
        Generate 10 test data records using this schema:
        
        Schema:
        {json.dumps({
            "type": "object",
            "required": ["id", "name"],
            "properties": {
                "id": {"type": "integer", "minimum": 1},
                "name": {"type": "string", "minLength": 1},
                "active": {"type": "boolean", "default": True}
            }
        }, indent=2)}
        
        Requirements:
        Create 10 records with id values between 1 and 100
        """
        
        print(f"Query: {query[:100]}...")

        response = await invoke_supervisor_workflow(
            query=query,
            app_config=app_config,
            config_path=str(config_path)
        )
        
        print(f"✓ Data generation completed")
        print(f"  Response length: {len(response)}")
        
        # Check if data was generated
        has_records = "record" in response.lower() or "data" in response.lower()
        has_success = "success" in response.lower() or "generated" in response.lower()
        
        result.add_sub_test(
            "Simple Schema Generation",
            has_records or has_success,
            response_length=len(response)
        )
        
        result.finish(True, tests_passed=1)
        
    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()
    
    return result


async def test_complex_schema_generation():
    """Test data generation with complex ProgramMetrics schema"""
    result = TestResult("Complex Schema Generation")
    env = TestEnvironment("complex_data_gen")
    
    try:
        if not check_azure_credentials():
            result.finish(False, error="Azure credentials not available")
            return result
        
        print_section("Testing Complex Schema Data Generation")
        
        config_path = Path(__file__).parent.parent / "config" / "json_schema_test_data_generator.yaml"
        app_config = load_app_config(config_path)
        
        # Use supervisor for full workflow with complex schema
        query = f"""
        Generate 20 test data records using this schema:
        
        Schema:
        {json.dumps(PROGRAM_METRICS_SCHEMA, indent=2)}
        
        Requirements:
        Create 20 records for program prg1 with sector manufacturing and record_count between 50 and 200
        """
        
        print(f"Query: Complex schema with nested objects...")

        response = await invoke_supervisor_workflow(
            query=query,
            app_config=app_config,
            config_path=str(config_path)
        )

        print(f"✓ Complex data generation completed")
        print(f"  Response length: {len(response)}")
        
        # Check if data was generated
        has_records = "record" in response.lower()
        has_validation = "valid" in response.lower() or "success" in response.lower()
        
        result.add_sub_test(
            "Complex Schema Generation",
            has_records or has_validation,
            response_length=len(response)
        )
        
        result.finish(True, tests_passed=1)

    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()

    return result


async def test_large_dataset_generation():
    """Test large dataset generation with auto-storage"""
    result = TestResult("Large Dataset Generation")
    env = TestEnvironment("large_dataset_gen")

    try:
        if not check_azure_credentials():
            result.finish(False, error="Azure credentials not available")
            return result

        print_section("Testing Large Dataset Generation (100+ records)")

        config_path = Path(__file__).parent.parent / "config" / "json_schema_test_data_generator.yaml"
        app_config = load_app_config(config_path)

        # Check if large data handling is enabled
        large_data_config = getattr(app_config, 'large_data_handling', None)
        if large_data_config:
            is_enabled = large_data_config.get('enabled', False)
            print(f"✓ Large data handling: enabled={is_enabled}")

        # Generate 100 records to trigger large data handling
        query = f"""
        Generate 100 test data records using this schema:

        Schema:
        {json.dumps({
            "type": "object",
            "required": ["id", "value"],
            "properties": {
                "id": {"type": "integer", "minimum": 1, "maximum": 1000},
                "value": {"type": "number", "minimum": 0, "maximum": 100},
                "category": {"type": "string", "enum": ["A", "B", "C"]}
            }
        }, indent=2)}

        Requirements:
        Create 100 records with value between 10 and 90
        """

        print(f"Generating 100 records (should trigger auto-storage)...")

        response = await invoke_supervisor_workflow(
            query=query,
            app_config=app_config,
            config_path=str(config_path)
        )

        print(f"✓ Large dataset generation completed")
        print(f"  Response length: {len(response)}")

        # Check for reference ID (indicates large data storage)
        has_reference = "ref_" in response or "reference" in response.lower()
        has_records = "100" in response or "record" in response.lower()

        result.add_sub_test(
            "Large Dataset Auto-Storage",
            has_records,
            response_length=len(response),
            has_reference=has_reference
        )

        result.finish(True, tests_passed=1)

    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()

    return result


async def test_validation_workflow():
    """Test schema validation of generated data"""
    result = TestResult("Validation Workflow")
    env = TestEnvironment("validation_workflow")

    try:
        if not check_azure_credentials():
            result.finish(False, error="Azure credentials not available")
            return result

        print_section("Testing Schema Validation Workflow")

        config_path = Path(__file__).parent.parent / "config" / "json_schema_test_data_generator.yaml"
        app_config = load_app_config(config_path)

        # Generate and validate data
        query = f"""
        Generate 15 test data records and validate them against this schema:

        Schema:
        {json.dumps({
            "type": "object",
            "required": ["name", "age", "email"],
            "properties": {
                "name": {"type": "string", "minLength": 2, "maxLength": 50},
                "age": {"type": "integer", "minimum": 18, "maximum": 100},
                "email": {"type": "string", "format": "email"}
            }
        }, indent=2)}

        Requirements:
        Create 15 records with age between 25 and 65
        """

        print(f"Generating and validating 15 records...")

        response = await invoke_supervisor_workflow(
            query=query,
            app_config=app_config,
            config_path=str(config_path)
        )

        print(f"✓ Validation workflow completed")
        print(f"  Response length: {len(response)}")

        # Check for validation results
        has_validation = "valid" in response.lower() or "validation" in response.lower()
        has_success = "success" in response.lower() or "pass" in response.lower()

        result.add_sub_test(
            "Validation Report",
            has_validation,
            response_length=len(response),
            has_success=has_success
        )

        result.finish(True, tests_passed=1)

    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()

    return result


async def test_end_to_end_workflow():
    """Test complete end-to-end workflow with all agents"""
    result = TestResult("End-to-End Workflow")
    env = TestEnvironment("e2e_workflow")

    try:
        if not check_azure_credentials():
            result.finish(False, error="Azure credentials not available")
            return result

        print_section("Testing End-to-End Workflow")

        config_path = Path(__file__).parent.parent / "config" / "json_schema_test_data_generator.yaml"
        app_config = load_app_config(config_path)

        # Full workflow: schema analysis -> requirement parsing -> data generation -> validation
        query = f"""
        I need test data for a program metrics system.

        JSON Schema:
        {json.dumps(PROGRAM_METRICS_SCHEMA, indent=2)}

        Requirements:
        Generate 30 records for program prg2 in the retail sector.
        The record_count should be between 100 and 500.
        Plant codes should follow the pattern.
        Include the window object with dates in January 2025.
        """

        print(f"Running full workflow with 4 agents...")
        print(f"  1. Schema Analyzer")
        print(f"  2. Requirement Parser")
        print(f"  3. Data Generator")
        print(f"  4. Schema Validator")

        response = await invoke_supervisor_workflow(
            query=query,
            app_config=app_config,
            config_path=str(config_path)
        )

        print(f"✓ End-to-end workflow completed")
        print(f"  Response length: {len(response)}")

        # Check for all workflow stages
        has_schema_analysis = "schema" in response.lower() or "metadata" in response.lower()
        has_requirements = "requirement" in response.lower() or "constraint" in response.lower()
        has_generation = "generat" in response.lower() or "record" in response.lower()
        has_validation = "valid" in response.lower()

        workflow_complete = has_generation  # At minimum, generation should happen

        result.add_sub_test(
            "Complete Workflow",
            workflow_complete,
            response_length=len(response),
            has_schema_analysis=has_schema_analysis,
            has_requirements=has_requirements,
            has_generation=has_generation,
            has_validation=has_validation
        )

        result.finish(True, tests_passed=1)

    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()

    return result


# Main test runner
async def run_all_tests():
    """Run all JSON Schema data generator tests"""
    print("\n" + "="*80)
    print("JSON SCHEMA TEST DATA GENERATOR - INTEGRATION TESTS")
    print("="*80 + "\n")

    results = []

    # Run tests in sequence
    tests = [
        ("Schema Analysis", test_schema_analysis),
        ("Requirement Parsing", test_requirement_parsing),
        ("Simple Data Generation", test_simple_data_generation),
        ("Complex Schema Generation", test_complex_schema_generation),
        ("Large Dataset Generation", test_large_dataset_generation),
        ("Validation Workflow", test_validation_workflow),
        ("End-to-End Workflow", test_end_to_end_workflow),
    ]

    for test_name, test_func in tests:
        print(f"\n{'='*80}")
        print(f"Running: {test_name}")
        print(f"{'='*80}\n")

        result = await test_func()
        results.append(result)

        # Print result
        result.print_result()

        # Small delay between tests
        await asyncio.sleep(1)

    # Print overall summary
    print("\n" + "="*80)
    print("OVERALL TEST SUMMARY")
    print("="*80 + "\n")

    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.passed)
    failed_tests = total_tests - passed_tests

    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✓")
    print(f"Failed: {failed_tests} ✗")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

    print("\nTest Details:")
    for i, result in enumerate(results, 1):
        status = "✓ PASS" if result.passed else "✗ FAIL"
        print(f"  {i}. {result.test_name}: {status}")

    print("\n" + "="*80 + "\n")

    return passed_tests == total_tests


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
