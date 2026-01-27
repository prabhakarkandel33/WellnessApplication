# Statistics Endpoint Authentication & Auto-Updates

## ✅ Authentication Security

### JWT Token Required
The `/api/statistics/` endpoint is **fully secured** with JWT authentication:

```python
permission_classes = [IsAuthenticated]
```

### How It Works:
1. User logs in and receives JWT access token
2. User includes token in request header:
   ```
   Authorization: Bearer <access_token>
   ```
3. Endpoint automatically filters data by `request.user`
4. **Users can ONLY see their own data** - no way to access other users' statistics

### Example Request:
```bash
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbG..." \
     http://localhost:8000/api/statistics/?period=7days
```

---

## ✅ Automatic Statistics Updates

### Signal-Based Auto-Updates
Statistics are **automatically updated** whenever:
- ✅ User completes an activity
- ✅ User updates an activity
- ✅ User deletes an activity
- ✅ Workout session is created/updated/deleted

### Implementation:
Created `api/signals.py` with Django signals:
- `post_save` for Activity model → updates stats on create/update
- `post_delete` for Activity model → updates stats on delete
- `post_save` for WorkoutSession model → updates stats
- `post_delete` for WorkoutSession model → updates stats

### What Gets Auto-Calculated:
1. **Total activities completed**
2. **Total duration** (minutes/hours)
3. **Average session length**
4. **Total calories burned**
5. **Average motivation level**
6. **Average performance rating**
7. **Current streak** (consecutive days)
8. **Longest streak** (best ever)
9. **Last activity date**
10. **Consistency rate** (% of days with activity in last 30 days)

### Signal Registration:
Signals are automatically loaded via `api/apps.py`:
```python
def ready(self):
    import api.signals  # Registers all signal handlers
```

---

## 📊 Statistics Endpoint Details

### URL
`GET /api/statistics/`

### Query Parameters

#### Time Period Filters:
- `?period=7days` - Last 7 days
- `?period=30days` - Last 30 days  
- `?period=90days` - Last 90 days
- `?period=all` - All time
- `?period=custom` - Custom date range (requires start_date & end_date)

#### Custom Date Range:
```
?period=custom&start_date=2026-01-01&end_date=2026-01-27
```

### Response Structure (Frontend-Friendly)

```json
{
  "overview": {
    "total_activities_completed": 45,
    "total_activities_assigned": 50,
    "completion_rate": 90.0,
    "total_duration_minutes": 1350,
    "total_duration_hours": 22.5
  },
  
  "activity_breakdown": {
    "exercise": 20,
    "meditation": 15,
    "journaling": 10
  },
  
  "timeline": [
    {
      "date": "2026-01-27",
      "activities_completed": 2,
      "total_duration": 60,
      "average_motivation": 4.5
    }
  ],
  
  "motivation_trends": {
    "average": 4.2,
    "by_activity_type": {
      "exercise": 4.5,
      "meditation": 4.0,
      "journaling": 4.1
    }
  },
  
  "performance_metrics": {
    "average_rating": 4.3,
    "activities_with_ratings": 40
  },
  
  "engagement": {
    "current_streak": 7,
    "longest_streak": 14,
    "consistency_rate": 85.5,
    "last_activity_date": "2026-01-27T10:30:00Z"
  },
  
  "period_info": {
    "start_date": "2026-01-20",
    "end_date": "2026-01-27",
    "days_in_period": 7
  }
}
```

### Perfect for Frontend Graphs:
- **Line charts**: `timeline` data (date vs activities/duration)
- **Bar charts**: `activity_breakdown` (activity type distribution)
- **Pie charts**: Activity type percentages
- **Progress bars**: Completion rate, consistency rate
- **Badges**: Streaks, total activities, calories burned

---

## 🔐 Security Summary

| Feature | Status |
|---------|--------|
| JWT Authentication | ✅ Required |
| User Data Isolation | ✅ Enforced |
| Token in Header | ✅ Required |
| Cross-User Access | ❌ Blocked |
| Auto-Updates | ✅ Signal-based |
| Real-time Stats | ✅ Live |

**Result**: Users can ONLY access their own activity history. All statistics auto-update when activities are completed. No manual updates needed.
