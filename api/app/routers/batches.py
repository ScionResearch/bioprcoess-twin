"""
Batch management endpoints.
CRUD operations for batch records.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID

from ..database import get_db
from ..models import Batch, User
from ..schemas import BatchCreate, BatchResponse, BatchUpdate
from ..auth import get_current_user, require_technician

router = APIRouter()


@router.post("/batches", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
async def create_batch(
    batch_in: BatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """
    Create a new batch record.

    **Validation:**
    - Batch number must be unique within phase
    - Vessel must not have another active (pending/running) batch
    - User must have technician, engineer, or admin role

    **Workflow:**
    - Sets batch status to 'pending'
    - Waits for media prep, calibrations, and inoculation
    """
    # Check for duplicate batch number in phase
    stmt = select(Batch).where(
        Batch.batch_number == batch_in.batch_number,
        Batch.phase == batch_in.phase
    )
    result = await db.execute(stmt)
    existing_batch = result.scalar_one_or_none()

    if existing_batch:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Batch {batch_in.batch_number} already exists in Phase {batch_in.phase}"
        )

    # Check vessel availability
    stmt = select(Batch).where(
        Batch.vessel_id == batch_in.vessel_id,
        Batch.status.in_(["pending", "running"])
    )
    result = await db.execute(stmt)
    active_batch = result.scalar_one_or_none()

    if active_batch:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Vessel {batch_in.vessel_id} has active batch #{active_batch.batch_number}"
        )

    # Create batch
    batch = Batch(
        batch_number=batch_in.batch_number,
        phase=batch_in.phase,
        vessel_id=batch_in.vessel_id,
        operator_id=batch_in.operator_id,
        notes=batch_in.notes,
        status="pending",
        created_by=current_user.username
    )

    db.add(batch)
    await db.commit()
    await db.refresh(batch)

    return batch


@router.get("/batches", response_model=List[BatchResponse])
async def list_batches(
    phase: Optional[str] = Query(None, regex="^[ABC]$"),
    status: Optional[str] = Query(None, regex="^(pending|running|complete|aborted)$"),
    vessel_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List batches with optional filtering.

    **Query Parameters:**
    - phase: Filter by campaign phase (A, B, or C)
    - status: Filter by batch status
    - vessel_id: Filter by vessel
    - limit: Number of results (max 100)
    - offset: Pagination offset
    """
    stmt = select(Batch).order_by(Batch.created_at.desc())

    # Apply filters
    if phase:
        stmt = stmt.where(Batch.phase == phase)
    if status:
        stmt = stmt.where(Batch.status == status)
    if vessel_id:
        stmt = stmt.where(Batch.vessel_id == vessel_id)

    # Pagination
    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    batches = result.scalars().all()

    return batches


@router.get("/batches/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single batch by ID with all child records."""
    stmt = select(Batch).where(Batch.batch_id == batch_id)
    result = await db.execute(stmt)
    batch = result.scalar_one_or_none()

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found"
        )

    return batch


@router.patch("/batches/{batch_id}", response_model=BatchResponse)
async def update_batch(
    batch_id: UUID,
    batch_update: BatchUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """
    Update batch metadata (limited fields).

    **Note:** Can only update notes and operator_id.
    Status changes are handled automatically by triggers.
    """
    stmt = select(Batch).where(Batch.batch_id == batch_id)
    result = await db.execute(stmt)
    batch = result.scalar_one_or_none()

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found"
        )

    # Only allow updating certain fields
    if batch_update.notes is not None:
        batch.notes = batch_update.notes
    if batch_update.operator_id is not None:
        batch.operator_id = batch_update.operator_id

    await db.commit()
    await db.refresh(batch)

    return batch


@router.delete("/batches/{batch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_batch(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """
    Delete a batch record.

    **Warning:** This will cascade delete all child records (media prep, samples, etc.).
    Only use for test/invalid batches.
    """
    stmt = select(Batch).where(Batch.batch_id == batch_id)
    result = await db.execute(stmt)
    batch = result.scalar_one_or_none()

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found"
        )

    # Prevent deletion of completed batches (production safety)
    if batch.status == "complete":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete completed batches"
        )

    await db.delete(batch)
    await db.commit()

    return None
