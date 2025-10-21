import { useCallback, useMemo, useState } from 'react';
import type { SampleCreate } from '../types';

/**
 * Scientific calculation constants for Pichia pastoris fermentation
 * Reference: batch-run-plan.md, Section 3.2
 */
export const SCIENTIFIC_CONSTANTS = {
  // Dry Cell Weight calculation
  DCW_CALCULATION: {
    // Average dry cell weight of Pichia cells
    defaultODToDCWFactor: 0.4, // g/L per OD600 unit
    filterTareFraction: 0.0003, // Account for filter tare variation
  },
  // OD600 validation ranges
  OD600: {
    minValidRaw: 0.01,
    maxValidRaw: 5.0,
    warningThreshold: 3.0, // High OD warning for potential stationary phase
  },
  // Dilution factor constraints
  DILUTION: {
    minFactor: 1,
    maxFactor: 1000,
  },
  // Sample volume constraints
  SAMPLE_VOLUME: {
    min: 1.0, // mL
    max: 50.0, // mL
    default: 10.0, // mL
  },
  // DCW measurement constraints
  DCW: {
    minFilterWeight: 0.0001, // g
    maxFilterWeight: 0.5, // g
    minSampleVolume: 1.0, // mL
    maxSampleVolume: 50.0, // mL
  },
} as const;

export interface SampleFormData {
  sample_volume_ml: number;
  od600_raw: number;
  od600_dilution_factor: number;
  dcw_filter_id: string;
  dcw_sample_volume_ml: number;
  dcw_filter_wet_weight_g: number;
  dcw_filter_dry_weight_g: number;
  contamination_detected: boolean;
  microscopy_observations: string;
  supernatant_cryovial_id: string;
  pellet_cryovial_id: string;
}

/**
 * Custom hook for sample form logic and calculations
 * Handles:
 * - OD600 corrected value calculations
 * - DCW calculations from filter weights
 * - Form validation with scientific constraints
 * - Data formatting for API submission
 */
export const useSampleForm = (batchId: string) => {
  const [formData, setFormData] = useState<Partial<SampleFormData>>({
    sample_volume_ml: SCIENTIFIC_CONSTANTS.SAMPLE_VOLUME.default,
    od600_dilution_factor: 1,
    contamination_detected: false,
  });

  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [warnings, setWarnings] = useState<Record<string, string>>({});

  /**
   * Calculate OD600 corrected value
   * Formula: OD600_corrected = OD600_raw × dilution_factor
   */
  const od600Corrected = useMemo(() => {
    if (!formData.od600_raw || !formData.od600_dilution_factor) return null;
    return Number((formData.od600_raw * formData.od600_dilution_factor).toFixed(3));
  }, [formData.od600_raw, formData.od600_dilution_factor]);

  /**
   * Calculate DCW (Dry Cell Weight) in g/L
   * Formula: DCW = (dry_weight - wet_weight) / sample_volume
   * This accounts for residual moisture on filter
   */
  const dcwCalculated = useMemo(() => {
    const { dcw_filter_wet_weight_g, dcw_filter_dry_weight_g, dcw_sample_volume_ml } = formData;

    if (
      dcw_filter_wet_weight_g === undefined ||
      dcw_filter_dry_weight_g === undefined ||
      dcw_sample_volume_ml === undefined ||
      dcw_filter_dry_weight_g <= dcw_filter_wet_weight_g
    ) {
      return null;
    }

    // Convert mL to L for g/L units
    const dryWeightDifference = dcw_filter_dry_weight_g - dcw_filter_wet_weight_g;
    const sampleVolumeL = dcw_sample_volume_ml / 1000;
    return Number((dryWeightDifference / sampleVolumeL).toFixed(4));
  }, [
    formData.dcw_filter_wet_weight_g,
    formData.dcw_filter_dry_weight_g,
    formData.dcw_sample_volume_ml,
  ]);

  /**
   * Estimate DCW from OD600 using empirical relationship
   * Formula: DCW_estimated = OD600_corrected × factor
   * Useful for cross-validation against measured DCW
   */
  const dcwEstimatedFromOD = useMemo(() => {
    if (!od600Corrected) return null;
    return Number(
      (od600Corrected * SCIENTIFIC_CONSTANTS.DCW_CALCULATION.defaultODToDCWFactor).toFixed(4)
    );
  }, [od600Corrected]);

  /**
   * Compare measured DCW against OD600-based estimate
   * Returns deviation percentage to flag measurement errors
   */
  const dcwDeviation = useMemo(() => {
    if (!dcwCalculated || !dcwEstimatedFromOD) return null;
    const deviation = ((dcwCalculated - dcwEstimatedFromOD) / dcwEstimatedFromOD) * 100;
    return Number(deviation.toFixed(1));
  }, [dcwCalculated, dcwEstimatedFromOD]);

  /**
   * Validate all form fields with scientific constraints
   */
  const validateForm = useCallback((data: Partial<SampleFormData>) => {
    const newErrors: Record<string, string> = {};
    const newWarnings: Record<string, string> = {};

    // OD600 raw validation
    if (data.od600_raw !== undefined) {
      if (data.od600_raw < SCIENTIFIC_CONSTANTS.OD600.minValidRaw) {
        newErrors.od600_raw = `OD600 must be ≥ ${SCIENTIFIC_CONSTANTS.OD600.minValidRaw}`;
      } else if (data.od600_raw > SCIENTIFIC_CONSTANTS.OD600.maxValidRaw) {
        newWarnings.od600_raw = `OD600 > ${SCIENTIFIC_CONSTANTS.OD600.maxValidRaw} detected. Consider dilution.`;
      }
    }

    // Dilution factor validation
    if (data.od600_dilution_factor !== undefined) {
      if (
        data.od600_dilution_factor < SCIENTIFIC_CONSTANTS.DILUTION.minFactor ||
        data.od600_dilution_factor > SCIENTIFIC_CONSTANTS.DILUTION.maxFactor
      ) {
        newErrors.od600_dilution_factor = `Dilution factor must be between ${SCIENTIFIC_CONSTANTS.DILUTION.minFactor} and ${SCIENTIFIC_CONSTANTS.DILUTION.maxFactor}`;
      }
    }

    // Sample volume validation
    if (data.sample_volume_ml !== undefined) {
      if (
        data.sample_volume_ml < SCIENTIFIC_CONSTANTS.SAMPLE_VOLUME.min ||
        data.sample_volume_ml > SCIENTIFIC_CONSTANTS.SAMPLE_VOLUME.max
      ) {
        newErrors.sample_volume_ml = `Sample volume must be between ${SCIENTIFIC_CONSTANTS.SAMPLE_VOLUME.min} and ${SCIENTIFIC_CONSTANTS.SAMPLE_VOLUME.max} mL`;
      }
    }

    // DCW measurements validation
    if (data.dcw_filter_wet_weight_g !== undefined && data.dcw_filter_dry_weight_g !== undefined) {
      if (data.dcw_filter_dry_weight_g <= data.dcw_filter_wet_weight_g) {
        newErrors.dcw_filter_dry_weight_g =
          'Dry weight must be greater than wet weight (moisture must be removed)';
      }

      if (
        data.dcw_filter_wet_weight_g < SCIENTIFIC_CONSTANTS.DCW.minFilterWeight ||
        data.dcw_filter_wet_weight_g > SCIENTIFIC_CONSTANTS.DCW.maxFilterWeight
      ) {
        newWarnings.dcw_filter_wet_weight_g =
          'Wet weight seems unusual. Verify scale calibration.';
      }
    }

    // DCW measurement consistency check
    if (dcwCalculated && dcwEstimatedFromOD && dcwDeviation !== null) {
      const maxDeviation = 30; // 30% tolerance between methods
      if (Math.abs(dcwDeviation) > maxDeviation) {
        newWarnings.dcw_deviation = `DCW deviation from OD estimate: ${dcwDeviation.toFixed(1)}%. Check measurements.`;
      }
    }

    // OD600 corrected value validation (cross-check)
    if (od600Corrected && od600Corrected > SCIENTIFIC_CONSTANTS.OD600.warningThreshold) {
      newWarnings.od600_corrected =
        'High OD600 corrected value suggests late exponential/stationary phase. Verify culture age.';
    }

    // Contamination flag validation
    if (data.contamination_detected && !data.microscopy_observations) {
      newErrors.microscopy_observations =
        'Contamination flagged. Microscopy observations are mandatory.';
    }

    setValidationErrors(newErrors);
    setWarnings(newWarnings);

    return Object.keys(newErrors).length === 0;
  }, [od600Corrected, dcwCalculated, dcwEstimatedFromOD, dcwDeviation]);

  /**
   * Update form field with validation
   */
  const updateField = useCallback(
    (key: keyof SampleFormData, value: unknown) => {
      const updatedData = { ...formData, [key]: value };
      setFormData(updatedData);

      // Re-validate affected fields
      if (key === 'od600_raw' || key === 'od600_dilution_factor') {
        validateForm(updatedData);
      } else if (
        key === 'dcw_filter_wet_weight_g' ||
        key === 'dcw_filter_dry_weight_g' ||
        key === 'dcw_sample_volume_ml'
      ) {
        validateForm(updatedData);
      } else if (key === 'contamination_detected') {
        validateForm(updatedData);
      } else {
        validateForm(updatedData);
      }
    },
    [formData, validateForm]
  );

  /**
   * Format form data for API submission
   * Note: sampled_by is required but provided by parent component via context
   */
  const formatForSubmit = useCallback(
    (sampledBy: string): SampleCreate => {
      return {
        sample_volume_ml: formData.sample_volume_ml || SCIENTIFIC_CONSTANTS.SAMPLE_VOLUME.default,
        od600_raw: formData.od600_raw || 0,
        od600_dilution_factor: formData.od600_dilution_factor || 1,
        dcw_filter_id: formData.dcw_filter_id || undefined,
        dcw_sample_volume_ml: formData.dcw_sample_volume_ml || undefined,
        dcw_filter_wet_weight_g: formData.dcw_filter_wet_weight_g || undefined,
        dcw_filter_dry_weight_g: formData.dcw_filter_dry_weight_g || undefined,
        contamination_detected: formData.contamination_detected || false,
        microscopy_observations: formData.microscopy_observations || undefined,
        supernatant_cryovial_id: formData.supernatant_cryovial_id || undefined,
        pellet_cryovial_id: formData.pellet_cryovial_id || undefined,
        sampled_by: sampledBy,
      };
    },
    [formData]
  );

  return {
    formData,
    setFormData,
    updateField,
    validationErrors,
    warnings,
    validateForm,
    formatForSubmit,
    // Calculated values
    od600Corrected,
    dcwCalculated,
    dcwEstimatedFromOD,
    dcwDeviation,
    // Batch ID
    batchId,
  };
};
