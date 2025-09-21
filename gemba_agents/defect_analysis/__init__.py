"""
Defect Analysis Pipeline

This module provides a comprehensive defect analysis pipeline using the pipefunc library
for orchestrating intent extraction, vector search, and result aggregation stages.

The pipeline processes user input describing equipment issues through three main stages:
1. Intent Extraction: Uses jk_pilger_extract_intent_agent to extract structured intent data
2. Vector Search: Performs vector search using extracted intent data
3. Result Aggregation: Consolidates and deduplicates search results

Example:
    from gemba_agents.defect_analysis import DefectAnalysisPipeline
    
    pipeline = DefectAnalysisPipeline()
    result = await pipeline.run("The pump's loading/unloading piston is not operating smoothly")
"""

from .pipeline import DefectAnalysisPipeline, analyze_defect, analyze_defect_sync
from .models.data_models import (
    IntentData,
    VectorSearchResults,
    AggregatedResults,
    DefectAnalysisConfig
)

__all__ = [
    'DefectAnalysisPipeline',
    'analyze_defect',
    'analyze_defect_sync',
    'IntentData',
    'VectorSearchResults',
    'AggregatedResults',
    'DefectAnalysisConfig'
]

__version__ = "1.0.0"
