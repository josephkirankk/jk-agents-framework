#!/usr/bin/env python
"""
Test script to verify supervisor-level memory persistence between API calls.
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


async def test_supervisor_memory_persistence():
    """Test that the supervisor understands context from previous queries."""
    
    # Load configuration
    config_path = Path("config/ado_realtime_jk.yaml")
    app_cfg = load_app_config(config_path)
    
    # Use a unique thread ID for this test
    thread_id = "test-supervisor-memory-12345"
    
    log.info("=" * 60)
    log.info("Testing Supervisor Memory Context with Thread ID: %s", thread_id)
    log.info("=" * 60)
    
    # First query - get user stories
    log.info("\n--- First Query ---")
    log.info("Query: get the top 3 recent user stores.")
    
    result1 = await run_supervised_api(
        user_input="get the top 3 recent user stores.",
        app_cfg=app_cfg,
        config_path=str(config_path),
        thread_id=thread_id
    )
    
    log.info("First query completed")
    if result1.get("success"):
        log.info("First query was successful")
    else:
        log.error("First query failed!")
        return
    
    # Wait a moment
    await asyncio.sleep(2)
    
    # Second query - reference previous context
    log.info("\n--- Second Query ---")
    log.info("Query: get the bug count for each of these")
    log.info("This should reference the user stories from the first query")
    
    result2 = await run_supervised_api(
        user_input="get the bug count for each of these",
        app_cfg=app_cfg,
        config_path=str(config_path),
        thread_id=thread_id  # Same thread ID
    )
    
    log.info("Second query completed")
    if result2.get("success"):
        log.info("Second query was successful")
        
        # Check if the supervisor plan shows understanding of context
        steps = result2.get("steps", {})
        for step_id, step_data in steps.items():
            task = step_data.get("task", "")
            if "these" in task.lower() or "each of" in task.lower():
                log.info(f"Step {step_id} task: {task}")
                
                # Check if it mentions specific work item IDs from first query
                if any(word in task for word in ["19283111", "18954043", "user stor"]):
                    log.info("\n✅ SUCCESS! The supervisor understood the context!")
                    log.info("The task references specific items from the previous conversation.")
                    return
        
        log.warning("\n⚠️ PARTIAL SUCCESS: Query completed but context understanding unclear.")
        log.info("Supervisor plan steps:")
        for step_id, step_data in steps.items():
            log.info(f"  {step_id}: {step_data.get('task', 'No task')}")
            
    else:
        log.error("Second query failed!")
    
    log.info("\n" + "=" * 60)
    log.info("Test Complete")
    log.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_supervisor_memory_persistence())