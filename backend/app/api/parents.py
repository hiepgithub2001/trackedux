"""Parent API routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, DbSession
from app.crud.parent import create_parent, get_parent_by_id, list_parents, update_parent
from app.schemas.parent import ParentCreate, ParentResponse, ParentUpdate

router = APIRouter(prefix="/parents", tags=["Parents"])


@router.get("", response_model=list[ParentResponse])
async def get_parents(db: DbSession, current_user: CurrentUser):
    """List all parents. Admin only."""
    if current_user.role not in ("admin",):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    parents = await list_parents(db)
    return [ParentResponse.model_validate(p) for p in parents]


@router.get("/{parent_id}", response_model=ParentResponse)
async def get_parent(parent_id: UUID, db: DbSession, current_user: CurrentUser):
    """Get parent detail. Admin only."""
    if current_user.role not in ("admin",):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    parent = await get_parent_by_id(db, parent_id)
    if parent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent not found")
    return ParentResponse.model_validate(parent)


@router.post("", response_model=ParentResponse, status_code=status.HTTP_201_CREATED)
async def create_parent_endpoint(data: ParentCreate, db: DbSession, current_user: CurrentUser):
    """Create a new parent. Admin only."""
    if current_user.role not in ("admin",):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    parent = await create_parent(db, data)
    return ParentResponse.model_validate(parent)


@router.patch("/{parent_id}", response_model=ParentResponse)
async def update_parent_endpoint(parent_id: UUID, data: ParentUpdate, db: DbSession, current_user: CurrentUser):
    """Update parent fields. Admin only."""
    if current_user.role not in ("admin",):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    parent = await update_parent(db, parent_id, data)
    if parent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent not found")
    return ParentResponse.model_validate(parent)
