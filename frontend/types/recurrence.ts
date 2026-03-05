/**
 * Recurrence types for recurring tasks
 */

/**
 * Recurrence pattern types
 */
export type RecurrencePattern = 'daily' | 'weekly' | 'monthly' | 'yearly';

/**
 * Recurrence settings for creating/updating recurrence rules
 */
export interface RecurrenceSettings {
  pattern: RecurrencePattern;
  interval?: number;
  start_date: string;
  end_date?: string;
  by_weekday?: string;
  by_monthday?: number;
}

/**
 * Recurrence rule response from API
 */
export interface RecurrenceRule {
  id: number;
  task_id: number;
  pattern: RecurrencePattern;
  interval: number;
  start_date: string;
  end_date?: string;
  by_weekday?: string;
  by_monthday?: number;
  last_generated?: string;
  created_at: string;
  is_active: boolean;
}

/**
 * Type guard for RecurrenceRule
 */
export function isRecurrenceRule(obj: any): obj is RecurrenceRule {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    typeof obj.id === 'number' &&
    typeof obj.task_id === 'number' &&
    typeof obj.pattern === 'string' &&
    typeof obj.interval === 'number' &&
    typeof obj.start_date === 'string' &&
    typeof obj.is_active === 'boolean'
  );
}
