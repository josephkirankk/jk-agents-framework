# Defect Analysis Pipeline

A comprehensive defect analysis pipeline using the pipefunc library for orchestrating intent extraction, vector search, and result aggregation stages.

## 🚀 Quick Start

```python
from gemba_agents.defect_analysis import DefectAnalysisPipeline

# Create and run pipeline
pipeline = DefectAnalysisPipeline()
result = await pipeline.run(
    "The pump's loading/unloading piston is not operating smoothly"
)

print(f"Component: {result.intent_data.component}")
print(f"Issue: {result.intent_data.issue}")
print(f"Found {result.total_unique_results} defects")
```

## 📋 Features

- **🔍 Intent Extraction**: Uses `jk_pilger_extract_intent_agent` for structured intent analysis
- **🔎 Vector Search**: Performs comprehensive vector search with top-n=10 results
- **📊 Result Aggregation**: Consolidates and deduplicates search results
- **🌐 Multi-language Support**: Handles English, Hindi, Urdu, and mixed languages
- **⚡ Performance Optimized**: Caching, parallel search, and profiling
- **🛡️ Error Resilient**: Comprehensive error handling and graceful degradation
- **🔧 Configurable**: Extensive configuration options
- **📱 Cross-platform**: Works on Windows and macOS

## 🏗️ Architecture

```
User Input → Intent Extraction → Vector Search → Result Aggregation → Final Results
              ↓                   ↓               ↓
         jk_pilger_agent     VectorDB Client   Deduplication
```

## 📦 Installation

1. **Install dependencies**:
   ```bash
   cd gemba_agents/defect_analysis
   python setup.py
   ```

2. **Install pipefunc** (if not already installed):
   ```bash
   pip install pipefunc
   ```

3. **Verify setup**:
   ```bash
   python setup.py deps
   ```

## 🔧 Configuration

```python
from gemba_agents.defect_analysis import DefectAnalysisConfig

config = DefectAnalysisConfig(
    # Intent extraction
    agent_name="jk_pilger_extract_intent_agent",
    config_path="config/jk-gemba.yaml",
    
    # Vector search
    top_n=10,
    min_score=0.6,
    parallel_search=True,
    
    # Pipeline options
    enable_logging=True,
    enable_caching=True
)
```

## 📚 Usage Examples

### Basic Usage

```python
from gemba_agents.defect_analysis import DefectAnalysisPipeline

pipeline = DefectAnalysisPipeline()
result = await pipeline.run("Motor bearing overheating")
```

### Synchronous Usage

```python
from gemba_agents.defect_analysis import analyze_defect_sync

result = analyze_defect_sync("Hydraulic pump cavitation")
```

### Custom Configuration

```python
config = DefectAnalysisConfig(top_n=15, min_score=0.5)
pipeline = DefectAnalysisPipeline(config)
result = await pipeline.run("Gear tooth broken")
```

### Multi-language Input

```python
# English
result1 = await pipeline.run("Motor bearing failure")

# Hindi
result2 = await pipeline.run("पंप लोडिंग अनलोडिंग करने वाला पिस्टन बराबर से चल नहीं रहा है")

# Mixed language
result3 = await pipeline.run("Hype jam ہو رہا ہے، ایچ ایس پی ون پہ")
```

## 📊 Output Format

```python
class AggregatedResults:
    original_input: str                    # Original user input
    intent_data: IntentData               # Extracted intent
    total_unique_results: int             # Number of unique defects
    defects: List[DefectResult]           # Defect details
    root_causes: List[str]                # Consolidated root causes
    corrective_actions: List[str]         # Consolidated actions
    processing_time_ms: float             # Processing time
```

### Intent Data Structure

```python
class IntentData:
    interpreted_meaning: str              # Clear English interpretation
    component: str                        # Main component (e.g., "Pump")
    sub_component: str                    # Sub-component (e.g., "Pump piston")
    related_component: str                # Related component (e.g., "Air compressor")
    issue: str                           # Issue type (e.g., "Not operating smoothly")
```

## 🧪 Testing

Run the test suite:

```bash
python setup.py test
```

Run examples:

```bash
python setup.py example
```

## 📈 Performance

- **Caching**: LRU cache for repeated queries
- **Parallel Search**: Concurrent vector searches
- **Profiling**: Built-in performance monitoring

```python
pipeline = DefectAnalysisPipeline()
result = await pipeline.run("test input")

# View performance stats
pipeline.print_profiling_stats()
```

## 🔍 Pipeline Visualization

```python
pipeline = DefectAnalysisPipeline()
pipeline.visualize()  # Shows pipeline graph
```

## 🛠️ Troubleshooting

### Common Issues

1. **Agent Not Found**
   ```
   Error: Agent 'jk_pilger_extract_intent_agent' not found
   Solution: Verify config/jk-gemba.yaml contains the agent
   ```

2. **Vector Search Timeout**
   ```
   Error: Vector search timeout
   Solution: Check VectorDB service availability
   ```

3. **JSON Parsing Error**
   ```
   Error: Could not parse JSON from response
   Solution: Enable debug logging to inspect agent response
   ```

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

config = DefectAnalysisConfig(enable_logging=True)
pipeline = DefectAnalysisPipeline(config)
```

## 📁 Project Structure

```
gemba_agents/defect_analysis/
├── __init__.py                 # Package initialization
├── pipeline.py                 # Main pipeline class
├── models/
│   ├── __init__.py
│   └── data_models.py         # Pydantic data models
├── stages/
│   ├── __init__.py
│   ├── intent_extraction.py   # Stage 1: Intent extraction
│   ├── vector_search.py       # Stage 2: Vector search
│   └── result_aggregation.py  # Stage 3: Result aggregation
├── utils/
│   ├── __init__.py
│   └── agent_utils.py         # Agent loading utilities
├── example.py                 # Usage examples
├── test_pipeline.py           # Test suite
├── setup.py                   # Setup script
├── requirements.txt           # Dependencies
└── README.md                  # This file
```

## 🤝 Contributing

1. Follow existing code patterns
2. Add comprehensive error handling
3. Include unit tests for new features
4. Update documentation
5. Ensure cross-platform compatibility

## 📄 License

This project is part of the jk-agents framework.

## 🔗 Related Documentation

- [Main Documentation](../../docs/DEFECT_ANALYSIS_PIPELINE.md)
- [VectorDB Wrapper](../../docs/VECTORDB_WRAPPER.md)
- [JK-Agents Usage](../../docs/USAGE.md)

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the test suite for examples
3. Enable debug logging for detailed information
