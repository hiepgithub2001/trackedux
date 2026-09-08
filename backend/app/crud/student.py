"""Student CRUD database operations."""

from datetime import date
from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.attendance import AttendanceRecord
from app.models.class_ import Class
from app.models.class_enrollment import ClassEnrollment
from app.models.lesson import Lesson
from app.models.lesson_occurrence import LessonOccurrence
from app.models.student import Student
from app.models.student_status_history import StudentStatusHistory
from app.models.tuition_ledger_entry import TuitionLedgerEntry
from app.models.tuition_payment import TuitionPayment
from app.schemas.student import StudentCreate, StudentUpdate


async def create_student(db: AsyncSession, data: StudentCreate, center_id: UUID) -> Student:
    """Create a new student scoped to a center."""
    class_ids = data.class_ids or []
    student_data = data.model_dump(exclude={"class_ids"})

    if student_data.get("date_of_birth"):
        dob = student_data["date_of_birth"]
        today = date.today()
        student_data["age"] = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    student = Student(
        **student_data,
        enrolled_at=date.today(),
        center_id=center_id,
    )
    db.add(student)
    await db.flush()

    for cid in class_ids:
        db.add(ClassEnrollment(class_id=cid, student_id=student.id, center_id=center_id))

    await db.commit()
    await db.refresh(student, ["enrollments"])
    return student


async def get_student_by_id(db: AsyncSession, student_id: UUID, center_id: UUID) -> Student | None:
    """Get a student by ID, scoped to a center."""
    result = await db.execute(
        select(Student)
        .options(selectinload(Student.enrollments))
        .where(Student.id == student_id, Student.center_id == center_id)
    )
    return result.scalar_one_or_none()


async def list_students(
    db: AsyncSession,
    center_id: UUID,
    status: str | None = None,
    search: str | None = None,
    sort_by: str = "name",
    sort_order: str = "asc",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Student], int]:
    """List students with filtering, searching, sorting, and pagination — scoped to center."""
    query = select(Student).where(Student.center_id == center_id)

    # Filters
    if status:
        query = query.where(Student.enrollment_status == status)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                func.unaccent(Student.name).ilike(func.unaccent(search_term)),
                func.unaccent(Student.nickname).ilike(func.unaccent(search_term)),
            )
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Sorting
    sort_column = getattr(Student, sort_by, Student.name)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    students = list(result.scalars().all())

    return students, total


async def update_student(db: AsyncSession, student_id: UUID, data: StudentUpdate, center_id: UUID) -> Student | None:
    """Update student fields, scoped to center."""
    student = await get_student_by_id(db, student_id, center_id)
    if student is None:
        return None

    class_ids = data.class_ids
    update_data = data.model_dump(exclude_unset=True, exclude={"class_ids"})

    dob = update_data.get("date_of_birth", student.date_of_birth)
    if dob:
        today = date.today()
        update_data["age"] = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    elif "date_of_birth" in update_data and update_data["date_of_birth"] is None:
        update_data["age"] = None

    for field, value in update_data.items():
        setattr(student, field, value)

    if class_ids is not None:
        # Sync enrollments
        existing = {e.class_id: e for e in student.enrollments}
        new_set = set(class_ids)

        # Deactivate removed ones
        for cid, e in existing.items():
            if cid not in new_set:
                e.is_active = False
            else:
                e.is_active = True

        # Add new ones
        for cid in new_set:
            if cid not in existing:
                db.add(ClassEnrollment(class_id=cid, student_id=student.id, center_id=center_id))

    await db.commit()
    # Refresh to get updated enrollments
    await db.refresh(student, ["enrollments"])
    return student


async def _purge_emptied_classes(db: AsyncSession, class_ids: list[UUID], center_id: UUID) -> None:
    """Drop classes left with an empty roster, together with their schedule.

    A 1-1 class is named after its only student, so deleting that student leaves a
    class nobody attends whose lessons keep materializing occurrences — those show up
    forever in Pending attendance with 0 students. Anything still referenced by
    surviving history (an attendance record or a tuition ledger entry) is kept and the
    class is only deactivated, so another student's ledger is never rewritten.
    """
    for class_id in {cid for cid in class_ids if cid is not None}:
        remaining = await db.scalar(
            select(func.count())
            .select_from(ClassEnrollment)
            .where(ClassEnrollment.class_id == class_id)
        )
        if remaining:
            continue

        lesson_ids = list(
            (
                await db.execute(
                    select(Lesson.id).where(Lesson.class_id == class_id, Lesson.center_id == center_id)
                )
            )
            .scalars()
            .all()
        )

        kept_lesson_ids: set[UUID] = set()
        if lesson_ids:
            occurrences = list(
                (
                    await db.execute(
                        select(LessonOccurrence.id, LessonOccurrence.lesson_id).where(
                            LessonOccurrence.lesson_id.in_(lesson_ids)
                        )
                    )
                ).all()
            )
            occ_ids = [occ_id for occ_id, _ in occurrences]
            marked_occ_ids: set[UUID] = set()
            if occ_ids:
                marked_occ_ids = set(
                    (
                        await db.execute(
                            select(AttendanceRecord.lesson_occurrence_id).where(
                                AttendanceRecord.lesson_occurrence_id.in_(occ_ids)
                            )
                        )
                    )
                    .scalars()
                    .all()
                )

            removable_occ_ids = [occ_id for occ_id in occ_ids if occ_id not in marked_occ_ids]
            if removable_occ_ids:
                await db.execute(delete(LessonOccurrence).where(LessonOccurrence.id.in_(removable_occ_ids)))

            kept_lesson_ids = {lesson_id for occ_id, lesson_id in occurrences if occ_id in marked_occ_ids}
            kept_lesson_ids |= set(
                (
                    await db.execute(
                        select(TuitionLedgerEntry.lesson_id).where(TuitionLedgerEntry.lesson_id.in_(lesson_ids))
                    )
                )
                .scalars()
                .all()
            )

            deletable = [lesson_id for lesson_id in lesson_ids if lesson_id not in kept_lesson_ids]
            if deletable:
                await db.execute(delete(Lesson).where(Lesson.id.in_(deletable)))

        class_ = await db.get(Class, class_id)
        if class_ is None:
            continue
        if kept_lesson_ids:
            class_.is_active = False
        else:
            await db.delete(class_)


async def delete_student(db: AsyncSession, student_id: UUID, center_id: UUID) -> bool:
    """Delete a student and related enrollments/history. Returns False if blocked by other records."""
    student = await get_student_by_id(db, student_id, center_id)
    if not student:
        return False

    class_ids = [e.class_id for e in student.enrollments]

    try:
        await db.execute(delete(TuitionLedgerEntry).where(TuitionLedgerEntry.student_id == student_id))
        await db.execute(delete(TuitionPayment).where(TuitionPayment.student_id == student_id))
        await db.execute(delete(AttendanceRecord).where(AttendanceRecord.student_id == student_id))
        await db.execute(delete(StudentStatusHistory).where(StudentStatusHistory.student_id == student_id))
        await db.execute(delete(ClassEnrollment).where(ClassEnrollment.student_id == student_id))
        await db.delete(student)
        await db.flush()
        await _purge_emptied_classes(db, class_ids, center_id)
        await db.commit()
        return True
    except IntegrityError:
        await db.rollback()
        return False
