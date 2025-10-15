# Multi-Model Integration Testing for JK-Agents Framework

## Overview

This document describes the implementation of multi-model and multi-turn integration tests for the JK-Agents Framework. The framework supports multiple model providers (Azure OpenAI, Google Gemini, OpenAI, Anthropic Claude) and allows for multi-turn conversations with context preservation.

## Integration Test Approaches

The integration tests are implemented in two ways:

1. **Full Stack Test (`test_litellm_multimodel_integration.py`)**: Tests the complete framework including the agent system, planning, execution, and memory.
2. **Direct Model Test (`test_multimodel_simple.py`)**: Tests just the model integration with simplified API calls.

## Prerequisites

To run the tests, the following prerequisites must be met:

1. **API Keys**: Valid API keys should be set in the `.env` file for at least one model provider:
   ```
   # Azure OpenAI
   AZURE_OPENAI_API_KEY=your_key
   AZURE_OPENAI_ENDPOINT=https://your_endpoint.openai.azure.com/
   AZURE_OPENAI_API_VERSION=2023-05-15
   
   # Google Gemini
   GOOGLE_API_KEY=your_key
   
   # OpenAI
   OPENAI_API_KEY=your_key
   
   # Anthropic
   ANTHROPIC_API_KEY=your_key
   ```

2. **Virtual Environment**: The tests should be run within the project's virtual environment:
   ```bash
   source .venv/bin/activate
   ```

## Test Components

### 1. Model Availability Test

Tests that configured models are accessible and responding correctly:

```python
async def _async_test_model_availability(self):
    for provider, model in self.available_models.items():
        result = await test_litellm_model(model, "What is 2+2?")
        # Verify result
```

### 2. Multi-Turn Conversation Test

Tests the conversation memory and context preservation:

```python
async def _async_test_multi_turn_conversation(self):
    # Turn 1: Ask about fruits
    messages_1 = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "List 3 fruits with their colors."}
    ]
    result_1 = await model.ainvoke(messages_1)
    
    # Turn 2: Ask about prices (referencing Turn 1)
    messages_2 = messages_1 + [
        {"role": "assistant", "content": result_1.content},
        {"role": "user", "content": "What's the average price for each?"}
    ]
    result_2 = await model.ainvoke(messages_2)
    
    # Verify context continuity
    for fruit in found_fruits:
        if fruit in result_2.content:
            # Context was preserved
```

### 3. Multi-Model Integration

Tests different models working together:

- Using Azure OpenAI for verification
- Using Google Gemini for execution
- Using a mix of models for different agents

## Design Decisions

1. **Test Isolation**: The `test_multimodel_simple.py` is designed to be more resilient to API changes and framework updates by focusing only on the core model functionality.

2. **API Keys Detection**: Tests automatically detect available API keys and adapt the test to use the available models, skipping tests when required keys aren't available.

3. **Verification Pattern**: The full stack test uses the detected model for verification instead of trying to disable verification, working with the framework's design instead of against it.

4. **Context Continuity Metric**: Tests include a context continuity score that measures how well the model maintains context across conversation turns.

## Running the Tests

Run the simplified test:
```bash
python tests/test_multimodel_simple.py
```

Run the full integration test:
```bash
python tests/test_litellm_multimodel_integration.py
```

Run all integration tests:
```bash
python run_integration_tests.py
```

## Handling API Key Absence

If no API keys are available, tests will be automatically skipped with appropriate messages:

```python
if not self.available_models:
    self.skipTest("No models available to test")
    return
```

## Troubleshooting

1. **Model Not Found Errors**: Verify the model name and provider format. Different providers use different naming conventions:
   - Azure OpenAI: `azure/gpt-4.1`
   - Google Gemini: `gemini/gemini-2.5-flash-lite`
   - OpenAI: `openai/gpt-4o-mini`
   - Anthropic: `anthropic/claude-3-sonnet`

2. **API Key Errors**: Make sure API keys are properly set in the `.env` file.

3. **Response Format Issues**: The framework may change response formats over time. The tests are designed to handle different response structures.

## Future Improvements

1. **Mocking**: Implement mocks for model responses during testing.
2. **Test Coverage**: Add tests for tool binding and special model capabilities.
3. **Benchmarking**: Add performance metrics to compare different models.
