"""Student business logic service."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.student import get_student_by_id
from app.models.student_status_history import StudentStatusHistory

# Valid state transitions
VALID_TRANSITIONS = {
    "trial": {"active", "withdrawn"},
    "active": {"paused", "withdrawn"},
    "paused": {"active", "withdrawn"},
    "withdrawn": set(),
}


async def change_student_status(
    db: AsyncSession,
    student_id: UUID,
    new_status: str,
    changed_by: UUID,
    reason: str | None = None,
    center_id: UUID | None = None,
) -> None:
    """Validate and execute a student status transition, recording history."""
    student = await get_student_by_id(db, student_id, center_id) if center_id else None
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    current_status = student.enrollment_status
    allowed = VALID_TRANSITIONS.get(current_status, set())

    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot change status from '{current_status}' to '{new_status}'. "
            f"Allowed transitions: {', '.join(allowed) if allowed else 'none'}",
        )

    # Record history (with center_id for isolation)
    history = StudentStatusHistory(
        student_id=student_id,
        from_status=current_status,
        to_status=new_status,
        changed_by=changed_by,
        reason=reason,
        center_id=center_id or student.center_id,
    )
    db.add(history)

    # Update status
    student.enrollment_status = new_status
    await db.commit()
