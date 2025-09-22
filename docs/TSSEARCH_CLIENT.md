# TsSearch Client Documentation

## Overview

The TsSearch Client is a Python client for interacting with the TsSearch (Typesense) API service. It provides comprehensive search functionality with support for hybrid, keyword, and vector search types, along with advanced filtering and scoring capabilities.

## Features

- **Multiple Search Types**: Hybrid (default), Keyword, and Vector search
- **Advanced Filtering**: Filter by machine, subsystem, component, and defect type
- **Score Thresholds**: Set minimum text match and similarity scores
- **Flexible API**: Both GET and POST methods supported
- **Error Handling**: Comprehensive exception handling with specific error types
- **Async Support**: Full async/await support with context managers
- **Environment Configuration**: Reads server URL from environment variables
- **Logging**: Built-in logging for debugging and monitoring

## Installation

The TsSearch client is part of the `vectordb_wrapper` package:

```python
from vectordb_wrapper import (
    TsSearchClient,
    TsSearchRequest,
    TsSearchFilters,
    SearchType
)
```

## Configuration

### Environment Variables

The client reads the server URL from the `HYBRID_SEARCH_BASE_URL` environment variable:

```bash
HYBRID_SEARCH_BASE_URL=http://localhost:3000
```

If not set, it defaults to `http://localhost:3000`.

## Quick Start

### Basic Search

```python
import asyncio
from vectordb_wrapper import TsSearchClient, TsSearchRequest, SearchType

async def basic_search():
    async with TsSearchClient() as client:
        # Health check
        health = await client.health_check()
        print(f"Server status: {health['status']}")
        
        # Basic hybrid search
        request = TsSearchRequest(
            query="bearing temperature problems",
            search_type=SearchType.HYBRID,
            limit=5
        )
        
        response = await client.search(request)
        
        print(f"Found {response.data.total_found} results")
        for result in response.data.results:
            print(f"- {result.defect_code}: {result.defect_text}")

asyncio.run(basic_search())
```

### Search with Filters

```python
from vectordb_wrapper import TsSearchFilters

async def filtered_search():
    async with TsSearchClient() as client:
        filters = TsSearchFilters(
            machine="PLG",
            subsystem="GBX",
            component="BEARING"
        )
        
        request = TsSearchRequest(
            query="overheating",
            search_type=SearchType.HYBRID,
            limit=10,
            filters=filters
        )
        
        response = await client.search(request)
        print(f"Filtered results: {response.data.total_found}")
```

## API Reference

### TsSearchClient

The main client class for interacting with the TsSearch API.

#### Constructor

```python
TsSearchClient(
    base_url: Optional[str] = None,
    timeout: float = 30.0,
    max_retries: int = 3,
    headers: Optional[Dict[str, str]] = None
)
```

**Parameters:**
- `base_url`: Base URL for the TsSearch API (defaults to env var `HYBRID_SEARCH_BASE_URL`)
- `timeout`: Request timeout in seconds
- `max_retries`: Maximum number of retry attempts
- `headers`: Additional headers to include in requests

#### Methods

##### `async search(request: TsSearchRequest) -> TsSearchResponse`

Perform a search using POST method (recommended).

##### `async search_post(request: TsSearchRequest) -> TsSearchResponse`

Perform a search using POST method with full request body.

##### `async search_get(...) -> TsSearchResponse`

Perform a search using GET method with query parameters.

```python
async search_get(
    query: str,
    search_type: SearchType = SearchType.HYBRID,
    limit: int = 10,
    collection: str = "defects",
    machine: Optional[str] = None,
    subsystem: Optional[str] = None,
    component: Optional[str] = None,
    defect_type: Optional[str] = None,
    include_highlights: bool = False,
    min_text_match_score: Optional[float] = None,
    min_similarity_score: Optional[float] = None
)
```

##### `async health_check() -> Dict[str, Any]`

Perform a health check on the TsSearch server.

### Data Models

#### TsSearchRequest

```python
class TsSearchRequest(BaseModel):
    query: str                                    # Search query (required)
    search_type: SearchType = SearchType.HYBRID  # Search type
    limit: int = 10                              # Results limit (1-100)
    collection: str = "defects"                  # Collection name
    filters: Optional[TsSearchFilters] = None    # Optional filters
    include_highlights: bool = False             # Include highlights
    min_text_match_score: Optional[float] = None # Min text score
    min_similarity_score: Optional[float] = None # Min similarity score
```

#### TsSearchFilters

```python
class TsSearchFilters(BaseModel):
    machine: Optional[str] = None      # Machine type (PLG, CEN, ROT)
    subsystem: Optional[str] = None    # Subsystem (GBX, MTR, PMP, etc.)
    component: Optional[str] = None    # Component (BEARING, GEAR, SEAL, etc.)
    defect_type: Optional[str] = None  # Defect type (OVERHEAT, WEAR, CRACK, etc.)
```

#### SearchType

```python
class SearchType(str, Enum):
    HYBRID = "hybrid"    # Default: combines text and vector search
    KEYWORD = "keyword"  # Text-based search only
    VECTOR = "vector"    # Semantic similarity search only
```

#### TsSearchResponse

```python
class TsSearchResponse(BaseModel):
    success: bool
    data: TsSearchData
    message: str
    timestamp: float
```

#### TsDefectResult

```python
class TsDefectResult(BaseModel):
    id: str
    defect_code: str
    defect_text: str
    machine: str
    subsystem: str
    component: str
    defect_type: str
    subsystem_description: str
    component_description: str
    defect_type_description: str
    keywords: List[str]
    tags: List[str]
    score: float
    highlights: Optional[Dict[str, Any]]
    created_on: int
```

## Search Types

### Hybrid Search (Default)

Combines keyword and vector search for best results:

```python
request = TsSearchRequest(
    query="bearing temperature rise",
    search_type=SearchType.HYBRID,
    limit=10
)
```

**Best for:** Most search scenarios, natural language queries

### Keyword Search

Text-based exact matching:

```python
request = TsSearchRequest(
    query="PLG.GBX.BEARING.OVERHEAT",
    search_type=SearchType.KEYWORD,
    limit=5
)
```

**Best for:** Exact defect codes, specific terminology

### Vector Search

Semantic similarity search:

```python
request = TsSearchRequest(
    query="equipment running hot with unusual noise",
    search_type=SearchType.VECTOR,
    limit=10
)
```

**Best for:** Conceptual searches, finding similar defects

## Advanced Features

### Score Thresholds

Control result quality with score thresholds:

```python
request = TsSearchRequest(
    query="bearing problems",
    search_type=SearchType.HYBRID,
    min_text_match_score=1.0e18,      # High precision text matches
    min_similarity_score=0.3,         # Good semantic similarity
    limit=10
)
```

### Highlights

Get search term highlights in results:

```python
request = TsSearchRequest(
    query="bearing temperature",
    include_highlights=True,
    limit=5
)
```

### Multiple Filters

Combine multiple filters for precise results:

```python
filters = TsSearchFilters(
    machine="PLG",
    subsystem="GBX",
    component="BEARING",
    defect_type="OVERHEAT"
)

request = TsSearchRequest(
    query="temperature",
    filters=filters,
    limit=5
)
```

## Error Handling

The client provides specific exception types:

```python
from vectordb_wrapper import (
    TsSearchException,
    TsSearchConnectionError,
    TsSearchValidationError,
    TsSearchServerError,
    TsSearchTimeoutError,
    TsSearchNotFoundError
)

async def search_with_error_handling():
    try:
        async with TsSearchClient() as client:
            request = TsSearchRequest(query="test search")
            response = await client.search(request)
            
    except TsSearchConnectionError:
        print("Failed to connect to server")
    except TsSearchValidationError:
        print("Invalid request parameters")
    except TsSearchServerError:
        print("Server error occurred")
    except TsSearchTimeoutError:
        print("Request timed out")
    except TsSearchException as e:
        print(f"General search error: {e}")
```

## Performance Tips

1. **Use Hybrid Search**: Best balance of precision and recall
2. **Apply Filters**: Reduce search space for faster results
3. **Set Appropriate Limits**: Don't request more results than needed
4. **Use Score Thresholds**: Filter out low-quality results
5. **Monitor Processing Time**: Available in response for optimization

## Examples

See `ts_search_example.py` for comprehensive usage examples including:

- Basic hybrid search
- Filtered searches
- GET method usage
- Search type comparisons
- Score threshold usage
- Error handling

## Testing

Run the test suite to verify functionality:

```bash
python test_ts_search_client.py
```

This runs comprehensive tests covering:
- Health checks
- All search types
- Filtering
- Score thresholds
- Error handling
- Performance validation

## Logging

The client includes built-in logging. Configure logging level as needed:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

Log messages include:
- Client initialization
- Search requests and responses
- Performance metrics
- Error details

## Cross-Platform Compatibility

The client is designed to work on both Windows and macOS:
- Uses forward slashes in URLs
- Handles encoding properly
- Compatible with different Python environments
- Works with virtual environments (.venv)

## Integration with Existing Code

The TsSearch client is completely separate from the existing VectorDB client:

```python
# Both can be used together
from vectordb_wrapper import VectorDBClient, TsSearchClient

# VectorDB for traditional operations
async with VectorDBClient() as vdb_client:
    # VectorDB operations
    pass

# TsSearch for Typesense operations  
async with TsSearchClient() as ts_client:
    # TsSearch operations
    pass
```
