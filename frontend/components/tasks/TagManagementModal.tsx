'use client';

import { useState, useEffect } from 'react';
import { Tag } from '@/types/entities';
import { getTags, createTag, updateTag, deleteTag } from '@/lib/api/tags';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { FormInput } from '@/components/ui/FormInput';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';

interface TagManagementModalProps {
  isOpen: boolean;
  onClose: () => void;
  onTagSelected?: (tagId: number) => void;
  selectedTagIds?: number[];
}

export function TagManagementModal({
  isOpen,
  onClose,
  onTagSelected,
  selectedTagIds = []
}: TagManagementModalProps) {
  const [tags, setTags] = useState<Tag[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [editingTag, setEditingTag] = useState<Tag | null>(null);
  
  // Form state
  const [tagName, setTagName] = useState('');
  const [tagColor, setTagColor] = useState('#3B82F6');

  // Load tags when modal opens
  useEffect(() => {
    if (isOpen) {
      loadTags();
    }
  }, [isOpen]);

  const loadTags = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await getTags();
      setTags(response.tags);
    } catch (err) {
      setError('Failed to load tags');
      console.error('Failed to load tags:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateTag = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tagName.trim()) return;

    setIsCreating(true);
    setError(null);
    try {
      const newTag = await createTag({ name: tagName, color: tagColor });
      setTags(prev => [...prev, newTag]);
      setTagName('');
      setTagColor('#3B82F6');
      onTagSelected?.(newTag.id);
    } catch (err) {
      setError('Failed to create tag. Name must be unique.');
      console.error('Failed to create tag:', err);
    } finally {
      setIsCreating(false);
    }
  };

  const handleUpdateTag = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingTag || !tagName.trim()) return;

    setIsCreating(true);
    setError(null);
    try {
      const updatedTag = await updateTag(editingTag.id, { name: tagName, color: tagColor });
      setTags(prev => prev.map(t => t.id === updatedTag.id ? updatedTag : t));
      setEditingTag(null);
      setTagName('');
      setTagColor('#3B82F6');
    } catch (err) {
      setError('Failed to update tag. Name must be unique.');
      console.error('Failed to update tag:', err);
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteTag = async (tagId: number) => {
    if (!confirm('Are you sure you want to delete this tag? This will remove it from all tasks.')) {
      return;
    }

    try {
      await deleteTag(tagId);
      setTags(prev => prev.filter(t => t.id !== tagId));
    } catch (err) {
      setError('Failed to delete tag');
      console.error('Failed to delete tag:', err);
    }
  };

  const handleEditTag = (tag: Tag) => {
    setEditingTag(tag);
    setTagName(tag.name);
    setTagColor(tag.color);
  };

  const handleCancelEdit = () => {
    setEditingTag(null);
    setTagName('');
    setTagColor('#3B82F6');
  };

  const handleTagClick = (tagId: number) => {
    onTagSelected?.(tagId);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={editingTag ? 'Edit Tag' : 'Manage Tags'}
    >
      <div className="space-y-4">
        {/* Create/Edit Form */}
        <form onSubmit={editingTag ? handleUpdateTag : handleCreateTag} className="space-y-3">
          <FormInput
            label="Tag Name"
            type="text"
            value={tagName}
            onChange={(e) => setTagName(e.target.value)}
            placeholder="e.g., work, personal, urgent"
            maxLength={50}
            required
          />
          
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
              Color
            </label>
            <div className="flex items-center gap-2">
              <input
                type="color"
                value={tagColor}
                onChange={(e) => setTagColor(e.target.value)}
                className="h-10 w-10 rounded border border-zinc-300 dark:border-zinc-600 cursor-pointer"
              />
              <span className="text-sm text-zinc-600 dark:text-zinc-400 font-mono">
                {tagColor}
              </span>
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              type="submit"
              disabled={isCreating || !tagName.trim()}
              className="flex-1"
            >
              {isCreating ? 'Saving...' : editingTag ? 'Update Tag' : 'Create Tag'}
            </Button>
            {editingTag && (
              <Button
                type="button"
                variant="ghost"
                onClick={handleCancelEdit}
              >
                Cancel
              </Button>
            )}
          </div>
        </form>

        {/* Error Message */}
        {error && <ErrorMessage message={error} />}

        {/* Tags List */}
        {isLoading ? (
          <LoadingSpinner />
        ) : tags.length === 0 ? (
          <div className="text-center py-8 text-zinc-500 dark:text-zinc-400">
            <p>No tags yet. Create your first tag above.</p>
          </div>
        ) : (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
              Your Tags ({tags.length})
            </h4>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {tags.map((tag) => (
                <div
                  key={tag.id}
                  className={`flex items-center justify-between p-3 rounded-lg border transition-colors ${
                    selectedTagIds.includes(tag.id)
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800'
                  }`}
                >
                  <div
                    className="flex items-center gap-2 cursor-pointer flex-1"
                    onClick={() => handleTagClick(tag.id)}
                  >
                    <span
                      className="h-3 w-3 rounded-full"
                      style={{ backgroundColor: tag.color }}
                    />
                    <span className="font-medium">{tag.name}</span>
                    {tag.task_count > 0 && (
                      <span className="text-xs text-zinc-500 dark:text-zinc-400">
                        ({tag.task_count} {tag.task_count === 1 ? 'task' : 'tasks'})
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEditTag(tag)}
                      aria-label="Edit tag"
                    >
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteTag(tag.id)}
                      aria-label="Delete tag"
                    >
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Close Button */}
        <div className="flex justify-end">
          <Button variant="ghost" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
}
