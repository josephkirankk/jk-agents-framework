# Schema-Agnostic Test Data Generator - Quick Start Guide

## What is Schema-Agnostic?

The test data generator now works with **ANY JSON Schema** from **ANY domain** without requiring configuration changes. Just provide:
1. Your JSON Schema
2. Your requirements in natural language

The system automatically adapts!

## Quick Examples

### Example 1: Simple Schema

**Your Schema:**
```json
{
  "type": "object",
  "properties": {
    "name": {"type": "string", "minLength": 3, "maxLength": 50},
    "age": {"type": "integer", "minimum": 0, "maximum": 120},
    "email": {"type": "string", "format": "email"}
  },
  "required": ["name", "email"]
}
```

**Your Request:**
```
Generate 100 records with age between 25 and 65
```

**What You Get:**
- 100 records
- All have valid names (3-50 chars) and emails
- Ages are between 25 and 65
- All records pass schema validation

### Example 2: Complex Nested Schema

**Your Schema:**
```json
{
  "type": "object",
  "properties": {
    "transaction_id": {"type": "string", "pattern": "^TXN-[0-9]{10}$"},
    "amount": {"type": "number", "minimum": 0, "multipleOf": 0.01},
    "currency": {"type": "string", "enum": ["USD", "EUR", "GBP", "JPY"]},
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "sku": {"type": "string"},
          "price": {"type": "number", "minimum": 0}
        }
      },
      "minItems": 1,
      "maxItems": 10
    }
  }
}
```

**Your Request:**
```
Create 50 records with amount between 100 and 1000 and currency USD or EUR
```

**What You Get:**
- 50 valid transactions
- Transaction IDs matching the pattern
- Amounts between 100-1000 (multiples of 0.01)
- Currency is USD or EUR
- Each transaction has 1-10 items with valid SKUs and prices

### Example 3: Time-Based Data

**Your Schema:**
```json
{
  "type": "object",
  "properties": {
    "event_id": {"type": "string", "format": "uuid"},
    "timestamp": {"type": "string", "format": "date-time"},
    "event_type": {"type": "string", "enum": ["login", "logout", "purchase", "view"]},
    "user_id": {"type": "integer", "minimum": 1000, "maximum": 9999}
  }
}
```

**Your Request:**
```
Generate 200 records for the last 30 days with event_type login or purchase
```

**What You Get:**
- 200 events
- Timestamps spread over the last 30 days
- Event types are login or purchase
- Valid UUIDs and user IDs

## Natural Language Patterns

### Record Count
```
"Create 100 records"
"Generate 50 items"
"Produce 200 entries"
```

### Field Constraints
```
"with [field_name] between [min] and [max]"
"where [field_name] is [value]"
"for [field_name] [value]"
```

### Time Ranges
```
"for the last 5 years"
"last 12 months"
"last 30 days"
"last 2 weeks"
```

### Lists and Arrays
```
"with items A, B, C"
"including X and Y"
"contains item1, item2"
```

### Special Flags
```
"with unique values"
"in ascending order"
"in descending order"
```

## Supported Schema Features

### All JSON Schema Types
✅ `string`, `number`, `integer`, `boolean`, `object`, `array`, `null`
✅ Multi-type: `["string", "null"]`

### String Validation
✅ `pattern` - Any regex pattern
✅ `format` - date, email, uri, uuid, ipv4, etc.
✅ `minLength`, `maxLength`
✅ `enum`, `const`

### Numeric Validation
✅ `minimum`, `maximum`
✅ `exclusiveMinimum`, `exclusiveMaximum`
✅ `multipleOf`

### Array Validation
✅ `items` - Any item type
✅ `minItems`, `maxItems`
✅ `uniqueItems`

### Object Validation
✅ `properties`, `required`
✅ `additionalProperties`
✅ Nested objects (any depth)

### Composition
✅ `oneOf`, `anyOf`, `allOf`

### References
✅ `$ref`, `$defs`

## How to Use

### Step 1: Prepare Your Schema
Save your JSON Schema in a file or have it ready as a JSON string.

### Step 2: Write Your Requirements
Use natural language to describe what you need:
- How many records?
- Any specific field constraints?
- Time ranges?
- Special conditions?

### Step 3: Run the Generator
The system will:
1. Analyze your schema (no matter how complex)
2. Parse your requirements
3. Generate compliant test data
4. Validate all records

### Step 4: Get Your Data
Receive a JSON array of records that:
- Match your schema exactly
- Meet your requirements
- Pass validation

## Common Use Cases

### 1. API Testing
Generate test data for API endpoints with any schema.

### 2. Database Seeding
Create realistic data for database testing.

### 3. Load Testing
Generate large datasets (1000+ records) efficiently.

### 4. Edge Case Testing
Create data with specific constraints to test edge cases.

### 5. Mock Data
Generate mock data for frontend development.

## Tips for Best Results

### 1. Be Specific with Constraints
```
✅ "Generate 100 records with age between 25 and 65"
❌ "Generate some records with ages"
```

### 2. Use Field Names from Your Schema
```
✅ "with transaction_amount between 100 and 1000"
❌ "with amount between 100 and 1000" (if field is named transaction_amount)
```

### 3. Combine Multiple Constraints
```
✅ "Create 50 records for the last 6 months with status active and priority high"
```

### 4. Leverage Enums
```
✅ "with currency USD or EUR" (if currency is an enum field)
```

## Advanced Features

### 1. Nested Object Generation
The system automatically handles nested objects at any depth.

### 2. Array Item Generation
Arrays are populated with items matching the item schema.

### 3. Pattern Matching
Any regex pattern is supported - the generator analyzes and creates matching strings.

### 4. Format Support
All JSON Schema formats are supported (date, email, uri, uuid, ipv4, ipv6, etc.).

### 5. Composition Schemas
oneOf, anyOf, allOf are handled automatically.

### 6. Large Dataset Handling
Datasets with 1000+ records are automatically optimized and stored efficiently.

## Troubleshooting

### Issue: Generated data doesn't match my constraints
**Solution**: Ensure field names in your requirements match the schema exactly.

### Issue: Validation fails
**Solution**: Check that your schema is valid JSON Schema Draft 2020-12.

### Issue: Not enough variation in data
**Solution**: The generator creates varied data automatically. For more control, specify ranges.

### Issue: Need specific enum values
**Solution**: Mention the enum values in your requirements: "with status active or pending"

## Examples by Domain

### E-commerce
```
Schema: orders, products, customers
Request: "Generate 100 orders with total_amount between 50 and 500"
```

### Healthcare
```
Schema: patients, appointments, diagnoses
Request: "Create 200 patient records for the last 2 years"
```

### Finance
```
Schema: transactions, accounts, portfolios
Request: "Generate 500 transactions with amount between 1000 and 10000"
```

### IoT
```
Schema: sensors, readings, devices
Request: "Create 1000 sensor readings with temperature between 20 and 30"
```

### Education
```
Schema: students, courses, grades
Request: "Generate 150 student records with gpa between 3.0 and 4.0"
```

### Manufacturing
```
Schema: products, batches, quality_checks
Request: "Create 300 quality check records with defect_rate between 0 and 5"
```

## Key Advantages

### 🚀 Zero Configuration
No need to modify the system for different schemas.

### 🎯 Accurate
Generates data that strictly conforms to your schema.

### 🔄 Flexible
Works with simple to highly complex schemas.

### ⚡ Fast
Efficiently generates large datasets.

### ✅ Validated
All generated data is validated against your schema.

### 🌍 Universal
Works across all domains and industries.

## Next Steps

1. **Try it with your schema** - The system adapts automatically
2. **Experiment with requirements** - Use natural language freely
3. **Generate test data** - Get validated, compliant data instantly
4. **Iterate** - Refine your requirements as needed

## Support

For detailed documentation, see:
- [Complete Schema-Agnostic Guide](./SCHEMA_AGNOSTIC_TEST_DATA_GENERATOR.md)
- [JSON Schema Test Data Generator](./JSON_SCHEMA_TEST_DATA_GENERATOR.md)

## Summary

The schema-agnostic test data generator is a universal tool that works with **any JSON Schema** from **any domain**. Just provide your schema and requirements - the system handles the rest!

**No configuration. No hardcoding. Just results.**

