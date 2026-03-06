'use client';

import { Tag } from '@/types/entities';

interface TagListProps {
  tags: Tag[];
  maxDisplay?: number;
  size?: 'sm' | 'md' | 'lg';
  onTagClick?: (tagId: number) => void;
  interactive?: boolean;
}

/**
 * Tag list component displaying tags as clickable badges
 */
export function TagList({
  tags,
  maxDisplay = 5,
  size = 'md',
  onTagClick,
  interactive = false,
}: TagListProps) {
  if (!tags || tags.length === 0) {
    return null;
  }
  
  const displayTags = tags.slice(0, maxDisplay);
  const remainingCount = tags.length - maxDisplay;
  
  const sizeClasses = {
    sm: 'px-1.5 py-0.5 text-xs',
    md: 'px-2 py-1 text-xs',
    lg: 'px-2.5 py-1.5 text-sm',
  };
  
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {displayTags.map((tag) => (
        <span
          key={tag.id}
          className={`
            inline-flex items-center gap-1 rounded-full font-medium
            border ${sizeClasses[size]}
            ${interactive && onTagClick
              ? 'cursor-pointer hover:opacity-80 transition-opacity'
              : ''
            }
          `}
          style={{
            backgroundColor: `${tag.color}20`, // 20% opacity background
            color: tag.color,
            borderColor: tag.color,
          }}
          onClick={() => interactive && onTagClick?.(tag.id)}
          title={interactive ? `Click to filter by ${tag.name}` : tag.name}
        >
          <span
            className="h-2 w-2 rounded-full"
            style={{ backgroundColor: tag.color }}
          />
          {tag.name}
        </span>
      ))}
      
      {remainingCount > 0 && (
        <span
          className={`
            inline-flex items-center rounded-full font-medium
            bg-gray-100 dark:bg-gray-800
            text-gray-600 dark:text-gray-400
            border border-gray-300 dark:border-gray-600
            ${sizeClasses[size]}
          `}
          title={`${remainingCount} more tag${remainingCount > 1 ? 's' : ''}`}
        >
          +{remainingCount}
        </span>
      )}
    </div>
  );
}

/**
 * Empty state for when no tags are present
 */
export function NoTags() {
  return (
    <span className="text-sm text-gray-400 dark:text-gray-500 italic">
      No tags
    </span>
  );
}
