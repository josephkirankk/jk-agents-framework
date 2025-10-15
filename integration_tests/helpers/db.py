"""
Database helper for integration tests.
Provides real database operations - NO MOCKING.
"""

import sqlite3
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class TestDB:
    """
    Test database for integration tests.
    Uses real SQLite database with automatic cleanup.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize test database.
        
        Args:
            db_path: Path to SQLite database. If None, creates temp database.
        """
        if db_path is None:
            db_path = Path(f"test_db_{uuid.uuid4().hex[:8]}.db")
        
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._tables_created = set()
    
    def prepare_schema(self):
        """Create test database schema."""
        # Jobs table for workflow testing
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                status TEXT DEFAULT 'pending',
                input TEXT,
                result_text TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._tables_created.add("jobs")
        
        # Conversation history table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        self._tables_created.add("conversations")
        
        # Agent execution logs table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                action TEXT NOT NULL,
                input_data TEXT,
                output_data TEXT,
                status TEXT DEFAULT 'success',
                error_message TEXT,
                duration_ms INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._tables_created.add("agent_logs")
        
        self.conn.commit()
    
    def create_job(self, data: Dict[str, Any]) -> str:
        """
        Create a test job.
        
        Args:
            data: Job data with 'input' and optional 'metadata'
            
        Returns:
            Created job_id
        """
        job_id = str(uuid.uuid4())
        import json
        
        self.cursor.execute("""
            INSERT INTO jobs (job_id, status, input, metadata)
            VALUES (?, ?, ?, ?)
        """, (
            job_id,
            'pending',
            data.get('input', ''),
            json.dumps(data.get('metadata', {}))
        ))
        self.conn.commit()
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job data or None if not found
        """
        self.cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        row = self.cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def update_job_status(self, job_id: str, status: str, result_text: Optional[str] = None):
        """
        Update job status and result.
        
        Args:
            job_id: Job identifier
            status: New status
            result_text: Optional result text
        """
        if result_text:
            self.cursor.execute("""
                UPDATE jobs 
                SET status = ?, result_text = ?, updated_at = CURRENT_TIMESTAMP
                WHERE job_id = ?
            """, (status, result_text, job_id))
        else:
            self.cursor.execute("""
                UPDATE jobs 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE job_id = ?
            """, (status, job_id))
        
        self.conn.commit()
    
    def trigger_processing(self, job_id: str):
        """
        Mark job for processing (simulates job trigger).
        
        Args:
            job_id: Job identifier
        """
        self.update_job_status(job_id, 'processing')
    
    def add_conversation_turn(self, thread_id: str, role: str, content: str, 
                             metadata: Optional[Dict] = None):
        """
        Add conversation turn to history.
        
        Args:
            thread_id: Conversation thread ID
            role: Role (user, assistant, system)
            content: Message content
            metadata: Optional metadata
        """
        import json
        
        self.cursor.execute("""
            INSERT INTO conversations (thread_id, role, content, metadata)
            VALUES (?, ?, ?, ?)
        """, (
            thread_id,
            role,
            content,
            json.dumps(metadata) if metadata else None
        ))
        self.conn.commit()
    
    def get_conversation_history(self, thread_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get conversation history for thread.
        
        Args:
            thread_id: Conversation thread ID
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of conversation turns
        """
        self.cursor.execute("""
            SELECT * FROM conversations
            WHERE thread_id = ?
            ORDER BY timestamp ASC
            LIMIT ?
        """, (thread_id, limit))
        
        return [dict(row) for row in self.cursor.fetchall()]
    
    def log_agent_execution(self, agent_name: str, action: str, 
                           input_data: Any, output_data: Any,
                           status: str = 'success', error_message: Optional[str] = None,
                           duration_ms: Optional[int] = None):
        """
        Log agent execution for testing.
        
        Args:
            agent_name: Name of agent
            action: Action performed
            input_data: Input data
            output_data: Output data
            status: Execution status
            error_message: Error message if failed
            duration_ms: Duration in milliseconds
        """
        import json
        
        self.cursor.execute("""
            INSERT INTO agent_logs 
            (agent_name, action, input_data, output_data, status, error_message, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            agent_name,
            action,
            json.dumps(input_data) if input_data else None,
            json.dumps(output_data) if output_data else None,
            status,
            error_message,
            duration_ms
        ))
        self.conn.commit()
    
    def get_agent_logs(self, agent_name: Optional[str] = None, 
                       limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get agent execution logs.
        
        Args:
            agent_name: Optional filter by agent name
            limit: Maximum number of logs to retrieve
            
        Returns:
            List of agent logs
        """
        if agent_name:
            self.cursor.execute("""
                SELECT * FROM agent_logs
                WHERE agent_name = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (agent_name, limit))
        else:
            self.cursor.execute("""
                SELECT * FROM agent_logs
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
        
        return [dict(row) for row in self.cursor.fetchall()]
    
    def clear_table(self, table_name: str):
        """Clear all data from a table."""
        if table_name in self._tables_created:
            self.cursor.execute(f"DELETE FROM {table_name}")
            self.conn.commit()
    
    def teardown_schema(self):
        """Drop all test tables and cleanup."""
        for table in self._tables_created:
            try:
                self.cursor.execute(f"DROP TABLE IF EXISTS {table}")
            except Exception as e:
                print(f"Warning: Failed to drop table {table}: {e}")
        
        self.conn.commit()
        self.conn.close()
        
        # Delete database file
        if self.db_path.exists():
            try:
                self.db_path.unlink()
            except Exception as e:
                print(f"Warning: Failed to delete database {self.db_path}: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.teardown_schema()
