'use client';

import { useState } from 'react';

interface ReminderSettingsProps {
  taskId: number;
  isOpen: boolean;
  onClose: () => void;
  onSave: (triggerTime: string) => void;
}

export function ReminderSettings({
  taskId,
  isOpen,
  onClose,
  onSave,
}: ReminderSettingsProps) {
  const [date, setDate] = useState('');
  const [time, setTime] = useState('09:00');
  const [error, setError] = useState('');

  const handleSave = () => {
    setError('');

    if (!date || !time) {
      setError('Please select both date and time');
      return;
    }

    const triggerTime = new Date(`${date}T${time}`);
    const now = new Date();

    if (triggerTime <= now) {
      setError('Reminder time must be in the future');
      return;
    }

    onSave(triggerTime.toISOString());
  };

  const handleCancel = () => {
    setDate('');
    setTime('09:00');
    setError('');
    onClose();
  };

  if (!isOpen) return null;

  // Get minimum date (today)
  const minDate = new Date().toISOString().split('T')[0];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white dark:bg-zinc-900 rounded-lg shadow-xl max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-zinc-200 dark:border-zinc-700">
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
            Add Reminder
          </h2>
          <button
            onClick={onClose}
            className="text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200"
            aria-label="Close"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          {/* Date Picker */}
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
              Date
            </label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              min={minDate}
              className="w-full px-3 py-2 border rounded-lg text-zinc-900 dark:text-zinc-50 bg-white dark:bg-zinc-800 border-zinc-300 dark:border-zinc-600 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-50"
            />
          </div>

          {/* Time Picker */}
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
              Time
            </label>
            <input
              type="time"
              value={time}
              onChange={(e) => setTime(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg text-zinc-900 dark:text-zinc-50 bg-white dark:bg-zinc-800 border-zinc-300 dark:border-zinc-600 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-50"
            />
          </div>

          {/* Quick Options */}
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
              Quick Options
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => {
                  const now = new Date();
                  now.setHours(now.getHours() + 1);
                  setDate(now.toISOString().split('T')[0]);
                  setTime(now.toTimeString().slice(0, 5));
                }}
                className="px-3 py-2 text-sm border border-zinc-300 dark:border-zinc-600 rounded-lg hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors text-zinc-700 dark:text-zinc-300"
              >
                In 1 hour
              </button>
              <button
                type="button"
                onClick={() => {
                  const now = new Date();
                  now.setHours(now.getHours() + 24);
                  setDate(now.toISOString().split('T')[0]);
                  setTime(now.toTimeString().slice(0, 5));
                }}
                className="px-3 py-2 text-sm border border-zinc-300 dark:border-zinc-600 rounded-lg hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors text-zinc-700 dark:text-zinc-300"
              >
                Tomorrow
              </button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </div>
          )}

          {/* Preview */}
          {date && time && (
            <div className="p-3 bg-zinc-50 dark:bg-zinc-800 rounded-lg">
              <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                Reminder will be set for:
              </p>
              <p className="text-sm text-zinc-600 dark:text-zinc-400">
                {new Date(`${date}T${time}`).toLocaleString()}
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-4 border-t border-zinc-200 dark:border-zinc-700">
          <button
            type="button"
            onClick={handleCancel}
            className="px-4 py-2 text-sm font-medium text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSave}
            className="px-4 py-2 text-sm font-medium text-white bg-zinc-900 dark:bg-zinc-100 dark:text-zinc-900 rounded-lg hover:bg-zinc-800 dark:hover:bg-zinc-200 transition-colors"
          >
            Set Reminder
          </button>
        </div>
      </div>
    </div>
  );
}
