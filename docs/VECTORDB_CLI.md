# VectorDB Wrapper CLI

Interactive command-line interface for testing and using the VectorDB wrapper functionality.

## Overview

The VectorDB CLI provides an interactive interface to:
- Test VectorDB API connectivity
- Search for defects using natural language queries
- Create and update defects (upsert operations)
- Perform batch operations from JSON files
- Run example operations for testing

## Installation & Setup

The CLI is included with the VectorDB wrapper package. No additional installation required.

### Prerequisites
- Python 3.8+
- VectorDB API server running (default: http://localhost:8010)
- Required dependencies installed (see requirements.txt)

## Usage

### Starting the CLI

#### Method 1: As a Module (Recommended)
```bash
python -m vectordb_wrapper.cli
```

#### Method 2: Direct Execution
```bash
python vectordb_wrapper/cli.py
```

#### Method 3: With Custom URL
```bash
python -m vectordb_wrapper.cli --url http://your-api-server:8010
```

### Command Line Options

```bash
python -m vectordb_wrapper.cli [OPTIONS]

Options:
  --url URL        Base URL for VectorDB API
  --create-sample  Create sample JSON file for batch testing
  -h, --help      Show help message
```

## Interactive Commands

Once the CLI is running, you can use these commands:

### System Commands

| Command | Description |
|---------|-------------|
| `help`, `h`, `?` | Show available commands |
| `health`, `status` | Check API health status |
| `config` | Show current configuration |
| `seturl <url>` | Change base URL |
| `quit`, `exit`, `q` | Exit CLI |

### Search Commands

| Command | Description | Example |
|---------|-------------|---------|
| `search <query>` | Quick search with default options | `search motor bearing failure` |
| `search` | Interactive search with custom options | Prompts for query, top_n, min_score |
| `searchget <query>` | Quick GET search | `searchget hydraulic pump` |
| `searchget` | Interactive GET search | Prompts for parameters |

### Data Commands

| Command | Description |
|---------|-------------|
| `upsert` | Interactive defect creation/update |
| `batch` | Batch upsert from JSON file |
| `examples` | Run example operations |

## Examples

### Basic Search
```
vectordb> search motor bearing failure
🔍 Searching for: 'motor bearing failure'

📊 Search Results:
   Query: motor bearing failure
   Total Results: 3
   Execution Time: 1234.5ms

   Result 1:
     🏷️  Code: MOT.BRG.FAIL.001
     📝 Text: Motor bearing failure causing vibration
     🎯 Score: 95.2%
     🔧 Subsystem: MOT
     ⚠️  Severity: High
```

### Interactive Search
```
vectordb> search
🔍 Interactive Search
--------------------
Enter search query: hydraulic pump cavitation
Number of results (default: 5): 3
Minimum score 0.0-1.0 (default: 0.7): 0.8

🔍 Searching for: 'hydraulic pump cavitation' (top_n=3, min_score=0.8)
[Results displayed...]
```

### Interactive Upsert
```
vectordb> upsert
📝 Interactive Defect Upsert
------------------------------
Defect Code (required): PUMP.SEAL.LEAK.001
Defect Description (required): Pump seal leakage causing fluid loss
Subsystem (required): PMP
Severity (default: Medium): High
Typical Frequency (default: Unknown): Occasional

Enter lists (comma-separated, or press Enter to skip):
Symptoms: visible leakage, pressure drop, fluid contamination
Detection Methods: visual inspection, pressure monitoring
[... more prompts ...]

📝 Upserting defect: PUMP.SEAL.LEAK.001
✅ Success: Defect created successfully
🔧 Operation: created
```

### Batch Upsert
```
vectordb> batch
📦 Batch Upsert from JSON
-------------------------
Enter JSON file path: sample_defects.json
📂 Reading file: sample_defects.json
🚀 Starting batch upsert...

📊 Batch Upsert Results:
   Total Defects: 10
   ✅ Successful: 9
   ❌ Failed: 1
   📈 Success Rate: 90.0%
```

## JSON File Format

For batch operations, use this JSON structure:

```json
{
  "defects": [
    {
      "defect_code": "EXAMPLE.001",
      "defect_text": "Example defect description",
      "subsystem": "EXM",
      "severity": "Medium",
      "typical_frequency": "Rare",
      "symptoms": ["symptom 1", "symptom 2"],
      "detection_methods": ["visual inspection"],
      "early_warning_signals": ["early signal"],
      "tags": ["tag1", "tag2"],
      "likely_root_causes": ["cause 1"],
      "recommended_actions": ["action 1"]
    }
  ]
}
```

### Required Fields
- `defect_code`: Unique identifier
- `defect_text`: Description
- `subsystem`: Subsystem code

### Optional Fields
- `severity`: Default "Medium"
- `typical_frequency`: Default "Unknown"
- `symptoms`: Array of strings
- `detection_methods`: Array of strings
- `early_warning_signals`: Array of strings
- `tags`: Array of strings
- `likely_root_causes`: Array of strings
- `recommended_actions`: Array of strings

## Configuration

### Environment Variables
- `VECTORDB_BASE_URL`: Default base URL for the API

### Runtime Configuration
- Base URL can be changed with `seturl` command
- Configuration displayed with `config` command

## Logging

All operations are automatically logged to:
- `vectorlogs/vector_YYYYMMDDHHMMSS.json`

Logs include:
- Operation type and parameters
- Execution time and performance metrics
- Results and error information
- Timestamps and request/response data

## Troubleshooting

### Connection Issues
1. Verify VectorDB API is running
2. Check base URL is correct
3. Test with `health` command
4. Review firewall settings

### Import Errors
1. Ensure you're in the correct directory
2. Use module execution: `python -m vectordb_wrapper.cli`
3. Check Python path and dependencies

### Performance Issues
1. Check network connectivity
2. Monitor API server resources
3. Review logs for detailed timing information
4. Adjust timeout settings if needed

## Tips

- Use `Ctrl+C` to cancel any operation
- Tab completion available where supported
- All list inputs are comma-separated
- Empty inputs use default values
- Use `--create-sample` to generate test data
- Review logs for detailed operation information
