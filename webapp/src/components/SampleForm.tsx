import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Modal } from './Modal';
import { api } from '../api/client';
import type { SampleCreate } from '../types';
import { useAuth } from '../contexts/AuthContext';
import './FormStyles.css';

interface SampleFormProps {
  isOpen: boolean;
  onClose: () => void;
  batchId: string;
  onSuccess: () => void;
}

interface FormData {
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

export const SampleForm: React.FC<SampleFormProps> = ({
  isOpen,
  onClose,
  batchId,
  onSuccess,
}) => {
  const { register, handleSubmit, formState: { errors }, watch } = useForm<FormData>({
    defaultValues: {
      sample_volume_ml: 10.0,
      od600_dilution_factor: 1.0,
      contamination_detected: false,
    },
  });
  const [submitting, setSubmitting] = useState(false);
  const [apiError, setApiError] = useState('');
  const { user } = useAuth();

  // Validate batchId
  const isValidBatchId = typeof batchId === 'string' && batchId.length > 0;

  const od600Raw = watch('od600_raw');
  const dilutionFactor = watch('od600_dilution_factor');
  const contaminationDetected = watch('contamination_detected');

  const od600Corrected = od600Raw && dilutionFactor ? od600Raw * dilutionFactor : 0;

  const onSubmit = async (data: FormData) => {
    if (!user) return;
    
    // Validate batchId
    if (!isValidBatchId) {
      setApiError('Invalid batch ID');
      return;
    }

    setSubmitting(true);
    setApiError('');

    try {
      const sampleData: SampleCreate = {
        sample_volume_ml: data.sample_volume_ml || 10.0,
        od600_raw: data.od600_raw,
        od600_dilution_factor: data.od600_dilution_factor,
        dcw_filter_id: data.dcw_filter_id || undefined,
        dcw_sample_volume_ml: data.dcw_sample_volume_ml || undefined,
        dcw_filter_wet_weight_g: data.dcw_filter_wet_weight_g || undefined,
        dcw_filter_dry_weight_g: data.dcw_filter_dry_weight_g || undefined,
        contamination_detected: data.contamination_detected,
        microscopy_observations: data.microscopy_observations || undefined,
        supernatant_cryovial_id: data.supernatant_cryovial_id || undefined,
        pellet_cryovial_id: data.pellet_cryovial_id || undefined,
        sampled_by: user.username,
      };

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

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Add Sample">
      <form onSubmit={handleSubmit(onSubmit)} className="modal-form">
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="sample_volume_ml">
              Sample Volume (mL)
            </label>
            <input
              id="sample_volume_ml"
              type="number"
              step="0.1"
              {...register('sample_volume_ml', {
                min: { value: 0, message: 'Must be non-negative' },
                valueAsNumber: true,
              })}
              placeholder="10.0"
            />
            {errors.sample_volume_ml && (
              <span className="error-text">{errors.sample_volume_ml.message}</span>
            )}
            <p className="help-text">Sample volume in mL (default: 10.0)</p>
          </div>

          <div className="form-group">
            <label htmlFor="od600_raw">
              OD₆₀₀ Raw Reading <span className="required">*</span>
            </label>
            <input
              id="od600_raw"
              type="number"
              step="0.01"
              {...register('od600_raw', {
                required: 'OD600 reading is required',
                min: { value: 0.01, message: 'Must be greater than 0' },
                valueAsNumber: true,
              })}
              placeholder="2.5"
            />
            {errors.od600_raw && (
              <span className="error-text">{errors.od600_raw.message}</span>
            )}
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="od600_dilution_factor">
              Dilution Factor <span className="required">*</span>
            </label>
            <input
              id="od600_dilution_factor"
              type="number"
              step="1"
              {...register('od600_dilution_factor', {
                required: 'Dilution factor is required',
                min: { value: 1, message: 'Must be at least 1' },
                valueAsNumber: true,
              })}
              placeholder="1"
            />
            {errors.od600_dilution_factor && (
              <span className="error-text">{errors.od600_dilution_factor.message}</span>
            )}
            <p className="help-text">Use 1 for no dilution, 10 for 1:10 dilution</p>
          </div>
        </div>

        {od600Corrected > 0 && (
          <div className="calculated-value">
            <strong>OD₆₀₀ Corrected:</strong> {Number(od600Corrected).toFixed(2)}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="dcw_filter_id">DCW Filter ID</label>
          <input
            id="dcw_filter_id"
            type="text"
            {...register('dcw_filter_id')}
            placeholder="Optional - filter identification number"
          />
          <p className="help-text">Used for dry cell weight measurements</p>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="dcw_sample_volume_ml">DCW Sample Volume (mL)</label>
            <input
              id="dcw_sample_volume_ml"
              type="number"
              step="0.1"
              {...register('dcw_sample_volume_ml', {
                min: { value: 0, message: 'Must be non-negative' },
                valueAsNumber: true,
              })}
              placeholder="Optional"
            />
          </div>

          <div className="form-group">
            <label htmlFor="dcw_filter_wet_weight_g">Filter Wet Weight (g)</label>
            <input
              id="dcw_filter_wet_weight_g"
              type="number"
              step="0.0001"
              {...register('dcw_filter_wet_weight_g', {
                min: { value: 0, message: 'Must be non-negative' },
                valueAsNumber: true,
              })}
              placeholder="Optional"
            />
          </div>

          <div className="form-group">
            <label htmlFor="dcw_filter_dry_weight_g">Filter Dry Weight (g)</label>
            <input
              id="dcw_filter_dry_weight_g"
              type="number"
              step="0.0001"
              {...register('dcw_filter_dry_weight_g', {
                min: { value: 0, message: 'Must be non-negative' },
                valueAsNumber: true,
              })}
              placeholder="Optional"
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="supernatant_cryovial_id">Supernatant Cryo Vial ID</label>
          <input
            id="supernatant_cryovial_id"
            type="text"
            {...register('supernatant_cryovial_id')}
            placeholder="Optional - e.g., CRYO-001"
          />
        </div>

        <div className="form-group">
          <label htmlFor="pellet_cryovial_id">Pellet Cryo Vial ID</label>
          <input
            id="pellet_cryovial_id"
            type="text"
            {...register('pellet_cryovial_id')}
            placeholder="Optional - e.g., CRYO-002"
          />
        </div>

        <div className="form-group">
          <label className="checkbox-label">
            <input type="checkbox" {...register('contamination_detected')} />
            <span>Contamination Detected</span>
          </label>
          {contaminationDetected && (
            <div className="alert alert-warning">
              <strong>⚠️ Warning:</strong> Contamination detected. Document findings in microscopy
              notes and consider filing a failure report.
            </div>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="microscopy_observations">Microscopy Notes</label>
          <textarea
            id="microscopy_observations"
            {...register('microscopy_observations')}
            placeholder="Cell morphology, viability observations, contamination details..."
            rows={3}
          />
          <p className="help-text">Optional but recommended for contamination cases</p>
        </div>

        <div className="form-group">
          <label>Sampled By</label>
          <input type="text" value={user?.full_name || ''} disabled className="disabled-input" />
        </div>

        {apiError && <div className="error-message">{apiError}</div>}

        <div className="form-actions">
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={submitting}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Saving...' : 'Save Sample'}
          </button>
        </div>
      </form>
    </Modal>
  );
};
