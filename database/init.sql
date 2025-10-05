-- Bioprocess Twin - Postgres Schema Initialization
-- Batch-centric electronic lab notebook for manual data capture
-- Based on Technical Plan Section 4.4

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Core Table: batches
CREATE TABLE batches (
    batch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_number INTEGER NOT NULL,
    phase CHAR(1) NOT NULL CHECK (phase IN ('A', 'B', 'C')),
    vessel_id VARCHAR(50) NOT NULL,
    operator_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('setup', 'running', 'complete', 'aborted')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    inoculated_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    notes TEXT,
    UNIQUE(batch_number)
);

-- Child Table: media_preparations
CREATE TABLE media_preparations (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES batches(batch_id) ON DELETE CASCADE,
    recipe_name VARCHAR(100) DEFAULT 'BMGY_Standard_4pc_Glycerol',
    phosphoric_acid_ml NUMERIC(5,2) DEFAULT 26.7,
    calcium_sulfate_g NUMERIC(5,2) DEFAULT 0.93,
    potassium_sulfate_g NUMERIC(5,2) DEFAULT 18.2,
    magnesium_sulfate_g NUMERIC(5,2) DEFAULT 14.9,
    potassium_hydroxide_g NUMERIC(5,2) DEFAULT 4.13,
    glycerol_g NUMERIC(5,2) DEFAULT 40.0,
    final_volume_l NUMERIC(4,2) DEFAULT 0.9,
    autoclave_cycle VARCHAR(50),
    sterility_verified BOOLEAN DEFAULT FALSE,
    prepared_by VARCHAR(50),
    prepared_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes TEXT
);

-- Child Table: calibrations
CREATE TABLE calibrations (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES batches(batch_id) ON DELETE CASCADE,
    probe_type VARCHAR(20) NOT NULL CHECK (probe_type IN ('pH', 'DO', 'Temp', 'OffGas_O2', 'OffGas_CO2', 'Pressure')),
    buffer_low_value NUMERIC(5,2),
    buffer_high_value NUMERIC(5,2),
    reading_low NUMERIC(5,2),
    reading_high NUMERIC(5,2),
    slope_percent NUMERIC(5,2),
    response_time_sec INTEGER,
    drift_from_previous NUMERIC(5,2),
    pass BOOLEAN NOT NULL,
    calibrated_by VARCHAR(50),
    calibrated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes TEXT
);

-- Child Table: inoculations
CREATE TABLE inoculations (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES batches(batch_id) ON DELETE CASCADE,
    cryo_vial_id VARCHAR(100) NOT NULL,
    inoculum_od600 NUMERIC(5,2) NOT NULL CHECK (inoculum_od600 BETWEEN 2.0 AND 10.0),
    inoculum_volume_ml NUMERIC(6,2) DEFAULT 100,
    dilution_factor NUMERIC(5,2) DEFAULT 1.0,
    microscopy_observations TEXT,
    go_decision BOOLEAN NOT NULL,
    inoculated_by VARCHAR(50),
    inoculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(batch_id)
);

-- Child Table: samples
CREATE TABLE samples (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES batches(batch_id) ON DELETE CASCADE,
    timepoint_hours NUMERIC(5,2) NOT NULL,
    sample_volume_ml NUMERIC(5,2) DEFAULT 10,
    od600_raw NUMERIC(8,4) NOT NULL,
    od600_dilution_factor NUMERIC(5,2) DEFAULT 1.0,
    od600_calculated NUMERIC(8,4) NOT NULL,
    dcw_filter_id VARCHAR(100),
    dcw_sample_volume_ml NUMERIC(5,2),
    dcw_filter_wet_weight_g NUMERIC(8,4),
    dcw_filter_dry_weight_g NUMERIC(8,4),
    dcw_g_per_l NUMERIC(8,4),
    contamination_detected BOOLEAN DEFAULT FALSE,
    microscopy_observations TEXT,
    supernatant_cryovial_id VARCHAR(100),
    pellet_cryovial_id VARCHAR(100),
    sampled_by VARCHAR(50),
    sampled_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Child Table: process_changes
CREATE TABLE process_changes (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES batches(batch_id) ON DELETE CASCADE,
    timepoint_hours NUMERIC(5,2) NOT NULL,
    parameter VARCHAR(50) NOT NULL,
    old_value NUMERIC(8,2),
    new_value NUMERIC(8,2),
    reason TEXT NOT NULL,
    supervisor_approval_id VARCHAR(50),
    changed_by VARCHAR(50),
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Child Table: failures (deviations)
CREATE TABLE failures (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES batches(batch_id) ON DELETE CASCADE,
    deviation_level INTEGER NOT NULL CHECK (deviation_level IN (1, 2, 3)),
    deviation_start_time TIMESTAMPTZ NOT NULL,
    deviation_end_time TIMESTAMPTZ,
    category VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    root_cause TEXT,
    corrective_action TEXT,
    impact_assessment TEXT,
    reported_by VARCHAR(50),
    reviewed_by VARCHAR(50),
    reported_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Child Table: batch_closures
CREATE TABLE batch_closures (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES batches(batch_id) ON DELETE CASCADE,
    final_od600 NUMERIC(8,4),
    total_runtime_hours NUMERIC(6,2),
    glycerol_depletion_time_hours NUMERIC(6,2),
    do_spike_observed BOOLEAN,
    max_do_percent NUMERIC(5,2),
    cumulative_base_addition_ml NUMERIC(6,2),
    outcome VARCHAR(50) NOT NULL,
    harvest_method VARCHAR(50),
    closed_by VARCHAR(50),
    approved_by VARCHAR(50),
    closed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(batch_id)
);

-- Indexes for performance
CREATE INDEX idx_batches_phase ON batches(phase);
CREATE INDEX idx_batches_status ON batches(status);
CREATE INDEX idx_calibrations_batch ON calibrations(batch_id);
CREATE INDEX idx_samples_batch ON samples(batch_id);
CREATE INDEX idx_failures_batch ON failures(batch_id);

-- Comments
COMMENT ON TABLE batches IS 'Core batch records - SSoT for all manual data';
COMMENT ON TABLE calibrations IS 'Pre-run sensor calibration records (pH, DO, off-gas, pressure)';
COMMENT ON TABLE inoculations IS 'Inoculum quality checks and GO/NO-GO decisions';
COMMENT ON TABLE samples IS 'In-run manual sampling and analysis (OD, DCW, microscopy)';
COMMENT ON TABLE process_changes IS 'Logged parameter changes during batch execution';
COMMENT ON TABLE failures IS 'Deviation management (Level 1/2/3 classification)';
COMMENT ON TABLE batch_closures IS 'Post-run batch closure and sign-off';

-- Grant permissions (adjust for your deployment)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO bioprocess;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO bioprocess;
