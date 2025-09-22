"""
TsDefects Pipeline

This module provides an integrated pipeline that combines defect analysis and agent processing
using TsSearch (Typesense) for vector search operations.

The pipeline performs:
1. Intent extraction from user input
2. Vector search using TsSearchClient
3. Result processing and deduplication
4. Agent enhancement with curator actions and rationale

Example:
    >>> from gemba_agents.tsdefects_pipeline import TsDefectsPipeline
    >>> 
    >>> pipeline = TsDefectsPipeline()
    >>> result = await pipeline.run("The pump piston is not operating smoothly")
    >>> print(f"Found {result.total_results} enhanced defects")
    >>> for defect in result.enhanced_defects:
    ...     print(f"- {defect.defect_code}: {defect.curator_action}")
"""

from .pipeline import TsDefectsPipeline, analyze_ts_defects, analyze_ts_defects_sync
from .models.data_models import (
    TsDefectsConfig,
    EnhancedTsDefectResult,
    TsDefectsResult
)

__all__ = [
    "TsDefectsPipeline",
    "TsDefectsConfig",
    "EnhancedTsDefectResult",
    "TsDefectsResult",
    "analyze_ts_defects",
    "analyze_ts_defects_sync"
]
