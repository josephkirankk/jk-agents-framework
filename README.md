# Agents Final - Supervisor Planner & Executor with FastAPI

This repository contains a production-minded LangGraph + LangChain agent orchestration
system with:
- YAML-configured supervisor and worker ReAct agents
- MCP servers converted into LangChain tools (via MultiServerMCPClient)
- Planner (supervisor) that returns a structured JSON plan (DAG of steps)
- Executor that runs steps in topological order with retries, timeouts, and verification
- FastAPI wrapper exposing /invoke and /plan_and_run endpoints

## Quickstart
1. Create virtualenv and install:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Start example MCP servers in separate shells:
   ```bash
   python examples/mcp_servers/math_server.py
   python examples/mcp_servers/weather_server.py
   ```
3. Run the FastAPI app:
   ```bash
   export OPENAI_API_KEY=...
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
4. Invoke planner & executor:
   ```bash
   curl -X POST "http://localhost:8000/plan_and_run" -H "Content-Type: application/json" -d '{"input":"Get Mumbai weather and compare to Delhi"}'
   ```
