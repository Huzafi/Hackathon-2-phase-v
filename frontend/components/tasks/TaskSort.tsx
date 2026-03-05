'use client';

export type SortBy = 'due_date' | 'priority' | 'created_at' | 'title';
export type SortOrder = 'asc' | 'desc';

interface TaskSortProps {
  sortBy: SortBy;
  sortOrder: SortOrder;
  onSortChange: (sortBy: SortBy, sortOrder: SortOrder) => void;
}

const SORT_OPTIONS: { value: SortBy; label: string }[] = [
  { value: 'due_date', label: 'Due Date' },
  { value: 'priority', label: 'Priority' },
  { value: 'created_at', label: 'Created Date' },
  { value: 'title', label: 'Title' },
];

export function TaskSort({ sortBy, sortOrder, onSortChange }: TaskSortProps) {
  const handleSortByChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onSortChange(e.target.value as SortBy, sortOrder);
  };

  const handleSortOrderChange = () => {
    onSortChange(sortBy, sortOrder === 'asc' ? 'desc' : 'asc');
  };

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-zinc-600 dark:text-zinc-400">Sort by:</span>
      
      <select
        value={sortBy}
        onChange={handleSortByChange}
        className="px-3 py-1.5 text-sm border rounded-lg text-zinc-900 dark:text-zinc-50 bg-white dark:bg-zinc-800 border-zinc-300 dark:border-zinc-600 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-50"
      >
        {SORT_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

      <button
        onClick={handleSortOrderChange}
        className="p-1.5 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg transition-colors"
        aria-label={`Sort ${sortOrder === 'asc' ? 'descending' : 'ascending'}`}
        title={`Sort ${sortOrder === 'asc' ? 'descending' : 'ascending'}`}
      >
        {sortOrder === 'asc' ? (
          <svg className="h-4 w-4 text-zinc-600 dark:text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
          </svg>
        ) : (
          <svg className="h-4 w-4 text-zinc-600 dark:text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h9m5-4v12m0 0l-4-4m4 4l4-4" />
          </svg>
        )}
      </button>
    </div>
  );
}
