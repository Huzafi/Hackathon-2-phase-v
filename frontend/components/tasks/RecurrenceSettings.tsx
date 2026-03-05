'use client';

import { useState, useEffect } from 'react';
import { RecurrencePattern } from '@/types/recurrence';

interface RecurrenceSettingsProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (settings: RecurrenceSettingsData) => void;
  initialData?: RecurrenceSettingsData | null;
}

export interface RecurrenceSettingsData {
  pattern: RecurrencePattern;
  interval: number;
  start_date: string;
  end_date?: string;
  by_weekday?: string;
  by_monthday?: number;
}

const WEEKDAY_OPTIONS = [
  { value: 'MO', label: 'Mon' },
  { value: 'TU', label: 'Tue' },
  { value: 'WE', label: 'Wed' },
  { value: 'TH', label: 'Thu' },
  { value: 'FR', label: 'Fri' },
  { value: 'SA', label: 'Sat' },
  { value: 'SU', label: 'Sun' },
];

const PATTERN_OPTIONS = [
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'yearly', label: 'Yearly' },
];

export function RecurrenceSettings({
  isOpen,
  onClose,
  onSave,
  initialData,
}: RecurrenceSettingsProps) {
  const [pattern, setPattern] = useState<RecurrencePattern>('weekly');
  const [interval, setInterval] = useState(1);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [selectedWeekdays, setSelectedWeekdays] = useState<string[]>(['MO']);
  const [monthDay, setMonthDay] = useState(1);
  const [error, setError] = useState('');

  // Initialize with existing data or defaults
  useEffect(() => {
    if (initialData) {
      setPattern(initialData.pattern);
      setInterval(initialData.interval || 1);
      setStartDate(initialData.start_date?.split('T')[0] || new Date().toISOString().split('T')[0]);
      setEndDate(initialData.end_date || '');
      setSelectedWeekdays(initialData.by_weekday?.split(',') || ['MO']);
      setMonthDay(initialData.by_monthday || 1);
    } else {
      // Defaults for new recurrence
      setStartDate(new Date().toISOString().split('T')[0]);
    }
  }, [initialData, isOpen]);

  const handleWeekdayToggle = (weekday: string) => {
    setSelectedWeekdays(prev =>
      prev.includes(weekday)
        ? prev.filter(d => d !== weekday)
        : [...prev, weekday]
    );
  };

  const handleSave = () => {
    setError('');

    // Validation
    if (pattern === 'weekly' && selectedWeekdays.length === 0) {
      setError('Please select at least one day of the week');
      return;
    }

    if (endDate && new Date(endDate) <= new Date(startDate)) {
      setError('End date must be after start date');
      return;
    }

    const settings: RecurrenceSettingsData = {
      pattern,
      interval,
      start_date: startDate,
      end_date: endDate || undefined,
      by_weekday: pattern === 'weekly' ? selectedWeekdays.join(',') : undefined,
      by_monthday: pattern === 'monthly' ? monthDay : undefined,
    };

    onSave(settings);
  };

  const handleCancel = () => {
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white dark:bg-zinc-900 rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-zinc-200 dark:border-zinc-700">
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
            Recurrence Settings
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
          {/* Pattern Selection */}
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
              Repeat
            </label>
            <select
              value={pattern}
              onChange={(e) => setPattern(e.target.value as RecurrencePattern)}
              className="w-full px-3 py-2 border rounded-lg text-zinc-900 dark:text-zinc-50 bg-white dark:bg-zinc-800 border-zinc-300 dark:border-zinc-600 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-50"
            >
              {PATTERN_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Interval */}
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
              Repeat Every
            </label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                min="1"
                max="365"
                value={interval}
                onChange={(e) => setInterval(Math.max(1, parseInt(e.target.value) || 1))}
                className="w-20 px-3 py-2 border rounded-lg text-zinc-900 dark:text-zinc-50 bg-white dark:bg-zinc-800 border-zinc-300 dark:border-zinc-600 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-50"
              />
              <span className="text-zinc-600 dark:text-zinc-400">
                {pattern === 'daily' ? 'day(s)' :
                 pattern === 'weekly' ? 'week(s)' :
                 pattern === 'monthly' ? 'month(s)' : 'year(s)'}
              </span>
            </div>
          </div>

          {/* Weekly: Weekday Selection */}
          {pattern === 'weekly' && (
            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                On Days
              </label>
              <div className="flex gap-2">
                {WEEKDAY_OPTIONS.map((day) => (
                  <button
                    key={day.value}
                    type="button"
                    onClick={() => handleWeekdayToggle(day.value)}
                    className={`w-10 h-10 rounded-full text-sm font-medium transition-colors ${
                      selectedWeekdays.includes(day.value)
                        ? 'bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900'
                        : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200 dark:hover:bg-zinc-700'
                    }`}
                  >
                    {day.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Monthly: Day Selection */}
          {pattern === 'monthly' && (
            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                On Day
              </label>
              <div className="flex items-center gap-2">
                <select
                  value={monthDay}
                  onChange={(e) => setMonthDay(parseInt(e.target.value))}
                  className="w-full px-3 py-2 border rounded-lg text-zinc-900 dark:text-zinc-50 bg-white dark:bg-zinc-800 border-zinc-300 dark:border-zinc-600 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-50"
                >
                  {Array.from({ length: 31 }, (_, i) => i + 1).map((day) => (
                    <option key={day} value={day}>
                      Day {day}
                      {day === 31 ? ' (adjusted for shorter months)' : ''}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}

          {/* Start Date */}
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
              Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg text-zinc-900 dark:text-zinc-50 bg-white dark:bg-zinc-800 border-zinc-300 dark:border-zinc-600 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-50"
            />
          </div>

          {/* End Date (Optional) */}
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
              End Date <span className="text-zinc-500">(optional)</span>
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg text-zinc-900 dark:text-zinc-50 bg-white dark:bg-zinc-800 border-zinc-300 dark:border-zinc-600 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-50"
            />
            <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-500">
              Leave empty for no end date
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </div>
          )}

          {/* Preview */}
          <div className="p-3 bg-zinc-50 dark:bg-zinc-800 rounded-lg">
            <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
              Preview:
            </p>
            <p className="text-sm text-zinc-600 dark:text-zinc-400">
              {pattern === 'daily' && `Every ${interval} day${interval > 1 ? 's' : ''}`}
              {pattern === 'weekly' && `Every ${interval} week${interval > 1 ? 's' : ''} on ${selectedWeekdays.join(', ')}`}
              {pattern === 'monthly' && `Every ${interval} month${interval > 1 ? 's' : ''} on day ${monthDay}`}
              {pattern === 'yearly' && `Every ${interval} year${interval > 1 ? 's' : ''}`}
              {endDate && ` until ${new Date(endDate).toLocaleDateString()}`}
            </p>
          </div>
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
            Save
          </button>
        </div>
      </div>
    </div>
  );
}
