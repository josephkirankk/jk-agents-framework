"""
Data models for the Pilger processing pipeline using Pydantic for validation.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict

# Import AggregatedResults from defect_analysis for input type
from gemba_agents.defect_analysis.models.data_models import AggregatedResults


class PilgerProcessingConfig(BaseModel):
    """
    Configuration model for the Pilger processing pipeline.
    
    This configuration controls how the pipeline processes DefectAnalysisPipeline
    results through the jk_pilger_new_entries_agent.
    """
    # Agent configuration
    agent_name: str = Field(
        default="jk_pilger_new_entries_agent", 
        description="Name of the Pilger processing agent"
    )
    config_path: str = Field(
        default="config/jk-gemba.yaml", 
        description="Path to agent configuration file"
    )
    
    # Processing configuration
    include_original_data: bool = Field(
        default=True, 
        description="Include original defect analysis data in the result"
    )
    format_for_agent: str = Field(
        default="structured", 
        description="Format for agent input: 'structured' or 'text'"
    )
    
    # Pipeline configuration
    enable_logging: bool = Field(
        default=True, 
        description="Enable detailed logging"
    )
    enable_caching: bool = Field(
        default=True, 
        description="Enable result caching"
    )
    timeout_seconds: int = Field(
        default=120, 
        ge=30, 
        le=300, 
        description="Timeout for agent processing in seconds"
    )
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )


class PilgerProcessingResult(BaseModel):
    """
    Model for the final result from the Pilger processing pipeline.
    
    This contains both the original defect analysis results and the additional
    processing results from the jk_pilger_new_entries_agent.
    """
    # Original defect analysis data
    original_defect_analysis: AggregatedResults = Field(
        ..., 
        description="Original results from DefectAnalysisPipeline"
    )
    
    # Pilger agent processing results
    pilger_agent_response: Dict[str, Any] = Field(
        ..., 
        description="Raw response from jk_pilger_new_entries_agent"
    )
    processed_insights: List[str] = Field(
        default_factory=list, 
        description="Additional insights from Pilger agent processing"
    )
    recommended_actions: List[str] = Field(
        default_factory=list, 
        description="Additional recommended actions from Pilger agent"
    )
    confidence_score: Optional[float] = Field(
        default=None, 
        ge=0.0, 
        le=1.0, 
        description="Confidence score for the processing results"
    )
    
    # Processing metadata
    processing_time_ms: float = Field(
        ..., 
        ge=0, 
        description="Total processing time in milliseconds"
    )
    agent_execution_time_ms: float = Field(
        ..., 
        ge=0, 
        description="Agent execution time in milliseconds"
    )
    success: bool = Field(
        ..., 
        description="Whether the processing was successful"
    )
    error_message: Optional[str] = Field(
        default=None, 
        description="Error message if processing failed"
    )
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
