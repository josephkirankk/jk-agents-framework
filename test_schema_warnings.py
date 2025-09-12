#!/usr/bin/env python3
"""
Test script to reproduce Google Gemini schema warnings by creating
tools with problematic schema properties.
"""

import os
import logging
from dotenv import load_dotenv
from langchain_core.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field
from typing import Dict, Any, List

# Load environment variables
load_dotenv()

# Set up logging to capture warnings
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class ProblematicSchema(BaseModel):
    """A schema that includes properties not supported by Gemini"""
    text: str = Field(description="Input text")
    options: List[str] = Field(description="List of options", default=[])

    model_config = {
        "extra": "allow",
        "json_schema_extra": {
            "additionalProperties": True,
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "problematic-schema",
            "definitions": {
                "custom_type": {
                    "type": "string"
                }
            }
        }
    }


class ProblematicTool(BaseTool):
    """A tool with a problematic schema that should trigger warnings"""

    name: str = "problematic_tool"
    description: str = "A tool with schema properties not supported by Gemini"
    args_schema: type = ProblematicSchema
    
    def _run(self, text: str, options: List[str] = None) -> Dict[str, Any]:
        """Run the tool"""
        return {
            "result": f"Processed: {text}",
            "options_count": len(options or [])
        }


def test_problematic_schema():
    """Test with a tool that has problematic schema properties"""
    
    # Check if API key is set
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not set")
        return
    
    print("Testing Google Gemini with problematic schema...")
    
    # Create a tool with problematic schema
    problematic_tool = ProblematicTool()
    
    # Print the schema to see what it contains
    schema = problematic_tool.args_schema.model_json_schema()
    print("Problematic tool schema:")
    import json
    print(json.dumps(schema, indent=2))
    
    # Test schema filtering
    from app.gemini_schema_filter import apply_gemini_schema_filtering
    
    tools = [problematic_tool]
    print(f"\nOriginal tools: {[tool.name for tool in tools]}")
    
    # Apply schema filtering
    filtered_tools = apply_gemini_schema_filtering(tools, "google:gemini-2.0-flash-lite-001")
    print(f"Filtered tools: {[tool.name for tool in filtered_tools]}")
    
    # Check if the tool was wrapped
    if tools[0] != filtered_tools[0]:
        print("Tool was wrapped for Gemini compatibility")
        
        # Check the cleaned schema
        if hasattr(filtered_tools[0], '_cleaned_schema'):
            print("Cleaned schema:")
            print(json.dumps(filtered_tools[0]._cleaned_schema, indent=2))
    else:
        print("Tool was not modified")
    
    # Create Gemini model
    model = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-lite-001",
        google_api_key=api_key,
        temperature=0.0,
    )
    
    print(f"\nCreated model: {model}")
    
    # Create agent with filtered tools
    try:
        agent = create_react_agent(
            model=model,
            tools=filtered_tools,
            prompt="You are a helpful assistant with access to tools."
        )
        print("Agent created successfully")
        
        # Test with a simple query
        response = agent.invoke({
            "messages": [("human", "Use the problematic_tool to process the text 'hello world' with options ['a', 'b']")]
        })
        
        print("Response:", response)
        
    except Exception as e:
        print(f"Error creating or using agent: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_problematic_schema()
