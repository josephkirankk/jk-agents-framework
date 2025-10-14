#!/usr/bin/env python3
"""
Simple test script to verify the LLM judge functionality.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Load environment
from dotenv import load_dotenv
load_dotenv()
print("✅ Loaded environment")

# Imports for LLM
from langchain_core.messages import HumanMessage
from app.enhanced_litellm_wrapper import EnhancedLiteLLMChat

# Function to create a model
def get_model(model_id="azure/gpt-4.1"):
    return EnhancedLiteLLMChat(
        model=model_id,
        temperature=0.2,
        timeout=60
    )

# Test response text
test_response = """
def fibonacci(n):
    # Generate a list of the first n Fibonacci numbers
    fib_list = []
    a, b = 0, 1
    for _ in range(n):
        fib_list.append(a)
        a, b = b, a + b
    return fib_list

# Example usage
result = fibonacci(10)
print(result)  # Output: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
"""

# Prompt for the LLM judge
judge_prompt = f"""Review the following response to the request: 'Create a function that generates Fibonacci sequence numbers'.

Response to evaluate:
```
{test_response}
```

Rate the response on a scale of 1-10, where:
- 1-3: Does not address the request at all
- 4-6: Partially addresses the request but with significant issues
- 7-8: Satisfactorily addresses the request with minor issues
- 9-10: Perfectly addresses the request

Provide your rating and a brief explanation. Does the response sufficiently address the request?

Rating (1-10): 
"""

async def main():
    print("\n=== Testing LLM Judge ===\n")
    
    # Create model
    model = get_model()
    print(f"Model created: {model.model}")
    
    # Create message
    judge_messages = [HumanMessage(content=judge_prompt)]
    
    try:
        # Call the model
        print("Calling model...")
        judge_response = await model._agenerate(judge_messages)
        judge_text = judge_response.generations[0].message.content
        
        # Print response
        print("\n=== Judge Response ===\n")
        print(judge_text)
        
        # Extract rating if possible
        import re
        # First try to match the full string "10"
        rating_match = re.search(r"Rating\s*(?:\(1-10\))?\s*:?\s*(10)", judge_text, re.IGNORECASE)
        
        # If that doesn't work, try for single digits
        if not rating_match:
            rating_match = re.search(r"Rating\s*(?:\(1-10\))?\s*:?\s*([1-9])", judge_text, re.IGNORECASE)
        
        if rating_match:
            rating = int(rating_match.group(1))
            print(f"\nExtracted rating: {rating}/10")
        else:
            print("\nCould not extract rating")
            
        return 0
            
    except Exception as e:
        import traceback
        print(f"\n❌ ERROR: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    asyncio.run(main())
