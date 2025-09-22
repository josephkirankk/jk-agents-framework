# TsDefects Pipeline

An integrated pipeline that combines defect analysis and agent processing using TsSearch (Typesense) for vector search operations.

## Overview

The TsDefects Pipeline performs comprehensive defect analysis through four integrated stages:

1. **Intent Extraction**: Extract structured intent from user input using `jk_pilger_extract_intent_agent`
2. **TS Vector Search**: Search for relevant defects using TsSearchClient (Typesense)
3. **Result Processing**: Simple deduplication and validation of search results
4. **Agent Enhancement**: Add curator actions and rationale using `jk_pilger_new_entries_agent`

## Features

- **Integrated Pipeline**: Combines functionality from both `defect_analysis` and `pilger_processing` pipelines
- **TsSearch Integration**: Uses Typesense for high-performance vector search
- **Agent Enhancement**: Adds curator actions and rationale to each defect result
- **Async/Sync Support**: Supports both asynchronous and synchronous execution
- **Configurable**: Highly configurable with sensible defaults
- **Cross-Platform**: Works on Windows and macOS

## Installation

The pipeline is part of the `gemba_agents` package and requires the following dependencies:

```bash
pip install pipefunc pydantic httpx
```

## Quick Start

### Basic Usage

```python
import asyncio
from gemba_agents.tsdefects_pipeline import TsDefectsPipeline

async def main():
    # Create pipeline with default configuration
    pipeline = TsDefectsPipeline()
    
    # Run analysis
    result = await pipeline.run(
        "The pump's loading/unloading piston is not operating smoothly"
    )
    
    # Display results
    print(f"Found {result.total_results} enhanced defects")
    for defect in result.enhanced_defects:
        print(f"- {defect.defect_code}: {defect.curator_action}")

asyncio.run(main())
```

### Synchronous Usage

```python
from gemba_agents.tsdefects_pipeline import analyze_ts_defects_sync

# Simple synchronous execution
result = analyze_ts_defects_sync(
    "Hydraulic pump cavitation detected in the main system"
)

print(f"Success: {result.success}")
print(f"Total results: {result.total_results}")
```

### Custom Configuration

```python
from gemba_agents.tsdefects_pipeline import TsDefectsPipeline, TsDefectsConfig

# Create custom configuration
config = TsDefectsConfig(
    intent_agent_name="jk_pilger_extract_intent_agent",
    processing_agent_name="jk_pilger_new_entries_agent_v2",
    search_limit=15,
    min_similarity_score=0.3,
    ts_search_base_url="http://localhost:3000",
    enable_logging=True,
    parallel_search=True
)

# Create pipeline with custom config
pipeline = TsDefectsPipeline(config)
result = await pipeline.run("Motor bearing vibration detected")
```

## API Reference

### TsDefectsPipeline

Main pipeline class that orchestrates all four stages.

#### Constructor

```python
TsDefectsPipeline(config: Optional[TsDefectsConfig] = None)
```

#### Methods

##### `async run(user_input: str) -> TsDefectsResult`

Run the complete pipeline asynchronously.

**Parameters:**
- `user_input`: Raw user input describing equipment issues

**Returns:**
- `TsDefectsResult`: Complete analysis results with enhanced defects

##### `run_sync(user_input: str) -> TsDefectsResult`

Run the pipeline synchronously.

##### `get_pipeline_info() -> dict`

Get information about the pipeline configuration.

##### `visualize(**kwargs)`

Visualize the pipeline structure (requires graphviz).

##### `print_profiling_stats()`

Print performance profiling statistics.

### Configuration Models

#### TsDefectsConfig

Configuration model for the pipeline.

```python
class TsDefectsConfig(BaseModel):
    # Intent extraction
    intent_agent_name: str = "jk_pilger_extract_intent_agent"
    
    # TsSearch configuration
    ts_search_base_url: Optional[str] = None  # Uses HYBRID_SEARCH_BASE_URL env var
    search_limit: int = 10
    min_similarity_score: float = 0.2
    collection: str = "defects"
    
    # Agent processing
    processing_agent_name: str = "jk_pilger_new_entries_agent_v2"
    config_path: str = "config/jk-gemba.yaml"
    
    # Pipeline settings
    enable_logging: bool = True
    enable_caching: bool = True
    parallel_search: bool = True
    timeout_seconds: int = 120
```

### Result Models

#### TsDefectsResult

Final pipeline result containing enhanced defects.

```python
class TsDefectsResult(BaseModel):
    original_input: str
    intent_data: IntentData
    total_results: int
    enhanced_defects: List[EnhancedTsDefectResult]
    processing_time_ms: float
    success: bool
    error_message: Optional[str] = None
```

#### EnhancedTsDefectResult

TsDefectResult enhanced with curator actions.

```python
class EnhancedTsDefectResult(TsDefectResult):
    curator_action: Optional[str] = None  # e.g., "REVIEW_REQUIRED", "APPROVED"
    rationale: Optional[str] = None       # Agent's reasoning
```

## Output Format

The pipeline returns enhanced defects in the following format:

```json
[{
  "defect_code": "PLG.LUB.LUB_PUMP.LEAK",
  "defect_text": "Hydraulic or lubrication pump leaks sighted at seals or connections",
  "curator_action": "REVIEW_REQUIRED",
  "rationale": "Requires immediate attention due to safety implications",
  "subsystem_description": "LUB-Lubrication system",
  "component_description": "LUB_PUMP-Lubrication pump",
  "defect_type_description": "LEAK-Leakage defect",
  "machine": "PLG",
  "subsystem": "LUB", 
  "component": "LUB_PUMP",
  "defect_type": "LEAK",
  "score": 0.85,
  "keywords": ["pump", "leak", "lubrication"],
  "tags": ["maintenance", "safety"]
}]
```

## Environment Variables

- `HYBRID_SEARCH_BASE_URL`: Base URL for TsSearch API (default: http://localhost:3000)

## Error Handling

The pipeline includes comprehensive error handling:

- **Graceful Degradation**: Returns partial results when possible
- **Detailed Logging**: Configurable logging for debugging
- **Error Context**: Detailed error messages with context
- **Fallback Values**: Default values when agent processing fails

## Performance

- **Parallel Processing**: Supports parallel vector searches
- **Caching**: Optional result caching with LRU cache
- **Profiling**: Built-in performance profiling
- **Timeouts**: Configurable timeouts for agent operations

## Testing

Run the test suite:

```bash
python -m pytest gemba_agents/tsdefects_pipeline/test_pipeline.py -v
```

Run examples:

```bash
python -m gemba_agents.tsdefects_pipeline.example
```

## Architecture

The pipeline uses `pipefunc` for orchestration and maintains the following data flow:

```
User Input → Intent Extraction → TS Vector Search → Result Processing → Agent Enhancement → Enhanced Defects
```

Each stage is independently testable and can be cached for performance.

## Comparison with Existing Pipelines

| Feature | DefectAnalysisPipeline | PilgerProcessingPipeline | TsDefectsPipeline |
|---------|----------------------|-------------------------|-------------------|
| Vector Search | VectorDB | N/A | TsSearch (Typesense) |
| Agent Processing | No | Yes | Yes |
| Data Models | VectorDB models | AggregatedResults | TsSearch models |
| Integration | Separate | Separate | Integrated |
| Output Format | Complex aggregation | Processing insights | Enhanced defects |

## Contributing

When contributing to the TsDefects pipeline:

1. Maintain compatibility with TsSearch data models
2. Ensure cross-platform compatibility (Windows/macOS)
3. Add comprehensive tests for new features
4. Update documentation for API changes
5. Follow existing code patterns and error handling

## License

This module is part of the jk-agents project.
