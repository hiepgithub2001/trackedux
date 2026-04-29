"""FastAPI dependencies for dependency injection."""

from functools import wraps
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_token
from app.db.session import async_session_factory

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_db() -> AsyncSession:
    """Yield a database session, auto-closing on exit."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Extract and validate the current user from the JWT token."""
    from sqlalchemy import select

    from app.crud.user import get_user_by_id
    from app.models.center import Center

    payload = verify_token(token, token_type="access")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = await get_user_by_id(db, UUID(user_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    if user.center_id is not None:
        center = (await db.execute(select(Center).where(Center.id == user.center_id))).scalar_one_or_none()
        if center is None or not center.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Center is deactivated",
            )

    return user


def require_role(*roles: str):
    """Decorator factory to restrict endpoint access to specific roles."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find current_user in kwargs
            current_user = kwargs.get("current_user")
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authentication required",
                )
            if current_user.role not in roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{current_user.role}' is not authorized. Required: {', '.join(roles)}",
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Type aliases for common dependency injections
CurrentUser = Annotated[object, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_center_id(current_user) -> UUID:
    """Extract center_id from the current user.

    Raises HTTP 403 if the user is a superadmin (superadmin has no center_id
    and must not access tenant-scoped endpoints).
    """
    if current_user.role == "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin accounts cannot access center-scoped resources directly.",
        )
    if current_user.center_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no center assigned.",
        )
    return UUID(str(current_user.center_id))


def require_superadmin(current_user: CurrentUser) -> object:
    """FastAPI dependency that raises 403 for non-superadmin users.

    Use as: ``current_user: Annotated[object, Depends(require_superadmin)]``
    """
    if current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is restricted to system administrators.",
        )
    return current_user


# Type alias for superadmin-only endpoints
SuperAdminUser = Annotated[object, Depends(require_superadmin)]
