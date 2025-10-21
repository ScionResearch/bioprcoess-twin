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
  batchId: number;
  onSuccess: () => void;
}

interface FormData {
  od600_raw: number;
  od600_dilution_factor: number;
  dcw_g_l: number;
  contamination_detected: boolean;
  microscopy_notes: string;
}

export const SampleForm: React.FC<SampleFormProps> = ({
  isOpen,
  onClose,
  batchId,
  onSuccess,
}) => {
  const { register, handleSubmit, formState: { errors }, watch } = useForm<FormData>({
    defaultValues: {
      od600_dilution_factor: 1.0,
      contamination_detected: false,
    },
  });
  const [submitting, setSubmitting] = useState(false);
  const [apiError, setApiError] = useState('');
  const { user } = useAuth();

  const od600Raw = watch('od600_raw');
  const dilutionFactor = watch('od600_dilution_factor');
  const contaminationDetected = watch('contamination_detected');

  const od600Corrected = od600Raw && dilutionFactor ? od600Raw * dilutionFactor : 0;

  const onSubmit = async (data: FormData) => {
    if (!user) return;

    setSubmitting(true);
    setApiError('');

    try {
      const sampleData: SampleCreate = {
        od600_raw: data.od600_raw,
        od600_dilution_factor: data.od600_dilution_factor,
        dcw_g_l: data.dcw_g_l || undefined,
        contamination_detected: data.contamination_detected,
        microscopy_notes: data.microscopy_notes || undefined,
        sampled_by: user.user_id,
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
            <strong>OD₆₀₀ Corrected:</strong> {od600Corrected.toFixed(2)}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="dcw_g_l">Dry Cell Weight (g/L)</label>
          <input
            id="dcw_g_l"
            type="number"
            step="0.01"
            {...register('dcw_g_l', {
              min: { value: 0, message: 'Must be non-negative' },
              valueAsNumber: true,
            })}
            placeholder="Optional - measured or calculated"
          />
          {errors.dcw_g_l && <span className="error-text">{errors.dcw_g_l.message}</span>}
          <p className="help-text">Leave blank if not measured. System may auto-calculate from OD600.</p>
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
          <label htmlFor="microscopy_notes">Microscopy Notes</label>
          <textarea
            id="microscopy_notes"
            {...register('microscopy_notes')}
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
