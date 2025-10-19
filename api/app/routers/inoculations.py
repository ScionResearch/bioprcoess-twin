"""Inoculation endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from ..database import get_db
from ..models import Inoculation, Batch, Calibration, MediaPreparation, User
from ..schemas import InoculationCreate, InoculationResponse
from ..auth import require_technician

router = APIRouter()


@router.post("/batches/{batch_id}/inoculation", response_model=InoculationResponse, status_code=status.HTTP_201_CREATED)
async def create_inoculation(
    batch_id: UUID,
    inoculation_in: InoculationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """
    Log inoculation and set T=0.

    **Validation:**
    - All calibrations must pass
    - Media prep must exist
    - GO decision must be TRUE
    """
    # Verify batch exists
    stmt = select(Batch).where(Batch.batch_id == batch_id)
    result = await db.execute(stmt)
    batch = result.scalar_one_or_none()

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Check media prep exists
    stmt = select(MediaPreparation).where(MediaPreparation.batch_id == batch_id)
    result = await db.execute(stmt)
    media_prep = result.scalar_one_or_none()

    if not media_prep:
        raise HTTPException(status_code=422, detail="Cannot inoculate: no media prep record")

    # Check all calibrations pass
    stmt = select(Calibration).where(Calibration.batch_id == batch_id)
    result = await db.execute(stmt)
    calibrations = result.scalars().all()

    failed_cals = [c for c in calibrations if not c.pass_]
    if failed_cals:
        detail = {
            "message": "Cannot inoculate: calibration failed",
            "failed_calibrations": [{"probe_type": c.probe_type, "slope_percent": float(c.slope_percent) if c.slope_percent else None} for c in failed_cals]
        }
        raise HTTPException(status_code=422, detail=detail)

    # Check GO decision
    if not inoculation_in.go_decision:
        raise HTTPException(status_code=422, detail="Inoculation rejected by operator (GO=FALSE)")

    # Create inoculation (trigger will update batch status)
    inoculation = Inoculation(
        batch_id=batch_id,
        **inoculation_in.model_dump(exclude_unset=True)
    )

    db.add(inoculation)
    await db.commit()
    await db.refresh(inoculation)

    return inoculation
