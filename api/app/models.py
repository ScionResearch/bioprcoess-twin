"""
SQLAlchemy ORM models for manual data collection.
Matches the database schema in database/init.sql
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, ForeignKey,
    DateTime, CheckConstraint, UniqueConstraint, CHAR, DECIMAL
)
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from .database import Base


class Batch(Base):
    """Parent table for all batch records."""

    __tablename__ = "batches"

    batch_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_number = Column(Integer, nullable=False)
    phase = Column(CHAR(1), nullable=False)
    vessel_id = Column(String(50), nullable=False)
    operator_id = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="pending")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(String(50))
    inoculated_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    notes = Column(Text)

    # Relationships
    media_prep = relationship("MediaPreparation", back_populates="batch", uselist=False, cascade="all, delete-orphan")
    calibrations = relationship("Calibration", back_populates="batch", cascade="all, delete-orphan")
    inoculation = relationship("Inoculation", back_populates="batch", uselist=False, cascade="all, delete-orphan")
    samples = relationship("Sample", back_populates="batch", order_by="Sample.timepoint_hours", cascade="all, delete-orphan")
    process_changes = relationship("ProcessChange", back_populates="batch", cascade="all, delete-orphan")
    failures = relationship("Failure", back_populates="batch", cascade="all, delete-orphan")
    closure = relationship("BatchClosure", back_populates="batch", uselist=False, cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("phase IN ('A', 'B', 'C')", name="check_phase"),
        CheckConstraint("status IN ('pending', 'running', 'complete', 'aborted')", name="check_status"),
        UniqueConstraint("batch_number", "phase", name="unique_batch_per_phase"),
    )


class MediaPreparation(Base):
    """Media preparation records with lot traceability."""

    __tablename__ = "media_preparations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.batch_id", ondelete="CASCADE"), nullable=False)

    # Recipe
    recipe_name = Column(String(100), default="Fermentation_Basal_Salts_4pct_Glycerol")

    # Components
    phosphoric_acid_ml = Column(DECIMAL(6, 2), default=26.7)
    phosphoric_acid_lot = Column(String(50))
    calcium_sulfate_g = Column(DECIMAL(6, 2), default=0.93)
    calcium_sulfate_lot = Column(String(50))
    potassium_sulfate_g = Column(DECIMAL(6, 2), default=18.2)
    potassium_sulfate_lot = Column(String(50))
    magnesium_sulfate_g = Column(DECIMAL(6, 2), default=14.9)
    magnesium_sulfate_lot = Column(String(50))
    potassium_hydroxide_g = Column(DECIMAL(6, 2), default=4.13)
    potassium_hydroxide_lot = Column(String(50))
    glycerol_g = Column(DECIMAL(6, 2), default=40.0)
    glycerol_lot = Column(String(50))

    # Preparation
    final_volume_l = Column(DECIMAL(4, 2), default=0.9)
    autoclave_cycle = Column(String(50), nullable=False)
    sterility_verified = Column(Boolean, default=False)

    # Metadata
    prepared_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    prepared_by = Column(String(50))
    notes = Column(Text)

    # Relationship
    batch = relationship("Batch", back_populates="media_prep")

    __table_args__ = (
        UniqueConstraint("batch_id", name="one_media_prep_per_batch"),
    )


class Calibration(Base):
    """Sensor calibration records."""

    __tablename__ = "calibrations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.batch_id", ondelete="CASCADE"), nullable=False)

    probe_type = Column(String(20), nullable=False)

    # 2-point calibration
    buffer_low_value = Column(DECIMAL(6, 2))
    buffer_low_lot = Column(String(50))
    buffer_high_value = Column(DECIMAL(6, 2))
    buffer_high_lot = Column(String(50))
    reading_low = Column(DECIMAL(8, 3))
    reading_high = Column(DECIMAL(8, 3))

    # Performance
    slope_percent = Column(DECIMAL(5, 2))  # Auto-calculated for pH
    response_time_sec = Column(Integer)  # For DO
    drift_from_previous = Column(DECIMAL(5, 2))

    # Pass/fail
    pass_ = Column("pass", Boolean, nullable=False)
    control_active = Column(Boolean, default=True)

    # Metadata
    calibrated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    calibrated_by = Column(String(50))
    notes = Column(Text)

    # Relationship
    batch = relationship("Batch", back_populates="calibrations")

    __table_args__ = (
        CheckConstraint(
            "probe_type IN ('pH', 'DO', 'Temp', 'OffGas_O2', 'OffGas_CO2', 'Pressure')",
            name="check_probe_type"
        ),
    )


class Inoculation(Base):
    """Inoculation quality check and GO/NO-GO decision."""

    __tablename__ = "inoculations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.batch_id", ondelete="CASCADE"), nullable=False)

    cryo_vial_id = Column(String(100), nullable=False)

    # OD measurements
    inoculum_od600 = Column(DECIMAL(6, 3), nullable=False)
    dilution_factor = Column(DECIMAL(6, 2), default=1.0)
    inoculum_volume_ml = Column(DECIMAL(6, 2), default=100.0)

    # Quality
    microscopy_observations = Column(Text)
    go_decision = Column(Boolean, nullable=False)

    # Metadata
    inoculated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    inoculated_by = Column(String(50))

    # Relationship
    batch = relationship("Batch", back_populates="inoculation")

    __table_args__ = (
        CheckConstraint("inoculum_od600 BETWEEN 2.0 AND 10.0", name="check_inoculum_od600"),
        UniqueConstraint("batch_id", name="one_inoculation_per_batch"),
    )


class Sample(Base):
    """In-process sample observations."""

    __tablename__ = "samples"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.batch_id", ondelete="CASCADE"), nullable=False)

    timepoint_hours = Column(DECIMAL(6, 2))  # Auto-calculated by trigger

    sample_volume_ml = Column(DECIMAL(6, 2), default=10.0)

    # OD600
    od600_raw = Column(DECIMAL(8, 4), nullable=False)
    od600_dilution_factor = Column(DECIMAL(6, 2), default=1.0)
    od600_calculated = Column(DECIMAL(8, 4))  # Auto-calculated by trigger

    # DCW
    dcw_filter_id = Column(String(100))
    dcw_sample_volume_ml = Column(DECIMAL(6, 2))
    dcw_filter_wet_weight_g = Column(DECIMAL(8, 4))
    dcw_filter_dry_weight_g = Column(DECIMAL(8, 4))
    dcw_g_per_l = Column(DECIMAL(8, 3))  # Auto-calculated by trigger

    # Quality
    contamination_detected = Column(Boolean, default=False)
    microscopy_observations = Column(Text)

    # Archival
    supernatant_cryovial_id = Column(String(100))
    pellet_cryovial_id = Column(String(100))

    # Metadata
    sampled_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    sampled_by = Column(String(50))

    # Relationship
    batch = relationship("Batch", back_populates="samples")


class ProcessChange(Base):
    """Process parameter changes during batch."""

    __tablename__ = "process_changes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.batch_id", ondelete="CASCADE"), nullable=False)

    timepoint_hours = Column(DECIMAL(6, 2))
    parameter = Column(String(50), nullable=False)
    old_value = Column(DECIMAL(8, 2))
    new_value = Column(DECIMAL(8, 2))
    reason = Column(Text, nullable=False)
    supervisor_approval_id = Column(String(50))

    # Metadata
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    changed_by = Column(String(50))

    # Relationship
    batch = relationship("Batch", back_populates="process_changes")


class Failure(Base):
    """Failure/deviation records."""

    __tablename__ = "failures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.batch_id", ondelete="CASCADE"), nullable=False)

    deviation_level = Column(Integer, nullable=False)

    # Timing
    deviation_start_time = Column(DateTime(timezone=True), nullable=False)
    deviation_end_time = Column(DateTime(timezone=True))

    # Classification
    category = Column(String(50), nullable=False)

    # Details
    description = Column(Text, nullable=False)
    root_cause = Column(Text)
    corrective_action = Column(Text)
    impact_assessment = Column(Text)

    # Review
    reported_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reported_by = Column(String(50))
    reviewed_by = Column(String(50))
    reviewed_at = Column(DateTime(timezone=True))

    # Relationship
    batch = relationship("Batch", back_populates="failures")

    __table_args__ = (
        CheckConstraint("deviation_level IN (1, 2, 3)", name="check_deviation_level"),
        CheckConstraint(
            """category IN (
                'Contamination', 'DO_Crash', 'DO_Crash_No_Control',
                'pH_Excursion', 'pH_Drift_No_Control', 'Temp_Excursion',
                'Sensor_Failure', 'Power_Outage', 'Sampling_Missed',
                'O2_Enrichment_Used', 'Other'
            )""",
            name="check_category"
        ),
    )


class BatchClosure(Base):
    """Batch closure and sign-off."""

    __tablename__ = "batch_closures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.batch_id", ondelete="CASCADE"), nullable=False)

    # Final metrics
    final_od600 = Column(DECIMAL(8, 4))
    total_runtime_hours = Column(DECIMAL(6, 2))
    glycerol_depletion_time_hours = Column(DECIMAL(6, 2))

    # DO spike
    do_spike_observed = Column(Boolean, default=True)
    max_do_percent = Column(DECIMAL(5, 2))

    # Consumables
    cumulative_base_addition_ml = Column(DECIMAL(8, 2))

    # Outcome
    outcome = Column(String(50), nullable=False)
    harvest_method = Column(String(50))

    # Sign-off
    closed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    closed_by = Column(String(50))
    approved_by = Column(String(50), nullable=False)
    notes = Column(Text)

    # Relationship
    batch = relationship("Batch", back_populates="closure")

    __table_args__ = (
        CheckConstraint(
            "outcome IN ('Complete', 'Aborted_Contamination', 'Aborted_Sensor_Failure', 'Aborted_Other')",
            name="check_outcome"
        ),
        CheckConstraint("harvest_method IN ('Cell_Banking', 'Disposal')", name="check_harvest_method"),
        UniqueConstraint("batch_id", name="one_closure_per_batch"),
    )


class User(Base):
    """User accounts with RBAC."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    full_name = Column(String(100))
    active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "role IN ('technician', 'engineer', 'admin', 'read_only')",
            name="check_role"
        ),
    )


class AuditLog(Base):
    """Append-only audit trail."""

    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    username = Column(String(50), nullable=False)
    action = Column(String(10), nullable=False)
    table_name = Column(String(50), nullable=False)
    record_id = Column(Integer)
    batch_id = Column(UUID(as_uuid=True))
    changes = Column(JSONB)
    ip_address = Column(INET)

    __table_args__ = (
        CheckConstraint("action IN ('INSERT', 'UPDATE', 'DELETE')", name="check_action"),
    )
