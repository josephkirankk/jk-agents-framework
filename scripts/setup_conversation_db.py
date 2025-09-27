#!/usr/bin/env python3
"""
Database setup script for JK-Agents Framework conversation storage.

This script initializes PostgreSQL database tables and indexes
for persistent conversation memory.

Usage:
    python scripts/setup_conversation_db.py [--database-url DATABASE_URL]

Environment Variables:
    DATABASE_URL: PostgreSQL connection URL (e.g., postgresql://user:pass@host:port/db)
    POSTGRES_URL: Alternative name for DATABASE_URL
"""

import asyncio
import argparse
import logging
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.memory.conversation_store import ConversationStore


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_database_url() -> str:
    """
    Get database URL from environment variables or command line.
    
    Returns:
        PostgreSQL database URL
        
    Raises:
        ValueError: If no database URL is found
    """
    # Check multiple environment variable names
    database_url = (
        os.getenv('DATABASE_URL') or 
        os.getenv('POSTGRES_URL') or
        os.getenv('POSTGRESQL_URL')
    )
    
    if not database_url:
        raise ValueError(
            "Database URL not found. Please set DATABASE_URL environment variable "
            "or provide --database-url argument.\n\n"
            "Example: DATABASE_URL='postgresql://user:password@localhost:5432/conversations'"
        )
    
    return database_url


async def create_database_if_not_exists(database_url: str) -> None:
    """
    Create the database if it doesn't exist.
    
    Args:
        database_url: Full database URL
    """
    import asyncpg
    from urllib.parse import urlparse
    
    # Parse the database URL
    parsed = urlparse(database_url)
    db_name = parsed.path.lstrip('/')
    
    # Create connection URL to postgres (default) database
    postgres_url = database_url.replace(f'/{db_name}', '/postgres')
    
    try:
        # Connect to postgres database
        conn = await asyncpg.connect(postgres_url)
        
        # Check if database exists
        result = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )
        
        if not result:
            logger.info(f"Creating database: {db_name}")
            # Note: Cannot use parameters for database name in CREATE DATABASE
            await conn.execute(f'CREATE DATABASE "{db_name}"')
            logger.info(f"Database {db_name} created successfully")
        else:
            logger.info(f"Database {db_name} already exists")
            
        await conn.close()
        
    except Exception as e:
        logger.error(f"Failed to create database: {e}")
        raise


async def setup_conversation_database(database_url: str) -> None:
    """
    Set up the conversation database with tables and indexes.
    
    Args:
        database_url: PostgreSQL database URL
    """
    logger.info("Setting up conversation database...")
    
    try:
        # First, try to create the database if it doesn't exist
        await create_database_if_not_exists(database_url)
        
        # Initialize conversation store (this will create tables)
        store = ConversationStore(database_url)
        await store.initialize()
        
        # Test the connection by counting conversations
        test_count = await store.count_conversations("__test__")
        logger.info(f"Database connection successful (test query returned: {test_count})")
        
        # Close the store
        await store.close()
        
        logger.info("✅ Database setup completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        raise


async def verify_database_setup(database_url: str) -> None:
    """
    Verify that the database is properly set up.
    
    Args:
        database_url: PostgreSQL database URL
    """
    logger.info("Verifying database setup...")
    
    try:
        store = ConversationStore(database_url)
        await store.initialize()
        
        # Test basic operations
        test_thread = "__verification_test__"
        
        # Store a test conversation
        await store.store_conversation(
            thread_id=test_thread,
            user_message="Test user message",
            assistant_response="Test assistant response",
            metadata={"test": True}
        )
        
        # Retrieve conversation
        conversations = await store.get_conversation_history(test_thread, limit=1)
        
        if not conversations:
            raise RuntimeError("Failed to retrieve stored conversation")
        
        if conversations[0].user_message != "Test user message":
            raise RuntimeError("Retrieved conversation does not match stored data")
        
        # Clean up test data
        await store.delete_conversation_history(test_thread)
        
        # Close store
        await store.close()
        
        logger.info("✅ Database verification completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Database verification failed: {e}")
        raise


def print_usage_info():
    """Print helpful usage information."""
    print("\n" + "="*60)
    print("🎉 JK-Agents Framework Conversation Database Setup Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Set the DATABASE_URL environment variable in your shell:")
    print("   export DATABASE_URL='postgresql://user:password@localhost:5432/conversations'")
    print("\n2. Or add it to your .env file:")
    print("   DATABASE_URL=postgresql://user:password@localhost:5432/conversations")
    print("\n3. Start using conversation memory in your agents!")
    print("\n4. Optional: Set up a cron job to clean up old conversations:")
    print("   # Clean conversations older than 30 days")
    print("   python -c \"import asyncio; from app.memory.conversation_store import *; store = get_conversation_store(); asyncio.run(store.cleanup_old_conversations(30))\"")
    print()


async def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(
        description='Setup PostgreSQL database for JK-Agents Framework conversation storage'
    )
    parser.add_argument(
        '--database-url',
        type=str,
        help='PostgreSQL database URL (overrides environment variables)'
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify existing database setup (do not create)'
    )
    parser.add_argument(
        '--skip-verification',
        action='store_true',
        help='Skip verification step after setup'
    )
    
    args = parser.parse_args()
    
    try:
        # Get database URL
        if args.database_url:
            database_url = args.database_url
        else:
            database_url = get_database_url()
        
        logger.info(f"Using database URL: {database_url.split('@')[0]}@***")
        
        if args.verify_only:
            await verify_database_setup(database_url)
        else:
            await setup_conversation_database(database_url)
            
            if not args.skip_verification:
                await verify_database_setup(database_url)
        
        print_usage_info()
        
    except KeyboardInterrupt:
        logger.info("Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())