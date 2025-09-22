"""
TsSearch Data Models

This module contains Pydantic models for the TsSearch (Typesense) API.
These models are completely separate from the existing VectorDB models.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class SearchType(str, Enum):
    """Supported search types for TsSearch API."""
    HYBRID = "hybrid"
    KEYWORD = "keyword"
    VECTOR = "vector"


class TsSearchFilters(BaseModel):
    """Filters for TsSearch requests."""
    machine: Optional[str] = Field(None, description="Machine type filter (e.g., PLG, CEN, ROT)")
    subsystem: Optional[str] = Field(None, description="Subsystem filter (e.g., GBX, MTR, PMP)")
    component: Optional[str] = Field(None, description="Component filter (e.g., BEARING, GEAR, SEAL)")
    defect_type: Optional[str] = Field(None, description="Defect type filter (e.g., OVERHEAT, WEAR, CRACK)")

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )


class TsSearchRequest(BaseModel):
    """Model for TsSearch request payload."""
    
    query: str = Field(..., min_length=1, description="Search query in natural language")
    search_type: SearchType = Field(default=SearchType.HYBRID, description="Type of search to perform")
    limit: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    collection: str = Field(default="defects", description="Collection to search in")
    filters: Optional[TsSearchFilters] = Field(None, description="Optional filters to apply")
    include_highlights: bool = Field(default=False, description="Whether to include highlights in results")
    min_text_match_score: Optional[float] = Field(None, ge=0.0, description="Minimum text match score")
    min_similarity_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum similarity score")

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )


class TsDefectResult(BaseModel):
    """Model for a single defect result from TsSearch."""
    
    id: str = Field(..., description="Unique identifier for the defect")
    defect_code: str = Field(..., description="Defect code (e.g., PLG.GBX.BEARING.OVERHEAT)")
    defect_text: str = Field(..., description="Defect description text")
    machine: str = Field(..., description="Machine type")
    subsystem: str = Field(..., description="Subsystem")
    component: str = Field(..., description="Component")
    defect_type: str = Field(..., description="Defect type")
    subsystem_description: str = Field(..., description="Subsystem description")
    component_description: str = Field(..., description="Component description")
    defect_type_description: str = Field(..., description="Defect type description")
    keywords: List[str] = Field(default_factory=list, description="Keywords associated with the defect")
    tags: List[str] = Field(default_factory=list, description="Tags associated with the defect")
    score: float = Field(..., description="Search relevance score")
    highlights: Optional[Dict[str, Any]] = Field(None, description="Search highlights if requested")
    created_on: int = Field(..., description="Creation timestamp")

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )


class TsSearchData(BaseModel):
    """Model for the data section of TsSearch response."""
    
    results: List[TsDefectResult] = Field(default_factory=list, description="Search results")
    total_found: int = Field(..., ge=0, description="Total number of results found")
    search_type: str = Field(..., description="Type of search performed")
    query: str = Field(..., description="Original search query")
    processing_time_ms: int = Field(..., ge=0, description="Processing time in milliseconds")
    collection: str = Field(..., description="Collection searched")
    filters_applied: Optional[Dict[str, Any]] = Field(None, description="Filters that were applied")

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )


class TsSearchResponse(BaseModel):
    """Model for TsSearch API response."""
    
    success: bool = Field(..., description="Whether the request was successful")
    data: TsSearchData = Field(..., description="Search results data")
    message: str = Field(..., description="Response message")
    timestamp: float = Field(..., description="Response timestamp")

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )


class TsSearchError(BaseModel):
    """Model for TsSearch API error response."""
    
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[str] = Field(None, description="Additional error details")

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )


class TsSearchErrorResponse(BaseModel):
    """Model for TsSearch API error response."""
    
    success: bool = Field(default=False, description="Always false for error responses")
    error: TsSearchError = Field(..., description="Error details")
    timestamp: float = Field(..., description="Error timestamp")

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )


# Convenience type for responses
TsSearchResult = Union[TsSearchResponse, TsSearchErrorResponse]
