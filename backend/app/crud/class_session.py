"""ClassSession CRUD database operations."""

from datetime import time
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.class_enrollment import ClassEnrollment
from app.models.class_session import ClassSession
from app.models.package import Package
from app.schemas.class_session import ClassSessionCreate, ClassSessionUpdate
from app.crud.lesson_kind import find_or_create_lesson_kind

# ── Display ID utilities ──────────────────────────────────────────────

DAY_ABBR = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _display_id_key(cs: ClassSession) -> tuple[str, str, str]:
    """Return the grouping key for display ID disambiguation."""
    teacher_first = (cs.teacher.full_name or "").split()[0] if cs.teacher else "Unknown"
    day = DAY_ABBR[cs.day_of_week] if 0 <= cs.day_of_week <= 6 else "?"
    t = cs.start_time.strftime("%H%M") if cs.start_time else "0000"
    return (teacher_first, day, t)


def compute_display_ids(classes: list[ClassSession]) -> dict[UUID, str]:
    """Compute human-readable display IDs for a list of class sessions.

    Groups by (TeacherFirstName, Weekday3, HHMM) and assigns disambiguator
    suffix (-2, -3, …) for collisions, ordered by created_at.
    """
    from collections import defaultdict

    groups: dict[tuple, list[ClassSession]] = defaultdict(list)
    for cs in classes:
        groups[_display_id_key(cs)].append(cs)

    result: dict[UUID, str] = {}
    for key, members in groups.items():
        members.sort(key=lambda c: c.created_at)
        base = f"{key[0]}-{key[1]}-{key[2]}"
        for idx, cs in enumerate(members):
            if idx == 0:
                result[cs.id] = base
            else:
                result[cs.id] = f"{base}-{idx + 1}"
    return result


def compute_single_display_id(
    cs: ClassSession, all_classes: list[ClassSession]
) -> str:
    """Convenience: compute display ID for a single class against its peers."""
    ids = compute_display_ids(all_classes)
    return ids.get(cs.id, "Unknown")


# ── CRUD operations ───────────────────────────────────────────────────


async def create_class_session(db: AsyncSession, data: ClassSessionCreate, center_id: UUID) -> ClassSession:
    """Create a new class session scoped to a center."""
    lesson_kind_id = None
    if data.lesson_kind_name:
        lk = await find_or_create_lesson_kind(db, data.lesson_kind_name, center_id)
        lesson_kind_id = lk.id

    cs = ClassSession(
        teacher_id=data.teacher_id,
        name=data.name,
        day_of_week=data.day_of_week,
        start_time=time.fromisoformat(data.start_time),
        duration_minutes=data.duration_minutes,
        tuition_fee_per_lesson=data.tuition_fee_per_lesson,
        lesson_kind_id=lesson_kind_id,
        is_recurring=data.is_recurring,
        center_id=center_id,
    )
    db.add(cs)
    await db.flush()

    for student_id in data.student_ids:
        enrollment = ClassEnrollment(class_session_id=cs.id, student_id=student_id, center_id=center_id)
        db.add(enrollment)

    await db.commit()
    await db.refresh(cs)
    return cs


async def update_class_session(
    db: AsyncSession, class_id: UUID, data: ClassSessionUpdate, center_id: UUID
) -> ClassSession | None:
    """Update a class session's mutable fields, scoped to center."""
    cs = await get_class_session_by_id(db, class_id, center_id)
    if cs is None:
        return None

    student_ids = data.student_ids
    for field, value in data.model_dump(exclude_unset=True, exclude={"student_ids"}).items():
        if field == "start_time" and value is not None:
            setattr(cs, field, time.fromisoformat(value))
        elif field == "lesson_kind_name":
            if value:
                lk = await find_or_create_lesson_kind(db, value, center_id)
                cs.lesson_kind_id = lk.id
            else:
                cs.lesson_kind_id = None
        else:
            setattr(cs, field, value)

    if student_ids is not None:
        existing = {e.student_id: e for e in cs.enrollments}
        new_set = set(student_ids)

        for sid, e in existing.items():
            if sid not in new_set:
                e.is_active = False
            else:
                e.is_active = True

        for sid in new_set:
            if sid not in existing:
                db.add(ClassEnrollment(class_session_id=cs.id, student_id=sid, center_id=center_id))

    await db.commit()
    await db.refresh(cs, ["enrollments"])
    return cs


async def delete_class_session(db: AsyncSession, class_id: UUID) -> None:
    """Delete a class if no packages reference it (active or historical)."""
    cs = await get_class_session_by_id(db, class_id)
    if cs is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class not found"
        )

    # Check for referencing packages (any status)
    pkg_count = await db.execute(
        select(func.count()).where(Package.class_session_id == class_id)
    )
    if (pkg_count.scalar() or 0) > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete class with associated packages. Deactivate referencing packages first.",
        )

    await db.delete(cs)
    await db.commit()


async def get_class_session_by_id(db: AsyncSession, class_id: UUID, center_id: UUID | None = None) -> ClassSession | None:
    """Get class session by ID. If center_id provided, scope to that center."""
    query = (
        select(ClassSession)
        .options(
            selectinload(ClassSession.teacher),
            selectinload(ClassSession.enrollments).selectinload(ClassEnrollment.student),
            selectinload(ClassSession.lesson_kind)
        )
        .where(ClassSession.id == class_id)
    )
    if center_id is not None:
        query = query.where(ClassSession.center_id == center_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def list_class_sessions(
    db: AsyncSession,
    center_id: UUID | None = None,
    teacher_id: UUID | None = None,
    day_of_week: int | None = None,
    active_only: bool = True,
) -> list[ClassSession]:
    """List class sessions with filters, optionally scoped to a center."""
    query = select(ClassSession).options(
        selectinload(ClassSession.teacher),
        selectinload(ClassSession.enrollments).selectinload(ClassEnrollment.student),
        selectinload(ClassSession.lesson_kind)
    )
    if center_id is not None:
        query = query.where(ClassSession.center_id == center_id)
    if teacher_id:
        query = query.where(ClassSession.teacher_id == teacher_id)
    if day_of_week is not None:
        query = query.where(ClassSession.day_of_week == day_of_week)
    if active_only:
        query = query.where(ClassSession.is_active == True)  # noqa: E712

    query = query.order_by(ClassSession.day_of_week, ClassSession.start_time)
    result = await db.execute(query)
    return list(result.scalars().all())


async def enroll_student(db: AsyncSession, class_id: UUID, student_id: UUID, center_id: UUID) -> ClassEnrollment:
    """Add a student to a class session, scoped to center."""
    enrollment = ClassEnrollment(class_session_id=class_id, student_id=student_id, center_id=center_id)
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)
    return enrollment


async def unenroll_student(db: AsyncSession, class_id: UUID, student_id: UUID) -> bool:
    """Remove a student from a class session."""
    result = await db.execute(
        select(ClassEnrollment).where(
            ClassEnrollment.class_session_id == class_id,
            ClassEnrollment.student_id == student_id,
        )
    )
    enrollment = result.scalar_one_or_none()
    if enrollment:
        enrollment.is_active = False
        await db.commit()
        return True
    return False


async def get_active_enrollment_count(db: AsyncSession, class_id: UUID) -> int:
    """Count active enrollments for a class."""
    result = await db.execute(
        select(func.count()).where(
            ClassEnrollment.class_session_id == class_id,
            ClassEnrollment.is_active == True,  # noqa: E712
        )
    )
    return result.scalar() or 0
