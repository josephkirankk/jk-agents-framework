"""
ADO Smart Data Filter

Intelligent filtering functions that analyze user queries and extract only the essential
information from large ADO datasets before sending to LLM. This prevents information
overload and ensures focused, relevant responses.

Functions are designed to be used with Python MCP for in-agent data processing.
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Union
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class QueryIntent:
    """Represents the user's query intent for intelligent data filtering"""
    intent_type: str  # 'count', 'list', 'details', 'analysis', 'relationship'
    entities_requested: List[str]  # ['bugs', 'user_stories', 'tasks']
    fields_needed: List[str]  # ['id', 'title', 'assignee', 'state', 'created_date']
    filter_criteria: Dict[str, Any]  # {'state': 'active', 'assignee': 'specific_user'}
    aggregation_level: str  # 'summary', 'grouped', 'individual'
    context_depth: str  # 'minimal', 'standard', 'comprehensive'


def analyze_query_intent(user_query: str, context: str = "") -> QueryIntent:
    """
    Analyze user query to understand what information they actually need.
    
    Args:
        user_query: The original user query
        context: Additional context from conversation or previous steps
    
    Returns:
        QueryIntent object with analysis results
    """
    query_lower = user_query.lower()
    
    # Intent type detection
    if any(word in query_lower for word in ['count', 'how many', 'number of']):
        intent_type = 'count'
        context_depth = 'minimal'
        aggregation_level = 'summary'
    elif any(word in query_lower for word in ['list', 'show', 'get all', 'what are']):
        intent_type = 'list'
        context_depth = 'standard'
        aggregation_level = 'individual'
    elif any(word in query_lower for word in ['details', 'describe', 'analyze', 'breakdown']):
        intent_type = 'details'
        context_depth = 'comprehensive'
        aggregation_level = 'grouped'
    elif any(word in query_lower for word in ['related', 'linked', 'connected', 'parent', 'child']):
        intent_type = 'relationship'
        context_depth = 'standard'
        aggregation_level = 'grouped'
    else:
        intent_type = 'analysis'
        context_depth = 'standard'
        aggregation_level = 'grouped'
    
    # Entity detection
    entities_requested = []
    entity_map = {
        'bug': ['bug', 'defect', 'issue'],
        'user_story': ['story', 'user story', 'feature'],
        'task': ['task', 'work item'],
        'epic': ['epic'],
        'feature': ['feature'],
        'test_case': ['test', 'test case']
    }
    
    for entity, keywords in entity_map.items():
        if any(keyword in query_lower for keyword in keywords):
            entities_requested.append(entity)
    
    if not entities_requested:
        entities_requested = ['work_item']  # Default fallback
    
    # Fields needed based on intent
    base_fields = ['id', 'title', 'state', 'work_item_type']
    
    if intent_type == 'count':
        fields_needed = ['id', 'work_item_type', 'state']
    elif intent_type == 'list':
        fields_needed = base_fields + ['assigned_to', 'created_date']
    elif intent_type == 'relationship':
        fields_needed = base_fields + ['parent_id', 'child_ids', 'related_ids']
    else:
        fields_needed = base_fields + ['assigned_to', 'created_date', 'priority', 'area_path']
    
    # Detect specific field requests
    field_keywords = {
        'assignee': ['assigned', 'assignee', 'owner'],
        'priority': ['priority', 'important', 'critical'],
        'created_date': ['created', 'when', 'date'],
        'description': ['description', 'details', 'content'],
        'comments': ['comments', 'discussion', 'notes'],
        'tags': ['tag', 'label']
    }
    
    for field, keywords in field_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            if field not in fields_needed:
                fields_needed.append(field)
    
    # Filter criteria detection
    filter_criteria = {}
    
    # State filters
    if any(word in query_lower for word in ['active', 'in progress', 'open']):
        filter_criteria['state'] = 'active'
    elif any(word in query_lower for word in ['closed', 'done', 'completed']):
        filter_criteria['state'] = 'closed'
    elif any(word in query_lower for word in ['new', 'unassigned']):
        filter_criteria['state'] = 'new'
    
    # Time-based filters
    time_patterns = [
        (r'last (\d+) days?', lambda x: {'created_after': datetime.now() - timedelta(days=int(x))}),
        (r'past (\d+) weeks?', lambda x: {'created_after': datetime.now() - timedelta(weeks=int(x))}),
        (r'recent', lambda x: {'created_after': datetime.now() - timedelta(days=7)})
    ]
    
    for pattern, filter_func in time_patterns:
        match = re.search(pattern, query_lower)
        if match:
            filter_criteria.update(filter_func(match.group(1) if match.groups() else None))
            break
    
    return QueryIntent(
        intent_type=intent_type,
        entities_requested=entities_requested,
        fields_needed=fields_needed,
        filter_criteria=filter_criteria,
        aggregation_level=aggregation_level,
        context_depth=context_depth
    )


def filter_work_items_by_intent(work_items: List[Dict[str, Any]], 
                               intent: QueryIntent,
                               max_items: int = 50) -> Dict[str, Any]:
    """
    Filter and summarize work items based on query intent.
    
    Args:
        work_items: List of work items from ADO API
        intent: QueryIntent object describing what user actually needs
        max_items: Maximum number of items to include in detailed results
    
    Returns:
        Filtered and structured data optimized for LLM consumption
    """
    if not work_items:
        return {
            'filtered_data': [],
            'summary': {'total_count': 0, 'message': 'No work items found'},
            'metadata': {'intent_type': intent.intent_type, 'fields_included': intent.fields_needed}
        }
    
    # Apply filters
    filtered_items = apply_filters(work_items, intent.filter_criteria)
    
    # Extract only needed fields
    essential_data = []
    for item in filtered_items[:max_items]:  # Limit for LLM consumption
        essential_item = extract_essential_fields(item, intent.fields_needed)
        essential_data.append(essential_item)
    
    # Generate appropriate summary based on intent
    summary = generate_summary_by_intent(filtered_items, intent)
    
    # Create metadata for LLM context
    metadata = {
        'intent_type': intent.intent_type,
        'total_found': len(filtered_items),
        'items_included': len(essential_data),
        'fields_included': intent.fields_needed,
        'truncated': len(filtered_items) > max_items
    }
    
    return {
        'filtered_data': essential_data,
        'summary': summary,
        'metadata': metadata
    }


def apply_filters(work_items: List[Dict[str, Any]], 
                 filter_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Apply filter criteria to work items list"""
    if not filter_criteria:
        return work_items
    
    filtered = []
    
    for item in work_items:
        include_item = True
        
        # State filter
        if 'state' in filter_criteria:
            item_state = item.get('fields', {}).get('System.State', '').lower()
            if filter_criteria['state'] == 'active' and item_state not in ['active', 'new', 'approved']:
                include_item = False
            elif filter_criteria['state'] == 'closed' and item_state not in ['closed', 'done', 'resolved']:
                include_item = False
            elif filter_criteria['state'] == 'new' and item_state != 'new':
                include_item = False
        
        # Date filter
        if 'created_after' in filter_criteria and include_item:
            created_date_str = item.get('fields', {}).get('System.CreatedDate', '')
            if created_date_str:
                try:
                    created_date = datetime.fromisoformat(created_date_str.replace('Z', '+00:00'))
                    if created_date < filter_criteria['created_after']:
                        include_item = False
                except:
                    pass
        
        if include_item:
            filtered.append(item)
    
    return filtered


def extract_essential_fields(work_item: Dict[str, Any], 
                           fields_needed: List[str]) -> Dict[str, Any]:
    """Extract only the essential fields from a work item based on query intent"""
    fields = work_item.get('fields', {})
    essential = {}
    
    # Field mapping from intent to ADO field names
    field_mapping = {
        'id': 'id',  # Use root level id
        'title': 'System.Title',
        'state': 'System.State',
        'work_item_type': 'System.WorkItemType',
        'assigned_to': 'System.AssignedTo',
        'created_date': 'System.CreatedDate',
        'priority': 'Microsoft.VSTS.Common.Priority',
        'area_path': 'System.AreaPath',
        'description': 'System.Description',
        'tags': 'System.Tags'
    }
    
    for field in fields_needed:
        if field == 'id':
            essential['id'] = work_item.get('id')
        elif field in field_mapping:
            ado_field = field_mapping[field]
            value = fields.get(ado_field)
            
            # Clean and format values
            if field == 'assigned_to' and isinstance(value, dict):
                essential[field] = value.get('displayName', 'Unassigned')
            elif field == 'created_date' and value:
                # Format date for better readability
                try:
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    essential[field] = dt.strftime('%Y-%m-%d')
                except:
                    essential[field] = value
            elif field == 'description' and value:
                # Truncate long descriptions
                essential[field] = (value[:200] + '...') if len(value) > 200 else value
            else:
                essential[field] = value
    
    # Handle relationships if requested
    if 'parent_id' in fields_needed or 'child_ids' in fields_needed:
        relations = work_item.get('relations', [])
        if 'parent_id' in fields_needed:
            parent = next((r for r in relations if r.get('rel') == 'System.LinkTypes.Hierarchy-Reverse'), None)
            essential['parent_id'] = parent.get('url', '').split('/')[-1] if parent else None
        
        if 'child_ids' in fields_needed:
            children = [r.get('url', '').split('/')[-1] for r in relations 
                       if r.get('rel') == 'System.LinkTypes.Hierarchy-Forward']
            essential['child_ids'] = children
    
    return essential


def generate_summary_by_intent(work_items: List[Dict[str, Any]], 
                             intent: QueryIntent) -> Dict[str, Any]:
    """Generate appropriate summary based on query intent"""
    if intent.intent_type == 'count':
        return generate_count_summary(work_items)
    elif intent.intent_type == 'list':
        return generate_list_summary(work_items)
    elif intent.intent_type == 'relationship':
        return generate_relationship_summary(work_items)
    else:
        return generate_general_summary(work_items)


def generate_count_summary(work_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate count-focused summary"""
    total = len(work_items)
    
    # Count by type
    type_counts = defaultdict(int)
    state_counts = defaultdict(int)
    
    for item in work_items:
        fields = item.get('fields', {})
        work_type = fields.get('System.WorkItemType', 'Unknown')
        state = fields.get('System.State', 'Unknown')
        
        type_counts[work_type] += 1
        state_counts[state] += 1
    
    return {
        'total_count': total,
        'by_type': dict(type_counts),
        'by_state': dict(state_counts),
        'summary_text': f"Found {total} items: {', '.join([f'{count} {type}s' for type, count in type_counts.items()])}"
    }


def generate_list_summary(work_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate list-focused summary with key stats"""
    total = len(work_items)
    
    # Basic stats
    assignee_counts = defaultdict(int)
    priority_counts = defaultdict(int)
    
    for item in work_items:
        fields = item.get('fields', {})
        assignee = fields.get('System.AssignedTo', {})
        assignee_name = assignee.get('displayName', 'Unassigned') if isinstance(assignee, dict) else 'Unassigned'
        priority = fields.get('Microsoft.VSTS.Common.Priority', 'Not Set')
        
        assignee_counts[assignee_name] += 1
        priority_counts[priority] += 1
    
    return {
        'total_count': total,
        'top_assignees': dict(list(assignee_counts.items())[:5]),
        'priority_distribution': dict(priority_counts),
        'summary_text': f"Listed {total} items across {len(assignee_counts)} assignees"
    }


def generate_relationship_summary(work_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate relationship-focused summary"""
    total = len(work_items)
    items_with_children = 0
    items_with_parents = 0
    total_relationships = 0
    
    for item in work_items:
        relations = item.get('relations', [])
        has_parent = any(r.get('rel') == 'System.LinkTypes.Hierarchy-Reverse' for r in relations)
        children_count = len([r for r in relations if r.get('rel') == 'System.LinkTypes.Hierarchy-Forward'])
        
        if has_parent:
            items_with_parents += 1
        if children_count > 0:
            items_with_children += 1
            
        total_relationships += len(relations)
    
    return {
        'total_count': total,
        'items_with_parents': items_with_parents,
        'items_with_children': items_with_children,
        'total_relationships': total_relationships,
        'summary_text': f"Analyzed {total} items: {items_with_children} have children, {items_with_parents} have parents"
    }


def generate_general_summary(work_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate general analysis summary"""
    total = len(work_items)
    
    type_counts = defaultdict(int)
    state_counts = defaultdict(int)
    recent_items = 0
    
    week_ago = datetime.now() - timedelta(days=7)
    
    for item in work_items:
        fields = item.get('fields', {})
        work_type = fields.get('System.WorkItemType', 'Unknown')
        state = fields.get('System.State', 'Unknown')
        
        type_counts[work_type] += 1
        state_counts[state] += 1
        
        # Check if recent
        created_date_str = fields.get('System.CreatedDate', '')
        if created_date_str:
            try:
                created_date = datetime.fromisoformat(created_date_str.replace('Z', '+00:00'))
                if created_date > week_ago:
                    recent_items += 1
            except:
                pass
    
    return {
        'total_count': total,
        'by_type': dict(type_counts),
        'by_state': dict(state_counts),
        'recent_items_count': recent_items,
        'summary_text': f"Analyzed {total} items: {recent_items} created in last 7 days"
    }


# Specialized filtering functions for common use cases

def extract_bug_ids_for_stories(work_items: List[Dict[str, Any]], 
                               story_ids: List[str]) -> Dict[str, List[str]]:
    """
    Extract bug IDs linked to specific user stories.
    Optimized for the specific use case from the log.
    
    Returns only the essential mapping: story_id -> [bug_ids]
    """
    story_bug_mapping = {}
    
    for item in work_items:
        item_id = str(item.get('id', ''))
        work_type = item.get('fields', {}).get('System.WorkItemType', '')
        
        if work_type == 'Bug':
            # Find which stories this bug is related to
            relations = item.get('relations', [])
            for relation in relations:
                if 'workItems' in relation.get('url', ''):
                    related_id = relation.get('url', '').split('/')[-1]
                    if related_id in story_ids:
                        if related_id not in story_bug_mapping:
                            story_bug_mapping[related_id] = []
                        story_bug_mapping[related_id].append(item_id)
    
    # Ensure all story IDs are represented
    for story_id in story_ids:
        if story_id not in story_bug_mapping:
            story_bug_mapping[story_id] = []
    
    return story_bug_mapping


def create_intelligent_filter_function(user_query: str, context: str = ""):
    """
    Factory function that creates a specialized filter function based on user query.
    This is the main entry point for intelligent filtering.
    
    Usage in agent:
    ```python
    filter_func = create_intelligent_filter_function(user_query)
    filtered_result = filter_func(raw_ado_data)
    ```
    """
    intent = analyze_query_intent(user_query, context)
    
    def intelligent_filter(work_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        return filter_work_items_by_intent(work_items, intent)
    
    return intelligent_filter


# Test function to validate filtering
def test_filtering():
    """Test the filtering functions with sample data"""
    sample_work_items = [
        {
            'id': 12345,
            'fields': {
                'System.Title': 'Fix login bug',
                'System.WorkItemType': 'Bug',
                'System.State': 'Active',
                'System.AssignedTo': {'displayName': 'John Doe'},
                'System.CreatedDate': '2024-01-15T10:00:00Z'
            },
            'relations': []
        },
        {
            'id': 12346,
            'fields': {
                'System.Title': 'User login feature',
                'System.WorkItemType': 'User Story',
                'System.State': 'Closed',
                'System.AssignedTo': {'displayName': 'Jane Smith'},
                'System.CreatedDate': '2024-01-10T09:00:00Z'
            },
            'relations': []
        }
    ]
    
    # Test count query
    filter_func = create_intelligent_filter_function("How many bugs are there?")
    result = filter_func(sample_work_items)
    print("Count Query Result:", json.dumps(result, indent=2))
    
    # Test list query  
    filter_func = create_intelligent_filter_function("List all active work items")
    result = filter_func(sample_work_items)
    print("List Query Result:", json.dumps(result, indent=2))


if __name__ == "__main__":
    test_filtering()