-- ============================================================================
-- Pichia pastoris Digital Twin - Manual Data Database Schema
-- Version: 2.0
-- Created: 2025-10-20
-- Description: Batch-centric schema for manual observations and quality data
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- PARENT TABLE: batches
-- ============================================================================
CREATE TABLE batches (
    batch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_number INTEGER NOT NULL,
    phase CHAR(1) NOT NULL CHECK (phase IN ('A', 'B', 'C')),
    vessel_id VARCHAR(50) NOT NULL,
    operator_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'complete', 'aborted')),

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(50),
    inoculated_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Notes
    notes TEXT,

    -- Constraints
    CONSTRAINT unique_batch_per_phase UNIQUE (batch_number, phase)
);

-- Indexes
CREATE INDEX idx_batches_phase ON batches(phase);
CREATE INDEX idx_batches_status ON batches(status);
CREATE INDEX idx_batches_vessel ON batches(vessel_id);
CREATE INDEX idx_batches_created_at ON batches(created_at DESC);

COMMENT ON TABLE batches IS 'Core batch records - SSoT for all manual data';

-- ============================================================================
-- CHILD TABLE: media_preparations
-- ============================================================================
CREATE TABLE media_preparations (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES batches(batch_id) ON DELETE CASCADE,

    -- Recipe details
    recipe_name VARCHAR(100) DEFAULT 'Fermentation_Basal_Salts_4pct_Glycerol',

    -- Components (per Batch Run Plan Sec 3.1.2)
    phosphoric_acid_ml NUMERIC(6,2) DEFAULT 26.7,
    phosphoric_acid_lot VARCHAR(50),
    calcium_sulfate_g NUMERIC(6,2) DEFAULT 0.93,
    calcium_sulfate_lot VARCHAR(50),
    potassium_sulfate_g NUMERIC(6,2) DEFAULT 18.2,
    potassium_sulfate_lot VARCHAR(50),
    magnesium_sulfate_g NUMERIC(6,2) DEFAULT 14.9,
    magnesium_sulfate_lot VARCHAR(50),
    potassium_hydroxide_g NUMERIC(6,2) DEFAULT 4.13,
    potassium_hydroxide_lot VARCHAR(50),
    glycerol_g NUMERIC(6,2) DEFAULT 40.0,
    glycerol_lot VARCHAR(50),

    -- Preparation details
    final_volume_l NUMERIC(4,2) DEFAULT 0.9,
    autoclave_cycle VARCHAR(50) NOT NULL,
    sterility_verified BOOLEAN DEFAULT FALSE,

    -- Metadata
    prepared_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    prepared_by VARCHAR(50),
    notes TEXT,

    -- One media prep per batch
    CONSTRAINT one_media_prep_per_batch UNIQUE (batch_id)
);

CREATE INDEX idx_media_batch ON media_preparations(batch_id);

COMMENT ON TABLE media_preparations IS 'Media preparation records with lot traceability';

-- ============================================================================
-- CHILD TABLE: calibrations
-- ============================================================================
CREATE TABLE calibrations (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES batches(batch_id) ON DELETE CASCADE,

    -- Probe type
    probe_type VARCHAR(20) NOT NULL CHECK (probe_type IN ('pH', 'DO', 'Temp', 'OffGas_O2', 'OffGas_CO2', 'Pressure')),

    -- 2-point calibration data
    buffer_low_value NUMERIC(6,2),
    buffer_low_lot VARCHAR(50),
    buffer_high_value NUMERIC(6,2),
    buffer_high_lot VARCHAR(50),
    reading_low NUMERIC(8,3),
    reading_high NUMERIC(8,3),

    -- Performance metrics
    slope_percent NUMERIC(5,2),  -- pH only (auto-calculated)
    response_time_sec INTEGER,   -- DO only
    drift_from_previous NUMERIC(5,2),

    -- Pass/fail
    pass BOOLEAN NOT NULL,
    control_active BOOLEAN DEFAULT TRUE,

    -- Metadata
    calibrated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    calibrated_by VARCHAR(50),
    notes TEXT
);

CREATE INDEX idx_calibrations_batch ON calibrations(batch_id);
CREATE INDEX idx_calibrations_probe_type ON calibrations(batch_id, probe_type);

COMMENT ON TABLE calibrations IS 'Pre-run sensor calibration records (pH, DO, off-gas, pressure)';

-- ============================================================================
-- CHILD TABLE: inoculations
-- ============================================================================
CREATE TABLE inoculations (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES batches(batch_id) ON DELETE CASCADE,

    -- Inoculum source
    cryo_vial_id VARCHAR(100) NOT NULL,

    -- OD measurements
    inoculum_od600 NUMERIC(6,3) NOT NULL CHECK (inoculum_od600 BETWEEN 2.0 AND 10.0),
    dilution_factor NUMERIC(6,2) DEFAULT 1.0,
    inoculum_volume_ml NUMERIC(6,2) DEFAULT 100.0,

    -- Quality check
    microscopy_observations TEXT,
    go_decision BOOLEAN NOT NULL,

    -- Metadata
    inoculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    inoculated_by VARCHAR(50),

    -- One inoculation per batch
    CONSTRAINT one_inoculation_per_batch UNIQUE (batch_id)
);

CREATE INDEX idx_inoculations_batch ON inoculations(batch_id);

COMMENT ON TABLE inoculations IS 'Inoculum quality checks and GO/NO-GO decisions';

-- ============================================================================
-- CHILD TABLE: samples
-- ============================================================================
CREATE TABLE samples (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES batches(batch_id) ON DELETE CASCADE,

    -- Timepoint (auto-calculated from inoculated_at)
    timepoint_hours NUMERIC(6,2),

    -- Sample volume
    sample_volume_ml NUMERIC(6,2) DEFAULT 10.0,

    -- OD600 measurements
    od600_raw NUMERIC(8,4) NOT NULL,
    od600_dilution_factor NUMERIC(6,2) DEFAULT 1.0,
    od600_calculated NUMERIC(8,4),  -- Auto-calculated: raw × dilution

    -- DCW (Dry Cell Weight) measurements
    dcw_filter_id VARCHAR(100),
    dcw_sample_volume_ml NUMERIC(6,2),
    dcw_filter_wet_weight_g NUMERIC(8,4),
    dcw_filter_dry_weight_g NUMERIC(8,4),
    dcw_g_per_l NUMERIC(8,3),  -- Auto-calculated

    -- Quality observations
    contamination_detected BOOLEAN DEFAULT FALSE,
    microscopy_observations TEXT,

    -- Sample archival
    supernatant_cryovial_id VARCHAR(100),
    pellet_cryovial_id VARCHAR(100),

    -- Metadata
    sampled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sampled_by VARCHAR(50)
);

CREATE INDEX idx_samples_batch ON samples(batch_id);
CREATE INDEX idx_samples_timepoint ON samples(batch_id, timepoint_hours);

COMMENT ON TABLE samples IS 'In-run manual sampling and analysis (OD, DCW, microscopy)';

-- ============================================================================
-- CHILD TABLE: process_changes
-- ============================================================================
CREATE TABLE process_changes (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES batches(batch_id) ON DELETE CASCADE,

    -- Change details
    timepoint_hours NUMERIC(6,2),
    parameter VARCHAR(50) NOT NULL,  -- e.g., 'Agitation', 'Temperature', 'Airflow'
    old_value NUMERIC(8,2),
    new_value NUMERIC(8,2),
    reason TEXT NOT NULL,
    supervisor_approval_id VARCHAR(50),

    -- Metadata
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    changed_by VARCHAR(50)
);

CREATE INDEX idx_process_changes_batch ON process_changes(batch_id);

COMMENT ON TABLE process_changes IS 'Logged parameter changes during batch execution';

-- ============================================================================
-- CHILD TABLE: failures
-- ============================================================================
CREATE TABLE failures (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES batches(batch_id) ON DELETE CASCADE,

    -- Severity
    deviation_level INTEGER NOT NULL CHECK (deviation_level IN (1, 2, 3)),

    -- Timing
    deviation_start_time TIMESTAMPTZ NOT NULL,
    deviation_end_time TIMESTAMPTZ,

    -- Classification
    category VARCHAR(50) NOT NULL CHECK (category IN (
        'Contamination',
        'DO_Crash',
        'DO_Crash_No_Control',
        'pH_Excursion',
        'pH_Drift_No_Control',
        'Temp_Excursion',
        'Sensor_Failure',
        'Power_Outage',
        'Sampling_Missed',
        'O2_Enrichment_Used',
        'Other'
    )),

    -- Details
    description TEXT NOT NULL,
    root_cause TEXT,
    corrective_action TEXT,
    impact_assessment TEXT,

    -- Review
    reported_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reported_by VARCHAR(50),
    reviewed_by VARCHAR(50),
    reviewed_at TIMESTAMPTZ
);

CREATE INDEX idx_failures_batch ON failures(batch_id);
CREATE INDEX idx_failures_level ON failures(batch_id, deviation_level);

COMMENT ON TABLE failures IS 'Deviation management (Level 1/2/3 classification)';

-- ============================================================================
-- CHILD TABLE: batch_closures
-- ============================================================================
CREATE TABLE batch_closures (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES batches(batch_id) ON DELETE CASCADE,

    -- Final metrics
    final_od600 NUMERIC(8,4),
    total_runtime_hours NUMERIC(6,2),
    glycerol_depletion_time_hours NUMERIC(6,2),

    -- DO spike observation
    do_spike_observed BOOLEAN DEFAULT TRUE,
    max_do_percent NUMERIC(5,2),

    -- Consumables
    cumulative_base_addition_ml NUMERIC(8,2),

    -- Outcome
    outcome VARCHAR(50) NOT NULL CHECK (outcome IN (
        'Complete',
        'Aborted_Contamination',
        'Aborted_Sensor_Failure',
        'Aborted_Other'
    )),
    harvest_method VARCHAR(50) CHECK (harvest_method IN ('Cell_Banking', 'Disposal')),

    -- Sign-off
    closed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_by VARCHAR(50),
    approved_by VARCHAR(50) NOT NULL,  -- Process Engineer required
    notes TEXT,

    -- One closure per batch
    CONSTRAINT one_closure_per_batch UNIQUE (batch_id)
);

CREATE INDEX idx_closures_batch ON batch_closures(batch_id);

COMMENT ON TABLE batch_closures IS 'Post-run batch closure and sign-off';

-- ============================================================================
-- USERS TABLE (for authentication)
-- ============================================================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- bcrypt hash
    role VARCHAR(20) NOT NULL CHECK (role IN ('technician', 'engineer', 'admin', 'read_only')),
    full_name VARCHAR(100),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login TIMESTAMPTZ
);

CREATE INDEX idx_users_username ON users(username);

COMMENT ON TABLE users IS 'User accounts with RBAC roles';

-- ============================================================================
-- AUDIT LOG TABLE (for all modifications)
-- ============================================================================
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    username VARCHAR(50) NOT NULL,
    action VARCHAR(10) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    table_name VARCHAR(50) NOT NULL,
    record_id INTEGER,
    batch_id UUID,
    changes JSONB,  -- Store old/new values
    ip_address INET
);

CREATE INDEX idx_audit_timestamp ON audit_log(timestamp DESC);
CREATE INDEX idx_audit_username ON audit_log(username);
CREATE INDEX idx_audit_batch ON audit_log(batch_id);

COMMENT ON TABLE audit_log IS 'Append-only audit trail for all data modifications';

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Function: Auto-calculate timepoint_hours for samples
CREATE OR REPLACE FUNCTION calculate_sample_timepoint()
RETURNS TRIGGER AS $$
DECLARE
    inoculation_time TIMESTAMPTZ;
BEGIN
    -- Get inoculation timestamp from parent batch
    SELECT inoculated_at INTO inoculation_time
    FROM batches
    WHERE batch_id = NEW.batch_id;

    IF inoculation_time IS NOT NULL THEN
        NEW.timepoint_hours := EXTRACT(EPOCH FROM (NEW.sampled_at - inoculation_time)) / 3600.0;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sample_timepoint
    BEFORE INSERT OR UPDATE ON samples
    FOR EACH ROW
    EXECUTE FUNCTION calculate_sample_timepoint();

-- Function: Auto-calculate OD600
CREATE OR REPLACE FUNCTION calculate_od600()
RETURNS TRIGGER AS $$
BEGIN
    NEW.od600_calculated := NEW.od600_raw * NEW.od600_dilution_factor;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_od600_calculated
    BEFORE INSERT OR UPDATE ON samples
    FOR EACH ROW
    EXECUTE FUNCTION calculate_od600();

-- Function: Auto-calculate DCW
CREATE OR REPLACE FUNCTION calculate_dcw()
RETURNS TRIGGER AS $$
DECLARE
    dry_mass_g NUMERIC;
BEGIN
    IF NEW.dcw_filter_dry_weight_g IS NOT NULL
       AND NEW.dcw_filter_wet_weight_g IS NOT NULL
       AND NEW.dcw_sample_volume_ml IS NOT NULL THEN

        dry_mass_g := NEW.dcw_filter_dry_weight_g - NEW.dcw_filter_wet_weight_g;
        NEW.dcw_g_per_l := (dry_mass_g / NEW.dcw_sample_volume_ml) * 1000.0;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_dcw_calculated
    BEFORE INSERT OR UPDATE ON samples
    FOR EACH ROW
    EXECUTE FUNCTION calculate_dcw();

-- Function: Update batch status on inoculation
CREATE OR REPLACE FUNCTION update_batch_on_inoculation()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.go_decision = true THEN
        UPDATE batches
        SET
            inoculated_at = NEW.inoculated_at,
            status = 'running'
        WHERE batch_id = NEW.batch_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_batch_inoculation
    AFTER INSERT ON inoculations
    FOR EACH ROW
    EXECUTE FUNCTION update_batch_on_inoculation();

-- Function: Update batch status on closure
CREATE OR REPLACE FUNCTION update_batch_on_closure()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE batches
    SET
        completed_at = NEW.closed_at,
        status = CASE
            WHEN NEW.outcome = 'Complete' THEN 'complete'
            ELSE 'aborted'
        END
    WHERE batch_id = NEW.batch_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_batch_closure
    AFTER INSERT ON batch_closures
    FOR EACH ROW
    EXECUTE FUNCTION update_batch_on_closure();

-- Function: Auto-calculate pH slope percentage
CREATE OR REPLACE FUNCTION calculate_ph_slope()
RETURNS TRIGGER AS $$
DECLARE
    delta_pH NUMERIC;
    delta_mV NUMERIC;
    measured_slope NUMERIC;
    ideal_slope NUMERIC := 59.16;  -- Nernst slope at 25°C in mV/pH
BEGIN
    IF NEW.probe_type = 'pH'
       AND NEW.buffer_low_value IS NOT NULL
       AND NEW.buffer_high_value IS NOT NULL
       AND NEW.reading_low IS NOT NULL
       AND NEW.reading_high IS NOT NULL THEN

        -- Calculate deltas
        delta_pH := NEW.buffer_high_value - NEW.buffer_low_value;
        delta_mV := NEW.reading_high - NEW.reading_low;

        -- Prevent division by zero
        IF delta_pH = 0 THEN
            NEW.slope_percent := NULL;
            RETURN NEW;
        END IF;

        -- Calculate measured slope in mV/pH
        measured_slope := delta_mV / delta_pH;

        -- Calculate slope percentage: (measured / ideal) × 100
        NEW.slope_percent := (ABS(measured_slope) / ideal_slope) * 100.0;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_ph_slope IS 'Auto-calculate pH probe slope percentage using Nernst equation.
Ideal slope at 25°C = 59.16 mV/pH. Acceptable range: 95-105% (56.2-62.1 mV/pH).
Formula: slope % = (|delta_mV / delta_pH| / 59.16) × 100';

CREATE TRIGGER trg_ph_slope
    BEFORE INSERT OR UPDATE ON calibrations
    FOR EACH ROW
    EXECUTE FUNCTION calculate_ph_slope();

-- ============================================================================
-- VIEWS (for common queries)
-- ============================================================================

-- View: Batch summary with all child record counts
CREATE VIEW batch_summary AS
SELECT
    b.batch_id,
    b.batch_number,
    b.phase,
    b.vessel_id,
    b.status,
    b.created_at,
    b.inoculated_at,
    b.completed_at,
    EXTRACT(EPOCH FROM (COALESCE(b.completed_at, NOW()) - b.inoculated_at)) / 3600.0 AS runtime_hours,

    -- Child record counts
    (SELECT COUNT(*) FROM media_preparations mp WHERE mp.batch_id = b.batch_id) AS has_media_prep,
    (SELECT COUNT(*) FROM calibrations c WHERE c.batch_id = b.batch_id) AS calibration_count,
    (SELECT COUNT(*) FROM calibrations c WHERE c.batch_id = b.batch_id AND c.pass = true) AS calibrations_passed,
    (SELECT COUNT(*) FROM inoculations i WHERE i.batch_id = b.batch_id) AS has_inoculation,
    (SELECT COUNT(*) FROM samples s WHERE s.batch_id = b.batch_id) AS sample_count,
    (SELECT COUNT(*) FROM failures f WHERE f.batch_id = b.batch_id) AS failure_count,
    (SELECT COUNT(*) FROM failures f WHERE f.batch_id = b.batch_id AND f.deviation_level = 3) AS critical_failures,
    (SELECT COUNT(*) FROM batch_closures bc WHERE bc.batch_id = b.batch_id) AS has_closure

FROM batches b
ORDER BY b.created_at DESC;

-- ============================================================================
-- SEED DATA (for development/testing)
-- ============================================================================

-- Create default admin user (password: 'admin123' - CHANGE IN PRODUCTION!)
-- Password hash generated with bcrypt cost factor 12
INSERT INTO users (username, password_hash, role, full_name, active) VALUES
    ('admin', '$2b$12$/D8WErR/YZtQnL.6JC.aJ.z3JixqRm7sFc3EfmLh4YT6NghGto/FC', 'admin', 'System Administrator', true),
    ('tech01', '$2b$12$4XAlLk4YISFTwrkhmEwFPeolFiT8bVVMwBmncaDGk4iXeEsG5BOdq', 'technician', 'Lab Technician 1', true),
    ('eng01', '$2b$12$FAElPchdRSsnC870s2kI5OOT.tFMmcqO8jE9HLM59JyA6ufcauh8S', 'engineer', 'Process Engineer 1', true);

-- ============================================================================
-- PERMISSIONS (for application user)
-- ============================================================================

-- Note: Run these commands manually with a secure password
-- CREATE USER pichia_api WITH PASSWORD 'your_secure_password_here';
-- GRANT CONNECT ON DATABASE pichia_manual_data TO pichia_api;
-- GRANT USAGE ON SCHEMA public TO pichia_api;
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO pichia_api;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO pichia_api;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT 'Database schema created successfully!' AS status;
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name;
