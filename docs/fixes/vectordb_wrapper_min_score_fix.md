# VectorDB Wrapper Min Score Fix

## Issue Description

The VectorDB Wrapper CLI was not returning search results even though the direct API calls were working correctly. The issue was identified as an overly restrictive default `min_score` parameter.

## Root Cause Analysis

### Problem
- Direct curl API call: `curl --location 'http://localhost:8010/search' --header 'Content-Type: application/json' --data '{"query": "air compressor", "top_n": 5}'` returned 2 results
- VectorDB Wrapper CLI: `search air compressor` returned 0 results

### Investigation
The API returned results with similarity scores:
- PLG.UTIL.COMPRESSED_AIR.LEAK: 0.269509912 (26.95%)
- PLG.PNE.CMP.COMPR.FAIL: 0.335179269 (33.52%)

However, the VectorDB Wrapper CLI was using a default `min_score` of 0.7 (70%), which filtered out these results since they were below the threshold.

### Verification
Testing with different min_score values:
- `min_score=0.7` (default): 0 results
- `min_score=0.2`: 2 results (same as direct API call)

## Solution

### Changes Made

1. **Updated SearchRequest Model** (`vectordb_wrapper/models.py`):
   ```python
   # Before
   min_score: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")
   
   # After  
   min_score: float = Field(default=0.1, ge=0.0, le=1.0, description="Minimum similarity score")
   ```

2. **Updated CLI Interactive Prompts** (`vectordb_wrapper/cli.py`):
   ```python
   # Before
   min_score = input("Minimum score 0.0-1.0 (default: 0.7): ").strip()
   min_score = float(min_score) if min_score else 0.7
   
   # After
   min_score = input("Minimum score 0.0-1.0 (default: 0.1): ").strip()
   min_score = float(min_score) if min_score else 0.1
   ```

3. **Updated Documentation** (`docs/VECTORDB_WRAPPER.md`):
   - Updated SearchRequest model documentation to reflect new default

### Rationale for min_score=0.1

- **Inclusive**: Captures results with low but potentially relevant similarity scores
- **Practical**: Based on actual data showing scores in the 0.26-0.33 range
- **Flexible**: Users can still specify higher thresholds when needed
- **Conservative**: Still filters out completely irrelevant results (< 10% similarity)

## Testing

### Before Fix
```bash
vectordb> search air compressor
📊 Search Results:
   Query: air compressor
   Total Results: 0
   Execution Time: 2074.8ms
   No results found.
```

### After Fix
```bash
vectordb> search air compressor
📊 Search Results:
   Query: air compressor
   Total Results: 2
   Execution Time: 2036.3ms

   Result 1:
     🏷️  Code: PLG.UTIL.COMPRESSED_AIR.LEAK
     📝 Text: Compressed air distribution leak
     🎯 Score: 27.0%
     🔧 Subsystem: AIRSYS
     ⚠️  Severity: Medium

   Result 2:
     🏷️  Code: PLG.PNE.CMP.COMPR.FAIL
     📝 Text: Air compressor failure
     🎯 Score: 33.5%
     🔧 Subsystem: CMP
     ⚠️  Severity: High
```

## Impact

### Positive
- ✅ CLI now returns results consistent with direct API calls
- ✅ More inclusive search results improve user experience
- ✅ Maintains backward compatibility (users can still specify higher min_score)
- ✅ Better default for datasets with lower similarity scores

### Considerations
- Users may see more results than before (potentially including less relevant ones)
- Users can adjust min_score parameter if they want more restrictive filtering

## Files Modified

1. `vectordb_wrapper/models.py` - Updated SearchRequest default min_score
2. `vectordb_wrapper/cli.py` - Updated interactive prompts (2 locations)
3. `docs/VECTORDB_WRAPPER.md` - Updated documentation
4. `docs/fixes/vectordb_wrapper_min_score_fix.md` - This documentation

## Verification Commands

Test the fix with:
```bash
# Start CLI
python -m vectordb_wrapper.cli

# Test search (should now return results)
search air compressor

# Test interactive search with custom min_score
search
# Enter: air compressor
# Enter: 5
# Enter: 0.3 (or any value)
```

Compare with direct API call:
```bash
curl --location 'http://localhost:8010/search' \
--header 'Content-Type: application/json' \
--data '{"query": "air compressor", "top_n": 5}'
```

Both should return the same results.
