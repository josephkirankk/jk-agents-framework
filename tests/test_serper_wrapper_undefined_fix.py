"""
Unit Test: SerperToolWrapper - 'undefined' Parameter Fix

Tests that SerperToolWrapper correctly filters out 'undefined' and invalid query parameters.

This test validates the fix for the bug where the string "undefined" was being passed
as a query parameter to the Serper MCP google_search tool.
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.mcp_loader import SerperToolWrapper


class TestSerperWrapperUndefinedFix:
    """Test suite for SerperToolWrapper 'undefined' parameter fix"""
    
    @pytest.mark.asyncio
    async def test_filters_undefined_string_in_dict(self):
        """Test that 'undefined' string in dict params is filtered out"""
        # Create mock MCP tool
        mock_tool = Mock()
        mock_tool.name = "google_search"
        mock_tool.description = "Search Google"
        
        async def mock_arun(params):
            return json.dumps({"results": []})
        
        mock_tool.arun = mock_arun
        
        # Create wrapper
        wrapper = SerperToolWrapper(inner=mock_tool)
        
        # Call with 'undefined' as query value
        params = {"query": "undefined"}
        
        # Should raise ValueError because query is invalid
        with pytest.raises(ValueError, match="google_search requires a valid 'q' or 'query' parameter"):
            await wrapper._arun(params)
    
    @pytest.mark.asyncio
    async def test_filters_undefined_string_literal(self):
        """Test that literal 'undefined' string argument is filtered out"""
        # Create mock MCP tool
        mock_tool = Mock()
        mock_tool.name = "google_search"
        mock_tool.description = "Search Google"
        
        async def mock_arun(params):
            return json.dumps({"results": []})
        
        mock_tool.arun = mock_arun
        
        # Create wrapper
        wrapper = SerperToolWrapper(inner=mock_tool)
        
        # Call with string "undefined" as positional arg
        # Should raise ValueError because it's treated as invalid
        with pytest.raises(ValueError, match="google_search requires a valid 'q' or 'query' parameter"):
            await wrapper._arun("undefined")
    
    @pytest.mark.asyncio
    async def test_filters_empty_string_query(self):
        """Test that empty string query is filtered out"""
        # Create mock MCP tool
        mock_tool = Mock()
        mock_tool.name = "google_search"
        mock_tool.description = "Search Google"
        
        async def mock_arun(params):
            return json.dumps({"results": []})
        
        mock_tool.arun = mock_arun
        
        # Create wrapper
        wrapper = SerperToolWrapper(inner=mock_tool)
        
        # Call with empty string
        with pytest.raises(ValueError, match="google_search requires a valid 'q' or 'query' parameter"):
            await wrapper._arun({"query": ""})
    
    @pytest.mark.asyncio
    async def test_filters_none_query(self):
        """Test that None query is filtered out"""
        # Create mock MCP tool
        mock_tool = Mock()
        mock_tool.name = "google_search"
        mock_tool.description = "Search Google"
        
        async def mock_arun(params):
            return json.dumps({"results": []})
        
        mock_tool.arun = mock_arun
        
        # Create wrapper
        wrapper = SerperToolWrapper(inner=mock_tool)
        
        # Call with None
        with pytest.raises(ValueError, match="google_search requires a valid 'q' or 'query' parameter"):
            await wrapper._arun({"query": None})
    
    @pytest.mark.asyncio
    async def test_accepts_valid_query_string(self):
        """Test that valid query strings are accepted"""
        # Create mock MCP tool
        mock_tool = Mock()
        mock_tool.name = "google_search"
        mock_tool.description = "Search Google"
        
        captured_params = {}
        
        async def mock_arun(params):
            captured_params.clear()
            captured_params.update(params)
            return json.dumps({"results": ["result1"]})
        
        mock_tool.arun = mock_arun
        
        # Create wrapper
        wrapper = SerperToolWrapper(inner=mock_tool)
        
        # Call with valid query
        result = await wrapper._arun({"query": "best smartphones India"})
        
        # Should have converted 'query' to 'q' and injected defaults
        assert captured_params["q"] == "best smartphones India"
        assert captured_params["gl"] == "us"
        assert captured_params["hl"] == "en"
        assert "query" not in captured_params
    
    @pytest.mark.asyncio
    async def test_accepts_valid_query_in_q_parameter(self):
        """Test that valid query in 'q' parameter is accepted"""
        # Create mock MCP tool
        mock_tool = Mock()
        mock_tool.name = "google_search"
        mock_tool.description = "Search Google"
        
        captured_params = {}
        
        async def mock_arun(params):
            captured_params.clear()
            captured_params.update(params)
            return json.dumps({"results": ["result1"]})
        
        mock_tool.arun = mock_arun
        
        # Create wrapper
        wrapper = SerperToolWrapper(inner=mock_tool)
        
        # Call with 'q' directly (already converted)
        result = await wrapper._arun({"q": "test query", "gl": "in"})
        
        # Should keep 'q' and inject missing defaults
        assert captured_params["q"] == "test query"
        assert captured_params["gl"] == "in"
        assert captured_params["hl"] == "en"
    
    @pytest.mark.asyncio
    async def test_filters_case_insensitive_undefined(self):
        """Test that 'undefined' is filtered regardless of case"""
        # Create mock MCP tool
        mock_tool = Mock()
        mock_tool.name = "google_search"
        mock_tool.description = "Search Google"
        
        async def mock_arun(params):
            return json.dumps({"results": []})
        
        mock_tool.arun = mock_arun
        
        # Create wrapper
        wrapper = SerperToolWrapper(inner=mock_tool)
        
        # Test different cases
        test_cases = ["undefined", "UNDEFINED", "Undefined", "UnDeFiNeD"]
        
        for test_value in test_cases:
            with pytest.raises(ValueError, match="google_search requires a valid 'q' or 'query' parameter"):
                await wrapper._arun({"query": test_value})
    
    @pytest.mark.asyncio
    async def test_filters_null_string(self):
        """Test that 'null' string is filtered out"""
        # Create mock MCP tool
        mock_tool = Mock()
        mock_tool.name = "google_search"
        mock_tool.description = "Search Google"
        
        async def mock_arun(params):
            return json.dumps({"results": []})
        
        mock_tool.arun = mock_arun
        
        # Create wrapper
        wrapper = SerperToolWrapper(inner=mock_tool)
        
        # Call with "null" string
        with pytest.raises(ValueError, match="google_search requires a valid 'q' or 'query' parameter"):
            await wrapper._arun("null")
    
    @pytest.mark.asyncio
    async def test_filters_none_string(self):
        """Test that 'None' string is filtered out"""
        # Create mock MCP tool
        mock_tool = Mock()
        mock_tool.name = "google_search"
        mock_tool.description = "Search Google"
        
        async def mock_arun(params):
            return json.dumps({"results": []})
        
        mock_tool.arun = mock_arun
        
        # Create wrapper
        wrapper = SerperToolWrapper(inner=mock_tool)
        
        # Call with "None" string
        with pytest.raises(ValueError, match="google_search requires a valid 'q' or 'query' parameter"):
            await wrapper._arun("None")
    
    @pytest.mark.asyncio
    async def test_handles_list_arg_with_valid_query(self):
        """Test that list args with valid query are handled correctly"""
        # Create mock MCP tool
        mock_tool = Mock()
        mock_tool.name = "google_search"
        mock_tool.description = "Search Google"
        
        captured_params = {}
        
        async def mock_arun(params):
            captured_params.clear()
            captured_params.update(params)
            return json.dumps({"results": ["result1"]})
        
        mock_tool.arun = mock_arun
        
        # Create wrapper
        wrapper = SerperToolWrapper(inner=mock_tool)
        
        # Call with list containing dict (as seen in some tool invocations)
        list_arg = [{'query': 'smartphones India', 'gl': 'in'}]
        result = await wrapper._arun(list_arg)
        
        # Should unwrap list and convert parameters
        assert captured_params["q"] == "smartphones India"
        assert captured_params["gl"] == "in"
        assert captured_params["hl"] == "en"
        assert "query" not in captured_params


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
