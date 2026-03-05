'use client';

/**
 * Task form component for creating and editing tasks
 */

import { useState, FormEvent, useEffect } from 'react';
import { FormInput } from '../ui/FormInput';
import { Button } from '../ui/Button';
import { ErrorMessage } from '../ui/ErrorMessage';
import { validateTaskTitle, validateTaskDescription } from '@/types/validation';
import { TaskFormData } from '@/types/ui';
import { Priority, Tag } from '@/types/entities';
import { getTags } from '@/lib/api/tags';
import { TagList } from '../ui/TagList';
import { RecurrenceSettings, RecurrenceRule } from '@/types/recurrence';
import { RecurrenceSettings as RecurrenceSettingsModal } from './RecurrenceSettings';
import { setRecurrence, getRecurrence, removeRecurrence } from '@/lib/api/tasks';
import { ReminderSettings as ReminderSettingsModal } from './ReminderSettings';
import { createReminder, deleteReminder, Reminder } from '@/lib/api/reminders';

interface TaskFormProps {
  initialData?: Partial<TaskFormData & { 
    due_date?: string; 
    priority?: Priority; 
    tag_ids?: number[];
    recurrence?: RecurrenceRule;
  }>;
  onSubmit: (data: TaskFormData & { due_date?: string; priority?: Priority; tag_ids?: number[]; recurrence?: RecurrenceSettings }) => Promise<void>;
  onCancel: () => void;
  submitLabel?: string;
}

export function TaskForm({
  initialData = {},
  onSubmit,
  onCancel,
  submitLabel = 'Save',
}: TaskFormProps) {
  const [title, setTitle] = useState(initialData.title || '');
  const [description, setDescription] = useState(initialData.description || '');
  const [dueDate, setDueDate] = useState(initialData.due_date?.split('T')[0] || '');
  const [priority, setPriority] = useState<Priority>(initialData.priority || 'medium');
  const [selectedTags, setSelectedTags] = useState<number[]>(initialData.tag_ids || []);
  const [availableTags, setAvailableTags] = useState<Tag[]>([]);
  const [isLoadingTags, setIsLoadingTags] = useState(false);
  const [recurrenceSettings, setRecurrenceSettings] = useState<RecurrenceRule | null>(initialData.recurrence || null);
  const [isRecurrenceModalOpen, setIsRecurrenceModalOpen] = useState(false);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [isReminderModalOpen, setIsReminderModalOpen] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState('');

  // Load available tags
  useEffect(() => {
    const loadTags = async () => {
      setIsLoadingTags(true);
      try {
        const response = await getTags();
        setAvailableTags(response.tags);
      } catch (err) {
        console.error('Failed to load tags:', err);
      } finally {
        setIsLoadingTags(false);
      }
    };
    loadTags();
  }, []);

  const toggleTag = (tagId: number) => {
    setSelectedTags(prev => 
      prev.includes(tagId) 
        ? prev.filter(id => id !== tagId)
        : [...prev, tagId]
    );
  };

  const handleOpenRecurrenceModal = () => {
    setIsRecurrenceModalOpen(true);
  };

  const handleCloseRecurrenceModal = () => {
    setIsRecurrenceModalOpen(false);
  };

  const handleSaveRecurrence = async (settings: RecurrenceSettings) => {
    if (!initialData?.id) {
      setApiError('Please save the task first before setting recurrence');
      return;
    }
    
    try {
      const rule = await setRecurrence(initialData.id, settings);
      setRecurrenceSettings(rule);
      setIsRecurrenceModalOpen(false);
    } catch (error: any) {
      setApiError(error.message || 'Failed to save recurrence settings');
    }
  };

  const handleRemoveRecurrence = async () => {
    if (!initialData?.id || !recurrenceSettings) return;
    
    if (!confirm('Remove recurrence from this task? Future instances will not be affected.')) {
      return;
    }
    
    try {
      await removeRecurrence(initialData.id, false);
      setRecurrenceSettings(null);
    } catch (error: any) {
      setApiError(error.message || 'Failed to remove recurrence');
    }
  };

  const handleOpenReminderModal = () => {
    setIsReminderModalOpen(true);
  };

  const handleCloseReminderModal = () => {
    setIsReminderModalOpen(false);
  };

  const handleSaveReminder = async (triggerTime: string) => {
    if (!initialData?.id) {
      setApiError('Please save the task first before setting a reminder');
      return;
    }
    
    try {
      const newReminder = await createReminder({
        task_id: initialData.id,
        trigger_time: triggerTime
      });
      setReminders(prev => [...prev, newReminder]);
      setIsReminderModalOpen(false);
    } catch (error: any) {
      setApiError(error.message || 'Failed to set reminder');
    }
  };

  const handleDeleteReminder = async (reminderId: number) => {
    if (!confirm('Delete this reminder?')) return;
    
    try {
      await deleteReminder(reminderId);
      setReminders(prev => prev.filter(r => r.id !== reminderId));
    } catch (error: any) {
      setApiError(error.message || 'Failed to delete reminder');
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setApiError('');
    setErrors({});

    // Validate form
    const newErrors: Record<string, string> = {};

    const titleError = validateTaskTitle(title);
    if (titleError) newErrors.title = titleError;

    const descriptionError = validateTaskDescription(description);
    if (descriptionError) newErrors.description = descriptionError;

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    // Submit form
    setIsSubmitting(true);
    try {
      await onSubmit({ 
        title, 
        description,
        due_date: dueDate ? new Date(dueDate).toISOString() : undefined,
        priority,
        tag_ids: selectedTags.length > 0 ? selectedTags : undefined
      });
    } catch (error: any) {
      setApiError(error.message || 'Failed to save task. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      {apiError && <ErrorMessage>{apiError}</ErrorMessage>}

      <FormInput
        label="Title"
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        error={errors.title}
        placeholder="Enter task title"
        required
        maxLength={200}
      />

      <div>
        <label
          htmlFor="description"
          className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1"
        >
          Description
        </label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Enter task description (optional)"
          rows={4}
          maxLength={1000}
          className="w-full px-3 py-2 border rounded-lg text-zinc-900 dark:text-zinc-50 bg-white dark:bg-zinc-900 border-zinc-300 dark:border-zinc-700 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-50 focus:border-transparent resize-none"
        />
        {errors.description && (
          <p className="mt-1 text-sm text-red-600 dark:text-red-400" role="alert">
            {errors.description}
          </p>
        )}
        <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-500">
          {description.length}/1000 characters
        </p>
      </div>

      {/* Due Date */}
      <div>
        <label
          htmlFor="dueDate"
          className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1"
        >
          Due Date
        </label>
        <input
          type="date"
          id="dueDate"
          value={dueDate}
          onChange={(e) => setDueDate(e.target.value)}
          className="w-full px-3 py-2 border rounded-lg text-zinc-900 dark:text-zinc-50 bg-white dark:bg-zinc-900 border-zinc-300 dark:border-zinc-700 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-50 focus:border-transparent"
        />
        <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-500">
          Optional - leave empty for no due date
        </p>
      </div>

      {/* Priority */}
      <div>
        <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
          Priority
        </label>
        <div className="flex gap-2">
          {(['low', 'medium', 'high'] as Priority[]).map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => setPriority(p)}
              className={`flex-1 py-2 px-3 rounded-lg border-2 font-medium transition-colors ${
                priority === p
                  ? p === 'high'
                    ? 'border-red-500 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400'
                    : p === 'medium'
                    ? 'border-amber-500 bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400'
                    : 'border-green-500 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400'
                  : 'border-zinc-300 dark:border-zinc-700 hover:border-zinc-400 dark:hover:border-zinc-600'
              }`}
            >
              {p.charAt(0).toUpperCase() + p.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Tags */}
      <div>
        <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
          Tags
        </label>
        {isLoadingTags ? (
          <p className="text-sm text-zinc-500 dark:text-zinc-400">Loading tags...</p>
        ) : availableTags.length === 0 ? (
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            No tags available. Create tags first.
          </p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {availableTags.map((tag) => (
              <button
                key={tag.id}
                type="button"
                onClick={() => toggleTag(tag.id)}
                className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-full border-2 font-medium text-sm transition-colors ${
                  selectedTags.includes(tag.id)
                    ? 'border-zinc-900 dark:border-zinc-100 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900'
                    : 'border-zinc-300 dark:border-zinc-700 hover:border-zinc-400 dark:hover:border-zinc-600'
                }`}
                style={{
                  backgroundColor: selectedTags.includes(tag.id) ? '' : `${tag.color}20`,
                  color: selectedTags.includes(tag.id) ? '' : tag.color,
                }}
              >
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: tag.color }}
                />
                {tag.name}
                {selectedTags.includes(tag.id) && (
                  <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </button>
            ))}
          </div>
        )}
        {selectedTags.length > 0 && (
          <div className="mt-2">
            <TagList 
              tags={availableTags.filter(t => selectedTags.includes(t.id))}
              size="sm"
            />
          </div>
        )}
      </div>

      {/* Recurrence */}
      <div>
        <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
          Recurrence
        </label>
        {recurrenceSettings ? (
          <div className="p-3 bg-zinc-50 dark:bg-zinc-800 rounded-lg border border-zinc-200 dark:border-zinc-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-zinc-900 dark:text-zinc-50">
                  {recurrenceSettings.pattern.charAt(0).toUpperCase() + recurrenceSettings.pattern.slice(1)}
                  {recurrenceSettings.interval > 1 ? ` (Every ${recurrenceSettings.interval})` : ''}
                </p>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">
                  Starts {new Date(recurrenceSettings.start_date).toLocaleDateString()}
                  {recurrenceSettings.end_date && ` • Ends ${new Date(recurrenceSettings.end_date).toLocaleDateString()}`}
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRemoveRecurrence}
                aria-label="Remove recurrence"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </Button>
            </div>
          </div>
        ) : (
          <Button
            type="button"
            variant="secondary"
            onClick={handleOpenRecurrenceModal}
            className="w-full"
          >
            <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Make Recurring
          </Button>
        )}
      </div>

      {/* Reminders */}
      <div>
        <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
          Reminders
        </label>
        {reminders.length > 0 ? (
          <div className="space-y-2">
            {reminders.map((reminder) => (
              <div
                key={reminder.id}
                className="flex items-center justify-between p-3 bg-zinc-50 dark:bg-zinc-800 rounded-lg border border-zinc-200 dark:border-zinc-700"
              >
                <div>
                  <p className="text-sm font-medium text-zinc-900 dark:text-zinc-50">
                    {new Date(reminder.trigger_time).toLocaleString()}
                  </p>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">
                    {reminder.delivered ? 'Delivered' : 'Pending'}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDeleteReminder(reminder.id)}
                  aria-label="Delete reminder"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </Button>
              </div>
            ))}
          </div>
        ) : (
          <Button
            type="button"
            variant="secondary"
            onClick={handleOpenReminderModal}
            className="w-full"
          >
            <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            Add Reminder
          </Button>
        )}
      </div>

      {/* Reminder Settings Modal */}
      <ReminderSettingsModal
        taskId={initialData.id || 0}
        isOpen={isReminderModalOpen}
        onClose={handleCloseReminderModal}
        onSave={handleSaveReminder}
      />
    </form>
  );
}
