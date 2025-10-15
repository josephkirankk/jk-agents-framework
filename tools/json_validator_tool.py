#!/usr/bin/env python3
"""
MCP Tool: JSON Schema Validator

Validates parsed parameters against the required schema for test data generation.
Ensures type correctness, range validity, and completeness.
"""

import json
import sys
from typing import Dict, List, Any, Optional


def validate_test_data_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate test data generation parameters against schema
    
    Expected schema:
    {
        "record_count": int (>0),
        "metrics": [str] (non-empty),
        "program_code": str (required),
        "sector": str (required),
        "plant_code": str (required),
        "market_code": str (optional),
        "value_range": {"min": int, "max": int} (min < max),
        "negative_percentage": float (0-1),
        "negative_range": {"min": int, "max": int} (both negative),
        "uom": str (required),
        "date_range_days": int (optional, >0)
    }
    """
    errors = []
    warnings = []
    
    # Validate record_count
    if "record_count" not in params:
        errors.append("Missing required field: record_count")
    elif not isinstance(params["record_count"], int):
        errors.append(f"record_count must be integer, got {type(params['record_count']).__name__}")
    elif params["record_count"] <= 0:
        errors.append(f"record_count must be > 0, got {params['record_count']}")
    
    # Validate metrics
    if "metrics" not in params:
        errors.append("Missing required field: metrics")
    elif not isinstance(params["metrics"], list):
        errors.append(f"metrics must be list, got {type(params['metrics']).__name__}")
    elif len(params["metrics"]) == 0:
        errors.append("metrics list cannot be empty")
    else:
        for idx, metric in enumerate(params["metrics"]):
            if not isinstance(metric, str):
                errors.append(f"metrics[{idx}] must be string, got {type(metric).__name__}")
    
    # Validate program_code
    if "program_code" not in params:
        errors.append("Missing required field: program_code")
    elif not isinstance(params["program_code"], str):
        errors.append(f"program_code must be string, got {type(params['program_code']).__name__}")
    elif params["program_code"] not in ["MFG", "ADV", "STD"]:
        warnings.append(f"program_code '{params['program_code']}' not in standard values [MFG, ADV, STD]")
    
    # Validate sector
    if "sector" not in params:
        errors.append("Missing required field: sector")
    elif not isinstance(params["sector"], str):
        errors.append(f"sector must be string, got {type(params['sector']).__name__}")
    elif params["sector"] not in ["PFNA", "PBNA", "QSNA", "RSNA", "ALL"]:
        warnings.append(f"sector '{params['sector']}' not in standard values [PFNA, PBNA, QSNA, RSNA, ALL]")
    
    # Validate plant_code
    if "plant_code" not in params:
        errors.append("Missing required field: plant_code")
    elif not isinstance(params["plant_code"], str):
        errors.append(f"plant_code must be string, got {type(params['plant_code']).__name__}")
    elif params["plant_code"] not in ["p1", "p2", "p3", "p4"]:
        warnings.append(f"plant_code '{params['plant_code']}' not in standard values [p1, p2, p3, p4]")
    
    # Validate market_code (optional)
    if "market_code" in params and params["market_code"] is not None:
        if not isinstance(params["market_code"], str):
            errors.append(f"market_code must be string, got {type(params['market_code']).__name__}")
        elif params["market_code"] not in ["US", "IN", "UK", "DE"]:
            warnings.append(f"market_code '{params['market_code']}' not in standard values [US, IN, UK, DE]")
    
    # Validate value_range
    if "value_range" not in params:
        errors.append("Missing required field: value_range")
    elif not isinstance(params["value_range"], dict):
        errors.append(f"value_range must be dict, got {type(params['value_range']).__name__}")
    else:
        vr = params["value_range"]
        if "min" not in vr:
            errors.append("value_range.min is required")
        elif not isinstance(vr["min"], (int, float)):
            errors.append(f"value_range.min must be number, got {type(vr['min']).__name__}")
        
        if "max" not in vr:
            errors.append("value_range.max is required")
        elif not isinstance(vr["max"], (int, float)):
            errors.append(f"value_range.max must be number, got {type(vr['max']).__name__}")
        
        if "min" in vr and "max" in vr and isinstance(vr["min"], (int, float)) and isinstance(vr["max"], (int, float)):
            if vr["min"] >= vr["max"]:
                errors.append(f"value_range.min ({vr['min']}) must be < value_range.max ({vr['max']})")
    
    # Validate negative_percentage
    if "negative_percentage" not in params:
        warnings.append("Missing negative_percentage, assuming 0.0")
    elif not isinstance(params["negative_percentage"], (int, float)):
        errors.append(f"negative_percentage must be number, got {type(params['negative_percentage']).__name__}")
    elif params["negative_percentage"] < 0 or params["negative_percentage"] > 1:
        errors.append(f"negative_percentage must be 0-1, got {params['negative_percentage']}")
    
    # Validate negative_range
    if "negative_range" in params and params["negative_range"] is not None:
        if not isinstance(params["negative_range"], dict):
            errors.append(f"negative_range must be dict, got {type(params['negative_range']).__name__}")
        else:
            nr = params["negative_range"]
            if "min" not in nr:
                errors.append("negative_range.min is required")
            elif not isinstance(nr["min"], (int, float)):
                errors.append(f"negative_range.min must be number, got {type(nr['min']).__name__}")
            elif nr["min"] >= 0:
                errors.append(f"negative_range.min must be negative, got {nr['min']}")
            
            if "max" not in nr:
                errors.append("negative_range.max is required")
            elif not isinstance(nr["max"], (int, float)):
                errors.append(f"negative_range.max must be number, got {type(nr['max']).__name__}")
            elif nr["max"] >= 0:
                errors.append(f"negative_range.max must be negative, got {nr['max']}")
            
            if "min" in nr and "max" in nr and isinstance(nr["min"], (int, float)) and isinstance(nr["max"], (int, float)):
                if nr["min"] >= nr["max"]:
                    errors.append(f"negative_range.min ({nr['min']}) must be < negative_range.max ({nr['max']})")
    
    # Validate uom
    if "uom" not in params:
        errors.append("Missing required field: uom")
    elif not isinstance(params["uom"], str):
        errors.append(f"uom must be string, got {type(params['uom']).__name__}")
    elif params["uom"] not in ["count", "kg", "liters", "units", "percentage", "hours"]:
        warnings.append(f"uom '{params['uom']}' not in standard values [count, kg, liters, units, percentage, hours]")
    
    # Validate date_range_days (optional)
    if "date_range_days" in params and params["date_range_days"] is not None:
        if not isinstance(params["date_range_days"], int):
            errors.append(f"date_range_days must be integer, got {type(params['date_range_days']).__name__}")
        elif params["date_range_days"] <= 0:
            errors.append(f"date_range_days must be > 0, got {params['date_range_days']}")
    
    # Build result
    is_valid = len(errors) == 0
    
    result = {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings
    }
    
    if is_valid:
        result["message"] = "Parameters are valid"
        if warnings:
            result["message"] += f" with {len(warnings)} warning(s)"
    else:
        result["message"] = f"Validation failed with {len(errors)} error(s)"
    
    return result


def fix_common_issues(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Automatically fix common issues in parameters
    
    Returns:
        Dict with fixed parameters and list of fixes applied
    """
    fixed = params.copy()
    fixes_applied = []
    
    # Fix negative_percentage type
    if "negative_percentage" in fixed and isinstance(fixed["negative_percentage"], str):
        try:
            # Handle percentage strings like "10%" or "0.1"
            val = fixed["negative_percentage"].strip().rstrip('%')
            fixed["negative_percentage"] = float(val) / 100 if float(val) > 1 else float(val)
            fixes_applied.append("Converted negative_percentage from string to float")
        except ValueError:
            pass
    
    # Add defaults for missing optional fields
    if "negative_percentage" not in fixed:
        fixed["negative_percentage"] = 0.0
        fixes_applied.append("Added default negative_percentage: 0.0")
    
    if "negative_range" not in fixed or fixed["negative_range"] is None:
        fixed["negative_range"] = {"min": -100, "max": -10}
        fixes_applied.append("Added default negative_range: {min: -100, max: -10}")
    
    if "date_range_days" not in fixed:
        fixed["date_range_days"] = 30
        fixes_applied.append("Added default date_range_days: 30")
    
    if "market_code" not in fixed:
        fixed["market_code"] = "US"
        fixes_applied.append("Added default market_code: US")
    
    # Fix empty metrics
    if "metrics" in fixed and len(fixed["metrics"]) == 0:
        fixed["metrics"] = ["default_metric"]
        fixes_applied.append("Added default metric name: default_metric")
    
    # Ensure value ranges are integers
    if "value_range" in fixed:
        if isinstance(fixed["value_range"]["min"], float):
            fixed["value_range"]["min"] = int(fixed["value_range"]["min"])
            fixes_applied.append("Converted value_range.min to integer")
        if isinstance(fixed["value_range"]["max"], float):
            fixed["value_range"]["max"] = int(fixed["value_range"]["max"])
            fixes_applied.append("Converted value_range.max to integer")
    
    if "negative_range" in fixed and fixed["negative_range"] is not None:
        if isinstance(fixed["negative_range"]["min"], float):
            fixed["negative_range"]["min"] = int(fixed["negative_range"]["min"])
            fixes_applied.append("Converted negative_range.min to integer")
        if isinstance(fixed["negative_range"]["max"], float):
            fixed["negative_range"]["max"] = int(fixed["negative_range"]["max"])
            fixes_applied.append("Converted negative_range.max to integer")
    
    return {
        "fixed_params": fixed,
        "fixes_applied": fixes_applied,
        "num_fixes": len(fixes_applied)
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
                    "name": "validate_test_data_params",
                    "description": "Validate parsed parameters against test data generation schema",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "params": {
                                "type": "object",
                                "description": "Parameters object to validate"
                            }
                        },
                        "required": ["params"]
                    }
                },
                {
                    "name": "fix_common_issues",
                    "description": "Automatically fix common issues in parameters (type conversions, defaults)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "params": {
                                "type": "object",
                                "description": "Parameters object to fix"
                            }
                        },
                        "required": ["params"]
                    }
                }
            ]
        }
    
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "validate_test_data_params":
            result = validate_test_data_params(arguments.get("params", {}))
        elif tool_name == "fix_common_issues":
            result = fix_common_issues(arguments.get("params", {}))
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
