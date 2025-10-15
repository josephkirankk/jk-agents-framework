# Schema Creator V2 - Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Describe Your Data Structure

Write your data structure in plain English:

```
user_id: unique identifier
username: 3-20 characters
email: valid email address
age: 18 to 100
role: admin, user, guest
is_active: true or false
created_at: date time format

Requirements: Generate 50 users with realistic data
```

### Step 2: Run the Workflow

```bash
# Activate environment
source .venv/bin/activate

# Use the API or test directly
python temp_tests/test_schema_creator_v2.py
```

### Step 3: Get Your Data

The system will:
1. ✅ Create JSON Schema from your description
2. ✅ Generate 50 test records
3. ✅ Validate all data
4. ✅ Return data or reference ID

---

## 📋 Input Format Examples

### Example 1: Employee Records
```
employee_id: unique ID
full_name: employee full name
department: Engineering, Sales, HR, Marketing
salary: 30000 to 200000
hire_date: date format
years_of_service: 0 to 40

Generate 100 employee records
```

### Example 2: Product Catalog
```
product_id: format PROD-NNNNNN
product_name: 5-100 characters
category: Electronics, Clothing, Food, Books, Toys
price: 1.00 to 10000.00
stock_quantity: 0 to 1000
rating: 1.0 to 5.0
available: yes or no

Generate 200 products across all categories
```

### Example 3: Transaction Logs
```
transaction_id: unique UUID
user_id: format USR-XXXXX
amount: 0.01 to 10000.00
currency: USD, EUR, GBP, JPY
status: pending, completed, failed, refunded
timestamp: date time with timezone
description: transaction details

Generate 500 transactions for the last 3 months
```

---

## 🔧 Type Mapping Cheat Sheet

| Your Description | Inferred Type | Schema |
|-----------------|---------------|---------|
| `name`, `title` | string | `{"type": "string"}` |
| `email address` | string+format | `{"type": "string", "format": "email"}` |
| `date`, `YYYY-MM-DD` | string+date | `{"type": "string", "format": "date"}` |
| `timestamp`, `datetime` | string+datetime | `{"type": "string", "format": "date-time"}` |
| `age`, `count` | integer | `{"type": "integer"}` |
| `N to M` | integer+range | `{"minimum": N, "maximum": M}` |
| `price`, `rating` | number | `{"type": "number"}` |
| `X.XX to Y.YY` | number+range | `{"minimum": X.XX, "maximum": Y.YY}` |
| `A, B, C` | enum | `{"enum": ["A", "B", "C"]}` |
| `yes/no`, `true/false` | boolean | `{"type": "boolean"}` |
| `URL`, `link` | string+uri | `{"type": "string", "format": "uri"}` |
| `UUID`, `guid` | string+uuid | `{"type": "string", "format": "uuid"}` |

---

## ⚡ Common Patterns

### Pattern 1: ID Fields
```
user_id: format UID-XXXXXX        → pattern: ^UID-[A-Z0-9]{6}$
order_id: format ORD-NNNNNNNN    → pattern: ^ORD-[0-9]{8}$
product_code: 6-10 alphanumeric  → pattern: ^[A-Z0-9]{6,10}$
```

### Pattern 2: Dates
```
birth_date: date format           → format: date
created_at: timestamp             → format: date-time
year: YYYY format                 → type: integer, pattern: ^[0-9]{4}$
```

### Pattern 3: Ranges
```
age: 18 to 65                     → minimum: 18, maximum: 65
price: 0.01 to 9999.99           → minimum: 0.01, maximum: 9999.99
quantity: at least 1              → minimum: 1
rating: up to 5                   → maximum: 5
```

### Pattern 4: Enumerations
```
status: pending, active, closed   → enum: ["pending", "active", "closed"]
size: S, M, L, XL                → enum: ["S", "M", "L", "XL"]
priority: low, medium, high       → enum: ["low", "medium", "high"]
```

---

## 💡 Tips & Best Practices

### ✅ DO:
- Be specific about ranges: "1 to 100" not just "number"
- List all enum options: "red, blue, green"
- Specify formats: "email address", "date format", "UUID"
- Include constraints: "3-50 characters", "at least 1"

### ❌ DON'T:
- Mix JSON Schema syntax with plain English
- Use vague descriptions: "some value", "data"
- Forget to specify requirements separately
- Include example data in the description

---

## 🔍 Troubleshooting

### Q: My field is generated as string but should be integer
**A:** Be explicit: "age: 18 to 100" not "age: years"

### Q: Enums not detected
**A:** Use comma-separated: "status: pending, active, closed"

### Q: Custom pattern not working
**A:** Specify format: "user_id: format UID-XXXXXX"

### Q: Generated schema looks wrong
**A:** Check the schema_creator output for explanations

---

## 📊 Workflow Comparison

### Plain English (NEW)
```
Input: Plain English description
  ↓
schema_creator: Generate JSON Schema
  ↓
requirement_parser: Parse requirements
  ↓
data_generator: Generate test data
  ↓
schema_validator: Validate data
  ↓
Output: Reference ID or data
```

### Existing Schema (Traditional)
```
Input: JSON Schema
  ↓
schema_analyzer: Analyze schema
  ↓
requirement_parser: Parse requirements
  ↓
data_generator: Generate test data
  ↓
schema_validator: Validate data
  ↓
Output: Reference ID or data
```

---

## 🎯 When to Use Which

### Use Plain English When:
- ✅ Prototyping new data structures
- ✅ Quick test data generation
- ✅ Non-technical team members defining schemas
- ✅ Exploratory data modeling

### Use Existing Schema When:
- ✅ Working with established APIs
- ✅ Precise control over validation rules
- ✅ Complex nested structures
- ✅ Integration with existing systems

---

## 🧪 Testing

### Quick Test
```bash
python temp_tests/test_schema_creator_v2.py
```

### API Test
```bash
curl -X POST http://localhost:8000/api/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "config_name": "json_schema_test_data_generator_v2",
    "user_request": "user_id: unique\nusername: 3-20 chars\nemail: email\n\nGenerate 50 users"
  }'
```

---

## 📚 More Examples

See full documentation: `temp_docs/JSON_SCHEMA_CREATOR_V2_README.md`

Test scripts: `temp_tests/test_schema_creator_v2.py`

Configuration: `config/json_schema_test_data_generator_v2.yaml`

---

## ⚙️ Configuration

Using v2 config:
```python
from app.config import load_app_config
config = load_app_config("config/json_schema_test_data_generator_v2.yaml")
```

Check loaded agents:
```python
print(config.get('agents'))  # Should include schema_creator
```

---

## 🆘 Support

1. Check syntax with: `python -c "import yaml; yaml.safe_load(open('config/json_schema_test_data_generator_v2.yaml'))"`
2. Run tests: `python temp_tests/test_schema_creator_v2.py`
3. Review logs in `agentlogs/` directory
4. Verify config loads: `python -c "from app.config import load_app_config; print(load_app_config('config/json_schema_test_data_generator_v2.yaml'))"`

---

**Ready to generate test data? Start with plain English! 🎉**
