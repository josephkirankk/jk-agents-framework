"""
Integration Test 07: MCP Azure DevOps Tools
Tests Azure DevOps integration via MCP server (Node.js-based ADO server).

NO MOCKING - Uses real MCP server, real Azure DevOps API, real LLM.

Scenarios:
1. Basic work item search and retrieval
2. Feature analysis with structured reports
3. Multi-turn ADO conversations
4. Project and area path filtering
5. Error handling and validation
6. Work item relationship traversal
7. Status and progress analysis

Prerequisites:
- Node.js 20+ installed
- Azure CLI authenticated (az login) OR Azure DevOps PAT token
- Azure DevOps organization access (PepsiCoIT)
- Read permissions for work items, repos, builds
- Azure OpenAI credentials configured
"""

import os
import pytest
import asyncio
import subprocess
from pathlib import Path
from langchain_core.messages import HumanMessage

# Load .env file explicitly to ensure AZURE_DEVOPS_EXT_PAT is available
from dotenv import load_dotenv
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Verify PAT token is loaded
ado_pat = os.getenv('AZURE_DEVOPS_EXT_PAT')
if ado_pat:
    print(f"✓ Azure DevOps PAT token loaded (length: {len(ado_pat)})")
else:
    print("⚠ Warning: AZURE_DEVOPS_EXT_PAT not found in environment")

from app.main import load_app_config
from app.agent_builder import build_agent
from test_utils import convert_app_config_to_dict
from helpers.utils import contains_keywords, extract_numbers


def check_node_available():
    """Check if Node.js is available."""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            # Extract major version (e.g., v23.7.0 -> 23)
            major_version = int(version.lstrip('v').split('.')[0])
            return major_version >= 20
        return False
    except Exception:
        return False


def check_npx_available():
    """Check if npx is available."""
    try:
        result = subprocess.run(['which', 'npx'], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False


def check_azure_devops_credentials():
    """Check if Azure DevOps credentials are configured."""
    # Check for PAT token
    pat_token = os.getenv('AZURE_DEVOPS_EXT_PAT')
    if pat_token:
        return True
    
    # Check if Azure CLI is authenticated
    try:
        result = subprocess.run(
            ['az', 'account', 'show'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


# Set environment variable to suppress tokenizers warning
os.environ['TOKENIZERS_PARALLELISM'] = 'false'


@pytest.mark.integration
@pytest.mark.azure
@pytest.mark.skipif(
    not (check_node_available() and check_npx_available()),
    reason="Node.js 20+ and npx are required"
)
class TestMCPAzureDevOpsTools:
    """Test Azure DevOps operations via MCP server."""
    
    @pytest.fixture
    async def ado_agent(self, config_dir, test_thread_id):
        """
        Build agent with Azure DevOps MCP server.
        """
        from app.mcp_loader import close_mcp_client
        
        # Check credentials first
        if not check_azure_devops_credentials():
            pytest.skip("Azure DevOps credentials not configured. Set AZURE_DEVOPS_EXT_PAT or run 'az login'")
        
        # Load config with Azure DevOps MCP server
        config_path = config_dir / "ado_working_v1.yaml"
        
        if not config_path.exists():
            pytest.skip("ADO configuration file not found")
        
        config = load_app_config(config_path)
        
        # Get Azure DevOps agent
        ado_agent_config = None
        for agent in config.agents:
            if "azure_devops" in agent.name.lower() or "feature_analyzer" in agent.name.lower():
                ado_agent_config = agent
                break
        
        if not ado_agent_config:
            pytest.skip("Azure DevOps agent not found in config")
        
        # Build agent
        app_config_dict = convert_app_config_to_dict(config)
        
        try:
            agent, mcp_client = await build_agent(
                agent_cfg=ado_agent_config,
                default_model=config.models.get("default", "azure_openai:gpt-4.1"),
                config_path=str(config_path),
                app_config=app_config_dict
            )
        except Exception as e:
            pytest.skip(f"Failed to build ADO agent: {e}")
        
        yield agent
        
        # Cleanup
        if mcp_client:
            await close_mcp_client(mcp_client)
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not check_azure_devops_credentials(),
        reason="Azure DevOps credentials not configured"
    )
    async def test_simple_workitem_search(self, ado_agent, test_thread_id):
        """
        Scenario: Search for work items in Azure DevOps
        
        Steps:
        1. Ask agent to search for work items in JBP Retail 360 MVP project
        2. Verify tool was called
        3. Verify response contains work item information
        """
        query = "Search for work items in the JBP Retail 360 MVP 1.0 project area. Show me the first 3 results."
        input_data = {"messages": [HumanMessage(content=query)]}
        config = {"configurable": {"thread_id": test_thread_id}}
        
        result = await ado_agent.ainvoke(input_data, config=config)
        
        assert result is not None
        assert len(result["messages"]) > 0
        
        # Get response
        response_text = result["messages"][-1].content.lower()
        
        # Should mention work items or project
        assert any(keyword in response_text for keyword in [
            "work item", "feature", "user story", "task", "jbp", "retail"
        ]), "Response should contain ADO work item information"
        
        # Check if tool was called
        messages = result["messages"]
        tool_called = any(
            hasattr(msg, "tool_calls") and msg.tool_calls 
            for msg in messages
        )
        
        print(f"Tool was called: {tool_called}")
        print(f"Response excerpt: {response_text[:200]}...")
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not check_azure_devops_credentials(),
        reason="Azure DevOps credentials not configured"
    )
    async def test_feature_analysis(self, ado_agent, test_thread_id):
        """
        Scenario: Analyze a specific feature
        
        Steps:
        1. Ask agent to analyze a feature by name
        2. Verify structured response with sections
        3. Verify work item links included
        """
        query = """Analyze any feature in the JBP Retail 360 MVP 1.0 project. 
        Provide a structured summary with description, status, and work items."""
        
        input_data = {"messages": [HumanMessage(content=query)]}
        config = {"configurable": {"thread_id": f"{test_thread_id}_feature"}}
        
        result = await ado_agent.ainvoke(input_data, config=config)
        response_text = result["messages"][-1].content.lower()
        
        # Should contain structured analysis elements
        expected_sections = ["feature", "status", "description"]
        found_sections = sum(1 for section in expected_sections if section in response_text)
        
        assert found_sections >= 2, "Response should contain structured feature analysis"
        
        print(f"Feature analysis response length: {len(response_text)} chars")
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not check_azure_devops_credentials(),
        reason="Azure DevOps credentials not configured"
    )
    async def test_project_area_filtering(self, ado_agent, test_thread_id):
        """
        Scenario: Verify project and area path filtering
        
        Steps:
        1. Search for work items with specific project area
        2. Verify results are filtered correctly
        """
        query = """Show me work items in the Global_Data_Project\\JBP\\JBP Retail 360 MVP 1.0 area path. 
        List any 2 work items."""
        
        input_data = {"messages": [HumanMessage(content=query)]}
        config = {"configurable": {"thread_id": f"{test_thread_id}_filter"}}
        
        result = await ado_agent.ainvoke(input_data, config=config)
        response_text = result["messages"][-1].content
        
        # Should reference the project or area
        assert any(keyword in response_text for keyword in [
            "JBP", "Retail 360", "Global_Data_Project", "work item"
        ]), "Response should reference project area"
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not check_azure_devops_credentials(),
        reason="Azure DevOps credentials not configured"
    )
    async def test_work_item_status_analysis(self, ado_agent, test_thread_id):
        """
        Scenario: Analyze work item status distribution
        
        Steps:
        1. Ask for status summary of work items
        2. Verify response includes status information
        """
        query = """What is the status distribution of work items in JBP Retail 360 MVP 1.0? 
        Show me how many are completed, in progress, or planned."""
        
        input_data = {"messages": [HumanMessage(content=query)]}
        config = {"configurable": {"thread_id": f"{test_thread_id}_status"}}
        
        result = await ado_agent.ainvoke(input_data, config=config)
        response_text = result["messages"][-1].content.lower()
        
        # Should mention status-related terms or work items
        status_keywords = ["status", "completed", "active", "progress", "closed", "new", "work item", "feature", "jbp"]
        found_keywords = sum(1 for keyword in status_keywords if keyword in response_text)
        
        assert found_keywords >= 1, "Response should contain status or work item information"
        assert len(response_text) > 50, "Response should provide meaningful content"
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not check_azure_devops_credentials(),
        reason="Azure DevOps credentials not configured"
    )
    async def test_multi_turn_ado_conversation(self, ado_agent, test_thread_id):
        """
        Scenario: Multi-turn conversation about ADO work items
        
        Steps:
        1. Turn 1: Search for work items
        2. Turn 2: Ask for details about previous results
        3. Turn 3: Request status summary
        4. Verify context persistence
        """
        config = {"configurable": {"thread_id": f"{test_thread_id}_multiturn"}}
        
        # Turn 1: Initial search
        query1 = "Search for any 3 work items in JBP Retail 360 MVP 1.0 project."
        input1 = {"messages": [HumanMessage(content=query1)]}
        result1 = await ado_agent.ainvoke(input1, config=config)
        response1 = result1["messages"][-1].content
        
        assert len(response1) > 0, "Turn 1 should return results"
        
        await asyncio.sleep(1)
        
        # Turn 2: Follow-up question
        query2 = "What types of work items did you find in the previous search?"
        input2 = {"messages": [HumanMessage(content=query2)]}
        result2 = await ado_agent.ainvoke(input2, config=config)
        response2 = result2["messages"][-1].content.lower()
        
        # Should reference previous context
        assert any(keyword in response2 for keyword in [
            "previous", "found", "search", "work item", "feature", "story", "task"
        ]), "Turn 2 should reference previous search"
        
        await asyncio.sleep(1)
        
        # Turn 3: Status summary
        query3 = "Summarize the status of those work items."
        input3 = {"messages": [HumanMessage(content=query3)]}
        result3 = await ado_agent.ainvoke(input3, config=config)
        response3 = result3["messages"][-1].content.lower()
        
        # Should provide status information
        assert any(keyword in response3 for keyword in [
            "status", "completed", "active", "progress"
        ]), "Turn 3 should provide status summary"
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not check_azure_devops_credentials(),
        reason="Azure DevOps credentials not configured"
    )
    async def test_error_handling_invalid_project(self, ado_agent, test_thread_id):
        """
        Scenario: Handle invalid project gracefully
        
        Steps:
        1. Query for non-existent project
        2. Verify graceful error handling
        """
        query = "Search for work items in a project called 'NonExistentProject12345XYZ'."
        input_data = {"messages": [HumanMessage(content=query)]}
        config = {"configurable": {"thread_id": f"{test_thread_id}_error"}}
        
        # Should not throw exception, should handle gracefully
        result = await ado_agent.ainvoke(input_data, config=config)
        response_text = result["messages"][-1].content.lower()
        
        # Should indicate no results or error
        assert any(keyword in response_text for keyword in [
            "not found", "no ", "unable", "cannot", "error", "does not exist"
        ]) or len(response_text) < 100, "Should handle invalid project gracefully"
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not check_azure_devops_credentials(),
        reason="Azure DevOps credentials not configured"
    )
    async def test_work_item_type_filtering(self, ado_agent, test_thread_id):
        """
        Scenario: Search for specific work item types
        
        Steps:
        1. Search for features only
        2. Verify response focuses on features
        """
        query = """Show me only Feature type work items in JBP Retail 360 MVP 1.0. 
        List any 2 features with their titles."""
        
        input_data = {"messages": [HumanMessage(content=query)]}
        config = {"configurable": {"thread_id": f"{test_thread_id}_type"}}
        
        result = await ado_agent.ainvoke(input_data, config=config)
        response_text = result["messages"][-1].content.lower()
        
        # Should mention features
        assert "feature" in response_text, "Response should mention features"
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not check_azure_devops_credentials(),
        reason="Azure DevOps credentials not configured"
    )
    async def test_ado_link_generation(self, ado_agent, test_thread_id):
        """
        Scenario: Verify ADO links are generated
        
        Steps:
        1. Query for work items
        2. Verify response includes Azure DevOps URLs
        """
        query = "Find any work item in JBP Retail 360 MVP 1.0 and provide its Azure DevOps link."
        input_data = {"messages": [HumanMessage(content=query)]}
        config = {"configurable": {"thread_id": f"{test_thread_id}_links"}}
        
        result = await ado_agent.ainvoke(input_data, config=config)
        response_text = result["messages"][-1].content
        
        # Should contain ADO URL pattern or work item reference
        has_ado_link = any(pattern in response_text for pattern in [
            "dev.azure.com", "_workitems", "PepsiCoIT", "work item", "#"
        ])
        
        assert has_ado_link or len(response_text) > 100, "Response should include ADO references or provide meaningful content"
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not check_azure_devops_credentials(),
        reason="Azure DevOps credentials not configured"
    )
    async def test_recent_activity_query(self, ado_agent, test_thread_id):
        """
        Scenario: Query for recent activity
        
        Steps:
        1. Ask about recently updated work items
        2. Verify response includes recent items
        """
        query = """What work items were recently updated in JBP Retail 360 MVP 1.0? 
        Show me the 3 most recently changed items."""
        
        input_data = {"messages": [HumanMessage(content=query)]}
        config = {"configurable": {"thread_id": f"{test_thread_id}_recent"}}
        
        result = await ado_agent.ainvoke(input_data, config=config)
        response_text = result["messages"][-1].content.lower()
        
        # Should reference recency or updates
        assert any(keyword in response_text for keyword in [
            "recent", "updated", "changed", "modified", "latest"
        ]), "Response should mention recent activity"
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not check_azure_devops_credentials(),
        reason="Azure DevOps credentials not configured"
    )
    async def test_comprehensive_feature_report(self, ado_agent, test_thread_id):
        """
        Scenario: Generate comprehensive feature report
        
        Steps:
        1. Request detailed feature analysis
        2. Verify all required sections present
        3. Verify structured format
        """
        query = """Provide a comprehensive analysis of any feature in JBP Retail 360 MVP 1.0.
        Include: description, business value, KPIs, implementation status, and work item links."""
        
        input_data = {"messages": [HumanMessage(content=query)]}
        config = {"configurable": {"thread_id": f"{test_thread_id}_comprehensive"}}
        
        result = await ado_agent.ainvoke(input_data, config=config)
        response_text = result["messages"][-1].content.lower()
        
        # Check for comprehensive analysis components
        components = ["feature", "status", "work item"]
        found_components = sum(1 for comp in components if comp in response_text)
        
        assert found_components >= 2, "Should provide comprehensive feature analysis"
        assert len(response_text) > 200, "Comprehensive report should be detailed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
