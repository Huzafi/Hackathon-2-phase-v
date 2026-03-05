/**
 * Task API functions
 */

import { api } from './client';
import { Task, Priority, Tag } from '@/types/entities';

/**
 * Recurrence pattern types
 */
export type RecurrencePattern = 'daily' | 'weekly' | 'monthly' | 'yearly';

/**
 * Recurrence settings
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
 * Recurrence rule response
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
 * Query parameters for listing tasks
 */
export interface TaskListParams {
  priority?: Priority;
  status?: 'completed' | 'incomplete' | 'overdue';
  tags?: number[];
  dueDateFrom?: string;
  dueDateTo?: string;
  search?: string;
  sortBy?: 'due_date' | 'priority' | 'created_at' | 'title';
  sortOrder?: 'asc' | 'desc';
  page?: number;
  limit?: number;
}

/**
 * Get all tasks for the authenticated user
 */
export async function getTasks(params?: TaskListParams): Promise<{ tasks: Task[]; total: number; page: number; limit: number }> {
  const queryParams: Record<string, string> = {};
  
  if (params?.priority) queryParams.priority = params.priority;
  if (params?.status) queryParams.status = params.status;
  if (params?.tags && params.tags.length > 0) queryParams.tags = params.tags.join(',');
  if (params?.dueDateFrom) queryParams.due_date_from = params.dueDateFrom;
  if (params?.dueDateTo) queryParams.due_date_to = params.dueDateTo;
  if (params?.search) queryParams.q = params.search;
  if (params?.sortBy) queryParams.sort_by = params.sortBy;
  if (params?.sortOrder) queryParams.sort_order = params.sortOrder;
  if (params?.page) queryParams.page = params.page.toString();
  if (params?.limit) queryParams.limit = params.limit.toString();
  
  const response = await api.get<any>('/api/todos', true, queryParams);
  
  // Map backend fields to frontend format
  return {
    tasks: response.tasks.map((todo: any) => mapBackendToTask(todo)),
    total: response.total,
    page: response.page,
    limit: response.limit
  };
}

/**
 * Get a single task by ID
 */
export async function getTask(id: string): Promise<Task> {
  const todo = await api.get<any>(`/api/todos/${id}`, true);
  return mapBackendToTask(todo);
}

/**
 * Create a new task
 */
export async function createTask(data: {
  title: string;
  description?: string;
  due_date?: string;
  priority?: Priority;
  tag_ids?: number[];
}): Promise<Task> {
  const todo = await api.post<any>('/api/todos', data, true);
  return mapBackendToTask(todo);
}

/**
 * Update an existing task
 */
export async function updateTask(id: string, data: {
  title?: string;
  description?: string;
  completed?: boolean;
  due_date?: string;
  priority?: Priority;
  tag_ids?: number[];
}): Promise<Task> {
  const todo = await api.patch<any>(`/api/todos/${id}`, data, true);
  return mapBackendToTask(todo);
}

/**
 * Delete a task
 */
export async function deleteTask(id: string): Promise<void> {
  return api.delete<void>(`/api/todos/${id}`, true);
}

/**
 * Toggle task completion status
 */
export async function toggleTaskCompletion(id: string, completed: boolean): Promise<Task> {
  return updateTask(id, { completed });
}

/**
 * Set recurrence rule for a task
 */
export async function setRecurrence(taskId: number, settings: RecurrenceSettings): Promise<RecurrenceRule> {
  return api.post<RecurrenceRule>(`/api/tasks/${taskId}/recurrence`, settings, true);
}

/**
 * Get recurrence rule for a task
 */
export async function getRecurrence(taskId: number): Promise<RecurrenceRule> {
  return api.get<RecurrenceRule>(`/api/tasks/${taskId}/recurrence`, true);
}

/**
 * Remove recurrence rule from a task
 */
export async function removeRecurrence(taskId: number, deleteFutureInstances: boolean = false): Promise<void> {
  return api.delete<void>(`/api/tasks/${taskId}/recurrence?delete_future_instances=${deleteFutureInstances}`, true);
}

/**
 * Helper function to map backend response to Task interface
 */
function mapBackendToTask(todo: any): Task {
  return {
    id: String(todo.id),
    title: todo.title,
    description: todo.description || '',
    completed: todo.is_completed || todo.completed || false,
    user_id: String(todo.user_id),
    due_date: todo.due_date,
    priority: todo.priority || 'medium',
    tags: todo.tags?.map((tag: any) => ({
      id: tag.id,
      name: tag.name,
      color: tag.color
    })),
    created_at: todo.created_at,
    updated_at: todo.updated_at
  };
}
