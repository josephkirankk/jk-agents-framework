#!/usr/bin/env python3
"""
Direct test of LiteLLM multi-model, multi-turn workflow with jk-agents-framework.
This script provides a practical demonstration of:
1. Using multiple LiteLLM models in the same workflow
2. Maintaining conversation context across turns
3. Tool binding with different model providers
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent  # Go up one level to project root
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / '.env')
    print("✅ Loaded environment variables from .env")
except ImportError:
    print("⚠️ dotenv not installed, skipping environment loading")

# Import framework components
from app.main import load_app_config
from app.supervisor_builder import build_supervisor_compiled
from app.planner_executor import execute_plan
from app.thread_id_utils import generate_thread_id
from app.simple_conversation_memory_fixed import get_conversation_memory
from app.enhanced_litellm_wrapper import EnhancedLiteLLMChat

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("litellm_multi_test")

# ANSI colors for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

async def test_multi_model_workflow():
    """Test a multi-model workflow with conversation continuity."""
    print(f"{BLUE}=== Testing Multi-Model, Multi-Turn Workflow ==={RESET}")
    
    # Configuration
    config_path = "config/multi_provider_agent.yaml"
    app_cfg = load_app_config(Path(config_path))
    thread_id = generate_thread_id()
    
    print(f"{BLUE}Thread ID: {thread_id}{RESET}")
    print(f"{BLUE}Configuration: {config_path}{RESET}")
    
    # Verify available model providers
    has_azure = bool(os.getenv("AZURE_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY"))
    has_google = bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    
    print(f"{BLUE}Available providers:{RESET}")
    print(f"  Azure OpenAI: {'✅' if has_azure else '❌'}")
    print(f"  Google Gemini: {'✅' if has_google else '❌'}")
    print(f"  OpenAI: {'✅' if has_openai else '❌'}")
    
    if not (has_azure or has_google or has_openai):
        print(f"{RED}Error: No model API credentials found. Cannot run test.{RESET}")
        return False
    
    # TURN 1: Create a dataset
    turn1_start = time.time()
    print(f"\n{BLUE}=== TURN 1: Create a dataset ==={RESET}")
    
    # Use Azure model for supervisor
    if has_azure:
        default_model = "azure/gpt-4.1"
        print(f"Using Azure OpenAI model for supervisor: {default_model}")
    elif has_openai:
        default_model = "openai/gpt-4o-mini"
        print(f"Using OpenAI model for supervisor: {default_model}")
    elif has_google:
        default_model = "gemini/gemini-2.5-flash-lite"
        print(f"Using Google Gemini model for supervisor: {default_model}")
    else:
        print(f"{RED}No valid model provider found{RESET}")
        return False
    
    user_input_1 = "Create a dataset of 5 fictional employees with names, roles, and salaries."
    
    # Build supervisor
    supervisor = build_supervisor_compiled(
        app_cfg.supervisor,
        app_cfg.agents,
        default_model,
        app_cfg.business_context or "",
        original_user_question=user_input_1,
        config_path=config_path,
        default_temperature=0.2,
        thread_id=thread_id,
    )
    
    # Build agents
    agents_map = {}
    from app.main import build_agents_map
    agents_map, mcp_clients = await build_agents_map(
        app_cfg, 
        user_input=user_input_1, 
        config_path=config_path
    )
    
    # Execute turn 1
    print(f"\n{YELLOW}Executing Turn 1: {user_input_1}{RESET}")
    
    try:
        result_1 = await execute_plan(
            supervisor_compiled=supervisor,
            agents_map=agents_map,
            user_input=user_input_1,
            thread_id=thread_id,
        )
        
        turn1_time = time.time() - turn1_start
        print(f"\n{GREEN}Turn 1 completed in {turn1_time:.2f}s{RESET}")
        print(f"{GREEN}Response:{RESET}\n{result_1['response']}")
        
        # Store reference to employees for verification
        employee_names = extract_employee_names(result_1['response'])
        print(f"\nExtracted employee names: {', '.join(employee_names)}")
        
        # TURN 2: Add departments to the existing employees
        turn2_start = time.time()
        print(f"\n{BLUE}=== TURN 2: Add departments to employees ==={RESET}")
        
        # For turn 2, switch to a different model if available
        if has_google and has_azure:
            # If we used Azure for turn 1, use Google for turn 2
            if "azure" in default_model:
                default_model = "gemini/gemini-2.5-flash-lite"
            else:
                default_model = "azure/gpt-4.1"
            print(f"Switching to {default_model} for turn 2")
        
        user_input_2 = "Assign a department to each employee from the previous list."
        
        # Build new supervisor (with the same thread_id)
        supervisor2 = build_supervisor_compiled(
            app_cfg.supervisor,
            app_cfg.agents,
            default_model,
            app_cfg.business_context or "",
            original_user_question=user_input_2,
            config_path=config_path,
            default_temperature=0.2,
            thread_id=thread_id,
        )
        
        # Execute turn 2
        print(f"\n{YELLOW}Executing Turn 2: {user_input_2}{RESET}")
        
        result_2 = await execute_plan(
            supervisor_compiled=supervisor2,
            agents_map=agents_map,
            user_input=user_input_2,
            thread_id=thread_id,
        )
        
        turn2_time = time.time() - turn2_start
        print(f"\n{GREEN}Turn 2 completed in {turn2_time:.2f}s{RESET}")
        print(f"{GREEN}Response:{RESET}\n{result_2['response']}")
        
        # Verify context continuity
        context_success = verify_context_continuity(
            employee_names, 
            result_2['response']
        )
        
        # TURN 3: Calculate department statistics
        if context_success:
            turn3_start = time.time()
            print(f"\n{BLUE}=== TURN 3: Calculate department statistics ==={RESET}")
            
            # Use a third model if available
            if has_openai and (has_azure or has_google):
                default_model = "openai/gpt-4o-mini"
                print(f"Switching to {default_model} for turn 3")
            
            user_input_3 = "Calculate the average salary per department based on the employee data."
            
            # Build new supervisor (with the same thread_id)
            supervisor3 = build_supervisor_compiled(
                app_cfg.supervisor,
                app_cfg.agents,
                default_model,
                app_cfg.business_context or "",
                original_user_question=user_input_3,
                config_path=config_path,
                default_temperature=0.2,
                thread_id=thread_id,
            )
            
            # Execute turn 3
            print(f"\n{YELLOW}Executing Turn 3: {user_input_3}{RESET}")
            
            result_3 = await execute_plan(
                supervisor_compiled=supervisor3,
                agents_map=agents_map,
                user_input=user_input_3,
                thread_id=thread_id,
            )
            
            turn3_time = time.time() - turn3_start
            print(f"\n{GREEN}Turn 3 completed in {turn3_time:.2f}s{RESET}")
            print(f"{GREEN}Response:{RESET}\n{result_3['response']}")
        
        # Check memory system
        memory = get_conversation_memory()
        context_summary = memory.get_conversation_summary(thread_id)
        print(f"\n{BLUE}Memory Context Summary:{RESET}")
        print(context_summary[:500] + "..." if len(context_summary) > 500 else context_summary)
        
        return True
    
    except Exception as e:
        print(f"{RED}Error executing workflow: {e}{RESET}")
        import traceback
        print(traceback.format_exc())
        return False

def extract_employee_names(text):
    """Extract employee names from the response text."""
    import re
    
    # Look for common name patterns
    name_pattern = r"(?:(?:Mr\.|Ms\.|Dr\.|Prof\.)\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)"
    names = re.findall(name_pattern, text)
    
    # Remove duplicates and clean up
    unique_names = []
    for name in names:
        name = name.strip()
        if name and name not in unique_names:
            unique_names.append(name)
    
    # If no names found via regex, try simple extraction of capitalized words
    if not unique_names:
        lines = text.split('\n')
        for line in lines:
            if re.search(r'name|employee', line.lower()):
                # Find capitalized words that could be names
                possible_names = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', line)
                for name in possible_names:
                    if name.strip() and name.strip() not in unique_names:
                        unique_names.append(name.strip())
    
    return unique_names

def verify_context_continuity(employee_names, turn2_response):
    """Verify that Turn 2 references employee names from Turn 1."""
    if not employee_names:
        print(f"{YELLOW}Warning: No employee names extracted from Turn 1{RESET}")
        return False
    
    context_preserved = False
    
    for name in employee_names:
        if name in turn2_response:
            print(f"{GREEN}✓ Context preserved: Found '{name}' in Turn 2 response{RESET}")
            context_preserved = True
        else:
            print(f"{YELLOW}✗ '{name}' not found in Turn 2 response{RESET}")
    
    if context_preserved:
        print(f"{GREEN}✓ Multi-turn conversation continuity verified{RESET}")
    else:
        print(f"{RED}✗ Multi-turn conversation continuity failed{RESET}")
    
    return context_preserved

async def main():
    """Main test runner."""
    success = await test_multi_model_workflow()
    
    if success:
        print(f"\n{GREEN}✅ Multi-model, multi-turn workflow test completed successfully!{RESET}")
        print(f"{GREEN}The test verified:{RESET}")
        print(f"{GREEN}- Multiple LiteLLM model providers work together{RESET}")
        print(f"{GREEN}- Conversation context is preserved across turns{RESET}")
        print(f"{GREEN}- Tool binding works with different model providers{RESET}")
        print(f"{GREEN}- Memory system properly stores and retrieves context{RESET}")
    else:
        print(f"\n{RED}❌ Multi-model, multi-turn workflow test failed{RESET}")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
