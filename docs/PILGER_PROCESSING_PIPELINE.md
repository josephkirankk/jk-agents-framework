# Pilger Processing Pipeline Documentation

## Overview

The Pilger Processing Pipeline is a specialized pipeline designed to process results from the DefectAnalysisPipeline through the `jk_pilger_new_entries_agent` for additional insights and recommended actions. It creates a two-stage processing workflow where defect analysis results are further enhanced with Pilger-specific processing.

## Architecture

### Design Principles

The pipeline follows the same architectural patterns as the DefectAnalysisPipeline:

- **pipefunc orchestration**: Uses pipefunc for pipeline management
- **Pydantic validation**: Strong typing and data validation
- **Async/sync support**: Both execution modes available
- **Error handling**: Comprehensive error handling and logging
- **Performance monitoring**: Built-in profiling and metrics
- **Cross-platform**: Windows and macOS compatibility

### Pipeline Flow

```
DefectAnalysisPipeline Output (AggregatedResults)
    ↓
┌─────────────────────────────────────────────────────┐
│              PilgerProcessingPipeline               │
│                                                     │
│  ┌─────────────────────────────────────────────────┐│
│  │           Agent Processing Stage                ││
│  │                                                 ││
│  │  1. Format defect analysis data                 ││
│  │  2. Load jk_pilger_new_entries_agent            ││
│  │  3. Invoke agent with formatted data            ││
│  │  4. Parse agent response                        ││
│  │  5. Extract insights and actions                ││
│  └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
    ↓
PilgerProcessingResult (Enhanced results with insights)
```

## Installation

### Prerequisites

- Python 3.8+
- pipefunc library
- Existing jk-agents infrastructure
- DefectAnalysisPipeline (for input data)

### Setup

The pipeline is located in `gemba_agents/pilger_processing/` and integrates with the existing codebase structure.

## Configuration

### PilgerProcessingConfig

```python
class PilgerProcessingConfig(BaseModel):
    # Agent configuration
    agent_name: str = "jk_pilger_new_entries_agent"
    config_path: str = "config/jk-gemba.yaml"
    
    # Processing configuration
    include_original_data: bool = True
    format_for_agent: str = "structured"  # 'structured' or 'text'
    
    # Pipeline configuration
    enable_logging: bool = True
    enable_caching: bool = True
    timeout_seconds: int = 120  # 30-300 seconds
```

### Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `agent_name` | str | "jk_pilger_new_entries_agent" | Name of the processing agent |
| `config_path` | str | "config/jk-gemba.yaml" | Path to agent configuration |
| `include_original_data` | bool | True | Include original analysis in result |
| `format_for_agent` | str | "structured" | Input format: 'structured' or 'text' |
| `enable_logging` | bool | True | Enable detailed logging |
| `enable_caching` | bool | True | Enable result caching |
| `timeout_seconds` | int | 120 | Agent processing timeout |

## Usage

### Basic Usage

```python
from gemba_agents.defect_analysis import DefectAnalysisPipeline
from gemba_agents.pilger_processing import PilgerProcessingPipeline

# Stage 1: Defect Analysis
defect_pipeline = DefectAnalysisPipeline()
defect_results = await defect_pipeline.run(
    "The pump's loading/unloading piston is not operating smoothly"
)

# Stage 2: Pilger Processing
pilger_pipeline = PilgerProcessingPipeline()
final_results = await pilger_pipeline.run(defect_results)

print(f"Original defects: {defect_results.total_unique_results}")
print(f"Additional insights: {len(final_results.processed_insights)}")
print(f"New actions: {len(final_results.recommended_actions)}")
```

### Convenience Functions

```python
from gemba_agents.defect_analysis import analyze_defect
from gemba_agents.pilger_processing import process_defect_analysis

# Streamlined processing
defect_results = await analyze_defect("Motor bearing overheating")
pilger_results = await process_defect_analysis(defect_results)
```

### Synchronous Usage

```python
from gemba_agents.defect_analysis import analyze_defect_sync
from gemba_agents.pilger_processing import process_defect_analysis_sync

# Synchronous processing
defect_results = analyze_defect_sync("Hydraulic pump cavitation")
pilger_results = process_defect_analysis_sync(defect_results)
```

### Custom Configuration

```python
from gemba_agents.pilger_processing import PilgerProcessingPipeline, PilgerProcessingConfig

config = PilgerProcessingConfig(
    format_for_agent="text",      # Use text format
    timeout_seconds=180,          # Extended timeout
    enable_caching=False          # Disable caching
)

pipeline = PilgerProcessingPipeline(config)
results = await pipeline.run(defect_results)
```

## Data Models

### Input: AggregatedResults

The pipeline accepts `AggregatedResults` from the DefectAnalysisPipeline:

```python
class AggregatedResults(BaseModel):
    original_input: str
    intent_data: IntentData
    total_unique_results: int
    defects: List[DefectResult]
    root_causes: List[str]
    corrective_actions: List[str]
    processing_time_ms: float
```

### Output: PilgerProcessingResult

```python
class PilgerProcessingResult(BaseModel):
    # Original data
    original_defect_analysis: AggregatedResults
    
    # Pilger processing results
    pilger_agent_response: Dict[str, Any]
    processed_insights: List[str]
    recommended_actions: List[str]
    confidence_score: Optional[float]
    
    # Metadata
    processing_time_ms: float
    agent_execution_time_ms: float
    success: bool
    error_message: Optional[str]
```

## Agent Integration

### Agent Configuration

The pipeline uses the `jk_pilger_new_entries_agent` configured in `config/jk-gemba.yaml`:

```yaml
- name: "jk_pilger_new_entries_agent"
  description: "Expert Pilger Machine Issue Predictor"
  model: "google:gemini-2.5-flash-lite"
  prompt_file: "prompts/latest/gemba_convert-to-english-v1.txt"
  mcp_servers: {}
```

### Input Formatting

The pipeline formats DefectAnalysisPipeline results for the agent in two modes:

#### Structured Format (JSON)
```json
{
  "original_input": "The pump piston is not operating smoothly",
  "intent_data": {
    "interpreted_meaning": "...",
    "component": "Pump",
    "sub_component": "Piston",
    "issue": "Not operating smoothly"
  },
  "total_unique_results": 5,
  "defects": [...],
  "root_causes": [...],
  "corrective_actions": [...]
}
```

#### Text Format
```
Original Input: The pump piston is not operating smoothly
Interpreted Meaning: The pump's loading/unloading piston is not operating smoothly
Component: Pump
Sub-component: Piston
Issue: Not operating smoothly
Found 5 related defects
Root Causes: insufficient_lubrication, wear
Corrective Actions: lubricate_system, inspect_seals
```

## Error Handling

### Pipeline-Level Errors

```python
try:
    results = await pipeline.run(defect_results)
    if results.success:
        print("Processing successful")
    else:
        print(f"Processing failed: {results.error_message}")
except Exception as e:
    print(f"Pipeline error: {e}")
```

### Agent-Level Errors

The pipeline handles agent failures gracefully:

- Timeout errors
- Agent configuration errors
- Response parsing errors
- Network connectivity issues

Failed processing returns a `PilgerProcessingResult` with:
- `success = False`
- `error_message` containing the error details
- Empty insights and actions lists
- Preserved original defect analysis data

## Performance Monitoring

### Timing Metrics

```python
results = await pipeline.run(defect_results)

print(f"Total processing time: {results.processing_time_ms:.2f}ms")
print(f"Agent execution time: {results.agent_execution_time_ms:.2f}ms")
```

### Profiling

```python
pipeline = PilgerProcessingPipeline()
results = await pipeline.run(defect_results)

# Print detailed profiling stats
pipeline.print_profiling_stats()
```

### Pipeline Information

```python
info = pipeline.get_pipeline_info()
print(f"Stages: {info['stages']}")
print(f"Agent: {info['agent_name']}")
print(f"Caching: {info['caching_enabled']}")
```

## Integration Patterns

### Sequential Processing

```python
async def complete_workflow(user_input: str):
    """Complete two-stage analysis workflow."""
    
    # Stage 1: Defect Analysis
    defect_pipeline = DefectAnalysisPipeline()
    defect_results = await defect_pipeline.run(user_input)
    
    # Stage 2: Pilger Processing
    pilger_pipeline = PilgerProcessingPipeline()
    final_results = await pilger_pipeline.run(defect_results)
    
    return final_results
```

### Batch Processing

```python
async def process_multiple_inputs(inputs: List[str]):
    """Process multiple inputs through both stages."""
    
    defect_pipeline = DefectAnalysisPipeline()
    pilger_pipeline = PilgerProcessingPipeline()
    
    results = []
    for user_input in inputs:
        defect_results = await defect_pipeline.run(user_input)
        pilger_results = await pilger_pipeline.run(defect_results)
        results.append(pilger_results)
    
    return results
```

### Conditional Processing

```python
async def smart_processing(user_input: str, use_pilger: bool = True):
    """Conditionally apply Pilger processing."""
    
    defect_results = await analyze_defect(user_input)
    
    if use_pilger and defect_results.total_unique_results > 0:
        return await process_defect_analysis(defect_results)
    else:
        # Return defect results wrapped in compatible format
        return create_pilger_result_from_defect_analysis(defect_results)
```

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest gemba_agents/pilger_processing/test_pipeline.py -v

# Run specific test class
python -m pytest gemba_agents/pilger_processing/test_pipeline.py::TestPilgerProcessingPipeline -v

# Run with coverage
python -m pytest gemba_agents/pilger_processing/test_pipeline.py --cov=gemba_agents.pilger_processing
```

### Test Categories

1. **Data Model Tests**: Validation and serialization
2. **Stage Function Tests**: Agent processing logic
3. **Pipeline Tests**: End-to-end pipeline execution
4. **Integration Tests**: DefectAnalysisPipeline integration
5. **Error Handling Tests**: Failure scenarios
6. **Performance Tests**: Timing and profiling

## Best Practices

### Configuration Management

- Use environment-specific configuration files
- Validate configuration before pipeline execution
- Monitor agent timeout settings for optimal performance

### Error Handling

- Always check `success` flag in results
- Log errors for debugging and monitoring
- Implement retry logic for transient failures

### Performance Optimization

- Enable caching for repeated processing
- Monitor agent execution times
- Use appropriate timeout values

### Integration

- Chain pipelines in logical sequence
- Preserve original data for traceability
- Handle partial failures gracefully

## Troubleshooting

### Common Issues

1. **Agent Configuration Errors**
   - Verify agent exists in config file
   - Check agent model availability
   - Validate prompt file paths

2. **Timeout Issues**
   - Increase `timeout_seconds` for complex processing
   - Monitor agent response times
   - Check network connectivity

3. **Response Parsing Errors**
   - Verify agent response format
   - Check JSON structure validity
   - Review agent prompt configuration

4. **Integration Issues**
   - Ensure DefectAnalysisPipeline compatibility
   - Verify data model versions
   - Check import paths

### Debugging

Enable detailed logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

config = PilgerProcessingConfig(enable_logging=True)
pipeline = PilgerProcessingPipeline(config)
```

## Future Enhancements

- Support for multiple agent processing
- Advanced result aggregation strategies
- Real-time processing capabilities
- Enhanced error recovery mechanisms
- Performance optimization features
