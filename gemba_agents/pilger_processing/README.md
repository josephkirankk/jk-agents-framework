# Pilger Processing Pipeline

A comprehensive pipeline for processing DefectAnalysisPipeline results through the jk_pilger_new_entries_agent for additional insights and actions. This pipeline is designed to work as a sequential step after the DefectAnalysisPipeline, creating a two-stage processing workflow.

## 🚀 Quick Start

```python
from gemba_agents.defect_analysis import DefectAnalysisPipeline
from gemba_agents.pilger_processing import PilgerProcessingPipeline

# First stage: Defect analysis
defect_pipeline = DefectAnalysisPipeline()
defect_results = await defect_pipeline.run(
    "The pump's loading/unloading piston is not operating smoothly"
)

# Second stage: Pilger processing
pilger_pipeline = PilgerProcessingPipeline()
final_results = await pilger_pipeline.run(defect_results)

print(f"Additional insights: {len(final_results.processed_insights)}")
print(f"Recommended actions: {len(final_results.recommended_actions)}")
```

## 📋 Features

- **Sequential Processing**: Designed to process DefectAnalysisPipeline results
- **Agent Integration**: Uses jk_pilger_new_entries_agent for additional processing
- **Comprehensive Results**: Includes original analysis plus new insights and actions
- **Error Handling**: Robust error handling with detailed logging
- **Performance Monitoring**: Built-in profiling and timing metrics
- **Cross-platform**: Works on both Windows and macOS
- **Async/Sync Support**: Both asynchronous and synchronous execution modes
- **Configurable**: Flexible configuration options for different use cases

## 🏗️ Architecture

The pipeline follows the same architectural patterns as DefectAnalysisPipeline:

```
Input: AggregatedResults (from DefectAnalysisPipeline)
    ↓
┌─────────────────────────────────────┐
│     PilgerProcessingPipeline        │
│                                     │
│  ┌─────────────────────────────────┐│
│  │    Agent Processing Stage       ││
│  │                                 ││
│  │  • Format defect analysis data  ││
│  │  • Call jk_pilger_new_entries   ││
│  │  • Parse agent response         ││
│  │  • Extract insights & actions   ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
    ↓
Output: PilgerProcessingResult
```

## 📦 Installation

The pipeline is located in the `gemba_agents/pilger_processing/` folder and requires:

- pipefunc library for pipeline orchestration
- Existing jk-agents infrastructure
- DefectAnalysisPipeline for input data

## 🔧 Configuration

### PilgerProcessingConfig

```python
from gemba_agents.pilger_processing import PilgerProcessingConfig

config = PilgerProcessingConfig(
    agent_name="jk_pilger_new_entries_agent",  # Agent to use
    config_path="config/jk-gemba.yaml",        # Agent config file
    include_original_data=True,                # Include original analysis
    format_for_agent="structured",             # Input format: 'structured' or 'text'
    enable_logging=True,                       # Enable detailed logging
    enable_caching=True,                       # Enable result caching
    timeout_seconds=120                        # Agent timeout
)
```

## 📚 Usage Examples

### Basic Usage

```python
from gemba_agents.defect_analysis import DefectAnalysisPipeline
from gemba_agents.pilger_processing import PilgerProcessingPipeline

# Create pipelines
defect_pipeline = DefectAnalysisPipeline()
pilger_pipeline = PilgerProcessingPipeline()

# Run sequential processing
defect_results = await defect_pipeline.run("Motor bearing overheating")
pilger_results = await pilger_pipeline.run(defect_results)

# Access results
print(f"Original defects found: {defect_results.total_unique_results}")
print(f"Additional insights: {len(pilger_results.processed_insights)}")
print(f"New actions: {len(pilger_results.recommended_actions)}")
```

### Synchronous Usage

```python
from gemba_agents.defect_analysis import analyze_defect_sync
from gemba_agents.pilger_processing import process_defect_analysis_sync

# Single-line processing
defect_results = analyze_defect_sync("Hydraulic pump cavitation")
pilger_results = process_defect_analysis_sync(defect_results)
```

### Custom Configuration

```python
from gemba_agents.pilger_processing import PilgerProcessingPipeline, PilgerProcessingConfig

config = PilgerProcessingConfig(
    format_for_agent="text",  # Use text format instead of JSON
    timeout_seconds=180,      # Longer timeout
    enable_caching=False      # Disable caching
)

pipeline = PilgerProcessingPipeline(config)
results = await pipeline.run(defect_results)
```

### Convenience Functions

```python
from gemba_agents.defect_analysis import analyze_defect
from gemba_agents.pilger_processing import process_defect_analysis

# Chain processing with convenience functions
defect_results = await analyze_defect("Gear tooth broken")
pilger_results = await process_defect_analysis(defect_results)
```

## 🔄 Integration Workflow

### Complete Two-Stage Workflow

```python
async def complete_analysis_workflow(user_input: str):
    """Complete defect analysis and Pilger processing workflow."""
    
    # Stage 1: Defect Analysis
    defect_pipeline = DefectAnalysisPipeline()
    defect_results = await defect_pipeline.run(user_input)
    
    print(f"Stage 1 Complete: Found {defect_results.total_unique_results} defects")
    
    # Stage 2: Pilger Processing
    pilger_pipeline = PilgerProcessingPipeline()
    final_results = await pilger_pipeline.run(defect_results)
    
    print(f"Stage 2 Complete: Generated {len(final_results.processed_insights)} insights")
    
    return final_results

# Usage
results = await complete_analysis_workflow(
    "The pump's loading/unloading piston is not operating smoothly"
)
```

### Error Handling

```python
from gemba_agents.pilger_processing import PilgerProcessingPipeline

pipeline = PilgerProcessingPipeline()

try:
    results = await pipeline.run(defect_results)
    if results.success:
        print(f"Processing successful: {len(results.processed_insights)} insights")
    else:
        print(f"Processing failed: {results.error_message}")
except Exception as e:
    print(f"Pipeline error: {e}")
```

## 📊 Result Structure

### PilgerProcessingResult

```python
{
    "original_defect_analysis": AggregatedResults,  # Original defect analysis
    "pilger_agent_response": dict,                  # Raw agent response
    "processed_insights": List[str],                # Additional insights
    "recommended_actions": List[str],               # Additional actions
    "confidence_score": float,                      # Confidence (0.0-1.0)
    "processing_time_ms": float,                    # Total processing time
    "agent_execution_time_ms": float,               # Agent execution time
    "success": bool,                                # Success status
    "error_message": str                            # Error message if failed
}
```

## 🛠️ Development

### Pipeline Information

```python
pipeline = PilgerProcessingPipeline()
info = pipeline.get_pipeline_info()
print(info)
```

### Performance Monitoring

```python
# Enable profiling
pipeline = PilgerProcessingPipeline()
results = await pipeline.run(defect_results)

# Print profiling stats
pipeline.print_profiling_stats()
```

### Visualization

```python
# Visualize pipeline structure
pipeline.visualize()
```

## 🧪 Testing

```python
# Run tests
python -m pytest gemba_agents/pilger_processing/test_pipeline.py -v
```

## 📁 File Structure

```
gemba_agents/pilger_processing/
├── __init__.py                 # Package initialization
├── pipeline.py                 # Main pipeline class
├── models/
│   ├── __init__.py
│   └── data_models.py         # Pydantic data models
├── stages/
│   ├── __init__.py
│   └── agent_processing.py    # Agent processing stage
├── utils/
│   ├── __init__.py
│   └── agent_utils.py         # Agent utilities (reused)
├── test_pipeline.py           # Test suite
└── README.md                  # This file
```

## 🔗 Dependencies

- pipefunc: Pipeline orchestration
- pydantic: Data validation
- DefectAnalysisPipeline: Input data source
- jk-agents infrastructure: Agent execution

## 📝 Notes

- The pipeline is designed to work sequentially after DefectAnalysisPipeline
- Agent configuration is loaded from config/jk-gemba.yaml
- Results include both original analysis and new processing insights
- Cross-platform compatibility ensured for Windows and macOS
- Comprehensive error handling and logging throughout
