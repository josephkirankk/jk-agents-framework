"""
Conversation tracking module for multi-turn conversations.

This module provides utilities for tracking conversations across turns.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

log = logging.getLogger("conversation_tracker")

class ConversationTracker:
    """Tracks multi-turn conversation state."""
    
    def __init__(self):
        """Initialize the conversation tracker."""
        self.conversations: Dict[str, Dict[str, Any]] = {}
        
    def start_conversation(self, thread_id: str) -> None:
        """Start tracking a new conversation."""
        if thread_id not in self.conversations:
            self.conversations[thread_id] = {
                "turns": 0,
                "started_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "messages": []
            }
            log.info(f"Started new conversation with thread_id: {thread_id}")
    
    def add_turn(self, thread_id: str, user_input: str, response: str) -> None:
        """Add a turn to an existing conversation."""
        if thread_id not in self.conversations:
            self.start_conversation(thread_id)
        
        self.conversations[thread_id]["turns"] += 1
        self.conversations[thread_id]["last_updated"] = datetime.now().isoformat()
        self.conversations[thread_id]["messages"].append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        self.conversations[thread_id]["messages"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        log.info(f"Added turn to conversation {thread_id} (now {self.conversations[thread_id]['turns']} turns)")
    
    def get_conversation(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get the full conversation history."""
        return self.conversations.get(thread_id)
    
    def get_message_history(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get the message history for a conversation."""
        if thread_id in self.conversations:
            return self.conversations[thread_id].get("messages", [])
        return []
    
    def get_turn_count(self, thread_id: str) -> int:
        """Get the number of turns in a conversation."""
        if thread_id in self.conversations:
            return self.conversations[thread_id].get("turns", 0)
        return 0
    
    def clear_conversation(self, thread_id: str) -> bool:
        """Clear a conversation from the tracker."""
        if thread_id in self.conversations:
            del self.conversations[thread_id]
            log.info(f"Cleared conversation {thread_id}")
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about tracked conversations."""
        return {
            "active_conversations": len(self.conversations),
            "total_turns": sum(conv["turns"] for conv in self.conversations.values()),
            "conversations": {
                thread_id: {
                    "turns": conv["turns"],
                    "started_at": conv["started_at"],
                    "last_updated": conv["last_updated"]
                } for thread_id, conv in self.conversations.items()
            }
        }
