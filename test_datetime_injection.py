#!/usr/bin/env python3
"""
Comprehensive tests for datetime injection functionality in the JK-Agents Framework.

This test suite ensures that datetime placeholders work correctly across
different scenarios, platforms, and edge cases.
"""

import pytest
import sys
import os
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add the app directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from placeholder_system import (
    PlaceholderContext,
    SystemPlaceholderProvider,
    get_default_registry
)
from placeholder_system.exceptions import PlaceholderNotFoundError
from template_utils import render_prompt_with_placeholders


class TestSystemPlaceholderProvider:
    """Test the enhanced SystemPlaceholderProvider datetime functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.provider = SystemPlaceholderProvider()
        self.mock_context = {}
    
    def test_basic_datetime_placeholders(self):
        """Test basic datetime placeholder resolution."""
        test_datetime = datetime(2025, 9, 24, 14, 30, 45)
        
        with patch('app.placeholder_system.providers.datetime') as mock_dt:
            mock_dt.now.return_value = test_datetime
            mock_dt.now.return_value.astimezone.return_value.isoformat.return_value = "2025-09-24T14:30:45-07:00"
            mock_dt.now.return_value.timestamp.return_value = 1727212245.0
            
            # Test timestamp
            result = self.provider.get_placeholder_value("timestamp", self.mock_context)
            assert isinstance(result, str)
            
            # Test date
            result = self.provider.get_placeholder_value("date", self.mock_context)
            assert result == "2025-09-24"
            
            # Test time
            result = self.provider.get_placeholder_value("time", self.mock_context)
            assert result == "14:30:45"
    
    def test_formatted_date_placeholders(self):
        """Test various date formatting placeholders."""
        test_datetime = datetime(2025, 9, 24, 14, 30, 45)
        
        with patch('app.placeholder_system.providers.datetime') as mock_dt:
            mock_dt.now.return_value = test_datetime
            
            # Test US format
            result = self.provider.get_placeholder_value("date_us", self.mock_context)
            assert result == "09/24/2025"
            
            # Test EU format
            result = self.provider.get_placeholder_value("date_eu", self.mock_context)
            assert result == "24/09/2025"
            
            # Test long format
            result = self.provider.get_placeholder_value("date_long", self.mock_context)
            assert result == "September 24, 2025"
            
            # Test short format
            result = self.provider.get_placeholder_value("date_short", self.mock_context)
            assert result == "Sep 24, 2025"
    
    def test_time_format_placeholders(self):
        """Test different time format placeholders."""
        test_datetime = datetime(2025, 9, 24, 14, 30, 45)
        
        with patch('app.placeholder_system.providers.datetime') as mock_dt:
            mock_dt.now.return_value = test_datetime
            
            # Test 24-hour format
            result = self.provider.get_placeholder_value("time_24h", self.mock_context)
            assert result == "14:30:45"
            
            # Test 12-hour format
            result = self.provider.get_placeholder_value("time_12h", self.mock_context)
            assert result == "02:30:45 PM"
    
    def test_timestamp_variants(self):
        """Test different timestamp format placeholders."""
        test_datetime = datetime(2025, 9, 24, 14, 30, 45)
        
        with patch('app.placeholder_system.providers.datetime') as mock_dt:
            mock_dt.now.return_value = test_datetime
            mock_dt.now.return_value.timestamp.return_value = 1727212245.0
            
            # Test Unix timestamp
            result = self.provider.get_placeholder_value("timestamp_unix", self.mock_context)
            assert result == 1727212245
            
            # Test milliseconds timestamp
            result = self.provider.get_placeholder_value("timestamp_ms", self.mock_context)
            assert result == 1727212245000
    
    def test_date_components(self):
        """Test individual date/time component placeholders."""
        test_datetime = datetime(2025, 9, 24, 14, 30, 45)  # Tuesday
        
        with patch('app.placeholder_system.providers.datetime') as mock_dt:
            mock_dt.now.return_value = test_datetime
            
            # Test year
            result = self.provider.get_placeholder_value("year", self.mock_context)
            assert result == 2025
            
            # Test month
            result = self.provider.get_placeholder_value("month", self.mock_context)
            assert result == 9
            
            # Test day
            result = self.provider.get_placeholder_value("day", self.mock_context)
            assert result == 24
            
            # Test month name
            result = self.provider.get_placeholder_value("month_name", self.mock_context)
            assert result == "September"
            
            # Test month short
            result = self.provider.get_placeholder_value("month_short", self.mock_context)
            assert result == "Sep"
            
            # Test day name
            result = self.provider.get_placeholder_value("day_name", self.mock_context)
            assert result == "Tuesday"
            
            # Test day short
            result = self.provider.get_placeholder_value("day_short", self.mock_context)
            assert result == "Tue"
            
            # Test quarter
            result = self.provider.get_placeholder_value("quarter", self.mock_context)
            assert result == 3  # September is Q3
    
    def test_week_number(self):
        """Test ISO week number calculation."""
        test_datetime = datetime(2025, 9, 24, 14, 30, 45)
        
        with patch('app.placeholder_system.providers.datetime') as mock_dt:
            mock_dt.now.return_value = test_datetime
            mock_dt.now.return_value.isocalendar.return_value = (2025, 39, 2)  # Week 39, Tuesday
            
            result = self.provider.get_placeholder_value("week_number", self.mock_context)
            assert result == 39
    
    def test_unsupported_placeholder(self):
        """Test handling of unsupported placeholders."""
        with pytest.raises(Exception):  # Should raise PlaceholderProviderError
            self.provider.get_placeholder_value("invalid_placeholder", self.mock_context)
    
    def test_supported_placeholders_set(self):
        """Test that all expected datetime placeholders are supported."""
        expected_placeholders = {
            "timestamp", "datetime", "datetime_local", "datetime_utc",
            "date", "time", "time_24h", "time_12h",
            "date_iso", "date_us", "date_eu", "date_long", "date_short",
            "timestamp_unix", "timestamp_ms",
            "year", "month", "month_name", "month_short",
            "day", "day_name", "day_short", "week_number", "quarter"
        }
        
        supported = self.provider.get_supported_placeholders()
        
        # All expected datetime placeholders should be supported
        for placeholder in expected_placeholders:
            assert placeholder in supported, f"Missing datetime placeholder: {placeholder}"
    
    def test_documentation_availability(self):
        """Test that documentation is available for datetime placeholders."""
        datetime_placeholders = [
            "timestamp", "datetime", "date", "time", "time_12h",
            "date_long", "timestamp_unix", "year", "month_name", "quarter"
        ]
        
        for placeholder in datetime_placeholders:
            doc = self.provider.get_placeholder_documentation(placeholder)
            assert doc is not None, f"Missing documentation for {placeholder}"
            assert len(doc) > 0, f"Empty documentation for {placeholder}"


class TestPlaceholderContext:
    """Test PlaceholderContext integration with datetime placeholders."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.context = PlaceholderContext()
    
    def test_datetime_placeholders_in_context(self):
        """Test that datetime placeholders are available in built context."""
        built_context = self.context.build_context()
        
        # Check that key datetime placeholders are present
        datetime_keys = ["timestamp", "date", "time", "year", "month", "day"]
        for key in datetime_keys:
            assert key in built_context, f"Missing datetime placeholder in context: {key}"
    
    def test_custom_datetime_placeholders(self):
        """Test adding custom datetime-related placeholders."""
        custom_placeholders = {
            "custom_date_format": "2025-Q3",
            "project_start_date": "2025-01-01"
        }
        
        self.context.add_custom_placeholders(custom_placeholders)
        built_context = self.context.build_context()
        
        assert built_context["custom_date_format"] == "2025-Q3"
        assert built_context["project_start_date"] == "2025-01-01"


class TestTemplateRendering:
    """Test datetime placeholder integration with template rendering."""
    
    def test_datetime_placeholders_in_template(self):
        """Test rendering templates with datetime placeholders."""
        template = """
        Current session: {{datetime}}
        Analysis date: {{date_long}}
        Time: {{time_12h}}
        Quarter: Q{{quarter}} {{year}}
        """
        
        # Mock datetime for consistent testing
        test_datetime = datetime(2025, 9, 24, 14, 30, 45)
        
        with patch('app.placeholder_system.providers.datetime') as mock_dt:
            mock_dt.now.return_value = test_datetime
            mock_dt.now.return_value.astimezone.return_value.isoformat.return_value = "2025-09-24T14:30:45-07:00"
            
            result = render_prompt_with_placeholders(template)
            
            # Check that placeholders were replaced with actual values
            assert "{{datetime}}" not in result
            assert "{{date_long}}" not in result  
            assert "{{time_12h}}" not in result
            assert "{{quarter}}" not in result
            assert "{{year}}" not in result
            
            # Check some expected content
            assert "September 24, 2025" in result
            assert "02:30:45 PM" in result
            assert "Q3 2025" in result
    
    def test_business_context_with_datetime(self):
        """Test business context template with datetime placeholders."""
        business_context_template = """
        **CURRENT SESSION**: {{datetime}} ({{day_name}}, {{date_long}})
        **ANALYSIS PERIOD**: {{month_name}} {{year}}, Week {{week_number}}
        
        You are analyzing Azure DevOps data for the current period.
        Current time context: {{date}} {{time}}
        """
        
        test_datetime = datetime(2025, 9, 24, 14, 30, 45)
        
        with patch('app.placeholder_system.providers.datetime') as mock_dt:
            mock_dt.now.return_value = test_datetime
            mock_dt.now.return_value.astimezone.return_value.isoformat.return_value = "2025-09-24T14:30:45-07:00"
            mock_dt.now.return_value.isocalendar.return_value = (2025, 39, 2)
            
            result = render_prompt_with_placeholders(business_context_template)
            
            # Verify key datetime information is present
            assert "Tuesday, September 24, 2025" in result
            assert "September 2025, Week 39" in result
            assert "2025-09-24 14:30:45" in result


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_different_timezones(self):
        """Test datetime placeholders work across different timezones."""
        provider = SystemPlaceholderProvider()
        
        # Test UTC timezone
        with patch('app.placeholder_system.providers.datetime') as mock_dt:
            utc_time = datetime(2025, 9, 24, 21, 30, 45, tzinfo=timezone.utc)
            mock_dt.now.side_effect = [datetime.now(), utc_time]
            mock_dt.now.return_value = datetime.now()
            
            # Should not raise errors
            result = provider.get_placeholder_value("datetime_utc", {})
            assert isinstance(result, str)
    
    def test_year_boundary_cases(self):
        """Test datetime placeholders around year boundaries."""
        provider = SystemPlaceholderProvider()
        
        # Test New Year's Day
        new_years = datetime(2025, 1, 1, 0, 0, 1)
        
        with patch('app.placeholder_system.providers.datetime') as mock_dt:
            mock_dt.now.return_value = new_years
            
            quarter = provider.get_placeholder_value("quarter", {})
            assert quarter == 1
            
            month = provider.get_placeholder_value("month", {})
            assert month == 1
    
    def test_leap_year_handling(self):
        """Test datetime placeholders handle leap years correctly."""
        provider = SystemPlaceholderProvider()
        
        # Test February 29th in a leap year (2024 is a leap year)
        leap_day = datetime(2024, 2, 29, 12, 0, 0)
        
        with patch('app.placeholder_system.providers.datetime') as mock_dt:
            mock_dt.now.return_value = leap_day
            
            date_result = provider.get_placeholder_value("date", {})
            assert date_result == "2024-02-29"
            
            month_result = provider.get_placeholder_value("month", {})
            assert month_result == 2


class TestPerformance:
    """Test performance characteristics of datetime injection."""
    
    def test_multiple_placeholder_resolution_performance(self):
        """Test that resolving many datetime placeholders is efficient."""
        import time
        
        context = PlaceholderContext()
        
        # Build context with many datetime placeholders
        start_time = time.time()
        
        for _ in range(100):  # Test 100 iterations
            built_context = context.build_context()
            # Access several datetime placeholders
            _ = built_context.get("timestamp")
            _ = built_context.get("date")
            _ = built_context.get("time")
            _ = built_context.get("year")
            _ = built_context.get("month")
            _ = built_context.get("day")
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete reasonably quickly (under 1 second for 100 iterations)
        assert execution_time < 1.0, f"Performance test failed: {execution_time:.3f} seconds"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])