# 📘 MCP Wrapper Server: Dataset Storage & Retrieval

## 1. Overview

We need to **extend the functionality** of the existing **Pydantic Run-Python MCP server** without modifying its code.
The solution is a **wrapper MCP server** built with **FastMCP** that mounts the original Run-Python server and adds **post-processing** + **dataset storage/retrieval**.

---

## 2. Requirements

* Run-Python MCP should remain **untouched**.
* After any dataset generation:

  * Store the **full dataset** in a **SQLite database**.
  * Return only:

    * **Preview (top 5 rows)**
    * **Total count of rows**
    * **Reference ID (UUID)** for later retrieval
* Add a new tool: **`dataset.retrieve(ref_id)`** that allows retrieval of the stored dataset.
* Full datasets should be **saved to JSON files**, not printed to console.
* This wrapper must integrate with a **LangGraph ReAct agent** for usage in AI workflows.

---

## 3. Architecture

```
[Agent / LangGraph ReAct]
        |
        v
[Wrapper MCP Server] --mount--> [Run-Python MCP Server]
        |
        +-- Middleware: post-process tool results
        |      ↳ Store dataset in SQLite
        |      ↳ Return { preview, total_count, ref_id }
        |
        +-- Tool: dataset.retrieve(ref_id)
               ↳ Fetch dataset from SQLite
               ↳ Save to dataset_<ref_id>.json
```

---

## 4. Project Files

### `requirements.txt`

```text
fastmcp>=2.0.0
mcp-run-python>=0.1.0
aiosqlite>=0.18.0
uvicorn>=0.20.0
configparser
langgraph
langchain-mcp-adapters
langchain-openai
```

---

### `config.ini`

```ini
[server]
existing_transport = sse
existing_sse_url = http://127.0.0.1:7000/mcp
existing_stdio_cmd = /path/to/run_python_mcp.py

wrapper_name = run_python_wrapper
mount_prefix = py
listen_transport = sse
listen_host = 127.0.0.1
listen_port = 8000

[database]
path = datasets.db
```

---

### `db_utils.py`

```python
import aiosqlite, json, uuid, asyncio, logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger("dataset.db")

class DatasetStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._inited = False
        self._lock = asyncio.Lock()

    async def init(self):
        async with self._lock:
            if self._inited:
                return
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                CREATE TABLE IF NOT EXISTS datasets (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    metadata TEXT,
                    data TEXT NOT NULL
                )""")
                await db.commit()
            self._inited = True

    async def insert_dataset(self, dataset: Any, metadata: Optional[Dict[str, Any]]=None) -> str:
        await self.init()
        ref_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat() + "Z"
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO datasets (id, created_at, metadata, data) VALUES (?, ?, ?, ?)",
                (ref_id, created_at, json.dumps(metadata or {}), json.dumps(dataset)),
            )
            await db.commit()
        return ref_id

    async def get_dataset(self, ref_id: str) -> Optional[Dict[str, Any]]:
        await self.init()
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute("SELECT id, created_at, metadata, data FROM datasets WHERE id = ?", (ref_id,))
            row = await cur.fetchone()
            if not row: return None
            id_, created_at, meta_json, data_json = row
            return {
                "id": id_,
                "created_at": created_at,
                "metadata": json.loads(meta_json),
                "data": json.loads(data_json),
            }
```

---

### `wrapper_mcp.py`

This wraps the Run-Python MCP, stores datasets, and exposes retrieval.

```python
import asyncio, json, configparser, logging, re
from typing import Any, Dict
from fastmcp import FastMCP, Client, ToolError
from fastmcp.server.middleware import Middleware, MiddlewareContext
from db_utils import DatasetStore

logger = logging.getLogger("wrapper")
logging.basicConfig(level=logging.INFO)

def extract_dataset(result) -> Any:
    sc = getattr(result, "structured_content", None) or {}
    if "dataset" in sc: return sc["dataset"]
    if "data" in sc: return sc["data"]
    try:
        return json.loads(result.text)
    except Exception:
        m = re.search(r"(\[.*\]|\{.*\})", result.text, re.S)
        if m:
            return json.loads(m.group(1))
    return None

class PostProcess(Middleware):
    def __init__(self, store: DatasetStore, prefix: str): self.store, self.prefix = store, prefix
    async def on_call_tool(self, ctx: MiddlewareContext, nxt):
        tool = ctx.message.name or ""
        if not tool.startswith(self.prefix): return await nxt(ctx)
        result = await nxt(ctx)
        dataset = extract_dataset(result)
        if dataset is None: return result
        ref_id = await self.store.insert_dataset(dataset, {"tool": tool})
        rows = dataset if isinstance(dataset, list) else dataset.get("rows", [])
        summary = {"preview": rows[:5], "total_count": len(rows), "ref_id": ref_id}
        result.text, result.structured_content = json.dumps(summary, indent=2), {"dataset_reference": summary}
        return result

async def build_and_run(cfg_file="config.ini"):
    cfg = configparser.ConfigParser(); cfg.read(cfg_file)
    store = DatasetStore(cfg["database"]["path"]); await store.init()
    mcp = FastMCP(cfg["server"]["wrapper_name"])
    client = Client(cfg["server"]["existing_sse_url"])
    proxy = FastMCP.from_client(client)
    mcp.mount(proxy, prefix=cfg["server"]["mount_prefix"])
    mcp.add_middleware(PostProcess(store, cfg["server"]["mount_prefix"]))
    @mcp.tool()
    async def dataset_retrieve(ref_id: str) -> Dict[str, Any]:
        rec = await store.get_dataset(ref_id)
        if not rec: raise ToolError("Not found")
        return rec
    mcp.run(transport=cfg["server"]["listen_transport"],
            host=cfg["server"]["listen_host"],
            port=int(cfg["server"]["listen_port"]))

if __name__ == "__main__":
    asyncio.run(build_and_run())
```

---

### `agent_with_mcp.py`

LangGraph ReAct agent using wrapper.

```python
import asyncio, json, os
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

WRAPPER_URL = os.getenv("WRAPPER_MCP_URL", "http://127.0.0.1:8000/mcp")

SYSTEM_PROMPT = """You are a data generation and analysis agent."""

async def main():
    client = MultiServerMCPClient({
        "wrapper": {"url": WRAPPER_URL, "transport": "streamable_http"}
    })
    tools = await client.get_tools()
    agent = create_react_agent(ChatOpenAI(model="gpt-4.1-mini"), tools, state_modifier=SYSTEM_PROMPT)

    # Generate dataset
    task = "Generate 200 sample electronics orders for India 2024. Return preview, count, ref_id."
    result = await agent.ainvoke({"messages": [{"role": "user", "content": task}]})
    print("\n=== Preview ===\n", result["messages"][-1].content)

    # Extract ref_id
    text = str(result["messages"][-1].content)
    ref_id = None
    try:
        obj = json.loads(text[text.find("{"):text.rfind("}")+1])
        ref_id = obj.get("ref_id") or obj.get("dataset_reference", {}).get("ref_id")
    except: pass

    # Retrieve & save
    if ref_id:
        retrieve_tool = next(t for t in tools if t.name == "dataset_retrieve")
        full = await retrieve_tool.ainvoke({"ref_id": ref_id})
        with open(f"dataset_{ref_id}.json", "w", encoding="utf-8") as f:
            json.dump(full, f, indent=2, ensure_ascii=False)
        print(f"Full dataset saved: dataset_{ref_id}.json")
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 5. Usage

1. Run the wrapper MCP:

   ```bash
   python wrapper_mcp.py --config config.ini
   ```
2. Run the agent:

   ```bash
   export OPENAI_API_KEY=sk-...
   python agent_with_mcp.py
   ```
3. You’ll see:

   * A preview (5 rows + ref_id) printed.
   * Full dataset saved as `dataset_<ref_id>.json`.

---

## 6. Extensions

* Add **CSV/Parquet export tool** inside wrapper.
* Switch to **Postgres** instead of SQLite for scale.
* Run behind **MCP gateway** for auth & RBAC.
* Add **observability** (logging/metrics).

---

✅ This markdown doc gives the dev team everything they need: **requirements, design, configs, code, and usage.**