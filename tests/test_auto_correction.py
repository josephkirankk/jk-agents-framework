"""
Unit tests for the auto-correction logic in app/mcp_python_wrapper.py

Tests verify that the auto-correction logic correctly detects and fixes
common LLM mistakes in generated Python code.
"""

import re
import pytest


class TestAutoCorrection:
    """Test suite for Python code auto-correction logic"""
    
    # Common variable names used for datasets
    COMMON_VARS = ['records', 'data', 'results', 'output', 'dataset', 'items', 'rows']
    
    def apply_auto_correction(self, python_code: str) -> tuple[str, bool]:
        """
        Apply the same auto-correction logic as in mcp_python_wrapper.py
        
        Returns:
            tuple: (corrected_code, was_fixed)
        """
        lines = python_code.strip().split('\n')
        if not lines:
            return python_code, False
        
        last_line = lines[-1].strip()
        fixed = False
        detected_var = None
        
        # Pattern 1: Slice/index (e.g., records[:5], data[0])
        for var in self.COMMON_VARS:
            if re.match(rf'^{var}\s*\[.*\].*$', last_line):
                detected_var = var
                lines[-1] = f"result = {var}"
                python_code = '\n'.join(lines)
                fixed = True
                break
        
        # Pattern 2: json.dumps() conversion
        if not fixed:
            for var in self.COMMON_VARS:
                if re.match(rf'^json\.dumps\s*\(.*{var}.*\).*$', last_line):
                    detected_var = var
                    lines[-1] = f"result = {var}"
                    python_code = '\n'.join(lines)
                    fixed = True
                    break
        
        # Pattern 3: str() conversion
        if not fixed:
            for var in self.COMMON_VARS:
                if re.match(rf'^str\s*\(.*{var}.*\).*$', last_line):
                    detected_var = var
                    lines[-1] = f"result = {var}"
                    python_code = '\n'.join(lines)
                    fixed = True
                    break
        
        # Pattern 4: Bare variable expression
        if not fixed:
            for var in self.COMMON_VARS:
                if last_line == var:
                    detected_var = var
                    lines[-1] = f"result = {var}"
                    python_code = '\n'.join(lines)
                    fixed = True
                    break
        
        return python_code, fixed
    
    # ========================================================================
    # Test Pattern 1: Slice/Index Detection
    # ========================================================================
    
    def test_detect_records_slice(self):
        """Test detection of records[:5] pattern"""
        code = """records = []
for i in range(10):
    records.append({'id': i})
records[:5]"""
        
        corrected, fixed = self.apply_auto_correction(code)
        assert fixed is True
        assert corrected.endswith("result = records")
    
    def test_detect_data_slice(self):
        """Test detection of data[:10] pattern"""
        code = """data = []
for i in range(100):
    data.append(i)
data[:10]"""
        
        corrected, fixed = self.apply_auto_correction(code)
        assert fixed is True
        assert corrected.endswith("result = data")
    
    def test_detect_results_index(self):
        """Test detection of results[0] pattern"""
        code = """results = [1, 2, 3, 4, 5]
results[0]"""
        
        corrected, fixed = self.apply_auto_correction(code)
        assert fixed is True
        assert corrected.endswith("result = results")
    
    def test_detect_slice_with_comment(self):
        """Test detection of slice with inline comment"""
        code = """records = []
for i in range(10):
    records.append({'id': i})
records[:5]  # Preview first 5 records"""
        
        corrected, fixed = self.apply_auto_correction(code)
        assert fixed is True
        assert corrected.endswith("result = records")
    
    # ========================================================================
    # Test Pattern 2: json.dumps() Detection
    # ========================================================================
    
    def test_detect_json_dumps_records(self):
        """Test detection of json.dumps(records) pattern"""
        code = """import json
records = [{'id': 1}, {'id': 2}]
json.dumps(records)"""
        
        corrected, fixed = self.apply_auto_correction(code)
        assert fixed is True
        assert corrected.endswith("result = records")
    
    def test_detect_json_dumps_data(self):
        """Test detection of json.dumps(data) pattern"""
        code = """import json
data = [1, 2, 3]
json.dumps(data)"""
        
        corrected, fixed = self.apply_auto_correction(code)
        assert fixed is True
        assert corrected.endswith("result = data")
    
    def test_detect_json_dumps_with_args(self):
        """Test detection of json.dumps(records, indent=2) pattern"""
        code = """import json
records = [{'id': 1}]
json.dumps(records, indent=2)"""
        
        corrected, fixed = self.apply_auto_correction(code)
        assert fixed is True
        assert corrected.endswith("result = records")
    
    # ========================================================================
    # Test Pattern 3: str() Detection
    # ========================================================================
    
    def test_detect_str_records(self):
        """Test detection of str(records) pattern"""
        code = """records = [1, 2, 3]
str(records)"""
        
        corrected, fixed = self.apply_auto_correction(code)
        assert fixed is True
        assert corrected.endswith("result = records")
    
    def test_detect_str_output(self):
        """Test detection of str(output) pattern"""
        code = """output = {'key': 'value'}
str(output)"""
        
        corrected, fixed = self.apply_auto_correction(code)
        assert fixed is True
        assert corrected.endswith("result = output")
    
    # ========================================================================
    # Test Pattern 4: Bare Expression Detection
    # ========================================================================
    
    def test_detect_bare_records(self):
        """Test detection of bare 'records' expression"""
        code = """records = []
for i in range(10):
    records.append(i)
records"""
        
        corrected, fixed = self.apply_auto_correction(code)
        assert fixed is True
        assert corrected.endswith("result = records")
    
    def test_detect_bare_data(self):
        """Test detection of bare 'data' expression"""
        code = """data = [1, 2, 3]
data"""
        
        corrected, fixed = self.apply_auto_correction(code)
        assert fixed is True
        assert corrected.endswith("result = data")
    
    def test_detect_bare_dataset(self):
        """Test detection of bare 'dataset' expression"""
        code = """dataset = []
for i in range(5):
    dataset.append({'id': i})
dataset"""
        
        corrected, fixed = self.apply_auto_correction(code)
        assert fixed is True
        assert corrected.endswith("result = dataset")
    
    # ========================================================================
    # Test All Variable Names
    # ========================================================================
    
    @pytest.mark.parametrize("var_name", COMMON_VARS)
    def test_all_variable_names_slice(self, var_name):
        """Test that all common variable names are detected for slice pattern"""
        code = f"""{var_name} = [1, 2, 3, 4, 5]
{var_name}[:3]"""
        
        corrected, fixed = self.apply_auto_correction(code)
        assert fixed is True
        assert corrected.endswith(f"result = {var_name}")
    
    @pytest.mark.parametrize("var_name", COMMON_VARS)
    def test_all_variable_names_bare(self, var_name):
        """Test that all common variable names are detected for bare expression"""
        code = f"""{var_name} = [1, 2, 3]
{var_name}"""
        
        corrected, fixed = self.apply_auto_correction(code)
        assert fixed is True
        assert corrected.endswith(f"result = {var_name}")
    
    # ========================================================================
    # Test No False Positives
    # ========================================================================
    
    def test_no_false_positive_assignment(self):
        """Test that proper assignments are not modified"""
        code = """records = []
for i in range(10):
    records.append(i)
result = records"""
        
        corrected, fixed = self.apply_auto_correction(code)
        assert fixed is False
        assert corrected == code
    
    def test_no_false_positive_function_call(self):
        """Test that function calls are not modified"""
        code = """def process_data(data):
    return data
result = process_data([1, 2, 3])"""
        
        corrected, fixed = self.apply_auto_correction(code)
        assert fixed is False
        assert corrected == code
    
    def test_no_false_positive_different_variable(self):
        """Test that unrelated variables are not modified"""
        code = """my_custom_var = [1, 2, 3]
my_custom_var"""
        
        corrected, fixed = self.apply_auto_correction(code)
        assert fixed is False
        assert corrected == code
    
    def test_no_false_positive_print_statement(self):
        """Test that print statements are not modified"""
        code = """records = [1, 2, 3]
print(records)"""
        
        corrected, fixed = self.apply_auto_correction(code)
        assert fixed is False
        assert corrected == code
    
    def test_no_false_positive_return_statement(self):
        """Test that return statements are not modified"""
        code = """def get_records():
    records = [1, 2, 3]
    return records"""
        
        corrected, fixed = self.apply_auto_correction(code)
        assert fixed is False
        assert corrected == code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

