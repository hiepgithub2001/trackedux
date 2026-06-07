"""CRUD operations for the Class entity."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.class_ import Class
from app.models.class_enrollment import ClassEnrollment
from app.schemas.class_ import ClassCreate, ClassUpdate


async def create_class(db: AsyncSession, data: ClassCreate, center_id: uuid.UUID) -> Class:
    """Create a new class and enroll initial students."""
    class_ = Class(
        name=data.name,
        teacher_id=data.teacher_id,
        tuition_fee_per_lesson=data.tuition_fee_per_lesson,
        lesson_kind_id=data.lesson_kind_id,
        center_id=center_id,
    )
    db.add(class_)
    await db.flush()  # get class_.id

    for student_id in data.student_ids:
        enrollment = ClassEnrollment(
            class_id=class_.id,
            student_id=student_id,
            center_id=center_id,
        )
        db.add(enrollment)

    await db.commit()
    await db.refresh(class_)
    return class_


async def get_class_by_id(db: AsyncSession, class_id: uuid.UUID, center_id: uuid.UUID) -> Class | None:
    result = await db.execute(select(Class).where(Class.id == class_id, Class.center_id == center_id))
    return result.scalar_one_or_none()


async def list_classes(
    db: AsyncSession,
    center_id: uuid.UUID,
    teacher_id: uuid.UUID | None = None,
    is_active: bool = True,
) -> list[Class]:
    q = select(Class).where(Class.center_id == center_id)
    if teacher_id is not None:
        q = q.where(Class.teacher_id == teacher_id)
    if is_active is not None:
        q = q.where(Class.is_active == is_active)
    result = await db.execute(q)
    return list(result.scalars().all())


async def update_class(db: AsyncSession, class_id: uuid.UUID, data: ClassUpdate, center_id: uuid.UUID) -> Class | None:
    class_ = await get_class_by_id(db, class_id, center_id)
    if class_ is None:
        return None
    update_data = data.model_dump(exclude_unset=True)
    student_ids = update_data.pop("student_ids", None)
    # lesson_kind_name is not on the ORM model, so we must not pass it to setattr
    update_data.pop("lesson_kind_name", None)

    for field, value in update_data.items():
        setattr(class_, field, value)

    if student_ids is not None:
        from datetime import date

        from sqlalchemy import select

        from app.models.class_enrollment import ClassEnrollment

        # 1. Unenroll students not in student_ids
        result = await db.execute(
            select(ClassEnrollment).where(
                ClassEnrollment.class_id == class_id,
                ClassEnrollment.center_id == center_id,
                ClassEnrollment.is_active,
            )
        )
        current_enrollments = result.scalars().all()
        current_ids = {e.student_id for e in current_enrollments}

        target_ids = set(student_ids)

        to_unenroll = current_ids - target_ids
        to_enroll = target_ids - current_ids

        for e in current_enrollments:
            if e.student_id in to_unenroll:
                e.is_active = False
                e.unenrolled_at = date.today()

        # 2. Enroll new students
        for sid in to_enroll:
            result = await db.execute(
                select(ClassEnrollment).where(
                    ClassEnrollment.class_id == class_id,
                    ClassEnrollment.student_id == sid,
                    ClassEnrollment.center_id == center_id,
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                existing.is_active = True
                existing.enrolled_since = date.today()
                existing.unenrolled_at = None
            else:
                new_e = ClassEnrollment(
                    class_id=class_id,
                    student_id=sid,
                    center_id=center_id,
                    enrolled_since=date.today(),
                )
                db.add(new_e)

    await db.commit()
    await db.refresh(class_)
    return class_

async def delete_class_completely(db: AsyncSession, class_id: uuid.UUID, center_id: uuid.UUID) -> bool:
    class_ = await get_class_by_id(db, class_id, center_id)
    if class_ is None:
        return False

    import re
    from datetime import date

    from sqlalchemy import delete, or_, select

    from app.models.attendance import AttendanceRecord
    from app.models.lesson import Lesson
    from app.models.lesson_occurrence import LessonOccurrence

    today = date.today()

    # Get lesson ids
    lesson_res = await db.execute(select(Lesson).where(Lesson.class_id == class_id))
    lessons = list(lesson_res.scalars().all())

    if lessons:
        lesson_ids = [lesson_obj.id for lesson_obj in lessons]

        # 1. Delete future occurrences and their attendance
        occ_res = await db.execute(
            select(LessonOccurrence).where(
                LessonOccurrence.lesson_id.in_(lesson_ids),
                or_(
                    LessonOccurrence.original_date > today,
                    LessonOccurrence.override_date > today
                )
            )
        )
        future_occs = list(occ_res.scalars().all())
        if future_occs:
            future_occ_ids = [o.id for o in future_occs]
            # Delete attendance records
            await db.execute(
                delete(AttendanceRecord).where(AttendanceRecord.lesson_occurrence_id.in_(future_occ_ids))
            )
            # Delete lesson occurrences
            await db.execute(
                delete(LessonOccurrence).where(LessonOccurrence.id.in_(future_occ_ids))
            )

        # 2. Update recurring lessons to end today, delete future one-off lessons
        for lesson in lessons:
            if lesson.specific_date and lesson.specific_date > today:
                await db.execute(delete(Lesson).where(Lesson.id == lesson.id))
            elif lesson.rrule:
                # Add or update UNTIL clause in RRULE
                # Format: UNTIL=YYYYMMDD
                until_str = today.strftime("UNTIL=%Y%m%d")
                if "UNTIL=" in lesson.rrule:
                    lesson.rrule = re.sub(r"UNTIL=\d{8}(T\d{6}Z)?", until_str, lesson.rrule)
                else:
                    lesson.rrule += f";{until_str}"

                # if the lesson was created recently and all occurrences are now in the future or not started,
                # the rrule just stops. The lesson definition stays for history.

    # Soft delete the class
    class_.is_active = False

    await db.commit()
    return True

async def enroll_student(
    db: AsyncSession,
    class_id: uuid.UUID,
    student_id: uuid.UUID,
    center_id: uuid.UUID,
    enrolled_since: date | None = None,
) -> ClassEnrollment:
    # Check if already enrolled
    result = await db.execute(
        select(ClassEnrollment).where(
            ClassEnrollment.class_id == class_id,
            ClassEnrollment.student_id == student_id,
            ClassEnrollment.center_id == center_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        existing.is_active = True
        existing.enrolled_since = enrolled_since
        existing.unenrolled_at = None
        await db.commit()
        return existing

    enrollment = ClassEnrollment(
        class_id=class_id,
        student_id=student_id,
        center_id=center_id,
        enrolled_since=enrolled_since,
    )
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)
    return enrollment


async def unenroll_student(
    db: AsyncSession,
    class_id: uuid.UUID,
    student_id: uuid.UUID,
    center_id: uuid.UUID,
    unenrolled_at: date | None = None,
) -> bool:
    result = await db.execute(
        select(ClassEnrollment).where(
            ClassEnrollment.class_id == class_id,
            ClassEnrollment.student_id == student_id,
            ClassEnrollment.center_id == center_id,
        )
    )
    enrollment = result.scalar_one_or_none()
    if enrollment is None:
        return False
    enrollment.is_active = False
    enrollment.unenrolled_at = unenrolled_at
    await db.commit()
    return True
