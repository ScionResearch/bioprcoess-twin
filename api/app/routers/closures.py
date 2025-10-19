"""Batch closure endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from ..database import get_db
from ..models import BatchClosure, Batch, Sample, Failure, User
from ..schemas import BatchClosureCreate, BatchClosureResponse
from ..auth import require_engineer

router = APIRouter()


@router.post("/batches/{batch_id}/close", response_model=BatchClosureResponse, status_code=status.HTTP_201_CREATED)
async def close_batch(
    batch_id: UUID,
    closure_in: BatchClosureCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_engineer)  # Only engineers can close batches
):
    """
    Close batch and finalize record.

    **Validation:**
    - Batch must be 'running'
    - Must have ≥8 sample records
    - All Level 3 failures must be reviewed
    - Requires engineer role
    """
    # Verify batch exists and is running
    stmt = select(Batch).where(Batch.batch_id == batch_id)
    result = await db.execute(stmt)
    batch = result.scalar_one_or_none()

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    if batch.status != "running":
        raise HTTPException(status_code=422, detail="Cannot close batch: not yet started")

    # Check minimum sample count
    stmt = select(Sample).where(Sample.batch_id == batch_id)
    result = await db.execute(stmt)
    samples = result.scalars().all()

    if len(samples) < 8:
        raise HTTPException(
            status_code=422,
            detail=f"Cannot close: only {len(samples)} samples (minimum 8 required)"
        )

    # Check for unreviewed critical failures
    stmt = select(Failure).where(
        Failure.batch_id == batch_id,
        Failure.deviation_level == 3,
        Failure.reviewed_by == None
    )
    result = await db.execute(stmt)
    unreviewed_failures = result.scalars().all()

    if unreviewed_failures:
        raise HTTPException(
            status_code=422,
            detail=f"Cannot close: {len(unreviewed_failures)} unreviewed critical failures"
        )

    # Create closure (trigger will update batch status)
    closure = BatchClosure(
        batch_id=batch_id,
        **closure_in.model_dump(exclude_unset=True)
    )

    db.add(closure)
    await db.commit()
    await db.refresh(closure)

    return closure
