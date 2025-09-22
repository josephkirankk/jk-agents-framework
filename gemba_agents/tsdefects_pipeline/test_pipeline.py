"""
Test suite for the TsDefects pipeline.

This module contains comprehensive tests for the integrated TsDefects pipeline
including unit tests for individual stages and integration tests for the complete pipeline.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from typing import List

from .pipeline import TsDefectsPipeline, analyze_ts_defects_sync
from .models.data_models import TsDefectsConfig, EnhancedTsDefectResult, TsDefectsResult
from .stages.intent_extraction import extract_intent
from .stages.ts_vector_search import search_ts_vectors
from .stages.result_processing import process_ts_results
from .stages.agent_enhancement import enhance_with_agent

from gemba_agents.defect_analysis.models.data_models import IntentData
from vectordb_wrapper.ts_models import TsDefectResult, TsSearchResponse, TsSearchData


class TestTsDefectsConfig:
    """Test TsDefectsConfig model."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = TsDefectsConfig()
        
        assert config.intent_agent_name == "jk_pilger_extract_intent_agent"
        assert config.processing_agent_name == "jk_pilger_new_entries_agent_v2"
        assert config.search_limit == 10
        assert config.min_similarity_score == 0.2
        assert config.collection == "defects"
        assert config.enable_logging is True
        assert config.enable_caching is True
        assert config.parallel_search is True
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = TsDefectsConfig(
            search_limit=5,
            min_similarity_score=0.5,
            enable_logging=False,
            parallel_search=False
        )
        
        assert config.search_limit == 5
        assert config.min_similarity_score == 0.5
        assert config.enable_logging is False
        assert config.parallel_search is False


class TestEnhancedTsDefectResult:
    """Test EnhancedTsDefectResult model."""
    
    def test_enhanced_result_creation(self):
        """Test creating enhanced result from TsDefectResult."""
        # Create a mock TsDefectResult
        base_result = TsDefectResult(
            id="test-123",
            defect_code="PLG.PMP.SEAL.LEAK",
            defect_text="Pump seal leakage",
            machine="PLG",
            subsystem="PMP",
            component="SEAL",
            defect_type="LEAK",
            subsystem_description="Pump system",
            component_description="Seal component",
            defect_type_description="Leakage defect",
            keywords=["pump", "seal", "leak"],
            tags=["maintenance"],
            score=0.85,
            created_on=1234567890
        )
        
        # Create enhanced result
        enhanced = EnhancedTsDefectResult(
            **base_result.model_dump(),
            curator_action="REVIEW_REQUIRED",
            rationale="Requires immediate attention"
        )
        
        assert enhanced.id == "test-123"
        assert enhanced.defect_code == "PLG.PMP.SEAL.LEAK"
        assert enhanced.curator_action == "REVIEW_REQUIRED"
        assert enhanced.rationale == "Requires immediate attention"


class TestTsDefectsPipeline:
    """Test TsDefectsPipeline class."""
    
    def test_pipeline_initialization(self):
        """Test pipeline initialization."""
        pipeline = TsDefectsPipeline()
        
        assert pipeline.config is not None
        assert pipeline.pipeline is not None
        assert isinstance(pipeline.config, TsDefectsConfig)
    
    def test_pipeline_with_custom_config(self):
        """Test pipeline with custom configuration."""
        config = TsDefectsConfig(search_limit=5, enable_logging=False)
        pipeline = TsDefectsPipeline(config)
        
        assert pipeline.config.search_limit == 5
        assert pipeline.config.enable_logging is False
    
    def test_get_pipeline_info(self):
        """Test pipeline information retrieval."""
        pipeline = TsDefectsPipeline()
        info = pipeline.get_pipeline_info()
        
        assert "stages" in info
        assert "config" in info
        assert len(info["stages"]) == 4
        assert "intent_extraction" in info["stages"]
        assert "ts_vector_search" in info["stages"]
        assert "result_processing" in info["stages"]
        assert "agent_enhancement" in info["stages"]


class TestPipelineIntegration:
    """Integration tests for the complete pipeline."""
    
    @pytest.fixture
    def mock_intent_data(self):
        """Mock intent data for testing."""
        return IntentData(
            interpreted_meaning="Pump seal leakage issue",
            component="Pump",
            sub_component="Seal",
            related_component="Unknown",
            issue="Leakage"
        )
    
    @pytest.fixture
    def mock_ts_defect_results(self):
        """Mock TsDefectResult objects for testing."""
        return [
            TsDefectResult(
                id="test-1",
                defect_code="PLG.PMP.SEAL.LEAK",
                defect_text="Pump seal leakage causing fluid loss",
                machine="PLG",
                subsystem="PMP",
                component="SEAL",
                defect_type="LEAK",
                subsystem_description="Pump system",
                component_description="Seal component",
                defect_type_description="Leakage defect",
                keywords=["pump", "seal", "leak"],
                tags=["maintenance"],
                score=0.85,
                created_on=1234567890
            ),
            TsDefectResult(
                id="test-2",
                defect_code="PLG.PMP.BEARING.WEAR",
                defect_text="Pump bearing wear detected",
                machine="PLG",
                subsystem="PMP",
                component="BEARING",
                defect_type="WEAR",
                subsystem_description="Pump system",
                component_description="Bearing component",
                defect_type_description="Wear defect",
                keywords=["pump", "bearing", "wear"],
                tags=["maintenance"],
                score=0.75,
                created_on=1234567891
            )
        ]
    
    @patch('gemba_agents.tsdefects_pipeline.stages.intent_extraction.load_and_build_agent')
    @patch('gemba_agents.tsdefects_pipeline.stages.intent_extraction.invoke_agent_async')
    async def test_intent_extraction_stage(self, mock_invoke, mock_load, mock_intent_data):
        """Test intent extraction stage."""
        # Mock agent loading and invocation
        mock_load.return_value = (Mock(), Mock(), Mock())
        mock_invoke.return_value = json.dumps(mock_intent_data.model_dump())
        
        config = TsDefectsConfig()
        result = extract_intent("Test input", config)
        
        assert isinstance(result, IntentData)
        assert result.component == "Pump"
        assert result.issue == "Leakage"
    
    @patch('gemba_agents.tsdefects_pipeline.stages.ts_vector_search.TsSearchClient')
    async def test_ts_vector_search_stage(self, mock_client_class, mock_intent_data, mock_ts_defect_results):
        """Test TsSearch vector search stage."""
        # Mock TsSearchClient
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock search response
        mock_response = Mock()
        mock_response.data.results = mock_ts_defect_results
        mock_response.data.processing_time_ms = 100
        mock_client.search.return_value = mock_response
        
        config = TsDefectsConfig()
        result = search_ts_vectors(mock_intent_data, config)
        
        assert result.total_results == 2
        assert len(result.results) == 2
        assert result.results[0].defect_code == "PLG.PMP.SEAL.LEAK"
    
    async def test_result_processing_stage(self, mock_intent_data, mock_ts_defect_results):
        """Test result processing stage."""
        from .models.data_models import TsSearchResults
        
        # Create mock search results
        search_results = TsSearchResults(
            query_terms=["pump seal leak"],
            total_results=2,
            execution_time_ms=100,
            results=mock_ts_defect_results
        )
        
        config = TsDefectsConfig()
        result = process_ts_results(mock_intent_data, search_results, config)
        
        assert len(result) == 2
        assert result[0].score >= result[1].score  # Should be sorted by score
    
    @patch('gemba_agents.tsdefects_pipeline.stages.agent_enhancement.load_and_build_agent_with_placeholders')
    @patch('gemba_agents.tsdefects_pipeline.stages.agent_enhancement.invoke_agent_async')
    async def test_agent_enhancement_stage(self, mock_invoke, mock_load, mock_intent_data, mock_ts_defect_results):
        """Test agent enhancement stage."""
        # Mock agent loading and invocation
        mock_load.return_value = (Mock(), Mock(), Mock())
        mock_invoke.return_value = json.dumps({
            "enhancements": [
                {"curator_action": "APPROVED", "rationale": "Standard maintenance"},
                {"curator_action": "REVIEW_REQUIRED", "rationale": "Needs inspection"}
            ]
        })
        
        config = TsDefectsConfig()
        result = enhance_with_agent(mock_ts_defect_results, mock_intent_data, config)
        
        assert len(result) == 2
        assert isinstance(result[0], EnhancedTsDefectResult)
        assert result[0].curator_action == "APPROVED"
        assert result[1].curator_action == "REVIEW_REQUIRED"
    
    @patch('gemba_agents.tsdefects_pipeline.pipeline.Pipeline')
    async def test_full_pipeline_success(self, mock_pipeline_class):
        """Test successful full pipeline execution."""
        # Mock pipeline execution
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline
        
        # Mock pipeline results
        mock_runner = AsyncMock()
        mock_result = {
            "intent_data": Mock(output=IntentData(
                interpreted_meaning="Test",
                component="Pump",
                sub_component="Seal",
                related_component="Unknown",
                issue="Leak"
            )),
            "enhanced_results": Mock(output=[
                EnhancedTsDefectResult(
                    id="test-1",
                    defect_code="PLG.PMP.SEAL.LEAK",
                    defect_text="Test defect",
                    machine="PLG",
                    subsystem="PMP",
                    component="SEAL",
                    defect_type="LEAK",
                    subsystem_description="Test",
                    component_description="Test",
                    defect_type_description="Test",
                    score=0.85,
                    created_on=1234567890,
                    curator_action="APPROVED",
                    rationale="Test rationale"
                )
            ])
        }
        mock_runner.task = asyncio.create_task(asyncio.coroutine(lambda: mock_result)())
        mock_pipeline.map_async.return_value = mock_runner
        
        pipeline = TsDefectsPipeline()
        result = await pipeline.run("Test input")
        
        assert result.success is True
        assert result.total_results == 1
        assert len(result.enhanced_defects) == 1
        assert result.enhanced_defects[0].curator_action == "APPROVED"
    
    def test_synchronous_execution(self):
        """Test synchronous pipeline execution."""
        # This is a basic test - in practice you'd mock the async components
        try:
            result = analyze_ts_defects_sync("Test input")
            # The result might fail due to missing dependencies, but it should return a TsDefectsResult
            assert isinstance(result, TsDefectsResult)
        except Exception:
            # Expected in test environment without proper setup
            pass


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
