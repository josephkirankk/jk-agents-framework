# DefectAnalysisPipeline Format Fix Documentation

## Overview

This document describes the fix implemented for the DefectAnalysisPipeline class to ensure it returns root cause and corrective action data in the correct structured format as specified by the ontology.

## Problem Description

The DefectAnalysisPipeline was returning root causes and corrective actions in an incorrect format:

**Previous Format (Incorrect):**
```python
# Root causes and corrective actions were returned as simple string arrays
root_causes: List[str] = ["RC.WEAR.NORMAL", "RC.LUBE.INSUFFICIENT", "RC.ALIGN.MISALIGN"]
corrective_actions: List[str] = ["CA.LUBE.REPLENISH", "CA.ALIGN.ADJUST", "CA.GEAR.REPLACE"]
```

**Expected Format (Correct):**
```python
# Root causes and corrective actions should be structured objects with both code and text
root_causes: List[RootCause] = [
    {"root_cause_code": "RC.ABRASION.EXTERNAL", "root_cause_text": "Abrasion from external contact with other components or surfaces"},
    {"root_cause_code": "RC.WEAR.NORMAL", "root_cause_text": "Normal wear over operational time"}
]

corrective_actions: List[CorrectiveAction] = [
    {"action_code": "CA.ALIGN.ADJUST", "action_text": "Adjust alignment of components to specifications"},
    {"action_code": "CA.LUBE.REPLENISH", "action_text": "Replenish lubrication"}
]
```

## Solution Implemented

### 1. New Data Models

Added two new Pydantic models in `gemba_agents/defect_analysis/models/data_models.py`:

```python
class RootCause(BaseModel):
    """Model for a structured root cause with code and descriptive text."""
    root_cause_code: str = Field(..., description="Root cause code from ontology")
    root_cause_text: str = Field(..., description="Descriptive text for the root cause")

class CorrectiveAction(BaseModel):
    """Model for a structured corrective action with code and descriptive text."""
    action_code: str = Field(..., description="Action code from ontology")
    action_text: str = Field(..., description="Descriptive text for the corrective action")
```

### 2. Updated AggregatedResults Model

Modified the `AggregatedResults` model to use the new structured format:

```python
class AggregatedResults(BaseModel):
    # ... other fields ...
    root_causes: List[RootCause] = Field(default_factory=list, description="Consolidated root causes with structured format")
    corrective_actions: List[CorrectiveAction] = Field(default_factory=list, description="Consolidated corrective actions with structured format")
```

### 3. Ontology Mapping Loader

Added functionality to load mappings from the ontology file (`config/prompts/ontology_merged_detailed_v8.json`):

```python
def _load_ontology_mappings() -> Dict[str, Dict[str, str]]:
    """Load root cause and corrective action mappings from the ontology file."""
    # Loads mappings from codes to descriptive text
    # Returns: {'root_causes': {code: text}, 'corrective_actions': {code: text}}
```

### 4. Updated Result Aggregation Logic

Modified the consolidation functions in `gemba_agents/defect_analysis/stages/result_aggregation.py`:

- `_consolidate_root_causes()` now returns `List[RootCause]` instead of `List[str]`
- `_consolidate_corrective_actions()` now returns `List[CorrectiveAction]` instead of `List[str]`
- Both functions now look up descriptive text from the ontology mappings

### 5. Fixed Dependent Code

Updated code that was affected by the format change:
- Fixed `gemba_agents/pilger_processing/stages/agent_processing.py` to handle the new structured format when creating string representations

## Testing

Created comprehensive tests to verify the fix:

1. **test_pipeline_format.py** - Basic format verification
2. **test_format_compliance.py** - Comprehensive format compliance testing

Both tests verify:
- Correct data structure (RootCause and CorrectiveAction objects)
- Proper attribute names (`root_cause_code`, `root_cause_text`, `action_code`, `action_text`)
- JSON serialization compatibility
- Code prefixes (`RC.` for root causes, `CA.` for corrective actions)

## Backward Compatibility

The changes maintain backward compatibility by:
- Preserving all existing functionality of the DefectAnalysisPipeline
- Only changing the internal data structure, not the API interface
- Ensuring JSON serialization produces the expected format

## Usage Examples

### Basic Usage
```python
from gemba_agents.defect_analysis.pipeline import DefectAnalysisPipeline

pipeline = DefectAnalysisPipeline()
result = await pipeline.run("Hydraulic hose is damaged and leaking")

# Access structured root causes
for rc in result.root_causes:
    print(f"Code: {rc.root_cause_code}")
    print(f"Text: {rc.root_cause_text}")

# Access structured corrective actions  
for ca in result.corrective_actions:
    print(f"Code: {ca.action_code}")
    print(f"Text: {ca.action_text}")
```

### JSON Output
```python
import json

result_dict = result.model_dump()
json_output = json.dumps(result_dict, indent=2)
# Now contains properly structured root_causes and corrective_actions
```

## Files Modified

1. `gemba_agents/defect_analysis/models/data_models.py` - Added new models
2. `gemba_agents/defect_analysis/stages/result_aggregation.py` - Updated aggregation logic
3. `gemba_agents/pilger_processing/stages/agent_processing.py` - Fixed string formatting

## Files Added

1. `test_pipeline_format.py` - Basic format test
2. `test_format_compliance.py` - Comprehensive compliance test
3. `docs/defect_analysis_format_fix.md` - This documentation

## Verification

Run the tests to verify the fix:

```bash
python test_pipeline_format.py
python test_format_compliance.py
```

Both tests should pass with output showing the correct structured format.
