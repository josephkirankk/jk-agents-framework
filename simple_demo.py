"""
Simple Direct Demo of Large Data Optimization System

This demo shows the large data optimization components working together
without requiring the full agent framework.
"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from core.large_data_storage import LargeDataStorage
from core.smart_tool_wrapper import SmartToolWrapper
from tools.large_data_test_tools import (
    fetch_sales_data,
    get_user_analytics,
    export_financial_report,
    search_documents
)

def main():
    """Demonstrate the large data optimization system step by step"""
    print("🚀 Large Data Optimization System - Direct Demo")
    print("=" * 60)
    
    # Step 1: Setup
    print("\n📋 Step 1: Setting up components...")
    
    # Create demo directories
    os.makedirs("./demo_data", exist_ok=True)
    os.makedirs("./demo_data/large_files", exist_ok=True)
    
    # Initialize storage
    storage = LargeDataStorage(
        storage_path="./demo_data/large_data_storage.db",
        file_storage_path="./demo_data/large_files",
        compression_enabled=True
    )
    
    # Initialize wrapper with low threshold for demo
    wrapper = SmartToolWrapper(
        storage=storage,
        token_threshold=2000,  # Low threshold to trigger optimization
        summarization_max_tokens=300
    )
    
    print("✅ Storage and wrapper initialized")
    
    # Step 2: Test with small data (should return directly)
    print("\n📊 Step 2: Testing small data (returns directly)...")
    
    small_sales_data = fetch_sales_data.invoke({
        "num_records": 50,
        "include_details": False
    })
    
    wrapped_small = wrapper.wrap_tool_result(small_sales_data, "fetch_sales_data")
    
    print(f"   Small data: {len(small_sales_data)} records")
    print(f"   Returned type: {type(wrapped_small)}")
    print(f"   Was wrapped: {'No' if isinstance(wrapped_small, list) else 'Yes'}")
    
    # Step 3: Test with large data (should create reference)
    print("\n📈 Step 3: Testing large data (creates reference)...")
    
    large_sales_data = fetch_sales_data.invoke({
        "num_records": 5000,
        "include_details": True
    })
    
    wrapped_large = wrapper.wrap_tool_result(large_sales_data, "fetch_sales_data")
    
    print(f"   Large data: {len(large_sales_data)} records")
    print(f"   Returned type: {type(wrapped_large)}")
    print(f"   Was wrapped: {'Yes' if isinstance(wrapped_large, dict) and 'reference_id' in wrapped_large else 'No'}")
    
    if isinstance(wrapped_large, dict) and "reference_id" in wrapped_large:
        ref_id = wrapped_large["reference_id"]
        print(f"   Reference ID: {ref_id}")
        print(f"   Summary: {wrapped_large['summary'][:100]}...")
        print(f"   Dynamic tools: {len(wrapped_large['dynamic_tools'])}")
        
        # Step 4: Test dynamic tools
        print("\n🛠️ Step 4: Testing dynamic tools...")
        
        for tool_name in wrapped_large["dynamic_tools"][:2]:  # Test first 2 tools
            print(f"\n   Testing {tool_name}:")
            tool_func = wrapper.get_dynamic_tool_function(tool_name)
            
            if tool_func:
                try:
                    if "details" in tool_name:
                        result = tool_func(max_items=3)
                        print(f"     Got {len(result.get('sample_data', []))} sample items")
                    elif "stats" in tool_name:
                        result = tool_func()
                        print(f"     Storage info: {result['storage_info']['size_classification']}")
                        print(f"     Data type: {result['data_type']}")
                    
                except Exception as e:
                    print(f"     Error: {e}")
            else:
                print("     Tool function not found")
    
    # Step 5: Test multiple data types
    print("\n🔄 Step 5: Testing different data types...")
    
    # Test user analytics
    analytics_data = get_user_analytics.invoke({
        "timeframe_days": 90,
        "include_behavior": True
    })
    
    wrapped_analytics = wrapper.wrap_tool_result(analytics_data, "get_user_analytics")
    print(f"   Analytics data wrapped: {'Yes' if isinstance(wrapped_analytics, dict) and 'reference_id' in wrapped_analytics else 'No'}")
    
    # Test financial report
    financial_data = export_financial_report.invoke({
        "quarters": 6,
        "detailed": True
    })
    
    wrapped_financial = wrapper.wrap_tool_result(financial_data, "export_financial_report")
    print(f"   Financial data wrapped: {'Yes' if isinstance(wrapped_financial, dict) and 'reference_id' in wrapped_financial else 'No'}")
    
    # Step 6: Show storage statistics
    print("\n📊 Step 6: Storage statistics...")
    
    storage_stats = storage.get_storage_stats()
    print(f"   Total references: {storage_stats['total_references']}")
    print(f"   Total storage: {storage_stats['total_size_mb']:.2f} MB")
    print(f"   Size distribution: {storage_stats['size_distribution']}")
    
    wrapper_stats = wrapper.get_tool_stats()
    print(f"   Dynamic tools created: {wrapper_stats['total_dynamic_tools']}")
    
    # Step 7: Performance comparison
    print("\n⚡ Step 7: Performance comparison...")
    
    # Estimate token savings
    if isinstance(wrapped_large, dict) and "reference_id" in wrapped_large:
        original_tokens = wrapped_large["estimated_tokens"]
        wrapped_tokens = wrapper._estimate_tokens(wrapped_large)
        
        token_savings = ((original_tokens - wrapped_tokens) / original_tokens) * 100
        cost_savings = token_savings  # Roughly same ratio
        
        print(f"   Original data: {original_tokens:,} tokens")
        print(f"   Wrapped data: {wrapped_tokens:,} tokens")
        print(f"   Token savings: {token_savings:.1f}%")
        print(f"   Estimated cost savings: {cost_savings:.1f}%")
    
    print("\n" + "=" * 60)
    print("🎯 Demo Complete!")
    print("\n✨ Key Benefits Demonstrated:")
    print("   📦 Automatic large data detection")
    print("   🔗 Compact reference generation")
    print("   🛠️  Dynamic tool creation")
    print("   📊 Intelligent summarization")
    print("   💾 Efficient storage (SQLite + files)")
    print("   ⚡ Massive token & cost savings")
    
    print(f"\n📁 Demo data saved to: ./demo_data/")
    print("   You can inspect the SQLite database and file storage")
    
    # List created references
    references = storage.list_references(10)
    if references:
        print(f"\n📚 Created references:")
        for ref in references:
            print(f"   - {ref['reference_id']}: {ref['data_type']} ({ref['size_mb']:.2f}MB)")

if __name__ == "__main__":
    main()