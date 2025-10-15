"""
Smart Python Code Analyzer - Token-Optimized, Dynamic Variable Detection

This module intelligently analyzes and fixes Python code without hardcoding variable names.
Uses AST parsing to understand code structure and detect anti-patterns.

Key Features:
1. Dynamic variable detection (no hardcoded names)
2. Intelligent dataset variable identification
3. Pattern-based anti-pattern detection
4. Token-optimized (minimal overhead)
"""

import ast
import re
from typing import Optional, Tuple, List, Set
import logging

logger = logging.getLogger("smart_code_analyzer")


class DatasetVariableFinder(ast.NodeVisitor):
    """
    AST visitor that identifies potential dataset variables.
    
    Heuristics:
    1. Variables assigned with list comprehensions
    2. Variables assigned with empty list then appended to in loops
    3. Variables assigned from function calls that return collections
    4. Variables with names suggesting collections (plural nouns)
    """
    
    def __init__(self):
        self.potential_datasets: Set[str] = set()
        self.list_assignments: Set[str] = set()
        self.loop_appends: Set[str] = set()
        
    def visit_Assign(self, node):
        """Track assignments to lists or list comprehensions"""
        # List comprehension: var = [... for ... in ...]
        if isinstance(node.value, ast.ListComp):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.potential_datasets.add(target.id)
                    self.list_assignments.add(target.id)
        
        # Empty list: var = []
        elif isinstance(node.value, ast.List) and len(node.value.elts) == 0:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.potential_datasets.add(target.id)
                    self.list_assignments.add(target.id)
        
        # Function call that might return a list
        elif isinstance(node.value, ast.Call):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.potential_datasets.add(target.id)
        
        self.generic_visit(node)
    
    def visit_For(self, node):
        """Track append operations inside loops"""
        # Look for var.append(...) inside loops
        for child in ast.walk(node):
            if isinstance(child, ast.Expr) and isinstance(child.value, ast.Call):
                if isinstance(child.value.func, ast.Attribute):
                    if child.value.func.attr == 'append':
                        if isinstance(child.value.func.value, ast.Name):
                            var_name = child.value.func.value.id
                            self.potential_datasets.add(var_name)
                            self.loop_appends.add(var_name)
        
        self.generic_visit(node)
    
    def get_best_dataset_variable(self) -> Optional[str]:
        """
        Return the most likely dataset variable.
        
        Priority:
        1. Variables with loop appends (highest confidence)
        2. Variables from list comprehensions
        3. Other list assignments
        """
        if self.loop_appends:
            # Prefer variables that are appended to in loops
            return sorted(self.loop_appends)[0]
        elif self.list_assignments:
            return sorted(self.list_assignments)[0]
        elif self.potential_datasets:
            return sorted(self.potential_datasets)[0]
        
        return None


def analyze_last_statement(code: str) -> Tuple[Optional[str], Optional[str], bool]:
    """
    Analyze the last statement of Python code.
    
    Returns:
        (statement_type, variable_name, is_problematic)
        
    Statement types:
    - 'slice': var[:n], var[n:m]
    - 'subscript': var[n]
    - 'json_dumps': json.dumps(var)
    - 'str_call': str(var)
    - 'print': print(var)
    - 'variable': var
    - 'expression': other expression
    - None: invalid/empty
    """
    lines = code.strip().split('\n')
    if not lines:
        return None, None, False
    
    last_line = lines[-1].strip()
    
    # Remove comments
    if '#' in last_line:
        last_line = last_line[:last_line.index('#')].strip()
    
    if not last_line:
        return None, None, False
    
    try:
        # Parse just the last line as an expression
        last_expr = ast.parse(last_line, mode='eval').body
        
        # Slice: var[:5], var[0:10]
        if isinstance(last_expr, ast.Subscript):
            if isinstance(last_expr.value, ast.Name):
                var_name = last_expr.value.id
                # Check if it's a slice (not just index)
                if isinstance(last_expr.slice, ast.Slice):
                    return 'slice', var_name, True
                else:
                    return 'subscript', var_name, True
        
        # Function calls: json.dumps(...), str(...), print(...)
        elif isinstance(last_expr, ast.Call):
            # json.dumps(var)
            if isinstance(last_expr.func, ast.Attribute):
                if last_expr.func.attr == 'dumps':
                    if last_expr.args and isinstance(last_expr.args[0], ast.Name):
                        var_name = last_expr.args[0].id
                        return 'json_dumps', var_name, True
            
            # str(var), print(var)
            elif isinstance(last_expr.func, ast.Name):
                func_name = last_expr.func.id
                if func_name in ('str', 'print', 'repr'):
                    if last_expr.args and isinstance(last_expr.args[0], ast.Name):
                        var_name = last_expr.args[0].id
                        return func_name, var_name, True
        
        # Bare variable: var
        elif isinstance(last_expr, ast.Name):
            return 'variable', last_expr.id, False  # Bare variable is OK
    
    except:
        # If parsing fails, it might be a statement, not expression
        pass
    
    return 'expression', None, False


def find_dataset_variable(code: str) -> Optional[str]:
    """
    Dynamically find the main dataset variable in the code.
    
    Uses AST analysis to identify the most likely dataset variable
    without hardcoding variable names.
    """
    try:
        tree = ast.parse(code)
        finder = DatasetVariableFinder()
        finder.visit(tree)
        return finder.get_best_dataset_variable()
    except:
        return None


def smart_auto_correct(python_code: str) -> Tuple[str, bool, Optional[str]]:
    """
    Intelligently auto-correct Python code for dataset generation.
    
    Uses AST-based analysis to:
    1. Dynamically identify dataset variables
    2. Detect anti-patterns (slices, conversions)
    3. Fix issues without hardcoding variable names
    
    Args:
        python_code: The Python code to analyze and fix
        
    Returns:
        (corrected_code, was_fixed, fix_description)
        
    Token Optimization:
    - Minimal overhead (AST parsing is fast)
    - No hardcoded lists to maintain
    - Only logs essential information
    """
    lines = python_code.strip().split('\n')
    if not lines:
        return python_code, False, None
    
    last_line = lines[-1].strip()
    
    # Analyze last statement
    stmt_type, var_name, is_problematic = analyze_last_statement(python_code)
    
    if not is_problematic:
        return python_code, False, None
    
    # Find the best dataset variable if we detected a problem
    if var_name:
        dataset_var = var_name
    else:
        # If we couldn't extract var from last line, find it from full code
        dataset_var = find_dataset_variable(python_code)
        if not dataset_var:
            return python_code, False, None
    
    # Fix the issue
    fix_descriptions = {
        'slice': f"Detected slice operation: {last_line} → Returning full dataset",
        'subscript': f"Detected subscript operation: {last_line} → Returning full dataset",
        'json_dumps': f"Detected json.dumps: {last_line} → Returning Python object",
        'str': f"Detected str() conversion: {last_line} → Returning original object",
        'print': f"Detected print statement: {last_line} → Returning object instead",
    }
    
    fix_description = fix_descriptions.get(stmt_type, f"Detected anti-pattern: {last_line}")
    
    # Replace last line with assignment to 'result'
    lines[-1] = f"result = {dataset_var}"
    corrected_code = '\n'.join(lines)
    
    return corrected_code, True, fix_description


def get_analysis_stats(python_code: str) -> dict:
    """
    Get code analysis statistics (for debugging/logging).
    
    Token-optimized: Only returns essential stats, not full code.
    """
    dataset_var = find_dataset_variable(python_code)
    stmt_type, var_name, is_problematic = analyze_last_statement(python_code)
    
    lines = python_code.strip().split('\n')
    last_line = lines[-1].strip() if lines else ""
    
    return {
        "detected_dataset_var": dataset_var,
        "last_statement_type": stmt_type,
        "last_statement_var": var_name,
        "is_problematic": is_problematic,
        "last_line_preview": last_line[:100],  # Limited for token optimization
        "total_lines": len(lines)
    }


# Example usage for testing
if __name__ == "__main__":
    # Test cases
    test_codes = [
        # Case 1: List comprehension with slice
        """
students = [{'name': f'Student {i}'} for i in range(100)]
students[:5]
""",
        # Case 2: Loop with append and slice
        """
records = []
for i in range(1000):
    records.append({'id': i, 'value': i*2})
records[:10]
""",
        # Case 3: json.dumps
        """
data = [{'x': i} for i in range(50)]
json.dumps(data)
""",
        # Case 4: Bare variable (OK)
        """
results = generate_data()
results
""",
    ]
    
    for i, code in enumerate(test_codes, 1):
        print(f"\n{'='*60}")
        print(f"Test Case {i}:")
        print(f"{'='*60}")
        corrected, was_fixed, description = smart_auto_correct(code)
        stats = get_analysis_stats(code)
        
        print(f"Dataset Variable: {stats['detected_dataset_var']}")
        print(f"Last Statement: {stats['last_statement_type']}")
        print(f"Problematic: {stats['is_problematic']}")
        print(f"Was Fixed: {was_fixed}")
        if was_fixed:
            print(f"Fix: {description}")
            print(f"New Last Line: {corrected.strip().split(chr(10))[-1]}")
