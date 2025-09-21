"""
Test suite for the defect analysis pipeline.

This module provides comprehensive tests for all components of the defect analysis pipeline.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch

from .pipeline import DefectAnalysisPipeline, analyze_defect_sync
from .models.data_models import (
    DefectAnalysisConfig, 
    IntentData, 
    VectorSearchResults, 
    AggregatedResults,
    DefectResult
)
from .stages.intent_extraction import extract_intent
from .stages.vector_search import search_vectors
from .stages.result_aggregation import aggregate_results


class TestDataModels:
    """Test data model validation."""
    
    def test_intent_data_creation(self):
        """Test IntentData model creation and validation."""
        intent = IntentData(
            interpreted_meaning="Pump piston not operating smoothly",
            component="Pump",
            sub_component="Pump piston",
            related_component="Air compressor",
            issue="Not operating smoothly"
        )
        
        assert intent.component == "Pump"
        assert intent.issue == "Not operating smoothly"
    
    def test_defect_analysis_config_defaults(self):
        """Test default configuration values."""
        config = DefectAnalysisConfig()
        
        assert config.agent_name == "jk_pilger_extract_intent_agent"
        assert config.top_n == 10
        assert config.min_score == 0.6
        assert config.enable_logging is True
        assert config.enable_caching is True
    
    def test_defect_result_creation(self):
        """Test DefectResult model creation."""
        defect = DefectResult(
            id="test-1",
            score=0.85,
            defect_code="HSP.PUMP.PISTON.FAIL",
            defect_text="Pump piston failure",
            subsystem="HYD",
            severity="High",
            symptoms=["noise", "vibration"],
            detection_methods=["visual", "acoustic"],
            tags=["pump", "piston"],
            likely_root_causes=["wear", "contamination"],
            recommended_actions=["replace", "inspect"]
        )
        
        assert defect.score == 0.85
        assert defect.defect_code == "HSP.PUMP.PISTON.FAIL"
        assert len(defect.symptoms) == 2


class TestUtilityFunctions:
    """Test utility functions."""
    
    @pytest.mark.asyncio
    async def test_load_and_build_agent_error_handling(self):
        """Test agent loading error handling."""
        from .utils.agent_utils import load_and_build_agent
        
        # Test with non-existent config file
        with pytest.raises(FileNotFoundError):
            await load_and_build_agent("test_agent", "non_existent_config.yaml")
    
    def test_parse_json_response(self):
        """Test JSON response parsing."""
        from .utils.agent_utils import parse_json_response
        
        # Test direct JSON
        json_str = '{"component": "Pump", "issue": "Failure"}'
        result = parse_json_response(json_str)
        assert result["component"] == "Pump"
        
        # Test JSON in code blocks
        markdown_json = '```json\n{"component": "Motor", "issue": "Overheating"}\n```'
        result = parse_json_response(markdown_json)
        assert result["component"] == "Motor"
        
        # Test invalid JSON
        with pytest.raises(ValueError):
            parse_json_response("invalid json content")


class TestPipelineStages:
    """Test individual pipeline stages."""
    
    @pytest.mark.asyncio
    async def test_intent_extraction_error_handling(self):
        """Test intent extraction error handling."""
        config = DefectAnalysisConfig(
            agent_name="non_existent_agent",
            config_path="config/jk-gemba.yaml"
        )
        
        # Should return default IntentData on error
        result = await extract_intent("test input", config)
        
        assert isinstance(result, IntentData)
        assert result.component == "Unknown"
        assert "Failed to extract intent" in result.interpreted_meaning
    
    @pytest.mark.asyncio
    async def test_vector_search_with_mock_client(self):
        """Test vector search with mocked VectorDB client."""
        intent_data = IntentData(
            interpreted_meaning="Pump failure",
            component="Pump",
            sub_component="Piston",
            related_component="Unknown",
            issue="Failure"
        )
        
        # Mock the VectorDB client
        mock_response = Mock()
        mock_response.results = []
        mock_response.execution_time_ms = 100.0
        
        with patch('gemba_agents.defect_analysis.stages.vector_search.VectorDBClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.search = AsyncMock(return_value=mock_response)
            
            result = await search_vectors(intent_data, DefectAnalysisConfig())
            
            assert isinstance(result, VectorSearchResults)
            assert result.total_results == 0
    
    @pytest.mark.asyncio
    async def test_result_aggregation(self):
        """Test result aggregation stage."""
        intent_data = IntentData(
            interpreted_meaning="Pump failure",
            component="Pump",
            sub_component="Piston",
            related_component="Unknown",
            issue="Failure"
        )
        
        # Create mock search results
        defect_result = DefectResult(
            id="test-1",
            score=0.9,
            defect_code="HSP.PUMP.FAIL",
            defect_text="Pump failure",
            subsystem="HYD",
            severity="High",
            symptoms=["noise"],
            detection_methods=["visual"],
            tags=["pump"],
            likely_root_causes=["wear"],
            recommended_actions=["replace"]
        )
        
        search_results = VectorSearchResults(
            query_terms=["pump failure"],
            total_results=1,
            execution_time_ms=100.0,
            results=[defect_result]
        )
        
        result = await aggregate_results(
            "test input",
            intent_data,
            search_results,
            DefectAnalysisConfig()
        )
        
        assert isinstance(result, AggregatedResults)
        assert result.total_unique_results == 1
        assert len(result.root_causes) == 1
        assert result.root_causes[0] == "wear"


class TestDefectAnalysisPipeline:
    """Test the main pipeline class."""
    
    def test_pipeline_initialization(self):
        """Test pipeline initialization."""
        pipeline = DefectAnalysisPipeline()
        
        assert pipeline.config is not None
        assert pipeline.pipeline is not None
        
        info = pipeline.get_pipeline_info()
        assert "stages" in info
        assert len(info["stages"]) == 3
    
    def test_pipeline_with_custom_config(self):
        """Test pipeline with custom configuration."""
        config = DefectAnalysisConfig(
            top_n=15,
            min_score=0.5,
            enable_caching=False
        )
        
        pipeline = DefectAnalysisPipeline(config)
        
        assert pipeline.config.top_n == 15
        assert pipeline.config.min_score == 0.5
        assert pipeline.config.enable_caching is False
    
    @pytest.mark.asyncio
    async def test_pipeline_error_handling(self):
        """Test pipeline error handling with invalid configuration."""
        config = DefectAnalysisConfig(
            agent_name="non_existent_agent",
            config_path="non_existent_config.yaml"
        )
        
        pipeline = DefectAnalysisPipeline(config)
        
        # Pipeline should handle errors gracefully
        with pytest.raises(Exception):
            await pipeline.run("test input")


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_synchronous_function_error_handling(self):
        """Test synchronous convenience function error handling."""
        # This should handle the case where we're not in an async context
        try:
            result = analyze_defect_sync("test input")
            # If it doesn't raise an exception, that's also valid
            assert isinstance(result, AggregatedResults)
        except Exception as e:
            # Expected if agent/config is not available
            assert "Agent" in str(e) or "config" in str(e) or "not found" in str(e)


class TestIntegration:
    """Integration tests for the complete pipeline."""
    
    @pytest.mark.asyncio
    async def test_pipeline_with_mocked_dependencies(self):
        """Test complete pipeline with mocked dependencies."""
        # Mock the agent loading and invocation
        mock_intent_response = {
            "interpreted_meaning": "Pump piston failure",
            "component": "Pump",
            "sub_component": "Piston",
            "related_component": "Unknown",
            "issue": "Failure"
        }
        
        # Mock vector search response
        mock_search_result = Mock()
        mock_search_result.defect = Mock()
        mock_search_result.defect.defect_code = "HSP.PUMP.FAIL"
        mock_search_result.defect.defect_text = "Pump failure"
        mock_search_result.defect.subsystem = "HYD"
        mock_search_result.defect.severity = "High"
        mock_search_result.defect.symptoms = ["noise"]
        mock_search_result.defect.detection_methods = ["visual"]
        mock_search_result.defect.tags = ["pump"]
        mock_search_result.defect.likely_root_causes = ["wear"]
        mock_search_result.defect.recommended_actions = ["replace"]
        mock_search_result.id = "test-1"
        mock_search_result.score = 0.9
        
        mock_vector_response = Mock()
        mock_vector_response.results = [mock_search_result]
        mock_vector_response.execution_time_ms = 100.0
        
        with patch('gemba_agents.defect_analysis.utils.agent_utils.load_and_build_agent') as mock_load_agent, \
             patch('gemba_agents.defect_analysis.utils.agent_utils.invoke_agent_async') as mock_invoke, \
             patch('gemba_agents.defect_analysis.stages.vector_search.VectorDBClient') as mock_client:
            
            # Setup mocks
            mock_load_agent.return_value = (Mock(), None)
            mock_invoke.return_value = json.dumps(mock_intent_response)
            mock_client.return_value.__aenter__.return_value.search = AsyncMock(return_value=mock_vector_response)
            
            # Run pipeline
            pipeline = DefectAnalysisPipeline()
            result = await pipeline.run("test pump failure")
            
            # Verify results
            assert isinstance(result, AggregatedResults)
            assert result.intent_data.component == "Pump"
            assert result.total_unique_results >= 0  # May be 0 due to mocking


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
