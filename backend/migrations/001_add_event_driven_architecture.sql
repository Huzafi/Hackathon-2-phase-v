-- Migration: 001_add_event_driven_architecture
-- Date: 2026-02-23
-- Description: Add event-driven architecture tables (EventLog) and Kafka/Dapr support
-- Phase: Phase 2 (Foundational)

-- Create EventLog table for event sourcing and audit trail
CREATE TABLE event_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    processed BOOLEAN NOT NULL DEFAULT FALSE,
    correlation_id VARCHAR(36),
    metadata JSONB,
    
    -- Indexes for efficient querying
    CONSTRAINT chk_event_type CHECK (event_type IN (
        'task.created', 'task.updated', 'task.completed', 'task.deleted',
        'tag.created', 'tag.updated', 'tag.deleted',
        'reminder.set', 'reminder.delivered', 'reminder.deleted',
        'recurrence.set', 'recurrence.removed', 'recurrence.generated',
        'search.performed'
    ))
);

-- Create indexes for EventLog
CREATE INDEX idx_event_log_user_id ON event_log(user_id);
CREATE INDEX idx_event_log_event_type ON event_log(event_type);
CREATE INDEX idx_event_log_timestamp ON event_log(timestamp);
CREATE INDEX idx_event_log_correlation ON event_log(correlation_id);
CREATE INDEX idx_event_log_processed ON event_log(processed, timestamp);

-- Add comment
COMMENT ON TABLE event_log IS 'Event log for audit trail and event sourcing. Append-only.';
COMMENT ON COLUMN event_log.event_type IS 'Type of event (task.*, tag.*, reminder.*, recurrence.*, search.*)';
COMMENT ON COLUMN event_log.payload IS 'Event data as JSON';
COMMENT ON COLUMN event_log.correlation_id IS 'Distributed tracing correlation ID';

-- Migration rollback
-- DROP TABLE IF EXISTS event_log CASCADE;
