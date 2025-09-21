"""
Enhanced Defect Analysis API Client Example

This script demonstrates how to use the new /defect-analysis-with-pilger endpoint
that combines DefectAnalysisPipeline and PilgerProcessingPipeline for comprehensive
equipment defect analysis.
"""

import asyncio
import json
import requests
from typing import Dict, Any, Optional


class EnhancedDefectAnalysisClient:
    """Client for the Enhanced Defect Analysis API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the client.
        
        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url.rstrip('/')
        self.endpoint = f"{self.base_url}/defect-analysis-with-pilger"
        self.form_endpoint = f"{self.base_url}/defect-analysis-with-pilger/form"
    
    def analyze_defect(
        self,
        user_input: str,
        top_n: int = 10,
        min_score: float = 0.6,
        enable_logging: bool = True,
        enable_caching: bool = True,
        parallel_search: bool = True,
        pilger_timeout_seconds: int = 120,
        pilger_format: str = "structured",
        skip_pilger_processing: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze equipment defect using both DefectAnalysisPipeline and PilgerProcessingPipeline.
        
        Args:
            user_input: Equipment issue description
            top_n: Number of top results from vector search
            min_score: Minimum similarity score for results
            enable_logging: Enable detailed logging
            enable_caching: Enable caching for repeated queries
            parallel_search: Enable parallel vector search
            pilger_timeout_seconds: Timeout for Pilger processing
            pilger_format: Format for Pilger agent input ("structured" or "text")
            skip_pilger_processing: Skip Pilger processing stage
            
        Returns:
            Dictionary containing the complete analysis results
        """
        payload = {
            "user_input": user_input,
            "top_n": top_n,
            "min_score": min_score,
            "enable_logging": enable_logging,
            "enable_caching": enable_caching,
            "parallel_search": parallel_search,
            "pilger_timeout_seconds": pilger_timeout_seconds,
            "pilger_format": pilger_format,
            "skip_pilger_processing": skip_pilger_processing
        }
        
        try:
            response = requests.post(self.endpoint, json=payload, timeout=300)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "original_input": user_input
            }
    
    def analyze_defect_form(
        self,
        user_input: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze equipment defect using form data submission.
        
        Args:
            user_input: Equipment issue description
            **kwargs: Additional parameters (same as analyze_defect)
            
        Returns:
            Dictionary containing the complete analysis results
        """
        # Set defaults
        form_data = {
            "user_input": user_input,
            "top_n": kwargs.get("top_n", 10),
            "min_score": kwargs.get("min_score", 0.6),
            "enable_logging": kwargs.get("enable_logging", True),
            "enable_caching": kwargs.get("enable_caching", True),
            "parallel_search": kwargs.get("parallel_search", True),
            "pilger_timeout_seconds": kwargs.get("pilger_timeout_seconds", 120),
            "pilger_format": kwargs.get("pilger_format", "structured"),
            "skip_pilger_processing": kwargs.get("skip_pilger_processing", False)
        }
        
        try:
            response = requests.post(self.form_endpoint, data=form_data, timeout=300)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Form request failed: {str(e)}",
                "original_input": user_input
            }


def print_analysis_results(result: Dict[str, Any]) -> None:
    """Print analysis results in a formatted way."""
    print("\n" + "=" * 80)
    print("ENHANCED DEFECT ANALYSIS RESULTS")
    print("=" * 80)
    
    print(f"📝 Input: {result.get('original_input', 'N/A')}")
    print(f"✅ Success: {result.get('success', False)}")
    print(f"⏱️  Total Time: {result.get('total_processing_time_ms', 0):.2f}ms")
    
    if result.get('error'):
        print(f"❌ Error: {result['error']}")
        return
    
    # Defect Analysis Results
    defect_analysis = result.get('defect_analysis', {})
    if defect_analysis:
        print(f"\n🔍 DEFECT ANALYSIS STAGE:")
        print(f"   ✅ Success: {defect_analysis.get('success', False)}")
        print(f"   📊 Results: {defect_analysis.get('total_unique_results', 0)} defects found")
        
        intent_data = defect_analysis.get('intent_data', {})
        if intent_data:
            print(f"   🏷️  Component: {intent_data.get('component', 'Unknown')}")
            print(f"   🔧 Sub-component: {intent_data.get('sub_component', 'Unknown')}")
            print(f"   ⚠️  Issue: {intent_data.get('issue', 'Unknown')}")
        
        print(f"   🛠️  Actions: {len(defect_analysis.get('corrective_actions', []))}")
        print(f"   ⏱️  Time: {defect_analysis.get('processing_time_ms', 0):.2f}ms")
    
    # Pilger Processing Results
    pilger_processing = result.get('pilger_processing')
    if pilger_processing:
        print(f"\n🤖 PILGER PROCESSING STAGE:")
        print(f"   ✅ Success: {pilger_processing.get('success', False)}")
        print(f"   💡 Insights: {len(pilger_processing.get('processed_insights', []))}")
        print(f"   🛠️  Actions: {len(pilger_processing.get('recommended_actions', []))}")
        print(f"   🎯 Confidence: {pilger_processing.get('confidence_score', 'N/A')}")
        print(f"   ⏱️  Time: {pilger_processing.get('processing_time_ms', 0):.2f}ms")
        
        if pilger_processing.get('error_message'):
            print(f"   ❌ Error: {pilger_processing['error_message']}")
    else:
        print(f"\n🤖 PILGER PROCESSING STAGE: Skipped or failed")
    
    # Combined Results
    print(f"\n📈 COMBINED RESULTS:")
    print(f"   💡 Total Insights: {len(result.get('total_insights', []))}")
    print(f"   🛠️  Total Actions: {len(result.get('total_recommended_actions', []))}")
    
    # Show sample insights and actions
    insights = result.get('total_insights', [])
    if insights:
        print(f"   📝 Sample Insights:")
        for i, insight in enumerate(insights[:3], 1):
            print(f"      {i}. {insight}")
    
    actions = result.get('total_recommended_actions', [])
    if actions:
        print(f"   📝 Sample Actions:")
        for i, action in enumerate(actions[:3], 1):
            print(f"      {i}. {action}")
    
    # Warnings
    warnings = result.get('warnings', [])
    if warnings:
        print(f"\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"   - {warning}")


def main():
    """Main function demonstrating the Enhanced Defect Analysis API."""
    print("🚀 Enhanced Defect Analysis API Client Example")
    print("=" * 80)
    
    # Initialize client
    client = EnhancedDefectAnalysisClient()
    
    # Test cases
    test_cases = [
        {
            "name": "Pump Piston Issue",
            "input": "The pump's loading/unloading piston is not operating smoothly",
            "config": {"top_n": 5, "min_score": 0.7}
        },
        {
            "name": "Motor Bearing Problem",
            "input": "Motor bearing overheating",
            "config": {"pilger_format": "text", "pilger_timeout_seconds": 60}
        },
        {
            "name": "Hydraulic System Issue",
            "input": "Hydraulic pump cavitation detected",
            "config": {"skip_pilger_processing": True}  # Skip Pilger for this test
        },
        {
            "name": "Gear Wear Issue",
            "input": "Gear tooth broken in transmission",
            "config": {"top_n": 8, "pilger_format": "structured"}
        }
    ]
    
    # Run test cases
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔄 Test Case {i}: {test_case['name']}")
        print("-" * 60)
        
        try:
            # Analyze using JSON endpoint
            result = client.analyze_defect(
                user_input=test_case["input"],
                **test_case["config"]
            )
            
            print_analysis_results(result)
            
            # Test form endpoint for first case
            if i == 1:
                print(f"\n🔄 Testing Form Endpoint for: {test_case['name']}")
                print("-" * 60)
                
                form_result = client.analyze_defect_form(
                    user_input=test_case["input"],
                    **test_case["config"]
                )
                
                print(f"📝 Form endpoint result: Success={form_result.get('success', False)}")
                print(f"⏱️  Form processing time: {form_result.get('total_processing_time_ms', 0):.2f}ms")
        
        except Exception as e:
            print(f"❌ Test case failed: {e}")
    
    print(f"\n" + "=" * 80)
    print("EXAMPLE COMPLETED")
    print("=" * 80)
    print("The Enhanced Defect Analysis API provides comprehensive two-stage processing:")
    print("1. DefectAnalysisPipeline: Intent extraction, vector search, result aggregation")
    print("2. PilgerProcessingPipeline: Additional insights via jk_pilger_new_entries_agent")
    print("\nBoth JSON and form endpoints are available for integration flexibility.")


if __name__ == "__main__":
    main()
