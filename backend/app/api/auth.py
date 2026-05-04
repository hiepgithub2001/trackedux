"""Authentication API routes."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password, verify_token
from app.crud.user import get_user_by_id, get_user_by_username
from app.models.center import Center
from app.schemas.user import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UpdateMeRequest,
    UpdatePasswordRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: DbSession):
    """Authenticate user and return JWT tokens."""
    user = await get_user_by_username(db, request.username)
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive",
        )

    if user.center_id is not None:
        center = (await db.execute(select(Center).where(Center.id == user.center_id))).scalar_one_or_none()
        if center is None or not center.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Center is deactivated",
            )

    token_data = {"sub": str(user.id), "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest, db: DbSession):
    """Refresh access token using a valid refresh token."""
    payload = verify_token(request.refresh_token, token_type="refresh")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    from uuid import UUID

    user = await get_user_by_id(db, UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    token_data = {"sub": str(user.id), "role": user.role}
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout")
async def logout():
    """Logout (client-side token removal)."""
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser):
    """Get current authenticated user profile."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_me(request: UpdateMeRequest, current_user: CurrentUser, db: DbSession):
    """Update current user profile info."""
    update_data = request.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(current_user, key, value)

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)

    return UserResponse.model_validate(current_user)


@router.put("/me/password")
async def update_my_password(request: UpdatePasswordRequest, current_user: CurrentUser, db: DbSession):
    """Update current user password."""
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    current_user.password_hash = hash_password(request.new_password)
    db.add(current_user)
    await db.commit()

    return {"detail": "Password updated successfully"}
