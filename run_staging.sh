#!/bin/bash
# Run any command with staging environment configuration

# Set the environment variable for this session
export ENVIRONMENT=staging

# Display header
echo "🔍 Running with STAGING environment"
echo "Loading configuration from: config/vars.staging.yaml"
echo "=================================================="

# Execute the command
"$@"
