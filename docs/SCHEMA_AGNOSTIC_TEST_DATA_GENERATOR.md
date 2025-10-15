# Schema-Agnostic Test Data Generator - Complete Guide

## Overview

The JSON Schema Test Data Generator has been completely redesigned to be **fully schema-agnostic**. This means it can dynamically adapt to **any JSON Schema** from **any domain** without requiring manual configuration changes or hardcoded assumptions.

## Key Principles

### 1. Zero Hardcoding
- **No hardcoded field names**: Works with any field names from any domain
- **No domain assumptions**: Adapts to healthcare, finance, education, IoT, manufacturing, etc.
- **No schema-specific logic**: Dynamically processes any schema structure
- **No fixed patterns**: Generates data for any regex, format, or validation rule

### 2. Dynamic Adaptation
- Analyzes schema structure on-the-fly
- Extracts metadata without assumptions
- Generates data based on discovered constraints
- Validates against the original schema

### 3. Universal Compatibility
- Works with any valid JSON Schema Draft 2020-12
- Supports all JSON Schema features comprehensively
- Handles simple and complex schemas equally well

## What Changed?

### Before (Schema-Specific)
The previous version had hardcoded references to specific domains:

```yaml
# ❌ OLD - Hardcoded examples
- "Create 100 records for program prg1 with metric defect_rate between 1 and 100"
- "Generate 50 records for manufacturing sector with throughput 10-500 items/hour"

# ❌ OLD - Hardcoded field extraction
if 'student' in requirement.lower():
    constraints["field_constraints"]["no_of_students"] = {...}

# ❌ OLD - Hardcoded pattern matching
if pattern == r'^[A-Z0-9-_.]{2,32}$':
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.', k=length))
```

### After (Schema-Agnostic)
The new version dynamically adapts to any schema:

```yaml
# ✅ NEW - Generic examples
- "Create [N] records with [field_name] between [min] and [max]"
- "Generate [N] records where [field_name] is [value]"

# ✅ NEW - Dynamic field extraction
range_pattern = r'(\w+(?:\s+\w+)?)\s+(?:between|from|range|ranging)\s+(\d+(?:\.\d+)?)\s+(?:and|to)\s+(\d+(?:\.\d+)?)'
for field_hint, min_val, max_val in range_matches:
    field_key = field_hint.strip().lower().replace(' ', '_')
    constraints["field_constraints"][field_key] = {"min": float(min_val), "max": float(max_val)}

# ✅ NEW - Dynamic pattern generation
def generate_string_with_pattern(pattern):
    # Analyzes pattern and generates matching strings dynamically
    # Works with ANY regex pattern
```

## Comprehensive JSON Schema Support

### Supported Types
- `string`, `number`, `integer`, `boolean`, `object`, `array`, `null`
- Multi-type arrays: `["string", "null"]`, `["integer", "string"]`

### Supported Validation Keywords

#### String Validation
- `pattern`: Any regex pattern (dynamically analyzed)
- `format`: date, date-time, time, email, uri, uuid, ipv4, ipv6, hostname, etc.
- `minLength`, `maxLength`: Any length constraints
- `enum`: Any enumerated values
- `const`: Constant values

#### Numeric Validation
- `minimum`, `maximum`: Inclusive bounds
- `exclusiveMinimum`, `exclusiveMaximum`: Exclusive bounds
- `multipleOf`: Multiple constraints (e.g., multiples of 5)

#### Array Validation
- `items`: Any item schema (objects, primitives, nested arrays)
- `minItems`, `maxItems`: Size constraints
- `uniqueItems`: Uniqueness enforcement
- `contains`, `minContains`, `maxContains`: Content validation

#### Object Validation
- `properties`: Any property definitions
- `required`: Required property lists
- `additionalProperties`: Additional property rules
- `minProperties`, `maxProperties`: Property count constraints
- `propertyNames`: Property name patterns
- `dependencies`, `dependentRequired`, `dependentSchemas`: Dependencies

#### Composition Keywords
- `oneOf`: Exactly one schema must match
- `anyOf`: At least one schema must match
- `allOf`: All schemas must match
- `not`: Schema must not match

#### References
- `$ref`: References to definitions
- `$defs`: Reusable schema definitions
- `$id`, `$anchor`: Schema identification

### Supported Formats

The generator automatically handles all standard JSON Schema formats:

- **Date/Time**: `date`, `date-time`, `time`, `duration`
- **Email**: `email`, `idn-email`
- **Network**: `ipv4`, `ipv6`, `hostname`, `idn-hostname`
- **URI**: `uri`, `uri-reference`, `iri`, `iri-reference`, `uri-template`
- **Identifiers**: `uuid`, `json-pointer`, `relative-json-pointer`, `regex`

## Agent Updates

### 1. Schema Analyzer (schema_analyzer)

**Purpose**: Analyzes ANY JSON Schema and extracts comprehensive metadata

**Key Changes**:
- Extracts all validation keywords dynamically (no hardcoded list)
- Handles composition schemas (oneOf, anyOf, allOf)
- Supports const and multi-type fields
- Extracts nested object and array structures recursively

**Output**: Complete schema metadata including:
```json
{
  "schema_version": "draft/2020-12",
  "type": "object|array",
  "required_fields": ["field1", "field2"],
  "fields": {
    "any_field_name": {
      "type": "string|number|integer|boolean|object|array|null|[types]",
      "validation": {
        "const": "...",
        "enum": [...],
        "pattern": "...",
        "format": "...",
        "minimum": 0,
        "maximum": 100,
        "exclusiveMinimum": 0,
        "exclusiveMaximum": 100,
        "multipleOf": 5,
        "minLength": 1,
        "maxLength": 100,
        "minItems": 1,
        "maxItems": 10,
        "uniqueItems": true,
        "items": {...},
        "properties": {...},
        "required": [...],
        "additionalProperties": true|false|{...}
      },
      "oneOf": [...],
      "anyOf": [...],
      "allOf": [...]
    }
  }
}
```

### 2. Requirement Parser (requirement_parser)

**Purpose**: Parses natural language requirements without domain assumptions

**Key Changes**:
- Dynamic field name extraction from user input
- Generic time-based pattern matching (years, months, weeks, days)
- Flexible value range extraction
- List/array constraint parsing
- Boolean flag detection (unique, duplicates, sorting)

**Supported Patterns**:
```
Record Count:
- "Create 100 records"
- "Generate 50 items"

Field Values:
- "where [field] is [value]"
- "for [field] [value]"
- "with [field] equals [value]"

Value Ranges:
- "[field] between [min] and [max]"
- "[field] from [min] to [max]"
- "[field] ranging [min] to [max]"

Time Ranges:
- "last 5 years"
- "last 12 months"
- "last 30 days"

Lists:
- "with items A, B, C"
- "including X and Y"

Flags:
- "with unique values"
- "in ascending order"
```

### 3. Data Generator (data_generator)

**Purpose**: Generates schema-compliant test data for ANY schema

**Key Changes**:
- Dynamic pattern generation for any regex
- Comprehensive format support (all JSON Schema formats)
- Multi-type field handling
- Composition schema support (oneOf, anyOf, allOf)
- Const and enum handling
- Nested object and array generation with proper recursion
- Unique item enforcement for arrays
- Exclusive min/max and multipleOf support

**Generation Algorithm**:
1. Parse schema metadata and user constraints
2. For each record:
   - Process required fields first
   - Apply user constraints where specified
   - Generate values based on field type and validation rules
   - Handle composition schemas (select one option)
   - Recursively generate nested structures
   - Ensure all validation rules are satisfied
3. Return complete dataset (auto-stored if large)

### 4. Schema Validator (schema_validator)

**Purpose**: Validates generated data against the original schema

**No changes needed** - Already schema-agnostic using jsonschema library

## Usage Examples

### Example 1: E-commerce Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "order_id": {"type": "string", "pattern": "^ORD-[0-9]{6}$"},
    "customer_email": {"type": "string", "format": "email"},
    "total_amount": {"type": "number", "minimum": 0, "maximum": 10000},
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "product_id": {"type": "string"},
          "quantity": {"type": "integer", "minimum": 1, "maximum": 100}
        },
        "required": ["product_id", "quantity"]
      },
      "minItems": 1,
      "maxItems": 20
    }
  },
  "required": ["order_id", "customer_email", "total_amount", "items"]
}
```

**User Request**: "Generate 50 records with total_amount between 100 and 5000"

**Result**: 50 valid e-commerce orders with amounts in the specified range

### Example 2: Healthcare Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "patient_id": {"type": "string", "format": "uuid"},
    "admission_date": {"type": "string", "format": "date"},
    "diagnosis_code": {"type": "string", "pattern": "^[A-Z][0-9]{2}\\.[0-9]$"},
    "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
    "vitals": {
      "type": "object",
      "properties": {
        "heart_rate": {"type": "integer", "minimum": 40, "maximum": 200},
        "blood_pressure": {"type": "string", "pattern": "^[0-9]{2,3}/[0-9]{2,3}$"}
      }
    }
  }
}
```

**User Request**: "Create 100 records for the last 2 years with severity high or critical"

**Result**: 100 valid patient records with dates in the last 2 years

### Example 3: IoT Sensor Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "sensor_id": {"type": "string", "pattern": "^SENSOR-[A-Z0-9]{8}$"},
    "timestamp": {"type": "string", "format": "date-time"},
    "temperature": {"type": "number", "minimum": -50, "maximum": 150, "multipleOf": 0.1},
    "humidity": {"type": "number", "minimum": 0, "maximum": 100},
    "location": {
      "type": "object",
      "properties": {
        "latitude": {"type": "number", "minimum": -90, "maximum": 90},
        "longitude": {"type": "number", "minimum": -180, "maximum": 180}
      },
      "required": ["latitude", "longitude"]
    }
  }
}
```

**User Request**: "Generate 200 records with temperature between 20 and 30"

**Result**: 200 valid sensor readings with temperatures in the specified range

## Benefits

### 1. Universal Applicability
- Works with schemas from any domain without modification
- No need to update configuration for new schemas
- Reduces maintenance overhead

### 2. Flexibility
- Users can provide any schema structure
- Natural language requirements adapt to any field names
- Supports simple to highly complex schemas

### 3. Accuracy
- Generates data that strictly conforms to schema constraints
- Validates all generated data
- Handles edge cases and complex validation rules

### 4. Efficiency
- Automatic large dataset handling
- Optimized for generating 1000+ records
- Parallel processing where applicable

## Migration Guide

If you were using the old version with hardcoded schemas:

1. **No changes needed to your workflow** - The system is backward compatible
2. **Remove any schema-specific configuration** - No longer necessary
3. **Use generic natural language** - Field names are extracted dynamically
4. **Test with your schemas** - The system will adapt automatically

## Technical Implementation

### Pattern Generation Algorithm

The new pattern generator analyzes regex patterns dynamically:

```python
def generate_string_with_pattern(pattern):
    # Extract character classes
    # Extract length constraints ({n,m}, +, *, ?)
    # Identify special characters
    # Generate matching string
```

### Field Value Generation

The generator handles any field type:

```python
def generate_field_value(field_name, field_meta, constraints):
    # Check user constraints first
    # Handle composition schemas (oneOf, anyOf, allOf)
    # Handle const and enum
    # Handle null and multi-type
    # Generate based on type and validation rules
    # Recursively handle nested structures
```

## Conclusion

The schema-agnostic redesign makes the JSON Schema Test Data Generator a truly universal tool that can handle any valid JSON Schema without manual configuration. This significantly improves usability, reduces maintenance, and ensures accurate test data generation across all domains.

