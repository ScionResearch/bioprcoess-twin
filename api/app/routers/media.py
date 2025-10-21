"""Media preparation endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from ..database import get_db
from ..models import MediaPreparation, Batch, User
from ..schemas import MediaPreparationCreate, MediaPreparationResponse
from ..auth import require_technician

router = APIRouter()


@router.get("/batches/{batch_id}/media", response_model=MediaPreparationResponse)
async def get_media_preparation(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """Get media preparation record for a batch."""
    # Verify batch exists
    stmt = select(Batch).where(Batch.batch_id == batch_id)
    result = await db.execute(stmt)
    batch = result.scalar_one_or_none()

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Get media prep
    stmt = select(MediaPreparation).where(MediaPreparation.batch_id == batch_id)
    result = await db.execute(stmt)
    media_prep = result.scalar_one_or_none()

    if not media_prep:
        raise HTTPException(status_code=404, detail="Media preparation not found")

    return media_prep


@router.post("/batches/{batch_id}/media", response_model=MediaPreparationResponse, status_code=status.HTTP_201_CREATED)
async def create_media_preparation(
    batch_id: UUID,
    media_in: MediaPreparationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """
    Log media preparation for a batch.

    **Required fields:**
    - recipe_name
    - All component quantities and lots
    - final_volume_l
    - autoclave_cycle
    - prepared_by
    """
    # Verify batch exists
    stmt = select(Batch).where(Batch.batch_id == batch_id)
    result = await db.execute(stmt)
    batch = result.scalar_one_or_none()

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Check if media prep already exists
    stmt = select(MediaPreparation).where(MediaPreparation.batch_id == batch_id)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Media preparation already logged for this batch"
        )

    # Create media preparation
    media_prep = MediaPreparation(
        batch_id=batch_id,
        **media_in.model_dump(exclude_unset=True)
    )

    db.add(media_prep)
    await db.commit()
    await db.refresh(media_prep)

    return media_prep
