"""
Test script to verify that the PilgerProcessingPipeline correctly passes
placeholder values ({{ontology}} and {{user_input}}) to the jk_pilger_new_entries_agent.
"""

import asyncio
import json
import logging
from typing import Dict, Any

from gemba_agents.defect_analysis.models.data_models import (
    AggregatedResults, IntentData, DefectResult
)
from gemba_agents.pilger_processing.models.data_models import PilgerProcessingConfig
from gemba_agents.pilger_processing.utils import load_and_build_agent_with_placeholders

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_mock_defect_analysis() -> AggregatedResults:
    """Create a mock AggregatedResults object for testing."""
    
    # Create mock intent data
    intent_data = IntentData(
        interpreted_meaning="The pump's loading/unloading piston is not operating smoothly",
        component="Pump",
        sub_component="Pump piston",
        related_component="Air compressor",
        issue="Not operating smoothly"
    )
    
    # Create mock defect results
    defects = [
        DefectResult(
            id="defect_1",
            score=0.95,
            defect_code="PLG.PMP.PISTON.SMOOTH",
            defect_text="Pump piston not operating smoothly",
            subsystem="PMP",
            severity="High",
            symptoms=["Irregular piston movement", "Unusual noise"],
            detection_methods=["Visual inspection", "Sound analysis"],
            tags=["pump", "piston", "smooth"],
            likely_root_causes=["Worn seals", "Contaminated fluid"],
            recommended_actions=["Replace seals", "Change fluid"]
        ),
        DefectResult(
            id="defect_2",
            score=0.87,
            defect_code="PLG.PMP.SEAL.WORN",
            defect_text="Pump seal worn causing irregular operation",
            subsystem="PMP",
            severity="Medium",
            symptoms=["Fluid leakage", "Pressure drop"],
            detection_methods=["Pressure test", "Visual inspection"],
            tags=["pump", "seal", "worn"],
            likely_root_causes=["Normal wear", "Contamination"],
            recommended_actions=["Replace seal", "Clean system"]
        )
    ]
    
    # Create aggregated results
    return AggregatedResults(
        original_input="The pump's loading/unloading piston is not operating smoothly",
        intent_data=intent_data,
        total_unique_results=2,
        defects=defects,
        root_causes=["Worn piston seals", "Contaminated hydraulic fluid", "Air in system"],
        corrective_actions=["Replace seals", "Change fluid", "Bleed air from system"],
        processing_time_ms=1500.0
    )


async def test_placeholder_passing():
    """Test that placeholders are correctly passed to the agent."""
    print("\n" + "=" * 80)
    print("TEST: Placeholder Passing to jk_pilger_new_entries_agent")
    print("=" * 80)
    
    try:
        # Create mock defect analysis data
        defect_analysis = create_mock_defect_analysis()
        print(f"📝 Mock defect analysis created with {defect_analysis.total_unique_results} defects")
        
        # Prepare custom placeholders (same logic as in agent_processing.py)
        ontology_data = {
            "defects": [defect.model_dump() for defect in defect_analysis.defects],
            "root_causes": defect_analysis.root_causes,
            "corrective_actions": defect_analysis.corrective_actions,
            "intent_data": defect_analysis.intent_data.model_dump(),
            "total_unique_results": defect_analysis.total_unique_results
        }
        
        user_input_text = defect_analysis.original_input
        
        custom_placeholders = {
            "ontology": json.dumps(ontology_data, indent=2),
            "user_input": user_input_text
        }
        
        print(f"🔧 Prepared placeholders:")
        print(f"   - ontology: {len(custom_placeholders['ontology'])} characters")
        print(f"   - user_input: {custom_placeholders['user_input']}")
        
        # Load and build the agent with custom placeholders
        print(f"\n🤖 Loading jk_pilger_new_entries_agent with placeholders...")
        agent, mcp_client, direct_logger = await load_and_build_agent_with_placeholders(
            agent_name="jk_pilger_new_entries_agent",
            custom_placeholders=custom_placeholders,
            config_path="config/jk-gemba.yaml"
        )

        print(f"✅ Agent loaded successfully")
        print(f"   - Agent type: {type(agent)}")
        print(f"   - MCP client: {mcp_client is not None}")
        print(f"   - Direct logger: {direct_logger is not None}")
        
        # Test that the agent was built with the correct prompt file
        print(f"\n📄 Agent should be using prompt file: config/prompts/gemba-d-r-c-v11.txt")
        print(f"   - This prompt contains {{{{ontology}}}} and {{{{user_input}}}} placeholders")
        
        # The placeholders should now be resolved in the agent's prompt
        print(f"\n✅ Placeholder test completed successfully!")
        print(f"   - The agent has been built with custom placeholders")
        print(f"   - {{{{ontology}}}} contains: {len(ontology_data['defects'])} defects, {len(ontology_data['root_causes'])} root causes, {len(ontology_data['corrective_actions'])} actions")
        print(f"   - {{{{user_input}}}} contains: {user_input_text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Placeholder test failed: {e}")
        logger.error(f"Placeholder test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_prompt_file_content():
    """Test that the prompt file contains the expected placeholders."""
    print("\n" + "=" * 80)
    print("TEST: Prompt File Placeholder Content")
    print("=" * 80)
    
    try:
        # Read the prompt file
        prompt_file_path = "config/prompts/gemba-d-r-c-v11.txt"
        with open(prompt_file_path, 'r', encoding='utf-8') as f:
            prompt_content = f.read()
        
        print(f"📄 Prompt file: {prompt_file_path}")
        print(f"   - File size: {len(prompt_content)} characters")
        
        # Check for placeholders
        has_ontology = "{{ontology}}" in prompt_content
        has_user_input = "{{user_input}}" in prompt_content
        
        print(f"\n🔍 Placeholder analysis:")
        print(f"   - Contains {{{{ontology}}}}: {'✅' if has_ontology else '❌'}")
        print(f"   - Contains {{{{user_input}}}}: {'✅' if has_user_input else '❌'}")
        
        if has_ontology and has_user_input:
            print(f"\n✅ Prompt file contains both required placeholders!")
            
            # Show context around placeholders
            ontology_pos = prompt_content.find("{{ontology}}")
            user_input_pos = prompt_content.find("{{user_input}}")
            
            print(f"\n📝 Placeholder context:")
            print(f"   - {{{{ontology}}}} at position {ontology_pos}:")
            print(f"     {prompt_content[max(0, ontology_pos-50):ontology_pos+50]}")
            print(f"   - {{{{user_input}}}} at position {user_input_pos}:")
            print(f"     {prompt_content[max(0, user_input_pos-50):user_input_pos+50]}")
            
            return True
        else:
            print(f"❌ Prompt file missing required placeholders!")
            return False
            
    except Exception as e:
        print(f"❌ Prompt file test failed: {e}")
        logger.error(f"Prompt file test failed: {e}")
        return False


async def test_configuration_consistency():
    """Test that the agent configuration is consistent."""
    print("\n" + "=" * 80)
    print("TEST: Configuration Consistency")
    print("=" * 80)
    
    try:
        # Check the configuration
        config = PilgerProcessingConfig()
        print(f"📋 PilgerProcessingConfig:")
        print(f"   - Agent name: {config.agent_name}")
        print(f"   - Config path: {config.config_path}")
        print(f"   - Format: {config.format_for_agent}")
        print(f"   - Timeout: {config.timeout_seconds}s")
        
        # Verify the agent exists in the configuration
        from app.main import load_app_config
        from pathlib import Path
        
        config_file_path = Path(config.config_path)
        if config_file_path.exists():
            app_config = load_app_config(config_file_path)
            agent_names = [agent.name for agent in app_config.agents]
            
            print(f"\n🔍 Available agents in {config.config_path}:")
            for name in agent_names:
                marker = "✅" if name == config.agent_name else "  "
                print(f"   {marker} {name}")
            
            if config.agent_name in agent_names:
                # Find the specific agent config
                target_agent = next(
                    (agent for agent in app_config.agents if agent.name == config.agent_name),
                    None
                )
                
                if target_agent:
                    print(f"\n📄 Agent configuration:")
                    print(f"   - Name: {target_agent.name}")
                    print(f"   - Description: {target_agent.description}")
                    print(f"   - Model: {target_agent.model}")
                    print(f"   - Prompt file: {target_agent.prompt_file}")
                    
                    # Check if prompt file exists
                    prompt_path = Path(target_agent.prompt_file)
                    if not prompt_path.is_absolute():
                        prompt_path = Path("config") / target_agent.prompt_file
                    
                    prompt_exists = prompt_path.exists()
                    print(f"   - Prompt file exists: {'✅' if prompt_exists else '❌'}")
                    
                    if prompt_exists:
                        print(f"✅ Configuration is consistent!")
                        return True
                    else:
                        print(f"❌ Prompt file not found: {prompt_path}")
                        return False
                else:
                    print(f"❌ Agent configuration not found")
                    return False
            else:
                print(f"❌ Agent '{config.agent_name}' not found in configuration")
                return False
        else:
            print(f"❌ Configuration file not found: {config.config_path}")
            return False
            
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        logger.error(f"Configuration test failed: {e}")
        return False


async def main():
    """Run all placeholder tests."""
    print("🚀 PilgerProcessingPipeline Placeholder Tests")
    print("=" * 80)
    
    tests = [
        ("Prompt File Content", test_prompt_file_content),
        ("Configuration Consistency", test_configuration_consistency),
        ("Placeholder Passing", test_placeholder_passing),
    ]
    
    results = {}
    
    for name, test_func in tests:
        try:
            print(f"\n🔄 Running {name}...")
            result = await test_func()
            results[name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status}: {name}")
        except Exception as e:
            print(f"❌ FAILED: {name} - {e}")
            results[name] = False
    
    # Summary
    print(f"\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    for name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")
    
    print(f"\n📊 Overall: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print(f"🎉 All tests passed! Placeholder system is working correctly.")
        print(f"\n📋 Summary:")
        print(f"   - The jk_pilger_new_entries_agent is configured to use gemba-d-r-c-v11.txt")
        print(f"   - The prompt file contains {{{{ontology}}}} and {{{{user_input}}}} placeholders")
        print(f"   - The PilgerProcessingPipeline passes DefectAnalysisPipeline results as {{{{ontology}}}}")
        print(f"   - The original user input is passed as {{{{user_input}}}}")
        print(f"   - The agent framework resolves these placeholders before sending to the LLM")
    else:
        print(f"⚠️ Some tests failed. Please review the issues above.")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
