"""
KISS Principle Demo: JSON Defects Upsert

This script demonstrates the simplest possible way to upsert defects
from a JSON string using the VectorDB wrapper. Following KISS principles:
- Keep It Simple, Stupid
- One-liner usage
- Both async and sync options
"""

import json
from vectordb_wrapper import upsert_json_defects, upsert_json_defects_sync


# Your JSON string (same format as provided)
JSON_STRING = """
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


def demo_sync_usage():
    """Demonstrate synchronous usage (KISS principle)."""
    print("🔧 SYNC Usage (Simplest - KISS Principle)")
    print("=" * 50)
    
    # ONE LINE OF CODE - KISS!
    result = upsert_json_defects_sync(JSON_STRING)
    
    # Print results
    print(f"✅ Upserted {result['successful_upserts']} out of {result['total_defects']} defects")
    
    if result['successful_upserts'] > 0:
        print("   Successfully upserted:")
        for res in result['results']:
            print(f"   - {res['defect_code']}: {res['operation']}")
    
    if result['failed_upserts'] > 0:
        print("   Failed upserts:")
        for error in result['errors']:
            print(f"   - {error['defect_code']}: {error['error']}")
    
    print()


async def demo_async_usage():
    """Demonstrate asynchronous usage."""
    print("🚀 ASYNC Usage")
    print("=" * 20)
    
    # ONE LINE OF CODE - KISS!
    result = await upsert_json_defects(JSON_STRING)
    
    print(f"✅ Upserted {result['successful_upserts']} out of {result['total_defects']} defects")
    print()


def demo_from_file():
    """Demonstrate reading JSON from file."""
    print("📁 From File Usage")
    print("=" * 20)
    
    # Save JSON to file first
    with open("sample_defects.json", "w") as f:
        f.write(JSON_STRING)
    
    # Read and upsert in one go
    with open("sample_defects.json", "r") as f:
        json_content = f.read()
    
    result = upsert_json_defects_sync(json_content)
    print(f"✅ Upserted {result['successful_upserts']} defects from file")
    
    # Clean up
    import os
    os.remove("sample_defects.json")
    print()


def demo_error_handling():
    """Demonstrate error handling."""
    print("⚠️  Error Handling Demo")
    print("=" * 25)
    
    # Test with invalid JSON
    invalid_json = '{"defects": [{"defect_code": ""}]}'  # Empty defect_code should fail
    
    try:
        result = upsert_json_defects_sync(invalid_json)
        print(f"   Successful: {result['successful_upserts']}")
        print(f"   Failed: {result['failed_upserts']}")
        if result['errors']:
            print(f"   Error: {result['errors'][0]['error']}")
    except Exception as e:
        print(f"   Caught exception: {e}")
    
    print()


if __name__ == "__main__":
    print("🎯 VectorDB JSON Upsert - KISS Principle Demo")
    print("=" * 60)
    print()
    
    # Demonstrate different usage patterns
    demo_sync_usage()
    
    # Async demo
    import asyncio
    asyncio.run(demo_async_usage())
    
    # File demo
    demo_from_file()
    
    # Error handling demo
    demo_error_handling()
    
    # Show the code examples
    print("💡 Code Examples:")
    print("=" * 20)
    print()
    print("# Synchronous (simplest):")
    print("from vectordb_wrapper import upsert_json_defects_sync")
    print("result = upsert_json_defects_sync(json_string)")
    print("print(f'Upserted {result[\"successful_upserts\"]} defects')")
    print()
    print("# Asynchronous:")
    print("from vectordb_wrapper import upsert_json_defects")
    print("result = await upsert_json_defects(json_string)")
    print("print(f'Upserted {result[\"successful_upserts\"]} defects')")
    print()
    print("# From file:")
    print("with open('defects.json', 'r') as f:")
    print("    result = upsert_json_defects_sync(f.read())")
    print()
    print("🎉 That's it! KISS principle in action!")
