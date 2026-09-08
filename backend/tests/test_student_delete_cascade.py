"""Regression tests for the fallout of deleting a student.

Covers two bugs seen in production on the "vuthao" center:
  1. Deleting the only student of a 1-1 class ("Bình", "Diệp Anh (Noel)") left the
     class and its lessons behind, so their occurrences sat in Pending attendance
     forever showing "0 students".
  2. Pending attendance listed occurrences with an empty roster, which can never be
     marked and so never leave the list.
"""

from __future__ import annotations

from datetime import date, time, timedelta

import pytest
from sqlalchemy import select

pytestmark = pytest.mark.asyncio


async def _enroll(db_session, cls, student, center):
    from app.models.class_enrollment import ClassEnrollment

    e = ClassEnrollment(class_id=cls.id, student_id=student.id, center_id=center.id)
    db_session.add(e)
    await db_session.commit()
    return e


async def test_deleting_last_student_removes_the_emptied_class_and_lessons(
    client, login, make_center, make_admin, make_teacher, make_class, make_student, db_session
):
    from app.models.class_ import Class
    from app.models.lesson import Lesson

    center = await make_center()
    admin = await make_admin(center)
    teacher = await make_teacher(center)
    cls = await make_class(center, teacher, name="Bình")
    student = await make_student(center)
    await _enroll(db_session, cls, student, center)

    headers = await login(admin)
    resp = await client.delete(f"/api/v1/students/{student.id}", headers=headers)
    assert resp.status_code == 204, resp.text

    assert (await db_session.execute(select(Class).where(Class.id == cls.id))).scalar_one_or_none() is None
    assert (await db_session.execute(select(Lesson).where(Lesson.class_id == cls.id))).scalars().all() == []


async def test_deleting_one_student_keeps_a_class_others_still_attend(
    client, login, make_center, make_admin, make_teacher, make_class, make_student, db_session
):
    from app.models.class_ import Class
    from app.models.lesson import Lesson

    center = await make_center()
    admin = await make_admin(center)
    teacher = await make_teacher(center)
    cls = await make_class(center, teacher, name="Group")
    leaving = await make_student(center)
    staying = await make_student(center)
    await _enroll(db_session, cls, leaving, center)
    await _enroll(db_session, cls, staying, center)

    headers = await login(admin)
    resp = await client.delete(f"/api/v1/students/{leaving.id}", headers=headers)
    assert resp.status_code == 204, resp.text

    kept = (await db_session.execute(select(Class).where(Class.id == cls.id))).scalar_one()
    assert kept.is_active is True
    assert (await db_session.execute(select(Lesson).where(Lesson.class_id == cls.id))).scalars().all() != []


async def test_emptied_class_with_marked_history_is_deactivated_not_deleted(
    client, login, make_center, make_admin, make_teacher, make_class, make_student, db_session
):
    """Another student's attendance history must survive; the class is only deactivated."""
    from app.models.attendance import AttendanceRecord
    from app.models.class_ import Class
    from app.models.lesson import Lesson
    from app.models.lesson_occurrence import LessonOccurrence

    center = await make_center()
    admin = await make_admin(center)
    teacher = await make_teacher(center)
    cls = await make_class(center, teacher, name="Solo")
    student = await make_student(center)
    past_student = await make_student(center)  # attended before being unenrolled
    await _enroll(db_session, cls, student, center)

    lesson = (await db_session.execute(select(Lesson).where(Lesson.class_id == cls.id))).scalar_one()
    past = date.today() - timedelta(days=7)
    occ = LessonOccurrence(lesson_id=lesson.id, original_date=past, center_id=center.id)
    db_session.add(occ)
    await db_session.flush()
    db_session.add(
        AttendanceRecord(
            lesson_occurrence_id=occ.id,
            student_id=past_student.id,
            session_date=past,
            status="present",
            marked_by=admin.id,
            center_id=center.id,
        )
    )
    await db_session.commit()

    headers = await login(admin)
    resp = await client.delete(f"/api/v1/students/{student.id}", headers=headers)
    assert resp.status_code == 204, resp.text

    # The app wrote through its own session, so re-read past this session's identity map.
    kept = (
        await db_session.execute(
            select(Class).where(Class.id == cls.id).execution_options(populate_existing=True)
        )
    ).scalar_one()
    assert kept.is_active is False
    assert (await db_session.execute(select(Lesson).where(Lesson.id == lesson.id))).scalar_one_or_none() is not None
    assert (
        await db_session.execute(select(AttendanceRecord).where(AttendanceRecord.lesson_occurrence_id == occ.id))
    ).scalar_one_or_none() is not None


async def test_pending_attendance_hides_occurrences_with_an_empty_roster(
    client, login, make_center, make_admin, make_teacher, make_class, make_student, db_session
):
    from app.models.class_ import Class
    from app.models.lesson import Lesson

    center = await make_center()
    admin = await make_admin(center)
    teacher = await make_teacher(center)
    yesterday = date.today() - timedelta(days=1)

    # A one-off makeup lesson whose class has nobody enrolled at all.
    orphan_class = Class(name="học bù", teacher_id=teacher.id, center_id=center.id)
    db_session.add(orphan_class)
    await db_session.flush()
    db_session.add(
        Lesson(
            class_id=orphan_class.id,
            teacher_id=teacher.id,
            start_time=time(12, 0),
            duration_minutes=60,
            specific_date=yesterday,
            center_id=center.id,
        )
    )

    # A staffed class on the same day, to prove the endpoint still returns real work.
    staffed = await make_class(center, teacher, name="Staffed")
    student = await make_student(center)
    await _enroll(db_session, staffed, student, center)
    db_session.add(
        Lesson(
            class_id=staffed.id,
            teacher_id=teacher.id,
            start_time=time(13, 0),
            duration_minutes=60,
            specific_date=yesterday,
            center_id=center.id,
        )
    )
    await db_session.commit()

    headers = await login(admin)
    resp = await client.get("/api/v1/attendance/pending", headers=headers)
    assert resp.status_code == 200, resp.text

    sessions = resp.json()["sessions"]
    assert all(s["students"] for s in sessions)
    assert not any(s["class_id"] == str(orphan_class.id) for s in sessions)
    assert any(s["class_id"] == str(staffed.id) for s in sessions)
