#!/usr/bin/env python3
"""Debug script to test the agent multiturn conversation."""

import sys
import os
import asyncio
import traceback
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("debug_script")

# Add the project directory to sys.path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))
log.info(f"Added {project_dir} to sys.path")

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = project_dir / '.env'
    load_dotenv(env_path)
    log.info(f"✅ Loaded environment from {env_path}")
except ImportError:
    log.warning("❌ python-dotenv not installed")

# Check environment variables
required_vars = [
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_ENDPOINT"
]

for var in required_vars:
    if os.environ.get(var):
        log.info(f"✓ {var} is set")
    else:
        log.warning(f"⚠️ {var} is NOT set")


# Import the test module
from tests.test_multi_turn_conversation import TestMultiTurnConversation

# Import needed modules for model creation
from langchain_core.messages import HumanMessage
from app.enhanced_litellm_wrapper import EnhancedLiteLLMChat

# Helper function to get model
def get_model(model_id):
    """Create a model instance for the given model ID."""
    # Assume it's a LiteLLM model
    return EnhancedLiteLLMChat(
        model=model_id,
        temperature=0.2,
        timeout=60
    )

# Create test instance and run it
async def main():
    try:
        log.info("========== STARTING TEST EXECUTION ==========")
        
        # Step 1: Create test class and initialize providers
        log.info("Step 1: Initializing test class and model providers")
        test_class = TestMultiTurnConversation
        test_class.setUpClass()
        log.info("✓ Class setup complete")
        
        # Step 2: Create test instance
        log.info("Step 2: Creating test instance")
        test = test_class()
        log.info("✓ Test instance created")

        # Step 3: Run setUp
        log.info("Step 3: Running setUp")
        test.setUp()
        log.info("✓ Setup complete")
        
        # Step 4: Set model for LLM judge
        log.info("Step 4: Setting up LLM judge model")
        if not hasattr(test, 'available_providers') or not test.available_providers:
            log.error("⚠️ No providers available in test instance")
            log.info(f"available_providers attribute exists: {hasattr(test, 'available_providers')}")
            if hasattr(test, 'available_providers'):
                log.info(f"available_providers value: {test.available_providers}")
            return 1
            
        provider_name, model_id = test.available_providers[0]
        log.info(f"Using provider: {provider_name}, model: {model_id}")
        
        # Create model instance
        try:
            test.model = get_model(model_id)
            log.info(f"✓ Model created successfully: {model_id}")
        except Exception as model_error:
            log.error(f"Failed to create model: {str(model_error)}")
            traceback.print_exc()
            return 1

        # Step 5: Run the test method
        log.info("\n========== RUNNING AGENT MULTITURN TEST ==========\n")
        
        # Execute the test with a timeout to prevent hanging
        try:
            # Give it 3 minutes to complete
            await asyncio.wait_for(test._async_test_agent_multiturn(), timeout=180)
            log.info("\n========== TEST COMPLETED SUCCESSFULLY ==========\n")
        except asyncio.TimeoutError:
            log.error("\n⏱️ TEST TIMED OUT AFTER 3 MINUTES\n")
            return 1

    except KeyboardInterrupt:
        log.warning("\n⚠️ Test interrupted by user")
        return 130
    except Exception as e:
        log.error(f"\n❌ ERROR: {str(e)}")
        log.error("\nTRACEBACK:")
        traceback.print_exc()
        log.error("\n========== TEST FAILED ==========\n")
        return 1

    log.info("Test execution completed successfully")
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(130)
