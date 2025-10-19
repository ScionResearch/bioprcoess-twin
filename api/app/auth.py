"""
Authentication and authorization with JWT and RBAC.
Implements secure password hashing and role-based access control.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .config import settings
from .database import get_db
from .models import User
from .schemas import TokenData

# Password hashing context (bcrypt with cost factor 12)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token security scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary with token claims (e.g., {"sub": username, "role": role})
        expires_delta: Token expiration time (default: 15 minutes)

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
    """
    Authenticate a user by username and password.

    Args:
        db: Database session
        username: Username to authenticate
        password: Plain text password

    Returns:
        User object if authentication successful, None otherwise
    """
    stmt = select(User).where(User.username == username, User.active == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    # Update last login timestamp
    user.last_login = datetime.utcnow()
    await db.commit()

    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    Usage:
        @router.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"username": current_user.username}

    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

        token_data = TokenData(username=username, role=payload.get("role"))

    except JWTError:
        raise credentials_exception

    # Fetch user from database
    stmt = select(User).where(User.username == token_data.username, User.active == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


def require_role(allowed_roles: list[str]):
    """
    Dependency factory to enforce role-based access control.

    Args:
        allowed_roles: List of roles allowed to access the endpoint

    Usage:
        @router.post("/batches/{batch_id}/close")
        async def close_batch(
            current_user: User = Depends(require_role(["engineer", "admin"]))
        ):
            # Only engineers and admins can access this endpoint
            pass

    Raises:
        HTTPException: 403 if user's role is not in allowed_roles
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {allowed_roles}"
            )
        return current_user

    return role_checker


# Role-specific dependencies (convenience shortcuts)
require_technician = require_role(["technician", "engineer", "admin"])
require_engineer = require_role(["engineer", "admin"])
require_admin = require_role(["admin"])
