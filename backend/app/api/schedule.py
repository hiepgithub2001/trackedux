"""Schedule API route — weekly calendar data."""

from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession, get_center_id
from app.crud.class_session import list_class_sessions
from app.schemas.class_session import _derive_end_time

router = APIRouter(prefix="/schedule", tags=["Schedule"])


@router.get("/weekly")
async def get_weekly_schedule(
    db: DbSession,
    current_user: CurrentUser,
    week_start: date | None = None,
    teacher_id: UUID | None = None,
):
    """Get weekly calendar view data, scoped to current user's center."""
    center_id = get_center_id(current_user)

    if week_start is None:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())  # Monday

    week_end = week_start + timedelta(days=6)

    classes = await list_class_sessions(db, center_id=center_id, teacher_id=teacher_id)

    sessions = []
    for cs in classes:
        session_date = week_start + timedelta(days=cs.day_of_week)
        start_str = cs.start_time.strftime("%H:%M")
        sessions.append(
            {
                "id": str(cs.id),
                "name": cs.name,
                "teacher": {
                    "id": str(cs.teacher.id) if cs.teacher else None,
                    "full_name": cs.teacher.full_name if cs.teacher else "Unknown",
                    "color": cs.teacher.color if cs.teacher else None,
                },
                "students": [
                    {"id": str(e.student_id), "name": e.student.name if e.student else ""}
                    for e in (cs.enrollments or [])
                    if e.is_active
                ],
                "day_of_week": cs.day_of_week,
                "start_time": start_str,
                "duration_minutes": cs.duration_minutes,
                "end_time": _derive_end_time(start_str, cs.duration_minutes),
                "date": session_date.isoformat(),
                "is_makeup": cs.is_makeup,
                "attendance_marked": False,
            }
        )

    return {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "sessions": sessions,
    }
