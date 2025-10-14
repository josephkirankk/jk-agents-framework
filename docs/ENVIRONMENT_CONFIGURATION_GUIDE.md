# Environment Configuration Guide

This guide explains how to use the environment configuration system in the JK-Agents Framework, including how to switch between different environments (development, staging, production).

## Configuration Files

The framework uses YAML files in the `config/` directory to manage environment-specific settings:

- `vars.local.yaml` - Your local development settings (gitignored)
- `vars.production.yaml` - Production environment settings
- `vars.staging.yaml` - Staging environment settings
- `vars.yaml` - Shared defaults (optional)

## Switching Environments

### Method 1: Environment Variable

Set the `ENVIRONMENT` variable before running your code:

```bash
# Use production settings
export ENVIRONMENT=production
python your_script.py

# Use staging settings
export ENVIRONMENT=staging
python your_script.py
```

### Method 2: Helper Scripts

Use the provided helper scripts to run commands with specific environments:

```bash
# Run with production environment
./run_production.sh python your_script.py

# Run with staging environment
./run_staging.sh python your_script.py
```

### Method 3: Python Helper

The `run_with_env.py` script provides more flexibility:

```bash
# Run with production environment
python run_with_env.py production python your_script.py [args]

# Run with staging environment
python run_with_env.py staging python your_script.py [args]

# List available environments
python run_with_env.py --list
```

## Available Environment Configurations

### Production (`vars.production.yaml`)

```yaml
ado_organization: "your-prod-org"
environment: "production"
debug_mode: false
api_timeout: 180
max_retries: 5
log_level: "WARNING"
enable_fast_track_routing: true
enable_performance_monitoring: true
mock_external_services: false
```

### Staging (`vars.staging.yaml`)

```yaml
ado_organization: "your-staging-org"
environment: "staging"
debug_mode: true
api_timeout: 150
max_retries: 3
log_level: "INFO"
enable_performance_monitoring: true
mock_external_services: false
```

## Using Configuration Variables in YAML Files

Configuration variables can be used in YAML files with double curly braces:

```yaml
agents:
  python_agent:
    args: ["-y", "@azure-devops/mcp", "{{ ado_organization }}"]
```

## Testing Configuration

Run the configuration test script to verify your settings:

```bash
python test_config_variables.py
```

This will show which configuration files are loaded and what variables are available.

## Creating Custom Environments

To create a new environment:

1. Create a new file: `config/vars.<environment_name>.yaml`
2. Add your environment-specific settings
3. Use it with: `export ENVIRONMENT=<environment_name>`

## Best Practices

1. **Keep sensitive data in `vars.local.yaml`** - This file is gitignored
2. **Use environment-specific configs for deployment settings**
3. **Use `vars.yaml` for shared defaults** across all environments
4. **Test configurations** before deployment using `test_config_variables.py`
