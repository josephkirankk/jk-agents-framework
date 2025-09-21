"""
Data models for the defect analysis pipeline using Pydantic for validation.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class RootCause(BaseModel):
    """
    Model for a structured root cause with code and descriptive text.

    This represents the structured format expected by the ontology:
    {"root_cause_code": "RC.ABRASION.EXTERNAL", "root_cause_text": "Abrasion from external contact..."}
    """
    root_cause_code: str = Field(..., description="Root cause code from ontology")
    root_cause_text: str = Field(..., description="Descriptive text for the root cause")

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )


class CorrectiveAction(BaseModel):
    """
    Model for a structured corrective action with code and descriptive text.

    This represents the structured format expected by the ontology:
    {"action_code": "CA.ALIGN.ADJUST", "action_text": "Adjust alignment of components..."}
    """
    action_code: str = Field(..., description="Action code from ontology")
    action_text: str = Field(..., description="Descriptive text for the corrective action")

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )


class IntentData(BaseModel):
    """
    Model for extracted intent data from the intent extraction stage.
    
    This represents the structured output from the jk_pilger_extract_intent_agent
    containing the interpreted meaning and component information.
    """
    interpreted_meaning: str = Field(..., description="Clear English meaning of the defect/event")
    component: str = Field(..., description="Standardized Pilger main component directly affected")
    sub_component: str = Field(..., description="Specific sub-part if identifiable, else 'Unknown'")
    related_component: str = Field(..., description="Another component/system causing or suspected to cause the issue, else 'Unknown'")
    issue: str = Field(..., description="Standardized defect")
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )


class DefectResult(BaseModel):
    """
    Model for a single defect result from vector search.
    """
    id: str = Field(..., description="Result ID")
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    defect_code: str = Field(..., description="Defect code")
    defect_text: str = Field(..., description="Defect description")
    subsystem: str = Field(..., description="Subsystem")
    severity: str = Field(..., description="Severity level")
    symptoms: List[str] = Field(default_factory=list, description="List of symptoms")
    detection_methods: List[str] = Field(default_factory=list, description="Detection methods")
    tags: List[str] = Field(default_factory=list, description="Tags")
    likely_root_causes: List[str] = Field(default_factory=list, description="Likely root causes")
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended actions")
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )


class VectorSearchResults(BaseModel):
    """
    Model for vector search results containing all retrieved defects.
    """
    query_terms: List[str] = Field(..., description="Search terms used")
    total_results: int = Field(..., ge=0, description="Total number of results")
    execution_time_ms: float = Field(..., ge=0, description="Total execution time in milliseconds")
    results: List[DefectResult] = Field(default_factory=list, description="Search results")
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )


class AggregatedResults(BaseModel):
    """
    Model for the final aggregated and deduplicated results.
    """
    original_input: str = Field(..., description="Original user input")
    intent_data: IntentData = Field(..., description="Extracted intent data")
    total_unique_results: int = Field(..., ge=0, description="Number of unique results after deduplication")
    defects: List[DefectResult] = Field(default_factory=list, description="Deduplicated defect results")
    root_causes: List[RootCause] = Field(default_factory=list, description="Consolidated root causes with structured format")
    corrective_actions: List[CorrectiveAction] = Field(default_factory=list, description="Consolidated corrective actions with structured format")
    processing_time_ms: float = Field(..., ge=0, description="Total processing time in milliseconds")

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )


class DefectAnalysisConfig(BaseModel):
    """
    Configuration model for the defect analysis pipeline.
    """
    # Intent extraction configuration
    agent_name: str = Field(default="jk_pilger_extract_intent_agent", description="Name of the intent extraction agent")
    config_path: str = Field(default="config/jk-gemba.yaml", description="Path to agent configuration file")
    
    # Vector search configuration
    top_n: int = Field(default=10, ge=1, le=50, description="Number of results to return from vector search")
    min_score: float = Field(default=0.6, ge=0.0, le=1.0, description="Minimum similarity score for vector search")
    vectordb_base_url: Optional[str] = Field(default=None, description="Base URL for VectorDB API")
    
    # Pipeline configuration
    enable_logging: bool = Field(default=True, description="Enable detailed logging")
    enable_caching: bool = Field(default=True, description="Enable result caching")
    parallel_search: bool = Field(default=True, description="Enable parallel vector searches")
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )
