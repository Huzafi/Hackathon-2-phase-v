"""Tag API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from typing import Optional

from ..core.database import get_session
from ..dependencies.auth import get_current_user
from ..models.user import User
from ..schemas.tag import TagCreate, TagUpdate, TagResponse, TagListResponse
from ..services.tag_service import get_tag_service, TagService


router = APIRouter(prefix="/api/tags", tags=["Tags"])


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Create a new tag for the authenticated user.
    
    - Name is required (1-50 characters, alphanumeric + spaces + hyphens)
    - Color is optional (defaults to #3B82F6)
    - Name must be unique per user (case-insensitive)
    - User ID is automatically set from JWT token
    - Returns created tag with timestamp
    """
    tag_service = get_tag_service(session)
    
    try:
        tag = await tag_service.create_tag(
            name=tag_data.name,
            user_id=current_user.id,
            color=tag_data.color
        )
        return TagResponse.model_validate(tag)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=TagListResponse)
def list_tags(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page")
):
    """
    List all tags for the authenticated user.
    
    - Returns tags with task count for each tag
    - Only returns tags belonging to the authenticated user
    - User isolation enforced at query level
    - Supports pagination
    """
    tag_service = get_tag_service(session)
    
    result = tag_service.list_tags(
        user_id=current_user.id,
        page=page,
        limit=limit
    )
    
    return TagListResponse(
        tags=result["tags"],
        total=result["total"],
        page=result["page"],
        limit=result["limit"]
    )


@router.get("/{tag_id}", response_model=TagResponse)
def get_tag(
    tag_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get a specific tag by ID.
    
    - Requires authentication
    - Verifies ownership (403 if not owned by user)
    - Returns 404 if tag doesn't exist
    - Includes task count
    """
    tag_service = get_tag_service(session)
    
    try:
        tag = tag_service.get_tag(tag_id, current_user.id)
        return TagResponse.model_validate(tag)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with id {tag_id} not found"
        )


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: int,
    tag_data: TagUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Update a tag (full or partial update).
    
    - Requires authentication
    - Verifies ownership (403 if not owned by user)
    - Name must be unique per user (case-insensitive)
    - Color must be valid 6-digit hex code
    - Returns updated tag
    """
    tag_service = get_tag_service(session)
    
    try:
        tag = await tag_service.update_tag(
            tag_id=tag_id,
            user_id=current_user.id,
            name=tag_data.name,
            color=tag_data.color
        )
        return TagResponse.model_validate(tag)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with id {tag_id} not found"
        )


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Delete a tag.
    
    - Requires authentication
    - Verifies ownership (403 if not owned by user)
    - Does not delete associated tasks, only removes tag association
    - Returns 204 No Content on success
    """
    tag_service = get_tag_service(session)
    
    try:
        await tag_service.delete_tag(tag_id, current_user.id)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with id {tag_id} not found"
        )
    
    return None
