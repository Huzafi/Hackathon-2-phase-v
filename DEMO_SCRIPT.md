# Demo Script: Advanced Task Management Features

**Version**: 1.0.0  
**Date**: 2026-02-23  
**Duration**: 15-20 minutes  
**Audience**: Stakeholders, Users, Development Team

---

## Demo Overview

This demo showcases three major features:
1. **Due Dates, Priorities, and Tags** - Enhanced task organization
2. **Recurring Tasks** - Automatic task generation
3. **Reminders** - In-app notifications

---

## Pre-Demo Setup (5 minutes before)

### 1. Start Services

```bash
cd /path/to/Hackathon-2/phase-V
docker-compose up -d

# Verify all services are running
docker-compose ps
# All should show "healthy" status
```

### 2. Open Browser Tabs

1. **Frontend**: http://localhost:3000
2. **Backend API Docs**: http://localhost:8000/docs
3. **This Script**: Keep open for reference

### 3. Create Demo Account

- Email: `demo@example.com`
- Password: `Demo1234!`

### 4. Pre-populate Some Data (Optional)

Create 2-3 sample tasks with different priorities and due dates.

---

## Demo Flow (15-20 minutes)

### Introduction (1 minute)

**Script**:
> "Today I'll demonstrate our advanced task management features that help users better organize and track their tasks. We've implemented three major capabilities: enhanced task organization with due dates, priorities, and tags; recurring tasks for routine activities; and reminders to ensure you never miss a deadline."

---

### Feature 1: Due Dates, Priorities, and Tags (5 minutes)

#### 1.1 Create Task with All Attributes

**Actions**:
1. Click "Create Task" button
2. Fill in:
   - Title: "Complete quarterly report"
   - Description: "Finish Q1 financial analysis and send to management"
   - Due Date: Select next Friday
   - Priority: Select "High" (shows red)
   - Tags: Click "work" and "urgent" tags
3. Click "Save"

**Script**:
> "Let's create a task with all the new attributes. You can set a due date, choose a priority level—high, medium, or low—and assign multiple tags for categorization. Notice how high priority is highlighted in red for quick visual identification."

**Expected Result**:
- Task created and appears in list
- PriorityBadge shows "High" in red
- DueDateBadge shows due date
- TagList shows assigned tags

#### 1.2 Visual Indicators

**Actions**:
1. Point to different tasks in the list
2. Highlight:
   - Red border on overdue tasks
   - Priority colors (red/amber/green)
   - Due date badges (overdue, today, tomorrow, future)
   - Tag colors

**Script**:
> "Each task displays visual indicators at a glance. Overdue tasks have a red border. Priority is color-coded: red for high, amber for medium, green for low. Due dates show whether a task is due today, tomorrow, or later. And tags use custom colors you define."

#### 1.3 Filter by Priority and Tags

**Actions**:
1. Click filter dropdown
2. Select "High Priority"
3. Show only high priority tasks
4. Add tag filter "urgent"
5. Show tasks that are both high priority AND urgent

**Script**:
> "You can filter tasks by priority to focus on what's most important. Combine filters to narrow down further—for example, show only high-priority tasks tagged as urgent."

**Expected Result**:
- Filtered list shows only matching tasks
- Filter combination uses AND logic

---

### Feature 2: Recurring Tasks (5 minutes)

#### 2.1 Set Weekly Recurrence

**Actions**:
1. Click on a task or create new one: "Team standup meeting"
2. Click "Make Recurring" button
3. Select:
   - Pattern: Weekly
   - Interval: 1 (every week)
   - Weekdays: Select Mon, Wed, Fri
   - Start Date: Today
4. Click "Save"

**Script**:
> "For routine tasks like team meetings, you can set up recurrence. Let's create a standup meeting that repeats every Monday, Wednesday, and Friday. When you complete one instance, the next one is automatically created."

**Expected Result**:
- Recurrence summary displayed on task
- Shows pattern, interval, and dates

#### 2.2 Complete Recurring Task

**Actions**:
1. Find the recurring task
2. Click checkbox to mark complete
3. Show new instance created
4. Point out next due date

**Script**:
> "Now watch what happens when I complete this recurring task. The system automatically creates the next instance with the same title, description, priority, and tags. You never have to manually recreate routine tasks."

**Expected Result**:
- Original task marked complete
- New task appears with next occurrence date
- All attributes copied (priority, tags, etc.)

#### 2.3 Monthly Recurrence with Edge Case

**Actions**:
1. Create task: "Pay rent"
2. Set recurrence:
   - Pattern: Monthly
   - Day: 31
3. Explain month-end handling

**Script**:
> "The system handles edge cases intelligently. If you set a monthly recurrence for the 31st, it automatically adjusts for months with fewer days—February 28th or 29th, April 30th, and so on."

---

### Feature 3: Reminders (5 minutes)

#### 3.1 Set Reminder

**Actions**:
1. Select a task with future due date
2. Click "Add Reminder" button
3. Select:
   - Date: Tomorrow
   - Time: 9:00 AM
4. Click "Set Reminder"

**Script**:
> "Never miss an important deadline with reminders. Set a reminder for any task, and you'll receive an in-app notification at the specified time. Let's set one for tomorrow morning at 9 AM."

**Expected Result**:
- Reminder appears in task's reminder list
- Shows trigger time and status (pending)

#### 3.2 Quick Options

**Actions**:
1. Click "Add Reminder" on another task
2. Click "In 1 hour" quick option
3. Show pre-filled date/time
4. Click "Set Reminder"

**Script**:
> "For convenience, there are quick options. 'In 1 hour' sets a reminder one hour from now. 'Tomorrow' sets it for the same time tomorrow. Perfect for quick reminders without manual date picking."

#### 3.3 Notification Display

**Actions**:
1. Trigger a reminder (or simulate with past time for demo)
2. Show notification toast appearing
3. Point out:
   - Amber color for reminders
   - Task title in notification
   - Auto-close after 5 seconds
4. Click notification to navigate to task

**Script**:
> "When a reminder fires, you'll see a notification like this. It's color-coded amber for reminders, shows the task title, and automatically closes after 5 seconds. Click it to jump directly to the task."

---

### Combined Workflow (3 minutes)

#### Complete Task Management Scenario

**Actions**:
1. Create task: "Submit expense report"
2. Set attributes:
   - Due date: End of month
   - Priority: High
   - Tags: "work", "finance"
3. Set recurrence: Monthly on last day
4. Add reminder: 1 day before due date
5. Complete the task
6. Show next instance created with reminder

**Script**:
> "Let's see all features working together. I'll create an expense report task that's due at month end, mark it high priority, tag it for work and finance, set it to recur monthly, and add a reminder one day before. When I complete it, the next month's instance is automatically created with the reminder already set."

**Expected Result**:
- Complete workflow demonstrates all three features
- Next instance has all attributes including reminder

---

### Q&A and Closing (1 minute)

**Script**:
> "To summarize, we've implemented:
> - **Due Dates, Priorities, and Tags** for better task organization
> - **Recurring Tasks** to automate routine task creation
> - **Reminders** to ensure you never miss a deadline
> 
> All three features work seamlessly together to help you stay on top of your tasks. Are there any questions?"

---

## Troubleshooting

### Issue: Services Not Starting

```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Restart services
docker-compose down
docker-compose up -d
```

### Issue: Database Not Migrated

```bash
# Run migrations
docker-compose exec backend python migrate.py

# Verify tables
docker-compose exec postgres psql -U todouser -d tododb -c "\dt"
```

### Issue: Frontend Not Connecting to Backend

```bash
# Check .env.local
cat frontend/.env.local
# Should have: NEXT_PUBLIC_API_URL=http://localhost:8000

# Restart frontend
docker-compose restart frontend
```

---

## Demo Success Criteria

- [ ] All services start without errors
- [ ] Can create task with due date, priority, and tags
- [ ] Visual indicators display correctly
- [ ] Filtering works for priority and tags
- [ ] Can set recurrence rule
- [ ] Completing recurring task creates next instance
- [ ] Can set reminder
- [ ] Notification displays and auto-closes
- [ ] Combined workflow completes successfully
- [ ] Demo completes within 20 minutes

---

## Post-Demo Actions

1. **Collect Feedback**:
   - What features are most valuable?
   - Any usability issues?
   - Additional features requested?

2. **Document Issues**:
   - Log any bugs encountered
   - Note performance issues
   - Record user suggestions

3. **Next Steps**:
   - Address critical bugs
   - Plan next feature set (Search/Filter)
   - Schedule production deployment

---

**Demo Status**: Ready  
**Last Rehearsed**: [Date]  
**Presenter**: [Your Name]
