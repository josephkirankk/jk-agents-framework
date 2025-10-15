# JSON Schema Creator V2 - Enhanced Test Data Generator

## Overview

The JSON Schema Test Data Generator V2 adds **automatic schema creation** from plain English descriptions, making it easier to generate test data without manually writing JSON Schema definitions.

## What's New in V2

### 1. **Schema Creator Agent** (NEW)
- Automatically generates JSON Schema Draft 2020-12 from plain English
- Infers types, constraints, enums, and validation rules
- Follows best practices (snake_case naming, additionalProperties: false)
- Provides explanations of design decisions

### 2. **Smart Supervisor Routing**
The supervisor now intelligently detects input type and routes to the appropriate workflow:

**Plain English Input** → schema_creator → requirement_parser → data_generator → schema_validator
**Existing Schema** → schema_analyzer → requirement_parser → data_generator → schema_validator

### 3. **Backward Compatible**
- All existing functionality preserved
- Traditional schema-based workflow still works
- Same agent configurations for analyzer, parser, generator, validator

---

## Usage

### Option 1: Plain English Input (NEW)

Simply describe your data structure in plain English:

```
Data Structure:

employee_id: unique identifier
employee_name: full name
department: HR, Engineering, Sales, Marketing
salary: 30000 to 200000
hire_date: date in YYYY-MM-DD format
is_active: true or false

Requirements: Generate 100 employee records across all departments
```

The system will:
1. ✅ Create a complete JSON Schema with proper types and constraints
2. ✅ Parse your requirements
3. ✅ Generate test data matching the schema
4. ✅ Validate all records

### Option 2: Existing Schema (Traditional)

Provide a complete JSON Schema:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Employee",
  "type": "object",
  "properties": {
    "employee_id": {"type": "string"},
    "employee_name": {"type": "string"},
    ...
  },
  "required": ["employee_id", "employee_name"]
}
```

Requirements: Generate 100 employee records

---

## Schema Creator Features

### Type Inference

The schema creator intelligently infers JSON Schema types:

| Plain English | Inferred Type | Example |
|--------------|---------------|---------|
| `name`, `title`, `description` | `string` | `{"type": "string"}` |
| `email address` | `string` with format | `{"type": "string", "format": "email"}` |
| `date`, `hire_date` | `string` with date format | `{"type": "string", "format": "date"}` |
| `age`, `count`, `quantity` | `integer` | `{"type": "integer"}` |
| `price`, `rating`, `percentage` | `number` | `{"type": "number"}` |
| `is_active`, `true/false` | `boolean` | `{"type": "boolean"}` |
| `options: A, B, C` | `enum` | `{"enum": ["A", "B", "C"]}` |

### Constraint Inference

| Plain English | Inferred Constraint | JSON Schema |
|--------------|-------------------|-------------|
| `1 to 10` | min/max | `{"minimum": 1, "maximum": 10}` |
| `YYYY format` | pattern | `{"pattern": "^[0-9]{4}$"}` |
| `2-50 characters` | length | `{"minLength": 2, "maxLength": 50}` |
| `required` or listed | required array | `"required": ["field1", ...]` |

### Naming Conventions

All field names are automatically converted to `snake_case`:

- "Student Name" → `student_name`
- "Employee ID" → `employee_id`
- "Date of Birth" → `date_of_birth`

---

## Examples

### Example 1: Student Exam Records

**Input:**
```
student name: name
student id: id
class: 1 to 10
subject: maths, physics, chemistry
marks: 1 to 100
exam quarter: Q1 to Q4
exam year: YYYY format

Requirements: Generate 900 records for 100 students across all subjects
```

**Generated Schema:**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "StudentExamRecord",
  "type": "object",
  "properties": {
    "student_name": {
      "type": "string",
      "description": "Full name of the student"
    },
    "student_id": {
      "type": "string",
      "description": "Unique identifier for the student"
    },
    "student_class": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10
    },
    "subject": {
      "type": "string",
      "enum": ["Maths", "Physics", "Chemistry"]
    },
    "marks": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100
    },
    "exam_quarter": {
      "type": "string",
      "enum": ["Q1", "Q2", "Q3", "Q4"]
    },
    "exam_year": {
      "type": "integer",
      "minimum": 2000,
      "maximum": 2100
    }
  },
  "required": ["student_name", "student_id", "student_class", "subject", "marks", "exam_quarter", "exam_year"],
  "additionalProperties": false
}
```

### Example 2: E-commerce Products

**Input:**
```
product_id: unique ID format PROD-NNNNNN
product_name: product name
category: Electronics, Clothing, Food, Books
price: 0.01 to 10000.00
stock: 0 to 10000 units
in_stock: yes or no

Requirements: Generate 200 products with realistic prices per category
```

**Generated Schema:**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Product",
  "type": "object",
  "properties": {
    "product_id": {
      "type": "string",
      "pattern": "^PROD-[0-9]{6}$"
    },
    "product_name": {
      "type": "string"
    },
    "category": {
      "type": "string",
      "enum": ["Electronics", "Clothing", "Food", "Books"]
    },
    "price": {
      "type": "number",
      "minimum": 0.01,
      "maximum": 10000.00,
      "multipleOf": 0.01
    },
    "stock": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10000
    },
    "in_stock": {
      "type": "boolean"
    }
  },
  "required": ["product_id", "product_name", "category", "price", "stock", "in_stock"],
  "additionalProperties": false
}
```

---

## Configuration Changes

### Updated Supervisor Prompt

The supervisor now includes input detection logic:

```yaml
supervisor:
  name: "schema_data_supervisor"
  prompt: |
    ## INPUT DETECTION RULES:
    
    If user input contains "$schema", "properties", "type": "object"
      → Use schema_analyzer workflow
    
    If user input contains plain English descriptions
      → Use schema_creator workflow
```

### New Agent: schema_creator

```yaml
agents:
  - name: "schema_creator"
    description: "Creates JSON Schema Draft 2020-12 from plain English"
    model: "azure_openai:gpt-4.1"
    agent_type: "react"
    require_tool_use: false
```

---

## API Integration

### Using with litellm_api.py

**Endpoint:** `POST /api/agent/execute`

**Plain English Request:**
```json
{
  "config_name": "json_schema_test_data_generator_v2",
  "user_request": "employee_id: unique ID\nemployee_name: full name\ndepartment: HR, Engineering, Sales\nsalary: 30000 to 200000\n\nRequirements: Generate 100 employees",
  "thread_id": "test-thread-001"
}
```

**Existing Schema Request:**
```json
{
  "config_name": "json_schema_test_data_generator_v2",
  "user_request": "schema: {...}\n\nRequirements: Generate 100 records",
  "thread_id": "test-thread-002"
}
```

---

## Testing

### Run the Test Suite

```bash
# Activate virtual environment
source .venv/bin/activate

# Run comprehensive tests
python temp_tests/test_schema_creator_v2.py
```

### Test Cases

1. **Plain English Workflow**: Verifies schema creation from description
2. **Existing Schema Workflow**: Verifies traditional schema analysis
3. **Supervisor Routing**: Verifies correct workflow selection

---

## Benefits

### ✅ Faster Development
- No need to manually write JSON Schema
- Describe data structure in plain English
- Auto-generates complete, valid schema

### ✅ Reduced Errors
- Consistent naming conventions (snake_case)
- Automatic constraint inference
- Built-in validation rules

### ✅ Better Documentation
- Schema creator explains design decisions
- Self-documenting field descriptions
- Clear type and constraint mappings

### ✅ Flexibility
- Works with plain English or formal schemas
- Backward compatible with existing workflows
- Supports all JSON Schema Draft 2020-12 features

---

## Troubleshooting

### Issue: Supervisor uses wrong workflow

**Symptom:** Plain English input goes to schema_analyzer instead of schema_creator

**Solution:** Ensure input doesn't contain JSON Schema keywords like `"$schema"`, `"properties"`, or `"type": "object"`. Use plain English descriptions only.

### Issue: Generated schema has wrong types

**Symptom:** Integer fields are generated as strings

**Solution:** Be explicit in your description:
- ❌ "age: years" → might infer as string
- ✅ "age: 18 to 100" → infers as integer with range

### Issue: Field names not in snake_case

**Symptom:** Fields like "StudentName" instead of "student_name"

**Solution:** This should auto-convert. If not, check schema_creator prompt is loaded correctly.

---

## Advanced Usage

### Custom Patterns

```
user_id: format UID-XXXXXX where X is uppercase letter or digit
email: valid email address
phone: format +1-XXX-XXX-XXXX
```

### Nested Objects

```
user:
  - user_id: unique ID
  - user_name: full name
  - address:
    - street: street address
    - city: city name
    - zip: 5 digit zip code
```

### Arrays

```
tags: list of 1 to 10 strings
scores: array of numbers from 0 to 100
categories: multiple selections from: A, B, C, D, E
```

---

## Compatibility

- ✅ Python 3.8+
- ✅ JSON Schema Draft 2020-12
- ✅ All existing agents (analyzer, parser, generator, validator)
- ✅ Large data handling (1000+ records)
- ✅ MCP servers (python_runner, large_data_storage)

---

## Migration from V1

No migration needed! V2 is fully backward compatible:

1. Keep using existing schema-based workflows
2. Start using plain English for new schemas
3. Mix and match as needed

---

## Future Enhancements

Potential future additions:
- [ ] Support for complex nested schemas
- [ ] Auto-detection of relationships (foreign keys)
- [ ] Schema templates for common domains
- [ ] Interactive schema refinement
- [ ] Export schemas to multiple formats

---

## Support

For issues or questions:
1. Check this documentation
2. Review test cases in `temp_tests/test_schema_creator_v2.py`
3. Examine supervisor routing logic in config
4. Test with `python temp_tests/test_schema_creator_v2.py`

---

## License

Same as jk-agents-core project license.
