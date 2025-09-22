"""
Pydantic models for VectorDB API requests and responses.

This module defines all the data models used for validation and serialization
of requests and responses to/from the VectorDB API service.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class DefectData(BaseModel):
    """Model representing defect data structure."""
    
    defect_code: str = Field(..., description="Unique defect identifier")
    defect_text: str = Field(..., description="Description of the defect")
    subsystem: str = Field(..., description="Subsystem code")
    severity: str = Field(default="Medium", description="Severity level")
    typical_frequency: str = Field(default="Unknown", description="How often this occurs")
    symptoms: List[str] = Field(default_factory=list, description="List of symptoms")
    detection_methods: List[str] = Field(default_factory=list, description="Detection methods")
    early_warning_signals: List[str] = Field(default_factory=list, description="Early warning signals")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    likely_root_causes: List[str] = Field(default_factory=list, description="Likely root causes")
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended actions")

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )


class SearchRequest(BaseModel):
    """Model for search request payload."""

    query: str = Field(..., min_length=1, description="Search query in natural language")
    top_n: int = Field(default=5, ge=1, le=50, description="Number of results to return")
    min_score: float = Field(default=0.1, ge=0.0, le=1.0, description="Minimum similarity score")

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )


class SearchResult(BaseModel):
    """Model representing a single search result."""
    
    id: str = Field(..., description="Result ID")
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    type: str = Field(..., description="Result type")
    defect: DefectData = Field(..., description="Defect data")

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )


class SearchResponse(BaseModel):
    """Model for search response payload."""
    
    query: str = Field(..., description="Original search query")
    total_results: int = Field(..., ge=0, description="Total number of results")
    execution_time_ms: float = Field(..., ge=0, description="Execution time in milliseconds")
    results: List[SearchResult] = Field(default_factory=list, description="Search results")

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )


class UpsertRequest(BaseModel):
    """Model for upsert request payload."""
    
    defect_code: str = Field(..., description="Unique defect identifier")
    defect_text: str = Field(..., description="Description of the defect")
    subsystem: str = Field(..., description="Subsystem code")
    severity: str = Field(default="Medium", description="Severity level")
    typical_frequency: str = Field(default="Unknown", description="How often this occurs")
    symptoms: List[str] = Field(default_factory=list, description="List of symptoms")
    detection_methods: List[str] = Field(default_factory=list, description="Detection methods")
    early_warning_signals: List[str] = Field(default_factory=list, description="Early warning signals")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    likely_root_causes: List[str] = Field(default_factory=list, description="Likely root causes")
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended actions")

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )


class UpsertResponse(BaseModel):
    """Model for upsert response payload."""
    
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    defect_code: str = Field(..., description="Defect code that was processed")
    operation: str = Field(..., description="Operation performed (created/updated)")

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )


class HealthResponse(BaseModel):
    """Model for health check response."""
    
    status: str = Field(..., description="Health status")
    message: str = Field(..., description="Health message")
    pinecone_connected: bool = Field(..., description="Whether Pinecone is connected")

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )


class ErrorResponse(BaseModel):
    """Model for error responses."""
    
    detail: str = Field(..., description="Error detail message")
    error_code: Optional[str] = Field(None, description="Optional error code")
    timestamp: Optional[str] = Field(None, description="Error timestamp")

    model_config = ConfigDict(
        validate_assignment=True,
        extra="allow"  # Allow extra fields for flexibility
    )
