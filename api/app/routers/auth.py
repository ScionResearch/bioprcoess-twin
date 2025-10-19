"""
Authentication endpoints.
Handles user login and token generation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas import LoginRequest, Token
from ..auth import authenticate_user, create_access_token

router = APIRouter()


@router.post("/auth/login", response_model=Token)
async def login(
    login_request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT access token.

    **Process:**
    1. Validate username and password
    2. Generate JWT token with user claims
    3. Return token for subsequent authenticated requests

    **Example:**
    ```bash
    curl -X POST http://localhost:8000/api/v1/auth/login \\
      -H "Content-Type: application/json" \\
      -d '{"username": "tech01", "password": "admin123"}'
    ```

    Returns:
        Token with access_token and token_type
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

    return Token(access_token=access_token, token_type="bearer")
