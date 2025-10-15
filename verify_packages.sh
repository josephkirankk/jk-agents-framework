#!/bin/bash

# Package Verification Script for JSON Schema Test Data Generator
# This script verifies that all required packages are installed

echo "=========================================="
echo "Package Verification Script"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall status
ALL_OK=true

echo "Checking Python environment..."
echo ""

# Check Python version
PYTHON_VERSION=$(python --version 2>&1)
echo "Python version: $PYTHON_VERSION"
echo ""

# Check if uv is available
if command -v uv &> /dev/null; then
    echo -e "${GREEN}✅ uv package manager found${NC}"
else
    echo -e "${YELLOW}⚠️  uv not found, using pip${NC}"
fi
echo ""

echo "=========================================="
echo "Checking Required Packages"
echo "=========================================="
echo ""

# Function to check if a package is installed
check_package() {
    local package_name=$1
    local min_version=$2
    
    if uv pip list 2>/dev/null | grep -q "^$package_name"; then
        local installed_version=$(uv pip list 2>/dev/null | grep "^$package_name" | awk '{print $2}')
        echo -e "${GREEN}✅ $package_name${NC} (version: $installed_version)"
        return 0
    else
        echo -e "${RED}❌ $package_name${NC} (NOT INSTALLED)"
        ALL_OK=false
        return 1
    fi
}

# Core packages for JSON Schema Test Data Generator
echo "Core Packages:"
check_package "jsonschema" "4.20.0"
check_package "rstr" "3.2.0"
check_package "faker" "18.0.0"
echo ""

# Dependencies
echo "Dependencies:"
check_package "jsonschema-specifications"
check_package "referencing"
check_package "rpds-py"
echo ""

# Framework packages
echo "Framework Packages:"
check_package "langchain"
check_package "langgraph"
check_package "fastapi"
check_package "pydantic"
echo ""

echo "=========================================="
echo "Testing Package Imports"
echo "=========================================="
echo ""

# Test jsonschema import
echo -n "Testing jsonschema import... "
if python -c "from jsonschema import validate, Draft202012Validator, ValidationError; print('OK')" 2>/dev/null | grep -q "OK"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
    ALL_OK=false
fi

# Test rstr import
echo -n "Testing rstr import... "
if python -c "import rstr; print('OK')" 2>/dev/null | grep -q "OK"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
    ALL_OK=false
fi

# Test faker import
echo -n "Testing faker import... "
if python -c "from faker import Faker; print('OK')" 2>/dev/null | grep -q "OK"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
    ALL_OK=false
fi

echo ""

echo "=========================================="
echo "Testing Package Functionality"
echo "=========================================="
echo ""

# Test jsonschema validation
echo -n "Testing jsonschema validation... "
if python -c "
from jsonschema import validate, Draft202012Validator
schema = {'type': 'object', 'required': ['name'], 'properties': {'name': {'type': 'string'}}}
data = {'name': 'test'}
validator = Draft202012Validator(schema)
validator.validate(data)
print('OK')
" 2>/dev/null | grep -q "OK"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
    ALL_OK=false
fi

# Test rstr pattern generation
echo -n "Testing rstr pattern generation... "
if python -c "
import rstr
pattern = r'^[A-Z0-9-_.]{2,10}$'
result = rstr.xeger(pattern)
print('OK')
" 2>/dev/null | grep -q "OK"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
    ALL_OK=false
fi

# Test faker data generation
echo -n "Testing faker data generation... "
if python -c "
from faker import Faker
fake = Faker()
name = fake.name()
print('OK')
" 2>/dev/null | grep -q "OK"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
    ALL_OK=false
fi

echo ""

echo "=========================================="
echo "Configuration File Check"
echo "=========================================="
echo ""

# Check if config file exists
if [ -f "config/json_schema_test_data_generator.yaml" ]; then
    echo -e "${GREEN}✅ Configuration file found${NC}"
    echo "   Path: config/json_schema_test_data_generator.yaml"
else
    echo -e "${RED}❌ Configuration file NOT found${NC}"
    ALL_OK=false
fi

echo ""

echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""

if [ "$ALL_OK" = true ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo ""
    echo "The JSON Schema Test Data Generator is ready to use."
    echo ""
    echo "Next steps:"
    echo "  1. Start the API:"
    echo "     python api.py --config config/json_schema_test_data_generator.yaml"
    echo ""
    echo "  2. Test with curl:"
    echo "     ./test_curl_request.sh"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Some checks failed!${NC}"
    echo ""
    echo "Please fix the issues above before using the generator."
    echo ""
    echo "To install missing packages:"
    echo "  uv pip install -r requirements.txt"
    echo ""
    echo "Or install specific packages:"
    echo "  uv pip install jsonschema>=4.20.0 rstr>=3.2.0 faker>=18.0.0"
    echo ""
    exit 1
fi

