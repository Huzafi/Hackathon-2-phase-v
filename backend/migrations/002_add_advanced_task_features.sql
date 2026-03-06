-- Migration: 002_add_advanced_task_features
-- Date: 2026-02-23
-- Description: Add due dates, priorities, tags, and task-tag relationships (User Story 1)
-- Phase: Phase 3 (User Story 1)

-- ============================================
-- Part 1: Extend Task (todo) table
-- ============================================

-- Add due_date and priority columns to todos table
ALTER TABLE todos
    ADD COLUMN due_date TIMESTAMP NULL,
    ADD COLUMN priority VARCHAR(20) NOT NULL DEFAULT 'medium';

-- Add check constraint for priority values
ALTER TABLE todos
    ADD CONSTRAINT chk_priority CHECK (priority IN ('high', 'medium', 'low'));

-- Create indexes for new columns
CREATE INDEX idx_todos_due_date ON todos(due_date);
CREATE INDEX idx_todos_priority ON todos(priority);

-- Add comments
COMMENT ON COLUMN todos.due_date IS 'Due date and time (UTC). NULL means no due date.';
COMMENT ON COLUMN todos.priority IS 'Priority level: high, medium, low';

-- ============================================
-- Part 2: Create Tag table
-- ============================================

CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    color VARCHAR(7) NOT NULL DEFAULT '#3B82F6',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_tag_name_format CHECK (name ~ '^[a-zA-Z0-9\s\-]+$'),
    CONSTRAINT chk_tag_color_format CHECK (color ~ '^#[0-9A-Fa-f]{6}$')
);

-- Create unique index for case-insensitive name uniqueness per user
CREATE UNIQUE INDEX idx_tags_user_name ON tags(user_id, LOWER(name));
CREATE INDEX idx_tags_user_id ON tags(user_id);

-- Add comments
COMMENT ON TABLE tags IS 'User-defined tags for categorizing tasks';
COMMENT ON COLUMN tags.name IS 'Tag name (unique per user, case-insensitive)';
COMMENT ON COLUMN tags.color IS 'Hex color code for display (e.g., #3B82F6)';

-- ============================================
-- Part 3: Create TaskTag junction table
-- ============================================

CREATE TABLE task_tags (
    task_id INTEGER NOT NULL REFERENCES todos(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Composite primary key prevents duplicate associations
    PRIMARY KEY (task_id, tag_id)
);

-- Create indexes for efficient querying
CREATE INDEX idx_task_tags_task_id ON task_tags(task_id);
CREATE INDEX idx_task_tags_tag_id ON task_tags(tag_id);

-- Add comments
COMMENT ON TABLE task_tags IS 'Junction table for many-to-many task-tag relationship';
COMMENT ON COLUMN task_tags.task_id IS 'Reference to todo.id';
COMMENT ON COLUMN task_tags.tag_id IS 'Reference to tags.id';

-- ============================================
-- Part 4: Seed default data (optional)
-- ============================================

-- Optional: Insert some default tags for testing
-- Uncomment if needed
-- INSERT INTO tags (user_id, name, color) VALUES
--     (1, 'work', '#3B82F6'),
--     (1, 'personal', '#10B981'),
--     (1, 'urgent', '#EF4444');

-- ============================================
-- Migration Rollback
-- ============================================
-- Run these commands in reverse order to rollback:
-- DROP TABLE IF EXISTS task_tags CASCADE;
-- DROP TABLE IF EXISTS tags CASCADE;
-- ALTER TABLE todos DROP COLUMN IF EXISTS due_date;
-- ALTER TABLE todos DROP COLUMN IF EXISTS priority;
-- DROP INDEX IF EXISTS idx_todos_due_date;
-- DROP INDEX IF EXISTS idx_todos_priority;
