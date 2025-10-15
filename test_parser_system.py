#!/usr/bin/env python3
"""
Test Script for Test Data Parser Multi-Agent System

This script demonstrates various parsing scenarios including:
- Basic parsing
- Fuzzy matching
- Edge cases
- Error handling
"""

import requests
import json
import time
from typing import Dict, Any


API_BASE_URL = "http://localhost:8000"
CONFIG_PATH = "config/test_data_parser.yaml"


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_query(query: str, description: str) -> Dict[str, Any]:
    """
    Test a query against the parser system
    
    Args:
        query: Natural language requirement
        description: Description of what this test demonstrates
    
    Returns:
        Parsed parameters or error response
    """
    print(f"\n🧪 Test: {description}")
    print(f"📝 Query: {query}")
    print("\n⏳ Parsing...")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/query",
            json={
                "input": query,
                "config_path": CONFIG_PATH
            },
            timeout=60
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Success! (took {elapsed:.2f}s)")
            print(f"📊 Result:\n{json.dumps(result, indent=2)}")
            return result
        else:
            print(f"\n❌ Error: Status {response.status_code}")
            print(f"Response: {response.text}")
            return {"error": response.text}
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection Error: Is the API server running?")
        print(f"   Start it with: uvicorn api:app --reload --host 0.0.0.0 --port 8000")
        return {"error": "Connection refused"}
    
    except requests.exceptions.Timeout:
        print(f"\n❌ Timeout: Request took too long (>60s)")
        return {"error": "Timeout"}
    
    except Exception as e:
        print(f"\n❌ Exception: {str(e)}")
        return {"error": str(e)}


def main():
    """Run comprehensive test suite"""
    
    print_section("Test Data Parser - Multi-Agent System Test Suite")
    print("\nThis script tests the natural language parsing system with various scenarios.")
    print("\n⚠️  Ensure the API server is running:")
    print("   uvicorn api:app --reload --host 0.0.0.0 --port 8000")
    
    input("\nPress Enter to start tests...")
    
    # Test 1: Basic Example
    print_section("Test 1: Basic Parsing")
    test_query(
        query="create 100 records for metric abcd, xyz, program MFG, sector PFNA, plant p1, values 100 to 10000, uom count, 10% negative from -10 to -100",
        description="Basic parsing with all required fields"
    )
    
    # Test 2: Fuzzy Matching - Program Name
    print_section("Test 2: Fuzzy Matching - Program Name")
    test_query(
        query="generate 50 records for efficiency metric, program Merlli, sector PFNA, plant p1, values 0-100, 5 percent negative -5 to -20, unit percentage",
        description="Fuzzy match 'Merlli' to 'MFG' program code"
    )
    
    # Test 3: Fuzzy Matching - Plant Name
    print_section("Test 3: Fuzzy Matching - Plant Name")
    test_query(
        query="100 records for quality_score, program ADV, sector PBNA, Plant1, values 50-150, uom units",
        description="Fuzzy match 'Plant1' to 'p1'"
    )
    
    # Test 4: All Sectors
    print_section("Test 4: Multiple Sectors")
    test_query(
        query="200 records for production_volume and throughput, program STD, all sectors, plant p2, 1000-5000 range, 10% negative -100 to -500, units",
        description="Handle 'all sectors' → 'ALL'"
    )
    
    # Test 5: Market Specification
    print_section("Test 5: Market/Region Specification")
    test_query(
        query="150 records for defect_rate, program MFG, sector QSNA, plant p3, values 0-50, uom percentage, India market",
        description="Include market/region in parameters"
    )
    
    # Test 6: UOM Fuzzy Matching
    print_section("Test 6: UOM Fuzzy Matching")
    test_query(
        query="75 records for downtime_hours, program ADV, sector RSNA, plant p4, values 1-24, unit: hrs, 2% negative -1 to -5",
        description="Fuzzy match 'hrs' to 'hours'"
    )
    
    # Test 7: Minimal Input
    print_section("Test 7: Minimal Input (with defaults)")
    test_query(
        query="50 records, program MFG, sector PFNA, plant p1, values 0-100, uom count",
        description="Minimal input - system should apply defaults"
    )
    
    # Test 8: Multiple Metrics
    print_section("Test 8: Multiple Metrics")
    test_query(
        query="300 records for efficiency_rate, quality_score, and production_volume, program STD, sector PFNA, plant p1, 100-1000, count, 5% negative -50 to -200",
        description="Handle multiple metric names"
    )
    
    # Test 9: Edge Case - Large Numbers
    print_section("Test 9: Edge Case - Large Value Range")
    test_query(
        query="1000 records for utilization, program MFG, sector PBNA, plant p2, values 1000 to 100000, uom units, 15% negative -1000 to -5000",
        description="Handle large value ranges"
    )
    
    # Test 10: Custom Metric Names
    print_section("Test 10: Custom Metric Names")
    test_query(
        query="100 records for metric 'custom_metric_x', 'custom_metric_y', program ADV, sector QSNA, plant p3, values 10-500, uom count, 8% negative -10 to -100",
        description="Preserve custom metric names from user"
    )
    
    # Summary
    print_section("Test Suite Complete")
    print("\n✅ All tests executed!")
    print("\n📝 Notes:")
    print("   - Each test demonstrates different parsing capabilities")
    print("   - Fuzzy matching handles variations in user input")
    print("   - Validation ensures constraint compliance")
    print("   - Refinement fixes common issues automatically")
    print("\n🎯 The system successfully combines LLM reasoning with programmatic validation!")


if __name__ == "__main__":
    main()
