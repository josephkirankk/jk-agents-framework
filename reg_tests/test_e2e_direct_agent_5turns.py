import asyncio
import time
from pathlib import Path
from typing import List

import pytest

from app.main import load_app_config
from app.memory.memory_integration import (
    initialize_conversation_memory,
    is_conversation_memory_enabled,
    enhance_system_message_with_memory,
)
from api import run_direct_agent_api
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage


class StubChatModel:
    """Minimal stub for LangChain ChatModel used by create_react_agent.

    - Supports bind_tools(tools, parallel_tool_calls=...)
    - Provides ainvoke/invoke returning an object with .content
    """

    def __init__(self, model_id: str):
        self.model_id = model_id

    # create_react_agent calls .bind_tools on the model
    def bind_tools(self, tools, **kwargs):
        return self

    # Agent execution path may call async
    async def ainvoke(self, messages, *, config=None, **kwargs):
        # Return a deterministic, short response as AIMessage
        return AIMessage(content="OK - stubbed response")

    # Some paths may call sync invoke
    def invoke(self, messages, *, config=None, **kwargs):
        return AIMessage(content="OK - stubbed response (sync)")

    # Allow coerce_to_runnable to treat this as a callable if needed
    def __call__(self, messages, *args, **kwargs):
        return AIMessage(content="OK - stubbed response (__call__) ")


@pytest.mark.asyncio
async def test_e2e_direct_agent_5turns_python_exec_config(monkeypatch):
    """
    End-to-end regression: send 5 direct-agent turns with a fixed thread_id using a
    real AppConfig (python_exec_agent_working.yaml), stub LLM providers, and verify that
    conversation memory contains all prior turns in the enhanced context.
    """
    # Monkeypatch init_chat_model to avoid hitting real providers (Azure/OpenAI/etc.)
    def _stub_init_chat_model(model_id: str):
        return StubChatModel(model_id)

    monkeypatch.setattr("langchain.chat_models.init_chat_model", _stub_init_chat_model, raising=True)

    # Use in-memory checkpointer to avoid Chroma writes in tests
    monkeypatch.setattr(
        "app.checkpointer_manager.get_global_checkpointer",
        lambda config=None: MemorySaver(),
        raising=True,
    )
    # Also patch module-local import in agent_builder
    monkeypatch.setattr(
        "app.agent_builder.get_global_checkpointer",
        lambda config=None: MemorySaver(),
        raising=True,
    )
    # Ensure any optimized path is disabled during tests
    monkeypatch.setattr(
        "app.memory.langgraph_adapter.get_optimized_checkpointer",
        lambda config=None: MemorySaver(),
        raising=True,
    )

    # Load the specific working config selected by the user
    cfg_path = Path("config/python_exec_agent_working.yaml").resolve()
    app_cfg = load_app_config(cfg_path)

    # If conversation memory is disabled or DB is not configured, skip the test
    if not is_conversation_memory_enabled(app_cfg):
        pytest.skip("Conversation memory is not enabled or database not configured.")

    # Initialize conversation memory store (PostgreSQL)
    ok = await initialize_conversation_memory(app_cfg)
    if not ok:
        pytest.skip("Failed to initialize conversation memory (DB not reachable?).")

    # Use a consistent thread_id for all turns
    base_thread_id = f"e2e-5turns-{int(time.time())}"

    # Choose a simple agent from the config without external tools: human_response_agent
    agent = "human_response_agent"

    # Five realistic user inputs that build upon each other
    inputs: List[str] = [
        "We are planning a 2-day tech meetup. Draft the Day 1 and Day 2 structure.",
        "Add a 30-minute keynote to Day 1 and suggest a keynote topic.",
        "Propose 4 workshop topics for Day 2 that align with the keynote theme.",
        "Suggest 3 panelist roles/titles for Day 2 panel discussion.",
        "Summarize the plan so far in 3 bullets.",
    ]

    # Execute 5 turns through the actual API helper (end-to-end path)
    last_thread = None
    for i, user_input in enumerate(inputs, start=1):
        res = await run_direct_agent_api(
            agent_name=agent,
            user_input=user_input,
            app_cfg=app_cfg,
            config_path=str(cfg_path),
            thread_id=base_thread_id,
        )
        assert res.get("success") is True
        assert res.get("agent_name") == agent
        # Ensure thread_id continuity returned by the API
        assert res.get("thread_id") == base_thread_id
        last_thread = res.get("thread_id")

    assert last_thread == base_thread_id

    # After 5 turns, verify that the enhanced system context includes "Previous conversation" with the 5 turns
    enhanced = await enhance_system_message_with_memory(
        original_message=app_cfg.business_context or "",
        thread_id=base_thread_id,
        app_config=app_cfg,
    )

    assert "Previous conversation:" in enhanced

    # Verify that each user input appears in the enhanced context (as stored conversation entries)
    for text in inputs:
        expected_user_line = f"User: {text}"
        assert expected_user_line in enhanced, f"Missing prior user input in context: {expected_user_line}"

    # Verify ordering by position (older first)
    positions = [enhanced.index(f"User: {txt}") for txt in inputs]
    assert positions == sorted(positions), "Conversation order is not chronological in enhanced context"
