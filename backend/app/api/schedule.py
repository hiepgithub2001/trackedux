"""Schedule API route — weekly calendar data."""

from datetime import date, timedelta

from fastapi import APIRouter, Query
from uuid import UUID

from app.core.deps import CurrentUser, DbSession
from app.crud.class_session import list_class_sessions

router = APIRouter(prefix="/schedule", tags=["Schedule"])


@router.get("/weekly")
async def get_weekly_schedule(
    db: DbSession,
    current_user: CurrentUser,
    week_start: date | None = None,
    teacher_id: UUID | None = None,
):
    """Get weekly calendar view data."""
    if week_start is None:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())  # Monday

    week_end = week_start + timedelta(days=6)

    classes = await list_class_sessions(db, teacher_id=teacher_id)

    sessions = []
    for cs in classes:
        session_date = week_start + timedelta(days=cs.day_of_week)
        sessions.append({
            "id": str(cs.id),
            "title": cs.title or f"{cs.class_type.capitalize()} Class",
            "class_type": cs.class_type,
            "teacher": {
                "id": str(cs.teacher.id) if cs.teacher else None,
                "full_name": cs.teacher.full_name if cs.teacher else "Unknown",
            },
            "students": [
                {"id": str(e.student_id), "name": e.student.name if e.student else ""}
                for e in (cs.enrollments or [])
                if e.is_active
            ],
            "day_of_week": cs.day_of_week,
            "start_time": cs.start_time.strftime("%H:%M"),
            "end_time": cs.end_time.strftime("%H:%M"),
            "date": session_date.isoformat(),
            "is_makeup": cs.is_makeup,
            "attendance_marked": False,
        })

    return {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "sessions": sessions,
    }
