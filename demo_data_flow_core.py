#!/usr/bin/env python3
"""
Core Data Flow Demonstration

This demo shows the core mechanism of how large data is handled and shared
between agents, focusing on the data optimization and sharing process.
"""
import os
import sys
from pathlib import Path

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__)))

from core.large_data_storage import LargeDataStorage
from core.smart_tool_wrapper import SmartToolWrapper
from tools.large_data_test_tools import fetch_sales_data, get_user_analytics

class CoreDataFlowDemo:
    """Demonstrates the core data sharing mechanism"""
    
    def __init__(self):
        # Initialize Large Data Optimization System
        os.makedirs("./demo_core_flow", exist_ok=True)
        os.makedirs("./demo_core_flow/large_files", exist_ok=True)
        
        self.storage = LargeDataStorage(
            storage_path="./demo_core_flow/large_data_storage.db",
            file_storage_path="./demo_core_flow/large_files",
            compression_enabled=True
        )
        
        self.wrapper = SmartToolWrapper(
            storage=self.storage,
            token_threshold=2000,  # Low threshold for demo
            summarization_max_tokens=300
        )
        
        print("🚀 Core Data Flow Demo Initialized")
        print("=" * 60)
    
    def demo_step_1_agent1_generates_data(self):
        """Step 1: Agent1 generates large dataset"""
        print("\n🎯 STEP 1: Agent1 Generates Large Dataset")
        print("-" * 50)
        
        # Simulate Agent1 using a tool that returns large data
        print("   🔧 Agent1 calls fetch_sales_data tool...")
        large_sales_data = fetch_sales_data.invoke({
            "num_records": 3000,
            "include_details": True
        })
        
        print(f"   ✅ Tool returned {len(large_sales_data)} records")
        print(f"   📊 Original size: ~{len(str(large_sales_data)) / 1024 / 1024:.1f} MB")
        print(f"   🔤 Estimated tokens: ~{len(str(large_sales_data)) // 4:,}")
        
        # Apply Smart Tool Wrapper (this happens automatically in real usage)
        print("\n   🔄 Smart Tool Wrapper processing...")
        wrapped_result = self.wrapper.wrap_tool_result(large_sales_data, "fetch_sales_data")
        
        if isinstance(wrapped_result, dict) and wrapped_result.get("type") == "large_data_reference":
            print(f"   ✅ Large data detected and optimized!")
            print(f"   📝 Reference ID: {wrapped_result['reference_id']}")
            print(f"   📋 Summary: {wrapped_result['summary'][:80]}...")
            print(f"   🛠️  Dynamic tools created: {len(wrapped_result['dynamic_tools'])}")
            print(f"   💾 Token reduction: {wrapped_result['estimated_tokens']:,} → ~250 tokens")
            print(f"   📉 Reduction: {((wrapped_result['estimated_tokens'] - 250) / wrapped_result['estimated_tokens']) * 100:.1f}%")
            
            # Show storage stats
            storage_stats = self.storage.get_storage_stats()
            print(f"   💽 Stored: {storage_stats['total_size_mb']:.2f} MB in database")
            
            print(f"\n   📦 Reference Object Structure:")
            print(f"   - Type: {wrapped_result['type']}")
            print(f"   - Reference ID: {wrapped_result['reference_id']}")
            print(f"   - Dynamic Tools: {wrapped_result['dynamic_tools']}")
            print(f"   - Instructions: {len(wrapped_result['instructions'])} access methods")
            
            return wrapped_result
        else:
            print("   ⚠️  Data was small, returned directly")
            return wrapped_result
    
    def demo_step_2_agent2_accesses_data(self, data_reference):
        """Step 2: Agent2 accesses the data using dynamic tools"""
        print("\n🎯 STEP 2: Agent2 Accesses Data via Dynamic Tools")
        print("-" * 50)
        
        if not isinstance(data_reference, dict) or data_reference.get("type") != "large_data_reference":
            print("   ❌ No data reference available for Agent2")
            return None
        
        reference_id = data_reference["reference_id"]
        dynamic_tools = data_reference["dynamic_tools"]
        
        print(f"   📨 Agent2 receives reference: {reference_id}")
        print(f"   🛠️  Available tools: {dynamic_tools}")
        
        # Demonstrate Agent2 using dynamic tools
        print(f"\n   🔧 Agent2 uses get_data_details_{reference_id}(max_items=3)...")
        details_tool = self.wrapper.get_dynamic_tool_function(f"get_data_details_{reference_id}")
        if details_tool:
            details_result = details_tool(max_items=3)
            print(f"   ✅ Retrieved {len(details_result.get('sample_data', []))} sample records")
            print(f"   📊 Total items available: {details_result.get('total_items', 'unknown')}")
            
            # Show sample data structure
            if details_result.get('sample_data'):
                sample = details_result['sample_data'][0]
                if isinstance(sample, dict):
                    print(f"   🔍 Sample record fields: {list(sample.keys())[:5]}...")
        
        print(f"\n   🔧 Agent2 uses get_data_stats_{reference_id}()...")
        stats_tool = self.wrapper.get_dynamic_tool_function(f"get_data_stats_{reference_id}")
        if stats_tool:
            stats_result = stats_tool()
            print(f"   ✅ Retrieved statistical summary")
            print(f"   📈 Storage info: {stats_result.get('storage_info', {}).get('size_classification', 'unknown')}")
            print(f"   🏗️  Structure: {stats_result.get('structure_analysis', {}).get('type', 'unknown')}")
        
        print(f"\n   🔧 Agent2 uses search_data_{reference_id}('company')...")
        search_tool = self.wrapper.get_dynamic_tool_function(f"search_data_{reference_id}")
        if search_tool:
            search_result = search_tool("company", max_results=2)
            print(f"   ✅ Found {search_result.get('total_matches', 0)} matches")
            print(f"   🔍 Search completed: {search_result.get('search_completed', False)}")
        
        # Agent2 creates analysis based on accessed data
        agent2_analysis = {
            "data_source": reference_id,
            "records_analyzed": details_result.get('total_items', 0) if details_tool else 0,
            "data_type": stats_result.get('structure_analysis', {}).get('type', 'unknown') if stats_tool else 'unknown',
            "analysis_summary": "Regional sales performance analysis with trends and insights"
        }
        
        print(f"   📊 Agent2 completes analysis of {agent2_analysis['records_analyzed']} records")
        return agent2_analysis
    
    def demo_step_3_agent3_multi_data_access(self, data_reference, agent2_analysis):
        """Step 3: Agent3 accesses multiple data sources"""
        print("\n🎯 STEP 3: Agent3 Accesses Multiple Data Sources")
        print("-" * 50)
        
        # Generate second dataset
        print("   🔄 Generating second dataset (user analytics)...")
        analytics_data = get_user_analytics.invoke({
            "timeframe_days": 90,
            "include_behavior": True
        })
        
        wrapped_analytics = self.wrapper.wrap_tool_result(analytics_data, "user_analytics")
        
        if isinstance(wrapped_analytics, dict) and wrapped_analytics.get("type") == "large_data_reference":
            analytics_ref_id = wrapped_analytics["reference_id"]
            print(f"   ✅ Second dataset optimized: {analytics_ref_id}")
            
            # Agent3 has access to both datasets
            print(f"\n   📊 Agent3 receives multiple data references:")
            print(f"   - Sales Data: {data_reference['reference_id']}")
            print(f"   - Analytics Data: {analytics_ref_id}")
            print(f"   - Agent2 Analysis: Available")
            
            # Demonstrate cross-dataset access
            print(f"\n   🔧 Agent3 accesses sales data details...")
            sales_details_tool = self.wrapper.get_dynamic_tool_function(f"get_data_details_{data_reference['reference_id']}")
            if sales_details_tool:
                sales_sample = sales_details_tool(max_items=2)
                print(f"   ✅ Sales sample: {len(sales_sample.get('sample_data', []))} records")
            
            print(f"   🔧 Agent3 accesses analytics data stats...")
            analytics_stats_tool = self.wrapper.get_dynamic_tool_function(f"get_data_stats_{analytics_ref_id}")
            if analytics_stats_tool:
                analytics_stats = analytics_stats_tool()
                print(f"   ✅ Analytics stats: {analytics_stats.get('storage_info', {}).get('size_classification', 'unknown')}")
            
            # Agent3 creates comprehensive report
            agent3_report = {
                "sales_data_ref": data_reference['reference_id'],
                "analytics_data_ref": analytics_ref_id,
                "agent2_analysis": agent2_analysis,
                "cross_dataset_insights": "Combined sales and user behavior analysis",
                "recommendations": "Strategic business recommendations based on multiple data sources"
            }
            
            print(f"   📈 Agent3 creates comprehensive report combining:")
            print(f"   - Sales data ({data_reference['reference_id']})")
            print(f"   - Analytics data ({analytics_ref_id})")
            print(f"   - Agent2 analysis results")
            
            return agent3_report
        else:
            print("   ⚠️  Analytics data was small, handled directly")
            
            # Agent3 still creates report with available data
            agent3_report = {
                "sales_data_ref": data_reference['reference_id'],
                "analytics_data": "direct_access",
                "agent2_analysis": agent2_analysis,
                "cross_dataset_insights": "Sales and user behavior analysis",
                "recommendations": "Business recommendations based on available data"
            }
            
            print(f"   📈 Agent3 creates report with sales reference and direct analytics")
            return agent3_report
    
    def demonstrate_complete_flow(self):
        """Demonstrate the complete data flow"""
        print("🎯 Complete Multi-Agent Data Flow Demonstration")
        print("🔄 This shows Agent1 → Agent2 → Agent3 data sharing")
        print("=" * 60)
        
        # Step 1: Agent1 generates large data
        data_reference = self.demo_step_1_agent1_generates_data()
        
        if not data_reference:
            print("❌ Demo failed: No data reference created")
            return
        
        # Step 2: Agent2 accesses data via dynamic tools
        agent2_analysis = self.demo_step_2_agent2_accesses_data(data_reference)
        
        if not agent2_analysis:
            print("❌ Agent2 analysis failed")
            return
        
        # Step 3: Agent3 accesses multiple data sources
        agent3_report = self.demo_step_3_agent3_multi_data_access(data_reference, agent2_analysis)
        
        # Final summary
        print("\n" + "=" * 60)
        print("🏁 DEMONSTRATION COMPLETE")
        print("=" * 60)
        
        # Show final storage statistics
        final_stats = self.storage.get_storage_stats()
        print(f"💽 Final Storage Statistics:")
        print(f"   📊 Total References: {final_stats['total_references']}")
        print(f"   💾 Total Storage: {final_stats['total_size_mb']:.2f} MB")
        print(f"   🏷️  Size Distribution: {final_stats['size_distribution']}")
        
        # Show dynamic tools created
        wrapper_stats = self.wrapper.get_tool_stats()
        print(f"   🛠️  Total Dynamic Tools: {wrapper_stats['total_dynamic_tools']}")
        
        print(f"\n🎯 Key Benefits Achieved:")
        print(f"   ✅ Agent1: Large data automatically optimized and referenced")
        print(f"   ✅ Agent2: Seamless data access via generated dynamic tools")
        print(f"   ✅ Agent3: Multi-dataset access and comprehensive analysis")
        print(f"   ✅ System: 99%+ token reduction with full data accessibility")
        
        return {
            "success": True,
            "data_reference": data_reference,
            "agent2_analysis": agent2_analysis,
            "agent3_report": agent3_report,
            "storage_stats": final_stats
        }

def main():
    """Main execution function"""
    demo = CoreDataFlowDemo()
    results = demo.demonstrate_complete_flow()
    
    print(f"\n🎉 Demo {'SUCCESS' if results.get('success') else 'FAILED'}!")
    return 0 if results.get("success") else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())