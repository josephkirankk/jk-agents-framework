# Agents Final - Supervisor Planner & Executor with FastAPI

This repository contains a production-minded LangGraph + LangChain agent orchestration
system with:
- YAML-configured supervisor and worker ReAct agents
- MCP servers converted into LangChain tools (via MultiServerMCPClient)
- Planner (supervisor) that returns a structured JSON plan (DAG of steps)
- Executor that runs steps in topological order with retries, timeouts, and verification
- FastAPI wrapper exposing /invoke and /plan_and_run endpoints

## Run
-  .venv\Scripts\python.exe -m app.main --config config\brave_math_weather.yaml "print the current population of india in ASCII art"

## Quickstart
1. Create virtualenv and install:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   .venv\Scripts\activate
   .venv\Scripts\Activate.ps1

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


## MCP servers

- deno cache --node-modules-dir=auto jsr:@pydantic/mcp-run-python


## Azure OpenAI setup

This repo supports both OpenAI and Azure OpenAI. If these environment variables are present, models like `openai:gpt-4o-mini` are auto-switched to `azure_openai:gpt-4o-mini` and used with Azure OpenAI SDK:

- AZURE_OPENAI_API_KEY
- AZURE_OPENAI_ENDPOINT (e.g., https://your-resource-name.openai.azure.com)
- Optional per-deployment: AZURE_OPENAI_API_VERSION (defaults to SDK)

Windows PowerShell example:

```
$env:AZURE_OPENAI_API_KEY="<your-key>"
$env:AZURE_OPENAI_ENDPOINT="https://<your-resource>.openai.azure.com"
python -m app.main "Research ACME quarterly results and summarize with sources."
```

If your Brave MCP requires auth headers, add them under `headers` in `config/agents.yaml` for the `web_agent` MCP server.
