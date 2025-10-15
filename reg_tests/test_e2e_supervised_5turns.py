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
from api import run_supervised_api
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage


class StubChatModel:
    """Minimal stub for LangChain ChatModel used by create_react_agent/supervisor.

    - Supports bind_tools(tools, parallel_tool_calls=...)
    - Provides ainvoke/invoke returning an AIMessage with .content
    """

    def __init__(self, model_id: str):
        self.model_id = model_id

    def bind_tools(self, tools, **kwargs):
        return self

    async def ainvoke(self, messages, *, config=None, **kwargs):
        return AIMessage(content="OK - stubbed response")

    def invoke(self, messages, *, config=None, **kwargs):
        return AIMessage(content="OK - stubbed response (sync)")

    def __call__(self, messages, *args, **kwargs):
        return AIMessage(content="OK - stubbed response (__call__)")


@pytest.mark.asyncio
async def test_e2e_supervised_5turns_python_exec_config(monkeypatch):
    """
    End-to-end regression: send 5 supervised runs with a fixed thread_id using a
    real AppConfig (python_exec_agent_working.yaml), stub LLM providers and MCP tools,
    and verify conversation memory contains prior turns in the enhanced context.
    """
    # Monkeypatch init_chat_model to avoid real network/model calls
    def _stub_init_chat_model(model_id: str):
        return StubChatModel(model_id)

    monkeypatch.setattr("langchain.chat_models.init_chat_model", _stub_init_chat_model, raising=True)

    # Monkeypatch MCP loader to avoid spawning external processes like Deno
    async def _stub_load_mcp_tools(servers_cfg, tool_timeout: float = 30.0, tool_retries: int = 0):
        return None, []

    monkeypatch.setattr("app.mcp_loader.load_mcp_tools", _stub_load_mcp_tools, raising=True)

    # Monkeypatch checkpointer to use in-memory saver (avoid optimized backend writes)
    monkeypatch.setattr(
        "app.checkpointer_manager.get_global_checkpointer",
        lambda config=None: MemorySaver(),
        raising=True,
    )
    # Also patch module-local imports
    monkeypatch.setattr(
        "app.agent_builder.get_global_checkpointer",
        lambda config=None: MemorySaver(),
        raising=True,
    )
    monkeypatch.setattr(
        "app.supervisor_builder.get_global_checkpointer",
        lambda config=None: MemorySaver(),
        raising=True,
    )

    # Load the working config
    cfg_path = Path("config/python_exec_agent_working.yaml").resolve()
    app_cfg = load_app_config(cfg_path)

    # Skip if conversation memory is not enabled/configured
    if not is_conversation_memory_enabled(app_cfg):
        pytest.skip("Conversation memory is not enabled or database not configured.")

    # Initialize conversation memory (PostgreSQL)
    ok = await initialize_conversation_memory(app_cfg)
    if not ok:
        pytest.skip("Failed to initialize conversation memory (DB not reachable?).")

    # Use a consistent thread_id for all turns
    base_thread_id = f"e2e-supervised-5turns-{int(time.time())}"

    # Five user inputs building on prior context
    inputs: List[str] = [
        "We are planning a 2-day tech meetup. Draft the Day 1 and Day 2 structure.",
        "Add a 30-minute keynote to Day 1 and suggest a keynote topic.",
        "Propose 4 workshop topics for Day 2 that align with the keynote theme.",
        "Suggest 3 panelist roles/titles for Day 2 panel discussion.",
        "Summarize the plan so far in 3 bullets.",
    ]

    # Execute 5 supervised runs end-to-end
    for user_input in inputs:
        result = await run_supervised_api(
            user_input=user_input,
            app_cfg=app_cfg,
            config_path=str(cfg_path),
            thread_id=base_thread_id,
        )
        assert isinstance(result, dict)
        assert result.get("ok") is not False  # supervisor flow shouldn't hard-fail

    # After 5 turns, verify enhanced context includes all prior user lines
    enhanced = await enhance_system_message_with_memory(
        original_message=app_cfg.business_context or "",
        thread_id=base_thread_id,
        app_config=app_cfg,
    )

    assert "Previous conversation:" in enhanced

    # Verify each input appears as a prior user line
    for text in inputs:
        line = f"User: {text}"
        assert line in enhanced, f"Missing prior user input in context: {line}"

    # Verify chronological ordering
    positions = [enhanced.index(f"User: {txt}") for txt in inputs]
    assert positions == sorted(positions), "Conversation order is not chronological in enhanced context"
