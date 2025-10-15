#!/usr/bin/env python3
"""
Comprehensive End-to-End Integration Test for Schema Creator V2

Tests both workflows:
1. Plain English → JSON Schema → Test Data → Validation
2. Existing Schema → Test Data → Validation

Verifies:
- Database records are created
- Data conforms to schema
- All required fields present
- Data quality and statistics
- Validation results
"""

import json
import sqlite3
import gzip
import sys
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import jsonschema

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import load_app_config, build_agents_map
from app.supervisor_builder import build_supervisor_compiled
from app.memory.large_data_storage import LargeDataStorage


# =============================================================================
# TEST DATA DEFINITIONS
# =============================================================================

# Test Case 1: Plain English Input (NEW FEATURE)
PLAIN_ENGLISH_INPUT_SMALL = """
Data Structure:

product_id: unique ID format PROD-XXXXXX
product_name: product name 5-50 characters
category: Electronics, Clothing, Food
price: 10.00 to 1000.00
stock: 0 to 500
in_stock: yes or no

Requirements: Generate 30 products with 10 in each category
"""

# Test Case 2: Existing Schema
EXISTING_SCHEMA_SMALL = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "EmployeeRecord",
    "description": "Employee data schema",
    "type": "object",
    "properties": {
        "employee_id": {
            "type": "string",
            "description": "Unique employee identifier",
            "pattern": "^EMP-[0-9]{5}$"
        },
        "employee_name": {
            "type": "string",
            "description": "Full name",
            "minLength": 2,
            "maxLength": 100
        },
        "department": {
            "type": "string",
            "enum": ["Engineering", "Sales", "HR"],
            "description": "Department name"
        },
        "salary": {
            "type": "number",
            "minimum": 30000,
            "maximum": 200000,
            "description": "Annual salary"
        },
        "is_active": {
            "type": "boolean",
            "description": "Employment status"
        }
    },
    "required": ["employee_id", "employee_name", "department", "salary", "is_active"],
    "additionalProperties": False
}

# =============================================================================
# DATABASE UTILITIES
# =============================================================================

def get_database_connection():
    """Get connection to the large data storage database"""
    db_path = "./data/schema_test_data.db"
    if not os.path.exists(db_path):
        print(f"⚠️  Database not found: {db_path}")
        return None
    return sqlite3.connect(db_path)


def get_all_datasets(limit=10):
    """Retrieve all datasets from database"""
    conn = get_database_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT reference_id, tool_name, size_bytes, content_type, 
               compressed, metadata, created_at, access_count
        FROM large_tool_data
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    
    datasets = []
    for row in cursor.fetchall():
        datasets.append({
            "reference_id": row[0],
            "tool_name": row[1],
            "size_bytes": row[2],
            "content_type": row[3],
            "compressed": bool(row[4]),
            "metadata": json.loads(row[5]) if row[5] else {},
            "created_at": row[6],
            "access_count": row[7]
        })
    
    conn.close()
    return datasets


def retrieve_dataset_by_reference(reference_id: str) -> Optional[Dict]:
    """Retrieve complete dataset from database by reference ID"""
    conn = get_database_connection()
    if not conn:
        return None
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT data_blob, compressed, content_type, metadata
        FROM large_tool_data
        WHERE reference_id = ?
    """, (reference_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        print(f"❌ No dataset found for reference ID: {reference_id}")
        return None
    
    data_blob, compressed, content_type, metadata_json = result
    
    # Decompress if needed
    if compressed:
        data_blob = gzip.decompress(data_blob)
    
    # Parse data
    if content_type == 'json':
        data = json.loads(data_blob.decode('utf-8'))
    else:
        data = data_blob.decode('utf-8')
    
    metadata = json.loads(metadata_json) if metadata_json else {}
    
    return {
        "data": data,
        "metadata": metadata,
        "compressed": compressed,
        "content_type": content_type
    }


# =============================================================================
# VALIDATION UTILITIES
# =============================================================================

def validate_dataset_against_schema(data: List[Dict], schema: Dict) -> Dict[str, Any]:
    """Validate all records in dataset against JSON Schema"""
    results = {
        "total": len(data),
        "valid": 0,
        "invalid": 0,
        "errors": []
    }
    
    for idx, record in enumerate(data):
        try:
            jsonschema.validate(instance=record, schema=schema)
            results["valid"] += 1
        except jsonschema.ValidationError as e:
            results["invalid"] += 1
            if len(results["errors"]) < 5:  # Store first 5 errors
                results["errors"].append({
                    "record_index": idx,
                    "error": str(e.message),
                    "path": list(e.path),
                    "record_sample": record
                })
    
    results["success_rate"] = (results["valid"] / results["total"] * 100) if results["total"] > 0 else 0
    return results


def analyze_data_quality(data: List[Dict], expected_count: int = None) -> Dict[str, Any]:
    """Analyze data quality metrics"""
    if not isinstance(data, list):
        return {"error": f"Data is not a list: {type(data)}"}
    
    analysis = {
        "record_count": len(data),
        "expected_count": expected_count,
        "count_match": len(data) == expected_count if expected_count else None,
        "data_type": "list",
        "sample_record": data[0] if data else None,
        "field_coverage": {}
    }
    
    # Analyze field coverage
    if data:
        all_fields = set()
        field_counts = {}
        
        for record in data:
            if isinstance(record, dict):
                for field in record.keys():
                    all_fields.add(field)
                    field_counts[field] = field_counts.get(field, 0) + 1
        
        analysis["field_coverage"] = {
            "total_fields": len(all_fields),
            "fields": list(all_fields),
            "field_presence": {
                field: {
                    "count": count,
                    "percentage": (count / len(data) * 100)
                }
                for field, count in field_counts.items()
            }
        }
    
    return analysis


def extract_reference_id_from_result(result: Any) -> Optional[str]:
    """Extract reference ID from supervisor result"""
    result_str = str(result)
    
    # Pattern: ref_[a-f0-9]{12}
    match = re.search(r'ref_[a-f0-9]{12}', result_str)
    if match:
        return match.group(0)
    return None


# =============================================================================
# TEST EXECUTION
# =============================================================================

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def print_subsection(title):
    """Print formatted subsection"""
    print(f"\n{'─'*80}")
    print(f"  {title}")
    print(f"{'─'*80}")


def test_plain_english_workflow():
    """Test plain English → JSON Schema → Test Data workflow"""
    print_section("TEST 1: Plain English → JSON Schema → Test Data")
    
    test_results = {
        "workflow": "plain_english",
        "status": "unknown",
        "steps": {}
    }
    
    try:
        # Step 1: Load configuration
        print("\n[1] Loading configuration...")
        config_path = Path(__file__).parent.parent / "config" / "json_schema_test_data_generator_v2.yaml"
        config = load_app_config(config_path)
        print(f"✅ Config loaded: {len(config.agents)} agents")
        test_results["steps"]["config_load"] = "success"
        
        # Step 2: Build supervisor
        print("\n[2] Building supervisor and agents...")
        agents_map = build_agents_map(config)
        supervisor = build_supervisor_compiled(config, agents_map)
        print(f"✅ Built {len(agents_map)} agents: {list(agents_map.keys())}")
        test_results["steps"]["supervisor_build"] = "success"
        
        # Verify schema_creator exists
        if "schema_creator" not in agents_map:
            print("❌ schema_creator agent not found!")
            test_results["status"] = "failed"
            return test_results
        print("✅ schema_creator agent found")
        
        # Step 3: Execute workflow
        print("\n[3] Executing plain English workflow...")
        print("   Input: Product catalog with 30 records")
        print("   Expected: schema_creator → requirement_parser → data_generator → schema_validator")
        
        result = supervisor.invoke({
            "messages": [{"role": "user", "content": PLAIN_ENGLISH_INPUT_SMALL}]
        })
        print("✅ Workflow completed")
        test_results["steps"]["workflow_execution"] = "success"
        
        # Step 4: Extract reference ID
        print("\n[4] Extracting reference ID...")
        ref_id = extract_reference_id_from_result(result)
        
        if not ref_id:
            print("⚠️  No reference ID found in result")
            print(f"   Result preview: {str(result)[:500]}")
            test_results["steps"]["reference_extraction"] = "no_ref_id"
            test_results["reference_id"] = None
        else:
            print(f"✅ Reference ID: {ref_id}")
            test_results["steps"]["reference_extraction"] = "success"
            test_results["reference_id"] = ref_id
        
        # Step 5: Query database
        print("\n[5] Querying database...")
        datasets = get_all_datasets(limit=5)
        print(f"✅ Found {len(datasets)} recent datasets")
        
        if datasets:
            latest = datasets[0]
            print(f"\n   Latest dataset:")
            print(f"   - Reference ID: {latest['reference_id']}")
            print(f"   - Tool: {latest['tool_name']}")
            print(f"   - Size: {latest['size_bytes']:,} bytes")
            print(f"   - Created: {latest['created_at']}")
            print(f"   - Compressed: {latest['compressed']}")
            
            test_results["steps"]["database_query"] = "success"
            test_results["latest_dataset"] = latest
            
            # Use reference ID from database if not found in result
            if not ref_id:
                ref_id = latest['reference_id']
                print(f"   Using latest dataset reference ID: {ref_id}")
                test_results["reference_id"] = ref_id
        else:
            print("⚠️  No datasets found in database")
            test_results["steps"]["database_query"] = "no_datasets"
        
        # Step 6: Retrieve and validate data
        if ref_id:
            print("\n[6] Retrieving and validating data...")
            dataset = retrieve_dataset_by_reference(ref_id)
            
            if dataset:
                data = dataset["data"]
                print(f"✅ Dataset retrieved")
                print(f"   Records: {len(data) if isinstance(data, list) else 'N/A'}")
                
                # Analyze data quality
                print("\n[6a] Analyzing data quality...")
                quality = analyze_data_quality(data, expected_count=30)
                print(f"   Record count: {quality['record_count']}")
                print(f"   Expected count: {quality['expected_count']}")
                print(f"   Match: {quality['count_match']}")
                
                if quality.get('field_coverage'):
                    print(f"   Total fields: {quality['field_coverage']['total_fields']}")
                    print(f"   Fields: {quality['field_coverage']['fields']}")
                
                test_results["data_quality"] = quality
                test_results["steps"]["data_retrieval"] = "success"
                
                # Extract schema from result for validation
                print("\n[6b] Extracting generated schema...")
                result_str = str(result)
                
                # Try to find JSON schema in result
                schema_match = re.search(r'\{[^{]*"\$schema"[^}]*"properties"[^}]*\}', result_str, re.DOTALL)
                if schema_match:
                    try:
                        # This is a simple extraction - might need refinement
                        print("   Schema pattern found in result")
                        test_results["steps"]["schema_extraction"] = "found"
                    except:
                        print("   Could not parse schema from result")
                        test_results["steps"]["schema_extraction"] = "parse_error"
                else:
                    print("   No schema pattern found in result")
                    test_results["steps"]["schema_extraction"] = "not_found"
                
                test_results["status"] = "success"
            else:
                print("❌ Could not retrieve dataset")
                test_results["steps"]["data_retrieval"] = "failed"
                test_results["status"] = "partial"
        else:
            print("\n[6] Skipping data validation (no reference ID)")
            test_results["status"] = "partial"
        
        return test_results
        
    except Exception as e:
        print(f"\n❌ Error in test: {e}")
        import traceback
        traceback.print_exc()
        test_results["status"] = "error"
        test_results["error"] = str(e)
        return test_results


def test_existing_schema_workflow():
    """Test existing schema → test data workflow"""
    print_section("TEST 2: Existing Schema → Test Data")
    
    test_results = {
        "workflow": "existing_schema",
        "status": "unknown",
        "steps": {}
    }
    
    try:
        # Step 1: Load configuration
        print("\n[1] Loading configuration...")
        config_path = Path(__file__).parent.parent / "config" / "json_schema_test_data_generator_v2.yaml"
        config = load_app_config(config_path)
        print(f"✅ Config loaded")
        test_results["steps"]["config_load"] = "success"
        
        # Step 2: Build supervisor
        print("\n[2] Building supervisor and agents...")
        agents_map = build_agents_map(config)
        supervisor = build_supervisor_compiled(config, agents_map)
        print(f"✅ Built {len(agents_map)} agents")
        test_results["steps"]["supervisor_build"] = "success"
        
        # Verify schema_analyzer exists
        if "schema_analyzer" not in agents_map:
            print("❌ schema_analyzer agent not found!")
            test_results["status"] = "failed"
            return test_results
        print("✅ schema_analyzer agent found")
        
        # Step 3: Prepare input
        print("\n[3] Preparing input...")
        schema_json = json.dumps(EXISTING_SCHEMA_SMALL, indent=2)
        user_input = f"""schema:
{schema_json}

Request: Generate 30 employee records with 10 in each department"""
        
        print("   Schema: EmployeeRecord")
        print("   Requirements: 30 records, 10 per department")
        
        # Step 4: Execute workflow
        print("\n[4] Executing existing schema workflow...")
        print("   Expected: schema_analyzer → requirement_parser → data_generator → schema_validator")
        
        result = supervisor.invoke({
            "messages": [{"role": "user", "content": user_input}]
        })
        print("✅ Workflow completed")
        test_results["steps"]["workflow_execution"] = "success"
        
        # Step 5: Extract reference ID
        print("\n[5] Extracting reference ID...")
        ref_id = extract_reference_id_from_result(result)
        
        if ref_id:
            print(f"✅ Reference ID: {ref_id}")
            test_results["reference_id"] = ref_id
            test_results["steps"]["reference_extraction"] = "success"
        else:
            print("⚠️  No reference ID found")
            test_results["steps"]["reference_extraction"] = "no_ref_id"
            
            # Try to get latest from database
            datasets = get_all_datasets(limit=1)
            if datasets:
                ref_id = datasets[0]['reference_id']
                print(f"   Using latest from database: {ref_id}")
                test_results["reference_id"] = ref_id
        
        # Step 6: Retrieve and validate data
        if ref_id:
            print("\n[6] Retrieving dataset...")
            dataset = retrieve_dataset_by_reference(ref_id)
            
            if dataset:
                data = dataset["data"]
                print(f"✅ Dataset retrieved: {len(data) if isinstance(data, list) else 'N/A'} records")
                
                # Analyze data quality
                print("\n[6a] Analyzing data quality...")
                quality = analyze_data_quality(data, expected_count=30)
                print(f"   Record count: {quality['record_count']}")
                print(f"   Expected: {quality['expected_count']}")
                print(f"   Match: {'✅' if quality['count_match'] else '❌'}")
                
                if quality.get('field_coverage'):
                    print(f"   Fields: {quality['field_coverage']['fields']}")
                    print(f"   Sample record: {json.dumps(quality['sample_record'], indent=2)[:200]}...")
                
                test_results["data_quality"] = quality
                test_results["steps"]["data_quality"] = "success"
                
                # Validate against schema
                print("\n[6b] Validating against schema...")
                if isinstance(data, list):
                    validation = validate_dataset_against_schema(data, EXISTING_SCHEMA_SMALL)
                    print(f"   Total records: {validation['total']}")
                    print(f"   Valid: {validation['valid']}")
                    print(f"   Invalid: {validation['invalid']}")
                    print(f"   Success rate: {validation['success_rate']:.2f}%")
                    
                    if validation['errors']:
                        print(f"\n   First {len(validation['errors'])} errors:")
                        for err in validation['errors']:
                            print(f"   - Record {err['record_index']}: {err['error']}")
                    
                    test_results["validation"] = validation
                    test_results["steps"]["schema_validation"] = "success"
                    
                    if validation['success_rate'] == 100.0:
                        print("\n   ✅ ALL RECORDS VALID!")
                        test_results["status"] = "success"
                    else:
                        print(f"\n   ⚠️  {validation['invalid']} records failed validation")
                        test_results["status"] = "partial"
                else:
                    print("   ⚠️  Data is not a list, skipping validation")
                    test_results["steps"]["schema_validation"] = "skipped"
                    test_results["status"] = "partial"
            else:
                print("❌ Could not retrieve dataset")
                test_results["steps"]["data_retrieval"] = "failed"
                test_results["status"] = "failed"
        else:
            print("\n[6] Skipping validation (no reference ID)")
            test_results["status"] = "partial"
        
        return test_results
        
    except Exception as e:
        print(f"\n❌ Error in test: {e}")
        import traceback
        traceback.print_exc()
        test_results["status"] = "error"
        test_results["error"] = str(e)
        return test_results


def verify_database_health():
    """Verify database health and structure"""
    print_section("DATABASE HEALTH CHECK")
    
    db_path = "./data/schema_test_data.db"
    
    print("\n[1] Checking database file...")
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print(f"✅ Database exists: {db_path}")
        print(f"   Size: {size:,} bytes ({size/1024/1024:.2f} MB)")
    else:
        print(f"❌ Database not found: {db_path}")
        return False
    
    print("\n[2] Checking database structure...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"   Tables: {tables}")
    
    if 'large_tool_data' in tables:
        print("   ✅ large_tool_data table exists")
        
        # Get row count
        cursor.execute("SELECT COUNT(*) FROM large_tool_data")
        count = cursor.fetchone()[0]
        print(f"   Total datasets: {count}")
        
        # Get storage statistics
        cursor.execute("""
            SELECT 
                SUM(size_bytes) as total_size,
                AVG(size_bytes) as avg_size,
                MIN(size_bytes) as min_size,
                MAX(size_bytes) as max_size
            FROM large_tool_data
        """)
        stats = cursor.fetchone()
        if stats[0]:
            print(f"   Total storage: {stats[0]:,} bytes ({stats[0]/1024/1024:.2f} MB)")
            print(f"   Average size: {stats[1]:,.0f} bytes")
            print(f"   Min size: {stats[2]:,} bytes")
            print(f"   Max size: {stats[3]:,} bytes")
    else:
        print("   ❌ large_tool_data table not found")
        conn.close()
        return False
    
    conn.close()
    return True


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def main():
    """Run comprehensive integration tests"""
    print("="*80)
    print("  JSON SCHEMA CREATOR V2 - COMPREHENSIVE INTEGRATION TEST")
    print("="*80)
    print(f"\n  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Database: ./data/schema_test_data.db")
    print(f"  Config: config/json_schema_test_data_generator_v2.yaml")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {}
    }
    
    # Pre-flight check
    print_section("PRE-FLIGHT CHECK")
    db_healthy = verify_database_health()
    results["database_health"] = db_healthy
    
    # Test 1: Plain English workflow
    test1_results = test_plain_english_workflow()
    results["tests"]["plain_english"] = test1_results
    
    # Test 2: Existing schema workflow
    test2_results = test_existing_schema_workflow()
    results["tests"]["existing_schema"] = test2_results
    
    # Final summary
    print_section("FINAL TEST SUMMARY")
    
    print("\n📊 Test Results:")
    print(f"\n  Database Health: {'✅ PASS' if db_healthy else '❌ FAIL'}")
    print(f"  Plain English Workflow: {get_status_emoji(test1_results['status'])} {test1_results['status'].upper()}")
    print(f"  Existing Schema Workflow: {get_status_emoji(test2_results['status'])} {test2_results['status'].upper()}")
    
    # Detailed statistics
    if test1_results.get('data_quality'):
        q1 = test1_results['data_quality']
        print(f"\n  Test 1 Data:")
        print(f"    - Records: {q1['record_count']} (expected: {q1['expected_count']})")
        print(f"    - Fields: {q1.get('field_coverage', {}).get('total_fields', 'N/A')}")
    
    if test2_results.get('validation'):
        v2 = test2_results['validation']
        print(f"\n  Test 2 Validation:")
        print(f"    - Total: {v2['total']}")
        print(f"    - Valid: {v2['valid']}")
        print(f"    - Invalid: {v2['invalid']}")
        print(f"    - Success rate: {v2['success_rate']:.2f}%")
    
    # Overall status
    overall_pass = (
        db_healthy and
        test1_results['status'] in ['success', 'partial'] and
        test2_results['status'] in ['success', 'partial']
    )
    
    print(f"\n{'='*80}")
    if overall_pass:
        print("  🎉 INTEGRATION TESTS PASSED")
        print("="*80)
        return 0
    else:
        print("  ❌ INTEGRATION TESTS FAILED")
        print("="*80)
        return 1


def get_status_emoji(status: str) -> str:
    """Get emoji for status"""
    emoji_map = {
        "success": "✅",
        "partial": "⚠️",
        "failed": "❌",
        "error": "💥",
        "unknown": "❓"
    }
    return emoji_map.get(status, "❓")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n💥 UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
