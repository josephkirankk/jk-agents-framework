# Conversation Memory System

The JK-Agents Framework now includes a powerful conversation memory system that allows agents to maintain context across multiple interactions within the same conversation thread. This feature uses PostgreSQL for reliable, scalable storage of conversation history.

## Overview

The conversation memory system provides:

- **Persistent Conversation Storage**: All user questions and agent responses are stored in PostgreSQL
- **Automatic Context Injection**: Previous conversations are automatically injected into agent system messages
- **Thread-Based Organization**: Conversations are organized by thread ID for isolation
- **Configurable Limits**: Control how many previous conversations to include and context length limits
- **Performance Optimized**: Uses async connection pooling for high performance

## Quick Start

### 1. Install PostgreSQL

**On macOS with Homebrew:**
```bash
brew update
brew install postgresql
brew services start postgresql
```

**Alternative:** Download and install from [postgresql.org](https://www.postgresql.org/download/macosx/)

### 2. Create Database and User

```bash
# Connect to PostgreSQL
psql postgres

# In psql shell:
CREATE DATABASE conversations;
CREATE USER jkagent_user WITH PASSWORD 'securepassword';
GRANT ALL PRIVILEGES ON DATABASE conversations TO jkagent_user;
\q
```

### 3. Set Environment Variables

Add to your shell profile (`.zshrc` or `.bash_profile`):
```bash
export DATABASE_URL="postgresql://jkagent_user:securepassword@localhost:5432/conversations"
```

Or create a `.env` file in your project root:
```env
DATABASE_URL=postgresql://jkagent_user:securepassword@localhost:5432/conversations
```

### 4. Initialize the Database

```bash
python scripts/setup_conversation_db.py
```

This script will:
- Create the database if it doesn't exist
- Set up the required tables and indexes
- Verify the connection is working

### 5. Enable in Configuration

Update your `config/agents.yaml` file:
```yaml
models:
  default: "openai:gpt-4o-mini"

# Enable conversation memory
conversation_memory:
  enabled: true
  max_conversations: 5
  max_context_length: 2000
  prepend_context: false
  cleanup_days: 30

supervisor:
  name: "supervisor"
  # ... rest of supervisor config

agents:
  # ... your agents
```

That's it! Your agents will now maintain conversation memory automatically.

## Configuration Options

The conversation memory system is highly configurable through the `conversation_memory` section in your configuration:

```yaml
conversation_memory:
  enabled: true                    # Enable/disable conversation memory
  database_url: null              # PostgreSQL URL (uses DATABASE_URL env var if null)
  max_conversations: 5             # Max number of recent conversations to include
  max_context_length: 2000         # Max length of conversation context in characters
  pool_size: 10                    # Database connection pool size
  cleanup_days: 30                 # Days to keep conversations (0 = no cleanup)
  prepend_context: false           # If true, add context before system message
```

### Configuration Details

- **`enabled`**: Master switch to enable/disable the feature
- **`database_url`**: PostgreSQL connection string. If not set, uses `DATABASE_URL` environment variable
- **`max_conversations`**: Number of recent conversation pairs to include in context (default: 5)
- **`max_context_length`**: Maximum character length for conversation context to prevent token overflow (default: 2000)
- **`pool_size`**: Number of database connections in the async pool (default: 10)
- **`cleanup_days`**: Automatically delete conversations older than this many days. Set to 0 to disable cleanup (default: 30)
- **`prepend_context`**: Whether to add conversation context before or after the system message (default: false - appends after)

## How It Works

### Storage Format

Conversations are stored as pairs of user questions and assistant responses:

```sql
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    thread_id VARCHAR(255) NOT NULL,
    user_message TEXT NOT NULL,
    assistant_response TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB,
    CONSTRAINT conversations_thread_timestamp_idx 
        UNIQUE (thread_id, timestamp)
);
```

### Context Injection

When an agent receives a new query, the system:

1. Retrieves the most recent conversations for the thread ID
2. Formats them as a readable context:
   ```
   Previous conversation:
   User: What is machine learning?
   Assistant: Machine learning is a subset of artificial intelligence...

   User: Can you give me an example?
   Assistant: Sure! A common example is email spam detection...
   ```
3. Injects this context into the system message

### Thread Management

- Each API request can specify a `thread_id` parameter
- If no thread ID is provided, one is automatically generated
- Conversations are isolated by thread ID
- Supervisor workflows use hierarchical thread IDs for proper isolation

## API Usage

### Direct Agent with Memory

```bash
curl -X POST "http://localhost:8000/worker" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "research_agent",
    "input": "What did we discuss about machine learning?",
    "thread_id": "user_session_123"
  }'
```

### Supervised Multi-Agent with Memory

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Continue our previous analysis",
    "thread_id": "user_session_123"
  }'
```

## Database Management

### Manual Database Setup

If the setup script doesn't work for your environment:

```sql
-- Create database
CREATE DATABASE conversations;

-- Create user
CREATE USER jkagent_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE conversations TO jkagent_user;

-- Connect to conversations database
\c conversations

-- Create table
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    thread_id VARCHAR(255) NOT NULL,
    user_message TEXT NOT NULL,
    assistant_response TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB,
    CONSTRAINT conversations_thread_timestamp_idx 
        UNIQUE (thread_id, timestamp)
);

-- Create indexes
CREATE INDEX idx_conversations_thread_id ON conversations(thread_id);
CREATE INDEX idx_conversations_timestamp ON conversations(timestamp DESC);
CREATE INDEX idx_conversations_thread_timestamp ON conversations(thread_id, timestamp DESC);
```

### Cleanup Old Conversations

The system can automatically clean up old conversations based on the `cleanup_days` setting. You can also run cleanup manually:

```python
import asyncio
from app.memory.conversation_store import get_conversation_store

async def cleanup():
    store = get_conversation_store()
    deleted = await store.cleanup_old_conversations(days_to_keep=30)
    print(f"Deleted {deleted} old conversations")

asyncio.run(cleanup())
```

### Backup and Monitoring

For production use, consider:

1. **Regular backups**:
   ```bash
   pg_dump -U jkagent_user conversations > backup.sql
   ```

2. **Monitoring disk usage**:
   ```sql
   SELECT 
       schemaname,
       tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
   FROM pg_tables 
   WHERE schemaname = 'public';
   ```

3. **Connection monitoring**:
   ```sql
   SELECT count(*) as active_connections 
   FROM pg_stat_activity 
   WHERE datname = 'conversations';
   ```

## Troubleshooting

### Common Issues

**1. Database connection errors**
```
Failed to initialize ConversationStore: could not connect to server
```
- Verify PostgreSQL is running: `brew services list | grep postgresql`
- Check DATABASE_URL format: `postgresql://user:password@host:port/database`
- Ensure database and user exist

**2. Permission errors**
```
permission denied for table conversations
```
- Grant proper permissions: `GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO jkagent_user;`

**3. Memory not working**
```
Conversation memory disabled in configuration
```
- Check `conversation_memory.enabled: true` in config
- Verify DATABASE_URL environment variable is set
- Check logs for initialization errors

**4. Context not appearing**
```
No previous conversation context in agent responses
```
- Verify conversations are being stored (check database)
- Ensure same thread_id is used across requests
- Check `max_conversations` and `max_context_length` settings

### Debug Mode

Enable debug logging to troubleshoot:

```python
import logging
logging.getLogger('app.memory').setLevel(logging.DEBUG)
```

### Performance Tuning

For high-traffic deployments:

1. **Increase connection pool size**:
   ```yaml
   conversation_memory:
     pool_size: 20
   ```

2. **Tune PostgreSQL settings** in `postgresql.conf`:
   ```
   max_connections = 200
   shared_buffers = 256MB
   effective_cache_size = 1GB
   ```

3. **Monitor query performance**:
   ```sql
   SELECT * FROM pg_stat_user_tables WHERE relname = 'conversations';
   ```

## Security Considerations

- Use strong passwords for database users
- Limit database user permissions to only necessary operations
- Consider encrypting sensitive conversation data
- Implement proper network security (firewall, VPN)
- Regular security updates for PostgreSQL
- Monitor database access logs

## Testing

Run the conversation memory tests:

```bash
# Unit tests (no database required)
pytest tests/test_conversation_memory.py -v

# Integration tests (requires database)
export TEST_DATABASE_URL="postgresql://jkagent_user:securepassword@localhost:5432/conversations_test"
pytest tests/test_conversation_memory.py -v -m integration
```

## Limitations

- Maximum context length is limited by your LLM's token limits
- Very long conversations may need periodic cleanup
- Database storage grows with conversation volume
- Thread IDs must be consistent across requests for memory to work

## Future Enhancements

Planned features for future releases:

- Conversation summarization for very long histories  
- Multiple storage backends (Redis, MongoDB)
- Conversation search and filtering
- User-level conversation isolation
- Conversation export/import functionality
- Advanced cleanup strategies

## Example Configuration File

Complete example `config/agents.yaml` with conversation memory:

```yaml
models:
  default: "openai:gpt-4o-mini"

business_context: "You are an AI assistant helping with software development tasks."

# Conversation memory configuration
conversation_memory:
  enabled: true
  max_conversations: 5
  max_context_length: 2000
  prepend_context: false
  cleanup_days: 30
  pool_size: 10

persistence:
  type: "memory"

supervisor:
  name: "supervisor"
  prompt: "You are a supervisor agent that plans and coordinates tasks."

agents:
  - name: "research_agent"
    description: "Handles research and information gathering tasks"
    prompt: "You are a research specialist. Use your tools to find accurate information."
    
  - name: "coding_agent"
    description: "Handles programming and code-related tasks"
    prompt: "You are an expert programmer. Write clean, efficient code."

temperature: 0.0
parallel_tool_calls_enabled: true
```

This configuration enables conversation memory with sensible defaults that work well for most use cases.