# Context7 MCP Integration Guide

## Overview

This document provides comprehensive guidance on integrating Context7 MCP (Model Context Protocol) stdio agent into the JK-Agents multi-agent system. Context7 provides up-to-date, version-specific documentation and code examples directly from library sources, making it an invaluable tool for development assistance.

## What is Context7?

Context7 is a service that provides real-time access to library documentation, API references, and code examples. The Context7 MCP server allows AI agents to:

- Retrieve the latest documentation for any supported library or framework
- Get version-specific information and code examples
- Access comprehensive API references
- Obtain practical implementation guidance

## Configuration

### Basic MCP Server Configuration

The Context7 agent is configured in `config/azure_openai_reference.yaml` with the following MCP server setup:

```yaml
- name: "context7_agent"
  description: "Retrieve up-to-date library documentation and code examples using Context7 MCP"
  model: "azure_openai:gpt-4.1"
  prompt: |
    {{dependent_request_responses}}

    You are Context7Agent. You provide up-to-date, version-specific documentation and code examples directly from library sources.

    CRITICAL RULES:
    - ALWAYS use Context7 MCP tools to retrieve the latest documentation
    - When asked about a library/framework, use resolve-library-id first to get the correct library ID
    - Then use get-library-docs to fetch comprehensive documentation
    - Focus on providing practical code examples and implementation guidance
    - Include version-specific information when available
    - Cite the source documentation URLs when provided
    - If documentation is not available, clearly state this limitation

    Available MCP servers: {{mcpservers}}

    Your goal is to provide accurate, current documentation that helps developers implement solutions correctly.
  mcp_servers:
    context7:
      description: "Context7 MCP server for up-to-date library documentation (stdio)"
      transport: "stdio"
      command: "npx"
      args:
        - "-y"
        - "@upstash/context7-mcp"
      env: {}
```

### Prerequisites

Before using the Context7 agent, ensure you have:

1. **Node.js installed** - Required for running the npx command
2. **Internet connection** - Context7 needs to fetch documentation from remote sources
3. **Proper environment setup** - The agent runs in the local virtual environment (.venv)

### Supervisor Configuration

The supervisor has been updated to include Context7 agent selection guidelines:

```yaml
Agent Selection Guidelines:
- Use context7_agent for: library documentation, API references, code examples, framework guides
- Use python_exec_agent for: code execution, data processing, calculations requiring computation
- Use math_agent for: arithmetic calculations using HTTP service
- Use test_agent for: simple questions not requiring external tools
```

## Available Tools

The Context7 MCP server provides two main tools:

### 1. resolve-library-id
- **Purpose**: Resolves a package/product name to a Context7-compatible library ID
- **Usage**: Must be called before `get-library-docs` to obtain a valid library ID
- **Input**: Library name (e.g., "fastapi", "pandas", "react")
- **Output**: Context7-compatible library ID (e.g., "/tiangolo/fastapi")

### 2. get-library-docs
- **Purpose**: Fetches up-to-date documentation for a library
- **Usage**: Requires a Context7-compatible library ID from `resolve-library-id`
- **Parameters**:
  - `context7CompatibleLibraryID`: The exact library ID
  - `tokens`: Maximum number of tokens to retrieve (default: 10000)
  - `topic`: Optional topic to focus documentation on (e.g., 'routing', 'authentication')

## Usage Examples

### Simple Documentation Request

```python
# User query: "Show me how to use FastAPI to create a simple REST API"
# 
# The Context7 agent will:
# 1. Use resolve-library-id to find FastAPI's library ID
# 2. Use get-library-docs to fetch FastAPI documentation
# 3. Provide practical code examples for creating REST APIs
```

### Multi-Agent Workflow

```python
# User query: "Get pandas documentation and create code to analyze CSV data"
#
# The supervisor will create a plan involving:
# 1. context7_agent: Retrieve pandas documentation
# 2. python_exec_agent: Create and execute data analysis code
# 3. human_response_agent: Present the final result
```

## Testing

### Simple Tests

Run basic Context7 functionality tests:

```bash
# From the repository root
python tests/test_context7_simple.py
```

This test suite includes:
- Basic library documentation retrieval
- Library resolution functionality
- Response validation

### Advanced Multi-Agent Tests

Run comprehensive multi-agent workflow tests:

```bash
# From the repository root  
python tests/test_context7_advanced.py
```

This test suite includes:
- Context7 + Python execution agent collaboration
- Context7 + Math calculation agent workflow
- Full multi-agent data science workflow

## Best Practices

### 1. Library Resolution First
Always use `resolve-library-id` before `get-library-docs` to ensure you have the correct library identifier.

### 2. Specific Topics
When requesting documentation, specify topics to get more focused results:
- "authentication" for auth-related docs
- "routing" for URL routing information
- "database" for database integration guides

### 3. Version Awareness
Context7 provides version-specific documentation. Always check if the retrieved information matches your target version.

### 4. Error Handling
The Context7 agent is configured to clearly state when documentation is not available rather than hallucinating information.

## Troubleshooting

### Common Issues

1. **NPX Command Not Found**
   - Ensure Node.js is properly installed
   - Verify npx is available in your PATH

2. **Network Connectivity Issues**
   - Context7 requires internet access to fetch documentation
   - Check firewall settings if requests are blocked

3. **Library Not Found**
   - Not all libraries are available in Context7
   - The agent will clearly indicate when a library is not supported

4. **Timeout Issues**
   - Large documentation requests may timeout
   - Consider using the `topic` parameter to focus requests

### Debugging

Enable detailed logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Integration with Other Agents

The Context7 agent is designed to work seamlessly with other agents in the system:

- **Python Execution Agent**: Get documentation, then implement and test code
- **Math Agent**: Retrieve mathematical library docs, then perform calculations
- **Web Agent**: Combine web search with authoritative documentation

## Security Considerations

- The Context7 MCP server runs locally using npx
- No sensitive data is sent to external services beyond library names
- All documentation is retrieved from public sources

## Performance Optimization

- Use specific topics to reduce response size
- Limit token count for faster responses
- Cache frequently requested documentation locally when possible

## Future Enhancements

Potential improvements for the Context7 integration:

1. **Local Caching**: Cache frequently requested documentation
2. **Version Pinning**: Allow specifying exact library versions
3. **Custom Sources**: Support for private documentation sources
4. **Batch Requests**: Retrieve multiple library docs in one request

## Support and Resources

- **Context7 Documentation**: https://github.com/upstash/context7
- **MCP Specification**: https://modelcontextprotocol.io/
- **Issue Reporting**: Use the project's GitHub issues for Context7-related problems

---

*Last updated: 2025-08-26*
*Configuration tested with: Azure OpenAI GPT-4.1, Node.js 18+*
