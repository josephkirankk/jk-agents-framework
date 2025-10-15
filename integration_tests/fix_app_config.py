#!/usr/bin/env python3
"""
Script to automatically add app_config parameter to build_agent calls in test files.
"""

import re
from pathlib import Path

# Files to fix (already fixed: test_01_basic_flow.py, test_02_tool_calling_mcp.py, test_01_agent_types.py)
FILES_TO_FIX = [
    "test_03_chromadb_memory.py",
    "test_05_litellm_providers.py",
    "test_07_json_schema_data_generator.py",
    "test_05_error_handling_recovery.py",
    "test_06_mcp_python_tools.py",
    "test_00_super_integrated.py",
    "test_06_large_data_mcp_demo_multi_turn.py",
]

def fix_imports(content):
    """Add convert_app_config_to_dict to imports if not present."""
    # Check if already imported
    if 'convert_app_config_to_dict' in content:
        return content
    
    # Pattern to find test_utils import
    import_pattern = r'(from test_utils import \([^)]+)\)'
    
    def add_import(match):
        imports = match.group(1)
        if 'convert_app_config_to_dict' not in imports:
            return imports + ',\n    convert_app_config_to_dict)'
        return match.group(0)
    
    content = re.sub(import_pattern, add_import, content, count=1)
    
    # If no parentheses import found, try single line
    if 'convert_app_config_to_dict' not in content:
        single_import_pattern = r'from test_utils import ([^\n]+)'
        def add_single_import(match):
            imports = match.group(1)
            if 'convert_app_config_to_dict' not in imports:
                return f'from test_utils import {imports.strip()}, convert_app_config_to_dict'
            return match.group(0)
        content = re.sub(single_import_pattern, add_single_import, content, count=1)
    
    return content

def fix_build_agent_calls(content):
    """Add app_config parameter to build_agent calls."""
    lines = content.split('\n')
    result_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        result_lines.append(line)
        
        # Check if this line contains build_agent call
        if 'await build_agent(' in line or 'await build_react_agent(' in line:
            # Check if app_config_dict conversion is already above
            has_conversion = False
            for j in range(max(0, i-5), i):
                if 'convert_app_config_to_dict' in lines[j]:
                    has_conversion = True
                    break
            
            # If no conversion found, add it before the build_agent call
            if not has_conversion:
                # Find the line with default_model
                for j in range(max(0, i-10), i):
                    if 'default_model' in lines[j] and '=' in lines[j]:
                        # Insert conversion after default_model line
                        indent = len(lines[j]) - len(lines[j].lstrip())
                        conversion_line = ' ' * indent + 'app_config_dict = convert_app_config_to_dict(app_config)'
                        result_lines.insert(-1, conversion_line)
                        break
            
            # Now check if build_agent call has app_config parameter
            # Scan through the function call to find closing paren
            call_lines = [line]
            j = i + 1
            paren_count = line.count('(') - line.count(')')
            while j < len(lines) and paren_count > 0:
                call_lines.append(lines[j])
                paren_count += lines[j].count('(') - lines[j].count(')')
                result_lines.append(lines[j])
                j += 1
            
            # Check if app_config is in the call
            call_text = '\n'.join(call_lines)
            if 'app_config=' not in call_text:
                # Find the closing paren and add app_config before it
                last_line_idx = len(result_lines) - 1
                last_line = result_lines[last_line_idx]
                if last_line.strip() == ')':
                    # Get indent
                    indent = len(last_line) - len(last_line.lstrip())
                    # Add app_config line before closing paren
                    app_config_line = ' ' * (indent + 4) + 'app_config=app_config_dict'
                    result_lines.insert(last_line_idx, app_config_line + ',')
            
            i = j
            continue
        
        i += 1
    
    return '\n'.join(result_lines)

def process_file(filepath):
    """Process a single test file."""
    print(f"Processing {filepath.name}...")
    
    try:
        content = filepath.read_text()
        
        # Skip if already has the fix
        if 'app_config=app_config_dict' in content and 'convert_app_config_to_dict' in content:
            print(f"  ✓ Already fixed, skipping")
            return True
        
        # Apply fixes
        content = fix_imports(content)
        content = fix_build_agent_calls(content)
        
        # Write back
        filepath.write_text(content)
        print(f"  ✓ Fixed")
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    integration_tests_dir = Path(__file__).parent
    
    print("Fixing integration test files to include app_config parameter...\n")
    
    fixed = 0
    failed = 0
    
    for filename in FILES_TO_FIX:
        filepath = integration_tests_dir / filename
        if filepath.exists():
            if process_file(filepath):
                fixed += 1
            else:
                failed += 1
        else:
            print(f"File not found: {filename}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Results: {fixed} fixed, {failed} failed")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
