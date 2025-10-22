# Deep Agents System - Overview and Architecture

**Version:** 1.0  
**Last Updated:** October 2025  
**Status:** Production Ready

---

## Table of Contents

1. [What are Deep Agents?](#what-are-deep-agents)
2. [When to Use Deep Agents](#when-to-use-deep-agents)
3. [System Architecture](#system-architecture)
4. [Key Components](#key-components)
5. [Core Concepts](#core-concepts)

---

## What are Deep Agents?

Deep Agents is an advanced agentic framework integrated into `jk-agents-core` that enables AI agents to handle complex, multi-step tasks through sophisticated planning, context management, and hierarchical task decomposition.

### Foundation

Built on:
- **LangChain**: Tool integration and model abstraction
- **LangGraph**: Stateful agent workflows and checkpointing
- **DeepAgents Package**: Core middleware and subagent functionality (`pip install deepagents`)
- **ChromaDB**: Persistent memory backend

### Key Capabilities

Unlike traditional ReAct agents that operate in a single reasoning loop, Deep Agents provide:

| Feature | Description | Benefit |
|---------|-------------|---------|
| **Task Planning** | TodoList middleware for task decomposition | Break complex tasks into manageable steps |
| **Context Management** | Virtual filesystem (ls, read, write, edit files) | Organize large amounts of information |
| **Hierarchical Decomposition** | Specialized subagents for different tasks | Context isolation and specialization |
| **Long-term Memory** | Optional cross-thread persistence | Maintain knowledge across conversations |
| **Human-in-the-Loop** | Approval workflows for sensitive operations | Safety and control |

---

## When to Use Deep Agents

### Use Deep Agents For:

✅ **Complex Research Tasks**
- Multi-step investigation requiring source synthesis
- Information gathering across multiple domains
- Structured report generation

✅ **Large Context Management**
- Projects with extensive documentation
- Code analysis over large codebases
- Multi-file organization and editing

✅ **Hierarchical Task Decomposition**
- Tasks requiring specialized expertise
- Parallel workstream execution
- Context isolation between subtasks

✅ **Stateful Workflows**
- Long-running conversations with context
- Resume interrupted work
- Track progress across sessions

### Use ReAct Agents For:

❌ **Simple Q&A**
- Direct questions with straightforward answers
- Single tool call scenarios

❌ **Speed-Critical Operations**
- Quick responses needed
- Minimal reasoning steps

❌ **Simple Tool Execution**
- Basic function calls
- No planning required

---

## System Architecture

### High-Level Flow

```
User Request
    ↓
Supervisor Agent (Planning)
    ↓
Deep Agent (Main)
├── TodoList Middleware (Task Planning)
├── Filesystem Middleware (Context Management)
├── SubAgent Middleware (Task Delegation)
└── Tools & MCP Servers (External Actions)
    ↓
Subagents (Optional, Isolated Context)
├── web-researcher
├── data-analyzer
└── synthesizer
    ↓
Memory & Persistence
├── ChromaDB Checkpointer (Conversation State)
├── Virtual Filesystem (Session Files)
└── LangGraph Store (Long-term Memory)
```

### Detailed Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     API Request                              │
│  POST /v1/supervisor/run                                     │
│  {                                                           │
│    "user_message": "Research quantum computing",             │
│    "thread_id": "session-123"                                │
│  }                                                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Load Checkpoint (if exists)                     │
│  • Restore conversation history                              │
│  • Restore virtual filesystem                                │
│  • Restore todo list state                                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Supervisor Agent                            │
│  • Analyzes user request                                     │
│  • Creates execution plan (JSON)                             │
│  • Routes to appropriate agent(s)                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Deep Agent Execution                        │
│                                                              │
│  ┌────────────────────────────────────────────────┐         │
│  │         Agent Core (LangGraph)                  │         │
│  │  • Message processing                           │         │
│  │  • Reasoning loop                               │         │
│  │  • Tool selection                               │         │
│  └────────────────────────────────────────────────┘         │
│                       │                                      │
│  ┌────────────────────┼────────────────────────────┐        │
│  │  Middleware Layer  │                             │        │
│  │                    ▼                             │        │
│  │  ┌──────────────────────────────────────┐       │        │
│  │  │   TodoList Middleware                 │       │        │
│  │  │   Tools: add_todo, mark_done, list    │       │        │
│  │  └──────────────────────────────────────┘       │        │
│  │                                                  │        │
│  │  ┌──────────────────────────────────────┐       │        │
│  │  │   Filesystem Middleware               │       │        │
│  │  │   Tools: ls, read, write, edit        │       │        │
│  │  └──────────────────────────────────────┘       │        │
│  │                                                  │        │
│  │  ┌──────────────────────────────────────┐       │        │
│  │  │   SubAgent Middleware                 │       │        │
│  │  │   Delegates to specialized agents     │       │        │
│  │  └──────────────────────────────────────┘       │        │
│  └──────────────────────────────────────────────────┘       │
│                       │                                      │
│  ┌────────────────────┼────────────────────────────┐        │
│  │  External Tools    │                             │        │
│  │                    ▼                             │        │
│  │  ┌──────────────────────────────────────┐       │        │
│  │  │   MCP Servers                         │       │        │
│  │  │   • google_search (Serper)            │       │        │
│  │  │   • scrape (Web scraping)             │       │        │
│  │  │   • filesystem (MCP)                  │       │        │
│  │  └──────────────────────────────────────┘       │        │
│  │                                                  │        │
│  │  ┌──────────────────────────────────────┐       │        │
│  │  │   Python Function Tools               │       │        │
│  │  │   • Custom analysis functions         │       │        │
│  │  │   • Data processing tools             │       │        │
│  │  └──────────────────────────────────────┘       │        │
│  └──────────────────────────────────────────────────┘       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Subagent Execution (If Delegated)               │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │web-researcher│  │data-analyzer │  │ synthesizer  │      │
│  │              │  │              │  │              │      │
│  │ Isolated     │  │ Isolated     │  │ Isolated     │      │
│  │ Context      │  │ Context      │  │ Context      │      │
│  │              │  │              │  │              │      │
│  │ Own tools    │  │ Own tools    │  │ Own tools    │      │
│  │ Own model    │  │ Own model    │  │ Own model    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                  │              │
│         └─────────────────┴──────────────────┘              │
│                           │                                 │
│                  Only final results                         │
│                  return to main agent                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                Save Checkpoint                               │
│  • Store updated conversation                                │
│  • Store virtual filesystem state                            │
│  • Store todo list state                                     │
│  • Store execution metadata                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Return Response                            │
│  {                                                           │
│    "messages": [...],                                        │
│    "files": {"/research.md": "..."},                         │
│    "todos": [...]                                            │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Components

### 1. DeepAgentAdapter (`app/deep_agent_adapter.py`)

**Purpose:** Bridge between jk-agents-core configuration and DeepAgents package

**Responsibilities:**
- Parse `deep_agent_config` from YAML
- Initialize DeepAgents middleware
- Build subagent configurations
- Configure long-term memory store
- Provide unified invoke/stream interface

**Key Methods:**
```python
class DeepAgentAdapter:
    def __init__(model, tools, system_prompt, deep_config, checkpointer)
    def invoke(state, config) -> Dict[str, Any]
    def stream(state, config) -> Iterator
    def _build_subagents(subagents_config) -> List[Dict]
```

### 2. Configuration Models (`app/config.py`)

**DeepAgentConfig:**
```python
class DeepAgentConfig(BaseModel):
    enabled: bool = True
    enable_filesystem: bool = True       # Virtual filesystem
    enable_todolist: bool = True         # Task planning
    enable_longterm_memory: bool = False # Cross-thread memory
    subagents: List[SubAgentConfig] = []
    interrupt_on: Optional[Dict] = None  # Human approval
    store_config: Optional[Dict] = None
```

**SubAgentConfig:**
```python
class SubAgentConfig(BaseModel):
    name: str                            # Unique identifier
    description: str                     # For routing decisions
    system_prompt: str                   # Subagent instructions
    model: Optional[str] = None          # Override parent model
    tools: Optional[List[str]] = []      # Tool subset
```

### 3. Agent Builder Integration (`app/agent_builder.py`)

**Agent Type Detection:**
```python
agent_type = agent_cfg.agent_type  # "react", "normal", or "deep"

if agent_type == "deep":
    agent = create_deep_agent_from_config(
        model=model,
        tools=tools,
        system_prompt=prompt,
        agent_config=agent_cfg,
        checkpointer=checkpointer,
    )
```

### 4. Memory System

**ChromaDB Checkpointer (`app/memory/chromadb_checkpointer.py`):**
- Stores conversation state
- Persists virtual filesystem
- Thread-scoped isolation
- Automatic serialization/deserialization

**LangGraph Store (Optional):**
- Cross-thread memory
- `/memories/` prefix for long-term files
- Multiple backend options (InMemory, ChromaDB, PostgreSQL)

---

## Core Concepts

### 1. Middleware Architecture

Deep Agents use middleware to extend capabilities without polluting the reasoning loop.

#### TodoList Middleware

**Tools Provided:**
- `add_todo(task: str)` - Add task to list
- `mark_todo_done(task_id: int)` - Mark complete
- `list_todos()` - View pending tasks
- `clear_todos()` - Clear completed

**Usage Pattern:**
```
Agent: "I'll break this down into steps"
→ add_todo("Step 1: Research topic")
→ add_todo("Step 2: Analyze findings")
→ add_todo("Step 3: Write summary")
→ list_todos()  # Shows: [Task 1: Pending, Task 2: Pending, Task 3: Pending]
→ mark_todo_done(1)
→ list_todos()  # Shows: [Task 1: Done, Task 2: Pending, Task 3: Pending]
```

#### Filesystem Middleware

**Tools Provided:**
- `ls(path: str = "/")` - List directory contents
- `read_file(path: str)` - Read file content
- `write_file(path: str, content: str)` - Create/overwrite file
- `edit_file(path: str, old_content: str, new_content: str)` - Modify file

**Usage Pattern:**
```
Agent: "I'll organize my research"
→ write_file("/research_notes.md", "# Research Notes\n...")
→ write_file("/analysis.txt", "Key findings: ...")
→ ls("/")  # Shows: ["research_notes.md", "analysis.txt"]
→ read_file("/research_notes.md")  # Retrieves content
→ edit_file("/research_notes.md", "old text", "new text")
```

**File Persistence:**
- Regular files: Stored in LangGraph state (thread-scoped)
- Memory files: Files with `/memories/` prefix (cross-thread, if enabled)

#### SubAgent Middleware

**Purpose:** Hierarchical task delegation with context isolation

**How It Works:**
1. Main agent identifies specialized task
2. Delegates to subagent by name
3. Subagent executes in isolated context
4. Only final result returns to main agent
5. Intermediate reasoning hidden from main context

**Benefits:**
- **Context Isolation**: Subagent work doesn't pollute main context
- **Specialization**: Different subagents for different expertise
- **Parallel Execution**: Multiple subagents can work simultaneously
- **Flexibility**: Each subagent can use different models

### 2. Context Management Strategy

**Problem:** Traditional agents hit context limits with large tasks

**Deep Agents Solution:**

```
Traditional Agent (Context Overflow):
├── User Message (100 tokens)
├── Tool Call 1 + Result (500 tokens)
├── Tool Call 2 + Result (800 tokens)
├── Tool Call 3 + Result (1200 tokens)
├── Tool Call 4 + Result (1500 tokens)
└── ... (CONTEXT LIMIT EXCEEDED)

Deep Agent (Context Managed):
├── User Message (100 tokens)
├── write_file("/research.md", large_data)  (50 tokens)
├── Tool Call 1 + Result summary (200 tokens)
├── Delegate to subagent (returns summary) (150 tokens)
├── read_file("/research.md") when needed (50 tokens)
└── Final synthesis (300 tokens)
Total: ~850 tokens (sustainable)
```

### 3. Subagent Delegation Pattern

**Main Agent → Subagent Flow:**

```python
# Main Agent prompt
"""
You have subagents:
- web-researcher: For gathering online information
- data-analyzer: For statistical analysis
"""

# User asks complex question
"Research AI trends and analyze market data"

# Main agent delegates
1. Call web-researcher: "Research recent AI trends"
   └── Subagent searches, analyzes, returns summary
   
2. Call data-analyzer: "Analyze AI market growth statistics"
   └── Subagent processes data, returns insights
   
3. Main agent synthesizes both results
   └── Creates final comprehensive report
```

**Context Isolation:**
- Web-researcher context: Only sees web search results
- Data-analyzer context: Only sees data analysis
- Main agent context: Only sees final summaries

### 4. Memory Hierarchy

```
┌─────────────────────────────────────────────────────────┐
│                  Ephemeral (Current Turn)                │
│  • Working memory                                        │
│  • Temporary variables                                   │
│  • Tool outputs                                          │
│  Lifetime: Single invocation                             │
└─────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│              Session Memory (Thread State)               │
│  • Conversation history                                  │
│  • Virtual filesystem (/file.txt)                        │
│  • Todo list state                                       │
│  Lifetime: Until thread expires                          │
│  Storage: ChromaDB checkpointer                          │
└─────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│            Long-term Memory (Cross-Thread)               │
│  • User preferences (/memories/prefs.txt)                │
│  • Knowledge base (/memories/kb/)                        │
│  • Persistent facts                                      │
│  Lifetime: Permanent (until deleted)                     │
│  Storage: LangGraph Store                                │
└─────────────────────────────────────────────────────────┘
```

---

## Next Steps

For detailed information, see:
- **[Configuration Guide](./31_deep_agents_configuration.md)** - YAML configuration and setup
- **[Usage Examples](./32_deep_agents_examples.md)** - Code examples and patterns
- **[Advanced Features](./33_deep_agents_advanced.md)** - Best practices and optimization
- **[API Reference](./34_deep_agents_api.md)** - Detailed API documentation

---

**Related Documentation:**
- [Agent System](./10_module_agent_system.md)
- [Memory System](./10_module_memory_system.md)
- [MCP Tools](./10_module_mcp_tools.md)
