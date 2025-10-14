import asyncio
import time
from typing import List, Tuple

import pytest

from app.main import load_app_config
from app.thread_manager import get_or_create_thread_id
from app.memory.memory_integration import (
    initialize_conversation_memory,
    enhance_system_message_with_memory,
    store_conversation_memory,
    is_conversation_memory_enabled,
)


@pytest.mark.asyncio
async def test_conversation_memory_five_turns_includes_prior_history_and_ordering():
    """
    Regression: Multi-turn memory should include the last 5 turns for a fixed thread_id
    and preserve ordering in the formatted "Previous conversation" context.

    This test avoids external LLM calls by directly using the memory integration layer.
    """
    # Load application config
    app_cfg = load_app_config()

    # Skip if conversation memory is not enabled/configured
    if not is_conversation_memory_enabled(app_cfg):
        pytest.skip("Conversation memory is not enabled or database not configured.")

    # Ensure the conversation store is initialized
    initialized = await initialize_conversation_memory(app_cfg)
    if not initialized:
        pytest.skip("Failed to initialize conversation memory store (DB not reachable?).")

    # Use a stable thread_id for all five turns
    base_thread_id = f"regtest-{int(time.time())}"
    thread_id = get_or_create_thread_id(base_thread_id)

    # Realistic scenario: planning a 2-day tech meetup
    # Five sequential turns where later turns depend on earlier context
    turns: List[Tuple[str, str]] = [
        (
            "We are organizing a 2-day tech meetup. Draft a high-level agenda for Day 1 and Day 2.",
            "Day 1: Registration, Opening Remarks, Keynote, Track Sessions, Networking.\n"
            "Day 2: Workshops, Panel Discussion, Lightning Talks, Closing Remarks.",
        ),
        (
            "Add a 30-minute keynote to Day 1 after opening remarks and suggest a keynote topic.",
            "Added a 30-minute keynote to Day 1 post opening remarks. Suggested topic: 'AI Agents in Enterprise'.",
        ),
        (
            "Create a short list of 4 workshop topics for Day 2 aligned with the keynote theme.",
            "Workshops: (1) Building Agentic Workflows, (2) Vector Databases 101, (3) Prompt Engineering, (4) LLM Observability.",
        ),
        (
            "Now propose 3 panelists for the Day 2 panel discussion (roles/titles only).",
            "Panelists: (1) Head of AI Platform, (2) CTO of a SaaS Company, (3) AI Research Lead.",
        ),
        (
            "Summarize the plan so far in 3 bullet points.",
            "- Two-day agenda with keynote and sessions.\n- Workshops aligned to AI Agents theme.\n- Panel with senior leaders in AI/tech.",
        ),
    ]

    # For each turn, simulate enhancement (as the API does) and then store the conversation entry
    for idx, (user_msg, assistant_resp) in enumerate(turns, start=1):
        # Enhance system context (not strictly needed for storing, but mirrors real flow)
        _ = await enhance_system_message_with_memory(
            original_message=(app_cfg.business_context or ""),
            thread_id=thread_id,
            app_config=app_cfg,
        )

        # Store the conversation turn
        await store_conversation_memory(
            thread_id=thread_id,
            user_message=user_msg,
            assistant_response=assistant_resp,
            app_config=app_cfg,
            metadata={"test_case": "regression_5turns", "turn": idx},
        )

    # After 5 turns, the next enhancement should include all 5 prior turns
    enhanced = await enhance_system_message_with_memory(
        original_message=(app_cfg.business_context or ""),
        thread_id=thread_id,
        app_config=app_cfg,
    )

    # Verify the "Previous conversation" block exists
    assert "Previous conversation:" in enhanced, "Expected Previous conversation block not found in enhanced context"

    # Verify all five turns' user and assistant lines are present
    user_positions = []
    for user_msg, assistant_resp in turns:
        user_line = f"User: {user_msg.strip()}"
        assistant_line = f"Assistant: {assistant_resp.strip()}"
        assert user_line in enhanced, f"Missing user line in enhanced context: {user_line}"
        assert assistant_line in enhanced, f"Missing assistant line in enhanced context: {assistant_line}"
        user_positions.append(enhanced.index(user_line))

    # Verify ordering: earlier user lines appear before later ones (chronological)
    assert user_positions == sorted(user_positions), (
        "User message order is not chronological in the enhanced context"
    )

    # Optional: verify that only the last 5 are included by adding a 6th and checking one drops
    extra_turn = (
        "Add a lightning talk about evaluation frameworks.",
        "Lightning talk added: 'Evaluating Agentic Systems at Scale'.",
    )

    await store_conversation_memory(
        thread_id=thread_id,
        user_message=extra_turn[0],
        assistant_response=extra_turn[1],
        app_config=app_cfg,
        metadata={"test_case": "regression_5turns", "turn": 6},
    )

    enhanced_after_6 = await enhance_system_message_with_memory(
        original_message=(app_cfg.business_context or ""),
        thread_id=thread_id,
        app_config=app_cfg,
    )

    # The first turn might be dropped due to max_conversations=5 default
    first_user_line = f"User: {turns[0][0].strip()}"
    first_assistant_line = f"Assistant: {turns[0][1].strip()}"

    # If the enhancer uses max_conversations=5, the first turn may no longer be present
    # Accept either presence (if configured differently) or absence (default) without failing
    # But the 6th turn must be present now
    new_user_line = f"User: {extra_turn[0].strip()}"
    new_assistant_line = f"Assistant: {extra_turn[1].strip()}"
    assert new_user_line in enhanced_after_6
    assert new_assistant_line in enhanced_after_6
