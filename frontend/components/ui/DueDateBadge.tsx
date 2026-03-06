'use client';

import { format, isPast, isToday, isTomorrow, isThisWeek } from 'date-fns';

interface DueDateBadgeProps {
  dueDate: string;
  completed?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

/**
 * Due date badge component with visual indicators for overdue/due soon
 * 
 * States:
 * - Overdue: Red background
 * - Due today: Orange background with pulse
 * - Due tomorrow: Amber background
 * - Due this week: Yellow background
 * - Due later: Gray background
 */
export function DueDateBadge({ dueDate, completed = false, size = 'md' }: DueDateBadgeProps) {
  const date = new Date(dueDate);
  const now = new Date();
  
  const isOverdue = isPast(date) && !isToday(date);
  const dueToday = isToday(date);
  const dueTomorrow = isTomorrow(date);
  const dueThisWeek = isThisWeek(date);
  
  // Determine styling based on due date status
  let bgColor, textColor, borderColor, icon;
  
  if (completed) {
    bgColor = 'bg-gray-100 dark:bg-gray-800';
    textColor = 'text-gray-500 dark:text-gray-400 line-through';
    borderColor = 'border-gray-300 dark:border-gray-600';
    icon = '✓';
  } else if (isOverdue) {
    bgColor = 'bg-red-100 dark:bg-red-900/30';
    textColor = 'text-red-700 dark:text-red-400';
    borderColor = 'border-red-300 dark:border-red-700';
    icon = '⚠';
  } else if (dueToday) {
    bgColor = 'bg-orange-100 dark:bg-orange-900/30 animate-pulse';
    textColor = 'text-orange-700 dark:text-orange-400';
    borderColor = 'border-orange-300 dark:border-orange-700';
    icon = '●';
  } else if (dueTomorrow) {
    bgColor = 'bg-amber-100 dark:bg-amber-900/30';
    textColor = 'text-amber-700 dark:text-amber-400';
    borderColor = 'border-amber-300 dark:border-amber-700';
    icon = '◐';
  } else if (dueThisWeek) {
    bgColor = 'bg-yellow-100 dark:bg-yellow-900/30';
    textColor = 'text-yellow-700 dark:text-yellow-400';
    borderColor = 'border-yellow-300 dark:border-yellow-700';
    icon = '○';
  } else {
    bgColor = 'bg-gray-100 dark:bg-gray-800';
    textColor = 'text-gray-700 dark:text-gray-300';
    borderColor = 'border-gray-300 dark:border-gray-600';
    icon = '○';
  }
  
  const sizeClasses = {
    sm: 'px-1.5 py-0.5 text-xs',
    md: 'px-2 py-1 text-xs',
    lg: 'px-2.5 py-1.5 text-sm',
  };
  
  // Format the date display
  let dateDisplay;
  if (dueToday) {
    dateDisplay = 'Today';
  } else if (dueTomorrow) {
    dateDisplay = 'Tomorrow';
  } else if (isOverdue) {
    const daysOverdue = Math.floor(Math.abs(now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    dateDisplay = `${daysOverdue}d overdue`;
  } else {
    dateDisplay = format(date, 'MMM d');
  }
  
  return (
    <span
      className={`
        inline-flex items-center gap-1 rounded-full font-medium
        ${bgColor} ${textColor} ${borderColor} border
        ${sizeClasses[size]}
      `}
      title={`Due: ${format(date, 'PPP p')}`}
    >
      <span className="flex-shrink-0">{icon}</span>
      <span className="flex-shrink-0">{dateDisplay}</span>
    </span>
  );
}

/**
 * Helper function to check if a due date is overdue
 */
export function isOverdue(dueDate: string, completed: boolean = false): boolean {
  if (completed) return false;
  const date = new Date(dueDate);
  return isPast(date) && !isToday(date);
}

/**
 * Helper function to check if a due date is due soon (within 24 hours)
 */
export function isDueSoon(dueDate: string, completed: boolean = false, hours: number = 24): boolean {
  if (completed) return false;
  const date = new Date(dueDate);
  const now = new Date();
  const diffMs = date.getTime() - now.getTime();
  const diffHours = diffMs / (1000 * 60 * 60);
  return diffHours > 0 && diffHours <= hours;
}
