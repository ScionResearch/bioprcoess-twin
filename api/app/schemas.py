"""
Pydantic schemas for request/response validation.
Provides type safety and automatic validation for API endpoints.
"""

from pydantic import BaseModel, Field, field_validator, computed_field
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID
from decimal import Decimal


# ============================================================================
# BATCH SCHEMAS
# ============================================================================

class BatchCreate(BaseModel):
    """Schema for creating a new batch."""
    batch_number: int = Field(..., ge=1, le=18, description="Batch number (1-18)")
    phase: Literal["A", "B", "C"] = Field(..., description="Campaign phase")
    vessel_id: str = Field(..., min_length=1, max_length=50, description="Vessel identifier (any format)")
    operator_id: str = Field(..., min_length=1, max_length=50, description="Operator identifier")
    notes: Optional[str] = None


class BatchResponse(BaseModel):
    """Schema for batch API responses."""
    batch_id: UUID
    batch_number: int
    phase: str
    vessel_id: str
    operator_id: str
    status: str
    created_at: datetime
    created_by: Optional[str]
    inoculated_at: Optional[datetime]
    completed_at: Optional[datetime]
    notes: Optional[str]

    @computed_field
    @property
    def runtime_hours(self) -> Optional[float]:
        """Calculate batch runtime in hours."""
        if self.inoculated_at and self.completed_at:
            delta = self.completed_at - self.inoculated_at
            return round(delta.total_seconds() / 3600, 2)
        return None

    @computed_field
    @property
    def current_timepoint_hours(self) -> Optional[float]:
        """Calculate current timepoint in hours since inoculation."""
        if self.inoculated_at:
            delta = datetime.utcnow() - self.inoculated_at
            return round(delta.total_seconds() / 3600, 2)
        return None

    @computed_field
    @property
    def total_samples_count(self) -> int:
        """Count of samples for this batch."""
        return 0  # Placeholder - will be populated by API route

    @computed_field
    @property
    def calibrations_count(self) -> int:
        """Count of calibrations for this batch."""
        return 0  # Placeholder - will be populated by API route

    @computed_field
    @property
    def critical_failures_count(self) -> int:
        """Count of critical failures for this batch."""
        return 0  # Placeholder - will be populated by API route

    model_config = {"from_attributes": True}


class BatchUpdate(BaseModel):
    """Schema for updating batch metadata (limited fields)."""
    notes: Optional[str] = None
    operator_id: Optional[str] = None


# ============================================================================
# MEDIA PREPARATION SCHEMAS
# ============================================================================

class MediaPreparationCreate(BaseModel):
    """Schema for logging media preparation."""
    recipe_name: str = "Fermentation_Basal_Salts_4pct_Glycerol"

    # Components
    phosphoric_acid_ml: Decimal = Field(default=Decimal("26.7"), ge=0)
    phosphoric_acid_lot: Optional[str] = None
    calcium_sulfate_g: Decimal = Field(default=Decimal("0.93"), ge=0)
    calcium_sulfate_lot: Optional[str] = None
    potassium_sulfate_g: Decimal = Field(default=Decimal("18.2"), ge=0)
    potassium_sulfate_lot: Optional[str] = None
    magnesium_sulfate_g: Decimal = Field(default=Decimal("14.9"), ge=0)
    magnesium_sulfate_lot: Optional[str] = None
    potassium_hydroxide_g: Decimal = Field(default=Decimal("4.13"), ge=0)
    potassium_hydroxide_lot: Optional[str] = None
    glycerol_g: Decimal = Field(default=Decimal("40.0"), ge=0)
    glycerol_lot: Optional[str] = None

    # Preparation details
    final_volume_l: Decimal = Field(default=Decimal("0.9"), ge=0)
    autoclave_cycle: str = Field(..., min_length=1)
    sterility_verified: bool = False
    prepared_by: str = Field(..., min_length=1)
    notes: Optional[str] = None


class MediaPreparationResponse(BaseModel):
    """Schema for media preparation responses."""
    id: int
    batch_id: UUID
    recipe_name: str
    autoclave_cycle: str
    sterility_verified: bool
    prepared_at: datetime
    prepared_by: str

    model_config = {"from_attributes": True}


# ============================================================================
# CALIBRATION SCHEMAS
# ============================================================================

class CalibrationCreate(BaseModel):
    """
    Schema for logging sensor calibration.

    Calibration methods by probe type:
    - pH: 2-point buffer calibration (e.g., pH 4.01 and pH 7.00)
    - DO: 0% (N2 purge) and 100% (air saturation) calibration
    - Temp: Single-point or ice bath verification
    - OffGas_O2: Span gas calibration (N2 for 0%, air for 20.9%)
    - OffGas_CO2: Span gas calibration (N2 for 0%, certified span gas for high point)
    - Pressure: Atmospheric reference or certified gauge
    """
    probe_type: Literal["pH", "DO", "Temp", "OffGas_O2", "OffGas_CO2", "Pressure"]

    # Calibration reference points (terminology adapts to probe type)
    # pH: buffer values (e.g., 4.01, 7.00)
    # DO: saturation % (0%, 100%)
    # Gas sensors: span gas concentrations (0%, 20.9% for O2, etc.)
    # Pressure: reference pressure values
    buffer_low_value: Optional[Decimal] = Field(None, description="Low calibration point reference value")
    buffer_low_lot: Optional[str] = Field(None, description="Lot number for low point reference (buffer/span gas)")
    buffer_high_value: Optional[Decimal] = Field(None, description="High calibration point reference value")
    buffer_high_lot: Optional[str] = Field(None, description="Lot number for high point reference (buffer/span gas)")

    # Actual readings from probe
    reading_low: Optional[Decimal] = Field(None, description="Probe reading at low calibration point")
    reading_high: Optional[Decimal] = Field(None, description="Probe reading at high calibration point")

    # Performance metrics
    response_time_sec: Optional[int] = Field(None, description="Response time in seconds (primarily for DO probe, should be <30s)")
    pass_: bool = Field(..., alias="pass", description="Did calibration meet acceptance criteria?")
    control_active: bool = Field(default=True, description="Will automated control be active for this batch?")

    calibrated_by: str = Field(..., min_length=1)
    notes: Optional[str] = Field(None, description="Additional calibration notes (e.g., temperature, span gas cert number)")

    @field_validator("pass_")
    @classmethod
    def validate_calibration_pass(cls, v: bool, info) -> bool:
        """Auto-fail if pH slope <95% or DO response >30s."""
        probe_type = info.data.get("probe_type")

        if probe_type == "pH":
            # pH probes must have ≥95% slope
            slope_pct = cls._calculate_ph_slope(
                info.data.get("buffer_low_value"),
                info.data.get("buffer_high_value"),
                info.data.get("reading_low"),
                info.data.get("reading_high")
            )
            if slope_pct and slope_pct < 95.0:
                return False

        elif probe_type == "DO":
            # DO probes must respond in <30 seconds
            response_time = info.data.get("response_time_sec")
            if response_time and response_time > 30:
                return False

        return v

    @staticmethod
    def _calculate_ph_slope(low_ref, high_ref, low_read, high_read) -> Optional[float]:
        """
        Calculate pH probe slope percentage using Nernst equation.

        Nernst equation at 25°C: E = E₀ - 59.16 mV/pH × pH
        Ideal slope = 59.16 mV per pH unit

        Example:
        - pH 4.0 buffer → probe reads -177 mV
        - pH 7.0 buffer → probe reads 0 mV
        - delta_mV = 0 - (-177) = 177 mV
        - delta_pH = 7.0 - 4.0 = 3.0
        - slope = 177 / 3.0 = 59 mV/pH
        - slope % = (59 / 59.16) × 100 = 99.7%
        """
        if not all([low_ref, high_ref, low_read, high_read]):
            return None

        delta_pH = float(high_ref) - float(low_ref)
        delta_mV = float(high_read) - float(low_read)

        if delta_pH == 0:
            return None  # Avoid division by zero

        # Slope in mV/pH unit
        measured_slope = delta_mV / delta_pH

        # Nernst ideal slope: 59.16 mV/pH at 25°C
        ideal_slope = 59.16

        # Slope percentage
        slope_pct = (abs(measured_slope) / ideal_slope) * 100
        return round(slope_pct, 1)

    model_config = {"populate_by_name": True}


class CalibrationResponse(BaseModel):
    """Schema for calibration responses."""
    id: int
    batch_id: UUID
    probe_type: str
    slope_percent: Optional[Decimal]
    response_time_sec: Optional[int]
    pass_: bool = Field(..., alias="pass")
    calibrated_at: datetime
    calibrated_by: str

    model_config = {"from_attributes": True, "populate_by_name": True}


# ============================================================================
# INOCULATION SCHEMAS
# ============================================================================

class InoculationCreate(BaseModel):
    """
    Schema for logging inoculation (sets T=0).

    Supports multiple inoculum sources:
    - Cryovial (frozen stock)
    - Plate culture (agar plate)
    - Seed flask (from previous shake flask culture)
    """
    inoculum_source: Optional[str] = Field(
        None,
        description="Source description (e.g., 'Cryo-2024-001', 'Plate YPD-5', 'Seed Flask A')"
    )
    inoculum_od600: Decimal = Field(..., ge=Decimal("0.1"), description="Final inoculum OD600 (typical range: 2-6)")
    dilution_factor: Decimal = Field(default=Decimal("1.0"), ge=Decimal("1.0"))
    inoculum_volume_ml: Decimal = Field(default=Decimal("100.0"), ge=0)
    microscopy_observations: Optional[str] = Field(None, description="Cell morphology, viability observations")
    go_decision: bool = Field(..., description="GO/NO-GO decision to proceed with inoculation")
    inoculated_by: str = Field(..., min_length=1)

    @field_validator("go_decision")
    @classmethod
    def validate_go_decision(cls, v: bool, info) -> bool:
        """Validate GO decision - allow any OD but log warnings for unusual values."""
        od = info.data.get("inoculum_od600")

        # Typical range is 2.0-6.0, but allow any positive OD with GO decision
        if v and od:
            if od < Decimal("0.5"):
                # Very low OD - technician should justify in microscopy_observations
                pass
            elif od > Decimal("10.0"):
                # Very high OD - may indicate over-growth
                pass

        return v


class InoculationResponse(BaseModel):
    """Schema for inoculation responses."""
    id: int
    batch_id: UUID
    inoculum_source: Optional[str]
    inoculum_od600: Decimal
    go_decision: bool
    inoculated_at: datetime
    inoculated_by: str

    model_config = {"from_attributes": True}


# ============================================================================
# SAMPLE SCHEMAS
# ============================================================================

class SampleCreate(BaseModel):
    """Schema for logging in-process sample."""
    sample_volume_ml: Decimal = Field(default=Decimal("10.0"), ge=0)

    # OD600
    od600_raw: Decimal = Field(..., ge=0)
    od600_dilution_factor: Decimal = Field(default=Decimal("1.0"), ge=Decimal("1.0"))

    # DCW (optional)
    dcw_filter_id: Optional[str] = None
    dcw_sample_volume_ml: Optional[Decimal] = Field(None, ge=0)
    dcw_filter_wet_weight_g: Optional[Decimal] = Field(None, ge=0)
    dcw_filter_dry_weight_g: Optional[Decimal] = Field(None, ge=0)

    # Quality
    contamination_detected: bool = False
    microscopy_observations: Optional[str] = None

    # Archival
    supernatant_cryovial_id: Optional[str] = None
    pellet_cryovial_id: Optional[str] = None

    sampled_by: str = Field(..., min_length=1)

    @computed_field
    @property
    def od600_calculated(self) -> Decimal:
        """Auto-calculate final OD600."""
        return self.od600_raw * self.od600_dilution_factor


class SampleResponse(BaseModel):
    """Schema for sample responses."""
    id: int
    batch_id: UUID
    timepoint_hours: Optional[Decimal]
    od600_raw: Decimal
    od600_calculated: Optional[Decimal]
    dcw_g_per_l: Optional[Decimal]
    contamination_detected: bool
    sampled_at: datetime
    sampled_by: str

    model_config = {"from_attributes": True}


# ============================================================================
# FAILURE SCHEMAS
# ============================================================================

class FailureCreate(BaseModel):
    """Schema for logging deviation/failure."""
    deviation_level: Literal[1, 2, 3]
    deviation_start_time: datetime
    deviation_end_time: Optional[datetime] = None

    category: Literal[
        "Contamination", "DO_Crash", "DO_Crash_No_Control",
        "pH_Excursion", "pH_Drift_No_Control", "Temp_Excursion",
        "Sensor_Failure", "Power_Outage", "Sampling_Missed",
        "O2_Enrichment_Used", "Other"
    ]

    description: str = Field(..., min_length=10)
    root_cause: Optional[str] = None
    corrective_action: Optional[str] = None
    impact_assessment: Optional[str] = None

    reported_by: str = Field(..., min_length=1)
    reviewed_by: Optional[str] = None


class FailureResponse(BaseModel):
    """Schema for failure responses."""
    id: int
    batch_id: UUID
    deviation_level: int
    category: str
    description: str
    reported_at: datetime
    reported_by: str
    reviewed_by: Optional[str]

    model_config = {"from_attributes": True}


# ============================================================================
# BATCH CLOSURE SCHEMAS
# ============================================================================

class BatchClosureCreate(BaseModel):
    """Schema for closing a batch."""
    final_od600: Decimal = Field(..., ge=0)
    total_runtime_hours: Decimal = Field(..., ge=0)
    glycerol_depletion_time_hours: Decimal = Field(..., ge=0)

    do_spike_observed: bool = True
    max_do_percent: Optional[Decimal] = Field(None, ge=0, le=100)

    cumulative_base_addition_ml: Optional[Decimal] = Field(None, ge=0)

    outcome: Literal["Complete", "Aborted_Contamination", "Aborted_Sensor_Failure", "Aborted_Other"]
    harvest_method: Optional[Literal["Cell_Banking", "Disposal"]] = None

    closed_by: str = Field(..., min_length=1)
    approved_by: str = Field(..., min_length=1, description="Process Engineer approval required")
    notes: Optional[str] = None


class BatchClosureResponse(BaseModel):
    """Schema for batch closure responses."""
    id: int
    batch_id: UUID
    final_od600: Decimal
    total_runtime_hours: Decimal
    outcome: str
    closed_at: datetime
    approved_by: str

    model_config = {"from_attributes": True}


# ============================================================================
# USER/AUTH SCHEMAS
# ============================================================================

class UserCreate(BaseModel):
    """Schema for creating a new user."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    role: Literal["technician", "engineer", "admin", "read_only"]
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user responses (no password)."""
    user_id: int
    username: str
    role: str
    full_name: Optional[str]
    active: bool

    model_config = {"from_attributes": True}
    
    @classmethod
    def from_orm(cls, obj):
        """Map database 'id' field to 'user_id' for API responses."""
        data = obj.__dict__.copy() if hasattr(obj, '__dict__') else obj
        if 'id' in data:
            data['user_id'] = data.pop('id')
        return cls(**data)


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for decoded JWT token data."""
    username: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    """Schema for login request."""
    username: str
    password: str


# ============================================================================
# ERROR SCHEMAS
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response format."""
    status: Literal["error"]
    code: int
    message: str
    detail: Optional[dict] = None
    timestamp: datetime
    path: str


class ValidationErrorDetail(BaseModel):
    """Pydantic validation error detail."""
    loc: list[str]
    msg: str
    type: str
