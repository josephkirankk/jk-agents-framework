# JSON Schema Test Data Generator

## Overview

The JSON Schema Test Data Generator is a comprehensive, AI-powered system that generates accurate, schema-compliant test data based on:

1. **JSON Schema definitions** (with full Draft 2020-12 support)
2. **Natural language requirements** from users

This system leverages a multi-agent architecture to parse schemas, interpret requirements, generate data, and validate results - all while handling large datasets efficiently.

## Features

### ✅ Comprehensive JSON Schema Support

- **All Types**: string, number, integer, boolean, object, array, null
- **Validation Rules**: pattern, minLength, maxLength, minimum, maximum, enum
- **References**: $ref, $defs for reusable definitions
- **Composition**: oneOf, anyOf, allOf for complex schemas
- **Objects**: required fields, additionalProperties, nested structures
- **Arrays**: items, minItems, maxItems, uniqueItems
- **Formats**: date, date-time, email, uri, uuid, and more

### 🤖 Multi-Agent Architecture

The system uses 4 specialized agents:

1. **Schema Analyzer**: Parses JSON Schema and extracts comprehensive metadata
2. **Requirement Parser**: Interprets natural language requirements
3. **Data Generator**: Creates schema-compliant test data with variations
4. **Schema Validator**: Validates all generated records against the schema

### 📊 Large Data Handling

- Automatically stores datasets with 1000+ records
- Efficient database-backed storage (SQLite + file system)
- Compression for optimal storage
- Reference-based retrieval for large datasets

### 🎯 Natural Language Interface

Users can specify requirements in plain English:

- "Create 100 records for program prg1 with metric defect_rate between 1 and 100"
- "Generate 50 records for manufacturing sector with throughput 10-500 items/hour"
- "Produce 200 records for plant PLT-01 with yield metric 0.5-0.95 ratio"

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Supervisor                              │
│                  (Orchestrates Workflow)                        │
└────────────┬────────────────────────────────────────────────────┘
             │
             ├──────────────────────────────────────────────────┐
             │                                                  │
             ▼                                                  ▼
    ┌────────────────┐                              ┌────────────────┐
    │ Schema Analyzer│                              │ Requirement    │
    │                │                              │ Parser         │
    │ - Parse schema │                              │ - Extract      │
    │ - Extract meta │                              │   constraints  │
    │ - Resolve $ref │                              │ - Parse NL     │
    └────────┬───────┘                              └────────┬───────┘
             │                                               │
             └───────────────────┬───────────────────────────┘
                                 │
                                 ▼
                        ┌────────────────┐
                        │ Data Generator │
                        │                │
                        │ - Generate data│
                        │ - Apply rules  │
                        │ - Ensure valid │
                        └────────┬───────┘
                                 │
                                 ▼
                        ┌────────────────┐
                        │ Schema         │
                        │ Validator      │
                        │                │
                        │ - Validate all │
                        │ - Report errors│
                        └────────────────┘
```

## Configuration

The system is configured via `config/json_schema_test_data_generator.yaml`:

```yaml
models:
  default: "azure_openai:gpt-4.1"
  supervisor: "azure_openai:gpt-4.1"

temperature: 0.1  # Low for deterministic output

large_data_handling:
  enabled: true
  token_threshold: 1000
  large_data:
    sqlite_path: "./data/schema_test_data.db"
    file_path: "./data/schema_test_files/"
    compression: true

agents:
  - name: "schema_analyzer"
    # ... configuration
  - name: "requirement_parser"
    # ... configuration
  - name: "data_generator"
    # ... configuration
  - name: "schema_validator"
    # ... configuration
```

## Usage

### 1. Start the API Server

```bash
# Using uvicorn
uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Or using the startup script
python api.py --config config/json_schema_test_data_generator.yaml
```

### 2. Send a Request

#### Example 1: Simple Schema

```bash
curl -X POST http://localhost:8000/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Generate 50 test records using this schema:\n\n{\n  \"type\": \"object\",\n  \"required\": [\"id\", \"name\"],\n  \"properties\": {\n    \"id\": {\"type\": \"integer\", \"minimum\": 1},\n    \"name\": {\"type\": \"string\", \"minLength\": 2}\n  }\n}\n\nRequirements: Create 50 records with id between 1 and 100",
    "config_path": "config/json_schema_test_data_generator.yaml",
    "thread_id": "test_001"
  }'
```

#### Example 2: Complex Schema with Natural Language

```bash
curl -X POST http://localhost:8000/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I need test data for a program metrics system.\n\nJSON Schema:\n{\n  \"type\": \"object\",\n  \"required\": [\"program_name\", \"record_count\"],\n  \"properties\": {\n    \"program_name\": {\"type\": \"string\", \"enum\": [\"prg1\", \"prg2\", \"prg3\"]},\n    \"sector\": {\"type\": \"string\", \"enum\": [\"manufacturing\", \"retail\"]},\n    \"record_count\": {\"type\": \"integer\", \"minimum\": 0}\n  }\n}\n\nRequirements:\nGenerate 100 records for program prg1 in manufacturing sector.\nRecord count should be between 50 and 500.",
    "config_path": "config/json_schema_test_data_generator.yaml",
    "thread_id": "test_002"
  }'
```

### 3. Python SDK Usage

```python
import asyncio
import json
import uuid
from app.main import load_app_config, build_agents_map
from app.supervisor_builder import build_supervisor_compiled
from app.planner_executor import execute_plan

async def generate_test_data():
    # Load configuration
    config_path = "config/json_schema_test_data_generator.yaml"
    app_config = load_app_config(config_path)

    # Define your schema
    schema = {
        "type": "object",
        "required": ["id", "value"],
        "properties": {
            "id": {"type": "integer", "minimum": 1},
            "value": {"type": "number", "minimum": 0, "maximum": 100}
        }
    }

    # Create query
    query = f"""
    Generate 100 test records using this schema:
    {json.dumps(schema, indent=2)}

    Requirements:
    Create 100 records with value between 10 and 90
    """

    # Setup
    thread_id = f"test_{uuid.uuid4().hex[:8]}"
    default_model = app_config.models.get('default')

    # Build supervisor
    supervisor = build_supervisor_compiled(
        app_config.supervisor,
        app_config.agents,
        default_model,
        app_config.business_context or "",
        original_user_question=query,
        config_path=config_path,
        default_temperature=0.1,
        thread_id=thread_id,
    )

    # Build agents
    agents_map, mcp_clients = await build_agents_map(
        app_config,
        user_input=query,
        config_path=config_path
    )

    # Execute
    result = await execute_plan(
        supervisor_compiled=supervisor,
        agents_map=agents_map,
        user_input=query,
        thread_id=thread_id,
        default_model_for_verifier=default_model
    )

    print(result.get("final_result", ""))

# Run
asyncio.run(generate_test_data())
```

## Example Schemas

### Simple User Schema

```json
{
  "type": "object",
  "required": ["name", "age", "email"],
  "properties": {
    "name": {"type": "string", "minLength": 2, "maxLength": 50},
    "age": {"type": "integer", "minimum": 18, "maximum": 100},
    "email": {"type": "string", "format": "email"}
  }
}
```

### Complex Program Metrics Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ProgramMetrics",
  "type": "object",
  "required": ["program_name", "record_count", "window"],
  "properties": {
    "program_name": {
      "type": "string",
      "enum": ["prg1", "prg2", "prg3"]
    },
    "sector": {
      "type": "string",
      "enum": ["manufacturing", "retail", "services"]
    },
    "plant_code": {
      "type": "string",
      "pattern": "^[A-Z0-9-_.]{2,32}$"
    },
    "record_count": {
      "type": "integer",
      "minimum": 0
    },
    "window": {
      "type": "object",
      "required": ["start_date", "end_date"],
      "properties": {
        "start_date": {"type": "string", "format": "date"},
        "end_date": {"type": "string", "format": "date"},
        "timezone": {"type": "string"},
        "days": {"type": "integer", "minimum": 1}
      }
    }
  }
}
```

## Testing

### Run Integration Tests

```bash
# Run all tests
cd integration_tests
python test_07_json_schema_data_generator.py

# Or run specific test
python -m pytest test_07_json_schema_data_generator.py::test_schema_analysis -v
```

### Test Coverage

The integration tests cover:

1. ✅ Schema analysis and metadata extraction
2. ✅ Natural language requirement parsing
3. ✅ Simple schema data generation
4. ✅ Complex schema data generation
5. ✅ Large dataset generation (100+ records)
6. ✅ Schema validation workflow
7. ✅ End-to-end workflow with all agents

## Performance

### Token Optimization

- **Small datasets** (< 100 records): ~2,500 tokens
- **Large datasets** (1000+ records): ~3,000 tokens (with auto-storage)
- **Savings**: Up to 95% for large datasets vs. inline data

### Generation Speed

- **Simple schema**: ~5-10 seconds for 100 records
- **Complex schema**: ~15-30 seconds for 100 records
- **Large datasets**: ~30-60 seconds for 1000 records

## Troubleshooting

### Common Issues

1. **Schema parsing errors**
   - Ensure schema is valid JSON Schema Draft 2020-12
   - Check for circular $ref references
   - Validate schema using online validators

2. **Validation failures**
   - Review validation report for specific errors
   - Check if user constraints conflict with schema rules
   - Verify enum values match schema definitions

3. **Large data not storing**
   - Check `large_data_handling.enabled` is true
   - Verify `token_threshold` is appropriate
   - Ensure database paths are writable

### Debug Mode

Enable detailed logging:

```yaml
# In config file
logging:
  level: DEBUG
  format: detailed
```

## Advanced Features

### Custom Patterns

The generator supports common regex patterns:

- `^[A-Z0-9-_.]{2,32}$` - Alphanumeric with special chars
- `^[A-Z]{2}(-[A-Z]{2})?$` - Country codes (US, IN-MH)
- Email, URI, UUID formats

### Nested Objects

Automatically handles nested structures:

```json
{
  "type": "object",
  "properties": {
    "user": {
      "type": "object",
      "properties": {
        "profile": {
          "type": "object",
          "properties": {
            "name": {"type": "string"}
          }
        }
      }
    }
  }
}
```

### Array Generation

Supports array constraints:

```json
{
  "type": "array",
  "items": {"type": "string", "enum": ["A", "B", "C"]},
  "minItems": 2,
  "maxItems": 5,
  "uniqueItems": true
}
```

## Contributing

To extend the generator:

1. Add new pattern handlers in `data_generator` agent
2. Extend schema analysis for new JSON Schema features
3. Add validation rules in `schema_validator` agent
4. Update tests in `test_07_json_schema_data_generator.py`

## License

Part of the JK Agents Core framework.

## Support

For issues or questions:
- Check the integration tests for examples
- Review the configuration file comments
- Consult the main JK Agents documentation

