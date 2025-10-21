-- ============================================================================
-- Migration: Flexible ELN Fields
-- Version: 001
-- Date: 2025-10-22
-- Description: Make electronic lab notebook more flexible and realistic
-- ============================================================================

-- Changes:
-- 1. Remove rigid vessel_id validation (was enforced in app layer anyway)
-- 2. Rename cryo_vial_id -> inoculum_source (support plates, seed flasks, etc.)
-- 3. Relax inoculum OD600 constraints (from 2.0-10.0 to >= 0.1)
-- 4. Make calibration fields optional (not all probes need all fields)

BEGIN;

-- ============================================================================
-- 1. Update inoculations table
-- ============================================================================

-- Rename column
ALTER TABLE inoculations
    RENAME COLUMN cryo_vial_id TO inoculum_source;

-- Make it optional (nullable)
ALTER TABLE inoculations
    ALTER COLUMN inoculum_source DROP NOT NULL;

-- Increase size for longer descriptions
ALTER TABLE inoculations
    ALTER COLUMN inoculum_source TYPE VARCHAR(200);

-- Drop old constraint
ALTER TABLE inoculations
    DROP CONSTRAINT IF EXISTS check_inoculum_od600;

-- Add new relaxed constraint
ALTER TABLE inoculations
    ADD CONSTRAINT check_inoculum_od600_positive CHECK (inoculum_od600 >= 0.1);

-- Update comment
COMMENT ON COLUMN inoculations.inoculum_source IS 'Inoculum source (e.g., Cryo-2024-001, Plate YPD-5, Seed Flask A)';

-- ============================================================================
-- 2. Update calibrations table - make fields optional
-- ============================================================================

-- Make calibration reference fields optional (not all probes use buffers)
ALTER TABLE calibrations
    ALTER COLUMN buffer_low_value DROP NOT NULL;

ALTER TABLE calibrations
    ALTER COLUMN buffer_high_value DROP NOT NULL;

ALTER TABLE calibrations
    ALTER COLUMN reading_low DROP NOT NULL;

ALTER TABLE calibrations
    ALTER COLUMN reading_high DROP NOT NULL;

-- Update table comment to clarify field usage
COMMENT ON TABLE calibrations IS 'Pre-run sensor calibration records. Field usage varies by probe type:
- pH: buffer_low/high_value (e.g., 4.01, 7.00), reading_low/high (mV), slope_percent (≥95%)
- DO: buffer_low/high_value (0%, 100%), reading_low/high (actual readings), response_time_sec (<30s)
- OffGas O2/CO2: buffer values = span gas concentrations, readings = actual sensor output
- Temp: Single-point verification (ice bath or reference thermometer)
- Pressure: Atmospheric reference or certified gauge';

-- ============================================================================
-- 3. Data migration (if needed)
-- ============================================================================

-- Convert any existing cryo_vial_id values to inoculum_source format
-- (This is a no-op since we renamed the column, but included for clarity)

-- ============================================================================
-- 4. Update batch_summary view
-- ============================================================================

-- Drop and recreate view with updated column name
DROP VIEW IF EXISTS batch_summary CASCADE;

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
-- Verification
-- ============================================================================

-- Verify column rename
SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'inoculations'
    AND column_name = 'inoculum_source';

-- Verify constraint
SELECT
    conname,
    pg_get_constraintdef(oid) as definition
FROM pg_constraint
WHERE conname LIKE '%inoculum%'
    AND conrelid = 'inoculations'::regclass;

COMMIT;

SELECT 'Migration 001 completed successfully!' AS status;
