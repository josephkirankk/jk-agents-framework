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


## Multi-Provider OpenAI Setup

This repo supports **multiple OpenAI providers simultaneously**:

- **Regular OpenAI API** - Official OpenAI models
- **Azure OpenAI** - Enterprise OpenAI models via Azure
- **LM Studio** - Local models running on your machine
- **Other OpenAI-compatible services** - Ollama, LocalAI, etc.

### Quick Setup

1. **Copy and configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and endpoints
   ```

2. **Test your configuration**:
   ```bash
   python scripts/test_multi_provider.py
   ```

3. **Use multiple providers in your YAML config**:
   ```yaml
   models:
     default: "azure_openai:gpt-4o-mini"      # Uses Azure OpenAI
     supervisor: "azure_openai:gpt-4o"        # Uses Azure OpenAI
     local_dev: "openai:google/gemma-3n-e4b"  # Uses LM Studio
     local_test: "openai:llama-3.2-3b"        # Uses LM Studio
   ```

### Model Naming Convention

- `openai:model-name` - Uses OpenAI API or local server (if OPENAI_BASE_URL is set)
- `azure_openai:deployment-name` - Uses Azure OpenAI

### Example Configurations

**Azure OpenAI + LM Studio** (Recommended):
```env
# Azure OpenAI for production
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# LM Studio for local development
OPENAI_BASE_URL=http://127.0.0.1:1234/v1
OPENAI_API_KEY=lm-studio
```

**All three providers**:
```env
OPENAI_API_KEY=sk-your-openai-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-azure-key
OPENAI_BASE_URL=http://127.0.0.1:1234/v1  # Overrides regular OpenAI for openai: models
```

### Documentation

- 📖 **Complete Guide**: [docs/MULTI_PROVIDER_SETUP.md](docs/MULTI_PROVIDER_SETUP.md)
- 🧪 **Test Script**: `python scripts/test_multi_provider.py`
- 📝 **Example Config**: [config/multi_provider_example.yaml](config/multi_provider_example.yaml)

### Legacy Azure-Only Setup

For backward compatibility, the old Azure-only setup still works:

```bash
$env:AZURE_OPENAI_API_KEY="<your-key>"
$env:AZURE_OPENAI_ENDPOINT="https://<your-resource>.openai.azure.com"
python -m app.main "Research ACME quarterly results and summarize with sources."
```

If your Brave MCP requires auth headers, add them under `headers` in `config/agents.yaml` for the `web_agent` MCP server.
