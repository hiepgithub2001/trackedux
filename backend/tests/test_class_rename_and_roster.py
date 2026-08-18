"""Regression tests for class rename cascade + historical roster membership.

Covers two bugs seen in production on the "Hân + Súp Lơ" class:
  1. Renaming a class left Lesson.title frozen at the old name, so the
     attendance/schedule views kept showing the stale name.
  2. A student unenrolled *today* disappeared from *past* sessions, because the
     roster filter rejected on is_active before consulting the unenrolled_at date.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy import select

pytestmark = pytest.mark.asyncio


async def test_rename_class_cascades_to_mirrored_lesson_title(
    client, login, make_center, make_admin, make_teacher, make_class, db_session
):
    from app.models.lesson import Lesson

    center = await make_center()
    admin = await make_admin(center)
    teacher = await make_teacher(center)
    cls = await make_class(center, teacher, name="OldName")

    lesson = (await db_session.execute(select(Lesson).where(Lesson.class_id == cls.id))).scalar_one()
    lesson.title = cls.name  # title mirrors the class name, as the prod data did
    await db_session.commit()
    new_name = cls.name + "-RENAMED"

    headers = await login(admin)
    resp = await client.put(f"/api/v1/classes/{cls.id}", json={"name": new_name}, headers=headers)
    assert resp.status_code == 200, resp.text

    await db_session.refresh(lesson)
    assert lesson.title == new_name


async def test_rename_class_preserves_genuine_custom_title(
    client, login, make_center, make_admin, make_teacher, make_class, db_session
):
    """A deliberately custom title must NOT be clobbered by a rename."""
    from app.models.lesson import Lesson

    center = await make_center()
    admin = await make_admin(center)
    teacher = await make_teacher(center)
    cls = await make_class(center, teacher, name="OldName")

    lesson = (await db_session.execute(select(Lesson).where(Lesson.class_id == cls.id))).scalar_one()
    lesson.title = "Theory lesson"
    await db_session.commit()

    headers = await login(admin)
    resp = await client.put(f"/api/v1/classes/{cls.id}", json={"name": cls.name + "-RENAMED"}, headers=headers)
    assert resp.status_code == 200, resp.text

    await db_session.refresh(lesson)
    assert lesson.title == "Theory lesson"


async def test_rename_class_with_roster_edit_returns_200(
    client, login, make_center, make_admin, make_teacher, make_class, make_student, db_session
):
    """Rename + add a student in one PUT must not 500 while serializing the response."""
    from app.models.lesson import Lesson

    center = await make_center()
    admin = await make_admin(center)
    teacher = await make_teacher(center)
    cls = await make_class(center, teacher, name="OldName")
    student = await make_student(center, "S1")

    lesson = (await db_session.execute(select(Lesson).where(Lesson.class_id == cls.id))).scalar_one()
    lesson.title = cls.name
    await db_session.commit()
    new_name = cls.name + "-RENAMED"

    headers = await login(admin)
    resp = await client.put(
        f"/api/v1/classes/{cls.id}",
        json={"name": new_name, "student_ids": [str(student.id)]},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert [s["id"] for s in resp.json()["enrolled_students"]] == [str(student.id)]

    await db_session.refresh(lesson)
    assert lesson.title == new_name


async def test_unenrolled_student_still_shows_for_past_occurrence(
    client, login, make_center, make_admin, make_teacher, make_class, make_student, db_session
):
    """A student unenrolled today was still enrolled for yesterday's session."""
    from app.models.class_enrollment import ClassEnrollment
    from app.models.lesson import Lesson
    from app.models.lesson_occurrence import LessonOccurrence

    center = await make_center()
    admin = await make_admin(center)
    teacher = await make_teacher(center)

    yesterday = date.today() - timedelta(days=1)
    cls = await make_class(center, teacher, day_of_week=yesterday.weekday(), name="Han+SupLo")

    lesson = (await db_session.execute(select(Lesson).where(Lesson.class_id == cls.id))).scalar_one()
    db_session.add(
        LessonOccurrence(lesson_id=lesson.id, original_date=yesterday, status="active", center_id=center.id)
    )

    leaver = await make_student(center, "Leaver")
    stayer = await make_student(center, "Stayer")
    enr_leaver = ClassEnrollment(class_id=cls.id, student_id=leaver.id, center_id=center.id)
    db_session.add_all([enr_leaver, ClassEnrollment(class_id=cls.id, student_id=stayer.id, center_id=center.id)])
    await db_session.commit()

    # Unenroll as of today — yesterday's session predates the removal.
    enr_leaver.is_active = False
    enr_leaver.unenrolled_at = date.today()
    await db_session.commit()

    headers = await login(admin)
    resp = await client.get("/api/v1/attendance/pending", headers=headers)
    assert resp.status_code == 200
    sessions = resp.json()["sessions"]
    assert len(sessions) == 1, sessions
    ids = {s["id"] for s in sessions[0]["students"]}
    assert ids == {str(leaver.id), str(stayer.id)}


async def test_unenrolled_student_hidden_from_future_occurrence(
    client, login, make_center, make_admin, make_teacher, make_class, make_student, db_session
):
    """The flip side: after the unenrollment date the student must be gone."""
    from app.models.class_enrollment import ClassEnrollment
    from app.models.lesson import Lesson
    from app.models.lesson_occurrence import LessonOccurrence

    center = await make_center()
    admin = await make_admin(center)
    teacher = await make_teacher(center)

    yesterday = date.today() - timedelta(days=1)
    cls = await make_class(center, teacher, day_of_week=yesterday.weekday(), name="Han+SupLo")

    lesson = (await db_session.execute(select(Lesson).where(Lesson.class_id == cls.id))).scalar_one()
    db_session.add(
        LessonOccurrence(lesson_id=lesson.id, original_date=yesterday, status="active", center_id=center.id)
    )

    leaver = await make_student(center, "Leaver")
    stayer = await make_student(center, "Stayer")
    enr_leaver = ClassEnrollment(class_id=cls.id, student_id=leaver.id, center_id=center.id)
    db_session.add_all([enr_leaver, ClassEnrollment(class_id=cls.id, student_id=stayer.id, center_id=center.id)])
    await db_session.commit()

    # Unenrolled *before* the session in question.
    enr_leaver.is_active = False
    enr_leaver.unenrolled_at = yesterday - timedelta(days=7)
    await db_session.commit()

    headers = await login(admin)
    resp = await client.get("/api/v1/attendance/pending", headers=headers)
    assert resp.status_code == 200
    sessions = resp.json()["sessions"]
    assert len(sessions) == 1, sessions
    ids = {s["id"] for s in sessions[0]["students"]}
    assert ids == {str(stayer.id)}
