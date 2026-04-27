"""Dashboard service — aggregate metrics."""
from datetime import date
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.student import Student
from app.models.class_session import ClassSession
from app.models.attendance import AttendanceRecord
from app.models.package import Package
from app.models.payment_record import PaymentRecord


async def get_dashboard_metrics(db: AsyncSession, user_role: str) -> dict:
    today = date.today()
    today_dow = today.weekday()

    # Active students count
    result = await db.execute(select(func.count()).where(Student.enrollment_status == "active"))
    active_students = result.scalar() or 0

    # Today's sessions count
    result = await db.execute(select(func.count()).where(ClassSession.day_of_week == today_dow, ClassSession.is_active == True))
    today_sessions = result.scalar() or 0

    # Today's absences count
    result = await db.execute(select(func.count()).where(AttendanceRecord.session_date == today, AttendanceRecord.status.in_(["absent", "absent_with_notice"])))
    today_absences = result.scalar() or 0

    # Expiring packages (<=2 remaining sessions)
    result = await db.execute(select(func.count()).where(Package.is_active == True, Package.remaining_sessions <= 2))
    expiring_packages = result.scalar() or 0

    # Monthly revenue (admin only)
    monthly_revenue = None
    if user_role == "admin":
        first_of_month = today.replace(day=1)
        result = await db.execute(select(func.coalesce(func.sum(PaymentRecord.amount), 0)).where(PaymentRecord.payment_date >= first_of_month))
        monthly_revenue = result.scalar() or 0

    return {
        "active_students": active_students,
        "today_sessions": today_sessions,
        "today_absences": today_absences,
        "expiring_packages": expiring_packages,
        "monthly_revenue": monthly_revenue,
        "today_date": today.isoformat(),
    }
