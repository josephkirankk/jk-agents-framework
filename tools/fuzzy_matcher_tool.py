#!/usr/bin/env python3
"""
MCP Tool: Fuzzy Matcher Service

Provides fuzzy string matching to handle variations in user input.
Maps user-provided values to canonical constraint values.
"""

import json
import sys
from typing import Dict, List, Any, Optional
from difflib import SequenceMatcher


class FuzzyMatcher:
    """Fuzzy matching for constraint values"""
    
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
    
    @staticmethod
    def similarity_score(str1: str, str2: str) -> float:
        """Calculate similarity score between two strings (0-1)"""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    @staticmethod
    def find_best_match(input_value: str, candidates: List[str], 
                       threshold: float = 0.6) -> Optional[Dict[str, Any]]:
        """
        Find best matching candidate for input value
        
        Args:
            input_value: User-provided value
            candidates: List of valid values
            threshold: Minimum similarity score (0-1)
        
        Returns:
            Dict with best match and score, or None if no good match
        """
        best_match = None
        best_score = 0.0
        
        for candidate in candidates:
            score = FuzzyMatcher.similarity_score(input_value, candidate)
            if score > best_score:
                best_score = score
                best_match = candidate
        
        if best_score >= threshold:
            return {
                "match": best_match,
                "score": best_score,
                "confidence": "high" if best_score >= 0.8 else "medium"
            }
        
        return None


def match_region(input_value: str) -> Dict[str, Any]:
    """
    Match user input to a valid region code
    
    Examples:
        'United States' -> 'US'
        'usa' -> 'US'
        'india' -> 'IN'
    """
    input_clean = input_value.strip().upper()
    
    # Exact match on code
    if input_clean in FuzzyMatcher.REGIONS:
        return {
            "matched": True,
            "code": input_clean,
            "name": FuzzyMatcher.REGIONS[input_clean],
            "confidence": "exact"
        }
    
    # Exact match on name
    for code, name in FuzzyMatcher.REGIONS.items():
        if input_clean == name.upper():
            return {
                "matched": True,
                "code": code,
                "name": name,
                "confidence": "exact"
            }
    
    # Fuzzy match on codes
    codes = list(FuzzyMatcher.REGIONS.keys())
    match = FuzzyMatcher.find_best_match(input_value, codes)
    if match:
        code = match["match"]
        return {
            "matched": True,
            "code": code,
            "name": FuzzyMatcher.REGIONS[code],
            "confidence": match["confidence"],
            "score": match["score"]
        }
    
    # Fuzzy match on names
    names = list(FuzzyMatcher.REGIONS.values())
    match = FuzzyMatcher.find_best_match(input_value, names)
    if match:
        # Find code for this name
        for code, name in FuzzyMatcher.REGIONS.items():
            if name == match["match"]:
                return {
                    "matched": True,
                    "code": code,
                    "name": name,
                    "confidence": match["confidence"],
                    "score": match["score"]
                }
    
    return {
        "matched": False,
        "message": f"No match found for '{input_value}'. Valid options: {list(FuzzyMatcher.REGIONS.keys())}"
    }


def match_program(input_value: str) -> Dict[str, Any]:
    """
    Match user input to a valid program code
    
    Examples:
        'MFG' -> 'MFG'
        'Merlli' -> 'MFG'
        'manufacturing' -> 'MFG'
        'advanced' -> 'ADV'
    """
    input_clean = input_value.strip().upper()
    
    # Exact match on code
    if input_clean in FuzzyMatcher.PROGRAMS:
        return {
            "matched": True,
            "code": input_clean,
            "name": FuzzyMatcher.PROGRAMS[input_clean],
            "confidence": "exact"
        }
    
    # Exact match on name
    for code, name in FuzzyMatcher.PROGRAMS.items():
        if input_clean == name.upper():
            return {
                "matched": True,
                "code": code,
                "name": name,
                "confidence": "exact"
            }
    
    # Fuzzy match on codes
    codes = list(FuzzyMatcher.PROGRAMS.keys())
    match = FuzzyMatcher.find_best_match(input_value, codes)
    if match:
        code = match["match"]
        return {
            "matched": True,
            "code": code,
            "name": FuzzyMatcher.PROGRAMS[code],
            "confidence": match["confidence"],
            "score": match["score"]
        }
    
    # Fuzzy match on names
    names = list(FuzzyMatcher.PROGRAMS.values())
    match = FuzzyMatcher.find_best_match(input_value, names)
    if match:
        for code, name in FuzzyMatcher.PROGRAMS.items():
            if name == match["match"]:
                return {
                    "matched": True,
                    "code": code,
                    "name": name,
                    "confidence": match["confidence"],
                    "score": match["score"]
                }
    
    return {
        "matched": False,
        "message": f"No match found for '{input_value}'. Valid options: {list(FuzzyMatcher.PROGRAMS.keys())}"
    }


def match_plant(input_value: str) -> Dict[str, Any]:
    """
    Match user input to a valid plant code
    
    Examples:
        'p1' -> 'p1'
        'Plant1' -> 'p1'
        'plant 1' -> 'p1'
    """
    input_clean = input_value.strip().lower()
    
    # Exact match on code
    if input_clean in FuzzyMatcher.PLANTS:
        return {
            "matched": True,
            "code": input_clean,
            "name": FuzzyMatcher.PLANTS[input_clean],
            "confidence": "exact"
        }
    
    # Exact match on name
    for code, name in FuzzyMatcher.PLANTS.items():
        if input_clean == name.lower():
            return {
                "matched": True,
                "code": code,
                "name": name,
                "confidence": "exact"
            }
    
    # Fuzzy match on codes
    codes = list(FuzzyMatcher.PLANTS.keys())
    match = FuzzyMatcher.find_best_match(input_value, codes)
    if match:
        code = match["match"]
        return {
            "matched": True,
            "code": code,
            "name": FuzzyMatcher.PLANTS[code],
            "confidence": match["confidence"],
            "score": match["score"]
        }
    
    # Fuzzy match on names
    names = list(FuzzyMatcher.PLANTS.values())
    match = FuzzyMatcher.find_best_match(input_value, names)
    if match:
        for code, name in FuzzyMatcher.PLANTS.items():
            if name == match["match"]:
                return {
                    "matched": True,
                    "code": code,
                    "name": name,
                    "confidence": match["confidence"],
                    "score": match["score"]
                }
    
    return {
        "matched": False,
        "message": f"No match found for '{input_value}'. Valid options: {list(FuzzyMatcher.PLANTS.keys())}"
    }


def match_sector(input_value: str) -> Dict[str, Any]:
    """Match user input to a valid sector"""
    input_clean = input_value.strip().upper()
    
    # Exact match
    if input_clean in FuzzyMatcher.SECTORS:
        return {
            "matched": True,
            "sector": input_clean,
            "confidence": "exact"
        }
    
    # Fuzzy match
    match = FuzzyMatcher.find_best_match(input_value, FuzzyMatcher.SECTORS)
    if match:
        return {
            "matched": True,
            "sector": match["match"],
            "confidence": match["confidence"],
            "score": match["score"]
        }
    
    return {
        "matched": False,
        "message": f"No match found for '{input_value}'. Valid options: {FuzzyMatcher.SECTORS}"
    }


def match_uom(input_value: str) -> Dict[str, Any]:
    """Match user input to a valid UOM"""
    input_clean = input_value.strip().lower()
    
    # Exact match
    if input_clean in FuzzyMatcher.UOM_OPTIONS:
        return {
            "matched": True,
            "uom": input_clean,
            "confidence": "exact"
        }
    
    # Handle common variations
    uom_aliases = {
        "kgs": "kg",
        "kilograms": "kg",
        "kilogram": "kg",
        "liter": "liters",
        "litre": "liters",
        "litres": "liters",
        "unit": "units",
        "percent": "percentage",
        "%": "percentage",
        "pct": "percentage",
        "hour": "hours",
        "hr": "hours",
        "hrs": "hours",
        "counts": "count"
    }
    
    if input_clean in uom_aliases:
        mapped_uom = uom_aliases[input_clean]
        return {
            "matched": True,
            "uom": mapped_uom,
            "confidence": "high"
        }
    
    # Fuzzy match
    match = FuzzyMatcher.find_best_match(input_value, FuzzyMatcher.UOM_OPTIONS)
    if match:
        return {
            "matched": True,
            "uom": match["match"],
            "confidence": match["confidence"],
            "score": match["score"]
        }
    
    return {
        "matched": False,
        "message": f"No match found for '{input_value}'. Valid options: {FuzzyMatcher.UOM_OPTIONS}"
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
                    "name": "match_region",
                    "description": "Fuzzy match user input to valid region code (US, IN, UK, DE)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "input_value": {
                                "type": "string",
                                "description": "User-provided region name or code"
                            }
                        },
                        "required": ["input_value"]
                    }
                },
                {
                    "name": "match_program",
                    "description": "Fuzzy match user input to valid program code (MFG, ADV, STD)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "input_value": {
                                "type": "string",
                                "description": "User-provided program name or code"
                            }
                        },
                        "required": ["input_value"]
                    }
                },
                {
                    "name": "match_plant",
                    "description": "Fuzzy match user input to valid plant code (p1, p2, p3, p4)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "input_value": {
                                "type": "string",
                                "description": "User-provided plant name or code"
                            }
                        },
                        "required": ["input_value"]
                    }
                },
                {
                    "name": "match_sector",
                    "description": "Fuzzy match user input to valid sector (PFNA, PBNA, QSNA, RSNA)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "input_value": {
                                "type": "string",
                                "description": "User-provided sector name"
                            }
                        },
                        "required": ["input_value"]
                    }
                },
                {
                    "name": "match_uom",
                    "description": "Fuzzy match user input to valid UOM (count, kg, liters, units, percentage, hours)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "input_value": {
                                "type": "string",
                                "description": "User-provided unit of measure"
                            }
                        },
                        "required": ["input_value"]
                    }
                }
            ]
        }
    
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "match_region":
            result = match_region(arguments.get("input_value", ""))
        elif tool_name == "match_program":
            result = match_program(arguments.get("input_value", ""))
        elif tool_name == "match_plant":
            result = match_plant(arguments.get("input_value", ""))
        elif tool_name == "match_sector":
            result = match_sector(arguments.get("input_value", ""))
        elif tool_name == "match_uom":
            result = match_uom(arguments.get("input_value", ""))
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
