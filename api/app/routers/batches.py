"""
Batch management endpoints.
CRUD operations for batch records.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import csv
from io import StringIO

from ..database import get_db
from ..models import Batch, User, Sample, Calibration, Inoculation, Failure, BatchClosure
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


@router.get("/batches/{batch_id}/export")
async def export_batch(
    batch_id: UUID,
    format: str = Query("markdown", regex="^(csv|markdown|json)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export complete batch data in multiple formats.

    **Formats:**
    - `csv` - For digital twin model training (samples only)
    - `markdown` - For OneNote lab notebook (complete batch record)
    - `json` - For programmatic access

    **Use Cases:**
    - CSV: Copy into Python/R for model training
    - Markdown: Copy/paste into OneNote, GitHub, or lab reports
    - JSON: API integrations, data pipelines
    """
    # Fetch batch with all relationships eagerly loaded
    stmt = (
        select(Batch)
        .options(
            selectinload(Batch.calibrations),
            selectinload(Batch.inoculation),
            selectinload(Batch.samples),
            selectinload(Batch.failures),
            selectinload(Batch.closure),
            selectinload(Batch.media_prep)
        )
        .where(Batch.batch_id == batch_id)
    )
    result = await db.execute(stmt)
    batch = result.scalar_one_or_none()

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found"
        )

    # Generate export based on format
    if format == "csv":
        return _export_csv(batch)
    elif format == "markdown":
        return _export_markdown(batch)
    else:  # json
        return _export_json(batch)


def _export_csv(batch: Batch) -> Response:
    """Export sample data as CSV for model training."""
    output = StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "batch_id",
        "batch_number",
        "phase",
        "timepoint_hours",
        "od600_raw",
        "od600_dilution_factor",
        "od600_calculated",
        "dcw_g_per_l",
        "contamination_detected",
        "sampled_at"
    ])

    # Data rows
    for sample in batch.samples:
        writer.writerow([
            str(batch.batch_id),
            batch.batch_number,
            batch.phase,
            float(sample.timepoint_hours) if sample.timepoint_hours else None,
            float(sample.od600_raw),
            float(sample.od600_dilution_factor),
            float(sample.od600_calculated) if sample.od600_calculated else None,
            float(sample.dcw_g_per_l) if sample.dcw_g_per_l else None,
            sample.contamination_detected,
            sample.sampled_at.isoformat() if sample.sampled_at else None
        ])

    csv_content = output.getvalue()

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=batch_{batch.batch_number}_phase_{batch.phase}_samples.csv"
        }
    )


def _export_markdown(batch: Batch) -> PlainTextResponse:
    """Export complete batch record as Markdown for OneNote/lab notebooks."""

    md = []

    # Header
    md.append(f"# Batch #{batch.batch_number} - Phase {batch.phase}")
    md.append("")
    md.append(f"**Vessel:** {batch.vessel_id}")
    md.append(f"**Operator:** {batch.operator_id}")
    md.append(f"**Status:** {batch.status}")
    md.append(f"**Created:** {batch.created_at.strftime('%Y-%m-%d %H:%M')}")

    if batch.inoculated_at:
        md.append(f"**Inoculated:** {batch.inoculated_at.strftime('%Y-%m-%d %H:%M')}")

    if batch.completed_at:
        runtime = (batch.completed_at - batch.inoculated_at).total_seconds() / 3600
        md.append(f"**Completed:** {batch.completed_at.strftime('%Y-%m-%d %H:%M')} ({runtime:.1f}h runtime)")

    if batch.notes:
        md.append(f"\n**Notes:** {batch.notes}")

    md.append("")
    md.append("---")
    md.append("")

    # Calibrations
    md.append("## Pre-Run Calibrations")
    md.append("")

    if batch.calibrations:
        md.append("| Probe | Buffer Low | Buffer High | Reading Low | Reading High | Slope % | Pass |")
        md.append("|-------|-----------|-------------|-------------|--------------|---------|------|")

        for cal in batch.calibrations:
            slope = f"{float(cal.slope_percent):.1f}%" if cal.slope_percent else "-"
            pass_status = "✅ PASS" if cal.pass_ else "❌ FAIL"

            md.append(
                f"| {cal.probe_type} | "
                f"{float(cal.buffer_low_value) if cal.buffer_low_value else '-'} | "
                f"{float(cal.buffer_high_value) if cal.buffer_high_value else '-'} | "
                f"{float(cal.reading_low) if cal.reading_low else '-'} | "
                f"{float(cal.reading_high) if cal.reading_high else '-'} | "
                f"{slope} | {pass_status} |"
            )
    else:
        md.append("*No calibration records*")

    md.append("")

    # Inoculation
    md.append("## Inoculation")
    md.append("")

    if batch.inoculation:
        inoc = batch.inoculation
        md.append(f"- **Cryo Vial:** {inoc.cryo_vial_id}")
        md.append(f"- **Inoculum OD₆₀₀:** {float(inoc.inoculum_od600):.2f}")
        md.append(f"- **Volume:** {float(inoc.inoculum_volume_ml):.1f} mL")
        md.append(f"- **GO Decision:** {'✅ GO' if inoc.go_decision else '❌ NO-GO'}")

        if inoc.microscopy_observations:
            md.append(f"- **Microscopy:** {inoc.microscopy_observations}")

        md.append(f"- **Inoculated by:** {inoc.inoculated_by}")
    else:
        md.append("*Not yet inoculated*")

    md.append("")

    # Samples
    md.append("## Sample Observations")
    md.append("")

    if batch.samples:
        md.append("| Time (h) | OD₆₀₀ (raw) | Dilution | OD₆₀₀ (calc) | DCW (g/L) | Contamination | Sampled By |")
        md.append("|----------|-------------|----------|--------------|-----------|---------------|------------|")

        for sample in batch.samples:
            time_h = f"{float(sample.timepoint_hours):.1f}" if sample.timepoint_hours else "-"
            od_raw = f"{float(sample.od600_raw):.3f}"
            dilution = f"{float(sample.od600_dilution_factor):.1f}×"
            od_calc = f"{float(sample.od600_calculated):.2f}" if sample.od600_calculated else "-"
            dcw = f"{float(sample.dcw_g_per_l):.2f}" if sample.dcw_g_per_l else "-"
            contam = "⚠️ YES" if sample.contamination_detected else "✅ No"

            md.append(
                f"| {time_h} | {od_raw} | {dilution} | {od_calc} | {dcw} | {contam} | {sample.sampled_by} |"
            )

        md.append("")
        md.append(f"**Total samples:** {len(batch.samples)}")
    else:
        md.append("*No samples yet*")

    md.append("")

    # Failures/Deviations
    if batch.failures:
        md.append("## Failures & Deviations")
        md.append("")

        for failure in batch.failures:
            level_emoji = {1: "🟡", 2: "🟠", 3: "🔴"}
            md.append(f"### {level_emoji.get(failure.deviation_level, '⚪')} Level {failure.deviation_level} - {failure.category}")
            md.append("")
            md.append(f"**Description:** {failure.description}")

            if failure.root_cause:
                md.append(f"**Root Cause:** {failure.root_cause}")

            if failure.corrective_action:
                md.append(f"**Corrective Action:** {failure.corrective_action}")

            md.append(f"**Reported by:** {failure.reported_by}")
            md.append("")

    # Closure
    if batch.closure:
        md.append("## Batch Closure")
        md.append("")
        closure = batch.closure

        md.append(f"- **Final OD₆₀₀:** {float(closure.final_od600):.2f}" if closure.final_od600 else "")
        md.append(f"- **Total Runtime:** {float(closure.total_runtime_hours):.1f} hours" if closure.total_runtime_hours else "")
        md.append(f"- **Glycerol Depletion:** {float(closure.glycerol_depletion_time_hours):.1f} h" if closure.glycerol_depletion_time_hours else "")
        md.append(f"- **DO Spike Observed:** {'Yes' if closure.do_spike_observed else 'No'}")
        md.append(f"- **Outcome:** {closure.outcome}")
        md.append(f"- **Closed by:** {closure.closed_by}")
        md.append(f"- **Approved by:** {closure.approved_by}")

        if closure.notes:
            md.append(f"\n**Final Notes:** {closure.notes}")

    md.append("")
    md.append("---")
    md.append(f"\n*Exported: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*")

    markdown_content = "\n".join(md)

    return PlainTextResponse(
        content=markdown_content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f"attachment; filename=batch_{batch.batch_number}_phase_{batch.phase}_report.md"
        }
    )


def _export_json(batch: Batch) -> dict:
    """Export complete batch record as JSON."""

    return {
        "batch": {
            "batch_id": str(batch.batch_id),
            "batch_number": batch.batch_number,
            "phase": batch.phase,
            "vessel_id": batch.vessel_id,
            "operator_id": batch.operator_id,
            "status": batch.status,
            "created_at": batch.created_at.isoformat() if batch.created_at else None,
            "inoculated_at": batch.inoculated_at.isoformat() if batch.inoculated_at else None,
            "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
            "notes": batch.notes
        },
        "calibrations": [
            {
                "probe_type": cal.probe_type,
                "buffer_low_value": float(cal.buffer_low_value) if cal.buffer_low_value else None,
                "buffer_high_value": float(cal.buffer_high_value) if cal.buffer_high_value else None,
                "reading_low": float(cal.reading_low) if cal.reading_low else None,
                "reading_high": float(cal.reading_high) if cal.reading_high else None,
                "slope_percent": float(cal.slope_percent) if cal.slope_percent else None,
                "pass": cal.pass_,
                "calibrated_by": cal.calibrated_by,
                "calibrated_at": cal.calibrated_at.isoformat() if cal.calibrated_at else None
            }
            for cal in batch.calibrations
        ] if batch.calibrations else [],
        "inoculation": {
            "cryo_vial_id": batch.inoculation.cryo_vial_id,
            "inoculum_od600": float(batch.inoculation.inoculum_od600),
            "inoculum_volume_ml": float(batch.inoculation.inoculum_volume_ml),
            "go_decision": batch.inoculation.go_decision,
            "microscopy_observations": batch.inoculation.microscopy_observations,
            "inoculated_by": batch.inoculation.inoculated_by
        } if batch.inoculation else None,
        "samples": [
            {
                "timepoint_hours": float(sample.timepoint_hours) if sample.timepoint_hours else None,
                "od600_raw": float(sample.od600_raw),
                "od600_dilution_factor": float(sample.od600_dilution_factor),
                "od600_calculated": float(sample.od600_calculated) if sample.od600_calculated else None,
                "dcw_g_per_l": float(sample.dcw_g_per_l) if sample.dcw_g_per_l else None,
                "contamination_detected": sample.contamination_detected,
                "microscopy_observations": sample.microscopy_observations,
                "sampled_by": sample.sampled_by,
                "sampled_at": sample.sampled_at.isoformat() if sample.sampled_at else None
            }
            for sample in batch.samples
        ] if batch.samples else [],
        "failures": [
            {
                "deviation_level": failure.deviation_level,
                "category": failure.category,
                "description": failure.description,
                "root_cause": failure.root_cause,
                "corrective_action": failure.corrective_action,
                "reported_by": failure.reported_by,
                "reported_at": failure.reported_at.isoformat() if failure.reported_at else None
            }
            for failure in batch.failures
        ] if batch.failures else [],
        "closure": {
            "final_od600": float(batch.closure.final_od600) if batch.closure.final_od600 else None,
            "total_runtime_hours": float(batch.closure.total_runtime_hours) if batch.closure.total_runtime_hours else None,
            "glycerol_depletion_time_hours": float(batch.closure.glycerol_depletion_time_hours) if batch.closure.glycerol_depletion_time_hours else None,
            "outcome": batch.closure.outcome,
            "closed_by": batch.closure.closed_by,
            "approved_by": batch.closure.approved_by,
            "notes": batch.closure.notes
        } if batch.closure else None
    }
