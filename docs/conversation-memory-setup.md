# Conversation Memory - Quick Setup Guide

This guide will get conversation memory up and running in just a few minutes.

## Prerequisites

- macOS (Darwin)
- Python virtual environment activated
- JK-Agents Framework installed

## Step-by-Step Setup

### 1. Install PostgreSQL

```bash
# Using Homebrew
brew install postgresql
brew services start postgresql
```

### 2. Create Database

```bash
# Connect to PostgreSQL
psql postgres

# Create database and user (copy-paste all lines)
CREATE DATABASE conversations;
CREATE USER jkagent_user WITH PASSWORD 'securepassword';
GRANT ALL PRIVILEGES ON DATABASE conversations TO jkagent_user;
\q
```

### 3. Set Environment Variable

```bash
# Add to your shell profile or run this command
export DATABASE_URL="postgresql://jkagent_user:securepassword@localhost:5432/conversations"

# Or add to .env file in project root
echo 'DATABASE_URL=postgresql://jkagent_user:securepassword@localhost:5432/conversations' >> .env
```

### 4. Initialize Database Tables

```bash
# This installs required packages and sets up tables
source .venv/bin/activate  # Make sure virtual environment is active
python scripts/setup_conversation_db.py
```

You should see:
```
✅ Database setup completed successfully!
✅ Database verification completed successfully!
```

### 5. Enable in Configuration

Edit your `config/agents.yaml` file and add:

```yaml
# Add this section to your config file
conversation_memory:
  enabled: true
  max_conversations: 5
  max_context_length: 2000

# Your existing configuration continues below
models:
  default: "openai:gpt-4o-mini"

supervisor:
  # ... your supervisor config

agents:
  # ... your agents config
```

### 6. Start the API Server

```bash
python -m uvicorn api:app --reload
```

The server will automatically initialize conversation memory on startup. Look for:
```
INFO:api:Conversation memory initialized successfully
```

### 7. Test It Works

Open a new terminal and test with the same thread ID:

```bash
# First request
curl -X POST "http://localhost:8000/worker" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "research_agent", 
    "input": "Hi, my name is John", 
    "thread_id": "test_123"
  }'

# Second request - should remember your name
curl -X POST "http://localhost:8000/worker" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "research_agent", 
    "input": "What is my name?", 
    "thread_id": "test_123"
  }'
```

The agent should remember your name from the previous conversation!

## Troubleshooting

### PostgreSQL Not Running
```bash
brew services start postgresql
# or
postgres -D /usr/local/var/postgres
```

### Permission Errors
```bash
psql conversations -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO jkagent_user;"
```

### Database Connection Issues
- Check DATABASE_URL format: `postgresql://user:password@host:port/database`
- Verify the database exists: `psql -U jkagent_user -d conversations -c "SELECT 1;"`

### Memory Not Working
- Check API server logs for "Conversation memory initialized successfully"
- Verify `conversation_memory.enabled: true` in config
- Use the same thread_id for related conversations

## Next Steps

- Read the full [conversation memory documentation](conversation-memory.md)
- Explore advanced configuration options
- Set up automatic cleanup for production use

That's it! Your JK-Agents now have persistent conversation memory. 🎉