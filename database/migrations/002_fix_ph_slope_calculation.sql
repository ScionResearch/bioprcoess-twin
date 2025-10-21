-- ============================================================================
-- Migration: Fix pH Slope Calculation
-- Version: 002
-- Date: 2025-10-22
-- Description: Correct pH probe slope calculation formula (was inverted)
-- ============================================================================

-- The previous formula was: (delta_pH / delta_mV) / 59.16 * 100
-- This is incorrect because it gives (pH/mV) / (mV/pH) = pH²/mV²

-- Correct formula: (delta_mV / delta_pH) / 59.16 * 100
-- This gives (mV/pH) / (mV/pH) = dimensionless percentage

-- Example:
-- pH 4.0 buffer → probe reads -177 mV
-- pH 7.0 buffer → probe reads 0 mV
-- delta_mV = 0 - (-177) = 177 mV
-- delta_pH = 7.0 - 4.0 = 3.0
-- slope = 177 / 3.0 = 59 mV/pH
-- slope % = (59 / 59.16) × 100 = 99.7% ✓

BEGIN;

-- Drop old function
DROP FUNCTION IF EXISTS calculate_ph_slope() CASCADE;

-- Recreate with corrected formula
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

        -- Calculate slope percentage
        -- slope % = (measured_slope / ideal_slope) × 100
        NEW.slope_percent := (ABS(measured_slope) / ideal_slope) * 100.0;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Recreate trigger
CREATE TRIGGER trg_ph_slope
    BEFORE INSERT OR UPDATE ON calibrations
    FOR EACH ROW
    EXECUTE FUNCTION calculate_ph_slope();

-- Update comment
COMMENT ON FUNCTION calculate_ph_slope IS 'Auto-calculate pH probe slope percentage using Nernst equation.
Ideal slope at 25°C = 59.16 mV/pH. Acceptable range: 95-105% (56.2-62.1 mV/pH).
Formula: slope % = (|delta_mV / delta_pH| / 59.16) × 100';

-- ============================================================================
-- Recalculate existing pH calibrations (if any)
-- ============================================================================

-- This will trigger the new function to recalculate slope_percent for all existing pH calibrations
UPDATE calibrations
SET slope_percent = NULL  -- Set to NULL to force recalculation
WHERE probe_type = 'pH'
  AND buffer_low_value IS NOT NULL
  AND buffer_high_value IS NOT NULL
  AND reading_low IS NOT NULL
  AND reading_high IS NOT NULL;

-- Now trigger the recalculation by updating a dummy field
UPDATE calibrations
SET notes = COALESCE(notes, '') || ''  -- No-op update that triggers the BEFORE UPDATE trigger
WHERE probe_type = 'pH'
  AND buffer_low_value IS NOT NULL
  AND buffer_high_value IS NOT NULL
  AND reading_low IS NOT NULL
  AND reading_high IS NOT NULL;

-- ============================================================================
-- Verification
-- ============================================================================

-- Show all pH calibrations with recalculated slopes
SELECT
    id,
    batch_id,
    buffer_low_value as "pH Low",
    buffer_high_value as "pH High",
    reading_low as "Reading Low (mV)",
    reading_high as "Reading High (mV)",
    slope_percent as "Slope %",
    CASE
        WHEN slope_percent >= 95 AND slope_percent <= 105 THEN 'PASS'
        ELSE 'FAIL'
    END as "95-105% Range",
    calibrated_at
FROM calibrations
WHERE probe_type = 'pH'
ORDER BY calibrated_at DESC;

COMMIT;

SELECT 'Migration 002 completed successfully! pH slope formula corrected.' AS status;
