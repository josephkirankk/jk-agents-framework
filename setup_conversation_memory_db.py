#!/usr/bin/env python3
"""
Setup script for conversation memory database.

This script creates a PostgreSQL database for conversation memory storage.
"""

import asyncio
import asyncpg
import sys
import os


async def setup_database():
    """Set up the conversation memory database."""
    
    # Database configuration
    db_name = "jk_agents_memory"
    db_user = os.getenv('USER', 'postgres')
    db_host = "localhost"
    db_port = 5432
    
    # Connection URL for creating database
    admin_url = f"postgresql://{db_user}@{db_host}:{db_port}/postgres"
    db_url = f"postgresql://{db_user}@{db_host}:{db_port}/{db_name}"
    
    try:
        # Connect to postgres database to create our database
        print(f"Connecting to PostgreSQL as {db_user}...")
        admin_conn = await asyncpg.connect(admin_url)
        
        # Check if database exists
        result = await admin_conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )
        
        if result:
            print(f"✅ Database '{db_name}' already exists")
        else:
            # Create database
            await admin_conn.execute(f'CREATE DATABASE "{db_name}"')
            print(f"✅ Created database '{db_name}'")
        
        await admin_conn.close()
        
        # Connect to our new database and create tables
        print(f"Setting up tables in '{db_name}'...")
        db_conn = await asyncpg.connect(db_url)
        
        # Create conversations table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS conversations (
            id SERIAL PRIMARY KEY,
            thread_id VARCHAR(255) NOT NULL,
            user_message TEXT NOT NULL,
            assistant_response TEXT NOT NULL,
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            metadata JSONB,
            
            -- Indexes for efficient querying
            CONSTRAINT conversations_thread_timestamp_idx 
                UNIQUE (thread_id, timestamp)
        );

        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_conversations_thread_id 
            ON conversations(thread_id);
        CREATE INDEX IF NOT EXISTS idx_conversations_timestamp 
            ON conversations(timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_conversations_thread_timestamp 
            ON conversations(thread_id, timestamp DESC);
        """
        
        await db_conn.execute(create_table_sql)
        print("✅ Created conversations table and indexes")
        
        await db_conn.close()
        
        print(f"""
🎉 Database setup complete!

Configuration for your application:
  Database URL: {db_url}
  
This has been added to your config file. The application will now be able to:
  ✅ Store conversation history per thread
  ✅ Retrieve conversation context for memory enhancement
  ✅ Log detailed memory transactions with actual content

To test the setup, restart your application and make an API call.
The logs will now include actual message content and retrieved context!
""")
        
        return db_url
        
    except asyncpg.exceptions.InvalidCatalogNameError:
        print("❌ Could not connect to PostgreSQL. Make sure PostgreSQL is running:")
        print("   brew services start postgresql")
        return None
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return None


if __name__ == "__main__":
    db_url = asyncio.run(setup_database())
    
    if db_url:
        # Update the config file with the correct database URL
        config_file = "config/python_exec_agent_working.yaml"
        
        # Read the config
        with open(config_file, 'r') as f:
            config_content = f.read()
        
        # Replace the database URL
        updated_content = config_content.replace(
            'database_url: "postgresql://localhost/jk_agents_memory"',
            f'database_url: "{db_url}"'
        )
        
        # Write back the config
        with open(config_file, 'w') as f:
            f.write(updated_content)
        
        print(f"✅ Updated {config_file} with correct database URL")
        sys.exit(0)
    else:
        sys.exit(1)