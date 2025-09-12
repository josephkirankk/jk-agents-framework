# Data Analysis Agent Integration

## Overview

The `data_analysis_agent` is a comprehensive agent that combines both Context7 MCP tools and Python function tools to provide powerful data analysis capabilities with up-to-date documentation access.

## Features

### 1. Context7 MCP Integration
- **resolve-library-id**: Resolves library names to Context7-compatible IDs
- **get-library-docs**: Fetches up-to-date documentation for any library
- Supports all major data science libraries (pandas, numpy, matplotlib, scikit-learn, etc.)

### 2. Python Function Tools
- **calculate_percentage**: Calculate percentages for business metrics
- **data_analyzer**: Perform statistical analysis (mean, median, std dev, outliers)
- **format_currency**: Format numbers as currency (USD, EUR, etc.)
- **calculate_business_days**: Calculate business days between dates
- **text_processor**: Advanced text processing (word count, cleaning, summarization)
- **count_csv_rows**: Analyze CSV data structure

## Configuration

The agent is configured in `config/azure_openai_reference.yaml`:

```yaml
- name: "data_analysis_agent"
  description: "Comprehensive data analysis agent with Context7 docs and Python tools"
  model: "azure_openai:gpt-4.1"
  mcp_servers:
    context7_local:
      transport: "stdio"
      command: "npx"
      args: ["-y", "@upstash/context7-mcp@latest", "--api-key", "ctx7sk-..."]
      env: {}
  python_tools:
    data_tools:
      module_path: "tools.python_function_tools"
      tool_names: ["calculate_percentage", "data_analyzer", "format_currency", "calculate_business_days"]
      description: "Data analysis and business calculation tools"
    text_tools:
      module_path: "tools.python_function_tools"
      tool_names: ["text_processor", "count_csv_rows"]
      description: "Text processing and CSV analysis tools"
```

## Usage Examples

### Example 1: Statistical Analysis with Documentation
```bash
curl -X POST "http://localhost:8000/worker/upload" \
  -F "agent_name=data_analysis_agent" \
  -F "input=I have sales data: [100, 150, 200, 175, 300]. Please analyze this data statistically and also get documentation for matplotlib plotting" \
  -F "config_path=config/azure_openai_reference.yaml"
```

**Response**: The agent will:
1. Use `data_analyzer` tool to calculate mean, median, std dev, outliers
2. Use Context7 to fetch current matplotlib documentation
3. Provide both statistical insights and plotting code examples

### Example 2: Business Calculations with Library Documentation
```bash
curl -X POST "http://localhost:8000/worker/upload" \
  -F "agent_name=data_analysis_agent" \
  -F "input=Calculate what percentage 45 is of 180, format it as currency (USD), and get documentation for numpy array creation" \
  -F "config_path=config/azure_openai_reference.yaml"
```

**Response**: The agent will:
1. Use `calculate_percentage` tool: 45/180 = 25%
2. Use `format_currency` tool: USD 45.00
3. Use Context7 to fetch numpy array creation documentation

### Example 3: Text Analysis with Framework Documentation
```bash
curl -X POST "http://localhost:8000/worker/upload" \
  -F "agent_name=data_analysis_agent" \
  -F "input=Analyze this text for word count and get documentation for pandas text processing methods" \
  -F "config_path=config/azure_openai_reference.yaml"
```

## Tool Capabilities

### Statistical Analysis (`data_analyzer`)
- **Basic**: count, sum, mean, min, max, range
- **Statistical**: variance, standard deviation, median
- **Advanced**: quartiles, IQR, outlier detection

### Text Processing (`text_processor`)
- **word_count**: Count words, unique words, average word length
- **char_count**: Character count, lines, paragraphs
- **clean**: Remove special characters, normalize whitespace
- **summary**: Extract first and last sentences

### Business Tools
- **Percentage calculations**: For KPIs and metrics
- **Currency formatting**: Multi-currency support
- **Business days**: Exclude weekends from date calculations
- **CSV analysis**: Row counting with header handling

## Integration Benefits

1. **Real-time Documentation**: Always get the latest API documentation
2. **Immediate Analysis**: Process data without external dependencies
3. **Combined Insights**: Merge documentation with practical analysis
4. **Comprehensive Coverage**: Handle both numerical and text data
5. **Business Ready**: Format results for presentations and reports

## Testing Results

✅ **MCP Tools**: 2 tools loaded (resolve-library-id, get-library-docs)
✅ **Python Tools**: 6 tools loaded from 2 tool sets
✅ **Total Tools**: 8 tools available to the agent
✅ **API Integration**: Full HTTP API support
✅ **Error Handling**: Robust error handling with TaskGroup fix
✅ **Performance**: Fast response times with proper timeout handling

## Technical Implementation

- **MCP Transport**: stdio with npx for reliability
- **Tool Loading**: Dynamic loading from `tools.python_function_tools`
- **Error Handling**: Enhanced TimeoutTool with proper retry logic
- **Configuration**: Flexible YAML-based tool selection
- **Validation**: Comprehensive tool validation and testing

This integration provides a powerful foundation for data analysis tasks while maintaining access to the latest documentation and best practices.
