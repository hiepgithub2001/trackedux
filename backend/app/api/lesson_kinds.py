"""Lesson Kind API routes — vocabulary listing."""

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession, get_center_id
from app.crud.lesson_kind import list_lesson_kinds

router = APIRouter(prefix="/lesson-kinds", tags=["Lesson Kinds"])


@router.get("")
async def get_lesson_kinds(
    db: DbSession,
    current_user: CurrentUser,
    search: str | None = Query(None, max_length=100),
):
    """List lesson kinds with optional case-insensitive search, scoped to center."""
    center_id = get_center_id(current_user)
    kinds = await list_lesson_kinds(db, center_id=center_id, search=search)
    return [{"id": str(k.id), "name": k.name, "created_at": k.created_at} for k in kinds]
