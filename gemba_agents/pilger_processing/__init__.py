"""
Pilger Processing Pipeline

This module provides a pipeline for processing DefectAnalysisPipeline results
through the jk_pilger_new_entries_agent for additional insights and actions.

The pipeline is designed to work as a sequential step after the DefectAnalysisPipeline,
creating a two-stage processing workflow where defect analysis results are further
processed by the Pilger agent.

Example:
    from gemba_agents.defect_analysis import DefectAnalysisPipeline
    from gemba_agents.pilger_processing import PilgerProcessingPipeline
    
    # First stage: Defect analysis
    defect_pipeline = DefectAnalysisPipeline()
    defect_results = await defect_pipeline.run("The pump's loading/unloading piston is not operating smoothly")
    
    # Second stage: Pilger processing
    pilger_pipeline = PilgerProcessingPipeline()
    final_results = await pilger_pipeline.run(defect_results)
"""

from .pipeline import PilgerProcessingPipeline, process_defect_analysis, process_defect_analysis_sync
from .models.data_models import (
    PilgerProcessingConfig,
    PilgerProcessingResult
)

__all__ = [
    'PilgerProcessingPipeline',
    'process_defect_analysis',
    'process_defect_analysis_sync',
    'PilgerProcessingConfig',
    'PilgerProcessingResult'
]

__version__ = "1.0.0"
