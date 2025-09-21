#!/usr/bin/env python3
"""
Comprehensive test to verify the DefectAnalysisPipeline returns root causes and corrective actions
in the exact format specified by the user and ontology.
"""

import asyncio
import json
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gemba_agents.defect_analysis.pipeline import DefectAnalysisPipeline
from gemba_agents.defect_analysis.models.data_models import DefectAnalysisConfig


async def test_format_compliance():
    """Test that the pipeline returns the exact format specified by the user."""
    
    print("Testing DefectAnalysisPipeline format compliance...")
    print("Expected format:")
    print('  Root cause: {"root_cause_code": "RC.ABRASION.EXTERNAL", "root_cause_text": "Abrasion from external contact..."}')
    print('  Corrective action: {"action_code": "CA.ALIGN.ADJUST", "action_text": "Adjust alignment of components..."}')
    
    # Create pipeline with default config
    config = DefectAnalysisConfig(enable_logging=False)  # Disable logging for cleaner output
    pipeline = DefectAnalysisPipeline(config)
    
    # Test input
    test_input = "Hydraulic hose is damaged and leaking"
    
    try:
        print(f"\nRunning pipeline with input: '{test_input}'")
        result = await pipeline.run(test_input)
        
        print(f"\nPipeline completed successfully!")
        print(f"Total unique results: {result.total_unique_results}")
        
        # Test root causes format
        print(f"\nRoot Causes ({len(result.root_causes)}):")
        for i, rc in enumerate(result.root_causes[:5]):  # Show first 5
            print(f"  {i+1}. {{'root_cause_code': '{rc.root_cause_code}', 'root_cause_text': '{rc.root_cause_text}'}}")
            
            # Verify exact format
            assert hasattr(rc, 'root_cause_code'), "Missing root_cause_code attribute"
            assert hasattr(rc, 'root_cause_text'), "Missing root_cause_text attribute"
            assert isinstance(rc.root_cause_code, str), "root_cause_code must be string"
            assert isinstance(rc.root_cause_text, str), "root_cause_text must be string"
            assert rc.root_cause_code.startswith('RC.'), f"root_cause_code should start with 'RC.': {rc.root_cause_code}"
        
        # Test corrective actions format
        print(f"\nCorrective Actions ({len(result.corrective_actions)}):")
        for i, ca in enumerate(result.corrective_actions[:5]):  # Show first 5
            print(f"  {i+1}. {{'action_code': '{ca.action_code}', 'action_text': '{ca.action_text}'}}")
            
            # Verify exact format
            assert hasattr(ca, 'action_code'), "Missing action_code attribute"
            assert hasattr(ca, 'action_text'), "Missing action_text attribute"
            assert isinstance(ca.action_code, str), "action_code must be string"
            assert isinstance(ca.action_text, str), "action_text must be string"
            assert ca.action_code.startswith('CA.'), f"action_code should start with 'CA.': {ca.action_code}"
        
        # Test JSON serialization (to ensure it can be serialized properly)
        print(f"\nTesting JSON serialization...")
        result_dict = result.model_dump()
        json_str = json.dumps(result_dict, indent=2)
        print("✅ JSON serialization successful!")
        
        # Verify the JSON contains the expected structure
        parsed = json.loads(json_str)
        if parsed['root_causes']:
            first_rc = parsed['root_causes'][0]
            assert 'root_cause_code' in first_rc, "JSON missing root_cause_code"
            assert 'root_cause_text' in first_rc, "JSON missing root_cause_text"
        
        if parsed['corrective_actions']:
            first_ca = parsed['corrective_actions'][0]
            assert 'action_code' in first_ca, "JSON missing action_code"
            assert 'action_text' in first_ca, "JSON missing action_text"
        
        print("✅ All format compliance tests passed!")
        print("\n🎉 The pipeline now returns root causes and corrective actions in the exact format specified by the ontology!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Format compliance test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function to run the test."""
    success = asyncio.run(test_format_compliance())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
