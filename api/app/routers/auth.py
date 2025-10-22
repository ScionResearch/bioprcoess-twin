"""
Authentication endpoints.
Handles user login, token generation, and admin user management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..schemas import LoginRequest, Token, UserResponse, UserCreate
from ..auth import authenticate_user, create_access_token, get_password_hash, require_admin
from ..models import User
from pydantic import BaseModel

router = APIRouter()


class AuthResponse(BaseModel):
    """Authentication response with token and user info."""
    access_token: str
    token_type: str
    user: UserResponse


@router.post("/auth/login", response_model=AuthResponse)
async def login(
    login_request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT access token with user info.

    **Process:**
    1. Validate username and password
    2. Generate JWT token with user claims
    3. Return token and user information for authenticated requests

    **Example:**
    ```bash
    curl -X POST http://localhost:8000/api/v1/auth/login \\
      -H "Content-Type: application/json" \\
      -d '{"username": "tech01", "password": "admin123"}'
    ```

    Returns:
        AuthResponse with access_token, token_type, and user info
    """
    user = await authenticate_user(db, login_request.username, login_request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token with user claims
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}
    )

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Create a new user account (admin only).

    **Required role:** admin

    **Example:**
    ```bash
    curl -X POST http://localhost:8000/api/users \\
      -H "Authorization: Bearer $TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "username": "tech01",
        "password": "SecurePass123!",
        "role": "technician",
        "full_name": "Jane Technician"
      }'
    ```
    """
    # Check if username already exists
    stmt = select(User).where(User.username == user_in.username)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{user_in.username}' already exists"
        )

    # Create new user
    new_user = User(
        username=user_in.username,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role,
        full_name=user_in.full_name,
        active=True
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    List all users (admin only).

    **Required role:** admin
    """
    stmt = select(User).order_by(User.username)
    result = await db.execute(stmt)
    users = result.scalars().all()

    return users


@router.delete("/users/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Delete a user account (admin only).

    **Required role:** admin

    **Warning:** Cannot delete your own account.
    """
    # Prevent self-deletion
    if username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    # Find user
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()

    return None
