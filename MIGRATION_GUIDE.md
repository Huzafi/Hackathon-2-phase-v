# Migration Guide: Upgrading to Advanced Task Management

**Version**: 1.0.0  
**Date**: 2026-02-23  
**From**: Basic Todo App  
**To**: Advanced Task Management (v2.0)

---

## Overview

This guide helps you migrate your existing tasks to the new advanced task management system with due dates, priorities, tags, recurring tasks, reminders, search, and sort features.

---

## What's New

### 1. Due Dates
- Set deadlines for tasks
- Visual indicators (overdue, due soon, today, future)
- Filter and sort by due date

### 2. Priorities
- Three levels: High, Medium, Low
- Color-coded badges (red/amber/green)
- Filter and sort by priority

### 3. Tags
- Custom tags with colors
- Multiple tags per task
- Tag-based filtering

### 4. Recurring Tasks
- Daily, weekly, monthly, yearly patterns
- Automatic next instance generation
- Custom intervals (every N days/weeks/months)

### 5. Reminders
- In-app notifications
- Custom trigger times
- Quick options (1 hour, tomorrow)

### 6. Search & Filter
- Full-text search
- Filter by priority, status, tags, dates
- Combined filters (AND logic)

### 7. Sort
- Sort by due date, priority, created date, title
- Ascending/descending order
- Persistent sort preferences

---

## Database Migration

### Automatic Migration

The database migration will run automatically on first startup:

```bash
# Run migrations
cd backend
python migrate.py
```

### What Gets Migrated

**Existing Tasks**:
- All existing tasks are preserved
- `due_date`: Set to NULL (no due date)
- `priority`: Set to 'medium' (default)
- `tags`: No tags assigned (you can add them later)

**New Tables Created**:
- `tags` - Tag definitions
- `task_tags` - Task-tag relationships
- `recurrence_rules` - Recurring task configurations
- `reminders` - Task reminders
- `event_log` - Event audit trail

### Manual Migration (Optional)

If you want to set default priorities for existing tasks:

```sql
-- Set high priority for overdue tasks (if you have due dates)
UPDATE todos SET priority = 'high' 
WHERE due_date < NOW() AND is_completed = false;

-- Set medium priority for all other tasks
UPDATE todos SET priority = 'medium' 
WHERE priority IS NULL;
```

---

## Updating Existing Tasks

### Via API

```bash
# Get your auth token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/signin \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"your-password"}' | jq -r '.access_token')

# Update task with due date and priority
curl -X PUT http://localhost:8000/api/todos/123 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Existing task",
    "due_date": "2026-03-01T23:59:59Z",
    "priority": "high"
  }'

# Create tags
curl -X POST http://localhost:8000/api/tags \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "urgent",
    "color": "#EF4444"
  }'

# Assign tag to task
curl -X PUT http://localhost:8000/api/todos/123 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Existing task",
    "tag_ids": [1]
  }'
```

### Via UI

1. **Open task** in the task panel
2. **Click Edit** (pencil icon)
3. **Add due date** using the date picker
4. **Select priority** (high/medium/low)
5. **Add tags** by clicking on tag buttons
6. **Save** changes

---

## Creating Tags

### Recommended Tag Structure

**Work Tags**:
- `work` (#3B82F6 - Blue)
- `meeting` (#8B5CF6 - Purple)
- `deadline` (#EF4444 - Red)

**Personal Tags**:
- `personal` (#10B981 - Green)
- `home` (#F59E0B - Amber)
- `health` (#EC4899 - Pink)

**Priority Tags**:
- `urgent` (#EF4444 - Red)
- `important` (#F59E0B - Amber)
- `optional` (#6B7280 - Gray)

### Bulk Tag Creation Script

```python
#!/usr/bin/env python3
"""Create default tags for all users."""

import requests

BASE_URL = 'http://localhost:8000'
EMAIL = 'you@example.com'
PASSWORD = 'your-password'

# Default tags
TAGS = [
    {'name': 'work', 'color': '#3B82F6'},
    {'name': 'personal', 'color': '#10B981'},
    {'name': 'urgent', 'color': '#EF4444'},
    {'name': 'important', 'color': '#F59E0B'},
    {'name': 'optional', 'color': '#6B7280'},
]

# Get auth token
response = requests.post(f'{BASE_URL}/api/auth/signin', json={
    'email': EMAIL,
    'password': PASSWORD
})
token = response.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Create tags
for tag in TAGS:
    response = requests.post(f'{BASE_URL}/api/tags', json=tag, headers=headers)
    if response.status_code == 201:
        print(f"✓ Created tag: {tag['name']}")
    else:
        print(f"✗ Failed to create tag: {tag['name']}")
```

---

## Setting Up Recurring Tasks

### Via UI

1. **Open or create task**
2. **Click "Make Recurring"** button
3. **Select pattern**:
   - Daily
   - Weekly (select weekdays)
   - Monthly (select day)
   - Yearly
4. **Set interval** (every N days/weeks/months)
5. **Optional**: Set end date
6. **Save**

### Via API

```bash
curl -X POST http://localhost:8000/api/tasks/123/recurrence \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "weekly",
    "interval": 1,
    "start_date": "2026-02-24",
    "by_weekday": "MO"
  }'
```

### Common Patterns

**Daily Standup**:
```json
{
  "pattern": "daily",
  "interval": 1,
  "start_date": "2026-02-24",
  "by_weekday": "MO,TU,WE,TH,FR"
}
```

**Bi-Weekly Sprint**:
```json
{
  "pattern": "weekly",
  "interval": 2,
  "start_date": "2026-02-24",
  "by_weekday": "MO"
}
```

**Monthly Report**:
```json
{
  "pattern": "monthly",
  "interval": 1,
  "start_date": "2026-02-24",
  "by_monthday": 1
}
```

---

## Setting Up Reminders

### Via UI

1. **Open or create task**
2. **Click "Add Reminder"** button
3. **Select date and time**
4. **Or use quick options**:
   - In 1 hour
   - Tomorrow
5. **Save**

### Via API

```bash
curl -X POST http://localhost:8000/api/reminders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": 123,
    "trigger_time": "2026-02-25T09:00:00Z"
  }'
```

---

## Using Search and Filter

### Search

**Via UI**:
- Type in search box
- Results update as you type
- Click suggestion to use it

**Via API**:
```bash
curl "http://localhost:8000/api/tasks/search?q=report" \
  -H "Authorization: Bearer $TOKEN"
```

### Filter

**Via UI**:
1. Click "Filters" button
2. Select priority, status, tags, date range
3. Results update automatically

**Via API**:
```bash
curl "http://localhost:8000/api/tasks?priority=high&status=overdue&tags=1,2" \
  -H "Authorization: Bearer $TOKEN"
```

### Sort

**Via UI**:
1. Click sort dropdown
2. Select field (due date, priority, etc.)
3. Click order toggle (asc/desc)

**Via API**:
```bash
curl "http://localhost:8000/api/tasks?sort_by=due_date&sort_order=asc" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Best Practices

### Task Organization

1. **Set due dates** for all time-sensitive tasks
2. **Use priorities** to indicate importance
3. **Add tags** for categorization
4. **Use recurring tasks** for routine activities
5. **Set reminders** for important deadlines

### Recommended Workflow

**Morning**:
1. Review tasks sorted by due date
2. Filter by high priority
3. Set reminders for critical tasks

**Evening**:
1. Review completed tasks
2. Plan next day's tasks
3. Set up recurring tasks for next day

**Weekly**:
1. Review overdue tasks
2. Clean up old tags
3. Plan recurring tasks for next week

---

## Troubleshooting

### Issues After Migration

**Tasks not showing due dates**:
```sql
-- Check if migration ran
SELECT COUNT(*) FROM todos WHERE due_date IS NOT NULL;

-- If 0, migration may not have run
-- Run: python migrate.py
```

**Priority not showing**:
```sql
-- Check priority values
SELECT priority, COUNT(*) FROM todos GROUP BY priority;

-- Update NULL priorities
UPDATE todos SET priority = 'medium' WHERE priority IS NULL;
```

### Common Questions

**Q: Will my existing tasks be deleted?**  
A: No, all existing tasks are preserved.

**Q: Can I undo the migration?**  
A: Yes, but it's not recommended. See rollback section below.

**Q: Do I need to restart the application?**  
A: Yes, restart after running migrations.

---

## Rollback (If Needed)

⚠️ **Warning**: Rollback will remove new features from database.

```sql
-- Remove new columns
ALTER TABLE todos DROP COLUMN IF EXISTS due_date;
ALTER TABLE todos DROP COLUMN IF EXISTS priority;

-- Remove new tables
DROP TABLE IF EXISTS reminders CASCADE;
DROP TABLE IF EXISTS recurrence_rules CASCADE;
DROP TABLE IF EXISTS task_tags CASCADE;
DROP TABLE IF EXISTS tags CASCADE;
DROP TABLE IF EXISTS event_log CASCADE;
```

---

## Next Steps

1. ✅ Run migration: `python migrate.py`
2. ✅ Create your first tags
3. ✅ Update existing tasks with due dates and priorities
4. ✅ Set up recurring tasks for routine activities
5. ✅ Set reminders for important deadlines
6. ✅ Try search and filter features
7. ✅ Experiment with sort options

---

**Need Help?**

- **Documentation**: See `IMPLEMENTATION_SUMMARY.md`
- **API Docs**: http://localhost:8000/docs
- **Issues**: https://github.com/Huzafi/Hackathon-2/issues

---

**Document Version**: 1.0.0  
**Last Updated**: 2026-02-23
