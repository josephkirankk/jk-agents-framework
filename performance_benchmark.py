"""
Performance Benchmark - Large Data Optimization Impact

This benchmark demonstrates the real-world performance improvements
achieved by the large data optimization system.
"""

import sys
import time
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from core.large_data_storage import LargeDataStorage
from core.smart_tool_wrapper import SmartToolWrapper
from tools.large_data_test_tools import (
    fetch_sales_data,
    get_user_analytics,
    export_financial_report,
    search_documents,
    fetch_research_data
)

def estimate_llm_cost(tokens, model="claude-3-5-sonnet"):
    """Estimate LLM API cost based on token count"""
    # Rough pricing estimates (per 1M tokens)
    pricing = {
        "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
        "gpt-4": {"input": 30.00, "output": 60.00},
        "gpt-3.5": {"input": 0.50, "output": 1.50}
    }
    
    rate = pricing.get(model, pricing["claude-3-5-sonnet"])
    # Assume 50/50 input/output split for estimation
    cost = (tokens / 1_000_000) * ((rate["input"] + rate["output"]) / 2)
    return cost

def benchmark_tool(tool_name, tool_func, wrapper, iterations=1):
    """Benchmark a single tool"""
    print(f"\n🔧 Benchmarking {tool_name}...")
    
    results = {
        "tool_name": tool_name,
        "iterations": iterations,
        "total_records": 0,
        "avg_execution_time": 0,
        "avg_wrap_time": 0,
        "original_tokens": 0,
        "wrapped_tokens": 0,
        "token_savings": 0,
        "cost_savings_usd": 0,
        "size_classification": "unknown"
    }
    
    total_execution_time = 0
    total_wrap_time = 0
    
    for i in range(iterations):
        # Time tool execution
        start_time = time.time()
        raw_data = tool_func()
        execution_time = time.time() - start_time
        total_execution_time += execution_time
        
        # Time wrapping
        wrap_start = time.time()
        wrapped_result = wrapper.wrap_tool_result(raw_data, tool_name)
        wrap_time = time.time() - wrap_start
        total_wrap_time += wrap_time
        
        # Calculate metrics
        if isinstance(raw_data, list):
            results["total_records"] = len(raw_data)
        elif isinstance(raw_data, dict) and "records" in raw_data:
            results["total_records"] = len(raw_data["records"])
        elif isinstance(raw_data, dict):
            results["total_records"] = len(raw_data)
        
        original_tokens = wrapper._estimate_tokens(raw_data)
        
        if isinstance(wrapped_result, dict) and "reference_id" in wrapped_result:
            wrapped_tokens = wrapper._estimate_tokens(wrapped_result)
            results["size_classification"] = wrapper.storage.get_metadata(wrapped_result["reference_id"])["size_classification"]
        else:
            wrapped_tokens = original_tokens
        
        results["original_tokens"] = original_tokens
        results["wrapped_tokens"] = wrapped_tokens
    
    # Calculate averages
    results["avg_execution_time"] = total_execution_time / iterations
    results["avg_wrap_time"] = total_wrap_time / iterations
    results["token_savings"] = ((results["original_tokens"] - results["wrapped_tokens"]) / results["original_tokens"]) * 100
    
    # Cost calculations
    original_cost = estimate_llm_cost(results["original_tokens"])
    wrapped_cost = estimate_llm_cost(results["wrapped_tokens"])
    results["cost_savings_usd"] = original_cost - wrapped_cost
    
    return results

def main():
    """Run comprehensive performance benchmark"""
    print("⚡ Large Data Optimization - Performance Benchmark")
    print("=" * 70)
    
    # Setup
    storage = LargeDataStorage(
        storage_path="./demo_data/large_data_storage.db",
        compression_enabled=True
    )
    wrapper = SmartToolWrapper(storage=storage, token_threshold=1000)
    
    # Define test cases
    test_cases = [
        ("Small Sales Data", lambda: fetch_sales_data.invoke({"num_records": 100, "include_details": False})),
        ("Medium Sales Data", lambda: fetch_sales_data.invoke({"num_records": 2000, "include_details": True})),
        ("Large Sales Data", lambda: fetch_sales_data.invoke({"num_records": 10000, "include_details": True})),
        ("User Analytics", lambda: get_user_analytics.invoke({"timeframe_days": 365, "include_behavior": True})),
        ("Financial Report", lambda: export_financial_report.invoke({"quarters": 8, "detailed": True})),
        ("Document Search", lambda: search_documents.invoke({"query": "machine learning", "max_results": 2000})),
        ("Research Data", lambda: fetch_research_data.invoke({"topic": "artificial intelligence", "num_studies": 3000}))
    ]
    
    benchmark_results = []
    
    print("\n📊 Running Benchmarks...")
    print("-" * 70)
    
    for test_name, test_func in test_cases:
        try:
            result = benchmark_tool(test_name, test_func, wrapper)
            benchmark_results.append(result)
            
            # Print immediate results
            print(f"✅ {test_name}:")
            print(f"   📦 Records: {result['total_records']:,}")
            print(f"   ⏱️  Execution: {result['avg_execution_time']:.2f}s")
            print(f"   🔧 Wrapping: {result['avg_wrap_time']:.3f}s")
            print(f"   🎯 Tokens: {result['original_tokens']:,} → {result['wrapped_tokens']:,} ({result['token_savings']:.1f}% saved)")
            print(f"   💰 Cost: ${estimate_llm_cost(result['original_tokens']):.3f} → ${estimate_llm_cost(result['wrapped_tokens']):.3f} (${result['cost_savings_usd']:.3f} saved)")
            print(f"   📊 Storage: {result['size_classification']}")
            
        except Exception as e:
            print(f"❌ {test_name} failed: {str(e)}")
    
    # Summary Analysis
    print("\n" + "=" * 70)
    print("📈 BENCHMARK SUMMARY")
    print("=" * 70)
    
    if benchmark_results:
        total_original_tokens = sum(r["original_tokens"] for r in benchmark_results)
        total_wrapped_tokens = sum(r["wrapped_tokens"] for r in benchmark_results)
        total_records = sum(r["total_records"] for r in benchmark_results)
        total_cost_savings = sum(r["cost_savings_usd"] for r in benchmark_results)
        
        overall_token_savings = ((total_original_tokens - total_wrapped_tokens) / total_original_tokens) * 100
        
        print(f"\n🎯 OVERALL PERFORMANCE:")
        print(f"   📊 Total Records Processed: {total_records:,}")
        print(f"   🎯 Total Token Reduction: {total_original_tokens:,} → {total_wrapped_tokens:,}")
        print(f"   📉 Overall Token Savings: {overall_token_savings:.1f}%")
        print(f"   💰 Total Cost Savings: ${total_cost_savings:.2f}")
        
        print(f"\n⚡ EFFICIENCY GAINS:")
        avg_execution_time = sum(r["avg_execution_time"] for r in benchmark_results) / len(benchmark_results)
        avg_wrap_time = sum(r["avg_wrap_time"] for r in benchmark_results) / len(benchmark_results)
        print(f"   ⏱️  Average Execution Time: {avg_execution_time:.2f}s")
        print(f"   🔧 Average Wrapping Overhead: {avg_wrap_time:.3f}s")
        print(f"   📊 Wrapping Overhead: {(avg_wrap_time/avg_execution_time)*100:.1f}% of execution time")
        
        # Storage analysis
        storage_stats = storage.get_storage_stats()
        print(f"\n💾 STORAGE EFFICIENCY:")
        print(f"   📦 Total References: {storage_stats['total_references']}")
        print(f"   📊 Total Storage: {storage_stats['total_size_mb']:.2f}MB")
        print(f"   🗂️  Size Distribution: {storage_stats['size_distribution']}")
        
        # ROI Analysis
        print(f"\n💵 RETURN ON INVESTMENT:")
        # Assume processing 1000 queries per month
        monthly_queries = 1000
        monthly_savings = (total_cost_savings / len(test_cases)) * monthly_queries
        yearly_savings = monthly_savings * 12
        
        print(f"   📈 Monthly Savings (1K queries): ${monthly_savings:.2f}")
        print(f"   📊 Yearly Savings (12K queries): ${yearly_savings:.2f}")
        print(f"   🎯 Token Efficiency Ratio: {overall_token_savings:.1f}% reduction")
        
        # Performance Categories
        print(f"\n🏆 PERFORMANCE CATEGORIES:")
        for result in benchmark_results:
            if result["token_savings"] > 95:
                category = "🚀 EXCELLENT"
            elif result["token_savings"] > 80:
                category = "✅ VERY GOOD"
            elif result["token_savings"] > 50:
                category = "📈 GOOD"
            else:
                category = "📊 BASELINE"
            
            print(f"   {result['tool_name']:.<25} {category} ({result['token_savings']:.1f}% savings)")
    
    print(f"\n🎉 BENCHMARK COMPLETE!")
    print(f"   📁 Storage location: ./demo_data/")
    print(f"   🔍 Database size: {storage_stats['total_size_mb']:.2f}MB")
    
    # Cleanup recommendation
    print(f"\n🧹 MAINTENANCE RECOMMENDATIONS:")
    print(f"   • Run cleanup every 24 hours for optimal performance")
    print(f"   • Monitor storage growth - current: {storage_stats['total_size_mb']:.2f}MB")
    print(f"   • Consider Redis caching for frequently accessed references")
    
    if storage_stats['total_size_mb'] > 100:
        print(f"   ⚠️  Storage > 100MB - consider cleanup or archiving")

if __name__ == "__main__":
    main()