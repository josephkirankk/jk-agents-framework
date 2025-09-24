# Python Analysis Examples for Azure DevOps Feature Analyzer

## Overview

The `azure_devops_feature_analyzer` now has Python execution capabilities through the `python_runner` MCP tool. This enables sophisticated data processing, calculations, and visualizations when analyzing Azure DevOps work items.

## Example Use Cases

### 1. **Completion Rate Calculation**

When analyzing a feature with multiple work items, the analyzer can calculate completion percentages:

```python
# Example: Calculate feature completion rate
work_items = [
    {"id": 123, "state": "Closed", "type": "User Story"},
    {"id": 124, "state": "Active", "type": "User Story"}, 
    {"id": 125, "state": "Closed", "type": "Task"},
    {"id": 126, "state": "New", "type": "Bug"}
]

total_items = len(work_items)
completed_items = len([item for item in work_items if item["state"] == "Closed"])
completion_rate = (completed_items / total_items) * 100

print(f"Feature Completion: {completion_rate:.1f}% ({completed_items}/{total_items})")

# Output: Feature Completion: 50.0% (2/4)
```

### 2. **Timeline Analysis**

Process dates to analyze delivery timelines and identify delays:

```python
from datetime import datetime, timedelta
import pandas as pd

# Example: Analyze work item timeline
work_items_with_dates = [
    {"id": 123, "created": "2024-01-15", "closed": "2024-02-10", "state": "Closed"},
    {"id": 124, "created": "2024-01-20", "closed": None, "state": "Active"},
    {"id": 125, "created": "2024-01-10", "closed": "2024-01-25", "state": "Closed"}
]

# Calculate cycle times for closed items
cycle_times = []
for item in work_items_with_dates:
    if item["closed"]:
        created = datetime.strptime(item["created"], "%Y-%m-%d")
        closed = datetime.strptime(item["closed"], "%Y-%m-%d")
        cycle_time = (closed - created).days
        cycle_times.append(cycle_time)

avg_cycle_time = sum(cycle_times) / len(cycle_times) if cycle_times else 0
print(f"Average Cycle Time: {avg_cycle_time:.1f} days")

# Output: Average Cycle Time: 18.5 days
```

### 3. **Status Distribution Analysis**

Create summary statistics for work item states:

```python
from collections import Counter
import matplotlib.pyplot as plt

# Example: Analyze work item status distribution
work_items = [
    {"state": "Closed"}, {"state": "Active"}, {"state": "Closed"},
    {"state": "New"}, {"state": "Active"}, {"state": "Closed"},
    {"state": "Resolved"}, {"state": "New"}
]

# Count work items by state
state_counts = Counter([item["state"] for item in work_items])

# Create a simple visualization
states = list(state_counts.keys())
counts = list(state_counts.values())

plt.figure(figsize=(8, 5))
plt.bar(states, counts, color=['green', 'blue', 'orange', 'red'])
plt.title('Work Item Status Distribution')
plt.xlabel('State')
plt.ylabel('Count')
plt.show()

# Also create a formatted table
print("\nStatus Distribution:")
print("-" * 20)
for state, count in state_counts.items():
    percentage = (count / len(work_items)) * 100
    print(f"{state:<10}: {count:>2} ({percentage:4.1f}%)")
```

### 4. **KPI and Metrics Calculation**

Process complex metrics for business stakeholders:

```python
import pandas as pd
from datetime import datetime, timedelta

# Example: Calculate feature health metrics
def calculate_feature_health(work_items):
    df = pd.DataFrame(work_items)
    
    # Calculate various metrics
    total_items = len(df)
    completed = len(df[df['state'] == 'Closed'])
    in_progress = len(df[df['state'].isin(['Active', 'Resolved'])])
    blocked = len(df[df['state'] == 'Blocked']) if 'Blocked' in df['state'].values else 0
    
    # Health score calculation
    completion_score = (completed / total_items) * 40
    progress_score = (in_progress / total_items) * 30
    blocked_penalty = (blocked / total_items) * -20
    health_score = completion_score + progress_score + blocked_penalty + 30
    
    metrics = {
        'total_items': total_items,
        'completion_rate': f"{(completed/total_items)*100:.1f}%",
        'in_progress_rate': f"{(in_progress/total_items)*100:.1f}%",
        'health_score': f"{health_score:.1f}/100",
        'health_status': 'Good' if health_score > 70 else 'Needs Attention' if health_score > 40 else 'Critical'
    }
    
    return metrics

# Example usage
work_items = [
    {'id': 1, 'state': 'Closed', 'priority': 'High'},
    {'id': 2, 'state': 'Active', 'priority': 'Medium'},
    {'id': 3, 'state': 'Closed', 'priority': 'High'},
    {'id': 4, 'state': 'New', 'priority': 'Low'},
]

health_metrics = calculate_feature_health(work_items)
print("Feature Health Dashboard:")
print("=" * 25)
for key, value in health_metrics.items():
    print(f"{key.replace('_', ' ').title()}: {value}")
```

### 5. **Sprint Velocity Analysis**

Analyze delivery velocity across iterations:

```python
# Example: Calculate sprint velocity trends
sprint_data = [
    {"sprint": "Sprint 1", "completed_points": 23, "planned_points": 30},
    {"sprint": "Sprint 2", "completed_points": 28, "planned_points": 30},
    {"sprint": "Sprint 3", "completed_points": 25, "planned_points": 32},
    {"sprint": "Sprint 4", "completed_points": 30, "planned_points": 35}
]

# Calculate velocity metrics
velocities = []
commitment_accuracy = []

for sprint in sprint_data:
    velocity = sprint["completed_points"]
    accuracy = (sprint["completed_points"] / sprint["planned_points"]) * 100
    velocities.append(velocity)
    commitment_accuracy.append(accuracy)

avg_velocity = sum(velocities) / len(velocities)
avg_accuracy = sum(commitment_accuracy) / len(commitment_accuracy)

print("Sprint Velocity Analysis:")
print("-" * 30)
print(f"Average Velocity: {avg_velocity:.1f} points")
print(f"Commitment Accuracy: {avg_accuracy:.1f}%")

# Trend analysis
if len(velocities) >= 2:
    trend = "Increasing" if velocities[-1] > velocities[0] else "Decreasing" if velocities[-1] < velocities[0] else "Stable"
    print(f"Velocity Trend: {trend}")
```

## Integration with Feature Analysis

These Python capabilities are seamlessly integrated into the feature analyzer workflow:

1. **Data Retrieval**: Use Azure DevOps MCP tools to fetch work items
2. **Python Processing**: Execute calculations and analysis on the retrieved data
3. **Enhanced Reporting**: Include computed metrics in the structured response template
4. **Visual Insights**: Generate charts and visualizations when helpful

## Benefits

- **Accurate Metrics**: Precise calculations for completion rates, cycle times, and KPIs
- **Visual Insights**: Charts and graphs to illustrate feature status and trends  
- **Statistical Analysis**: Confidence intervals, trends, and predictive insights
- **Formatted Output**: Professional tables and summaries for stakeholders
- **Time-based Analysis**: Proper date arithmetic for timeline and delivery analysis

## Best Practices

1. **Always validate data** before processing with Python
2. **Show both code and results** for transparency
3. **Include error handling** for missing or invalid data
4. **Generate visualizations** that enhance understanding
5. **Calculate confidence levels** for statistical insights
6. **Format output** professionally for business stakeholders