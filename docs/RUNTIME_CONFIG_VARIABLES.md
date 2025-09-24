# Runtime Configuration Variables System

The JK-Agents framework now supports **runtime configuration variables** for multi-environment setups, making it easy to manage configurations across development, staging, and production environments.

## 🚀 Quick Start

### 1. Set Your ADO Organization

Edit `config/vars.local.yaml` and replace the placeholder:

```yaml
# Replace 'contoso' with your actual Azure DevOps organization name
ado_organization: "your-ado-org-name"
```

### 2. Use in Configuration Files

In your YAML configurations, reference variables using `{{variable_name}}` syntax:

```yaml
mcp_servers:
  ado_server:
    transport: "stdio"
    command: "npx"
    args:
      - "-y"
      - "@azure-devops/mcp"
      - "{{ado_organization}}"  # Automatically resolved at runtime
```

### 3. Test the System

Run the verification test:

```bash
python test_config_variables.py
```

## 📋 How It Works

### Configuration File Loading Order

The system automatically loads configuration variables from these files (in order):

1. `config/vars.yaml` (shared defaults)
2. `config/vars.local.yaml` (local overrides - **gitignored**)
3. `config/variables.yaml` (alternative naming)
4. `config/variables.local.yaml` (alternative naming - **gitignored**)
5. `config/vars.{ENVIRONMENT}.yaml` (environment-specific)

### Environment-Specific Configurations

Set the `ENVIRONMENT` variable to load specific configurations:

```bash
# Load config/vars.development.yaml
export ENVIRONMENT=development

# Load config/vars.production.yaml  
export ENVIRONMENT=production

# Load config/vars.staging.yaml
export ENVIRONMENT=staging
```

### Available Configuration Files

The test script automatically creates these example files:

- **`config/vars.local.yaml`** - Your local development settings (gitignored)
- **`config/vars.production.yaml`** - Production environment settings
- **`config/vars.staging.yaml`** - Staging environment settings

## 🛠️ Configuration Variables

### ADO-Specific Variables

```yaml
# Azure DevOps Configuration
ado_organization: "your-org-name"
api_timeout: 120
max_retries: 3
```

### Environment Settings

```yaml
environment: "development"
debug_mode: true
log_level: "INFO"
```

### Feature Flags

```yaml
enable_fast_track_routing: true
enable_performance_monitoring: true
mock_external_services: false
```

## 🔧 Integration with Existing Placeholders

The configuration system integrates seamlessly with the existing placeholder system:

### System Placeholders
- `{{timestamp}}` - Current timestamp
- `{{date}}` - Current date
- `{{platform}}` - Operating system

### Agent Placeholders
- `{{agent_name}}` - Current agent name
- `{{mcpservers}}` - Available MCP servers

### Context Placeholders
- `{{business_context}}` - Business context
- `{{dependent_request_responses}}` - Previous step results

### Configuration Placeholders (NEW)
- `{{ado_organization}}` - Your ADO organization
- `{{environment}}` - Current environment
- `{{debug_mode}}` - Debug mode flag
- Any variable you define in config files!

## 📁 File Structure

```
config/
├── vars.local.yaml              # Local config (gitignored)
├── vars.production.yaml         # Production settings
├── vars.staging.yaml           # Staging settings
├── vars.yaml                   # Shared defaults (optional)
└── ado_realtime_analysis_optimized.yaml  # Uses {{ado_organization}}
```

## 🔐 Security Best Practices

### Sensitive Configuration

For sensitive values, use local files that are gitignored:

```yaml
# config/vars.local.yaml (gitignored)
ado_organization: "my-real-org"
api_key: "secret-key"
database_url: "connection-string"
```

### Environment Variables

You can also reference environment variables:

```yaml
# In your config files, you can still use environment variables
api_key: "${API_KEY}"  # Shell-style expansion (if supported)
```

## 🧪 Testing Your Configuration

### Run the Test Suite

```bash
python test_config_variables.py
```

Expected output:
```
🎉 All tests passed! Configuration variables system is working correctly.

💡 Next Steps:
   1. Update config/vars.local.yaml with your actual ADO organization
   2. Use the optimized ADO config: config/ado_realtime_analysis_optimized.yaml
   3. Run queries and see the fast-track routing in action!
```

### Manual Testing

Check available variables:

```python
from app.placeholder_system.context import PlaceholderContext

context = PlaceholderContext()
vars = context.build_context()
print(f"ADO Organization: {vars.get('ado_organization', 'not found')}")
```

## 🚀 Production Deployment

### 1. Environment-Specific Files

Create environment-specific configuration files:

```bash
# Production
cat > config/vars.production.yaml << EOF
ado_organization: "prod-org"
environment: "production"
debug_mode: false
api_timeout: 180
log_level: "WARNING"
EOF

# Staging
cat > config/vars.staging.yaml << EOF
ado_organization: "staging-org"
environment: "staging"
debug_mode: true
api_timeout: 150
log_level: "INFO"
EOF
```

### 2. Set Environment Variable

```bash
# In your deployment script or container
export ENVIRONMENT=production

# Then run your application
python -m app.main "get my work items" --config config/ado_realtime_analysis_optimized.yaml
```

### 3. Verify Configuration

```bash
# Check which variables are loaded
python -c "
from app.placeholder_system.config_provider import ConfigPlaceholderProvider
provider = ConfigPlaceholderProvider()
print('Loaded files:', provider.get_loaded_files())
print('Variables:', provider.get_all_variables())
"
```

## 🎯 ADO Configuration Example

Here's how the optimized ADO configuration uses runtime variables:

```yaml
# config/ado_realtime_analysis_optimized.yaml
agents:
  - name: "ado_quick_query_agent"
    mcp_servers:
      ado_server:
        transport: "stdio"
        command: "npx"
        args:
          - "-y"
          - "@azure-devops/mcp"
          - "{{ado_organization}}"  # 🎯 Resolved at runtime!
```

When you run this configuration:

1. System loads `config/vars.local.yaml`
2. Finds `ado_organization: "your-org"`
3. Replaces `{{ado_organization}}` with `"your-org"`
4. Final command becomes: `npx -y @azure-devops/mcp your-org`

## 🔄 Dynamic Reloading

For development, you can reload configuration at runtime:

```python
from app.placeholder_system.config_provider import ConfigPlaceholderProvider
from app.placeholder_system.registry import get_default_registry

# Get the config provider
registry = get_default_registry()
for provider in registry.get_providers():
    if provider.get_name() == "config":
        provider.reload_config()
        print("Configuration reloaded!")
        break
```

## 🐛 Troubleshooting

### Common Issues

1. **Variable not found**
   ```
   PlaceholderNotFoundError: ado_organization
   ```
   **Solution**: Check that `config/vars.local.yaml` exists and contains the variable.

2. **File not loading**
   ```
   Loaded 0 variables from 0 files
   ```
   **Solution**: Ensure you're running from the project root directory.

3. **Permission issues**
   ```
   Failed to load config file: Permission denied
   ```
   **Solution**: Check file permissions: `chmod 644 config/vars.local.yaml`

### Debugging

Enable debug logging:

```python
import logging
logging.getLogger("config_provider").setLevel(logging.DEBUG)
logging.getLogger("placeholder_registry").setLevel(logging.DEBUG)
```

### Reset Configuration

Remove all local config files:

```bash
rm -f config/vars.local.yaml config/vars.*.yaml
python test_config_variables.py  # Recreates examples
```

## 📚 Advanced Usage

### Custom Variable Providers

You can create custom configuration providers:

```python
from app.placeholder_system.config_provider import ConfigPlaceholderProvider
from app.placeholder_system.registry import get_default_registry

# Create custom provider
class DatabaseConfigProvider(ConfigPlaceholderProvider):
    def get_name(self):
        return "database"
    
    def get_supported_placeholders(self):
        return {"db_host", "db_port", "db_name"}

# Register with registry
registry = get_default_registry()
registry.register_provider(DatabaseConfigProvider(), priority=5)
```

### Runtime Variable Injection

Add variables programmatically:

```python
from app.placeholder_system.context import PlaceholderContext

context = PlaceholderContext()
context.add_custom_placeholder("runtime_value", "dynamic-data")
vars = context.build_context()
```

## 🎉 Summary

The runtime configuration variables system provides:

✅ **Multi-environment support** - Development, staging, production configs  
✅ **Secure by default** - Local configs are gitignored  
✅ **Framework integration** - Works with existing placeholder system  
✅ **Easy maintenance** - Single place to manage all variables  
✅ **Fast performance** - Variables cached during execution  
✅ **Full testing** - Comprehensive test suite included  

**Next Steps**: Update your `config/vars.local.yaml` with your actual ADO organization and start using the optimized configuration!