import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../api/client';
import { Modal } from './Modal';
import { useSampleForm, SCIENTIFIC_CONSTANTS } from '../hooks/useSampleForm';
import type { SampleFormData } from '../hooks/useSampleForm';
import './SampleFormRefactored.css';

interface SampleFormProps {
  isOpen: boolean;
  onClose: () => void;
  batchId: string;
  onSuccess: () => void;
}

/**
 * SampleForm Component - Scientific Sample Data Collection
 *
 * Purpose: Capture OD600 and Dry Cell Weight (DCW) measurements during fermentation
 * Features:
 * - Real-time calculation of OD600 corrected and DCW values
 * - Cross-validation between measured and estimated DCW
 * - Contamination detection workflow
 * - Comprehensive field validation with scientific constraints
 * - Accessibility: WCAG 2.1 AA compliance, keyboard navigation, screen reader support
 * - Mobile-optimized responsive layout
 *
 * Scientific Reference:
 * - Batch Run Plan: Section 3.2 (Sample Observation)
 * - DCW calculation: Filter dry weight - filter wet weight / sample volume
 * - OD600 corrected: OD600_raw × dilution_factor
 * - Cross-validation: Compare measured DCW against OD-based estimate (±30%)
 */
export const SampleForm: React.FC<SampleFormProps> = ({ isOpen, onClose, batchId, onSuccess }) => {
  const { user } = useAuth();
  const {
    formData,
    updateField,
    validationErrors,
    warnings,
    validateForm,
    formatForSubmit,
    od600Corrected,
    dcwCalculated,
    dcwEstimatedFromOD,
    dcwDeviation,
  } = useSampleForm(batchId);

  const [submitting, setSubmitting] = useState(false);
  const [apiError, setApiError] = useState('');

  const isValidBatchId = typeof batchId === 'string' && batchId.length > 0;

  const handleFieldChange = (field: keyof SampleFormData, value: unknown) => {
    updateField(field, value);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!user) {
      setApiError('User not authenticated');
      return;
    }

    if (!isValidBatchId) {
      setApiError('Invalid batch ID');
      return;
    }

    // Final validation
    if (!validateForm(formData)) {
      setApiError('Please correct the errors in the form');
      return;
    }

    setSubmitting(true);
    setApiError('');

    try {
      const sampleData = formatForSubmit(user.username);
      await api.samples.create(batchId, sampleData);
      onSuccess();
      onClose();
    } catch (error: any) {
      console.error('Error creating sample:', error);
      setApiError(error.response?.data?.detail || 'Failed to create sample');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Add Sample Observation">
      <form onSubmit={handleSubmit} className="sample-form" noValidate>
        {/* OD600 Measurements Section */}
        <fieldset className="form-section">
          <legend className="section-header">
            <span className="section-title">OD₆₀₀ Optical Density Measurement</span>
            <span className="section-subtitle">
              Required: Measure culture absorbance at 600 nm
            </span>
          </legend>

          <div className="form-row">
            {/* OD600 Raw Reading */}
            <div className="form-group">
              <label htmlFor="od600_raw" className="form-label">
                OD₆₀₀ Raw Reading
                <span className="required-indicator" aria-label="required">
                  *
                </span>
              </label>

              <input
                id="od600_raw"
                type="number"
                inputMode="decimal"
                step="0.01"
                min={SCIENTIFIC_CONSTANTS.OD600.minValidRaw}
                max={SCIENTIFIC_CONSTANTS.OD600.maxValidRaw}
                placeholder="e.g., 2.5"
                value={formData.od600_raw || ''}
                onChange={(e) => handleFieldChange('od600_raw', parseFloat(e.target.value) || '')}
                aria-required="true"
                aria-invalid={!!validationErrors.od600_raw}
                aria-describedby={
                  validationErrors.od600_raw
                    ? 'od600_raw-error'
                    : 'od600_raw-help'
                }
                className={`form-input ${
                  validationErrors.od600_raw ? 'input-error' : ''
                } ${warnings.od600_raw ? 'input-warning' : ''}`}
              />

              {validationErrors.od600_raw && (
                <span id="od600_raw-error" className="error-text" role="alert">
                  ✕ {validationErrors.od600_raw}
                </span>
              )}
              {warnings.od600_raw && !validationErrors.od600_raw && (
                <span className="warning-text" role="status">
                  ⚠ {warnings.od600_raw}
                </span>
              )}
              {!validationErrors.od600_raw && !warnings.od600_raw && (
                <span id="od600_raw-help" className="help-text">
                  Range: {SCIENTIFIC_CONSTANTS.OD600.minValidRaw}-
                  {SCIENTIFIC_CONSTANTS.OD600.maxValidRaw}. Direct spectrophotometer reading.
                </span>
              )}
            </div>

            {/* Dilution Factor */}
            <div className="form-group">
              <label htmlFor="od600_dilution_factor" className="form-label">
                Dilution Factor
                <span className="required-indicator" aria-label="required">
                  *
                </span>
              </label>

              <input
                id="od600_dilution_factor"
                type="number"
                inputMode="numeric"
                step="1"
                min={SCIENTIFIC_CONSTANTS.DILUTION.minFactor}
                max={SCIENTIFIC_CONSTANTS.DILUTION.maxFactor}
                placeholder="1 (no dilution) or 10 (1:10)"
                value={formData.od600_dilution_factor || ''}
                onChange={(e) =>
                  handleFieldChange('od600_dilution_factor', parseInt(e.target.value) || '')
                }
                aria-required="true"
                aria-invalid={!!validationErrors.od600_dilution_factor}
                aria-describedby="od600_dilution_factor-help"
                className={`form-input ${
                  validationErrors.od600_dilution_factor ? 'input-error' : ''
                }`}
              />

              {validationErrors.od600_dilution_factor && (
                <span className="error-text" role="alert">
                  ✕ {validationErrors.od600_dilution_factor}
                </span>
              )}
              {!validationErrors.od600_dilution_factor && (
                <span id="od600_dilution_factor-help" className="help-text">
                  Use 1 for no dilution. For diluted samples, enter dilution factor
                  (e.g., 10 for 1:10 dilution).
                </span>
              )}
            </div>
          </div>

          {/* OD600 Corrected Display - Scientific Calculation */}
          {od600Corrected !== null && (
            <div className="calculated-card">
              <div className="calculated-header">
                <strong>OD₆₀₀ Corrected</strong>
                <span className="calculated-formula" title="OD_raw × dilution_factor">
                  ⓘ
                </span>
              </div>
              <div className="calculated-value">{od600Corrected.toFixed(3)}</div>
              <div className="calculated-detail">
                Calculation: {(formData.od600_raw || 0).toFixed(2)} × {formData.od600_dilution_factor || 1} = {od600Corrected.toFixed(3)}
              </div>
              {warnings.od600_corrected && (
                <div className="calculated-warning">⚠ {warnings.od600_corrected}</div>
              )}
            </div>
          )}
        </fieldset>

        {/* Dry Cell Weight (DCW) Measurements Section */}
        <fieldset className="form-section">
          <legend className="section-header">
            <span className="section-title">Dry Cell Weight (DCW) Measurement</span>
            <span className="section-subtitle">Optional: Gravimetric biomass quantification</span>
          </legend>

          <div className="form-group">
            <label htmlFor="dcw_filter_id" className="form-label">
              Filter ID
            </label>
            <input
              id="dcw_filter_id"
              type="text"
              placeholder="e.g., FILTER-001"
              value={formData.dcw_filter_id || ''}
              onChange={(e) => handleFieldChange('dcw_filter_id', e.target.value)}
              className="form-input"
              aria-describedby="dcw_filter_id-help"
            />
            <span id="dcw_filter_id-help" className="help-text">
              Unique identifier for filter paper used. Track for quality assurance.
            </span>
          </div>

          <div className="form-row">
            {/* DCW Sample Volume */}
            <div className="form-group">
              <label htmlFor="dcw_sample_volume_ml" className="form-label">
                Sample Volume (mL)
              </label>
              <input
                id="dcw_sample_volume_ml"
                type="number"
                inputMode="decimal"
                step="0.1"
                min={SCIENTIFIC_CONSTANTS.DCW.minSampleVolume}
                max={SCIENTIFIC_CONSTANTS.DCW.maxSampleVolume}
                placeholder="e.g., 10.0"
                value={formData.dcw_sample_volume_ml || ''}
                onChange={(e) =>
                  handleFieldChange('dcw_sample_volume_ml', parseFloat(e.target.value) || '')
                }
                className={`form-input ${
                  warnings.dcw_filter_wet_weight_g ? 'input-warning' : ''
                }`}
                aria-describedby="dcw_sample_volume_ml-help"
              />
              <span id="dcw_sample_volume_ml-help" className="help-text">
                Volume of culture filtered. Typical: 10 mL. Affects DCW precision.
              </span>
            </div>

            {/* Filter Wet Weight */}
            <div className="form-group">
              <label htmlFor="dcw_filter_wet_weight_g" className="form-label">
                Filter Wet Weight (g)
              </label>
              <input
                id="dcw_filter_wet_weight_g"
                type="number"
                inputMode="decimal"
                step="0.0001"
                min={SCIENTIFIC_CONSTANTS.DCW.minFilterWeight}
                max={SCIENTIFIC_CONSTANTS.DCW.maxFilterWeight}
                placeholder="e.g., 0.0250"
                value={formData.dcw_filter_wet_weight_g || ''}
                onChange={(e) =>
                  handleFieldChange('dcw_filter_wet_weight_g', parseFloat(e.target.value) || '')
                }
                className={`form-input ${
                  warnings.dcw_filter_wet_weight_g ? 'input-warning' : ''
                }`}
                aria-describedby="dcw_filter_wet_weight_g-help"
              />
              {warnings.dcw_filter_wet_weight_g && (
                <span className="warning-text">⚠ {warnings.dcw_filter_wet_weight_g}</span>
              )}
              <span id="dcw_filter_wet_weight_g-help" className="help-text">
                Mass of filter + cells after filtration, before drying. Use analytical balance.
              </span>
            </div>

            {/* Filter Dry Weight */}
            <div className="form-group">
              <label htmlFor="dcw_filter_dry_weight_g" className="form-label">
                Filter Dry Weight (g)
              </label>
              <input
                id="dcw_filter_dry_weight_g"
                type="number"
                inputMode="decimal"
                step="0.0001"
                min={SCIENTIFIC_CONSTANTS.DCW.minFilterWeight}
                max={SCIENTIFIC_CONSTANTS.DCW.maxFilterWeight}
                placeholder="e.g., 0.0280"
                value={formData.dcw_filter_dry_weight_g || ''}
                onChange={(e) =>
                  handleFieldChange('dcw_filter_dry_weight_g', parseFloat(e.target.value) || '')
                }
                className={`form-input ${
                  validationErrors.dcw_filter_dry_weight_g ? 'input-error' : ''
                }`}
                aria-invalid={!!validationErrors.dcw_filter_dry_weight_g}
                aria-describedby="dcw_filter_dry_weight_g-help"
              />
              {validationErrors.dcw_filter_dry_weight_g && (
                <span className="error-text" role="alert">
                  ✕ {validationErrors.dcw_filter_dry_weight_g}
                </span>
              )}
              <span id="dcw_filter_dry_weight_g-help" className="help-text">
                Mass after drying at 105°C, cooled in desiccator. Must be ≥ wet weight.
              </span>
            </div>
          </div>

          {/* DCW Calculated Display - Scientific Calculation */}
          {dcwCalculated !== null && (
            <div className="calculated-card">
              <div className="calculated-header">
                <strong>Measured DCW</strong>
                <span className="calculated-formula" title="(dry - wet) / volume">
                  ⓘ
                </span>
              </div>
              <div className="calculated-value">{dcwCalculated.toFixed(4)} g/L</div>
              <div className="calculated-detail">
                Calculation: ({(formData.dcw_filter_dry_weight_g || 0).toFixed(4)} − {(formData.dcw_filter_wet_weight_g || 0).toFixed(4)}) g ÷ {(formData.dcw_sample_volume_ml || 0) / 1000} L
              </div>
            </div>
          )}

          {/* DCW Cross-Validation - OD600 Based Estimate */}
          {dcwEstimatedFromOD !== null && (
            <div className="calculated-card secondary">
              <div className="calculated-header">
                <strong>Estimated DCW from OD₆₀₀</strong>
                <span
                  className="calculated-formula"
                  title={`OD_corrected × ${SCIENTIFIC_CONSTANTS.DCW_CALCULATION.defaultODToDCWFactor} g/L factor`}
                >
                  ⓘ
                </span>
              </div>
              <div className="calculated-value">{dcwEstimatedFromOD.toFixed(4)} g/L</div>
              <div className="calculated-detail">
                Empirical conversion: {od600Corrected?.toFixed(3)} × {SCIENTIFIC_CONSTANTS.DCW_CALCULATION.defaultODToDCWFactor} = {dcwEstimatedFromOD.toFixed(4)}
              </div>
              {dcwCalculated && dcwDeviation !== null && (
                <div className={dcwDeviation > 10 ? 'calculated-warning' : 'calculated-info'}>
                  {dcwDeviation > 0 ? '+' : ''}{dcwDeviation.toFixed(1)}% deviation from measured
                </div>
              )}
              {warnings.dcw_deviation && (
                <div className="calculated-warning">⚠ {warnings.dcw_deviation}</div>
              )}
            </div>
          )}
        </fieldset>

        {/* Sample Cryopreservation Section */}
        <fieldset className="form-section">
          <legend className="section-header">
            <span className="section-title">Sample Cryopreservation</span>
            <span className="section-subtitle">Optional: Sample archival for future analysis</span>
          </legend>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="supernatant_cryovial_id" className="form-label">
                Supernatant Cryo Vial ID
              </label>
              <input
                id="supernatant_cryovial_id"
                type="text"
                placeholder="e.g., CRYO-B5-001"
                value={formData.supernatant_cryovial_id || ''}
                onChange={(e) => handleFieldChange('supernatant_cryovial_id', e.target.value)}
                className="form-input"
                aria-describedby="supernatant_cryovial_id-help"
              />
              <span id="supernatant_cryovial_id-help" className="help-text">
                ID for frozen supernatant. Stored at -80°C.
              </span>
            </div>

            <div className="form-group">
              <label htmlFor="pellet_cryovial_id" className="form-label">
                Cell Pellet Cryo Vial ID
              </label>
              <input
                id="pellet_cryovial_id"
                type="text"
                placeholder="e.g., CRYO-B5-002"
                value={formData.pellet_cryovial_id || ''}
                onChange={(e) => handleFieldChange('pellet_cryovial_id', e.target.value)}
                className="form-input"
                aria-describedby="pellet_cryovial_id-help"
              />
              <span id="pellet_cryovial_id-help" className="help-text">
                ID for frozen cell pellet. Stored at -80°C.
              </span>
            </div>
          </div>
        </fieldset>

        {/* Microscopy & Contamination Section */}
        <fieldset className="form-section">
          <legend className="section-header">
            <span className="section-title">Microscopy Observations</span>
            <span className="section-subtitle">Visual inspection and contamination detection</span>
          </legend>

          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={formData.contamination_detected || false}
                onChange={(e) => handleFieldChange('contamination_detected', e.target.checked)}
                aria-describedby="contamination-help"
              />
              <span>Contamination Detected</span>
            </label>
            <span id="contamination-help" className="help-text">
              Check if bacterial or fungal contamination is visible under microscope
            </span>
          </div>

          {formData.contamination_detected && (
            <div
              className="alert alert-danger"
              role="region"
              aria-label="Contamination warning"
            >
              <strong>⚠️ Contamination Alert</strong>
              <p>
                Contamination detected. Document observations in notes and consider filing a
                failure report to the Process Engineer.
              </p>
            </div>
          )}

          <div className="form-group full-width">
            <label htmlFor="microscopy_observations" className="form-label">
              Microscopy Notes {formData.contamination_detected && '(Required)'}
            </label>
            <textarea
              id="microscopy_observations"
              rows={3}
              placeholder="Cell morphology, viability, contamination details, colony-forming units estimate..."
              value={formData.microscopy_observations || ''}
              onChange={(e) => handleFieldChange('microscopy_observations', e.target.value)}
              aria-invalid={
                formData.contamination_detected && !formData.microscopy_observations
              }
              aria-describedby="microscopy_observations-help"
              className={`form-input textarea ${
                formData.contamination_detected && !formData.microscopy_observations
                  ? 'input-error'
                  : ''
              }`}
            />
            {formData.contamination_detected && !formData.microscopy_observations && (
              <span className="error-text" role="alert">
                ✕ Notes are required when contamination is detected
              </span>
            )}
            <span id="microscopy_observations-help" className="help-text">
              Describe cell morphology, viability estimate, and any observed abnormalities
            </span>
          </div>
        </fieldset>

        {/* Sample Volume Display */}
        <div className="form-section info-section">
          <div className="info-row">
            <div className="info-item">
              <span className="info-label">Sample Volume</span>
              <span className="info-value">
                {formData.sample_volume_ml || SCIENTIFIC_CONSTANTS.SAMPLE_VOLUME.default} mL
              </span>
            </div>
            <div className="info-item">
              <span className="info-label">Sampled By</span>
              <span className="info-value">{user?.full_name || user?.username}</span>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {apiError && (
          <div className="alert alert-danger" role="alert">
            <strong>Error:</strong> {apiError}
          </div>
        )}

        {/* Form Actions */}
        <div className="form-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onClose}
            disabled={submitting}
            aria-label="Cancel and close form"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={submitting || Object.keys(validationErrors).length > 0}
            aria-label={submitting ? 'Saving sample data...' : 'Save sample observation'}
          >
            {submitting ? 'Saving...' : 'Save Sample'}
          </button>
        </div>
      </form>
    </Modal>
  );
};
