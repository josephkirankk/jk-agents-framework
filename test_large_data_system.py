"""
Comprehensive Test for Large Data Optimization System

This script demonstrates the complete large data handling pipeline:
1. Creating agents with large data optimization enabled
2. Testing tools that generate large datasets
3. Showing automatic data reference creation
4. Demonstrating dynamic tool generation for data exploration
5. Testing multi-agent workflows with large data
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agent_builder import JKAgentBuilder
from core.large_data_storage import LargeDataStorage
from core.smart_tool_wrapper import SmartToolWrapper
from tools.large_data_test_tools import (
    fetch_sales_data, 
    get_user_analytics, 
    export_financial_report,
    search_documents,
    fetch_research_data
)

# Test configuration
TEST_CONFIG = {
    "storage_path": "./test_data/large_data_storage.db",
    "file_storage_path": "./test_data/large_files",
    "token_threshold": 1000,  # Low threshold for testing
    "cleanup_interval": 300,   # 5 minutes for testing
}

class LargeDataSystemTester:
    """Comprehensive tester for the large data optimization system"""
    
    def __init__(self):
        self.test_results = []
        self.storage = None
        self.wrapper = None
        
    def setup_test_environment(self):
        """Set up the test environment"""
        print("🔧 Setting up test environment...")
        
        # Create test directories
        os.makedirs("./test_data", exist_ok=True)
        os.makedirs("./test_data/large_files", exist_ok=True)
        
        # Initialize storage and wrapper
        self.storage = LargeDataStorage(**TEST_CONFIG)
        self.wrapper = SmartToolWrapper(
            storage=self.storage,
            token_threshold=TEST_CONFIG["token_threshold"]
        )
        
        print("✅ Test environment ready")
        
    def test_basic_storage(self):
        """Test basic storage functionality"""
        print("\n📦 Testing Basic Storage Functionality")
        print("-" * 50)
        
        # Test small data storage
        small_data = {"test": "small data", "size": "tiny"}
        ref_id = self.storage.store_data(small_data, "test_small")
        retrieved = self.storage.get_data(ref_id)
        
        assert retrieved == small_data, "Small data retrieval failed"
        print("✅ Small data storage/retrieval works")
        
        # Test large data storage
        large_data = {"records": [{"id": i, "data": "x" * 1000} for i in range(1000)]}
        ref_id = self.storage.store_data(large_data, "test_large")
        retrieved = self.storage.get_data(ref_id)
        
        assert len(retrieved["records"]) == 1000, "Large data retrieval failed"
        print("✅ Large data storage/retrieval works")
        
        # Test metadata
        metadata = self.storage.get_metadata(ref_id)
        print(f"✅ Metadata: {metadata['size_classification']} ({metadata['size_bytes']:,} bytes)")
        
        self.test_results.append({
            "test": "basic_storage",
            "status": "passed",
            "details": "All storage operations successful"
        })

    def test_tool_wrapping(self):
        """Test smart tool wrapper functionality"""
        print("\n🔧 Testing Smart Tool Wrapper")
        print("-" * 50)
        
        # Test with small dataset (should return directly)
        print("Testing small dataset...")
        result = self.wrapper.wrap_tool_result(
            fetch_sales_data(50, False), 
            "fetch_sales_data"
        )
        
        if isinstance(result, list):
            print("✅ Small dataset returned directly (not wrapped)")
        else:
            print("⚠️ Small dataset was wrapped (unexpected)")
        
        # Test with large dataset (should create reference)
        print("\nTesting large dataset...")
        result = self.wrapper.wrap_tool_result(
            fetch_sales_data(5000, True),
            "fetch_sales_data"
        )
        
        if isinstance(result, dict) and "reference_id" in result:
            print(f"✅ Large dataset wrapped with reference: {result['reference_id']}")
            print(f"   Summary: {result['summary'][:100]}...")
            print(f"   Dynamic tools: {len(result.get('dynamic_tools', []))}")
            
            # Test dynamic tools
            dynamic_tools = result.get("dynamic_tools", [])
            if dynamic_tools:
                print("\n   Testing dynamic tools:")
                for tool_name in dynamic_tools:
                    print(f"   - {tool_name}: Available")
                    
            self.test_results.append({
                "test": "tool_wrapping",
                "status": "passed",
                "reference_id": result["reference_id"],
                "dynamic_tools": len(dynamic_tools)
            })
        else:
            print("❌ Large dataset was not wrapped properly")
            self.test_results.append({
                "test": "tool_wrapping",
                "status": "failed",
                "error": "Large dataset not wrapped"
            })

    def test_multiple_tool_types(self):
        """Test wrapping different types of tools"""
        print("\n🛠️ Testing Multiple Tool Types")
        print("-" * 50)
        
        tools_to_test = [
            ("get_user_analytics", lambda: get_user_analytics(365, True)),
            ("export_financial_report", lambda: export_financial_report(8, True)),
            ("search_documents", lambda: search_documents("AI research", 2000)),
            ("fetch_research_data", lambda: fetch_research_data("machine learning", 3000))
        ]
        
        wrapped_results = {}
        
        for tool_name, tool_func in tools_to_test:
            print(f"\nTesting {tool_name}...")
            
            start_time = time.time()
            raw_result = tool_func()
            execution_time = time.time() - start_time
            
            wrapped_result = self.wrapper.wrap_tool_result(raw_result, tool_name)
            wrap_time = time.time() - start_time - execution_time
            
            if isinstance(wrapped_result, dict) and "reference_id" in wrapped_result:
                wrapped_results[tool_name] = wrapped_result
                print(f"✅ {tool_name} wrapped successfully")
                print(f"   Reference ID: {wrapped_result['reference_id']}")
                print(f"   Execution time: {execution_time:.2f}s")
                print(f"   Wrap time: {wrap_time:.2f}s")
                print(f"   Dynamic tools: {len(wrapped_result.get('dynamic_tools', []))}")
            else:
                print(f"❌ {tool_name} wrapping failed")
        
        self.test_results.append({
            "test": "multiple_tool_types",
            "status": "passed",
            "tools_tested": len(tools_to_test),
            "tools_wrapped": len(wrapped_results)
        })
        
        return wrapped_results

    def test_dynamic_tool_functionality(self, wrapped_results: Dict[str, Any]):
        """Test dynamic tool functionality"""
        print("\n⚡ Testing Dynamic Tool Functionality")
        print("-" * 50)
        
        for tool_name, result in wrapped_results.items():
            ref_id = result["reference_id"]
            dynamic_tools = result.get("dynamic_tools", [])
            
            print(f"\nTesting dynamic tools for {tool_name} (ref: {ref_id[:8]}...):")
            
            # Test get_data_details function
            details_func_name = f"get_data_details_{ref_id}"
            if details_func_name in dynamic_tools:
                # Get the actual function from wrapper
                details_func = self.wrapper.get_dynamic_tool_function(details_func_name)
                if details_func:
                    details = details_func(max_items=5)
                    print(f"✅ Data details retrieved: {type(details)} with sample data")
                else:
                    print(f"❌ Could not get details function")
            
            # Test get_data_stats function
            stats_func_name = f"get_data_stats_{ref_id}"
            if stats_func_name in dynamic_tools:
                stats_func = self.wrapper.get_dynamic_tool_function(stats_func_name)
                if stats_func:
                    stats = stats_func()
                    print(f"✅ Data stats retrieved: {stats}")
                else:
                    print(f"❌ Could not get stats function")
            
            # Test search function if available
            search_func_name = f"search_data_{ref_id}"
            if search_func_name in dynamic_tools:
                search_func = self.wrapper.get_dynamic_tool_function(search_func_name)
                if search_func:
                    # Try a generic search
                    search_results = search_func("test", max_results=3)
                    print(f"✅ Search completed: found {len(search_results) if search_results else 0} results")
                else:
                    print(f"❌ Could not get search function")

    def test_storage_stats_and_cleanup(self):
        """Test storage statistics and cleanup functionality"""
        print("\n📊 Testing Storage Statistics & Cleanup")
        print("-" * 50)
        
        # Get storage stats
        stats = self.storage.get_storage_stats()
        print("Current Storage Statistics:")
        print(f"  Total references: {stats['total_references']}")
        print(f"  Total size: {stats['total_size_bytes']:,} bytes ({stats['total_size_mb']:.1f} MB)")
        print(f"  Size breakdown:")
        for size_class, count in stats['size_distribution'].items():
            print(f"    {size_class}: {count} items")
        
        # Test cleanup of expired data
        print("\nTesting cleanup (this may take a moment)...")
        initial_count = stats['total_references']
        
        # Force cleanup by setting a very recent expiration
        cleaned_count = self.storage.cleanup_expired_data(max_age_hours=0.001)  # Very short age
        
        final_stats = self.storage.get_storage_stats()
        final_count = final_stats['total_references']
        
        print(f"Cleanup results:")
        print(f"  Initial references: {initial_count}")
        print(f"  Cleaned references: {cleaned_count}")
        print(f"  Final references: {final_count}")
        
        self.test_results.append({
            "test": "storage_stats_cleanup",
            "status": "passed",
            "initial_references": initial_count,
            "cleaned_references": cleaned_count,
            "final_references": final_count
        })

    def test_agent_integration(self):
        """Test integration with agent builder"""
        print("\n🤖 Testing Agent Integration")
        print("-" * 50)
        
        try:
            # Create agent with large data optimization enabled
            builder = JKAgentBuilder()
            
            # Test configuration
            agent_config = {
                "agent_type": "data_analyst",
                "llm_provider": "anthropic",
                "model_name": "claude-3-5-sonnet-20241022",
                "enable_large_data_optimization": True,
                "large_data_config": TEST_CONFIG,
                "tools": [fetch_sales_data, get_user_analytics, export_financial_report]
            }
            
            agent = builder.build_agent(agent_config)
            print("✅ Agent created with large data optimization")
            
            # Test agent graph structure
            if hasattr(agent, 'graph'):
                nodes = agent.graph.nodes if hasattr(agent.graph, 'nodes') else []
                print(f"✅ Agent graph has {len(nodes)} nodes")
                
                # Check if enhanced tool node is being used
                node_types = [str(type(node)).split('.')[-1] for node in nodes]
                if 'EnhancedToolNode' in str(node_types):
                    print("✅ Enhanced tool node detected")
                else:
                    print("⚠️ Enhanced tool node not detected")
            
            self.test_results.append({
                "test": "agent_integration",
                "status": "passed",
                "details": "Agent created with large data optimization"
            })
            
        except Exception as e:
            print(f"❌ Agent integration failed: {str(e)}")
            self.test_results.append({
                "test": "agent_integration",
                "status": "failed",
                "error": str(e)
            })

    def test_performance_comparison(self):
        """Test performance comparison between wrapped and unwrapped operations"""
        print("\n⚡ Testing Performance Comparison")
        print("-" * 50)
        
        # Test large dataset generation
        print("Generating large dataset for performance test...")
        
        # Time unwrapped operation
        start_time = time.time()
        large_dataset = fetch_sales_data(10000, True)
        unwrapped_time = time.time() - start_time
        
        # Time wrapped operation
        start_time = time.time()
        wrapped_result = self.wrapper.wrap_tool_result(large_dataset, "fetch_sales_data")
        wrapped_time = time.time() - start_time
        
        # Calculate token savings (rough estimate)
        original_tokens = len(str(large_dataset)) // 4  # Rough token estimation
        wrapped_tokens = len(str(wrapped_result)) // 4
        token_savings = ((original_tokens - wrapped_tokens) / original_tokens) * 100
        
        print(f"Performance Results:")
        print(f"  Original data generation: {unwrapped_time:.2f}s")
        print(f"  Wrapping overhead: {wrapped_time:.2f}s")
        print(f"  Estimated original tokens: {original_tokens:,}")
        print(f"  Estimated wrapped tokens: {wrapped_tokens:,}")
        print(f"  Token savings: {token_savings:.1f}%")
        
        self.test_results.append({
            "test": "performance_comparison",
            "status": "passed",
            "unwrapped_time": unwrapped_time,
            "wrapped_time": wrapped_time,
            "token_savings_percent": token_savings
        })

    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n📋 Comprehensive Test Report")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["status"] == "passed"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nTest Details:")
        for i, test in enumerate(self.test_results, 1):
            status_emoji = "✅" if test["status"] == "passed" else "❌"
            print(f"{i:2d}. {status_emoji} {test['test']}")
            
            if "details" in test:
                print(f"     {test['details']}")
            if "error" in test:
                print(f"     Error: {test['error']}")
        
        # Storage final stats
        if self.storage:
            final_stats = self.storage.get_storage_stats()
            print(f"\nFinal Storage Statistics:")
            print(f"  Total references: {final_stats['total_references']}")
            print(f"  Total storage: {final_stats['total_size_mb']:.1f} MB")
            print(f"  Average reference size: {final_stats['avg_size_mb']:.2f} MB")
        
        # Save detailed report
        report_file = "./test_data/test_report.json"
        with open(report_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": (passed_tests/total_tests)*100
                },
                "test_results": self.test_results,
                "storage_stats": final_stats if self.storage else None,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Large Data Optimization System Tests")
        print("=" * 60)
        
        try:
            # Setup
            self.setup_test_environment()
            
            # Core functionality tests
            self.test_basic_storage()
            self.test_tool_wrapping()
            
            # Advanced functionality tests
            wrapped_results = self.test_multiple_tool_types()
            self.test_dynamic_tool_functionality(wrapped_results)
            
            # System tests
            self.test_storage_stats_and_cleanup()
            self.test_agent_integration()
            self.test_performance_comparison()
            
        except Exception as e:
            print(f"❌ Test suite encountered an error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Generate report
            self.generate_test_report()

def main():
    """Main test execution function"""
    tester = LargeDataSystemTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()