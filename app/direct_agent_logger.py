"""
Direct Agent Logging Utility

This module provides logging functionality for direct agent calls,
similar to the supervisor agent logging system.
"""

from __future__ import annotations
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

log = logging.getLogger("direct_agent_logger")


class DirectAgentLogger:
    """Logger for direct agent execution with request/response tracking."""
    
    def __init__(self, agent_name: str, user_input: str, business_context: str = ""):
        """
        Initialize the logger with basic information.
        
        Args:
            agent_name: Name of the agent being executed
            user_input: User's input/request
            business_context: Business context for the agent
        """
        self.agent_name = agent_name
        self.user_input = user_input
        self.business_context = business_context
        self.log_file_path: Optional[Path] = None
        self.start_time = datetime.now()
        
        # Initialize log file
        self._initialize_log_file()
        
        # Write initial log header
        self._write_log_header()
    
    def _initialize_log_file(self):
        """Initialize the log file with timestamped name at repo root."""
        try:
            ts = self.start_time.strftime("%Y%m%d%H%M%S")
            repo_root = Path(__file__).resolve().parents[1]
            self.log_file_path = repo_root / f"direct_agentlog_{ts}.log"
        except Exception as e:
            log.debug("Failed to initialize log file: %s", e)
            self.log_file_path = None
    
    def _safe_write(self, lines: List[str]):
        """Safely write lines to the log file."""
        if not self.log_file_path:
            return
        try:
            with self.log_file_path.open("a", encoding="utf-8") as f:
                for line in lines:
                    f.write(line)
                    if not line.endswith("\n"):
                        f.write("\n")
        except Exception as e:
            log.debug("Log file write failed: %s", e)
    
    def _write_log_header(self):
        """Write the initial log header."""
        self._safe_write([
            "=== jk-agents direct run log ===",
            f"Started: {self.start_time.isoformat(timespec='seconds')}",
            f"Agent: {self.agent_name}",
            f"User input: {self.user_input}",
            f"Business context: {self.business_context or '(none)'}",
            "",
        ])
    
    def _extract_usage(self, message: Any) -> Dict[str, int]:
        """Extract usage information from a message object."""
        usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        try:
            # Handle different message formats
            if hasattr(message, "usage_metadata"):
                um = message.usage_metadata
                if hasattr(um, "input_tokens"):
                    usage["input_tokens"] = int(um.input_tokens or 0)
                if hasattr(um, "output_tokens"):
                    usage["output_tokens"] = int(um.output_tokens or 0)
                usage["total_tokens"] = usage["input_tokens"] + usage["output_tokens"]
                return usage
            
            # Dict-shaped message
            if isinstance(message, dict):
                um = message.get("usage_metadata") or message.get("usage")
                if isinstance(um, dict):
                    usage.update({
                        "input_tokens": int(um.get("input_tokens", 0) or 0),
                        "output_tokens": int(um.get("output_tokens", 0) or 0),
                    })
                    usage["total_tokens"] = (
                        usage["input_tokens"] + usage["output_tokens"]
                    )
        except Exception:
            pass
        return usage
    
    def log_agent_request(
        self, 
        compiled_agent: Any, 
        system_context: str, 
        user_task: str,
        file_info: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Log the agent request details.
        
        Args:
            compiled_agent: The compiled agent object
            system_context: System context for the agent
            user_task: The user task/input
            file_info: Optional file information for multimodal requests
        """
        model_id = getattr(compiled_agent, "_model_id", "unknown")
        rendered_prompt = getattr(compiled_agent, "_rendered_prompt", "(none)")
        
        log_lines = [
            f"--- Direct Agent Request (agent={self.agent_name}) ---",
            f"Model: {model_id}",
            f"Agent Prompt: {rendered_prompt}",
            f"System Context: {system_context}",
            f"User: {user_task}",
        ]
        
        # Add file information if present
        if file_info:
            log_lines.append("Files:")
            for info in file_info:
                filename = info.get("filename", "unknown")
                mime_type = info.get("mime_type", "unknown")
                purpose = info.get("purpose", "unknown")
                log_lines.append(f"  - {filename} ({mime_type}, purpose: {purpose})")
        
        log_lines.append("")
        self._safe_write(log_lines)
    
    def _extract_tool_calls(self, messages: List[Any]) -> List[Dict[str, Any]]:
        """Extract tool calls and results from messages."""
        tool_calls = []

        for msg in messages:
            msg_type = getattr(msg, 'type', None)

            # Check for AIMessage with tool_calls
            if msg_type == 'ai' and hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    # Handle different tool call formats
                    if hasattr(tool_call, 'name'):
                        name = tool_call.name
                    elif isinstance(tool_call, dict):
                        name = tool_call.get('name', 'unknown')
                    else:
                        name = 'unknown'

                    if hasattr(tool_call, 'id'):
                        call_id = tool_call.id
                    elif isinstance(tool_call, dict):
                        call_id = tool_call.get('id', 'unknown')
                    else:
                        call_id = 'unknown'

                    if hasattr(tool_call, 'args'):
                        args = tool_call.args
                    elif isinstance(tool_call, dict):
                        args = tool_call.get('args', {})
                    else:
                        args = {}

                    call_info = {
                        "type": "tool_call",
                        "name": name,
                        "id": call_id,
                        "args": args
                    }
                    tool_calls.append(call_info)

            # Check for ToolMessage with results
            elif msg_type == 'tool':
                tool_id = getattr(msg, 'tool_call_id', 'unknown')
                content = getattr(msg, 'content', '')
                name = getattr(msg, 'name', 'unknown')

                # Find matching tool call and add result
                for call in tool_calls:
                    if call.get("id") == tool_id:
                        call["result"] = content
                        if call["name"] == 'unknown' and name != 'unknown':
                            call["name"] = name
                        break
                else:
                    # Tool result without matching call
                    tool_calls.append({
                        "type": "tool_result",
                        "name": name,
                        "id": tool_id,
                        "result": content
                    })

        return tool_calls

    def log_agent_response(self, response_text: str, raw_output: Dict[str, Any]):
        """
        Log the agent response details.

        Args:
            response_text: The response text from the agent
            raw_output: Raw output from the agent execution
        """
        # Extract usage information
        usage_info = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        msgs = raw_output.get("messages", [])
        if msgs:
            last_msg = msgs[-1]
            usage_info = self._extract_usage(last_msg)

        # Extract tool calls
        tool_calls = self._extract_tool_calls(msgs) if msgs else []

        log_lines = [
            f"--- Direct Agent Response (agent={self.agent_name}) ---",
            response_text or "(empty)",
            "",
        ]

        # Add tool calls section if any were found
        if tool_calls:
            log_lines.extend([
                "--- Tool Calls ---",
            ])
            for i, call in enumerate(tool_calls, 1):
                if call["type"] == "tool_call":
                    args_str = self._format_args_compact(call.get("args", {}))
                    log_lines.append(f"{i}. {call['name']}({args_str})")
                    if "result" in call:
                        result_str = str(call["result"])[:100]
                        if len(str(call["result"])) > 100:
                            result_str += "..."
                        log_lines.append(f"   → {result_str}")
                elif call["type"] == "tool_result":
                    result_str = str(call["result"])[:100]
                    if len(str(call["result"])) > 100:
                        result_str += "..."
                    log_lines.append(f"{i}. Tool Result [{call['id']}]: {result_str}")
            log_lines.append("")

        log_lines.extend([
            f"--- Usage Information ---",
            f"Input tokens: {usage_info['input_tokens']}",
            f"Output tokens: {usage_info['output_tokens']}",
            f"Total tokens: {usage_info['total_tokens']}",
            "",
        ])

        self._safe_write(log_lines)

    def _format_args_compact(self, args: Dict[str, Any]) -> str:
        """Format tool arguments in a compact way."""
        if not args:
            return ""

        formatted_args = []
        for key, value in args.items():
            if isinstance(value, str):
                # Truncate long strings
                if len(value) > 50:
                    value_str = f'"{value[:47]}..."'
                else:
                    value_str = f'"{value}"'
            else:
                value_str = str(value)
            formatted_args.append(f"{key}={value_str}")

        return ", ".join(formatted_args)
    
    def log_execution_summary(self, success: bool, error_message: str = ""):
        """
        Log execution summary at the end.
        
        Args:
            success: Whether the execution was successful
            error_message: Error message if execution failed
        """
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        log_lines = [
            "--- Execution Summary ---",
            f"Status: {'SUCCESS' if success else 'FAILED'}",
            f"Duration: {duration:.2f} seconds",
            f"Completed: {end_time.isoformat(timespec='seconds')}",
        ]
        
        if not success and error_message:
            log_lines.append(f"Error: {error_message}")
        
        log_lines.append("")
        log_lines.append("=== End of direct agent log ===")
        
        self._safe_write(log_lines)
    
    def get_log_file_path(self) -> Optional[str]:
        """Get the path to the log file."""
        return str(self.log_file_path) if self.log_file_path else None


def create_direct_agent_logger(
    agent_name: str, 
    user_input: str, 
    business_context: str = ""
) -> DirectAgentLogger:
    """
    Factory function to create a DirectAgentLogger instance.
    
    Args:
        agent_name: Name of the agent being executed
        user_input: User's input/request
        business_context: Business context for the agent
    
    Returns:
        DirectAgentLogger instance
    """
    return DirectAgentLogger(agent_name, user_input, business_context)
