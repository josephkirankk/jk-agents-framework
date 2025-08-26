#!/usr/bin/env python3
"""
MCP Math Server

A simple MCP server that provides basic math operations.
Supports both stdio and HTTP transports.
"""

import sys
import os
import operator
from typing import Any, Dict

# Try to import MCP SDK
try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

# Fallback HTTP server for when MCP is not available
from fastapi import FastAPI
import uvicorn

# Math operations
OPERATIONS = {
    'add': operator.add,
    'subtract': operator.sub,
    'multiply': operator.mul,
    'divide': operator.truediv,
    'power': operator.pow,
    'modulo': operator.mod,
}


def safe_eval(expression: str) -> float:
    """Safely evaluate a math expression"""
    try:
        # Only allow basic math operations and numbers
        allowed_chars = set('0123456789+-*/.() ')
        if not all(c in allowed_chars for c in expression):
            raise ValueError("Invalid characters in expression")

        # Use eval with restricted builtins
        result = eval(expression, {"__builtins__": {}})
        return float(result)
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")


def calculate_operation(operation: str, a: float, b: float) -> float:
    """Perform a math operation"""
    if operation not in OPERATIONS:
        raise ValueError(f"Unknown operation: {operation}")

    try:
        return OPERATIONS[operation](a, b)
    except ZeroDivisionError:
        raise ValueError("Division by zero")
    except Exception as e:
        raise ValueError(f"Calculation error: {e}")

# MCP Server Implementation
if MCP_AVAILABLE:
    mcp = FastMCP("Math Server")

    @mcp.tool()
    def add(a: float, b: float) -> float:
        """Add two numbers"""
        return a + b

    @mcp.tool()
    def subtract(a: float, b: float) -> float:
        """Subtract b from a"""
        return a - b

    @mcp.tool()
    def multiply(a: float, b: float) -> float:
        """Multiply two numbers"""
        return a * b

    @mcp.tool()
    def divide(a: float, b: float) -> float:
        """Divide a by b"""
        if b == 0:
            raise ValueError("Division by zero")
        return a / b

    @mcp.tool()
    def calculate(expression: str) -> float:
        """Evaluate a mathematical expression"""
        return safe_eval(expression)

    @mcp.tool()
    def operation(op: str, a: float, b: float) -> float:
        """Perform a mathematical operation"""
        return calculate_operation(op, a, b)

# HTTP Server Implementation (fallback)
app = FastAPI(title="Math Server", description="Simple math operations server")

@app.get("/calculate")
def http_calculate(expression: str):
    """Calculate a mathematical expression via HTTP"""
    try:
        result = safe_eval(expression)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}

@app.post("/operation")
def http_operation(data: Dict[str, Any]):
    """Perform a mathematical operation via HTTP"""
    try:
        op = data.get("operation")
        a = float(data.get("a", 0))
        b = float(data.get("b", 0))
        result = calculate_operation(op, a, b)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok", "server": "math"}

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "stdio" and MCP_AVAILABLE:
        # Run as MCP server with stdio transport
        mcp.run(transport="stdio")
    elif len(sys.argv) > 1 and sys.argv[1] == "sse" and MCP_AVAILABLE:
        # Run as MCP server with SSE transport
        port = int(os.getenv("MATH_PORT", "8001"))
        mcp.run(transport="sse", port=port)
    else:
        # Run as HTTP server
        port = int(os.getenv("MATH_PORT", "8001"))
        uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
