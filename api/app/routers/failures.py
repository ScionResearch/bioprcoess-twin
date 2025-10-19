"""Failure/deviation endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from ..database import get_db
from ..models import Failure, Batch, User
from ..schemas import FailureCreate, FailureResponse
from ..auth import require_technician

router = APIRouter()


@router.post("/batches/{batch_id}/failures", response_model=FailureResponse, status_code=status.HTTP_201_CREATED)
async def create_failure(
    batch_id: UUID,
    failure_in: FailureCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """Log deviation or failure event."""
    # Verify batch exists
    stmt = select(Batch).where(Batch.batch_id == batch_id)
    result = await db.execute(stmt)
    batch = result.scalar_one_or_none()

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    failure = Failure(
        batch_id=batch_id,
        **failure_in.model_dump(exclude_unset=True)
    )

    db.add(failure)
    await db.commit()
    await db.refresh(failure)

    return failure


@router.get("/batches/{batch_id}/failures", response_model=List[FailureResponse])
async def list_failures(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """List all failures for a batch."""
    stmt = select(Failure).where(Failure.batch_id == batch_id).order_by(Failure.reported_at)
    result = await db.execute(stmt)
    return result.scalars().all()
