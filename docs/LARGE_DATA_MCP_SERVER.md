# Large Data MCP Server Documentation

## Overview

The Large Data MCP Server is a Model Context Protocol (MCP) server that provides efficient database-backed storage for large datasets. It prevents flooding the LLM context with excessive tokens by storing datasets in a database and returning only references and previews.

## Key Features

- **Database-Backed Storage**: Uses SQLite for metadata and medium data, file system for large data
- **Multi-Tier Storage**: Automatically selects optimal storage strategy based on data size
- **Token Optimization**: Returns only previews and reference IDs, dramatically reducing token usage
- **Data Persistence**: Datasets persist across sessions and can be accessed multiple times
- **Automatic Compression**: Compresses data to save storage space
- **Efficient Retrieval**: Fast retrieval by reference ID
- **Storage Management**: Tools for listing, statistics, and cleanup

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    JK Agent Framework                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Data         │  │ Data         │  │ Data         │      │
│  │ Generator    │  │ Analyzer     │  │ Manager      │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  Large Data MCP      │
                  │  Server (stdio)      │
                  └──────────┬───────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │   LargeDataStorage           │
              │                              │
              │  ┌────────────────────────┐  │
              │  │  SQLite Database       │  │
              │  │  - Metadata            │  │
              │  │  - Small data (<1MB)   │  │
              │  │  - Medium data (<50MB) │  │
              │  └────────────────────────┘  │
              │                              │
              │  ┌────────────────────────┐  │
              │  │  File System           │  │
              │  │  - Large data (>50MB)  │  │
              │  │  - Compressed files    │  │
              │  └────────────────────────┘  │
              └──────────────────────────────┘
```

## Storage Strategy

The system automatically selects the optimal storage strategy based on data size:

| Size Category | Size Range | Storage Location | Compression |
|--------------|------------|------------------|-------------|
| Small        | < 1MB      | SQLite BLOB      | Optional    |
| Medium       | 1-50MB     | SQLite BLOB      | Yes         |
| Large        | 50-500MB   | File System      | Yes         |
| Huge         | > 500MB    | File System      | Yes         |

## Available Tools

### 1. store_large_dataset

Store a large dataset in database-backed storage.

**Input:**
```json
{
  "dataset": "<JSON string of the dataset>",
  "description": "Description of the dataset",
  "tool_name": "optional_tool_name"
}
```

**Output:**
```json
{
  "status": "success",
  "reference_id": "ref_abc123def456",
  "description": "Large customer dataset",
  "preview": [/* first 5 records */],
  "total_count": 10000,
  "size_mb": 15.42,
  "size_bytes": 16171008,
  "storage_type": "sqlite",
  "compressed": true,
  "message": "✅ Dataset stored successfully! Use reference_id 'ref_abc123def456' to retrieve it later."
}
```

### 2. retrieve_large_dataset

Retrieve a complete dataset by reference ID.

**Input:**
```json
{
  "reference_id": "ref_abc123def456"
}
```

**Output:**
```json
{
  "status": "success",
  "reference_id": "ref_abc123def456",
  "data": [/* complete dataset */]
}
```

### 3. get_dataset_preview

Get a preview of a dataset without retrieving the full data.

**Input:**
```json
{
  "reference_id": "ref_abc123def456",
  "sample_size": 5
}
```

**Output:**
```json
{
  "status": "success",
  "reference_id": "ref_abc123def456",
  "metadata": {
    "description": "Large customer dataset",
    "tool_name": "data_generator",
    "size_mb": 15.42,
    "size_bytes": 16171008,
    "size_category": "medium",
    "storage_type": "sqlite",
    "content_type": "json",
    "compressed": true,
    "created_at": "2025-01-07T10:30:00",
    "access_count": 3,
    "record_count": 10000
  },
  "preview": [/* first 5 records */],
  "total_count": 10000,
  "sample_size": 5
}
```

### 4. list_stored_datasets

List all stored datasets with metadata.

**Input:**
```json
{
  "limit": 50
}
```

**Output:**
```json
{
  "status": "success",
  "total_datasets": 15,
  "datasets": [
    {
      "reference_id": "ref_abc123def456",
      "tool_name": "data_generator",
      "size_bytes": 16171008,
      "size_mb": 15.42,
      "size_category": "medium",
      "storage_type": "sqlite",
      "content_type": "json",
      "created_at": "2025-01-07T10:30:00",
      "last_accessed": "2025-01-07T11:45:00"
    }
  ]
}
```

### 5. get_storage_statistics

Get comprehensive statistics about storage usage.

**Input:**
```json
{}
```

**Output:**
```json
{
  "status": "success",
  "statistics": {
    "total_references": 15,
    "total_size_mb": 234.56,
    "storage_breakdown": {
      "sqlite_small": {
        "count": 5,
        "total_mb": 2.34,
        "avg_mb": 0.47
      },
      "sqlite_medium": {
        "count": 8,
        "total_mb": 156.78,
        "avg_mb": 19.60
      },
      "file_system_large": {
        "count": 2,
        "total_mb": 75.44,
        "avg_mb": 37.72
      }
    },
    "file_system_usage": 75.44
  }
}
```

### 6. cleanup_expired_datasets

Clean up expired datasets (default expiry: 48 hours).

**Input:**
```json
{}
```

**Output:**
```json
{
  "status": "success",
  "cleaned_records": 3,
  "cleaned_files": 2,
  "message": "✅ Cleaned up 3 expired datasets"
}
```

## Configuration

### JK Agent Configuration

Add the Large Data MCP Server to your agent configuration:

```yaml
agents:
  - name: "data_processor"
    description: "Processes large datasets efficiently"
    model: "openai:gpt-4o-mini"
    agent_type: "react"
    
    mcp_servers:
      large_data_storage:
        description: "Database-backed storage for large datasets"
        transport: "stdio"
        command: "python"
        args:
          - "-m"
          - "app.mcp_large_data_server"
```

### Storage Configuration

The storage system can be configured via the `large_data_handling` section in your YAML config:

```yaml
large_data_handling:
  enabled: true
  token_threshold: 1000
  
  large_data:
    sqlite_path: "./data/large_data_storage.db"
    file_path: "./data/large_files/"
    compression: true
    max_sqlite_size_mb: 50
  
  summarization:
    max_summary_tokens: 200
    sample_size: 5
    include_statistics: true
```

## Usage Examples

### Example 1: Generate and Store Large Dataset

```python
# Agent workflow
1. Generate data with Python:
   data = [{"id": i, "value": f"item_{i}"} for i in range(10000)]
   json_data = json.dumps(data)

2. Store using MCP tool:
   store_large_dataset(
     dataset=json_data,
     description="10K customer records"
   )

3. Receive response:
   {
     "reference_id": "ref_abc123",
     "preview": [/* first 5 records */],
     "total_count": 10000,
     "size_mb": 2.5
   }
```

### Example 2: Analyze Stored Dataset

```python
# Agent workflow
1. Get preview first:
   get_dataset_preview(reference_id="ref_abc123")

2. If full data needed:
   retrieve_large_dataset(reference_id="ref_abc123")

3. Analyze with Python:
   # Process the retrieved data
   analysis_results = analyze_data(data)
```

## Token Savings

The Large Data MCP Server dramatically reduces token usage:

| Dataset Size | Full Data Tokens | Preview Tokens | Savings |
|-------------|------------------|----------------|---------|
| 1K records  | ~25,000         | ~500           | 98%     |
| 10K records | ~250,000        | ~500           | 99.8%   |
| 100K records| ~2,500,000      | ~500           | 99.98%  |

## Best Practices

1. **Always use previews first**: Use `get_dataset_preview` to understand data structure before retrieving full datasets

2. **Store analysis results**: If your analysis produces large results, store them back to the database

3. **Regular cleanup**: Use `cleanup_expired_datasets` to free storage space

4. **Monitor storage**: Use `get_storage_statistics` to track storage usage

5. **Descriptive metadata**: Provide clear descriptions when storing datasets for easy identification

## Integration Testing

Run the comprehensive integration test suite:

```bash
python test_large_data_mcp_integration.py
```

This verifies:
- MCP server functionality
- Storage and retrieval operations
- Token efficiency
- Data persistence
- Compression
- Error handling

## Troubleshooting

### Issue: MCP server not starting

**Solution**: Ensure all dependencies are installed:
```bash
pip install mcp>=1.1.0
```

### Issue: Storage path errors

**Solution**: Ensure the storage directories exist and have write permissions:
```bash
mkdir -p ./data/large_files
chmod 755 ./data
```

### Issue: Data not persisting

**Solution**: Check that the SQLite database file is not being deleted between sessions. Verify the `sqlite_path` configuration.

## Performance Considerations

- **SQLite**: Optimized with WAL mode, memory mapping, and large cache
- **Compression**: Reduces storage by 60-80% for typical JSON data
- **Indexing**: Fast lookups by reference ID, tool name, and expiry date
- **Connection pooling**: Efficient database connection management

## Security Considerations

- **Data isolation**: Each dataset is stored with a unique reference ID
- **Expiry**: Automatic cleanup of old data (default: 48 hours)
- **Access tracking**: Monitor dataset access patterns
- **File permissions**: Ensure proper file system permissions for storage directories

## Future Enhancements

- PostgreSQL backend for distributed deployments
- CSV/Parquet export capabilities
- Data versioning and history
- Advanced query capabilities
- Encryption at rest
- Multi-user access control

