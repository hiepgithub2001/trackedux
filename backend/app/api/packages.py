"""Packages/Tuition API routes."""
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, status
from app.core.deps import CurrentUser, DbSession
from app.crud.package import create_package, get_package_by_id, list_packages
from app.schemas.package import PackageCreate, PackageResponse, PaymentRecordCreate, PaymentRecordResponse
from app.services.tuition_service import record_payment

router = APIRouter(prefix="/packages", tags=["Packages"])


@router.get("", response_model=list[PackageResponse])
async def get_packages(db: DbSession, current_user: CurrentUser, student_id: UUID | None = None, payment_status: str | None = None):
    """List packages with filters."""
    pkgs = await list_packages(db, student_id=student_id, payment_status=payment_status)
    return [PackageResponse(
        id=p.id, student_id=p.student_id, total_sessions=p.total_sessions,
        remaining_sessions=p.remaining_sessions, package_type=p.package_type, price=p.price,
        payment_status=p.payment_status, is_active=p.is_active, reminder_status=p.reminder_status,
        started_at=p.started_at, expired_at=p.expired_at,
        student_name=p.student.name if p.student else None,
        created_at=p.created_at, updated_at=p.updated_at,
    ) for p in pkgs]


@router.post("", response_model=PackageResponse, status_code=status.HTTP_201_CREATED)
async def create_package_endpoint(data: PackageCreate, db: DbSession, current_user: CurrentUser):
    """Create a new package. Admin only."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    pkg = await create_package(db, data)
    return PackageResponse(
        id=pkg.id, student_id=pkg.student_id, total_sessions=pkg.total_sessions,
        remaining_sessions=pkg.remaining_sessions, package_type=pkg.package_type, price=pkg.price,
        payment_status=pkg.payment_status, is_active=pkg.is_active, reminder_status=pkg.reminder_status,
        started_at=pkg.started_at, expired_at=pkg.expired_at, student_name=None,
        created_at=pkg.created_at, updated_at=pkg.updated_at,
    )


@router.post("/{package_id}/payments", response_model=PaymentRecordResponse, status_code=status.HTTP_201_CREATED)
async def add_payment(package_id: UUID, data: PaymentRecordCreate, db: DbSession, current_user: CurrentUser):
    """Record a payment for a package. Admin only."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    payment = await record_payment(db, package_id, data, current_user.id)
    return PaymentRecordResponse.model_validate(payment)
