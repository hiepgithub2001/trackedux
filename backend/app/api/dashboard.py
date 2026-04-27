"""Dashboard API route."""
from fastapi import APIRouter
from app.core.deps import CurrentUser, DbSession
from app.services.dashboard_service import get_dashboard_metrics

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("")
async def get_dashboard(db: DbSession, current_user: CurrentUser):
    """Get dashboard metrics."""
    return await get_dashboard_metrics(db, current_user.role)
