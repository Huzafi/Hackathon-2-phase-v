"""Search service for task search and filtering."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlmodel import Session, select, func, text
import logging

from ..models.todo import Todo, PriorityEnum
from ..models.tag import Tag
from ..models.task_tag import TaskTag


logger = logging.getLogger(__name__)


class SearchService:
    """Service for searching and filtering tasks."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def search_tasks(
        self,
        user_id: int,
        query: Optional[str] = None,
        priority: Optional[PriorityEnum] = None,
        status: Optional[str] = None,
        tag_ids: Optional[List[int]] = None,
        due_date_from: Optional[datetime] = None,
        due_date_to: Optional[datetime] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Search and filter tasks with pagination and sorting.
        
        Args:
            user_id: User ID (always filter by user)
            query: Search keyword (searches title and description)
            priority: Filter by priority level
            status: Filter by status (completed, incomplete, overdue)
            tag_ids: Filter by tag IDs
            due_date_from: Filter tasks due on or after this date
            due_date_to: Filter tasks due on or before this date
            sort_by: Sort field (due_date, priority, created_at, title)
            sort_order: Sort order (asc, desc)
            page: Page number (1-indexed)
            limit: Items per page
        
        Returns:
            Dict with tasks list, total count, and pagination info
        """
        logger.info(f"Searching tasks for user {user_id}: query={query}, sort_by={sort_by}, sort_order={sort_order}")
        
        # Build base query with user filter
        base_query = select(Todo).where(Todo.user_id == user_id)
        
        # Apply search query (full-text search)
        if query:
            # Use PostgreSQL full-text search
            search_query = text(
                "to_tsvector('english', title || ' ' || COALESCE(description, '')) @@ plainto_tsquery(:query)"
            )
            base_query = base_query.where(search_query.bindparams(query=query))
        
        # Apply priority filter
        if priority:
            base_query = base_query.where(Todo.priority == priority)
        
        # Apply status filter
        if status:
            if status == "completed":
                base_query = base_query.where(Todo.is_completed == True)
            elif status == "incomplete":
                base_query = base_query.where(Todo.is_completed == False)
            elif status == "overdue":
                base_query = base_query.where(
                    (Todo.due_date < datetime.utcnow()) & (Todo.is_completed == False)
                )
        
        # Apply tag filter
        if tag_ids:
            tag_filter_query = (
                select(TaskTag.task_id)
                .where(TaskTag.tag_id.in_(tag_ids))
                .distinct()
            )
            base_query = base_query.where(Todo.id.in_(tag_filter_query))
        
        # Apply due date range filter
        if due_date_from:
            base_query = base_query.where(Todo.due_date >= due_date_from)
        if due_date_to:
            base_query = base_query.where(Todo.due_date <= due_date_to)
        
        # Get total count before pagination
        count_query = select(func.count()).select_from(base_query.subquery())
        total = self.session.exec(count_query).one()
        
        # Apply sorting
        base_query = self._apply_sorting(base_query, sort_by, sort_order)
        
        # Apply pagination
        offset = (page - 1) * limit
        base_query = base_query.offset(offset).limit(limit)
        
        # Execute query
        tasks = self.session.exec(base_query).all()
        
        # Load tags for each task
        for task in tasks:
            self.session.refresh(task, ["tags"])
        
        # Calculate total pages
        total_pages = (total + limit - 1) // limit if total > 0 else 1
        
        return {
            "tasks": tasks,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }
    
    def _apply_sorting(self, query, sort_by: str, sort_order: str):
        """Apply sorting to query."""
        from sqlalchemy import case
        
        logger.debug(f"Applying sort: sort_by={sort_by}, sort_order={sort_order}")
        
        # Determine sort direction
        if sort_order.lower() == "asc":
            if sort_by == "due_date":
                query = query.order_by(Todo.due_date.asc())
            elif sort_by == "priority":
                # Custom ordering: low=1, medium=2, high=3
                query = query.order_by(
                    case(
                        (Todo.priority == PriorityEnum.low, 1),
                        (Todo.priority == PriorityEnum.medium, 2),
                        (Todo.priority == PriorityEnum.high, 3),
                    ).asc()
                )
            elif sort_by == "title":
                query = query.order_by(Todo.title.asc())
            else:  # created_at
                query = query.order_by(Todo.created_at.asc())
        else:  # desc
            if sort_by == "due_date":
                query = query.order_by(Todo.due_date.desc())
            elif sort_by == "priority":
                # Custom ordering: high=1, medium=2, low=3
                query = query.order_by(
                    case(
                        (Todo.priority == PriorityEnum.high, 1),
                        (Todo.priority == PriorityEnum.medium, 2),
                        (Todo.priority == PriorityEnum.low, 3),
                    ).desc()
                )
            elif sort_by == "title":
                query = query.order_by(Todo.title.desc())
            else:  # created_at
                query = query.order_by(Todo.created_at.desc())
        
        return query
    
    def search_with_ranking(
        self,
        user_id: int,
        query: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search tasks with relevance ranking.
        
        Args:
            user_id: User ID
            query: Search query
            limit: Maximum results to return
        
        Returns:
            List of tasks with relevance scores
        """
        # Full-text search with ranking
        ranking_query = text("""
            SELECT 
                todos.*,
                ts_rank(
                    to_tsvector('english', title || ' ' || COALESCE(description, '')),
                    plainto_tsquery(:query)
                ) as rank
            FROM todos
            WHERE todos.user_id = :user_id
              AND to_tsvector('english', title || ' ' || COALESCE(description, '')) @@ plainto_tsquery(:query)
            ORDER BY rank DESC
            LIMIT :limit
        """)
        
        results = self.session.execute(
            ranking_query,
            {"user_id": user_id, "query": query, "limit": limit}
        )
        
        tasks_with_rank = []
        for row in results:
            task = row[0]
            rank = row[1]
            tasks_with_rank.append({
                "task": task,
                "rank": rank
            })
        
        return tasks_with_rank
    
    def get_search_suggestions(
        self,
        user_id: int,
        prefix: str,
        limit: int = 5
    ) -> Dict[str, List[str]]:
        """
        Get search suggestions based on prefix.
        
        Args:
            user_id: User ID
            prefix: Search prefix
            limit: Maximum suggestions per category
        
        Returns:
            Dict with suggestion categories
        """
        # Get matching task titles
        title_query = select(Todo.title).where(
            (Todo.user_id == user_id) &
            (Todo.title.ilike(f"{prefix}%"))
        ).limit(limit)
        
        titles = self.session.exec(title_query).all()
        
        # Get matching tags
        tag_query = select(Tag.name).where(
            (Tag.user_id == user_id) &
            (Tag.name.ilike(f"{prefix}%"))
        ).limit(limit)
        
        tags = self.session.exec(tag_query).all()
        
        return {
            "titles": list(titles),
            "tags": list(tags)
        }


def get_search_service(session: Session) -> SearchService:
    """Get a SearchService instance."""
    return SearchService(session)
