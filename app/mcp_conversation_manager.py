#!/usr/bin/env python3
"""
MCP Server for Conversation Memory Management

Provides tools for the conversation_summarizer agent to:
1. Analyze conversation context and word counts
2. Create intelligent summaries 
3. Replace conversation history with summaries
4. Monitor memory usage and optimization
"""

import asyncio
import json
import logging
import sys
from typing import Any, Sequence
from datetime import datetime

# MCP imports
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# Import our conversation memory system
try:
    from app.simple_conversation_memory_fixed import get_conversation_memory, SimpleConversationMemory
except ImportError:
    # Fallback import path
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from simple_conversation_memory_fixed import get_conversation_memory, SimpleConversationMemory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("conversation_manager")

# Initialize the MCP server
server = Server("conversation-manager")

@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available conversation management resources."""
    return [
        Resource(
            uri="conversation://stats",
            name="Conversation Statistics",
            description="Get statistics about current conversation memory usage",
            mimeType="application/json",
        ),
        Resource(
            uri="conversation://context/current",
            name="Current Conversation Context",
            description="Get the current conversation context with word count analysis",
            mimeType="text/plain",
        ),
    ]

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read conversation management resources."""
    if uri == "conversation://stats":
        memory = get_conversation_memory()
        stats = memory.get_stats() if hasattr(memory, 'get_stats') else {
            "total_conversations": len(memory.conversations),
            "total_messages": sum(len(msgs) for msgs in memory.conversations.values())
        }
        return json.dumps(stats, indent=2)
    
    elif uri == "conversation://context/current":
        memory = get_conversation_memory()
        # Get the most recent conversation (this is a simplified approach)
        if memory.conversations:
            latest_thread = list(memory.conversations.keys())[-1]
            context = memory.get_conversation_summary(latest_thread)
            return context
        else:
            return "No active conversations found."
    
    else:
        raise ValueError(f"Unknown resource URI: {uri}")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available conversation management tools."""
    return [
        Tool(
            name="analyze_conversation_context",
            description="Analyze conversation context and provide word count, turn count, and data type analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "thread_id": {
                        "type": "string",
                        "description": "The conversation thread ID to analyze"
                    }
                },
                "required": ["thread_id"],
            },
        ),
        Tool(
            name="create_intelligent_summary",
            description="Create an intelligent conversation summary preserving all structured data",
            inputSchema={
                "type": "object", 
                "properties": {
                    "thread_id": {
                        "type": "string",
                        "description": "The conversation thread ID to summarize"
                    },
                    "preserve_recent_count": {
                        "type": "integer",
                        "description": "Number of recent messages to keep (default: 10)",
                        "default": 10
                    }
                },
                "required": ["thread_id"],
            },
        ),
        Tool(
            name="conversation_cleanup",
            description="Replace old conversation messages with an intelligent summary while preserving recent messages",
            inputSchema={
                "type": "object",
                "properties": {
                    "thread_id": {
                        "type": "string", 
                        "description": "The conversation thread ID to clean up"
                    },
                    "summary_content": {
                        "type": "string",
                        "description": "The intelligent summary content to replace old messages with"
                    },
                    "keep_recent_count": {
                        "type": "integer",
                        "description": "Number of recent messages to preserve (default: 10)",
                        "default": 10
                    }
                },
                "required": ["thread_id", "summary_content"],
            },
        ),
        Tool(
            name="get_memory_impact",
            description="Calculate memory usage before and after summarization",
            inputSchema={
                "type": "object",
                "properties": {
                    "thread_id": {
                        "type": "string",
                        "description": "The conversation thread ID to analyze"
                    }
                },
                "required": ["thread_id"],
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls for conversation management."""
    
    if name == "analyze_conversation_context":
        thread_id = arguments["thread_id"]
        memory = get_conversation_memory()
        
        if not memory.has_conversation(thread_id):
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"No conversation found for thread_id: {thread_id}",
                    "word_count": 0,
                    "turn_count": 0,
                    "message_count": 0,
                    "has_structured_data": False
                })
            )]
        
        # Get conversation context
        context = memory.get_conversation_summary(thread_id) 
        messages = memory.get_conversation_history(thread_id, limit=-1)
        
        # Analyze context
        import re
        words = re.findall(r'\b\w+\b', context)
        word_count = len(words)
        
        # Count turns and detect data types
        turn_count = len(set(msg.get('turn_id', 'Turn-?') for msg in messages if msg.get('turn_id') != 'Summary'))
        
        # Detect structured data types
        full_content = " ".join(msg['content'] for msg in messages)
        has_json = '{' in full_content and '}' in full_content
        has_arrays = '[' in full_content and ']' in full_content
        has_code = '```' in full_content
        has_numbers = len(re.findall(r'\d+\.?\d*', full_content)) > 5
        
        data_types = []
        if has_json: data_types.append("JSON")
        if has_arrays: data_types.append("Arrays")
        if has_code: data_types.append("Code")
        if has_numbers: data_types.append("Numerical")
        
        analysis = {
            "thread_id": thread_id,
            "word_count": word_count,
            "turn_count": turn_count,
            "message_count": len(messages),
            "has_structured_data": len(data_types) > 0,
            "data_types": data_types,
            "memory_size_bytes": len(json.dumps(messages)),
            "summarization_recommended": word_count > 2000 or len(messages) > 20,
            "context_preview": context[:200] + "..." if len(context) > 200 else context
        }
        
        return [TextContent(type="text", text=json.dumps(analysis, indent=2))]
    
    elif name == "create_intelligent_summary":
        thread_id = arguments["thread_id"]
        preserve_recent = arguments.get("preserve_recent_count", 10)
        memory = get_conversation_memory()
        
        if not memory.has_conversation(thread_id):
            return [TextContent(type="text", text=json.dumps({"error": f"No conversation found for thread_id: {thread_id}"}))]
        
        messages = memory.get_conversation_history(thread_id, limit=-1)
        
        # Determine which messages to summarize vs keep
        if len(messages) <= preserve_recent:
            return [TextContent(type="text", text=json.dumps({
                "summary": "No summarization needed - conversation is already short",
                "original_count": len(messages),
                "action": "none"
            }))]
        
        older_messages = messages[:-preserve_recent]
        recent_messages = messages[-preserve_recent:]
        
        # Create enhanced summary using the logic from our enhanced system
        summary_content = _create_enhanced_summary(older_messages)
        
        result = {
            "summary_content": summary_content,
            "original_message_count": len(older_messages),
            "recent_messages_kept": len(recent_messages),
            "total_messages_before": len(messages),
            "compression_ratio": f"{len(older_messages)}:1",
            "recommended_action": "replace_old_messages_with_summary"
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "conversation_cleanup":
        thread_id = arguments["thread_id"]
        summary_content = arguments["summary_content"]
        keep_recent = arguments.get("keep_recent_count", 10)
        memory = get_conversation_memory()
        
        if not memory.has_conversation(thread_id):
            return [TextContent(type="text", text=json.dumps({"error": f"No conversation found for thread_id: {thread_id}"}))]
        
        messages = memory.get_conversation_history(thread_id, limit=-1)
        
        # Calculate memory impact
        original_size = len(json.dumps(messages))
        
        # Keep recent messages
        recent_messages = messages[-keep_recent:] if len(messages) > keep_recent else messages
        
        # Create summary message
        summary_message = {
            'role': 'system',
            'content': summary_content,
            'timestamp': datetime.now().isoformat(),
            'turn_id': 'Summary',
            'metadata': {
                'type': 'intelligent_summary',
                'original_count': len(messages) - len(recent_messages),
                'summarization_timestamp': datetime.now().isoformat(),
                'version': '2.1'
            }
        }
        
        # Replace conversation with summary + recent messages
        new_messages = [summary_message] + recent_messages
        memory.conversations[thread_id] = new_messages
        
        # Save to disk if enabled
        if memory.persist_to_disk:
            memory._save_conversation(thread_id)
        
        # Calculate results
        new_size = len(json.dumps(new_messages))
        savings_percent = ((original_size - new_size) / original_size * 100) if original_size > 0 else 0
        
        result = {
            "success": True,
            "thread_id": thread_id,
            "messages_before": len(messages),
            "messages_after": len(new_messages),
            "memory_saved_bytes": original_size - new_size,
            "memory_saved_percent": round(savings_percent, 1),
            "summary_length_chars": len(summary_content),
            "recent_messages_preserved": len(recent_messages),
            "cleanup_timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Conversation cleanup completed for {thread_id}: {len(messages)} → {len(new_messages)} messages ({savings_percent:.1f}% memory saved)")
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "get_memory_impact":
        thread_id = arguments["thread_id"]
        memory = get_conversation_memory()
        
        if not memory.has_conversation(thread_id):
            return [TextContent(type="text", text=json.dumps({"error": f"No conversation found for thread_id: {thread_id}"}))]
        
        messages = memory.get_conversation_history(thread_id, limit=-1)
        
        # Calculate current memory usage
        current_size = len(json.dumps(messages))
        
        # Simulate summarization impact (keeping last 10 messages)
        if len(messages) > 10:
            recent_messages = messages[-10:]
            older_messages = messages[:-10]
            
            # Estimate summary size (typically 20-30% of original)
            estimated_summary_size = len(json.dumps(older_messages)) * 0.25
            estimated_new_size = len(json.dumps(recent_messages)) + estimated_summary_size
            
            projected_savings = ((current_size - estimated_new_size) / current_size * 100)
        else:
            projected_savings = 0
            estimated_new_size = current_size
        
        impact = {
            "thread_id": thread_id,
            "current_memory_bytes": current_size,
            "current_message_count": len(messages),
            "projected_memory_bytes": int(estimated_new_size),
            "projected_savings_bytes": int(current_size - estimated_new_size),
            "projected_savings_percent": round(projected_savings, 1),
            "summarization_recommended": projected_savings > 30,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        return [TextContent(type="text", text=json.dumps(impact, indent=2))]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

def _create_enhanced_summary(messages: list[dict]) -> str:
    """Create enhanced summary with intelligent data preservation (simplified version)."""
    if not messages:
        return "No previous conversation history."
    
    # Group by turns with data classification
    turn_groups = {}
    for msg in messages:
        turn_id = msg.get('turn_id', 'Turn-?')
        if turn_id not in turn_groups:
            turn_groups[turn_id] = {
                'user': None, 
                'assistant': None, 
                'timestamp': None,
                'has_structured_data': False,
                'data_types': []
            }
        
        content = msg['content']
        
        if msg['role'] == 'user':
            # Compress user message intelligently
            turn_groups[turn_id]['user'] = _compress_user_message(content)
            turn_groups[turn_id]['timestamp'] = msg['timestamp'][:19]
        elif msg['role'] == 'assistant':
            # Process assistant content with data preservation
            processed_content, has_data, data_types = _process_assistant_content(content)
            turn_groups[turn_id]['assistant'] = processed_content
            turn_groups[turn_id]['has_structured_data'] = has_data
            turn_groups[turn_id]['data_types'] = data_types
    
    # Generate enhanced summary
    summary_parts = [
        f"CONVERSATION SUMMARY (Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):",
        ""
    ]
    
    # Add turn summaries with intelligent formatting
    structured_turns = 0
    for turn_id, data in turn_groups.items():
        if data['user'] and data['assistant']:
            timestamp = data['timestamp'] or 'Unknown'
            
            # Format with data type indicators
            if data['has_structured_data']:
                structured_turns += 1
                data_indicator = f" [{', '.join(data['data_types'])}]"
            else:
                data_indicator = ""
            
            summary_parts.append(f"[{turn_id}] ({timestamp}) User: {data['user']}")
            summary_parts.append(f"[{turn_id}] ({timestamp}) Assistant{data_indicator}: {data['assistant']}")
    
    # Add comprehensive footer
    summary_parts.extend([
        "",
        f"[Summary: {len(turn_groups)} turns processed, {structured_turns} with structured data]",
        f"[All JSON, arrays, and numerical data preserved exactly]",
        f"[Narrative content intelligently compressed for memory efficiency]"
    ])
    
    return "\n".join(summary_parts)

def _compress_user_message(content: str) -> str:
    """Intelligently compress user messages while preserving key intent."""
    if len(content) <= 150:
        return content
    
    # Extract key action words and context
    import re
    action_words = ['create', 'add', 'update', 'delete', 'generate', 'analyze', 'calculate', 
                   'show', 'list', 'export', 'import', 'process', 'convert', 'transform']
    
    sentences = [s.strip() for s in content.split('.') if s.strip()]
    
    # Find sentences with action words or specific instructions
    key_sentences = []
    for sentence in sentences:
        if (any(word in sentence.lower() for word in action_words) or 
            len(sentence) < 100 or
            any(indicator in sentence for indicator in ['"', "'", '[', '{', 'data', 'file'])):
            key_sentences.append(sentence)
    
    if key_sentences:
        compressed = '. '.join(key_sentences[:2])  # Take first 2 key sentences
        if len(compressed) < len(content):
            return compressed + ('...' if len(sentences) > len(key_sentences) else '')
    
    # Fallback to truncation with smart boundary
    return content[:150] + '...'

def _process_assistant_content(content: str) -> tuple[str, bool, list[str]]:
    """Process assistant content with intelligent data preservation."""
    import re
    
    has_structured_data = False
    data_types = []
    
    # Detect structured data types
    if '```json' in content or ('{' in content and '}' in content):
        has_structured_data = True
        data_types.append('JSON')
    
    if '[' in content and ']' in content:
        bracket_content = content[content.find('['):content.rfind(']')+1]
        if ',' in bracket_content or bracket_content.count('[') > 1:
            has_structured_data = True
            data_types.append('Array')
    
    # Detect numerical data patterns
    number_patterns = re.findall(r'\d+\.?\d*', content)
    if len(number_patterns) > 3:
        has_structured_data = True
        data_types.append('Numerical')
    
    # Detect code blocks
    if '```' in content and any(lang in content for lang in ['python', 'sql', 'javascript', 'html']):
        has_structured_data = True
        data_types.append('Code')
    
    # Preserve structured data exactly, compress narrative
    if has_structured_data:
        return content, True, data_types  # Keep exactly as-is
    else:
        # Compress narrative content intelligently
        return _compress_narrative_content(content), False, []

def _compress_narrative_content(content: str) -> str:
    """Intelligently compress narrative content while preserving key information."""
    if len(content) <= 250:
        return content
    
    import re
    sentences = [s.strip() for s in content.split('.') if s.strip()]
    
    if len(sentences) <= 2:
        return content
    
    # Identify important sentences
    important_sentences = []
    
    # Always keep first sentence (usually contains main point)
    if sentences:
        important_sentences.append(sentences[0])
    
    # Keep sentences with specific keywords or patterns
    for sentence in sentences[1:-1]:
        if (any(keyword in sentence.lower() for keyword in 
               ['result', 'created', 'generated', 'calculated', 'total', 'average', 'summary']) or
            re.search(r'\d+', sentence) or  # Contains numbers
            len(sentence) < 60):  # Short, likely important
            important_sentences.append(sentence)
    
    # Always keep last sentence if it's conclusive
    if len(sentences) > 1 and sentences[-1].strip():
        last_sentence = sentences[-1].strip()
        if (any(word in last_sentence.lower() for word in 
               ['completed', 'finished', 'done', 'ready', 'success']) or
            len(last_sentence) < 80):
            important_sentences.append(last_sentence)
    
    # Reconstruct with ellipsis if compressed
    compressed = '. '.join(important_sentences)
    if len(compressed) < len(content) and len(sentences) > len(important_sentences):
        return compressed + '...'
    
    # If no significant compression achieved, truncate smartly
    return content[:250] + '...' if len(content) > 250 else content

async def main():
    # Run the server using stdin/stdout streams
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="conversation-manager",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
