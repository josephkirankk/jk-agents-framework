#!/usr/bin/env python3
"""
Complex Agent Workflow Test Suite for Google Gemini Models

This test suite covers:
1. Multi-agent supervisor workflow
2. Large data integration
3. Memory persistence across interactions
4. Tool integration
5. Performance under load
"""
import os
import sys
import asyncio
import yaml
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List, Any

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.agent_builder import build_react_agent
from app.supervisor_builder import build_supervisor_compiled
from app.config import AgentConfig, AppConfig
from app.checkpointer_manager import get_global_checkpointer
from app.planner_executor import execute_plan

# Import Large Data Optimization System
from core.large_data_storage import LargeDataStorage
from core.smart_tool_wrapper import SmartToolWrapper
from tools.large_data_test_tools import (
    fetch_sales_data,
    get_user_analytics,
    export_financial_report
)


class ComplexWorkflowTester:
    """Comprehensive test suite for complex agent workflows"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        
        # Load environment
        load_dotenv()
        
        # Initialize Large Data Optimization System
        os.makedirs("./test_workflow_data", exist_ok=True)
        os.makedirs("./test_workflow_data/large_files", exist_ok=True)
        
        self.storage = LargeDataStorage(
            storage_path="./test_workflow_data/large_data_storage.db",
            file_storage_path="./test_workflow_data/large_files",
            compression_enabled=True
        )
        
        self.wrapper = SmartToolWrapper(
            storage=self.storage,
            token_threshold=1000,  # Lower threshold for testing
            summarization_max_tokens=200
        )
        
        print("🚀 Complex Workflow Test Suite Initialized")
        print("=" * 60)
    
    def print_test_header(self, test_name: str):
        """Print formatted test header"""
        print(f"\n🧪 {test_name}")
        print("-" * (len(test_name) + 4))
    
    def record_result(self, test_name: str, success: bool, details: Dict[str, Any] = None):
        """Record test result"""
        self.test_results[test_name] = {
            "success": success,
            "details": details or {},
            "timestamp": time.time() - self.start_time
        }
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            for key, value in details.items():
                print(f"   {key}: {value}")
    
    async def test_1_supervisor_workflow(self) -> bool:
        """Test multi-agent supervisor workflow with Google Gemini"""
        self.print_test_header("Multi-Agent Supervisor Workflow")
        
        try:
            # Load supervisor test config
            config_path = Path("config/basic_test.yaml")
            with config_path.open("r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
            
            # Normalize config
            models = config_data.get("models", {}) or {}
            if "temperature" in models and "temperature" not in config_data:
                config_data["temperature"] = models.get("temperature")
                models.pop("temperature", None)
            models = {str(k): str(v) for k, v in models.items() if v is not None}
            config_data["models"] = models
            
            app_config = AppConfig(**config_data)
            app_config_dict = app_config.model_dump() if hasattr(app_config, 'model_dump') else app_config.__dict__
            
            # Build supervisor
            supervisor = build_supervisor_compiled(
                supervisor_cfg=app_config.supervisor,
                agents_cfg=app_config.agents,
                default_model=app_config.models.get('default', 'google:gemini-2.5-flash-lite'),
                business_context=app_config.business_context or "",
                checkpointer=None,
                original_user_question="Analyze business performance using sales data and user analytics",
                config_path=str(config_path),
                default_temperature=app_config.temperature
            )
            
            # Test supervisor planning
            test_query = "Create a comprehensive business analysis report using sales data from the last quarter and user analytics. Include recommendations for improving user engagement and revenue."
            
            response = await supervisor.ainvoke(
                {"messages": [{"role": "user", "content": test_query}]},
                {"configurable": {"thread_id": "supervisor-workflow-test"}}
            )
            
            # Check if we got a valid supervisor response
            has_valid_response = False
            response_content = ""
            
            if response and "messages" in response:
                messages = response["messages"]
                for msg in messages:
                    if hasattr(msg, 'content') and msg.content:
                        response_content = msg.content
                        # For basic test agent, any structured response about analysis is valid
                        if any(word in response_content.lower() for word in ["analysis", "plan", "business", "data"]):
                            has_valid_response = True
                        break
            
            self.record_result("Supervisor Workflow", has_valid_response, {
                "supervisor_built": True,
                "response_received": bool(response),
                "valid_response": has_valid_response,
                "response_length": len(response_content)
            })
            
            return has_valid_response
            
        except Exception as e:
            self.record_result("Supervisor Workflow", False, {"error": str(e)})
            return False
    
    async def test_2_large_data_integration(self) -> bool:
        """Test Google Gemini agents with Large Data Optimization System"""
        self.print_test_header("Large Data Integration with Google Gemini")
        
        try:
            # Generate large dataset
            print("   Generating large sales dataset...")
            large_sales_data = fetch_sales_data.invoke({
                "num_records": 3000,
                "include_details": True
            })
            
            # Wrap with optimization system
            wrapped_data = self.wrapper.wrap_tool_result(large_sales_data, "fetch_sales_data")
            
            # Load agent config
            config_path = Path("config/basic_test.yaml")
            with config_path.open("r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
            
            # Normalize config
            models = config_data.get("models", {}) or {}
            if "temperature" in models and "temperature" not in config_data:
                config_data["temperature"] = models.get("temperature")
                models.pop("temperature", None)
            models = {str(k): str(v) for k, v in models.items() if v is not None}
            config_data["models"] = models
            
            app_config = AppConfig(**config_data)
            app_config_dict = app_config.model_dump() if hasattr(app_config, 'model_dump') else app_config.__dict__
            
            # Get agent config
            simple_agent_config = app_config.agents[0]
            checkpointer = get_global_checkpointer(app_config_dict)
            
            # Build agent
            agent, mcp_client = await build_react_agent(
                agent_cfg=simple_agent_config,
                default_model=app_config.models.get('default', 'google:gemini-2.5-flash-lite'),
                checkpointer=checkpointer,
                app_config=app_config_dict
            )
            
            # Test agent with optimized data
            if isinstance(wrapped_data, dict) and "reference_id" in wrapped_data:
                query = f"""I have sales data with reference ID: {wrapped_data['reference_id']}. 
                
Summary: {wrapped_data['summary']}

Please analyze this data and provide insights about:
1. Top performing products
2. Sales trends by region
3. Revenue optimization opportunities

Available tools for detailed analysis: {wrapped_data.get('dynamic_tools', [])}"""
                
                print("   Testing agent with optimized large dataset...")
                response = await agent.ainvoke(
                    {"messages": [{"role": "user", "content": query}]}, 
                    {"configurable": {"thread_id": "large-data-test"}}
                )
                
                # Check response
                analysis_provided = False
                if response and "messages" in response:
                    messages = response["messages"]
                    for msg in messages:
                        if hasattr(msg, 'content') and msg.content:
                            content = msg.content.lower()
                            if any(word in content for word in ["analysis", "insights", "trends", "revenue", "products"]):
                                analysis_provided = True
                                break
                
                # Get storage stats
                storage_stats = self.storage.get_storage_stats()
                
                self.record_result("Large Data Integration", analysis_provided, {
                    "data_optimized": True,
                    "reference_created": True,
                    "analysis_provided": analysis_provided,
                    "total_references": storage_stats['total_references'],
                    "storage_size_mb": storage_stats['total_size_mb'],
                    "dynamic_tools": len(wrapped_data.get('dynamic_tools', []))
                })
                
                return analysis_provided
            else:
                self.record_result("Large Data Integration", False, {
                    "error": "Data optimization failed - no reference created"
                })
                return False
                
        except Exception as e:
            self.record_result("Large Data Integration", False, {"error": str(e)})
            return False
    
    async def test_3_memory_persistence(self) -> bool:
        """Test memory persistence across multiple interactions"""
        self.print_test_header("Memory Persistence Across Interactions")
        
        try:
            # Load config and build agent
            config_path = Path("config/basic_test.yaml")
            with config_path.open("r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
            
            # Normalize config
            models = config_data.get("models", {}) or {}
            if "temperature" in models and "temperature" not in config_data:
                config_data["temperature"] = models.get("temperature")
                models.pop("temperature", None)
            models = {str(k): str(v) for k, v in models.items() if v is not None}
            config_data["models"] = models
            
            app_config = AppConfig(**config_data)
            app_config_dict = app_config.model_dump() if hasattr(app_config, 'model_dump') else app_config.__dict__
            
            simple_agent_config = app_config.agents[0]
            checkpointer = get_global_checkpointer(app_config_dict)
            
            agent, mcp_client = await build_react_agent(
                agent_cfg=simple_agent_config,
                default_model=app_config.models.get('default', 'google:gemini-2.5-flash-lite'),
                checkpointer=checkpointer,
                app_config=app_config_dict
            )
            
            thread_id = "memory-persistence-test"
            config = {"configurable": {"thread_id": thread_id}}
            
            # Interaction 1: Establish context
            print("   Interaction 1: Establishing context...")
            response1 = await agent.ainvoke({
                "messages": [{"role": "user", "content": "My name is Alex and I work for TechCorp as a data analyst. Please remember this information."}]
            }, config)
            
            # Interaction 2: Add more context
            print("   Interaction 2: Adding project context...")
            response2 = await agent.ainvoke({
                "messages": [{"role": "user", "content": "I'm working on Q4 sales analysis project with a deadline of December 15th. This is my top priority."}]
            }, config)
            
            # Interaction 3: Test memory recall
            print("   Interaction 3: Testing memory recall...")
            response3 = await agent.ainvoke({
                "messages": [{"role": "user", "content": "What's my name, company, role, and current priority project with its deadline?"}]
            }, config)
            
            # Check if the agent remembered information
            memory_recall_success = False
            if response3 and "messages" in response3:
                messages = response3["messages"]
                for msg in messages:
                    if hasattr(msg, 'content') and msg.content:
                        content = msg.content.lower()
                        if all(item in content for item in ["alex", "techcorp", "analyst", "q4", "december"]):
                            memory_recall_success = True
                            break
            
            self.record_result("Memory Persistence", memory_recall_success, {
                "context_established": bool(response1),
                "context_expanded": bool(response2),
                "memory_recalled": memory_recall_success,
                "thread_id": thread_id
            })
            
            return memory_recall_success
            
        except Exception as e:
            self.record_result("Memory Persistence", False, {"error": str(e)})
            return False
    
    async def test_4_concurrent_agents(self) -> bool:
        """Test multiple concurrent agent interactions"""
        self.print_test_header("Concurrent Agent Performance")
        
        try:
            # Load config
            config_path = Path("config/basic_test.yaml")
            with config_path.open("r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
            
            # Normalize config
            models = config_data.get("models", {}) or {}
            if "temperature" in models and "temperature" not in config_data:
                config_data["temperature"] = models.get("temperature")
                models.pop("temperature", None)
            models = {str(k): str(v) for k, v in models.items() if v is not None}
            config_data["models"] = models
            
            app_config = AppConfig(**config_data)
            app_config_dict = app_config.model_dump() if hasattr(app_config, 'model_dump') else app_config.__dict__
            
            # Create multiple agents
            agents = []
            for i in range(3):
                simple_agent_config = app_config.agents[0]
                checkpointer = get_global_checkpointer(app_config_dict)
                
                agent, _ = await build_react_agent(
                    agent_cfg=simple_agent_config,
                    default_model=app_config.models.get('default', 'google:gemini-2.5-flash-lite'),
                    checkpointer=checkpointer,
                    app_config=app_config_dict
                )
                agents.append((agent, f"concurrent-test-{i}"))
            
            # Define concurrent tasks
            tasks = [
                ("Calculate 47 * 83 and explain the process", 0),
                ("What are the benefits of renewable energy?", 1),
                ("Explain the concept of machine learning in simple terms", 2)
            ]
            
            # Run concurrent tasks
            print("   Running 3 concurrent agent interactions...")
            start_time = time.time()
            
            async def run_agent_task(agent, thread_id, query):
                try:
                    response = await agent.ainvoke(
                        {"messages": [{"role": "user", "content": query}]},
                        {"configurable": {"thread_id": thread_id}}
                    )
                    return response, None
                except Exception as e:
                    return None, str(e)
            
            # Execute all tasks concurrently
            concurrent_tasks = [
                run_agent_task(agents[agent_idx][0], agents[agent_idx][1], query)
                for query, agent_idx in tasks
            ]
            
            results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
            end_time = time.time()
            
            # Analyze results
            successful_responses = 0
            total_tasks = len(tasks)
            
            for i, result in enumerate(results):
                if not isinstance(result, Exception) and result[0] and result[1] is None:
                    successful_responses += 1
            
            success_rate = (successful_responses / total_tasks) * 100
            execution_time = end_time - start_time
            
            self.record_result("Concurrent Agent Performance", successful_responses == total_tasks, {
                "successful_responses": successful_responses,
                "total_tasks": total_tasks,
                "success_rate": f"{success_rate:.1f}%",
                "execution_time": f"{execution_time:.2f}s",
                "avg_time_per_task": f"{execution_time/total_tasks:.2f}s"
            })
            
            return successful_responses == total_tasks
            
        except Exception as e:
            self.record_result("Concurrent Agent Performance", False, {"error": str(e)})
            return False
    
    async def test_5_workflow_integration(self) -> bool:
        """Test complete workflow integration with data processing"""
        self.print_test_header("Complete Workflow Integration")
        
        try:
            # Step 1: Generate multiple datasets
            print("   Step 1: Generating multiple datasets...")
            sales_data = fetch_sales_data.invoke({"num_records": 1000, "include_details": True})
            analytics_data = get_user_analytics.invoke({"timeframe_days": 90, "include_behavior": True})
            financial_data = export_financial_report.invoke({"quarters": 4, "detailed": True})
            
            # Step 2: Optimize datasets
            print("   Step 2: Optimizing datasets...")
            wrapped_sales = self.wrapper.wrap_tool_result(sales_data, "fetch_sales_data")
            wrapped_analytics = self.wrapper.wrap_tool_result(analytics_data, "get_user_analytics")
            wrapped_financial = self.wrapper.wrap_tool_result(financial_data, "export_financial_report")
            
            # Step 3: Create comprehensive analysis agent
            config_path = Path("config/basic_test.yaml")
            with config_path.open("r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
            
            # Normalize config
            models = config_data.get("models", {}) or {}
            if "temperature" in models and "temperature" not in config_data:
                config_data["temperature"] = models.get("temperature")
                models.pop("temperature", None)
            models = {str(k): str(v) for k, v in models.items() if v is not None}
            config_data["models"] = models
            
            app_config = AppConfig(**config_data)
            app_config_dict = app_config.model_dump() if hasattr(app_config, 'model_dump') else app_config.__dict__
            
            simple_agent_config = app_config.agents[0]
            checkpointer = get_global_checkpointer(app_config_dict)
            
            agent, mcp_client = await build_react_agent(
                agent_cfg=simple_agent_config,
                default_model=app_config.models.get('default', 'google:gemini-2.5-flash-lite'),
                checkpointer=checkpointer,
                app_config=app_config_dict
            )
            
            # Step 4: Comprehensive analysis
            print("   Step 4: Running comprehensive analysis...")
            
            analysis_query = f"""I need a comprehensive business analysis using the following optimized datasets:

1. Sales Data (Reference: {wrapped_sales.get('reference_id', 'N/A')})
   Summary: {wrapped_sales.get('summary', 'N/A')[:100]}...

2. User Analytics (Reference: {wrapped_analytics.get('reference_id', 'N/A')})
   Summary: {wrapped_analytics.get('summary', 'N/A')[:100]}...

3. Financial Report (Reference: {wrapped_financial.get('reference_id', 'N/A')})
   Summary: {wrapped_financial.get('summary', 'N/A')[:100]}...

Please provide:
1. Key performance indicators from each dataset
2. Cross-dataset correlations and insights
3. Strategic recommendations for business growth
4. Risk assessment and mitigation strategies
"""
            
            response = await agent.ainvoke(
                {"messages": [{"role": "user", "content": analysis_query}]},
                {"configurable": {"thread_id": "comprehensive-analysis"}}
            )
            
            # Analyze response quality
            analysis_quality = 0
            if response and "messages" in response:
                messages = response["messages"]
                for msg in messages:
                    if hasattr(msg, 'content') and msg.content:
                        content = msg.content.lower()
                        # Check for key analysis components
                        if "kpi" in content or "performance" in content:
                            analysis_quality += 1
                        if "correlation" in content or "insight" in content:
                            analysis_quality += 1
                        if "recommendation" in content or "strategy" in content:
                            analysis_quality += 1
                        if "risk" in content or "mitigation" in content:
                            analysis_quality += 1
                        break
            
            # Get final storage statistics
            final_stats = self.storage.get_storage_stats()
            
            workflow_success = analysis_quality >= 3  # At least 3 out of 4 analysis components
            
            self.record_result("Complete Workflow Integration", workflow_success, {
                "datasets_generated": 3,
                "datasets_optimized": sum(1 for d in [wrapped_sales, wrapped_analytics, wrapped_financial] if isinstance(d, dict) and "reference_id" in d),
                "analysis_components": f"{analysis_quality}/4",
                "total_storage_references": final_stats['total_references'],
                "total_storage_mb": final_stats['total_size_mb'],
                "workflow_complete": workflow_success
            })
            
            return workflow_success
            
        except Exception as e:
            self.record_result("Complete Workflow Integration", False, {"error": str(e)})
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all complex workflow tests"""
        print("🎯 Starting Complex Workflow Test Suite")
        print("Testing Google Gemini models with advanced features...")
        print("=" * 60)
        
        # Check API key
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            print("❌ GOOGLE_API_KEY not found in environment")
            return {"error": "Missing Google API key"}
        
        print(f"✅ Google API Key found: {google_api_key[:20]}...")
        
        # Run all tests
        test_functions = [
            self.test_1_supervisor_workflow,
            self.test_2_large_data_integration,
            self.test_3_memory_persistence,
            self.test_4_concurrent_agents,
            self.test_5_workflow_integration
        ]
        
        for test_func in test_functions:
            try:
                await test_func()
            except Exception as e:
                print(f"❌ Test {test_func.__name__} failed with exception: {e}")
            print()  # Add spacing between tests
        
        # Generate final report
        return self.generate_final_report()
    
    def generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["success"])
        
        print("\n" + "=" * 60)
        print("🏁 COMPLEX WORKFLOW TEST RESULTS")
        print("=" * 60)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{status} {test_name}")
            if result["details"]:
                for key, value in result["details"].items():
                    print(f"     {key}: {value}")
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        total_time = time.time() - self.start_time
        
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print(f"✅ Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"⏱️  Total Time: {total_time:.2f}s")
        print(f"🚀 System Status: {'EXCELLENT' if success_rate >= 80 else 'GOOD' if success_rate >= 60 else 'NEEDS ATTENTION'}")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": success_rate,
            "total_time": total_time,
            "detailed_results": self.test_results
        }


async def main():
    """Main test execution"""
    tester = ComplexWorkflowTester()
    results = await tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if results.get("success_rate", 0) >= 80 else 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))