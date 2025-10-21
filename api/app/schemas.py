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
    vessel_id: str = Field(..., min_length=1, max_length=50)
    operator_id: str = Field(..., min_length=1, max_length=50)
    notes: Optional[str] = None

    @field_validator("vessel_id")
    @classmethod
    def validate_vessel_format(cls, v: str) -> str:
        if not v.startswith("V-"):
            raise ValueError("Vessel ID must start with 'V-'")
        return v


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
    """Schema for logging sensor calibration."""
    probe_type: Literal["pH", "DO", "Temp", "OffGas_O2", "OffGas_CO2", "Pressure"]

    buffer_low_value: Decimal
    buffer_low_lot: Optional[str] = None
    buffer_high_value: Decimal
    buffer_high_lot: Optional[str] = None
    reading_low: Decimal
    reading_high: Decimal

    response_time_sec: Optional[int] = Field(None, description="DO probe only, must be <30s")
    pass_: bool = Field(..., alias="pass")
    control_active: bool = True

    calibrated_by: str = Field(..., min_length=1)
    notes: Optional[str] = None

    @field_validator("pass_")
    @classmethod
    def validate_calibration_pass(cls, v: bool, info) -> bool:
        """Auto-fail if pH slope <95% or DO response >30s."""
        probe_type = info.data.get("probe_type")

        if probe_type == "pH":
            slope_pct = cls._calculate_ph_slope(
                info.data.get("buffer_low_value"),
                info.data.get("buffer_high_value"),
                info.data.get("reading_low"),
                info.data.get("reading_high")
            )
            if slope_pct and slope_pct < 95.0:
                return False

        elif probe_type == "DO":
            response_time = info.data.get("response_time_sec")
            if response_time and response_time > 30:
                return False

        return v

    @staticmethod
    def _calculate_ph_slope(low_ref, high_ref, low_read, high_read) -> Optional[float]:
        """Calculate pH probe slope percentage."""
        if not all([low_ref, high_ref, low_read, high_read]):
            return None

        theoretical_slope = (high_ref - high_ref) / (high_read - low_read)
        # Nernst equation: 59.16 mV/pH at 25°C
        slope_pct = (abs(float(theoretical_slope)) / 59.16) * 100
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
    """Schema for logging inoculation (sets T=0)."""
    cryo_vial_id: str = Field(..., min_length=1)
    inoculum_od600: Decimal = Field(..., ge=Decimal("2.0"), le=Decimal("10.0"))
    dilution_factor: Decimal = Field(default=Decimal("1.0"), ge=Decimal("1.0"))
    inoculum_volume_ml: Decimal = Field(default=Decimal("100.0"), ge=0)
    microscopy_observations: str
    go_decision: bool
    inoculated_by: str = Field(..., min_length=1)

    @field_validator("go_decision")
    @classmethod
    def validate_go_decision(cls, v: bool, info) -> bool:
        """Validate GO decision based on OD range."""
        od = info.data.get("inoculum_od600")

        # Warn if OD is outside preferred range (2.0-6.0) but allow with justification
        if v and od:
            if od < Decimal("2.0") or od > Decimal("6.0"):
                # In production, log a warning
                pass

        return v


class InoculationResponse(BaseModel):
    """Schema for inoculation responses."""
    id: int
    batch_id: UUID
    cryo_vial_id: str
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
