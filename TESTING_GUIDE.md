# Testing Guide: Advanced Task Management Features

**Version**: 1.0.0  
**Date**: 2026-02-23  
**Features**: Due Dates/Priorities/Tags, Recurring Tasks, Reminders  
**Status**: Ready for E2E Testing

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Setup Instructions](#setup-instructions)
3. [Backend API Testing](#backend-api-testing)
4. [Frontend UI Testing](#frontend-ui-testing)
5. [Integration Testing](#integration-testing)
6. [QA Checklist](#qa-checklist)
7. [Known Issues & Limitations](#known-issues--limitations)
8. [Performance Testing](#performance-testing)

---

## Prerequisites

### Required Software
- Node.js 18+ and npm
- Python 3.11+
- Docker Desktop (for containerized testing)
- PostgreSQL client (psql)
- curl or Postman for API testing

### Test Accounts
Create at least 2 test users:
- User 1: `test1@example.com` / `Test1234!`
- User 2: `test2@example.com` / `Test1234!`

### Test Data
- Minimum 10 tasks per user
- Mix of priorities (high, medium, low)
- Mix of due dates (past, today, future)
- At least 5 tags per user
- At least 3 recurring tasks
- At least 5 reminders

---

## Setup Instructions

### 1. Start Development Environment

```bash
# Navigate to project root
cd /path/to/Hackathon-2/phase-V

# Start all services
docker-compose up -d

# Wait for services to be healthy
docker-compose ps
# All services should show "healthy" status

# Run database migrations
docker-compose exec backend python migrate.py
```

### 2. Verify Services

```bash
# Backend health check
curl http://localhost:8000/
# Expected: {"message":"Todo Backend API","status":"running",...}

# Frontend health check
curl http://localhost:3000/
# Expected: HTML response

# Database connection
docker-compose exec postgres pg_isready -U todouser -d tododb
# Expected: accepting connections
```

### 3. Create Test Data

```bash
# Sign up first user
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test1@example.com","password":"Test1234!"}'

# Sign in and save token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/signin \
  -H "Content-Type: application/json" \
  -d '{"email":"test1@example.com","password":"Test1234!"}' | jq -r '.access_token')

# Create test tasks
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/todos \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"title\": \"Test Task $i\",
      \"description\": \"Testing task number $i\",
      \"priority\": \"$([ $((i % 3)) -eq 0 ] && echo 'high' || ([ $((i % 3)) -eq 1 ] && echo 'medium' || echo 'low'))\",
      \"due_date\": \"2026-03-$((i % 28 + 1))T23:59:59Z\"
    }"
done
```

---

## Backend API Testing

### Feature 1: Due Dates, Priorities, Tags

#### Test Case 1.1: Create Task with Due Date and Priority
```bash
curl -X POST http://localhost:8000/api/todos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "High Priority Task",
    "description": "This is a high priority task",
    "priority": "high",
    "due_date": "2026-02-25T23:59:59Z"
  }'

# Expected: 201 Created with task data including priority and due_date
```

#### Test Case 1.2: Create Tag
```bash
curl -X POST http://localhost:8000/api/tags \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "urgent",
    "color": "#EF4444"
  }'

# Expected: 201 Created with tag data
```

#### Test Case 1.3: Assign Tag to Task
```bash
# First get task ID from previous creation
TASK_ID=123
TAG_ID=1

curl -X PUT http://localhost:8000/api/todos/$TASK_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"Task with tag\",
    \"priority\": \"high\",
    \"tag_ids\": [$TAG_ID]
  }"

# Expected: 200 OK with task including tags array
```

#### Test Case 1.4: Filter Tasks by Priority
```bash
curl -X GET "http://localhost:8000/api/todos?priority=high" \
  -H "Authorization: Bearer $TOKEN"

# Expected: Array of only high priority tasks
```

#### Test Case 1.5: Filter Tasks by Tags
```bash
curl -X GET "http://localhost:8000/api/todos?tags=1" \
  -H "Authorization: Bearer $TOKEN"

# Expected: Array of tasks with tag ID 1
```

### Feature 2: Recurring Tasks

#### Test Case 2.1: Set Weekly Recurrence
```bash
TASK_ID=123

curl -X POST http://localhost:8000/api/tasks/$TASK_ID/recurrence \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "weekly",
    "interval": 1,
    "start_date": "2026-02-24",
    "by_weekday": "MO"
  }'

# Expected: 201 Created with recurrence rule
```

#### Test Case 2.2: Get Recurrence Rule
```bash
curl -X GET http://localhost:8000/api/tasks/$TASK_ID/recurrence \
  -H "Authorization: Bearer $TOKEN"

# Expected: Recurrence rule data
```

#### Test Case 2.3: Complete Recurring Task
```bash
# Mark task as complete
curl -X PATCH http://localhost:8000/api/todos/$TASK_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'

# Expected: Task marked complete
# Verify: New task instance created with next Monday's date

# List tasks to verify new instance
curl -X GET "http://localhost:8000/api/todos" \
  -H "Authorization: Bearer $TOKEN"
```

#### Test Case 2.4: Remove Recurrence
```bash
curl -X DELETE http://localhost:8000/api/tasks/$TASK_ID/recurrence \
  -H "Authorization: Bearer $TOKEN"

# Expected: 204 No Content
# Verify: Recurrence rule removed, task remains
```

### Feature 3: Reminders

#### Test Case 3.1: Create Reminder
```bash
TASK_ID=123
TRIGGER_TIME="2026-02-25T09:00:00Z"

curl -X POST http://localhost:8000/api/reminders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"task_id\": $TASK_ID,
    \"trigger_time\": \"$TRIGGER_TIME\"
  }"

# Expected: 201 Created with reminder data
```

#### Test Case 3.2: Create Reminder in Past (Should Fail)
```bash
PAST_TIME="2020-01-01T09:00:00Z"

curl -X POST http://localhost:8000/api/reminders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"task_id\": $TASK_ID,
    \"trigger_time\": \"$PAST_TIME\"
  }"

# Expected: 400 Bad Request with error message
```

#### Test Case 3.3: List Reminders for Task
```bash
curl -X GET "http://localhost:8000/api/reminders?task_id=$TASK_ID" \
  -H "Authorization: Bearer $TOKEN"

# Expected: Array of reminders for the task
```

#### Test Case 3.4: Delete Reminder
```bash
REMINDER_ID=1

curl -X DELETE http://localhost:8000/api/reminders/$REMINDER_ID \
  -H "Authorization: Bearer $TOKEN"

# Expected: 204 No Content
```

---

## Frontend UI Testing

### Manual Testing Checklist

#### Due Dates, Priorities, Tags
- [ ] Create task with due date
- [ ] Create task with priority (high/medium/low)
- [ ] Create new tag with custom color
- [ ] Assign tag to task
- [ ] View PriorityBadge on task card (correct color)
- [ ] View DueDateBadge on task card (correct status)
- [ ] View TagList on task card
- [ ] Filter tasks by priority
- [ ] Filter tasks by tag
- [ ] Edit task due date
- [ ] Edit task priority
- [ ] Remove tag from task

#### Recurring Tasks
- [ ] Open "Make Recurring" modal
- [ ] Set daily recurrence
- [ ] Set weekly recurrence (select weekdays)
- [ ] Set monthly recurrence (select day)
- [ ] Set end date for recurrence
- [ ] View recurrence summary on task
- [ ] Complete recurring task
- [ ] Verify next instance created
- [ ] Remove recurrence from task

#### Reminders
- [ ] Open "Add Reminder" modal
- [ ] Select date and time
- [ ] Use "In 1 hour" quick option
- [ ] Use "Tomorrow" quick option
- [ ] Set reminder for future time
- [ ] Try to set reminder in past (should fail)
- [ ] View reminder in task list
- [ ] Delete reminder
- [ ] Receive notification when reminder fires
- [ ] Click notification to navigate to task
- [ ] Notification auto-closes after 5 seconds

---

## Integration Testing

### Test Scenario 1: Complete Task Management Workflow

1. Create user account
2. Create 3 tags (Work, Personal, Urgent)
3. Create task with:
   - Title: "Complete quarterly report"
   - Due date: Next Friday
   - Priority: High
   - Tags: Work, Urgent
4. Set weekly recurrence (every Monday)
5. Add reminder for 1 hour before due date
6. Complete the task
7. Verify:
   - Next instance created
   - Reminder copied to new instance
   - Tags copied to new instance

### Test Scenario 2: Multi-User Isolation

1. User 1 creates task with tags
2. User 2 logs in
3. Verify User 2 cannot:
   - See User 1's tasks
   - See User 1's tags
   - Modify User 1's tasks
4. User 2 creates own tasks and tags
5. Verify no data leakage

### Test Scenario 3: Edge Cases

1. Create task due on Jan 31
2. Set monthly recurrence
3. Verify Feb instance created on Feb 28/29
4. Verify Mar instance created on Mar 31
5. Create task with 10 tags
6. Verify all tags display correctly
7. Set reminder for 1 minute in future
8. Verify notification fires on time

---

## QA Checklist

### Functional Testing
- [ ] All CRUD operations work for tasks
- [ ] All CRUD operations work for tags
- [ ] All CRUD operations work for recurrence rules
- [ ] All CRUD operations work for reminders
- [ ] Filtering works correctly (priority, status, tags, dates)
- [ ] Sorting works correctly (due date, priority, created date)
- [ ] Search works correctly (keyword in title/description)
- [ ] Recurring tasks generate next instance on completion
- [ ] Reminders fire at correct time
- [ ] Notifications display and auto-close

### UI/UX Testing
- [ ] PriorityBadge displays correct colors
- [ ] DueDateBadge displays correct status (overdue, today, tomorrow, etc.)
- [ ] TagList displays all tags with correct colors
- [ ] RecurrenceSettings modal is user-friendly
- [ ] ReminderSettings modal is user-friendly
- [ ] NotificationToast is visible and dismissible
- [ ] Forms validate input correctly
- [ ] Error messages are clear and helpful
- [ ] Loading states display during async operations
- [ ] Responsive design works on mobile/tablet/desktop

### Security Testing
- [ ] JWT authentication required for all protected endpoints
- [ ] Users cannot access other users' data
- [ ] SQL injection prevented (test with special characters)
- [ ] XSS prevented (test with script tags in task titles)
- [ ] CSRF protection enabled
- [ ] Rate limiting working (100 requests/minute)

### Performance Testing
- [ ] Task list loads in < 2 seconds with 100 tasks
- [ ] Filter operations complete in < 500ms
- [ ] Search operations complete in < 1 second
- [ ] Creating task completes in < 1 second
- [ ] Completing recurring task generates next instance in < 2 seconds

---

## Known Issues & Limitations

### Current Limitations

1. **Reminder Delivery**:
   - Dapr actor integration requires Dapr runtime running
   - In-app notifications require WebSocket/SSE implementation
   - Email/push notifications not implemented

2. **Recurring Tasks**:
   - Complex patterns not supported (e.g., "every 2nd Tuesday")
   - Timezone handling uses UTC only
   - No preview of future instances

3. **Search**:
   - Full-text search uses PostgreSQL LIKE (basic)
   - No fuzzy matching or typo tolerance
   - No search result highlighting

4. **Performance**:
   - No pagination on task list (loads all tasks)
   - No caching for frequently accessed data
   - No lazy loading for task details

### Workarounds

1. **For reminder testing**: Manually trigger reminder delivery via API
2. **For timezone**: Store all dates in UTC, convert in frontend
3. **For search**: Use specific keywords for better results

---

## Performance Testing

### Load Testing with k6

Install k6: https://k6.io/docs/getting-started/installation/

Create load test script (`load-test.js`):

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 10,
  duration: '30s',
};

const BASE_URL = 'http://localhost:8000';
const TOKEN = 'YOUR_JWT_TOKEN_HERE';

const headers = {
  'Authorization': `Bearer ${TOKEN}`,
  'Content-Type': 'application/json',
};

export default function () {
  // List tasks
  let res = http.get(`${BASE_URL}/api/todos`, { headers });
  check(res, { 'list tasks: status 200': (r) => r.status === 200 });
  
  sleep(1);
  
  // Filter by priority
  res = http.get(`${BASE_URL}/api/todos?priority=high`, { headers });
  check(res, { 'filter tasks: status 200': (r) => r.status === 200 });
  
  sleep(1);
  
  // Search tasks
  res = http.get(`${BASE_URL}/api/todos?q=test`, { headers });
  check(res, { 'search tasks: status 200': (r) => r.status === 200 });
  
  sleep(1);
}
```

Run load test:
```bash
k6 run load-test.js
```

Expected Results:
- All requests complete with status 200
- p95 response time < 500ms
- No errors

---

## Bug Reporting Template

```markdown
### Bug Report

**Title**: [Brief description]

**Severity**: Critical / High / Medium / Low

**Feature**: Due Dates / Priorities / Tags / Recurring / Reminders

**Steps to Reproduce**:
1. 
2. 
3. 

**Expected Behavior**:


**Actual Behavior**:


**Environment**:
- Browser: [Chrome/Firefox/Safari/Edge]
- OS: [Windows/Mac/Linux]
- Frontend Version: [commit hash]
- Backend Version: [commit hash]

**Screenshots/Logs**:
[Attach if applicable]

**Additional Context**:

```

---

## Test Completion Criteria

All testing is complete when:
- [ ] All API test cases pass
- [ ] All UI test cases pass
- [ ] All integration scenarios pass
- [ ] All QA checklist items pass
- [ ] Performance tests meet targets
- [ ] No critical or high severity bugs open
- [ ] Documentation updated with known issues

---

**Testing Status**: Ready to Begin  
**Last Updated**: 2026-02-23  
**Test Lead**: [Your Name]
