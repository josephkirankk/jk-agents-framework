"""
Smart Context Search Tool

Efficiently searches conversation history for relevant context using:
1. Keyword matching for immediate relevance
2. Semantic similarity for related concepts  
3. Contextual cue detection ("these", "them", "those")
4. Vector search when available (ChromaDB backend)
"""

import logging
import re
from typing import Optional, List, Dict, Any, Tuple
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

log = logging.getLogger(__name__)


class ContextSearcher:
    """Smart context search with multiple relevance strategies."""
    
    def __init__(self, thread_id: str, checkpointer):
        self.thread_id = thread_id
        self.checkpointer = checkpointer
    
    def detect_context_query_type(self, query: str) -> str:
        """
        Detect what type of context the user is asking for.
        
        Returns:
            str: Type of context query (items, numbers, calculations, general)
        """
        query_lower = query.lower()
        
        # Reference to specific items/entities
        if any(word in query_lower for word in ['these', 'them', 'those', 'items', 'ones']):
            if any(word in query_lower for word in ['count', 'number', 'how many']):
                return 'count_items'
            elif any(word in query_lower for word in ['calculate', 'sum', 'total', 'average']):
                return 'calculate_items'
            else:
                return 'reference_items'
        
        # Looking for specific data mentioned before
        if any(word in query_lower for word in ['mentioned', 'discussed', 'said', 'told']):
            return 'recall_information'
        
        return 'general'
    
    def extract_entities_from_messages(self, messages: List[Any]) -> List[Dict[str, Any]]:
        """
        Extract structured entities (IDs, names, numbers) from messages.
        
        Returns:
            List of extracted entities with metadata
        """
        entities = []
        
        for i, msg in enumerate(messages):
            content = ""
            msg_type = "unknown"
            
            if hasattr(msg, 'type') and hasattr(msg, 'content'):
                msg_type = msg.type
                content = str(msg.content)
            elif isinstance(msg, dict):
                msg_type = msg.get('role', msg.get('type', 'unknown'))
                content = str(msg.get('content', ''))
            
            # Skip system messages for entity extraction
            if msg_type == 'system':
                continue
            
            # Extract IDs (numbers, alphanumeric IDs)
            id_patterns = [
                r'\bID:?\s*(\d+)',
                r'\b(\d{4,})\b',  # 4+ digit numbers (likely IDs)
                r'\b([A-Z]{2,}\d+)\b',  # Alphanumeric IDs
            ]
            
            for pattern in id_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    entities.append({
                        'type': 'id',
                        'value': match.group(1),
                        'context': content[max(0, match.start()-50):match.end()+50],
                        'message_index': i,
                        'message_type': msg_type
                    })
            
            # Extract lists (numbered items, bullet points)
            list_patterns = [
                r'^\s*\d+\.?\s+(.+)$',  # Numbered lists
                r'^\s*[•\-\*]\s+(.+)$',  # Bullet points
            ]
            
            for pattern in list_patterns:
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    entities.append({
                        'type': 'list_item',
                        'value': match.group(1).strip(),
                        'context': match.group(0),
                        'message_index': i,
                        'message_type': msg_type
                    })
            
            # Extract key phrases (titles, names in quotes or special formatting)
            if any(indicator in content for indicator in ['Title:', 'Name:', '**', '*']):
                # Extract text in bold or after labels
                phrase_patterns = [
                    r'\*\*([^*]+)\*\*',  # Bold text
                    r'Title:\s*([^\n]+)',  # After "Title:"
                    r'Name:\s*([^\n]+)',   # After "Name:"
                ]
                
                for pattern in phrase_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        entities.append({
                            'type': 'key_phrase',
                            'value': match.group(1).strip(),
                            'context': content[max(0, match.start()-30):match.end()+30],
                            'message_index': i,
                            'message_type': msg_type
                        })
        
        return entities
    
    def search_relevant_context(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Search for relevant context using multiple strategies.
        
        Args:
            query: What the user is looking for
            max_results: Maximum number of context items to return
            
        Returns:
            Dict with search results and metadata
        """
        try:
            config: RunnableConfig = {"configurable": {"thread_id": self.thread_id}}
            
            # Get conversation history
            messages = []
            if hasattr(self.checkpointer, 'get_tuple'):
                checkpoint_tuple = self.checkpointer.get_tuple(config)
                if checkpoint_tuple:
                    checkpoint_data = checkpoint_tuple[1] if isinstance(checkpoint_tuple, tuple) else checkpoint_tuple.checkpoint
                    if checkpoint_data and 'channel_values' in checkpoint_data:
                        messages = checkpoint_data.get('channel_values', {}).get('messages', [])
            
            if not messages:
                return {
                    'found': False,
                    'query_type': 'none',
                    'context_items': [],
                    'message': 'No previous conversation found.'
                }
            
            # Detect query type
            query_type = self.detect_context_query_type(query)
            
            # Extract entities from messages
            entities = self.extract_entities_from_messages(messages)
            
            # Filter entities based on query type and relevance
            relevant_entities = []
            query_lower = query.lower()
            
            for entity in entities:
                relevance_score = 0
                
                # Score based on query type alignment
                if query_type == 'count_items' or query_type == 'reference_items':
                    if entity['type'] in ['id', 'list_item', 'key_phrase']:
                        relevance_score += 2
                
                # Score based on keyword matching in context
                context_lower = entity['context'].lower()
                query_words = query_lower.split()
                for word in query_words:
                    if len(word) > 2 and word in context_lower:
                        relevance_score += 1
                
                # Score based on entity type relevance
                if entity['type'] == 'id' and any(word in query_lower for word in ['id', 'number', 'item']):
                    relevance_score += 1
                
                if entity['type'] == 'list_item' and any(word in query_lower for word in ['list', 'items', 'these', 'them']):
                    relevance_score += 1
                
                if relevance_score > 0:
                    entity['relevance_score'] = relevance_score
                    relevant_entities.append(entity)
            
            # Sort by relevance and message recency (more recent = higher score)
            relevant_entities.sort(key=lambda x: (x['relevance_score'], x['message_index']), reverse=True)
            
            # Take top results
            top_entities = relevant_entities[:max_results]
            
            return {
                'found': len(top_entities) > 0,
                'query_type': query_type,
                'context_items': top_entities,
                'total_entities': len(entities),
                'relevant_count': len(relevant_entities)
            }
            
        except Exception as e:
            log.error(f"Error in smart context search: {e}")
            return {
                'found': False,
                'query_type': 'error',
                'context_items': [],
                'message': f'Search error: {str(e)}'
            }


def create_smart_context_tool(thread_id: str, checkpointer) -> callable:
    """
    Create a smart context search tool for a specific conversation thread.
    
    Args:
        thread_id: Thread ID for the conversation
        checkpointer: Checkpointer instance for memory access
        
    Returns:
        Smart context search tool function
    """
    searcher = ContextSearcher(thread_id, checkpointer)
    
    @tool
    def get_conversation_context(query: str) -> str:
        """
        Intelligently search for relevant context from previous conversation.
        
        Use this when users refer to "these", "them", "those", or ask about
        something mentioned earlier. Performs targeted search instead of
        loading full conversation history.
        
        Args:
            query: What you're looking for (e.g., "the items mentioned", "those numbers", "what we discussed about pricing")
            
        Returns:
            Relevant context formatted for easy understanding
        """
        try:
            results = searcher.search_relevant_context(query)
            
            if not results['found']:
                return "No relevant context found for that query. Could you be more specific about what you're referring to?"
            
            # Format results for the agent
            context_lines = [f"Found {len(results['context_items'])} relevant items from previous conversation:"]
            context_lines.append("")
            
            for i, item in enumerate(results['context_items'], 1):
                item_type = item['type'].replace('_', ' ').title()
                value = item['value']
                context = item['context'].strip()
                
                context_lines.append(f"{i}. {item_type}: {value}")
                if len(context) > 100:
                    context_lines.append(f"   Context: {context[:97]}...")
                else:
                    context_lines.append(f"   Context: {context}")
                context_lines.append("")
            
            # Add query type info for debugging
            context_lines.append(f"Query type detected: {results['query_type']}")
            
            result = "\n".join(context_lines)
            log.info(f"Smart context search returned {len(results['context_items'])} items for query: {query}")
            return result
            
        except Exception as e:
            log.error(f"Error in context search tool: {e}")
            return f"Error searching conversation context: {str(e)}"
    
    # Set tool name
    get_conversation_context.name = "get_conversation_context"
    return get_conversation_context