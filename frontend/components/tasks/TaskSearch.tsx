'use client';

import { useState, useEffect, useCallback } from 'react';
import { debounce } from 'lodash';

interface TaskSearchProps {
  onSearchChange: (query: string) => void;
  initialValue?: string;
  placeholder?: string;
}

export function TaskSearch({
  onSearchChange,
  initialValue = '',
  placeholder = 'Search tasks...',
}: TaskSearchProps) {
  const [searchTerm, setSearchTerm] = useState(initialValue);
  const [suggestions, setSuggestions] = useState<{ titles: string[]; tags: string[] }>({
    titles: [],
    tags: [],
  });
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Debounced search
  const debouncedSearch = useCallback(
    debounce((query: string) => {
      onSearchChange(query);
      
      // Fetch suggestions if query is long enough
      if (query.length >= 2) {
        fetchSuggestions(query);
      } else {
        setSuggestions({ titles: [], tags: [] });
        setShowSuggestions(false);
      }
    }, 300),
    [onSearchChange]
  );

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchTerm(value);
    debouncedSearch(value);
  };

  const fetchSuggestions = async (query: string) => {
    try {
      const response = await fetch(
        `/api/tasks/search/suggestions?prefix=${encodeURIComponent(query)}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.suggestions);
        setShowSuggestions(true);
      }
    } catch (error) {
      console.error('Failed to fetch suggestions:', error);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setSearchTerm(suggestion);
    onSearchChange(suggestion);
    setShowSuggestions(false);
  };

  const handleClear = () => {
    setSearchTerm('');
    onSearchChange('');
    setSuggestions({ titles: [], tags: [] });
    setShowSuggestions(false);
  };

  return (
    <div className="relative">
      <div className="relative">
        <input
          type="text"
          value={searchTerm}
          onChange={handleSearchChange}
          placeholder={placeholder}
          className="w-full px-4 py-2 pl-10 pr-10 border rounded-lg text-zinc-900 dark:text-zinc-50 bg-white dark:bg-zinc-800 border-zinc-300 dark:border-zinc-600 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-50 focus:border-transparent"
        />
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-zinc-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        {searchTerm && (
          <button
            onClick={handleClear}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300"
            aria-label="Clear search"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Suggestions Dropdown */}
      {showSuggestions && (suggestions.titles.length > 0 || suggestions.tags.length > 0) && (
        <div className="absolute z-50 w-full mt-1 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {suggestions.titles.length > 0 && (
            <div className="p-2">
              <p className="text-xs font-medium text-zinc-500 dark:text-zinc-400 mb-1">
                Tasks
              </p>
              {suggestions.titles.map((title, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestionClick(title)}
                  className="w-full text-left px-3 py-2 text-sm text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-700 rounded-md transition-colors"
                >
                  {title}
                </button>
              ))}
            </div>
          )}
          
          {suggestions.tags.length > 0 && (
            <div className="p-2 border-t border-zinc-200 dark:border-zinc-700">
              <p className="text-xs font-medium text-zinc-500 dark:text-zinc-400 mb-1">
                Tags
              </p>
              {suggestions.tags.map((tag, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestionClick(tag)}
                  className="w-full text-left px-3 py-2 text-sm text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-700 rounded-md transition-colors"
                >
                  {tag}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
