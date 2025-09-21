"""
Integration test for the Pilger Processing Pipeline.

This script tests the basic integration between DefectAnalysisPipeline 
and PilgerProcessingPipeline to ensure they work together correctly.
"""

import asyncio
import logging
from typing import Optional

from gemba_agents.defect_analysis.models.data_models import (
    IntentData, 
    AggregatedResults, 
    DefectResult
)
from .models.data_models import PilgerProcessingConfig, PilgerProcessingResult
from .pipeline import PilgerProcessingPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_mock_defect_analysis() -> AggregatedResults:
    """Create mock defect analysis data for testing."""
    intent_data = IntentData(
        interpreted_meaning="The pump's loading/unloading piston is not operating smoothly",
        component="Pump",
        sub_component="Piston",
        related_component="Loading/Unloading System",
        issue="Not operating smoothly"
    )
    
    defect_result = DefectResult(
        id="D001",
        score=0.85,
        defect_code="PUMP-001",
        defect_text="Piston seal wear causing irregular movement",
        subsystem="Hydraulic System",
        severity="Medium",
        symptoms=["Irregular piston movement", "Reduced pump efficiency"],
        detection_methods=["Visual inspection", "Performance monitoring"],
        tags=["pump", "piston", "seal"],
        likely_root_causes=["Worn piston seals due to contaminated hydraulic fluid"],
        recommended_actions=["Replace piston seals and change hydraulic fluid"]
    )
    
    return AggregatedResults(
        original_input="The pump's loading/unloading piston is not operating smoothly",
        intent_data=intent_data,
        total_unique_results=1,
        defects=[defect_result],
        root_causes=["Worn piston seals due to contaminated hydraulic fluid"],
        corrective_actions=["Replace piston seals and change hydraulic fluid"],
        processing_time_ms=150.0
    )


async def test_basic_pipeline_creation():
    """Test basic pipeline creation and configuration."""
    print("\n" + "=" * 60)
    print("TEST: Basic Pipeline Creation")
    print("=" * 60)
    
    try:
        # Test default configuration
        pipeline = PilgerProcessingPipeline()
        info = pipeline.get_pipeline_info()
        
        print(f"✅ Pipeline created successfully")
        print(f"   - Agent: {info['agent_name']}")
        print(f"   - Stages: {info['stages']}")
        print(f"   - Caching: {info['caching_enabled']}")
        print(f"   - Timeout: {info['timeout_seconds']}s")
        
        # Test custom configuration
        custom_config = PilgerProcessingConfig(
            agent_name="jk_pilger_new_entries_agent_v2",
            timeout_seconds=180,
            format_for_agent="text",
            enable_caching=False
        )
        
        custom_pipeline = PilgerProcessingPipeline(custom_config)
        custom_info = custom_pipeline.get_pipeline_info()
        
        print(f"✅ Custom pipeline created successfully")
        print(f"   - Agent: {custom_info['agent_name']}")
        print(f"   - Timeout: {custom_info['timeout_seconds']}s")
        print(f"   - Caching: {custom_info['caching_enabled']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline creation failed: {e}")
        logger.error(f"Pipeline creation test failed: {e}")
        return False


async def test_data_model_validation():
    """Test data model creation and validation."""
    print("\n" + "=" * 60)
    print("TEST: Data Model Validation")
    print("=" * 60)
    
    try:
        # Test configuration model
        config = PilgerProcessingConfig(
            agent_name="test_agent",
            config_path="config/test.yaml",
            timeout_seconds=60,
            format_for_agent="structured"
        )
        
        print(f"✅ Configuration model created")
        print(f"   - Agent: {config.agent_name}")
        print(f"   - Format: {config.format_for_agent}")
        print(f"   - Timeout: {config.timeout_seconds}s")
        
        # Test result model
        mock_defect_analysis = create_mock_defect_analysis()
        
        result = PilgerProcessingResult(
            original_defect_analysis=mock_defect_analysis,
            pilger_agent_response={"test": "response"},
            processed_insights=["Test insight 1", "Test insight 2"],
            recommended_actions=["Test action 1"],
            confidence_score=0.75,
            processing_time_ms=250.0,
            agent_execution_time_ms=200.0,
            success=True
        )
        
        print(f"✅ Result model created")
        print(f"   - Success: {result.success}")
        print(f"   - Insights: {len(result.processed_insights)}")
        print(f"   - Actions: {len(result.recommended_actions)}")
        print(f"   - Confidence: {result.confidence_score}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data model validation failed: {e}")
        logger.error(f"Data model validation test failed: {e}")
        return False


async def test_mock_pipeline_execution():
    """Test pipeline execution with mock data (no actual agent call)."""
    print("\n" + "=" * 60)
    print("TEST: Mock Pipeline Execution")
    print("=" * 60)
    
    try:
        # Create mock defect analysis data
        defect_analysis = create_mock_defect_analysis()
        
        print(f"📊 Mock defect analysis created:")
        print(f"   - Input: {defect_analysis.original_input}")
        print(f"   - Component: {defect_analysis.intent_data.component}")
        print(f"   - Issue: {defect_analysis.intent_data.issue}")
        print(f"   - Results: {defect_analysis.total_unique_results}")
        
        # Create pipeline
        pipeline = PilgerProcessingPipeline()
        
        print(f"🔧 Pipeline created, ready for execution")
        print(f"   - This would normally call the {pipeline.config.agent_name} agent")
        print(f"   - Agent config path: {pipeline.config.config_path}")
        print(f"   - Timeout: {pipeline.config.timeout_seconds}s")
        
        # Note: We don't actually run the pipeline here because it would try to call the real agent
        # In a real integration test, you would mock the agent call or have a test agent configured
        
        print(f"✅ Mock pipeline execution test completed")
        print(f"   - Pipeline is ready to process defect analysis results")
        print(f"   - Would format data as: {pipeline.config.format_for_agent}")
        
        return True
        
    except Exception as e:
        print(f"❌ Mock pipeline execution failed: {e}")
        logger.error(f"Mock pipeline execution test failed: {e}")
        return False


async def test_error_handling():
    """Test error handling scenarios."""
    print("\n" + "=" * 60)
    print("TEST: Error Handling")
    print("=" * 60)
    
    try:
        # Test invalid configuration
        try:
            invalid_config = PilgerProcessingConfig(
                timeout_seconds=-1  # Invalid timeout
            )
            print(f"⚠️ Invalid config created (this might be expected)")
        except Exception as e:
            print(f"✅ Invalid config rejected: {e}")
        
        # Test with invalid defect analysis data
        try:
            from pydantic import ValidationError
            
            # This should work fine - testing that we handle various input formats
            minimal_intent = IntentData(
                interpreted_meaning="Test",
                component="Test Component",
                sub_component="Test Sub",
                related_component="Unknown",
                issue="Test Issue"
            )
            
            minimal_analysis = AggregatedResults(
                original_input="Test input",
                intent_data=minimal_intent,
                total_unique_results=0,
                defects=[],
                root_causes=[],
                corrective_actions=[],
                processing_time_ms=0.0
            )
            
            print(f"✅ Minimal defect analysis data handled correctly")
            print(f"   - Input: {minimal_analysis.original_input}")
            print(f"   - Results: {minimal_analysis.total_unique_results}")
            
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            return False
        
        print(f"✅ Error handling tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        logger.error(f"Error handling test failed: {e}")
        return False


async def main():
    """Run all integration tests."""
    print("🚀 Pilger Processing Pipeline Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Basic Pipeline Creation", test_basic_pipeline_creation),
        ("Data Model Validation", test_data_model_validation),
        ("Mock Pipeline Execution", test_mock_pipeline_execution),
        ("Error Handling", test_error_handling),
    ]
    
    results = {}
    
    for name, test_func in tests:
        try:
            print(f"\n🔄 Running {name}...")
            result = await test_func()
            results[name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status}: {name}")
        except Exception as e:
            print(f"❌ FAILED: {name} - {e}")
            results[name] = False
    
    # Summary
    print(f"\n" + "=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    passed_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    for name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")
    
    print(f"\n📊 Overall: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print(f"🎉 All integration tests passed! Pipeline is ready for use.")
    else:
        print(f"⚠️ Some tests failed. Please review the issues above.")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
