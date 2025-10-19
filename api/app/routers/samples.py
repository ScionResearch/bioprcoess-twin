"""Sample endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from ..database import get_db
from ..models import Sample, Batch, User
from ..schemas import SampleCreate, SampleResponse
from ..auth import require_technician

router = APIRouter()


@router.post("/batches/{batch_id}/samples", response_model=SampleResponse, status_code=status.HTTP_201_CREATED)
async def create_sample(
    batch_id: UUID,
    sample_in: SampleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """Log in-process sample observation."""
    # Verify batch is running
    stmt = select(Batch).where(Batch.batch_id == batch_id)
    result = await db.execute(stmt)
    batch = result.scalar_one_or_none()

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    if batch.status != "running":
        raise HTTPException(status_code=422, detail="Cannot add sample: batch not yet inoculated")

    # Create sample (triggers will calculate timepoint, OD, DCW)
    sample = Sample(
        batch_id=batch_id,
        **sample_in.model_dump(exclude_unset=True, exclude={"od600_calculated"})
    )

    db.add(sample)
    await db.commit()
    await db.refresh(sample)

    return sample


@router.get("/batches/{batch_id}/samples", response_model=List[SampleResponse])
async def list_samples(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """List all samples for a batch."""
    stmt = select(Sample).where(Sample.batch_id == batch_id).order_by(Sample.timepoint_hours)
    result = await db.execute(stmt)
    return result.scalars().all()
