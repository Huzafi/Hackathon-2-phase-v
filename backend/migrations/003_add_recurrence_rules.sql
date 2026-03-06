-- Migration: 003_add_recurrence_rules
-- Date: 2026-02-23
-- Description: Add recurrence rules for recurring tasks (User Story 2)
-- Phase: Phase 4 (User Story 2)

-- ============================================
-- Create Recurrence Rules table
-- ============================================

CREATE TABLE recurrence_rules (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL UNIQUE REFERENCES todos(id) ON DELETE CASCADE,
    pattern VARCHAR(20) NOT NULL,
    interval INTEGER NOT NULL DEFAULT 1,
    start_date DATE NOT NULL,
    end_date DATE NULL,
    by_weekday VARCHAR(50) NULL,
    by_monthday INTEGER NULL,
    last_generated TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_recurrence_pattern CHECK (pattern IN ('daily', 'weekly', 'monthly', 'yearly')),
    CONSTRAINT chk_recurrence_interval CHECK (interval >= 1),
    CONSTRAINT chk_recurrence_end_date CHECK (end_date IS NULL OR end_date > start_date),
    CONSTRAINT chk_recurrence_by_monthday CHECK (by_monthday IS NULL OR (by_monthday >= 1 AND by_monthday <= 31))
);

-- Create indexes
CREATE INDEX idx_recurrence_rules_task_id ON recurrence_rules(task_id);
CREATE INDEX idx_recurrence_rules_pattern ON recurrence_rules(pattern);
CREATE INDEX idx_recurrence_rules_last_generated ON recurrence_rules(last_generated);

-- Add comments
COMMENT ON TABLE recurrence_rules IS 'Recurrence rules for recurring tasks';
COMMENT ON COLUMN recurrence_rules.task_id IS 'Reference to todo.id (one-to-one relationship)';
COMMENT ON COLUMN recurrence_rules.pattern IS 'Recurrence pattern: daily, weekly, monthly, yearly';
COMMENT ON COLUMN recurrence_rules.interval IS 'Repeat every N periods (e.g., every 2 weeks)';
COMMENT ON COLUMN recurrence_rules.by_weekday IS 'Comma-separated weekdays for weekly pattern (MO,TU,WE,TH,FR,SA,SU)';
COMMENT ON COLUMN recurrence_rules.by_monthday IS 'Day of month for monthly pattern (1-31)';
COMMENT ON COLUMN recurrence_rules.last_generated IS 'When the last recurring instance was generated';

-- ============================================
-- Migration Rollback
-- ============================================
-- Run these commands in reverse order to rollback:
-- DROP TABLE IF EXISTS recurrence_rules CASCADE;
