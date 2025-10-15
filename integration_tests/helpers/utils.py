"""
Utility functions for integration tests.
"""

import asyncio
import time
import re
import json
import jsonschema
from typing import Any, Callable, Dict, Optional, List, Union
from functools import wraps


async def retry_on_failure(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 10.0,
    exceptions: tuple = (Exception,)
) -> Any:
    """
    Retry async function on failure with exponential backoff.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay after each retry
        max_delay: Maximum delay between retries
        exceptions: Tuple of exceptions to catch and retry
        
    Returns:
        Function result if successful
        
    Raises:
        Last exception if all retries fail
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func()
            else:
                return func()
        except exceptions as e:
            last_exception = e
            
            if attempt < max_retries:
                print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
                delay = min(delay * backoff_factor, max_delay)
            else:
                print(f"All {max_retries + 1} attempts failed.")
                raise last_exception


def validate_json_schema(data: Union[Dict, List], schema: Dict) -> tuple[bool, Optional[str]]:
    """
    Validate data against JSON schema.
    
    Args:
        data: Data to validate
        schema: JSON schema
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        jsonschema.validate(instance=data, schema=schema)
        return True, None
    except jsonschema.exceptions.ValidationError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Validation error: {e}"


def extract_json_from_text(text: str) -> Optional[Dict]:
    """
    Extract JSON object from text that may contain markdown or other content.
    
    Args:
        text: Text containing JSON
        
    Returns:
        Parsed JSON dict or None if not found
    """
    # Try direct parsing
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    
    # Try markdown code block
    patterns = [
        r'```json\s*(\{.*?\})\s*```',
        r'```\s*(\{.*?\})\s*```',
        r'(\{[^{}]*\{[^{}]*\}[^{}]*\})',  # Nested objects
        r'(\{[^{}]+\})',  # Simple objects
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
    
    return None


def extract_code_blocks(text: str, language: Optional[str] = None) -> List[str]:
    """
    Extract code blocks from markdown text.
    
    Args:
        text: Text containing markdown code blocks
        language: Optional language filter (e.g., 'python', 'json')
        
    Returns:
        List of code block contents
    """
    if language:
        pattern = rf'```{language}\s*(.*?)\s*```'
    else:
        pattern = r'```(?:\w+)?\s*(.*?)\s*```'
    
    matches = re.findall(pattern, text, re.DOTALL)
    return matches


def validate_regex_match(text: str, pattern: str, flags: int = 0) -> bool:
    """
    Check if text matches regex pattern.
    
    Args:
        text: Text to check
        pattern: Regex pattern
        flags: Optional regex flags
        
    Returns:
        True if pattern matches
    """
    return bool(re.search(pattern, text, flags))


def measure_execution_time(func: Callable) -> Callable:
    """
    Decorator to measure function execution time.
    
    Args:
        func: Function to measure
        
    Returns:
        Wrapped function that includes timing
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start_time
        
        # Attach duration to result if it's a dict
        if isinstance(result, dict):
            result['_execution_time'] = duration
        
        return result
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        
        # Attach duration to result if it's a dict
        if isinstance(result, dict):
            result['_execution_time'] = duration
        
        return result
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text for comparison.
    
    Args:
        text: Text to normalize
        
    Returns:
        Text with normalized whitespace
    """
    return ' '.join(text.split())


def contains_keywords(text: str, keywords: List[str], case_sensitive: bool = False) -> bool:
    """
    Check if text contains all specified keywords.
    
    Args:
        text: Text to search
        keywords: List of keywords to find
        case_sensitive: Whether search is case-sensitive
        
    Returns:
        True if all keywords found
    """
    if not case_sensitive:
        text = text.lower()
        keywords = [k.lower() for k in keywords]
    
    return all(keyword in text for keyword in keywords)


def contains_any_keyword(text: str, keywords: List[str], case_sensitive: bool = False) -> bool:
    """
    Check if text contains any of specified keywords.
    
    Args:
        text: Text to search
        keywords: List of keywords to find
        case_sensitive: Whether search is case-sensitive
        
    Returns:
        True if any keyword found
    """
    if not case_sensitive:
        text = text.lower()
        keywords = [k.lower() for k in keywords]
    
    return any(keyword in text for keyword in keywords)


def extract_numbers(text: str) -> List[float]:
    """
    Extract all numbers from text.
    
    Args:
        text: Text containing numbers
        
    Returns:
        List of extracted numbers
    """
    pattern = r'-?\d+\.?\d*'
    matches = re.findall(pattern, text)
    return [float(m) for m in matches if m]


def compare_dicts_partial(actual: Dict, expected: Dict, ignore_keys: Optional[List[str]] = None) -> bool:
    """
    Compare dicts allowing actual to have extra keys.
    
    Args:
        actual: Actual dict
        expected: Expected dict (subset)
        ignore_keys: Keys to ignore in comparison
        
    Returns:
        True if expected is subset of actual
    """
    ignore_keys = ignore_keys or []
    
    for key, value in expected.items():
        if key in ignore_keys:
            continue
        
        if key not in actual:
            return False
        
        if isinstance(value, dict) and isinstance(actual[key], dict):
            if not compare_dicts_partial(actual[key], value, ignore_keys):
                return False
        elif actual[key] != value:
            return False
    
    return True


async def wait_for_condition(
    condition: Callable[[], bool],
    timeout: float = 30.0,
    check_interval: float = 0.5,
    error_message: str = "Condition not met within timeout"
) -> bool:
    """
    Wait for a condition to become true.
    
    Args:
        condition: Callable that returns bool
        timeout: Maximum time to wait in seconds
        check_interval: Time between checks in seconds
        error_message: Error message if timeout
        
    Returns:
        True if condition met
        
    Raises:
        TimeoutError if condition not met within timeout
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if condition():
            return True
        await asyncio.sleep(check_interval)
    
    raise TimeoutError(error_message)


def create_test_data(template: Dict, count: int = 1, vary_fields: Optional[List[str]] = None) -> List[Dict]:
    """
    Create test data from template.
    
    Args:
        template: Template dict
        count: Number of items to create
        vary_fields: Fields to vary with index
        
    Returns:
        List of test data dicts
    """
    vary_fields = vary_fields or []
    result = []
    
    for i in range(count):
        item = template.copy()
        for field in vary_fields:
            if field in item:
                item[field] = f"{item[field]}_{i}"
        result.append(item)
    
    return result


def sanitize_for_logging(data: Any, max_length: int = 500) -> str:
    """
    Sanitize data for logging (truncate long strings, hide sensitive info).
    
    Args:
        data: Data to sanitize
        max_length: Maximum string length
        
    Returns:
        Sanitized string representation
    """
    if isinstance(data, str):
        # Hide potential API keys or tokens
        data = re.sub(r'(api[_-]?key|token|password)\s*[:=]\s*["\']?([^"\'\s]+)["\']?', 
                     r'\1=***', data, flags=re.IGNORECASE)
        
        if len(data) > max_length:
            return data[:max_length] + "..."
        return data
    
    elif isinstance(data, (dict, list)):
        json_str = json.dumps(data, indent=2)
        return sanitize_for_logging(json_str, max_length)
    
    else:
        return str(data)[:max_length]
