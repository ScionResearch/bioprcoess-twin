"""Calibration endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from ..database import get_db
from ..models import Calibration, Batch, User
from ..schemas import CalibrationCreate, CalibrationResponse
from ..auth import require_technician

router = APIRouter()


@router.post("/batches/{batch_id}/calibrations", response_model=CalibrationResponse, status_code=status.HTTP_201_CREATED)
async def create_calibration(
    batch_id: UUID,
    calibration_in: CalibrationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """Log sensor calibration for a batch."""
    # Verify batch exists and is in pending status
    stmt = select(Batch).where(Batch.batch_id == batch_id)
    result = await db.execute(stmt)
    batch = result.scalar_one_or_none()

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    if batch.status != "pending":
        raise HTTPException(status_code=422, detail="Cannot add calibration: batch already started")

    calibration = Calibration(
        batch_id=batch_id,
        **calibration_in.model_dump(exclude_unset=True, by_alias=True)
    )

    db.add(calibration)
    await db.commit()
    await db.refresh(calibration)

    return calibration


@router.get("/batches/{batch_id}/calibrations", response_model=List[CalibrationResponse])
async def list_calibrations(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """List all calibrations for a batch."""
    stmt = select(Calibration).where(Calibration.batch_id == batch_id).order_by(Calibration.calibrated_at)
    result = await db.execute(stmt)
    return result.scalars().all()
