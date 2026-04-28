"""Packages/Tuition API routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, DbSession, get_center_id
from app.crud.class_session import compute_display_ids, list_class_sessions
from app.crud.package import create_package, list_packages
from app.schemas.package import (
    PackageCreate,
    PackageResponse,
    PackageUpdate,
    PaymentRecordCreate,
    PaymentRecordResponse,
)
from app.services.tuition_service import record_payment

router = APIRouter(prefix="/packages", tags=["Packages"])


def _pkg_to_response(p, display_ids: dict[UUID, str], current_user) -> PackageResponse:
    # Hide price for non-admins
    price = p.price if current_user.role == "admin" else None

    return PackageResponse(
        id=p.id,
        student_id=p.student_id,
        student_name=p.student.name if p.student else None,
        class_session_id=p.class_session_id,
        class_display_id=display_ids.get(p.class_session_id),
        number_of_lessons=p.number_of_lessons,
        remaining_sessions=p.remaining_sessions,
        price=price,
        payment_status=p.payment_status,
        is_active=p.is_active,
        reminder_status=p.reminder_status,
        started_at=p.started_at,
        expired_at=p.expired_at,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.get("", response_model=list[PackageResponse])
async def get_packages(
    db: DbSession,
    current_user: CurrentUser,
    student_id: UUID | None = None,
    payment_status: str | None = None,
    class_session_id: UUID | None = None,
):
    """List packages with filters, scoped to center."""
    center_id = get_center_id(current_user)
    pkgs = await list_packages(
        db, center_id=center_id, student_id=student_id, payment_status=payment_status, class_session_id=class_session_id
    )
    all_classes = await list_class_sessions(db, center_id=center_id, active_only=False)
    display_ids = compute_display_ids(all_classes)
    return [_pkg_to_response(p, display_ids, current_user) for p in pkgs]


@router.post("", response_model=PackageResponse, status_code=status.HTTP_201_CREATED)
async def create_package_endpoint(data: PackageCreate, db: DbSession, current_user: CurrentUser):
    """Create a new flexible course package. Admin only."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    center_id = get_center_id(current_user)

    pkg = await create_package(db, data, center_id)

    all_classes = await list_class_sessions(db, center_id=center_id, active_only=False)
    display_ids = compute_display_ids(all_classes)
    return _pkg_to_response(pkg, display_ids, current_user)


@router.patch("/{package_id}", response_model=PackageResponse)
async def update_package_endpoint(package_id: UUID, data: PackageUpdate, db: DbSession, current_user: CurrentUser):
    """Update a package. Admin only."""
    from app.crud.package import update_package

    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    center_id = get_center_id(current_user)

    pkg = await update_package(db, package_id, data, center_id)

    all_classes = await list_class_sessions(db, center_id=center_id, active_only=False)
    display_ids = compute_display_ids(all_classes)
    return _pkg_to_response(pkg, display_ids, current_user)


@router.post("/{package_id}/payments", response_model=PaymentRecordResponse, status_code=status.HTTP_201_CREATED)
async def add_payment(package_id: UUID, data: PaymentRecordCreate, db: DbSession, current_user: CurrentUser):
    """Record a payment for a package. Admin only."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    payment = await record_payment(db, package_id, data, current_user.id)
    return PaymentRecordResponse.model_validate(payment)
