#!/bin/bash
# Run any command with production environment configuration

# Set the environment variable for this session
export ENVIRONMENT=production

# Display header
echo "🏭 Running with PRODUCTION environment"
echo "Loading configuration from: config/vars.production.yaml"
echo "=================================================="

# Execute the command
"$@"
