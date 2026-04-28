"""Dashboard service — aggregate metrics."""

from datetime import date, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import AttendanceRecord
from app.models.class_session import ClassSession
from app.models.package import Package
from app.models.payment_record import PaymentRecord
from app.models.student import Student


async def get_dashboard_metrics(db: AsyncSession, user_role: str, center_id: UUID) -> dict:
    today = date.today()
    today_dow = today.weekday()
    now = datetime.now()

    # Active students count (scoped to center)
    result = await db.execute(
        select(func.count()).where(Student.enrollment_status == "active", Student.center_id == center_id)
    )
    active_students = result.scalar() or 0

    # Today's sessions count and running sessions (scoped to center)
    result = await db.execute(
        select(ClassSession).where(
            ClassSession.day_of_week == today_dow,
            ClassSession.is_active == True,  # noqa: E712
            ClassSession.center_id == center_id,
        )
    )
    today_sessions_objs = result.scalars().all()
    today_sessions = len(today_sessions_objs)

    running_sessions = 0
    for s in today_sessions_objs:
        s_dt = datetime.combine(today, s.start_time)
        e_dt = s_dt + timedelta(minutes=s.duration_minutes)
        if s_dt <= now <= e_dt:
            running_sessions += 1

    # Today's absences count (scoped to center)
    result = await db.execute(
        select(func.count()).where(
            AttendanceRecord.session_date == today,
            AttendanceRecord.status.in_(["absent", "absent_with_notice"]),
            AttendanceRecord.center_id == center_id,
        )
    )
    today_absences = result.scalar() or 0

    # Expiring packages (<=2 remaining sessions, scoped to center)
    result = await db.execute(
        select(func.count()).where(
            Package.is_active == True,  # noqa: E712
            Package.remaining_sessions <= 2,
            Package.center_id == center_id,
        )
    )
    expiring_packages = result.scalar() or 0

    # Monthly revenue (admin only, scoped to center)
    monthly_revenue = None
    if user_role == "admin":
        first_of_month = today.replace(day=1)
        result = await db.execute(
            select(func.coalesce(func.sum(PaymentRecord.amount), 0)).where(
                PaymentRecord.payment_date >= first_of_month,
                PaymentRecord.center_id == center_id,
            )
        )
        monthly_revenue = result.scalar() or 0

    return {
        "active_students": active_students,
        "today_sessions": today_sessions,
        "running_sessions": running_sessions,
        "today_absences": today_absences,
        "expiring_packages": expiring_packages,
        "monthly_revenue": monthly_revenue,
        "today_date": today.isoformat(),
    }
