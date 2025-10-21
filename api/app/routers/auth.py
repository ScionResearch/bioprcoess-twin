"""
Authentication endpoints.
Handles user login and token generation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas import LoginRequest, Token, UserResponse
from ..auth import authenticate_user, create_access_token
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
