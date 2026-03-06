-- Migration: 005_add_full_text_search
-- Date: 2026-02-23
-- Description: Add full-text search capabilities for tasks (User Story 4)
-- Phase: Phase 6 (User Story 4 - Search and Filter)

-- ============================================
-- Add Full-Text Search Index for Tasks
-- ============================================

-- Create GIN index for full-text search on title and description
-- This enables efficient text search across task titles and descriptions
CREATE INDEX IF NOT EXISTS idx_tasks_full_text_search 
ON todos 
USING GIN (to_tsvector('english', title || ' ' || COALESCE(description, '')));

-- Create index for improved filtering performance
CREATE INDEX IF NOT EXISTS idx_tasks_user_status 
ON todos (user_id, is_completed);

-- Add comment
COMMENT ON INDEX idx_tasks_full_text_search IS 'Full-text search index for task title and description';

-- ============================================
-- Create Search Statistics View (Optional)
-- ============================================

-- View to analyze search performance and popular searches
-- This would be populated by application-level logging
CREATE OR REPLACE VIEW search_analytics AS
SELECT 
    'tasks' as search_type,
    COUNT(*) as search_count,
    AVG(EXECUTION_TIME) as avg_execution_time
FROM (
    -- This would be populated by application logging
    SELECT 1 as EXECUTION_TIME WHERE FALSE
) searches
GROUP BY search_type;

-- ============================================
-- Migration Rollback
-- ============================================
-- Run these commands in reverse order to rollback:
-- DROP VIEW IF EXISTS search_analytics;
-- DROP INDEX IF EXISTS idx_tasks_full_text_search;
-- DROP INDEX IF EXISTS idx_tasks_user_status;
