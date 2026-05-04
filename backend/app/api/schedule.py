"""Schedule API route — weekly calendar data using Lesson + recurrence expansion."""

from datetime import date, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, DbSession, get_center_id
from app.crud.lesson import list_lessons, load_overrides_for_week
from app.models.attendance import AttendanceRecord
from app.models.lesson import Lesson
from app.services.recurrence_service import (
    VirtualOccurrence,
    _build_occurrence,
    compute_week_occurrences,
)

router = APIRouter(prefix="/schedule", tags=["Schedule"])


def _format_time(t) -> str:
    if t is None:
        return ""
    return t.strftime("%H:%M")


def _derive_end_time(start: str, duration: int) -> str:
    dt = datetime.strptime(start, "%H:%M")
    from datetime import timedelta as td

    return (dt + td(minutes=duration)).strftime("%H:%M")


async def _build_session_dicts(
    db: AsyncSession,
    occurrences: list[VirtualOccurrence],
    lesson_map: dict[str, Lesson],
    center_id: UUID,
) -> list[dict]:
    """Build attendance-page session dicts, including attendance_marked state.

    Bulk-queries AttendanceRecord rows for occurrences that have a persisted
    LessonOccurrence id, then assembles the response dict matching the shape
    expected by the schedule UI.
    """
    occ_id_to_key: dict[UUID, tuple[str, str]] = {}
    for occ in occurrences:
        if occ.occurrence_id:
            occ_id_to_key[UUID(occ.occurrence_id)] = (
                occ.lesson_id,
                occ.original_date.isoformat(),
            )

    marked_set: set[tuple[str, str]] = set()
    if occ_id_to_key:
        count_result = await db.execute(
            select(AttendanceRecord.lesson_occurrence_id, func.count())
            .where(
                AttendanceRecord.lesson_occurrence_id.in_(list(occ_id_to_key.keys())),
                AttendanceRecord.center_id == center_id,
            )
            .group_by(AttendanceRecord.lesson_occurrence_id)
        )
        for occ_id, cnt in count_result.all():
            if cnt > 0 and occ_id in occ_id_to_key:
                marked_set.add(occ_id_to_key[occ_id])

    sessions = []
    for occ in occurrences:
        lesson = lesson_map.get(occ.lesson_id)
        if lesson is None:
            continue

        start_str = _format_time(occ.start_time)
        effective_date_iso = occ.effective_date.isoformat()
        original_date_iso = occ.original_date.isoformat()
        is_marked = (occ.lesson_id, original_date_iso) in marked_set

        students = []
        if lesson.class_ and lesson.class_.enrollments:
            for e in lesson.class_.enrollments:
                if not e.is_active:
                    continue
                if e.enrolled_since and occ.effective_date < e.enrolled_since:
                    continue
                if e.unenrolled_at and occ.effective_date >= e.unenrolled_at:
                    continue
                students.append(
                    {
                        "id": str(e.student_id),
                        "name": e.student.name if e.student else "",
                    }
                )

        sessions.append(
            {
                "id": occ.lesson_id,
                "occurrence_id": occ.occurrence_id,
                "lesson_id": occ.lesson_id,
                "class_id": occ.class_id,
                "name": occ.lesson_name,
                "teacher": {
                    "id": str(lesson.teacher_id),
                    "full_name": lesson.teacher.full_name if lesson.teacher else "Unknown",
                    "color": lesson.teacher.color if lesson.teacher else None,
                },
                "students": students,
                "day_of_week": occ.effective_date.weekday(),
                "start_time": start_str,
                "duration_minutes": occ.duration_minutes,
                "end_time": _derive_end_time(start_str, occ.duration_minutes),
                "date": effective_date_iso,
                "original_date": original_date_iso,
                "is_canceled": occ.is_canceled,
                "is_rescheduled": occ.is_rescheduled,
                "is_recurring": lesson.rrule is not None,
                "is_makeup": lesson.specific_date is not None,
                "attendance_marked": is_marked,
            }
        )

    return sessions


@router.get("/weekly")
async def get_weekly_schedule(
    db: DbSession,
    current_user: CurrentUser,
    week_start: date | None = None,
    teacher_id: UUID | None = None,
):
    """Get weekly calendar view data using the unified read model (Past=DB, Future=RRULE)."""
    center_id = get_center_id(current_user)
    today = date.today()

    if week_start is None:
        week_start = today - timedelta(days=today.weekday())  # Monday

    week_end = week_start + timedelta(days=6)

    # 1. Load all lessons so lesson_map contains inactive ones for the past
    lessons = await list_lessons(db, center_id=center_id, teacher_id=teacher_id, is_active=None)
    if not lessons:
        return {"week_start": week_start.isoformat(), "week_end": week_end.isoformat(), "sessions": []}

    lesson_map = {str(lesson.id): lesson for lesson in lessons}

    # 2. Past portion (effective_date < today)
    from app.crud.lesson import bulk_upsert_occurrences
    from app.models.lesson_occurrence import LessonOccurrence

    if week_start < today:
        # Materialize any unmaterialized past occurrences for the requested week
        past_range_end = min(week_end, today - timedelta(days=1))
        await bulk_upsert_occurrences(db, lessons, week_start, past_range_end, center_id)
        await db.commit()

    result = await db.execute(
        select(LessonOccurrence).where(
            LessonOccurrence.lesson_id.in_([lesson_obj.id for lesson_obj in lessons]),
            LessonOccurrence.center_id == center_id,
            func.coalesce(LessonOccurrence.override_date, LessonOccurrence.original_date) >= week_start,
            func.coalesce(LessonOccurrence.override_date, LessonOccurrence.original_date) <= week_end,
            func.coalesce(LessonOccurrence.override_date, LessonOccurrence.original_date) < today,
        )
    )
    past_rows = result.scalars().all()

    virtual_occs = []
    for occ_row in past_rows:
        lesson = lesson_map.get(str(occ_row.lesson_id))
        if not lesson:
            continue
        class_name = lesson.class_.name if lesson.class_ else None
        display_name = lesson.title or class_name or ""
        teacher_id_str = str(lesson.teacher_id)

        v_occ = _build_occurrence(
            lesson, str(lesson.id), class_name, display_name, teacher_id_str, occ_row.original_date, occ_row
        )
        virtual_occs.append(v_occ)

    # 3. Future portion (effective_date >= today): expand RRULE for active lessons
    active_lessons = [lesson_obj for lesson_obj in lessons if lesson_obj.is_active]
    lesson_ids = [lesson_obj.id for lesson_obj in active_lessons]
    overrides = await load_overrides_for_week(db, lesson_ids, week_start, week_end, center_id)

    future_virtual_occs = compute_week_occurrences(active_lessons, overrides, week_start, week_end)

    # Only keep future occurrences
    for occ in future_virtual_occs:
        if occ.effective_date >= today:
            virtual_occs.append(occ)

    sessions = await _build_session_dicts(db, virtual_occs, lesson_map, center_id)

    return {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "sessions": sessions,
    }


@router.get("/past")
async def get_past_sessions(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = 5,
    offset: int = 0,
    teacher_id: UUID | None = None,
):
    """List all past lesson occurrences across history, sorted newest-first.

    Self-heals missing past rows by triggering a bulk upsert before query.
    """
    from app.crud.lesson import bulk_upsert_occurrences
    from app.models.lesson import Lesson
    from app.models.lesson_occurrence import LessonOccurrence

    center_id = get_center_id(current_user)
    today = date.today()

    lessons = await list_lessons(db, center_id=center_id, teacher_id=teacher_id, is_active=None)
    if not lessons:
        return {"sessions": [], "total": 0}

    lesson_map = {str(lesson.id): lesson for lesson in lessons}

    # 1. Self-heal materialization
    # Anchor at the oldest lesson created_at (or just pass each lesson to the helper
    # which uses its own created_at). The helper accepts a global range start.
    min_created_at = today
    for lesson_obj in lessons:
        l_created = (
            lesson_obj.created_at.date() if hasattr(lesson_obj, "created_at") and lesson_obj.created_at else today
        )
        # Go back slightly further to be safe, up to 5 years (dtstart uses -5 years previously, now exact)
        if l_created < min_created_at:
            min_created_at = l_created

    await bulk_upsert_occurrences(db, lessons, min_created_at, today - timedelta(days=1), center_id)

    # 2. Query materialized past rows
    base_query = select(LessonOccurrence).where(
        LessonOccurrence.lesson_id.in_([lesson_obj.id for lesson_obj in lessons]),
        LessonOccurrence.center_id == center_id,
        func.coalesce(LessonOccurrence.override_date, LessonOccurrence.original_date) < today,
        LessonOccurrence.status != "canceled",
    )

    total_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = total_result.scalar() or 0

    stmt = (
        base_query.join(Lesson, Lesson.id == LessonOccurrence.lesson_id)
        .order_by(
            func.coalesce(LessonOccurrence.override_date, LessonOccurrence.original_date).desc(),
            func.coalesce(LessonOccurrence.override_start_time, Lesson.start_time).desc(),
        )
        .limit(limit)
        .offset(offset)
    )

    occ_rows = (await db.execute(stmt)).scalars().all()

    virtual_occs = []
    for occ_row in occ_rows:
        lesson = lesson_map.get(str(occ_row.lesson_id))
        if not lesson:
            continue

        class_name = lesson.class_.name if lesson.class_ else None
        display_name = lesson.title or class_name or ""
        teacher_id_str = str(lesson.teacher_id)

        v_occ = _build_occurrence(
            lesson, str(lesson.id), class_name, display_name, teacher_id_str, occ_row.original_date, occ_row
        )
        virtual_occs.append(v_occ)

    sessions = await _build_session_dicts(db, virtual_occs, lesson_map, center_id)
    return {"sessions": sessions, "total": total}
