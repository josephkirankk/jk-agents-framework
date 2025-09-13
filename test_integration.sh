#!/bin/bash

echo "🧪 Testing JK-Agents with Custom OpenAI Endpoint Integration"
echo "============================================================"

# Test 1: Basic worker request
echo "📝 Test 1: Basic Agent Request"
curl -X POST "http://localhost:8001/worker" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "custom_assistant",
    "input": "Say hello and confirm you are working correctly",
    "config_path": "config/openai_custom_endpoint.yaml"
  }' | jq .

echo -e "\n"

# Test 2: Different agent
echo "📝 Test 2: Creative Agent Request"
curl -X POST "http://localhost:8001/worker" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "custom_creative",
    "input": "Write a short haiku about AI",
    "config_path": "config/openai_custom_endpoint.yaml"
  }' | jq .

echo -e "\n"

# Test 3: Health check
echo "📝 Test 3: API Health Check"
curl -X GET "http://localhost:8001/health" | jq .

echo -e "\n"

# Test 4: Custom service health
echo "📝 Test 4: Custom Service Health"
curl -X GET "http://localhost:8080/health/" | jq .

echo -e "\n"

# Test 5: Available models
echo "📝 Test 5: Available Models"
curl -X GET "http://localhost:8080/v1/models" \
  -H "Authorization: Bearer sk-test-key1" | jq .

echo -e "\n✅ Integration tests complete!"
