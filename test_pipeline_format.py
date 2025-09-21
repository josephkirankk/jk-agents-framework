#!/usr/bin/env python3
"""
Test script to verify the DefectAnalysisPipeline returns root causes and corrective actions
in the correct structured format as specified by the ontology.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gemba_agents.defect_analysis.pipeline import DefectAnalysisPipeline
from gemba_agents.defect_analysis.models.data_models import DefectAnalysisConfig


async def test_pipeline_format():
    """Test that the pipeline returns the correct structured format."""
    
    print("Testing DefectAnalysisPipeline format compliance...")
    
    # Create pipeline with default config
    config = DefectAnalysisConfig(enable_logging=True)
    pipeline = DefectAnalysisPipeline(config)
    
    # Test input
    test_input = "The pump's loading/unloading piston is not operating smoothly"
    
    try:
        print(f"\nRunning pipeline with input: '{test_input}'")
        result = await pipeline.run(test_input)
        
        print(f"\nPipeline completed successfully!")
        print(f"Total unique results: {result.total_unique_results}")
        print(f"Processing time: {result.processing_time_ms:.2f}ms")
        
        # Check root causes format
        print(f"\nRoot Causes ({len(result.root_causes)}):")
        for i, rc in enumerate(result.root_causes[:3]):  # Show first 3
            print(f"  {i+1}. Code: {rc.root_cause_code}")
            print(f"     Text: {rc.root_cause_text}")
        
        # Check corrective actions format
        print(f"\nCorrective Actions ({len(result.corrective_actions)}):")
        for i, ca in enumerate(result.corrective_actions[:3]):  # Show first 3
            print(f"  {i+1}. Code: {ca.action_code}")
            print(f"     Text: {ca.action_text}")
        
        # Verify the format is correct
        if result.root_causes:
            first_rc = result.root_causes[0]
            assert hasattr(first_rc, 'root_cause_code'), "Root cause missing 'root_cause_code'"
            assert hasattr(first_rc, 'root_cause_text'), "Root cause missing 'root_cause_text'"
            print("\n✅ Root cause format is correct!")
        
        if result.corrective_actions:
            first_ca = result.corrective_actions[0]
            assert hasattr(first_ca, 'action_code'), "Corrective action missing 'action_code'"
            assert hasattr(first_ca, 'action_text'), "Corrective action missing 'action_text'"
            print("✅ Corrective action format is correct!")
        
        print("\n🎉 All format checks passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Pipeline test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function to run the test."""
    success = asyncio.run(test_pipeline_format())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
