'use client';

import { useEffect } from 'react';

export interface NotificationData {
  id: number;
  type: 'reminder' | 'success' | 'error' | 'info';
  title: string;
  message: string;
  taskId?: number;
  taskTitle?: string;
}

interface NotificationToastProps {
  notification: NotificationData;
  onClose: (id: number) => void;
  onClick?: (notification: NotificationData) => void;
  autoClose?: number; // milliseconds, 0 = no auto-close
}

export function NotificationToast({
  notification,
  onClose,
  onClick,
  autoClose = 5000,
}: NotificationToastProps) {
  // Auto-close timer
  useEffect(() => {
    if (autoClose > 0) {
      const timer = setTimeout(() => {
        onClose(notification.id);
      }, autoClose);

      return () => clearTimeout(timer);
    }
  }, [notification.id, autoClose, onClose]);

  const handleClick = () => {
    if (onClick) {
      onClick(notification);
    }
  };

  // Icon based on type
  const getIcon = () => {
    switch (notification.type) {
      case 'reminder':
        return (
          <svg className="h-5 w-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
        );
      case 'success':
        return (
          <svg className="h-5 w-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'error':
        return (
          <svg className="h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      default:
        return (
          <svg className="h-5 w-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  // Background color based on type
  const getBgColor = () => {
    switch (notification.type) {
      case 'reminder':
        return 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800';
      case 'success':
        return 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800';
      case 'error':
        return 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800';
      default:
        return 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800';
    }
  };

  return (
    <div
      className={`flex items-start gap-3 p-4 rounded-lg border shadow-lg ${getBgColor()} max-w-sm cursor-pointer hover:shadow-xl transition-shadow`}
      onClick={handleClick}
      role="alert"
    >
      {/* Icon */}
      <div className="flex-shrink-0">{getIcon()}</div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-zinc-900 dark:text-zinc-50">
          {notification.title}
        </p>
        <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
          {notification.message}
        </p>
        {notification.taskTitle && (
          <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-500">
            Task: {notification.taskTitle}
          </p>
        )}
      </div>

      {/* Close button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onClose(notification.id);
        }}
        className="flex-shrink-0 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300"
        aria-label="Close"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}
