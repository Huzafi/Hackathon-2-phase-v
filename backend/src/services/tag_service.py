"""Tag service for business logic and validation."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlmodel import Session, select, func
from ..models.tag import Tag
from ..models.event_log import EventType
from ..services.event_producer import get_event_producer
import logging
import re


logger = logging.getLogger(__name__)


class TagService:
    """Service layer for tag business logic."""
    
    def __init__(self, session: Session):
        self.session = session
        self.event_producer = get_event_producer(session)
    
    async def create_tag(
        self,
        name: str,
        user_id: int,
        color: Optional[str] = "#3B82F6"
    ) -> Tag:
        """Create a new tag.
        
        Args:
            name: Tag name (1-50 chars, alphanumeric + hyphens + spaces)
            user_id: Owner user ID
            color: Hex color code (default: #3B82F6)
        
        Returns:
            Created Tag instance
        
        Raises:
            ValueError: If validation fails
        """
        # Validate name
        name = name.strip()
        if not name:
            raise ValueError("Tag name cannot be empty")
        if len(name) > 50:
            raise ValueError("Tag name cannot exceed 50 characters")
        if not re.match(r'^[a-zA-Z0-9\s\-]+$', name):
            raise ValueError("Tag name can only contain letters, numbers, spaces, and hyphens")
        
        # Validate color
        if color and not re.match(r'^#[0-9A-Fa-f]{6}$', color):
            raise ValueError("Invalid color format. Use 6-digit hex code (e.g., #3B82F6)")
        
        # Check for duplicate (case-insensitive)
        existing_tag = self._get_tag_by_name(name, user_id)
        if existing_tag:
            raise ValueError(f"Tag with name '{name}' already exists")
        
        # Create tag
        tag = Tag(
            user_id=user_id,
            name=name,
            color=color or "#3B82F6"
        )
        
        self.session.add(tag)
        self.session.commit()
        self.session.refresh(tag)
        
        # Emit event
        await self._emit_tag_created_event(tag)
        
        logger.info(f"Tag created: id={tag.id}, user_id={user_id}, name={name}")
        return tag
    
    async def update_tag(
        self,
        tag_id: int,
        user_id: int,
        name: Optional[str] = None,
        color: Optional[str] = None
    ) -> Tag:
        """Update an existing tag.
        
        Args:
            tag_id: Tag ID to update
            user_id: Owner user ID
            name: New name (optional)
            color: New color (optional)
        
        Returns:
            Updated Tag instance
        
        Raises:
            ValueError: If validation fails
            HTTPException: If tag not found or wrong owner
        """
        tag = self._get_tag_or_raise(tag_id, user_id)
        
        # Update name if provided
        if name is not None:
            name = name.strip()
            if not name:
                raise ValueError("Tag name cannot be empty")
            if len(name) > 50:
                raise ValueError("Tag name cannot exceed 50 characters")
            if not re.match(r'^[a-zA-Z0-9\s\-]+$', name):
                raise ValueError("Tag name can only contain letters, numbers, spaces, and hyphens")
            
            # Check for duplicate (case-insensitive, excluding current tag)
            existing_tag = self._get_tag_by_name(name, user_id)
            if existing_tag and existing_tag.id != tag_id:
                raise ValueError(f"Tag with name '{name}' already exists")
            
            tag.name = name
        
        # Update color if provided
        if color is not None:
            if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
                raise ValueError("Invalid color format. Use 6-digit hex code (e.g., #3B82F6)")
            tag.color = color
        
        self.session.add(tag)
        self.session.commit()
        self.session.refresh(tag)
        
        # Emit event
        await self._emit_tag_updated_event(tag)
        
        logger.info(f"Tag updated: id={tag_id}, user_id={user_id}")
        return tag
    
    def get_tag(self, tag_id: int, user_id: int) -> Tag:
        """Get a tag by ID with ownership check.
        
        Args:
            tag_id: Tag ID
            user_id: Owner user ID
        
        Returns:
            Tag instance
        
        Raises:
            HTTPException: If not found or wrong owner
        """
        tag = self._get_tag_or_raise(tag_id, user_id)
        
        # Get task count for this tag
        from ..models.task_tag import TaskTag
        count_statement = select(func.count()).select_from(TaskTag).where(TaskTag.tag_id == tag_id)
        task_count = self.session.exec(count_statement).one()
        
        # Add task_count as a dynamic attribute
        tag.task_count = task_count  # type: ignore
        
        return tag
    
    def list_tags(
        self,
        user_id: int,
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """List all tags for a user.
        
        Args:
            user_id: Owner user ID
            page: Page number
            limit: Items per page
        
        Returns:
            Dict with tags list and pagination info
        """
        # Get total count
        count_statement = select(func.count()).where(Tag.user_id == user_id)
        total = self.session.exec(count_statement).one()
        
        # Get tags with pagination
        offset = (page - 1) * limit
        statement = select(Tag).where(Tag.user_id == user_id).offset(offset).limit(limit)
        tags = self.session.exec(statement).all()
        
        # Get task count for each tag
        from ..models.task_tag import TaskTag
        tags_with_count = []
        for tag in tags:
            count_statement = select(func.count()).select_from(TaskTag).where(TaskTag.tag_id == tag.id)
            task_count = self.session.exec(count_statement).one()
            
            # Create a dict with tag data and task count
            tag_dict = {
                "id": tag.id,
                "user_id": tag.user_id,
                "name": tag.name,
                "color": tag.color,
                "created_at": tag.created_at,
                "task_count": task_count
            }
            tags_with_count.append(tag_dict)
        
        return {
            "tags": tags_with_count,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
    
    async def delete_tag(self, tag_id: int, user_id: int) -> None:
        """Delete a tag.
        
        This does not delete associated tasks, only removes the tag association.
        
        Args:
            tag_id: Tag ID
            user_id: Owner user ID
        
        Raises:
            HTTPException: If not found or wrong owner
        """
        tag = self._get_tag_or_raise(tag_id, user_id)
        
        # Emit event before deletion
        await self._emit_tag_deleted_event(tag)
        
        self.session.delete(tag)
        self.session.commit()
        
        logger.info(f"Tag deleted: id={tag_id}, user_id={user_id}")
    
    def _get_tag_by_name(self, name: str, user_id: int) -> Optional[Tag]:
        """Get tag by name (case-insensitive)."""
        statement = select(Tag).where(
            (Tag.user_id == user_id) & (Tag.name.ilike(name))
        )
        return statement.first()
    
    def _get_tag_or_raise(self, tag_id: int, user_id: int) -> Tag:
        """Get tag by ID with ownership check."""
        from fastapi import HTTPException, status
        
        statement = select(Tag).where(Tag.id == tag_id)
        tag = self.session.exec(statement).first()
        
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found"
            )
        
        if tag.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this tag"
            )
        
        return tag
    
    async def _emit_tag_created_event(self, tag: Tag) -> None:
        """Emit tag.created event."""
        try:
            await self.event_producer.publish(
                event_type=EventType.TAG_CREATED,
                payload={
                    "tag_id": tag.id,
                    "name": tag.name,
                    "color": tag.color
                },
                user_id=tag.user_id
            )
        except Exception as e:
            logger.error(f"Failed to emit tag.created event: {e}")
    
    async def _emit_tag_updated_event(self, tag: Tag) -> None:
        """Emit tag.updated event."""
        try:
            await self.event_producer.publish(
                event_type=EventType.TAG_UPDATED,
                payload={
                    "tag_id": tag.id,
                    "name": tag.name,
                    "color": tag.color
                },
                user_id=tag.user_id
            )
        except Exception as e:
            logger.error(f"Failed to emit tag.updated event: {e}")
    
    async def _emit_tag_deleted_event(self, tag: Tag) -> None:
        """Emit tag.deleted event."""
        try:
            await self.event_producer.publish(
                event_type=EventType.TAG_DELETED,
                payload={
                    "tag_id": tag.id,
                    "name": tag.name
                },
                user_id=tag.user_id
            )
        except Exception as e:
            logger.error(f"Failed to emit tag.deleted event: {e}")


def get_tag_service(session: Session) -> TagService:
    """Get a TagService instance."""
    return TagService(session)
