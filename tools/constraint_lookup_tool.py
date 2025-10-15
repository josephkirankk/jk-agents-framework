#!/usr/bin/env python3
"""
MCP Tool: Constraint Lookup Service

Provides programmatic access to business constraints for test data generation.
Prevents LLM hallucination by offering ground-truth constraint values.
"""

import json
import sys
from typing import Dict, List, Any


class Constraints:
    """Centralized constraint definitions"""
    
    REGIONS = {
        "US": "United States",
        "IN": "India",
        "UK": "United Kingdom",
        "DE": "Germany"
    }
    
    PROGRAMS = {
        "MFG": "Merlli",
        "ADV": "Advanced Program",
        "STD": "Standard Program"
    }
    
    PLANTS = {
        "p1": "Plant1",
        "p2": "Plant2",
        "p3": "Plant3",
        "p4": "Plant4"
    }
    
    SECTORS = ["PFNA", "PBNA", "QSNA", "RSNA"]
    
    UOM_OPTIONS = ["count", "kg", "liters", "units", "percentage", "hours"]
    
    METRIC_NAMES = [
        "production_volume", "efficiency_rate", "downtime_hours",
        "quality_score", "defect_rate", "throughput", "utilization"
    ]


def get_all_constraints() -> Dict[str, Any]:
    """Get all constraints in one call"""
    return {
        "regions": Constraints.REGIONS,
        "programs": Constraints.PROGRAMS,
        "plants": Constraints.PLANTS,
        "sectors": Constraints.SECTORS,
        "uom_options": Constraints.UOM_OPTIONS,
        "metric_names": Constraints.METRIC_NAMES
    }


def get_regions() -> Dict[str, str]:
    """Get available regions/markets"""
    return Constraints.REGIONS


def get_programs() -> Dict[str, str]:
    """Get available programs"""
    return Constraints.PROGRAMS


def get_plants() -> Dict[str, str]:
    """Get available plants"""
    return Constraints.PLANTS


def get_sectors() -> List[str]:
    """Get available sectors"""
    return Constraints.SECTORS


def get_uom_options() -> List[str]:
    """Get available units of measure"""
    return Constraints.UOM_OPTIONS


def get_metric_names() -> List[str]:
    """Get available metric names"""
    return Constraints.METRIC_NAMES


def validate_constraint_value(constraint_type: str, value: str) -> Dict[str, Any]:
    """
    Validate if a value exists in a specific constraint type
    
    Args:
        constraint_type: One of 'region', 'program', 'plant', 'sector', 'uom', 'metric'
        value: The value to validate
    
    Returns:
        Dict with 'valid' boolean and optional 'message'
    """
    value_upper = value.upper()
    
    if constraint_type == "region":
        valid = value_upper in Constraints.REGIONS
        return {
            "valid": valid,
            "message": f"Valid regions: {list(Constraints.REGIONS.keys())}" if not valid else "Valid"
        }
    
    elif constraint_type == "program":
        valid = value_upper in Constraints.PROGRAMS
        return {
            "valid": valid,
            "message": f"Valid programs: {list(Constraints.PROGRAMS.keys())}" if not valid else "Valid"
        }
    
    elif constraint_type == "plant":
        valid = value.lower() in Constraints.PLANTS
        return {
            "valid": valid,
            "message": f"Valid plants: {list(Constraints.PLANTS.keys())}" if not valid else "Valid"
        }
    
    elif constraint_type == "sector":
        valid = value_upper in Constraints.SECTORS
        return {
            "valid": valid,
            "message": f"Valid sectors: {Constraints.SECTORS}" if not valid else "Valid"
        }
    
    elif constraint_type == "uom":
        valid = value.lower() in Constraints.UOM_OPTIONS
        return {
            "valid": valid,
            "message": f"Valid UOMs: {Constraints.UOM_OPTIONS}" if not valid else "Valid"
        }
    
    elif constraint_type == "metric":
        valid = value.lower() in Constraints.METRIC_NAMES
        return {
            "valid": valid,
            "message": f"Valid metrics: {Constraints.METRIC_NAMES}" if not valid else "Valid"
        }
    
    else:
        return {
            "valid": False,
            "message": f"Unknown constraint type: {constraint_type}"
        }


# MCP Server Implementation
def handle_mcp_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP protocol requests"""
    
    method = request.get("method")
    params = request.get("params", {})
    
    if method == "tools/list":
        return {
            "tools": [
                {
                    "name": "get_all_constraints",
                    "description": "Get all business constraints in one call",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "get_regions",
                    "description": "Get available regions/markets (US, IN, UK, DE)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "get_programs",
                    "description": "Get available programs (MFG, ADV, STD)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "get_plants",
                    "description": "Get available plants (p1, p2, p3, p4)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "get_sectors",
                    "description": "Get available sectors (PFNA, PBNA, QSNA, RSNA)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "get_uom_options",
                    "description": "Get available units of measure",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "get_metric_names",
                    "description": "Get available metric names",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "validate_constraint_value",
                    "description": "Validate if a value exists in a specific constraint type",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "constraint_type": {
                                "type": "string",
                                "description": "Type: region, program, plant, sector, uom, metric",
                                "enum": ["region", "program", "plant", "sector", "uom", "metric"]
                            },
                            "value": {
                                "type": "string",
                                "description": "Value to validate"
                            }
                        },
                        "required": ["constraint_type", "value"]
                    }
                }
            ]
        }
    
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "get_all_constraints":
            result = get_all_constraints()
        elif tool_name == "get_regions":
            result = get_regions()
        elif tool_name == "get_programs":
            result = get_programs()
        elif tool_name == "get_plants":
            result = get_plants()
        elif tool_name == "get_sectors":
            result = get_sectors()
        elif tool_name == "get_uom_options":
            result = get_uom_options()
        elif tool_name == "get_metric_names":
            result = get_metric_names()
        elif tool_name == "validate_constraint_value":
            result = validate_constraint_value(
                arguments.get("constraint_type"),
                arguments.get("value")
            )
        else:
            return {"error": f"Unknown tool: {tool_name}"}
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }
            ]
        }
    
    return {"error": "Unknown method"}


if __name__ == "__main__":
    # MCP stdio server loop
    for line in sys.stdin:
        try:
            request = json.loads(line)
            response = handle_mcp_request(request)
            print(json.dumps(response), flush=True)
        except Exception as e:
            error_response = {"error": str(e)}
            print(json.dumps(error_response), flush=True)
