# Consolidated Responses API - UI Specification

## Overview

This document provides complete specifications for building a user interface for the Consolidated Responses API. The API allows users to retrieve and filter user submissions from the system with optional date range filtering.

## API Endpoint Details

- **URL**: `POST /consolidated-responses`
- **Base URL**: `http://localhost:8000` (or your server URL)
- **Content-Type**: `application/json`
- **Method**: POST

## Request Schema

### Request Model
```typescript
interface ConsolidatedResponsesRequest {
  start_date?: string;  // Optional: ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
  end_date?: string;    // Optional: ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
}
```

### Request Examples

#### 1. Get All Submissions (No Filters)
```json
{}
```

#### 2. Get Submissions from Specific Date
```json
{
  "start_date": "2025-09-20T00:00:00Z"
}
```

#### 3. Get Submissions for Date Range
```json
{
  "start_date": "2025-09-20T00:00:00Z",
  "end_date": "2025-09-20T23:59:59Z"
}
```

#### 4. Get Submissions Until Specific Date
```json
{
  "end_date": "2025-09-20T23:59:59Z"
}
```

## Response Schema

### Success Response Model
```typescript
interface ConsolidatedResponsesResponse {
  status: string;                    // "success"
  message: string;                   // Human-readable message
  query_metadata: QueryMetadata;     // Query execution details
  submissions: Submission[];         // Array of user submissions
  total_count: number;              // Total number of submissions returned
}

interface QueryMetadata {
  query_timestamp: string;          // When query was executed (ISO 8601)
  start_date_filter?: string;       // Applied start date filter
  end_date_filter?: string;         // Applied end date filter
  directory_exists: boolean;        // Whether user_responses directory exists
  total_files_found: number;        // Total JSON files found
  files_processed: number;          // Files successfully processed
  files_skipped: number;           // Files skipped (filters/errors)
  processing_time_ms: number;      // Processing time in milliseconds
}

interface Submission {
  timestamp: string;                // Submission timestamp (ISO 8601)
  original_input: string;           // Original user input text
  remarks?: string;                 // Optional user remarks
  selected_defect: SelectedDefect;  // Selected defect information
  selected_pairs: SelectedPair[];   // Root cause/corrective action pairs
  analysis_metadata: AnalysisMetadata; // Analysis execution metadata
  submission_metadata: SubmissionMetadata; // Submission tracking data
}

interface SelectedDefect {
  defect_code: string;             // Defect classification code
  defect_text: string;             // Human-readable defect description
  confidence_score: number;        // AI confidence (0.0 to 1.0)
  mapping_status: string;          // Mapping quality indicator
  curator_action: string;          // Required curator action
}

interface SelectedPair {
  root_cause: RootCause;           // Root cause information
  corrective_action: CorrectiveAction; // Corrective action information
  pair_id: string;                 // Unique pair identifier
}

interface RootCause {
  root_cause_code: string;         // Root cause classification code
  root_cause_text: string;         // Human-readable description
  is_primary: boolean;             // Whether this is primary root cause
}

interface CorrectiveAction {
  action_code: string;             // Action classification code
  action_text: string;             // Human-readable description
  is_primary: boolean;             // Whether this is primary action
}

interface AnalysisMetadata {
  agent_name: string;              // AI agent that performed analysis
  config_path: string;             // Configuration file used
  submission_source: string;       // Source system/page
  total_pairs_selected: number;    // Number of pairs selected
}

interface SubmissionMetadata {
  submission_id: string;           // Unique submission identifier
  submission_timestamp: string;    // When submission was saved (ISO 8601)
  filename: string;               // JSON filename
}
```

### Error Response Model
```typescript
interface ErrorResponse {
  detail: {
    status: string;                 // "error"
    error_code: string;            // Error classification
    message: string;               // Human-readable error message
    timestamp: string;             // Error timestamp (ISO 8601)
  }
}
```

## Response Examples

### Success Response Example
```json
{
  "status": "success",
  "message": "Successfully retrieved 5 submissions",
  "query_metadata": {
    "query_timestamp": "2025-09-20T10:30:45.123Z",
    "start_date_filter": "2025-09-20T00:00:00Z",
    "end_date_filter": "2025-09-20T23:59:59Z",
    "directory_exists": true,
    "total_files_found": 41,
    "files_processed": 5,
    "files_skipped": 36,
    "processing_time_ms": 45
  },
  "submissions": [
    {
      "timestamp": "2025-09-20T08:07:31.595Z",
      "original_input": "मोल्ड अन इवन कूलिंग प्रॉब्लम.",
      "remarks": "",
      "selected_defect": {
        "defect_code": "PLG.CLB.COOLANT.CONTAM",
        "defect_text": "Coolant contamination",
        "confidence_score": 0.75,
        "mapping_status": "NEAR_MATCH:PLG.CLB.COOLANT.CONTAM",
        "curator_action": "REVIEW_REQUIRED"
      },
      "selected_pairs": [
        {
          "root_cause": {
            "root_cause_code": "RC.CONTAM.DEBRIS",
            "root_cause_text": "Debris contamination causing abrasion",
            "is_primary": true
          },
          "corrective_action": {
            "action_code": "CA.COOLANT.FLUSH",
            "action_text": "Flush and replace coolant",
            "is_primary": true
          },
          "pair_id": "primary"
        }
      ],
      "analysis_metadata": {
        "agent_name": "jk_pilger_agent_v8",
        "config_path": "config/jk-gemba.yaml",
        "submission_source": "enhanced_defect_analysis_page",
        "total_pairs_selected": 1
      },
      "submission_metadata": {
        "submission_id": "submit_20250920080726",
        "submission_timestamp": "2025-09-20T08:07:26.243Z",
        "filename": "submit_20250920080726.json"
      }
    }
  ],
  "total_count": 5
}
```

### Error Response Examples

#### Validation Error (400)
```json
{
  "detail": {
    "status": "error",
    "error_code": "VALIDATION_ERROR",
    "message": "Date must be in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)",
    "timestamp": "2025-09-20T10:30:45.123Z"
  }
}
```

#### Internal Server Error (500)
```json
{
  "detail": {
    "status": "error",
    "error_code": "INTERNAL_ERROR",
    "message": "Failed to process consolidated responses request",
    "timestamp": "2025-09-20T10:30:45.123Z"
  }
}
```

## UI Requirements

### 1. Date Filter Section
- **Start Date Input**: Optional datetime picker for start_date
- **End Date Input**: Optional datetime picker for end_date
- **Quick Filters**: Buttons for common ranges (Today, Last 7 days, Last 30 days, All)
- **Clear Filters**: Button to reset all filters
- **Search Button**: Trigger API call

### 2. Results Display Section
- **Summary Card**: Show total_count, processing_time_ms, files_processed
- **Submissions Table/List**: Display submissions with key information
- **Pagination**: Handle large result sets (if needed)
- **Export Options**: Download as JSON/CSV (optional)

### 3. Submission Details
Each submission should display:
- **Timestamp**: Formatted date/time
- **Original Input**: User's original text (truncated with expand option)
- **Defect Information**: Code, description, confidence score
- **Root Cause & Actions**: List of selected pairs
- **Remarks**: User comments (if any)
- **Metadata**: Agent info, processing details

### 4. Error Handling
- **Loading States**: Show spinner during API calls
- **Error Messages**: Display user-friendly error messages
- **Validation**: Client-side date format validation
- **Retry Options**: Allow users to retry failed requests

### 5. Responsive Design
- **Mobile-friendly**: Works on tablets and phones
- **Desktop optimized**: Full feature set on desktop
- **Accessibility**: WCAG compliant

## Sample UI Flow

1. **Page Load**: Show empty form with date filters
2. **User Input**: User selects date range or uses quick filters
3. **API Call**: Send POST request with filters
4. **Loading**: Show loading indicator
5. **Results**: Display submissions in organized layout
6. **Details**: Allow expanding individual submissions
7. **Actions**: Provide export/filter/search capabilities

## Technical Notes

- **Date Format**: Always use ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
- **Timezone**: All dates are in UTC
- **Sorting**: Results are pre-sorted by timestamp (newest first)
- **Performance**: Large datasets may take time to load
- **Caching**: Consider caching results for better UX

## UI Component Suggestions

### Filter Panel Component
```jsx
<FilterPanel>
  <DateRangePicker
    startDate={startDate}
    endDate={endDate}
    onChange={handleDateChange}
  />
  <QuickFilters>
    <Button onClick={() => setToday()}>Today</Button>
    <Button onClick={() => setLast7Days()}>Last 7 Days</Button>
    <Button onClick={() => setLast30Days()}>Last 30 Days</Button>
    <Button onClick={() => clearFilters()}>All Time</Button>
  </QuickFilters>
  <SearchButton onClick={handleSearch} loading={isLoading}>
    Search Submissions
  </SearchButton>
</FilterPanel>
```

### Results Summary Component
```jsx
<ResultsSummary>
  <StatCard title="Total Submissions" value={totalCount} />
  <StatCard title="Processing Time" value={`${processingTime}ms`} />
  <StatCard title="Files Processed" value={filesProcessed} />
  <StatCard title="Date Range" value={dateRangeText} />
</ResultsSummary>
```

### Submission Card Component
```jsx
<SubmissionCard>
  <Header>
    <Timestamp>{formatDate(submission.timestamp)}</Timestamp>
    <ConfidenceScore score={submission.selected_defect.confidence_score} />
  </Header>
  <Content>
    <OriginalInput>{truncate(submission.original_input, 100)}</OriginalInput>
    <DefectInfo>
      <Code>{submission.selected_defect.defect_code}</Code>
      <Description>{submission.selected_defect.defect_text}</Description>
    </DefectInfo>
    <ActionPairs>
      {submission.selected_pairs.map(pair => (
        <PairItem key={pair.pair_id}>
          <RootCause>{pair.root_cause.root_cause_text}</RootCause>
          <CorrectiveAction>{pair.corrective_action.action_text}</CorrectiveAction>
        </PairItem>
      ))}
    </ActionPairs>
  </Content>
  <Footer>
    <ExpandButton onClick={() => toggleExpanded()}>
      {expanded ? 'Show Less' : 'Show More'}
    </ExpandButton>
    <Remarks>{submission.remarks}</Remarks>
  </Footer>
</SubmissionCard>
```

## Color Coding Suggestions

- **Confidence Scores**:
  - High (0.8-1.0): Green
  - Medium (0.5-0.79): Yellow/Orange
  - Low (0.0-0.49): Red
- **Curator Actions**:
  - AUTO_ACCEPT: Green
  - REVIEW_REQUIRED: Orange
  - HUMAN_DECISION: Red
- **Status Indicators**:
  - Success: Green
  - Warning: Orange
  - Error: Red

## Testing Endpoints

Before building UI, test these scenarios:
1. Empty request `{}`
2. Start date only `{"start_date": "2025-09-20T00:00:00Z"}`
3. Date range `{"start_date": "2025-09-20T00:00:00Z", "end_date": "2025-09-20T23:59:59Z"}`
4. Invalid date `{"start_date": "invalid"}`
5. Invalid range `{"start_date": "2025-09-21T00:00:00Z", "end_date": "2025-09-20T00:00:00Z"}`

## API Integration Code Examples

### JavaScript/TypeScript Fetch Example
```typescript
async function fetchConsolidatedResponses(filters: ConsolidatedResponsesRequest) {
  try {
    const response = await fetch('/consolidated-responses', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(filters),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data: ConsolidatedResponsesResponse = await response.json();
    return data;
  } catch (error) {
    console.error('API call failed:', error);
    throw error;
  }
}
```

### React Hook Example
```typescript
function useConsolidatedResponses() {
  const [data, setData] = useState<ConsolidatedResponsesResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async (filters: ConsolidatedResponsesRequest) => {
    setLoading(true);
    setError(null);

    try {
      const result = await fetchConsolidatedResponses(filters);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, error, fetchData };
}
```
