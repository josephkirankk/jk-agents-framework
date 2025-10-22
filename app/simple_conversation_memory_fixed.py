#!/usr/bin/env python3
"""
Simple conversation memory system with turn tracking and basic auto-summarization.
Minimal implementation with focus on reliability.
"""

import os
import json
import logging
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class SimpleConversationMemory:
    """Simple in-memory conversation storage with disk persistence and turn tracking."""
    
    def __init__(self, persist_to_disk: bool = True, storage_dir: str = "./simple_memory"):
        self.conversations = {}  # thread_id -> list of messages
        self.persist_to_disk = persist_to_disk
        self.storage_dir = storage_dir
        self._lock = threading.RLock()
        
        if persist_to_disk and not os.path.exists(storage_dir):
            os.makedirs(storage_dir, exist_ok=True)
    
    def add_message(self, thread_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to the conversation history with turn tracking and auto-summarization."""
        with self._lock:
            if thread_id not in self.conversations:
                self.conversations[thread_id] = []
            
            # Determine turn ID based on role
            if role == 'user':
                # Start new turn for user messages
                turn_id = self._get_next_turn_id(thread_id)
            else:
                # Continue current turn for assistant messages
                turn_id = self._get_current_turn_id(thread_id)
            
            # Create message
            message = {
                'role': role,
                'content': content,
                'timestamp': datetime.now().isoformat(),
                'turn_id': turn_id,
                'metadata': metadata or {}
            }
            
            # Add message
            self.conversations[thread_id].append(message)
            
            # Basic auto-summarization to prevent memory bloat
            if len(self.conversations[thread_id]) > 30:  # Trigger at 31+ messages
                self._basic_summarize(thread_id)
            
            # Save to disk if enabled
            if self.persist_to_disk:
                self._save_conversation(thread_id)
            
            log.debug(f"Added {role} message to thread {thread_id} (turn: {turn_id})")
    
    def get_conversation_history(self, thread_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history for a thread."""
        with self._lock:
            messages = self.conversations.get(thread_id, [])
            return messages[-limit:] if limit > 0 else messages
    
    def get_conversation_summary(self, thread_id: str) -> str:
        """Generate a turn-aware summary of the conversation for context."""
        messages = self.get_conversation_history(thread_id, limit=20)
        
        if not messages:
            return "No previous conversation history available."
        
        # Create a turn-aware summary
        summary_parts = ["Previous conversation context:"]
        
        for msg in messages[-10:]:  # Last 10 messages for context
            role = msg['role']
            content = msg['content'][:200]  # Truncate long messages
            if len(msg['content']) > 200:
                content += "..."
            
            # Get turn ID with backward compatibility
            turn_id = msg.get('turn_id', 'Turn-?')
            summary_parts.append(f"[{turn_id}] {role.title()}: {content}")
        
        # Add current turn indicator
        current_turn = self._get_next_turn_id(thread_id)
        summary_parts.append(f"\nCurrent turn: {current_turn}")
        
        return "\n".join(summary_parts)
    
    def has_conversation(self, thread_id: str) -> bool:
        """Check if a conversation exists for the thread."""
        return thread_id in self.conversations and len(self.conversations[thread_id]) > 0
    
    def clear_conversation(self, thread_id: str):
        """Clear a conversation history."""
        with self._lock:
            if thread_id in self.conversations:
                del self.conversations[thread_id]
                
                if self.persist_to_disk:
                    # Remove the file if it exists
                    filepath = os.path.join(self.storage_dir, f"{thread_id}.json")
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        
                log.info(f"Cleared conversation for thread {thread_id}")
    
    def _save_conversation(self, thread_id: str):
        """Save conversation to disk."""
        if not self.persist_to_disk:
            return
            
        try:
            messages = self.conversations.get(thread_id, [])
            if not messages:
                return
                
            storage_path = os.path.join(self.storage_dir, f"{thread_id}.json")
            
            # Simple data structure for storage
            data = {
                'thread_id': thread_id,
                'updated_at': datetime.now().isoformat(),
                'messages': messages
            }
            
            with open(storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            log.debug(f"Saved conversation for thread {thread_id} with {len(messages)} messages")
        except Exception as e:
            log.error(f"Failed to save conversation for thread {thread_id}: {e}")
    
    def _get_next_turn_id(self, thread_id: str) -> str:
        """Get the next turn ID for a new user message."""
        messages = self.conversations.get(thread_id, [])
        
        # Count the number of user messages to determine turn number
        user_count = 0
        for msg in messages:
            if msg['role'] == 'user':
                user_count += 1
        
        return f"Turn-{user_count + 1}"
    
    def _get_current_turn_id(self, thread_id: str) -> str:
        """Get current turn ID for assistant response (matches last user's turn)."""
        messages = self.conversations.get(thread_id, [])
        # Find the last user message's turn_id
        for msg in reversed(messages):
            if msg.get('role') == 'user' and 'turn_id' in msg:
                return msg['turn_id']
        return "Turn-1"  # Fallback for first conversation or missing turn_id
    
    def _basic_summarize(self, thread_id: str):
        """Very basic summarization to prevent memory bloat.
        
        Triggers when conversation exceeds 30 messages.
        Keeps summary + last 10 messages = 11 total messages.
        This allows unlimited conversation turns without memory bloat.
        """
        messages = self.conversations.get(thread_id, [])
        
        # Only summarize if we have more than 30 messages
        if len(messages) <= 30:
            return
        
        # Count non-summary messages for accurate reporting
        non_summary_messages = [m for m in messages if m.get('role') != 'system' or m.get('turn_id') != 'Summary']
        
        # Keep last 10 messages (these are the most recent, critical for context)
        recent_messages = messages[-10:]
        
        # Count how many messages are being summarized
        summarized_count = len(messages) - 10
        
        # Create a comprehensive summary message with metadata
        summary_content = (
            f"CONVERSATION SUMMARY: {summarized_count} earlier messages have been summarized. "
            f"Recent context preserved for continuity."
        )
        
        summary_message = {
            'role': 'system',
            'content': summary_content,
            'timestamp': datetime.now().isoformat(),
            'turn_id': 'Summary',
            'metadata': {
                'type': 'basic_summary',
                'count': summarized_count,
                'summarization_timestamp': datetime.now().isoformat(),
                'original_message_count': len(messages),
                'preserved_message_count': 10
            }
        }
        
        # Replace conversation with summary + recent messages
        # This ensures we maintain 11 messages total (1 summary + 10 recent)
        self.conversations[thread_id] = [summary_message] + recent_messages
        
        log.info(f"Auto-summarization for thread {thread_id}: "
                f"summarized {summarized_count} messages, kept last 10 messages, "
                f"total now: {len(self.conversations[thread_id])} messages")

# Global instance
_global_conversation_memory: Optional[SimpleConversationMemory] = None
_memory_lock = threading.Lock()

def get_conversation_memory() -> SimpleConversationMemory:
    """Get the global conversation memory instance - THREAD SAFE."""
    global _global_conversation_memory
    
    # First check without lock (optimization)
    if _global_conversation_memory is not None:
        return _global_conversation_memory
    
    # Acquire lock for initialization
    with _memory_lock:
        # Double-check after acquiring lock (prevents race condition)
        if _global_conversation_memory is None:
            _global_conversation_memory = SimpleConversationMemory()
            log.info("Initialized simple conversation memory system")
    
    return _global_conversation_memory

def inject_conversation_context(user_input: str, thread_id: str) -> str:
    """
    Enhanced conversation context injection with pre-calculated metadata for supervisor.
    This is called before processing a request to add memory context.
    """
    memory = get_conversation_memory()
    
    if not memory.has_conversation(thread_id):
        # First message in conversation
        return user_input
    
    # Get conversation summary with enhanced metadata
    context_data = get_conversation_context_metadata(thread_id)
    context = context_data['context']
    
    # Inject context with comprehensive metadata into the user input
    enhanced_input = f"""Previous conversation context (words: {context_data['word_count']}, turns: {context_data['turn_count']}):
{context}

Current user input: {user_input}

**IMPORTANT**: Use the [Turn-X] data above when relevant to the current request. Build upon existing data rather than regenerating it.
"""
    
    return enhanced_input.strip()

def get_conversation_context_metadata(thread_id: str) -> dict:
    """
    Get comprehensive conversation context metadata for supervisor planning.
    This provides pre-calculated metrics that the supervisor can use for dynamic decision making.
    """
    memory = get_conversation_memory()
    
    if not memory.has_conversation(thread_id):
        return {
            'word_count': 0,
            'turn_count': 0,
            'message_count': 0,
            'context': '',
            'summarization_recommended': False,
            'has_structured_data': False,
            'memory_size_bytes': 0,
            'data_types': [],
            'last_activity': None
        }
    
    # Get conversation data
    context = memory.get_conversation_summary(thread_id)
    messages = memory.get_conversation_history(thread_id, limit=-1)
    
    # Calculate comprehensive metrics
    import re
    # FIXED: Count words in ALL messages, not just the summary
    # This gives accurate word count for full conversation history
    full_content = " ".join(msg['content'] for msg in messages)
    words = re.findall(r'\b\w+\b', full_content)
    word_count = len(words)
    
    # Count actual turns (not including system messages)
    turn_count = len(set(msg.get('turn_id', 'Turn-?') for msg in messages 
                        if msg.get('turn_id') != 'Summary' and msg.get('role') != 'system'))
    
    # Detect structured data in conversation (use already computed full_content)
    has_json = '{' in full_content and '}' in full_content
    has_arrays = '[' in full_content and ']' in full_content 
    has_code = '```' in full_content
    has_numbers = len(re.findall(r'\d+\.?\d*', full_content)) > 5
    
    has_structured_data = has_json or has_arrays or has_code or has_numbers
    
    # Calculate memory usage
    memory_size = len(json.dumps(messages))
    
    # Determine summarization recommendation
    summarization_recommended = (
        word_count > 2000 or 
        len(messages) > 30 or 
        memory_size > 50000  # 50KB threshold
    )
    
    return {
        'word_count': word_count,
        'turn_count': turn_count, 
        'message_count': len(messages),
        'context': context,
        'summarization_recommended': summarization_recommended,
        'has_structured_data': has_structured_data,
        'memory_size_bytes': memory_size,
        'data_types': _detect_data_types(full_content),
        'last_activity': messages[-1]['timestamp'] if messages else None
    }

def _detect_data_types(content: str) -> list[str]:
    """Detect types of structured data in conversation content."""
    import re
    data_types = []
    
    if '{' in content and '}' in content:
        data_types.append('JSON')
    if '[' in content and ']' in content and ',' in content:
        data_types.append('Arrays')
    if '```' in content:
        data_types.append('Code')
    if len(re.findall(r'\d+\.\d+', content)) > 3:
        data_types.append('Numerical')
    if '|' in content and content.count('|') > 5:
        data_types.append('Tables')
    
    return data_types

def store_conversation_turn(thread_id: str, user_input: str, assistant_response: str, metadata: Optional[Dict[str, Any]] = None):
    """Store a complete conversation turn."""
    try:
        if not thread_id:
            log.error("Cannot store conversation turn: thread_id is empty")
            return
            
        memory = get_conversation_memory()
        
        # Store user message
        memory.add_message(thread_id, 'user', user_input)
        
        # Store assistant response
        memory.add_message(thread_id, 'assistant', assistant_response, metadata)
        
        # Verify storage worked by checking message count
        recent_msgs = memory.get_conversation_history(thread_id, limit=5)
        if recent_msgs:
            log.info(f"Successfully stored conversation turn for thread {thread_id} - {len(recent_msgs)} messages in history")
        else:
            log.warning(f"Conversation stored but no history found for thread {thread_id}")
            
    except Exception as e:
        log.error(f"Failed to store conversation turn: {e}")
        # Re-raise in debug environments but not in production
        if os.environ.get('DEBUG_MEMORY', '').lower() == 'true':
            raise
