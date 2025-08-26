working with mcp
```
$ curl -X POST "http://localhost:8000/worker/upload" -F "agent_name=context7_docs_agent" -F "input=use context7 to get documentation for langchain and show me how to create use degrum with hailo. write a sample" -F "config_path=config/azure_openai_reference.yaml"

c:\JK\dev\repo\mcp_code_executor>npx -y @upstash/context7-mcp --transport stdio
```