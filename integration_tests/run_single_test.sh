#!/bin/bash
# Run a single test and capture output

cd "$(dirname "$0")"
../.venv/bin/pytest test_09_api_critical_flows.py::TestAPICriticalFlows::test_api_error_recovery -v --tb=short
