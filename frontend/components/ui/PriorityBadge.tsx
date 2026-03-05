'use client';

import { Priority } from '@/types/entities';

interface PriorityBadgeProps {
  priority: Priority;
  size?: 'sm' | 'md' | 'lg';
}

/**
 * Priority badge component displaying colored indicator
 * 
 * Colors:
 * - High: Red (#EF4444)
 * - Medium: Amber (#F59E0B)
 * - Low: Green (#10B981)
 */
export function PriorityBadge({ priority, size = 'md' }: PriorityBadgeProps) {
  const config = {
    high: {
      label: 'High',
      bgColor: 'bg-red-100 dark:bg-red-900/30',
      textColor: 'text-red-700 dark:text-red-400',
      borderColor: 'border-red-300 dark:border-red-700',
    },
    medium: {
      label: 'Medium',
      bgColor: 'bg-amber-100 dark:bg-amber-900/30',
      textColor: 'text-amber-700 dark:text-amber-400',
      borderColor: 'border-amber-300 dark:border-amber-700',
    },
    low: {
      label: 'Low',
      bgColor: 'bg-green-100 dark:bg-green-900/30',
      textColor: 'text-green-700 dark:text-green-400',
      borderColor: 'border-green-300 dark:border-green-700',
    },
  };

  const { label, bgColor, textColor, borderColor } = config[priority];

  const sizeClasses = {
    sm: 'px-1.5 py-0.5 text-xs',
    md: 'px-2 py-1 text-xs',
    lg: 'px-2.5 py-1.5 text-sm',
  };

  return (
    <span
      className={`
        inline-flex items-center gap-1 rounded-full font-medium
        ${bgColor} ${textColor} ${borderColor} border
        ${sizeClasses[size]}
      `}
      title={`Priority: ${label}`}
    >
      <span className="flex h-2 w-2">
        {priority === 'high' && (
          <span className="animate-pulse inline-flex h-2 w-2 rounded-full bg-red-500" />
        )}
        {priority === 'medium' && (
          <span className="inline-flex h-2 w-2 rounded-full bg-amber-500" />
        )}
        {priority === 'low' && (
          <span className="inline-flex h-2 w-2 rounded-full bg-green-500" />
        )}
      </span>
      {label}
    </span>
  );
}
