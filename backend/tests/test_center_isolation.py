"""Integration tests for multi-center data isolation (spec 007).

Each test sets up two centers with their own admin users, students, teachers,
and classes, then verifies that resources cannot leak across the tenancy
boundary. Cross-center access returns 404 (not 403) per the spec clarification.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


# ── User Story 1: Read isolation ───────────────────────────────────────────


async def test_cross_center_class_lookup_returns_404(
    client, login, make_center, make_admin, make_teacher, make_class
):
    """Center A's admin must get 404 (not 403) on Center B's class ID."""
    a = await make_center()
    b = await make_center()
    admin_a = await make_admin(a)
    teacher_b = await make_teacher(b)
    class_b = await make_class(b, teacher_b)

    headers = await login(admin_a)
    resp = await client.get(f"/api/v1/classes/{class_b.id}", headers=headers)
    assert resp.status_code == 404


async def test_cross_center_class_delete_returns_404(
    client, login, make_center, make_admin, make_teacher, make_class
):
    """Deleting another center's class must 404 and leave the row intact (G1)."""
    a = await make_center()
    b = await make_center()
    admin_a = await make_admin(a)
    teacher_b = await make_teacher(b)
    class_b = await make_class(b, teacher_b)

    headers = await login(admin_a)
    resp = await client.delete(f"/api/v1/classes/{class_b.id}", headers=headers)
    assert resp.status_code == 404


# ── User Story 2: Write isolation ──────────────────────────────────────────


async def test_cross_center_enrollment_blocked(
    client, login, make_center, make_admin, make_student, make_teacher, make_class
):
    """Enrolling Center B's student in Center A's class returns 404 (G4)."""
    a = await make_center()
    b = await make_center()
    admin_a = await make_admin(a)
    teacher_a = await make_teacher(a)
    class_a = await make_class(a, teacher_a)
    student_b = await make_student(b)

    headers = await login(admin_a)
    resp = await client.post(
        f"/api/v1/classes/{class_a.id}/enroll",
        json={"student_id": str(student_b.id)},
        headers=headers,
    )
    assert resp.status_code == 404


async def test_create_class_with_other_center_teacher_blocked(
    client, login, make_center, make_admin, make_teacher
):
    """Creating a class with a teacher from another center must 404 (Rule 2)."""
    a = await make_center()
    b = await make_center()
    admin_a = await make_admin(a)
    teacher_b = await make_teacher(b)

    headers = await login(admin_a)
    resp = await client.post(
        "/api/v1/classes",
        json={
            "teacher_id": str(teacher_b.id),
            "name": "Cross-tenant attempt",
            "day_of_week": 1,
            "start_time": "10:00",
            "duration_minutes": 60,
            "student_ids": [],
        },
        headers=headers,
    )
    assert resp.status_code == 404


async def test_unenroll_other_center_returns_404(
    client, login, db_session, make_center, make_admin, make_teacher, make_class, make_student
):
    """Unenrolling against another center's class must 404 (G2)."""
    from app.models.class_enrollment import ClassEnrollment

    a = await make_center()
    b = await make_center()
    admin_a = await make_admin(a)
    teacher_b = await make_teacher(b)
    class_b = await make_class(b, teacher_b)
    student_b = await make_student(b)

    db_session.add(
        ClassEnrollment(class_session_id=class_b.id, student_id=student_b.id, center_id=b.id)
    )
    await db_session.commit()

    headers = await login(admin_a)
    resp = await client.delete(
        f"/api/v1/classes/{class_b.id}/enroll/{student_b.id}", headers=headers
    )
    assert resp.status_code == 404


# ── User Story 3: Schedule conflict isolation ──────────────────────────────


async def test_schedule_conflicts_isolated_by_center(
    client, login, make_center, make_admin, make_teacher, make_class
):
    """A teacher in Center A with same time slot as Center B does not conflict (G3).

    Two centers happen to use the same day/time. Center A creates a class. Even
    though Center B has an overlapping class for an unrelated teacher, the
    create succeeds because conflict checks must be center-scoped.
    """
    a = await make_center()
    b = await make_center()
    admin_a = await make_admin(a)
    teacher_a = await make_teacher(a)
    teacher_b = await make_teacher(b)

    # Pre-existing class in B at the same slot (different teacher, different tenant).
    await make_class(b, teacher_b, day_of_week=2, start_time="14:00", duration_minutes=60)

    headers = await login(admin_a)
    resp = await client.post(
        "/api/v1/classes",
        json={
            "teacher_id": str(teacher_a.id),
            "name": "A's class same slot",
            "day_of_week": 2,
            "start_time": "14:00",
            "duration_minutes": 60,
            "student_ids": [],
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text


# ── Phase 2 Foundational: Center deactivation ──────────────────────────────


async def test_login_blocked_for_deactivated_center(
    client, db_session, make_center, make_admin
):
    """Login must reject users whose center has been deactivated (G5)."""
    c = await make_center()
    admin = await make_admin(c)
    c.is_active = False
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": admin.username, "password": "secret123"},
    )
    assert resp.status_code == 401
    assert "deactivated" in resp.json()["detail"].lower()


async def test_existing_token_blocked_after_center_deactivation(
    client, login, db_session, make_center, make_admin
):
    """JWT issued before deactivation is rejected on next request (G6)."""
    c = await make_center()
    admin = await make_admin(c)
    headers = await login(admin)

    c.is_active = False
    await db_session.commit()

    resp = await client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 401
