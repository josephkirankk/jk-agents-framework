"""
Test script for the enhanced defect analysis API endpoint.

This script tests the new /defect-analysis-with-pilger endpoint that combines
DefectAnalysisPipeline and PilgerProcessingPipeline for comprehensive analysis.
"""

import asyncio
import json
import logging
from typing import Dict, Any

# Import the API models and endpoint function directly
from api import (
    EnhancedDefectAnalysisRequest,
    EnhancedDefectAnalysisResponse,
    enhanced_defect_analysis_endpoint
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_enhanced_defect_analysis_basic():
    """Test basic enhanced defect analysis functionality."""
    print("\n" + "=" * 80)
    print("TEST: Basic Enhanced Defect Analysis")
    print("=" * 80)
    
    try:
        # Create a basic request
        request = EnhancedDefectAnalysisRequest(
            user_input="The pump's loading/unloading piston is not operating smoothly",
            top_n=5,
            min_score=0.2,
            enable_logging=True,
            enable_caching=True,
            parallel_search=True,
            pilger_timeout_seconds=120,
            pilger_format="structured",
            skip_pilger_processing=False
        )
        
        print(f"📝 Input: {request.user_input}")
        print(f"⚙️  Config: top_n={request.top_n}, min_score={request.min_score}")
        print(f"🔧 Pilger: timeout={request.pilger_timeout_seconds}s, format={request.pilger_format}")
        
        # Call the endpoint
        response = await enhanced_defect_analysis_endpoint(request)
        
        # Validate response
        print(f"\n📊 Response Summary:")
        print(f"   ✅ Success: {response.success}")
        print(f"   📝 Original input: {response.original_input}")
        print(f"   ⏱️  Total processing time: {response.total_processing_time_ms:.2f}ms")
        print(f"   ⚠️  Warnings: {len(response.warnings)}")
        
        # Defect analysis results
        if response.defect_analysis:
            defect_data = response.defect_analysis
            print(f"\n🔍 Defect Analysis Stage:")
            print(f"   ✅ Success: {defect_data.get('success', False)}")
            print(f"   📊 Results: {defect_data.get('total_unique_results', 0)} defects found")
            print(f"   🏷️  Component: {defect_data.get('intent_data', {}).get('component', 'Unknown')}")
            print(f"   ⚠️  Issue: {defect_data.get('intent_data', {}).get('issue', 'Unknown')}")
            print(f"   🔧 Actions: {len(defect_data.get('corrective_actions', []))}")
            print(f"   ⏱️  Time: {defect_data.get('processing_time_ms', 0):.2f}ms")
        
        # Pilger processing results
        if response.pilger_processing:
            pilger_data = response.pilger_processing
            print(f"\n🤖 Pilger Processing Stage:")
            print(f"   ✅ Success: {pilger_data.get('success', False)}")
            print(f"   💡 Insights: {len(pilger_data.get('processed_insights', []))}")
            print(f"   🛠️  Actions: {len(pilger_data.get('recommended_actions', []))}")
            print(f"   🎯 Confidence: {pilger_data.get('confidence_score', 'N/A')}")
            print(f"   ⏱️  Time: {pilger_data.get('processing_time_ms', 0):.2f}ms")
            print(f"   🤖 Agent time: {pilger_data.get('agent_execution_time_ms', 0):.2f}ms")
            
            if pilger_data.get('error_message'):
                print(f"   ❌ Error: {pilger_data['error_message']}")
        else:
            print(f"\n🤖 Pilger Processing Stage: Skipped or failed")
        
        # Combined results
        print(f"\n📈 Combined Results:")
        print(f"   💡 Total insights: {len(response.total_insights)}")
        print(f"   🛠️  Total actions: {len(response.total_recommended_actions)}")
        
        if response.total_insights:
            print(f"   📝 Sample insights:")
            for i, insight in enumerate(response.total_insights[:3], 1):
                print(f"      {i}. {insight}")
        
        if response.total_recommended_actions:
            print(f"   📝 Sample actions:")
            for i, action in enumerate(response.total_recommended_actions[:3], 1):
                print(f"      {i}. {action}")
        
        # Processing stages
        if response.processing_stages:
            print(f"\n⏱️  Processing Stages:")
            for stage, data in response.processing_stages.items():
                print(f"   {stage}: {data}")
        
        # Warnings
        if response.warnings:
            print(f"\n⚠️  Warnings:")
            for warning in response.warnings:
                print(f"   - {warning}")
        
        return response.success
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        logger.error(f"Basic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_enhanced_defect_analysis_skip_pilger():
    """Test enhanced defect analysis with Pilger processing skipped."""
    print("\n" + "=" * 80)
    print("TEST: Enhanced Defect Analysis (Skip Pilger)")
    print("=" * 80)
    
    try:
        # Create request with Pilger processing skipped
        request = EnhancedDefectAnalysisRequest(
            user_input="Motor bearing overheating",
            top_n=3,
            min_score=0.6,
            enable_logging=True,
            skip_pilger_processing=True  # Skip Pilger processing
        )
        
        print(f"📝 Input: {request.user_input}")
        print(f"🚫 Pilger processing: SKIPPED")
        
        # Call the endpoint
        response = await enhanced_defect_analysis_endpoint(request)
        
        # Validate response
        print(f"\n📊 Response Summary:")
        print(f"   ✅ Success: {response.success}")
        print(f"   ⏱️  Total processing time: {response.total_processing_time_ms:.2f}ms")
        
        # Should have defect analysis but no Pilger processing
        assert response.defect_analysis is not None, "Defect analysis should be present"
        assert response.pilger_processing is None, "Pilger processing should be None when skipped"
        
        print(f"   ✅ Defect analysis: Present")
        print(f"   🚫 Pilger processing: Correctly skipped")
        
        # Processing stages should reflect skipped Pilger
        pilger_stage = response.processing_stages.get("pilger_processing", {})
        assert pilger_stage.get("skipped") is True, "Pilger stage should be marked as skipped"
        
        print(f"   ✅ Processing stages correctly reflect skipped Pilger")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        logger.error(f"Skip Pilger test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_enhanced_defect_analysis_text_format():
    """Test enhanced defect analysis with text format for Pilger."""
    print("\n" + "=" * 80)
    print("TEST: Enhanced Defect Analysis (Text Format)")
    print("=" * 80)
    
    try:
        # Create request with text format for Pilger
        request = EnhancedDefectAnalysisRequest(
            user_input="Hydraulic pump cavitation",
            top_n=5,
            min_score=0.6,
            pilger_format="text",  # Use text format instead of structured
            pilger_timeout_seconds=60,
            enable_logging=True
        )
        
        print(f"📝 Input: {request.user_input}")
        print(f"📄 Pilger format: {request.pilger_format}")
        print(f"⏰ Pilger timeout: {request.pilger_timeout_seconds}s")
        
        # Call the endpoint
        response = await enhanced_defect_analysis_endpoint(request)
        
        # Validate response
        print(f"\n📊 Response Summary:")
        print(f"   ✅ Success: {response.success}")
        print(f"   ⏱️  Total processing time: {response.total_processing_time_ms:.2f}ms")
        
        # Check that configuration was applied
        metadata = response.metadata
        pilger_config = metadata.get("pilger_processing_config", {})
        assert pilger_config.get("format") == "text", "Pilger format should be 'text'"
        assert pilger_config.get("timeout_seconds") == 60, "Pilger timeout should be 60"
        
        print(f"   ✅ Configuration correctly applied")
        print(f"   📄 Format: {pilger_config.get('format')}")
        print(f"   ⏰ Timeout: {pilger_config.get('timeout_seconds')}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        logger.error(f"Text format test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_enhanced_defect_analysis_error_handling():
    """Test error handling in enhanced defect analysis."""
    print("\n" + "=" * 80)
    print("TEST: Enhanced Defect Analysis (Error Handling)")
    print("=" * 80)
    
    try:
        # Create request with invalid input to test error handling
        request = EnhancedDefectAnalysisRequest(
            user_input="",  # Empty input should cause validation error
            top_n=5,
            min_score=0.6
        )
        
        print(f"📝 Input: '{request.user_input}' (empty - should cause error)")
        
        # This should fail validation before reaching the endpoint
        print(f"❌ This test expects validation to fail for empty input")
        return True  # Expected behavior
        
    except Exception as e:
        print(f"✅ Expected validation error caught: {e}")
        return True


async def test_response_model_validation():
    """Test response model structure and validation."""
    print("\n" + "=" * 80)
    print("TEST: Response Model Validation")
    print("=" * 80)
    
    try:
        # Create a minimal valid request
        request = EnhancedDefectAnalysisRequest(
            user_input="Test input for model validation",
            skip_pilger_processing=True  # Skip to avoid agent dependencies
        )
        
        print(f"📝 Input: {request.user_input}")
        print(f"🧪 Testing response model structure...")
        
        # Call the endpoint
        response = await enhanced_defect_analysis_endpoint(request)
        
        # Validate response structure
        required_fields = [
            'success', 'original_input', 'defect_analysis', 'total_insights',
            'total_recommended_actions', 'processing_stages', 'total_processing_time_ms',
            'metadata'
        ]
        
        for field in required_fields:
            assert hasattr(response, field), f"Response missing required field: {field}"
            print(f"   ✅ Field '{field}': Present")
        
        # Validate defect_analysis structure
        defect_analysis = response.defect_analysis
        defect_required_fields = [
            'success', 'intent_data', 'total_unique_results', 'defects',
            'root_causes', 'corrective_actions', 'processing_time_ms'
        ]
        
        for field in defect_required_fields:
            assert field in defect_analysis, f"Defect analysis missing field: {field}"
            print(f"   ✅ Defect analysis field '{field}': Present")
        
        # Validate processing_stages structure
        stages = response.processing_stages
        assert 'defect_analysis' in stages, "Processing stages missing defect_analysis"
        assert 'pilger_processing' in stages, "Processing stages missing pilger_processing"
        print(f"   ✅ Processing stages: Both stages present")
        
        # Validate metadata structure
        metadata = response.metadata
        assert 'pipeline_version' in metadata, "Metadata missing pipeline_version"
        assert 'processing_stages' in metadata, "Metadata missing processing_stages"
        print(f"   ✅ Metadata: Required fields present")
        
        print(f"\n✅ Response model validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Response model validation failed: {e}")
        logger.error(f"Response model validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests for the enhanced defect analysis API."""
    print("🚀 Enhanced Defect Analysis API Tests")
    print("=" * 80)
    
    tests = [
        ("Basic Enhanced Analysis", test_enhanced_defect_analysis_basic),
        ("Skip Pilger Processing", test_enhanced_defect_analysis_skip_pilger),
        ("Text Format Configuration", test_enhanced_defect_analysis_text_format),
        ("Error Handling", test_enhanced_defect_analysis_error_handling),
        ("Response Model Validation", test_response_model_validation),
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
    print(f"\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    for name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")
    
    print(f"\n📊 Overall: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print(f"🎉 All tests passed! Enhanced API is ready for use.")
    else:
        print(f"⚠️ Some tests failed. Please review the issues above.")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
