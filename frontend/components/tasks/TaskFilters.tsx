'use client';

import { useState, useEffect } from 'react';
import { Priority, Tag } from '@/types/entities';

interface TaskFiltersProps {
  onFilterChange: (filters: TaskFilterState) => void;
  initialFilters?: TaskFilterState;
  tags: Tag[];
}

export interface TaskFilterState {
  priority: Priority | null;
  status: 'completed' | 'incomplete' | 'overdue' | null;
  tags: number[];
  dueDateFrom: string;
  dueDateTo: string;
}

const defaultFilters: TaskFilterState = {
  priority: null,
  status: null,
  tags: [],
  dueDateFrom: '',
  dueDateTo: '',
};

export function TaskFilters({
  onFilterChange,
  initialFilters = defaultFilters,
  tags,
}: TaskFiltersProps) {
  const [filters, setFilters] = useState<TaskFilterState>(initialFilters);
  const [showFilters, setShowFilters] = useState(false);

  const handlePriorityChange = (priority: Priority | null) => {
    const newFilters = { ...filters, priority };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleStatusChange = (status: TaskFilterState['status']) => {
    const newFilters = { ...filters, status };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleTagToggle = (tagId: number) => {
    const newTags = filters.tags.includes(tagId)
      ? filters.tags.filter((id) => id !== tagId)
      : [...filters.tags, tagId];
    
    const newFilters = { ...filters, tags: newTags };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleDueDateFromChange = (dueDateFrom: string) => {
    const newFilters = { ...filters, dueDateFrom };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleDueDateToChange = (dueDateTo: string) => {
    const newFilters = { ...filters, dueDateTo };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleClearFilters = () => {
    setFilters(defaultFilters);
    onFilterChange(defaultFilters);
  };

  const hasActiveFilters =
    filters.priority !== null ||
    filters.status !== null ||
    filters.tags.length > 0 ||
    filters.dueDateFrom !== '' ||
    filters.dueDateTo !== '';

  return (
    <div className="space-y-4">
      {/* Filter Toggle Button */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-zinc-700 dark:text-zinc-300 border border-zinc-300 dark:border-zinc-600 rounded-lg hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          Filters
          {hasActiveFilters && (
            <span className="px-2 py-0.5 text-xs font-medium bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 rounded-full">
              {filters.priority ? 1 : 0}
              {filters.status ? 1 : 0}
              {filters.tags.length}
              {filters.dueDateFrom ? 1 : 0}
              {filters.dueDateTo ? 1 : 0}
            </span>
          )}
        </button>

        {hasActiveFilters && (
          <button
            onClick={handleClearFilters}
            className="text-sm text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200 transition-colors"
          >
            Clear all
          </button>
        )}
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="p-4 space-y-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-lg">
          {/* Priority Filter */}
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
              Priority
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => handlePriorityChange(null)}
                className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                  filters.priority === null
                    ? 'bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 border-zinc-900 dark:border-zinc-100'
                    : 'border-zinc-300 dark:border-zinc-600 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800'
                }`}
              >
                All
              </button>
              {(['high', 'medium', 'low'] as Priority[]).map((priority) => (
                <button
                  key={priority}
                  onClick={() => handlePriorityChange(priority)}
                  className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                    filters.priority === priority
                      ? priority === 'high'
                        ? 'bg-red-500 text-white border-red-500'
                        : priority === 'medium'
                        ? 'bg-amber-500 text-white border-amber-500'
                        : 'bg-green-500 text-white border-green-500'
                      : 'border-zinc-300 dark:border-zinc-600 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800'
                  }`}
                >
                  {priority.charAt(0).toUpperCase() + priority.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
              Status
            </label>
            <div className="flex gap-2 flex-wrap">
              <button
                onClick={() => handleStatusChange(null)}
                className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                  filters.status === null
                    ? 'bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 border-zinc-900 dark:border-zinc-100'
                    : 'border-zinc-300 dark:border-zinc-600 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800'
                }`}
              >
                All
              </button>
              {(['completed', 'incomplete', 'overdue'] as const).map((status) => (
                <button
                  key={status}
                  onClick={() => handleStatusChange(status)}
                  className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                    filters.status === status
                      ? 'bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 border-zinc-900 dark:border-zinc-100'
                      : 'border-zinc-300 dark:border-zinc-600 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800'
                  }`}
                >
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Tags Filter */}
          {tags.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                Tags
              </label>
              <div className="flex gap-2 flex-wrap">
                {tags.map((tag) => (
                  <button
                    key={tag.id}
                    onClick={() => handleTagToggle(tag.id)}
                    className={`px-3 py-1.5 text-sm rounded-full border-2 transition-colors ${
                      filters.tags.includes(tag.id)
                        ? 'border-zinc-900 dark:border-zinc-100 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900'
                        : 'border-zinc-300 dark:border-zinc-600 hover:bg-zinc-50 dark:hover:bg-zinc-800'
                    }`}
                    style={{
                      color: filters.tags.includes(tag.id) ? '' : tag.color,
                    }}
                  >
                    {tag.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Due Date Range */}
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
              Due Date Range
            </label>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <input
                  type="date"
                  value={filters.dueDateFrom}
                  onChange={(e) => handleDueDateFromChange(e.target.value)}
                  placeholder="From"
                  className="w-full px-3 py-2 border rounded-lg text-zinc-900 dark:text-zinc-50 bg-white dark:bg-zinc-800 border-zinc-300 dark:border-zinc-600 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-50"
                />
                <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-500">From</p>
              </div>
              <div>
                <input
                  type="date"
                  value={filters.dueDateTo}
                  onChange={(e) => handleDueDateToChange(e.target.value)}
                  placeholder="To"
                  className="w-full px-3 py-2 border rounded-lg text-zinc-900 dark:text-zinc-50 bg-white dark:bg-zinc-800 border-zinc-300 dark:border-zinc-600 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-50"
                />
                <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-500">To</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
