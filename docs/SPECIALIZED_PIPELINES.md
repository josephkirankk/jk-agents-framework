# Specialized Agent Pipelines Documentation

## Overview

The jk-agents-framework provides a flexible foundation for creating specialized agent pipelines. The framework's modular architecture allows for the development of domain-specific workflows that combine multiple processing stages to provide comprehensive analysis and recommendations.

## Pipeline Architecture

### General Pipeline Structure

Specialized pipelines in the framework follow a common pattern of multi-stage processing:

1. **Input Processing Stage**
   - Analyzes user input to extract key information
   - Structures data for downstream processing
   - Validates and normalizes input format

2. **Analysis Stage**
   - Applies domain-specific logic and knowledge
   - Performs searches, calculations, or transformations
   - Generates intermediate results

3. **Result Synthesis Stage**
   - Consolidates analysis results
   - Identifies patterns and insights
   - Structures output for final presentation

### Configuration Models

Pipeline configurations use Pydantic models for validation and type safety:

```python
class PipelineConfig(BaseModel):
    enable_logging: bool = True        # Detailed logging
    enable_caching: bool = True        # Result caching
    timeout_seconds: int = 120         # Processing timeout
    parallel_processing: bool = True   # Parallel execution
```

## Building Custom Pipelines

### Pipeline Development Pattern

The framework supports creating custom pipelines by following these patterns:

#### 1. Multi-Stage Processing

```python
class CustomPipeline:
    def __init__(self, config: PipelineConfig):
        self.config = config
    
    async def run(self, user_input: str):
        # Stage 1: Input processing
        processed_input = await self.process_input(user_input)
        
        # Stage 2: Analysis
        analysis_result = await self.analyze(processed_input)
        
        # Stage 3: Result synthesis
        final_result = await self.synthesize_results(analysis_result)
        
        return final_result
```

#### 2. Agent Integration

Pipelines can leverage the framework's agent system:

```python
async def process_with_agent(self, input_data, agent_name):
    # Load agent configuration
    agent_config = self.get_agent_config(agent_name)
    
    # Build and execute agent
    agent = await build_react_agent(agent_config, ...)
    result = await agent.ainvoke(input_data)
    
    return result
```

#### 3. Tool Integration

Pipelines can use MCP servers and other tools:

```yaml
pipeline_config:
  tools:
    data_processor:
      transport: "stdio"
      command: "python"
      args: ["tools/data_processor.py"]
    
    api_client:
      transport: "http"
      url: "http://localhost:8000/api"
```

## Pipeline Examples

### 1. Data Processing Pipeline

A pipeline for processing and analyzing structured data:

```python
class DataProcessingPipeline:
    """Pipeline for structured data analysis."""
    
    async def run(self, data_input: str):
        # Parse and validate input data
        structured_data = await self.parse_input(data_input)
        
        # Apply analysis algorithms
        analysis_results = await self.analyze_data(structured_data)
        
        # Generate insights and recommendations
        insights = await self.generate_insights(analysis_results)
        
        return {
            "success": True,
            "data_summary": structured_data.summary(),
            "analysis_results": analysis_results,
            "insights": insights,
            "processing_time_ms": self.get_processing_time()
        }
```

### 2. Multi-Modal Analysis Pipeline

A pipeline that processes different types of content:

```python
class MultiModalPipeline:
    """Pipeline for analyzing text, images, and documents."""
    
    async def run(self, content_items: List[Any]):
        results = []
        
        for item in content_items:
            if self.is_text(item):
                result = await self.process_text(item)
            elif self.is_image(item):
                result = await self.process_image(item)
            elif self.is_document(item):
                result = await self.process_document(item)
            
            results.append(result)
        
        # Combine results from all modalities
        combined_analysis = await self.combine_results(results)
        
        return combined_analysis
```

### 3. Workflow Orchestration Pipeline

A pipeline that coordinates multiple agents:

```python
class WorkflowPipeline:
    """Pipeline for coordinating multiple specialized agents."""
    
    async def run(self, task_description: str):
        # Break down task into subtasks
        subtasks = await self.decompose_task(task_description)
        
        # Execute subtasks with appropriate agents
        subtask_results = []
        for subtask in subtasks:
            agent_name = self.select_agent(subtask.type)
            result = await self.execute_with_agent(subtask, agent_name)
            subtask_results.append(result)
        
        # Aggregate and synthesize results
        final_result = await self.synthesize_workflow_results(subtask_results)
        
        return final_result
```

## API Integration

Pipelines can be exposed through FastAPI endpoints:

```python
@app.post("/custom-pipeline")
async def custom_pipeline_endpoint(request: CustomPipelineRequest):
    """Custom pipeline endpoint for specialized processing."""
    try:
        # Create pipeline configuration
        config = CustomPipelineConfig(
            enable_logging=request.enable_logging,
            timeout_seconds=request.timeout_seconds
        )
        
        # Create and run pipeline
        pipeline = CustomPipeline(config)
        result = await pipeline.run(request.input)
        
        return CustomPipelineResponse(
            success=True,
            result=result,
            processing_time_ms=pipeline.get_processing_time()
        )
    
    except Exception as e:
        return CustomPipelineResponse(
            success=False,
            error=str(e)
        )
```

## Configuration Examples

### Basic Pipeline Configuration

```yaml
pipeline:
  name: "data_processing_pipeline"
  config:
    enable_logging: true
    enable_caching: true
    timeout_seconds: 300
    parallel_processing: true
  
  agents:
    - name: "data_validator"
      model: "openai:gpt-4o-mini"
      prompt: "Validate and structure input data"
    
    - name: "data_analyzer"
      model: "google:gemini-2.0-flash-exp"
      prompt: "Analyze structured data and generate insights"
```

### Multi-Provider Pipeline

```yaml
pipeline:
  name: "multi_provider_analysis"
  
  stages:
    - name: "preprocessing"
      agent: "preprocessor"
      model: "openai:gpt-3.5-turbo"
    
    - name: "analysis"
      agent: "analyzer"
      model: "google:gemini-1.5-pro"
    
    - name: "synthesis"
      agent: "synthesizer"
      model: "anthropic:claude-sonnet-4"
```

## Performance Optimization

### Parallel Processing

```python
async def parallel_pipeline_execution(tasks: List[Task]):
    """Execute multiple pipeline stages in parallel."""
    
    # Group tasks that can run in parallel
    parallel_groups = group_parallel_tasks(tasks)
    
    results = []
    for group in parallel_groups:
        # Execute tasks in parallel within each group
        group_results = await asyncio.gather(*[
            execute_task(task) for task in group
        ])
        results.extend(group_results)
    
    return results
```

### Caching Strategy

```python
class PipelineCache:
    """Caching system for pipeline results."""
    
    def __init__(self):
        self.cache = {}
        self.ttl = 3600  # 1 hour TTL
    
    async def get_or_compute(self, key: str, compute_func: Callable):
        if key in self.cache and not self.is_expired(key):
            return self.cache[key]['result']
        
        result = await compute_func()
        self.cache[key] = {
            'result': result,
            'timestamp': time.time()
        }
        return result
```

## Error Handling and Monitoring

### Pipeline Health Monitoring

```python
class PipelineMonitor:
    """Monitor pipeline health and performance."""
    
    def track_execution(self, pipeline_name: str, stage: str):
        return {
            "pipeline": pipeline_name,
            "stage": stage,
            "start_time": time.time(),
            "status": "running"
        }
    
    def record_completion(self, execution_info: dict, success: bool):
        execution_info.update({
            "end_time": time.time(),
            "duration_ms": (time.time() - execution_info["start_time"]) * 1000,
            "status": "completed" if success else "failed"
        })
        
        # Log to monitoring system
        self.log_execution(execution_info)
```

### Graceful Error Recovery

```python
async def resilient_pipeline_execution(pipeline, input_data, max_retries=3):
    """Execute pipeline with retry logic and fallback."""
    
    for attempt in range(max_retries):
        try:
            return await pipeline.run(input_data)
        
        except TemporaryError as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
            raise
        
        except PermanentError as e:
            # Try fallback pipeline
            fallback_pipeline = create_fallback_pipeline()
            return await fallback_pipeline.run(input_data)
```

## Integration with Main Framework

### Supervisor Integration

```yaml
supervisor:
  prompt: |
    Available specialized pipelines:
    - data_processor: For structured data analysis
    - multimodal_analyzer: For mixed content processing
    - workflow_orchestrator: For complex task coordination
    
    Route requests to appropriate pipelines based on input type and complexity.
```

### Agent Configuration

```yaml
agents:
  - name: "pipeline_coordinator"
    description: "Coordinates specialized pipeline execution"
    model: "azure_openai:gpt-4o"
    prompt: |
      You coordinate specialized pipeline execution based on input requirements.
      Select the most appropriate pipeline and configuration for each task.
    
    python_tools:
      pipeline_tools:
        module_path: "pipelines.coordinator"
        tool_names: ["execute_pipeline", "select_pipeline"]
```

## Extension Points

The pipeline system provides several extension points:

1. **Custom Pipeline Types**: Implement new pipeline classes
2. **Stage Processors**: Add new processing stages
3. **Result Formatters**: Custom output formatting
4. **Integration Adapters**: Connect to external systems
5. **Monitoring Plugins**: Custom monitoring and alerting

This flexible architecture enables the development of sophisticated, domain-specific processing workflows while maintaining the framework's core multi-agent capabilities.