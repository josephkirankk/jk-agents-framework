#!/bin/bash
# Database Path Fix Verification Script

echo "=================================="
echo "  Database Path Fix Verification"
echo "=================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python files
echo -e "\n[1] Checking MCP server code changes..."

if grep -q "LARGE_DATA_SQLITE_PATH" app/mcp_python_wrapper.py; then
    echo -e "${GREEN}✓${NC} mcp_python_wrapper.py has environment variable support"
else
    echo -e "${RED}✗${NC} mcp_python_wrapper.py missing environment variable support"
fi

if grep -q "LARGE_DATA_SQLITE_PATH" app/mcp_large_data_server.py; then
    echo -e "${GREEN}✓${NC} mcp_large_data_server.py has environment variable support"
else
    echo -e "${RED}✗${NC} mcp_large_data_server.py missing environment variable support"
fi

# Check config files
echo -e "\n[2] Checking config file updates..."

config_file="config/json_schema_test_data_generator.yaml"
if [ -f "$config_file" ]; then
    env_count=$(grep -c "LARGE_DATA_SQLITE_PATH" "$config_file")
    if [ "$env_count" -ge 4 ]; then
        echo -e "${GREEN}✓${NC} $config_file has $env_count env var definitions (expected ≥4)"
    else
        echo -e "${RED}✗${NC} $config_file has $env_count env var definitions (expected ≥4)"
    fi
else
    echo -e "${RED}✗${NC} $config_file not found"
fi

config_file_v2="config/json_schema_test_data_generator_v2.yaml"
if [ -f "$config_file_v2" ]; then
    env_count=$(grep -c "LARGE_DATA_SQLITE_PATH" "$config_file_v2")
    if [ "$env_count" -ge 4 ]; then
        echo -e "${GREEN}✓${NC} $config_file_v2 has $env_count env var definitions (expected ≥4)"
    else
        echo -e "${RED}✗${NC} $config_file_v2 has $env_count env var definitions (expected ≥4)"
    fi
else
    echo -e "${RED}✗${NC} $config_file_v2 not found"
fi

# Validate YAML syntax
echo -e "\n[3] Validating YAML syntax..."

if python3 -c "import yaml; yaml.safe_load(open('$config_file'))" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} $config_file syntax is valid"
else
    echo -e "${RED}✗${NC} $config_file has YAML syntax errors"
fi

if python3 -c "import yaml; yaml.safe_load(open('$config_file_v2'))" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} $config_file_v2 syntax is valid"
else
    echo -e "${RED}✗${NC} $config_file_v2 has YAML syntax errors"
fi

# Check database paths
echo -e "\n[4] Verifying database path configuration..."

db_path=$(python3 -c "
import yaml
c = yaml.safe_load(open('$config_file'))
print(c['large_data_handling']['large_data']['sqlite_path'])
" 2>/dev/null)

echo "   Config large_data_handling.large_data.sqlite_path: $db_path"

agent_db_path=$(python3 -c "
import yaml
c = yaml.safe_load(open('$config_file'))
agent = c['agents'][3]  # data_generator
env = agent['mcp_servers']['python_runner'].get('env', {})
print(env.get('LARGE_DATA_SQLITE_PATH', 'NOT SET'))
" 2>/dev/null)

echo "   Agent MCP server LARGE_DATA_SQLITE_PATH: $agent_db_path"

if [ "$db_path" == "$agent_db_path" ]; then
    echo -e "${GREEN}✓${NC} Database paths match!"
else
    echo -e "${RED}✗${NC} Database paths DO NOT match!"
fi

# Clean old databases
echo -e "\n[5] Cleaning old test databases..."

if [ -f "./data/large_data_storage.db" ]; then
    echo -e "${YELLOW}⚠${NC}  Found old database: ./data/large_data_storage.db"
    echo "   Consider removing: rm ./data/large_data_storage.db"
else
    echo -e "${GREEN}✓${NC} No old database found"
fi

# Summary
echo -e "\n=================================="
echo "  Verification Complete"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Restart API server: uvicorn api:app --host 0.0.0.0 --port 8000"
echo "2. Run test request with curl command"
echo "3. Verify data is stored in ./data/schema_test_data.db"
echo ""
