"""
PostgreSQL-based conversation storage for JK-Agents Framework.

This module provides persistent conversation memory storage using PostgreSQL
with async connection pooling for high performance and scalability.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from contextlib import asynccontextmanager

import asyncpg
from pydantic import BaseModel

from .transaction_logger import get_memory_logger


logger = logging.getLogger(__name__)


class ConversationEntry(BaseModel):
    """Model for a single conversation entry (user question + assistant response)."""
    thread_id: str
    user_message: str
    assistant_response: str
    timestamp: datetime
    metadata: Optional[Dict] = None


class ConversationStore:
    """
    PostgreSQL-based conversation storage with async connection pooling.
    
    This class manages conversation history persistence and retrieval
    using PostgreSQL for reliable, scalable storage.
    """

    def __init__(self, database_url: str, pool_size: int = 10):
        """
        Initialize the conversation store.
        
        Args:
            database_url: PostgreSQL connection URL
            pool_size: Maximum number of database connections in the pool
        """
        self.database_url = database_url
        self.pool_size = pool_size
        self._pool: Optional[asyncpg.Pool] = None
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the connection pool and create tables if needed."""
        if self._pool is not None:
            return

        async with self._lock:
            if self._pool is not None:
                return

            try:
                # Create connection pool
                self._pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=1,
                    max_size=self.pool_size,
                    command_timeout=30.0
                )
                
                # Ensure tables exist
                await self._create_tables()
                logger.info("ConversationStore initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize ConversationStore: {e}")
                raise

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def _create_tables(self) -> None:
        """Create conversation tables if they don't exist."""
        if not self._pool:
            raise RuntimeError("Connection pool not initialized")

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

        async with self._pool.acquire() as conn:
            await conn.execute(create_table_sql)

    @asynccontextmanager
    async def _get_connection(self):
        """Context manager to get a database connection from the pool."""
        if not self._pool:
            await self.initialize()
        
        async with self._pool.acquire() as conn:
            yield conn

    async def store_conversation(
        self,
        thread_id: str,
        user_message: str,
        assistant_response: str,
        metadata: Optional[Dict] = None,
        timestamp: Optional[datetime] = None,
        app_config = None
    ) -> None:
        """
        Store a conversation entry.
        
        Args:
            thread_id: Unique identifier for the conversation thread
            user_message: The user's question or input
            assistant_response: The agent's response
            metadata: Optional metadata dictionary
            timestamp: Optional timestamp (defaults to now)
            app_config: Optional app configuration for logging settings
        """
        import json
        
        # Log the transaction
        try:
            memory_logger = get_memory_logger()
            from .transaction_logger import prepare_content_for_logging
            
            # Get logging settings from app config or use defaults
            include_content = True  # Default to include content
            max_content_length = 1000  # Default limit
            
            if app_config and hasattr(app_config, 'memory_logging'):
                include_content = app_config.memory_logging.include_content
                max_content_length = app_config.memory_logging.max_content_length
            
            log_data = {
                'has_metadata': metadata is not None,
                'timestamp': timestamp.isoformat() if timestamp else None,
                'operation_source': 'conversation_store'
            }
            
            # Add user message content
            user_content = prepare_content_for_logging(user_message, include_content, max_content_length)
            log_data.update({f'user_message_{k}': v for k, v in user_content.items()})
            
            # Add assistant response content
            assistant_content = prepare_content_for_logging(assistant_response, include_content, max_content_length)
            log_data.update({f'assistant_response_{k}': v for k, v in assistant_content.items()})
            
            # Add metadata if present and content logging is enabled
            if metadata and include_content:
                log_data['metadata'] = metadata
            elif metadata:
                log_data['metadata_keys'] = list(metadata.keys())
            
            memory_logger.log_transaction(thread_id, 'STORE_CONVERSATION', log_data)
        except Exception as e:
            # Never let logging break the main functionality
            logger.warning(f"Failed to log STORE_CONVERSATION for thread {thread_id}: {e}")
        
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # Serialize metadata to JSON if provided
        metadata_json = json.dumps(metadata) if metadata is not None else None

        insert_sql = """
        INSERT INTO conversations (thread_id, user_message, assistant_response, timestamp, metadata)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (thread_id, timestamp) 
        DO UPDATE SET 
            user_message = EXCLUDED.user_message,
            assistant_response = EXCLUDED.assistant_response,
            metadata = EXCLUDED.metadata
        """

        try:
            async with self._get_connection() as conn:
                await conn.execute(
                    insert_sql,
                    thread_id,
                    user_message,
                    assistant_response,
                    timestamp,
                    metadata_json
                )
                logger.debug(f"Stored conversation for thread {thread_id}")
                
        except Exception as e:
            logger.error(f"Failed to store conversation for thread {thread_id}: {e}")
            raise

    async def get_conversation_history(
        self,
        thread_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[ConversationEntry]:
        """
        Retrieve conversation history for a thread.
        
        Args:
            thread_id: Thread identifier
            limit: Maximum number of entries to return (default 10)
            offset: Number of entries to skip (default 0)
            
        Returns:
            List of ConversationEntry objects in chronological order
        """
        # Log the retrieval
        try:
            memory_logger = get_memory_logger()
            memory_logger.log_transaction(thread_id, 'GET_CONVERSATION_HISTORY', {
                'limit': limit,
                'offset': offset,
                'retrieval_type': 'history'
            })
        except Exception as e:
            logger.warning(f"Failed to log GET_CONVERSATION_HISTORY for thread {thread_id}: {e}")
        
        select_sql = """
        SELECT thread_id, user_message, assistant_response, timestamp, metadata
        FROM conversations
        WHERE thread_id = $1
        ORDER BY timestamp ASC
        LIMIT $2 OFFSET $3
        """

        try:
            async with self._get_connection() as conn:
                rows = await conn.fetch(select_sql, thread_id, limit, offset)
                
                import json
                return [
                    ConversationEntry(
                        thread_id=row['thread_id'],
                        user_message=row['user_message'],
                        assistant_response=row['assistant_response'],
                        timestamp=row['timestamp'],
                        metadata=json.loads(row['metadata']) if row['metadata'] else None
                    )
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"Failed to retrieve conversation history for thread {thread_id}: {e}")
            raise

    async def get_recent_conversations(
        self,
        thread_id: str,
        limit: int = 5
    ) -> List[ConversationEntry]:
        """
        Get the most recent conversations for a thread.
        
        Args:
            thread_id: Thread identifier
            limit: Maximum number of recent entries (default 5)
            
        Returns:
            List of recent ConversationEntry objects in chronological order
        """
        # Log the retrieval
        try:
            memory_logger = get_memory_logger()
            memory_logger.log_transaction(thread_id, 'GET_RECENT_CONVERSATIONS', {
                'limit': limit,
                'retrieval_type': 'recent'
            })
        except Exception as e:
            logger.warning(f"Failed to log GET_RECENT_CONVERSATIONS for thread {thread_id}: {e}")
        
        select_sql = """
        SELECT thread_id, user_message, assistant_response, timestamp, metadata
        FROM conversations
        WHERE thread_id = $1
        ORDER BY timestamp DESC
        LIMIT $2
        """

        try:
            async with self._get_connection() as conn:
                rows = await conn.fetch(select_sql, thread_id, limit)
                
                import json
                # Reverse to get chronological order (oldest to newest)
                conversations = [
                    ConversationEntry(
                        thread_id=row['thread_id'],
                        user_message=row['user_message'],
                        assistant_response=row['assistant_response'],
                        timestamp=row['timestamp'],
                        metadata=json.loads(row['metadata']) if row['metadata'] else None
                    )
                    for row in reversed(rows)
                ]
                
                return conversations
                
        except Exception as e:
            logger.error(f"Failed to retrieve recent conversations for thread {thread_id}: {e}")
            raise

    async def count_conversations(self, thread_id: str) -> int:
        """
        Count total conversations for a thread.
        
        Args:
            thread_id: Thread identifier
            
        Returns:
            Total number of conversation entries
        """
        # Log the count operation
        try:
            memory_logger = get_memory_logger()
            memory_logger.log_transaction(thread_id, 'COUNT_CONVERSATIONS', {
                'operation_type': 'count'
            })
        except Exception as e:
            logger.warning(f"Failed to log COUNT_CONVERSATIONS for thread {thread_id}: {e}")
        
        count_sql = """
        SELECT COUNT(*) FROM conversations WHERE thread_id = $1
        """

        try:
            async with self._get_connection() as conn:
                count = await conn.fetchval(count_sql, thread_id)
                return count or 0
                
        except Exception as e:
            logger.error(f"Failed to count conversations for thread {thread_id}: {e}")
            raise

    async def delete_conversation_history(self, thread_id: str) -> int:
        """
        Delete all conversation history for a thread.
        
        Args:
            thread_id: Thread identifier
            
        Returns:
            Number of deleted entries
        """
        delete_sql = """
        DELETE FROM conversations WHERE thread_id = $1
        """

        try:
            async with self._get_connection() as conn:
                result = await conn.execute(delete_sql, thread_id)
                # Extract number from "DELETE X" result
                deleted_count = int(result.split()[-1]) if result.split()[-1].isdigit() else 0
                logger.info(f"Deleted {deleted_count} conversations for thread {thread_id}")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Failed to delete conversations for thread {thread_id}: {e}")
            raise

    async def cleanup_old_conversations(
        self,
        days_to_keep: int = 30,
        batch_size: int = 1000
    ) -> int:
        """
        Clean up conversations older than specified days.
        
        Args:
            days_to_keep: Number of days to keep (default 30)
            batch_size: Batch size for deletion (default 1000)
            
        Returns:
            Total number of deleted conversations
        """
        cleanup_sql = """
        DELETE FROM conversations 
        WHERE timestamp < NOW() - INTERVAL '%s days'
        """ % days_to_keep

        try:
            async with self._get_connection() as conn:
                result = await conn.execute(cleanup_sql)
                deleted_count = int(result.split()[-1]) if result.split()[-1].isdigit() else 0
                logger.info(f"Cleaned up {deleted_count} old conversations (older than {days_to_keep} days)")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Failed to cleanup old conversations: {e}")
            raise


# Global singleton instance
_conversation_store: Optional[ConversationStore] = None


def get_conversation_store() -> ConversationStore:
    """
    Get the global conversation store instance.
    
    Returns:
        ConversationStore instance
        
    Raises:
        RuntimeError: If store hasn't been initialized
    """
    global _conversation_store
    if _conversation_store is None:
        raise RuntimeError("ConversationStore not initialized. Call initialize_conversation_store() first.")
    return _conversation_store


async def initialize_conversation_store(database_url: str, pool_size: int = 10) -> ConversationStore:
    """
    Initialize the global conversation store.
    
    Args:
        database_url: PostgreSQL connection URL
        pool_size: Connection pool size
        
    Returns:
        ConversationStore instance
    """
    global _conversation_store
    if _conversation_store is None:
        _conversation_store = ConversationStore(database_url, pool_size)
        await _conversation_store.initialize()
    return _conversation_store


async def close_conversation_store() -> None:
    """Close the global conversation store."""
    global _conversation_store
    if _conversation_store:
        await _conversation_store.close()
        _conversation_store = None