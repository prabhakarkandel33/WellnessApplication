# User Statistics API Guide

## Overview
The statistics endpoint provides comprehensive analytics about user activities with flexible date filtering and structured data optimized for frontend visualization.

## Endpoint

```
GET /api/statistics/
```

**Authentication Required:** Yes (Bearer Token)

## Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `period` | string | No (default: `30days`) | Predefined time period: `7days`, `30days`, `90days`, `all`, `custom` |
| `start_date` | datetime (ISO 8601) | Conditional* | Start date for custom period |
| `end_date` | datetime (ISO 8601) | Conditional* | End date for custom period |

\* Required when `period=custom`

## Example Requests

### Last 7 Days
```bash
GET /api/statistics/?period=7days
```

### Last 30 Days (Default)
```bash
GET /api/statistics/
# or explicitly
GET /api/statistics/?period=30days
```

### Last 90 Days
```bash
GET /api/statistics/?period=90days
```

### All Time
```bash
GET /api/statistics/?period=all
```

### Custom Date Range
```bash
GET /api/statistics/?period=custom&start_date=2026-01-01T00:00:00Z&end_date=2026-01-27T23:59:59Z
```

## Response Structure

```json
{
  "period": "30days",
  "start_date": "2025-12-28T12:00:00Z",
  "end_date": "2026-01-27T12:00:00Z",
  
  "overview": {
    "total_activities_completed": 45,
    "total_activities_assigned": 60,
    "completion_rate": 75.0,
    "total_duration_minutes": 1350,
    "total_duration_hours": 22.5
  },
  
  "activity_breakdown": {
    "exercise": 25,
    "meditation": 15,
    "journaling": 5,
    "duration_by_type": {
      "exercise": 750,
      "meditation": 450,
      "journaling": 150
    }
  },
  
  "daily_activity_count": [
    {
      "date": "2026-01-20",
      "count": 2,
      "exercise": 1,
      "meditation": 1,
      "journaling": 0
    },
    // ... more days
  ],
  
  "daily_duration": [
    {
      "date": "2026-01-20",
      "total_minutes": 45,
      "exercise_minutes": 30,
      "meditation_minutes": 15
    },
    // ... more days
  ],
  
  "motivation_trends": {
    "average_motivation_before": 2.8,
    "average_motivation_after": 3.9,
    "average_improvement": 1.1,
    "activities_with_improvement": 38,
    "improvement_rate": 84.4
  },
  
  "engagement": {
    "current_streak_days": 7,
    "total_sessions": 15,
    "avg_session_completion_rate": 82.5,
    "engagement_score": 0.75,
    "motivation_score": 4
  },
  
  "ratings": {
    "average_enjoyment": 4.2,
    "average_difficulty": 2.8,
    "highly_enjoyed_activities": 35,
    "well_balanced_activities": 30
  },
  
  "goal_progress": {
    "workout_goal_days_per_week": 5,
    "actual_days_per_week": 4.3,
    "goal_achievement_rate": 86.0,
    "total_workouts_lifetime": 120,
    "total_meditations_lifetime": 85
  },
  
  "recent_activities": [
    {
      "id": 123,
      "name": "Morning Yoga",
      "type": "exercise",
      "completed_date": "2026-01-27T08:30:00Z",
      "duration_minutes": 30,
      "motivation_delta": 2,
      "enjoyment_rating": 5
    },
    // ... up to 5 recent activities
  ]
}
```

## Field Descriptions

### Overview
- **total_activities_completed**: Number of activities completed in the period
- **total_activities_assigned**: Total activities assigned (completed + incomplete)
- **completion_rate**: Percentage of assigned activities that were completed
- **total_duration_minutes**: Total time spent on completed activities (minutes)
- **total_duration_hours**: Total time spent on completed activities (hours)

### Activity Breakdown
- **exercise/meditation/journaling**: Count of each activity type completed
- **duration_by_type**: Minutes spent on each activity type

### Daily Time Series
Arrays of daily data points for creating graphs:
- **daily_activity_count**: Daily counts by type
- **daily_duration**: Daily duration by type

### Motivation Trends
- **average_motivation_before**: Average motivation level before activities (1-5)
- **average_motivation_after**: Average motivation level after activities (1-5)
- **average_improvement**: Average change in motivation (positive = improvement)
- **activities_with_improvement**: Count where motivation increased
- **improvement_rate**: Percentage of activities that improved motivation

### Engagement
- **current_streak_days**: Consecutive days with at least one completed activity
- **total_sessions**: Number of workout sessions in period
- **avg_session_completion_rate**: Average % completion across sessions
- **engagement_score**: AI-calculated engagement score (0-1)
- **motivation_score**: User's current motivation level (1-5)

### Ratings
- **average_enjoyment**: Average enjoyment rating (1-5, 5=loved it)
- **average_difficulty**: Average difficulty rating (1-5, 3=well balanced)
- **highly_enjoyed_activities**: Count with enjoyment rating ≥4
- **well_balanced_activities**: Count with difficulty rating 2-3

### Goal Progress
- **workout_goal_days_per_week**: User's target days per week
- **actual_days_per_week**: Actual average days per week in period
- **goal_achievement_rate**: Percentage of goal achieved
- **total_workouts_lifetime**: All-time workout count
- **total_meditations_lifetime**: All-time meditation count

### Recent Activities
Last 5 completed activities with key metrics

## Frontend Implementation Examples

### React/JavaScript Example

```javascript
// Fetch statistics for last 7 days
const fetchStatistics = async (period = '7days') => {
  const token = localStorage.getItem('authToken');
  
  const response = await fetch(
    `https://api.example.com/api/statistics/?period=${period}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  const data = await response.json();
  return data;
};

// Custom date range
const fetchCustomStats = async (startDate, endDate) => {
  const token = localStorage.getItem('authToken');
  const params = new URLSearchParams({
    period: 'custom',
    start_date: startDate.toISOString(),
    end_date: endDate.toISOString()
  });
  
  const response = await fetch(
    `https://api.example.com/api/statistics/?${params}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  return response.json();
};
```

### Chart.js Example

```javascript
// Create a line chart for daily activity count
const createActivityChart = (dailyData) => {
  const ctx = document.getElementById('activityChart').getContext('2d');
  
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: dailyData.map(d => d.date),
      datasets: [
        {
          label: 'Exercise',
          data: dailyData.map(d => d.exercise),
          borderColor: 'rgb(255, 99, 132)',
          backgroundColor: 'rgba(255, 99, 132, 0.2)'
        },
        {
          label: 'Meditation',
          data: dailyData.map(d => d.meditation),
          borderColor: 'rgb(54, 162, 235)',
          backgroundColor: 'rgba(54, 162, 235, 0.2)'
        },
        {
          label: 'Journaling',
          data: dailyData.map(d => d.journaling),
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)'
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: 'Daily Activity Count'
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });
};

// Usage
fetchStatistics('30days').then(data => {
  createActivityChart(data.daily_activity_count);
});
```

### Pie Chart for Activity Breakdown

```javascript
const createBreakdownChart = (breakdown) => {
  const ctx = document.getElementById('breakdownChart').getContext('2d');
  
  new Chart(ctx, {
    type: 'pie',
    data: {
      labels: ['Exercise', 'Meditation', 'Journaling'],
      datasets: [{
        data: [
          breakdown.exercise,
          breakdown.meditation,
          breakdown.journaling
        ],
        backgroundColor: [
          'rgb(255, 99, 132)',
          'rgb(54, 162, 235)',
          'rgb(75, 192, 192)'
        ]
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: 'Activity Type Distribution'
        }
      }
    }
  });
};
```

## Error Responses

### 400 Bad Request
```json
{
  "period": ["Invalid choice. Must be one of: 7days, 30days, 90days, all, custom"],
  "start_date": ["This field is required for custom period"],
  "end_date": ["start_date must be before end_date"]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

## Testing with cURL

```bash
# Get token first
TOKEN=$(curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}' \
  | jq -r '.access')

# Fetch statistics
curl -X GET "http://localhost:8000/api/statistics/?period=7days" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

## Performance Considerations

- The endpoint aggregates data on-the-fly for accuracy
- For large datasets (>10,000 activities), consider adding caching
- Daily time series data grows with the date range (7 days = 7 data points)
- The endpoint performs ~15-20 database queries per request

## Recommendations

1. **Cache on Frontend**: Store statistics data for 5-10 minutes to reduce API calls
2. **Progressive Loading**: Load overview first, then detailed charts
3. **Default to 30 Days**: Most users care about recent trends
4. **Visualize Streaks**: Highlight current streak prominently in UI
5. **Goal Progress**: Show progress bars for goal achievement
6. **Motivation Trends**: Use line charts to show improvement over time
7. **Activity Heatmap**: Use daily_activity_count for calendar heatmap visualization

## Related Endpoints

- `POST /api/workout/activities/{id}/complete/` - Complete an activity
- `GET /api/workout/activities/` - List user activities
- `GET /api/workout/sessions/` - List workout sessions
