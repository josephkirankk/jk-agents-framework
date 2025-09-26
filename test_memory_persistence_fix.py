#!/usr/bin/env python
"""
Test script to verify memory persistence between API calls with the same thread_id.
"""

import asyncio
import logging
import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import AppConfig
from api import run_direct_agent_api, load_app_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s"
)

log = logging.getLogger(__name__)


async def test_memory_persistence():
    """Test that memory persists between API calls with the same thread_id."""
    
    # Load configuration
    config_path = Path("config/ado_realtime_jk.yaml")
    app_cfg = load_app_config(config_path)
    
    # Use a unique thread ID for this test
    thread_id = "test-memory-persistence-12345"
    
    log.info("=" * 60)
    log.info("Testing Memory Persistence with Thread ID: %s", thread_id)
    log.info("=" * 60)
    
    # First query - get user stories
    log.info("\n--- First Query ---")
    log.info("Query: get the top 5 recent user stores.")
    
    result1 = await run_direct_agent_api(
        agent_name="ado_quick_query_agent",
        user_input="get the top 5 recent user stores.",
        app_cfg=app_cfg,
        config_path=str(config_path),
        thread_id=thread_id
    )
    
    log.info("First query response received")
    if result1.get("success"):
        log.info("Response preview: %s", result1["response"][:200] + "..." if len(result1["response"]) > 200 else result1["response"])
    else:
        log.error("First query failed!")
        return
    
    # Wait a moment
    await asyncio.sleep(2)
    
    # Second query - reference previous context
    log.info("\n--- Second Query ---")
    log.info("Query: get the bug count for each of these")
    log.info("This should reference the user stories from the first query")
    
    result2 = await run_direct_agent_api(
        agent_name="ado_quick_query_agent", 
        user_input="get the bug count for each of these",
        app_cfg=app_cfg,
        config_path=str(config_path),
        thread_id=thread_id  # Same thread ID
    )
    
    log.info("Second query response received")
    if result2.get("success"):
        response_text = result2["response"]
        log.info("Response: %s", response_text)
        
        # Check if the response shows understanding of context
        if "these" in response_text.lower() and "bug" in response_text.lower():
            # Check if it mentions user stories or specific IDs from first query
            if any(word in response_text.lower() for word in ["user stor", "19283111", "18954043", "18954039", "18954038", "18578823"]):
                log.info("\n✅ SUCCESS! The agent understood the context from the first query!")
                log.info("The response references the user stories from the previous conversation.")
            else:
                log.warning("\n⚠️ PARTIAL SUCCESS: The agent understood we're asking about bugs, but may not have the full context of specific user stories.")
        else:
            log.error("\n❌ FAILURE: The agent did not understand the context from the first query.")
            log.error("Expected a response about bug counts for the previously mentioned user stories.")
    else:
        log.error("Second query failed!")
    
    log.info("\n" + "=" * 60)
    log.info("Test Complete")
    log.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_memory_persistence())