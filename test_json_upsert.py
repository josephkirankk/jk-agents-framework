"""
Test script for JSON defects upsert functionality.

This script demonstrates how to use the new upsert_json_defects method
to seamlessly upsert defects from a JSON string.
"""

import asyncio
import json
from vectordb_wrapper import upsert_json_defects, VectorDBClient, SearchRequest


# Sample JSON string (same as provided by user)
SAMPLE_JSON = """
{
  "defects": [
    {
      "defect_code": "PLG.HYD.PMP.PISTON_STUCK",
      "defect_text": "Hydraulic pump piston not moving uniformly during loading/unloading.",
      "system": "Hydraulic System",
      "subsystem": "PMP",
      "component": "Hydraulic pump piston",
      "likely_root_causes": ["RC.HYD.PMP.CONTAMINATION", "RC.HYD.PMP.BEARING_FAILURE", "RC.HYD.PMP.SEAL_LEAK"],
      "recommended_actions": ["CA.HYD.PMP.CLEAN_FILTER", "CA.HYD.PMP.INSPECT_BEARING", "CA.HYD.PMP.REPLACE_SEAL"],
      "symptoms": ["Uneven piston movement", "Reduced pump output", "Increased noise"],
      "detection_methods": ["Visual inspection", "Pressure gauge monitoring", "Flow meter readings"],
      "early_warning_signals": ["Intermittent jerky motion", "Fluctuating pressure readings"],
      "tags": ["hydraulic pump", "piston", "loading", "unloading", "uneven movement"],
      "severity": "Medium",
      "typical_frequency": "Medium"
    },
    {
      "defect_code": "PLG.UTIL.AIRSYS.LOW_PRESSURE",
      "defect_text": "Low air pressure in the compressed air system, affecting pneumatic cylinder operation.",
      "system": "Utilities / Energy Supply",
      "subsystem": "AIRSYS",
      "component": "Compressed air system",
      "likely_root_causes": ["RC.AIRSYS.LEAK", "RC.AIRSYS.CMP_FAULT", "RC.AIRSYS.FILTER_CLOG"],
      "recommended_actions": ["CA.AIRSYS.FIND_LEAK", "CA.AIRSYS.INSPECT_COMPRESSOR", "CA.AIRSYS.CLEAN_FILTER"],
      "symptoms": ["Pneumatic cylinders not actuating properly", "Weak air flow", "Low pressure gauge reading"],
      "detection_methods": ["Pressure gauge monitoring", "Listening for air leaks", "Checking compressor status"],
      "early_warning_signals": ["Gradual decrease in system pressure", "Compressor running continuously"],
      "tags": ["air pressure", "low pressure", "compressor", "pneumatic cylinder", "air leak"],
      "severity": "High",
      "typical_frequency": "Medium"
    },
    {
      "defect_code": "PLG.PNE.CYL.ACTUATION_ISSUE",
      "defect_text": "Pneumatic cylinder not operating correctly due to insufficient air supply or internal fault.",
      "system": "Pneumatic System",
      "subsystem": "CYL",
      "component": "Pneumatic cylinder",
      "likely_root_causes": ["RC.PNE.CYL.SEAL_LEAK", "RC.PNE.CYL.VALVE_FAULT", "RC.PNE.CYL.LOW_AIR_PRESSURE"],
      "recommended_actions": ["CA.PNE.CYL.REPLACE_SEAL", "CA.PNE.CYL.INSPECT_VALVE", "CA.PNE.CYL.CHECK_AIR_SUPPLY"],
      "symptoms": ["Slow or incomplete cylinder stroke", "Jerky movement", "Failure to extend or retract"],
      "detection_methods": ["Visual inspection of cylinder movement", "Listening for air leaks", "Checking associated pneumatic valves"],
      "early_warning_signals": ["Slightly slower than normal operation", "Occasional hesitation"],
      "tags": ["pneumatic cylinder", "actuation", "slow", "incomplete stroke", "air cylinder issue"],
      "severity": "Medium",
      "typical_frequency": "Medium"
    }
  ]
}
"""


async def test_json_upsert():
    """Test the JSON upsert functionality."""
    print("🔧 Testing JSON Defects Upsert")
    print("=" * 50)
    
    try:
        # Method 1: Using the convenience function (KISS approach)
        print("1. 📤 Using convenience function upsert_json_defects()")
        result = await upsert_json_defects(SAMPLE_JSON)
        
        print(f"   Total defects: {result['total_defects']}")
        print(f"   Successful upserts: {result['successful_upserts']}")
        print(f"   Failed upserts: {result['failed_upserts']}")
        
        if result['successful_upserts'] > 0:
            print("   ✅ Successfully upserted defects:")
            for res in result['results']:
                print(f"     - {res['defect_code']}: {res['operation']} ({res['message']})")
        
        if result['failed_upserts'] > 0:
            print("   ❌ Failed upserts:")
            for error in result['errors']:
                print(f"     - {error['defect_code']}: {error['error']}")
        
        print()
        
        # Method 2: Using the client directly
        print("2. 🔍 Verifying upserted defects with search")
        async with VectorDBClient() as client:
            # Search for one of the upserted defects
            search_request = SearchRequest(
                query="hydraulic pump piston stuck",
                top_n=3,
                min_score=0.5
            )
            
            search_response = await client.search(search_request)
            print(f"   Found {search_response.total_results} results for 'hydraulic pump piston stuck'")
            
            # Check if our defect is in the results
            found_plg_defect = False
            for result in search_response.results:
                if "PLG.HYD.PMP.PISTON_STUCK" in result.defect.defect_code:
                    found_plg_defect = True
                    print(f"   ✅ Found our defect: {result.defect.defect_code} (Score: {result.score:.1%})")
                    print(f"      Text: {result.defect.defect_text}")
                    break
            
            if not found_plg_defect:
                print("   ℹ️  PLG defect not found in top results (may need lower min_score)")
        
        print()
        print("✅ JSON upsert test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise


async def test_simple_usage():
    """Demonstrate the simplest possible usage."""
    print("\n🚀 Simple Usage Example")
    print("=" * 30)
    
    # Create a minimal JSON for testing
    simple_json = """
    {
      "defects": [
        {
          "defect_code": "SIMPLE.TEST.001",
          "defect_text": "Simple test defect for demonstration",
          "subsystem": "TEST",
          "severity": "Low",
          "symptoms": ["Test symptom"],
          "tags": ["test", "simple", "demo"]
        }
      ]
    }
    """
    
    try:
        # One-liner usage (KISS principle)
        result = await upsert_json_defects(simple_json)
        
        print(f"✅ Upserted {result['successful_upserts']} defect(s) in one line!")
        if result['results']:
            defect = result['results'][0]
            print(f"   Defect: {defect['defect_code']} ({defect['operation']})")
        
    except Exception as e:
        print(f"❌ Simple test failed: {e}")


if __name__ == "__main__":
    print("Testing VectorDB JSON Upsert Functionality")
    print("=" * 60)
    
    # Run the tests
    asyncio.run(test_json_upsert())
    asyncio.run(test_simple_usage())
    
    print("\n🎯 Usage Summary:")
    print("   # Simplest usage (KISS principle):")
    print("   from vectordb_wrapper import upsert_json_defects")
    print("   result = await upsert_json_defects(json_string)")
    print("   print(f'Upserted {result[\"successful_upserts\"]} defects')")
