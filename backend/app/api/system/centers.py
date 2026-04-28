"""System Admin API routes for managing centers."""

from uuid import UUID

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession, require_superadmin
from app.crud.center import list_centers, patch_center
from app.schemas.center import CenterCreate, CenterListItem, CreateCenterResponse
from app.services.center_service import create_center_with_admin

router = APIRouter(prefix="/system/centers", tags=["System Admin"])


@router.get("", response_model=list[CenterListItem])
async def get_centers(
    db: DbSession,
    current_user: CurrentUser,
    search: str | None = Query(None, max_length=100),
    is_active: bool | None = None,
):
    """List all registered edu-centers. Superadmin only."""
    require_superadmin(current_user)
    return await list_centers(db, search, is_active)


@router.post("", response_model=CreateCenterResponse)
async def create_new_center(
    data: CenterCreate,
    db: DbSession,
    current_user: CurrentUser,
):
    """Register a new center and provision its admin user. Superadmin only."""
    require_superadmin(current_user)
    center_dict, credentials = await create_center_with_admin(
        db=db,
        center_name=data.name,
        admin_full_name=data.admin_full_name,
        admin_username=data.admin_username,
        admin_email=data.admin_email,
        registered_by_id=current_user.id,
    )
    return {"center": center_dict, "admin_credentials": credentials}


@router.patch("/{center_id}")
async def update_center(
    center_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    is_active: bool,
):
    """Activate or deactivate a center. Superadmin only."""
    require_superadmin(current_user)
    center = await patch_center(db, center_id, is_active=is_active)
    if not center:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Center not found")
    return {"id": center.id, "is_active": center.is_active}
