"""CRUD operations for the Lesson entity and LessonOccurrence overrides."""

from __future__ import annotations

import uuid
from datetime import date, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson import Lesson
from app.models.lesson_occurrence import LessonOccurrence
from app.schemas.lesson import LessonCreate, LessonSeriesUpdate, OccurrenceOverrideRequest
from app.services.recurrence_service import parse_rrule_day


async def create_lesson(
    db: AsyncSession, data: LessonCreate, center_id: uuid.UUID
) -> Lesson:
    """Create a new lesson (one-off or recurring)."""
    st = time.fromisoformat(data.start_time)
    day_of_week = None
    if data.rrule:
        day_of_week = parse_rrule_day(data.rrule)

    lesson = Lesson(
        class_id=data.class_id,
        teacher_id=data.teacher_id,
        title=data.title,
        start_time=st,
        duration_minutes=data.duration_minutes,
        day_of_week=day_of_week,
        specific_date=data.specific_date,
        rrule=data.rrule,
        center_id=center_id,
    )
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)
    return lesson


async def get_lesson_by_id(
    db: AsyncSession, lesson_id: uuid.UUID, center_id: uuid.UUID
) -> Lesson | None:
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id, Lesson.center_id == center_id)
    )
    return result.scalar_one_or_none()


async def list_lessons(
    db: AsyncSession,
    center_id: uuid.UUID,
    class_id: uuid.UUID | None = None,
    teacher_id: uuid.UUID | None = None,
    is_active: bool = True,
) -> list[Lesson]:
    q = select(Lesson).where(Lesson.center_id == center_id)
    if class_id is not None:
        q = q.where(Lesson.class_id == class_id)
    if teacher_id is not None:
        q = q.where(Lesson.teacher_id == teacher_id)
    if is_active is not None:
        q = q.where(Lesson.is_active == is_active)
    result = await db.execute(q)
    return list(result.scalars().all())


async def update_lesson_series(
    db: AsyncSession, lesson_id: uuid.UUID, data: LessonSeriesUpdate, center_id: uuid.UUID
) -> Lesson | None:
    """Update the series-level fields of a recurring lesson.

    CRITICAL: Does NOT touch any LessonOccurrence records.
    Persisted overrides (attendance, cancel, reschedule) always win over the new rule.
    """
    lesson = await get_lesson_by_id(db, lesson_id, center_id)
    if lesson is None:
        return None

    if data.start_time is not None:
        new_start_time = time.fromisoformat(data.start_time)
        if new_start_time != lesson.start_time:
            from datetime import date

            from sqlalchemy import update
            today = date.today()
            # Freeze the old start_time for past occurrences so they don't inherit the new time
            stmt = (
                update(LessonOccurrence)
                .where(
                    LessonOccurrence.lesson_id == lesson_id,
                    LessonOccurrence.center_id == center_id,
                    LessonOccurrence.override_start_time.is_(None),
                    LessonOccurrence.original_date < today
                )
                .values(override_start_time=lesson.start_time)
            )
            await db.execute(stmt)
            lesson.start_time = new_start_time
    if data.duration_minutes is not None:
        lesson.duration_minutes = data.duration_minutes
    if data.title is not None:
        lesson.title = data.title
    if data.rrule is not None:
        lesson.rrule = data.rrule
        lesson.day_of_week = parse_rrule_day(data.rrule)
    if data.teacher_id is not None:
        lesson.teacher_id = data.teacher_id
    if data.specific_date is not None:
        lesson.specific_date = data.specific_date

    await db.commit()
    await db.refresh(lesson)
    return lesson


async def deactivate_lesson(
    db: AsyncSession, lesson_id: uuid.UUID, center_id: uuid.UUID
) -> bool:
    lesson = await get_lesson_by_id(db, lesson_id, center_id)
    if lesson is None:
        return False
    lesson.is_active = False
    await db.commit()
    return True


async def get_occurrence(
    db: AsyncSession, lesson_id: uuid.UUID, original_date: date, center_id: uuid.UUID
) -> LessonOccurrence | None:
    result = await db.execute(
        select(LessonOccurrence).where(
            LessonOccurrence.lesson_id == lesson_id,
            LessonOccurrence.original_date == original_date,
            LessonOccurrence.center_id == center_id,
        )
    )
    return result.scalar_one_or_none()


async def upsert_occurrence(
    db: AsyncSession,
    lesson_id: uuid.UUID,
    original_date: date,
    data: OccurrenceOverrideRequest,
    center_id: uuid.UUID,
) -> LessonOccurrence:
    """Create or update a LessonOccurrence override record."""
    occ = await get_occurrence(db, lesson_id, original_date, center_id)

    if data.action == "revert":
        if occ is not None:
            occ.status = "active"
            occ.override_date = None
            occ.override_start_time = None
            await db.commit()
            await db.refresh(occ)
        else:
            # Nothing to revert — create a clean active record
            occ = LessonOccurrence(
                lesson_id=lesson_id,
                original_date=original_date,
                status="active",
                center_id=center_id,
            )
            db.add(occ)
            await db.commit()
            await db.refresh(occ)
        return occ

    if occ is None:
        occ = LessonOccurrence(
            lesson_id=lesson_id,
            original_date=original_date,
            center_id=center_id,
        )
        db.add(occ)

    if data.action == "cancel":
        occ.status = "canceled"
        occ.override_date = None
        occ.override_start_time = None
    elif data.action == "reschedule":
        occ.status = "active"
        occ.override_date = data.override_date
        if data.override_start_time:
            occ.override_start_time = time.fromisoformat(data.override_start_time)
        else:
            occ.override_start_time = None

    await db.commit()
    await db.refresh(occ)
    return occ


async def load_overrides_for_week(
    db: AsyncSession,
    lesson_ids: list[uuid.UUID],
    week_start: date,
    week_end: date,
    center_id: uuid.UUID,
) -> dict[tuple[str, date], LessonOccurrence]:
    """Load all LessonOccurrence records relevant to a week into a lookup dict.

    Includes occurrences whose original_date or override_date falls within the week
    (± 7 days buffer for rescheduled occurrences).
    """
    from datetime import timedelta

    if not lesson_ids:
        return {}

    result = await db.execute(
        select(LessonOccurrence).where(
            LessonOccurrence.lesson_id.in_(lesson_ids),
            LessonOccurrence.center_id == center_id,
            # Load occurrences from surrounding weeks too (catches reschedules)
            LessonOccurrence.original_date >= week_start - timedelta(days=7),
            LessonOccurrence.original_date <= week_end + timedelta(days=7),
        )
    )
    occurrences = result.scalars().all()
    return {(str(o.lesson_id), o.original_date): o for o in occurrences}


async def load_all_overrides(
    db: AsyncSession,
    lesson_ids: list[uuid.UUID],
    center_id: uuid.UUID,
) -> dict[tuple[str, date], LessonOccurrence]:
    """Load every persisted LessonOccurrence for the given lessons (no date filter)."""
    if not lesson_ids:
        return {}
    result = await db.execute(
        select(LessonOccurrence).where(
            LessonOccurrence.lesson_id.in_(lesson_ids),
            LessonOccurrence.center_id == center_id,
        )
    )
    occurrences = result.scalars().all()
    return {(str(o.lesson_id), o.original_date): o for o in occurrences}


async def bulk_upsert_occurrences(
    db: AsyncSession,
    lessons: list[Lesson],
    range_start: date,
    range_end: date,
    center_id: uuid.UUID,
) -> int:
    """Materialize RRULE-derived occurrences as DB rows for an arbitrary date range.

    Caller decides is_active filtering — this helper materializes whatever
    lessons are passed in.  Existing rows are preserved via ON CONFLICT DO NOTHING.

    Returns the number of rows actually inserted (for observability).
    """
    from datetime import datetime as dt_cls

    from dateutil.rrule import rrulestr
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from app.services.recurrence_service import _find_dtstart

    rows: list[dict] = []
    for lesson in lessons:
        if lesson.specific_date is not None:
            if range_start <= lesson.specific_date <= range_end:
                rows.append({
                    "lesson_id": lesson.id,
                    "original_date": lesson.specific_date,
                    "status": "active",
                    "center_id": center_id,
                })
        elif lesson.rrule:
            dtstart = _find_dtstart(lesson)
            try:
                rule = rrulestr(lesson.rrule, dtstart=dtstart, ignoretz=True)
            except Exception:
                continue
            expanded = rule.between(
                dt_cls.combine(range_start, dt_cls.min.time()),
                dt_cls.combine(range_end, dt_cls.max.time()),
                inc=True,
            )
            for d in expanded:
                rows.append({
                    "lesson_id": lesson.id,
                    "original_date": d.date(),
                    "status": "active",
                    "center_id": center_id,
                })

    if not rows:
        return 0

    stmt = (
        pg_insert(LessonOccurrence)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["lesson_id", "original_date"])
    )
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount  # type: ignore[return-value]


async def cleanup_future_ghosts(
    db: AsyncSession,
    lesson_id: uuid.UUID,
    center_id: uuid.UUID,
) -> int:
    """Delete clean future LessonOccurrence rows for a lesson (ghost cleanup).

    Called after an RRULE edit to re-align future occurrences to the new rule.
    Preserves: past rows, canceled rows, rescheduled rows, time-overridden rows,
    and rows with attendance records.

    Returns the number of rows deleted.
    """
    from sqlalchemy import delete, exists

    from app.models.attendance import AttendanceRecord

    today = date.today()
    stmt = (
        delete(LessonOccurrence)
        .where(
            LessonOccurrence.lesson_id == lesson_id,
            LessonOccurrence.center_id == center_id,
            LessonOccurrence.original_date >= today,
            LessonOccurrence.status == "active",
            LessonOccurrence.override_date.is_(None),
            LessonOccurrence.override_start_time.is_(None),
            ~exists(
                select(AttendanceRecord.id).where(
                    AttendanceRecord.lesson_occurrence_id == LessonOccurrence.id,
                )
            ),
        )
    )
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount  # type: ignore[return-value]

