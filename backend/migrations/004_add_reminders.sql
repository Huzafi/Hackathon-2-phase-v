-- Migration: 004_add_reminders
-- Date: 2026-02-23
-- Description: Add reminders for task notifications (User Story 3)
-- Phase: Phase 5 (User Story 3)

-- ============================================
-- Create Reminders table
-- ============================================

CREATE TABLE reminders (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES todos(id) ON DELETE CASCADE,
    trigger_time TIMESTAMP NOT NULL,
    delivered BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_reminders_task_id ON reminders(task_id);
CREATE INDEX idx_reminders_trigger_time ON reminders(trigger_time);
CREATE INDEX idx_reminders_delivered ON reminders(delivered);
CREATE INDEX idx_reminders_pending ON reminders(trigger_time, delivered);

-- Add comments
COMMENT ON TABLE reminders IS 'Reminders for task notifications';
COMMENT ON COLUMN reminders.task_id IS 'Reference to todo.id';
COMMENT ON COLUMN reminders.trigger_time IS 'When to trigger the reminder (UTC)';
COMMENT ON COLUMN reminders.delivered IS 'Whether the reminder has been delivered';

-- ============================================
-- Migration Rollback
-- ============================================
-- Run these commands in reverse order to rollback:
-- DROP TABLE IF EXISTS reminders CASCADE;
