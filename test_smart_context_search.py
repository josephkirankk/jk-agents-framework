#!/usr/bin/env python
"""
Test script for smart context search functionality.
Tests with simple conversations to verify efficient context retrieval.
"""

import asyncio
import logging
import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import AppConfig
from api import run_supervised_api, load_app_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s"
)

log = logging.getLogger(__name__)


async def test_smart_context_search():
    """Test smart context search with various scenarios."""
    
    # Load simple test configuration
    config_path = Path("config/simple_memory_test.yaml")
    
    try:
        app_cfg = load_app_config(config_path)
    except Exception as e:
        log.error(f"Failed to load test config: {e}")
        return
    
    # Use a unique thread ID for this test
    thread_id = "test-smart-context-12345"
    
    log.info("=" * 70)
    log.info("Testing Smart Context Search")
    log.info("=" * 70)
    
    # Test 1: Establish some context with a list of items
    log.info("\n--- Test 1: Creating Context with Items ---")
    log.info("Query: Tell me about these three programming languages: Python, JavaScript, and Go")
    
    try:
        result1 = await run_supervised_api(
            user_input="Tell me about these three programming languages: Python, JavaScript, and Go",
            app_cfg=app_cfg,
            config_path=str(config_path),
            thread_id=thread_id
        )
        
        # Check if we got a valid result with steps
        if result1 and "steps" in result1:
            # Check if any step completed successfully
            steps = result1.get("steps", {})
            success = any(step_data.get("ok", False) for step_data in steps.values())
            if success:
                log.info("✅ Context established successfully")
            else:
                log.error("❌ Failed to establish context - no successful steps")
                return
        else:
            log.error("❌ Failed to establish context - no valid result")
            return
            
    except Exception as e:
        log.error(f"❌ Error in test 1: {e}")
        return
    
    # Wait a moment
    await asyncio.sleep(1)
    
    # Test 2: Reference the items using "these"
    log.info("\n--- Test 2: Context Reference with 'these' ---")
    log.info("Query: Which of these is best for web development?")
    
    try:
        result2 = await run_supervised_api(
            user_input="Which of these is best for web development?",
            app_cfg=app_cfg,
            config_path=str(config_path),
            thread_id=thread_id  # Same thread ID
        )
        
        if result2 and "steps" in result2:
            # Check if the response shows understanding of the context
            steps = result2.get("steps", {})
            context_found = False
            
            for step_id, step_data in steps.items():
                response = step_data.get("raw", "")
                if any(lang in response for lang in ["Python", "JavaScript", "Go"]):
                    log.info("✅ Smart context search worked! Found programming languages in response.")
                    context_found = True
                    break
            
            if not context_found:
                log.warning("⚠️ Context reference unclear - checking if smart search tool was used")
                
        else:
            log.error("❌ Failed context reference query")
            
    except Exception as e:
        log.error(f"❌ Error in test 2: {e}")
    
    # Wait a moment
    await asyncio.sleep(1)
    
    # Test 3: Create numeric context
    log.info("\n--- Test 3: Creating Numeric Context ---")
    log.info("Query: Here are some numbers: 42, 87, 156, 203")
    
    try:
        result3 = await run_supervised_api(
            user_input="Here are some numbers: 42, 87, 156, 203",
            app_cfg=app_cfg,
            config_path=str(config_path),
            thread_id=thread_id
        )
        
        if result3 and "steps" in result3:
            steps = result3.get("steps", {})
            success = any(step_data.get("ok", False) for step_data in steps.values())
            if success:
                log.info("✅ Numeric context established")
            else:
                log.error("❌ Failed to establish numeric context")
        else:
            log.error("❌ Failed to establish numeric context")
            
    except Exception as e:
        log.error(f"❌ Error in test 3: {e}")
    
    # Wait a moment
    await asyncio.sleep(1)
    
    # Test 4: Reference numbers using "those"
    log.info("\n--- Test 4: Context Reference with 'those' ---")
    log.info("Query: What's the average of those numbers?")
    
    try:
        result4 = await run_supervised_api(
            user_input="What's the average of those numbers?",
            app_cfg=app_cfg,
            config_path=str(config_path),
            thread_id=thread_id
        )
        
        if result4 and "steps" in result4:
            steps = result4.get("steps", {})
            calculation_found = False
            
            for step_id, step_data in steps.items():
                response = step_data.get("raw", "")
                # Check if it found the numbers and calculated average
                if any(num in response for num in ["42", "87", "156", "203"]):
                    if any(calc in response.lower() for calc in ["average", "mean", "122"]):  # 122 is the average
                        log.info("✅ Smart context search found numbers and calculated average!")
                        calculation_found = True
                        break
            
            if not calculation_found:
                log.warning("⚠️ May not have found the specific numbers from context")
                
        else:
            log.error("❌ Failed numeric context reference")
            
    except Exception as e:
        log.error(f"❌ Error in test 4: {e}")
    
    log.info("\n" + "=" * 70)
    log.info("Smart Context Search Tests Complete")
    log.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_smart_context_search())