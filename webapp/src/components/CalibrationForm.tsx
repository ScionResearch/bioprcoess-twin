import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Modal } from './Modal';
import { api } from '../api/client';
import type { CalibrationCreate } from '../types';
import { useAuth } from '../contexts/AuthContext';
import './FormStyles.css';

interface CalibrationFormProps {
  isOpen: boolean;
  onClose: () => void;
  batchId: number;
  onSuccess: () => void;
}

interface FormData {
  probe_type: 'pH' | 'DO' | 'Temp';
  buffer_low_value: number;
  buffer_high_value: number;
  reading_low: number;
  reading_high: number;
  pass: boolean;
  notes: string;
}

export const CalibrationForm: React.FC<CalibrationFormProps> = ({
  isOpen,
  onClose,
  batchId,
  onSuccess,
}) => {
  const { register, handleSubmit, formState: { errors }, watch } = useForm<FormData>({
    defaultValues: {
      probe_type: 'pH',
      pass: true,
    },
  });
  const [submitting, setSubmitting] = useState(false);
  const [apiError, setApiError] = useState('');
  const { user } = useAuth();

  const probeType = watch('probe_type');

  const onSubmit = async (data: FormData) => {
    if (!user) return;

    setSubmitting(true);
    setApiError('');

    try {
      const calibrationData: CalibrationCreate = {
        probe_type: data.probe_type,
        buffer_low_value: data.buffer_low_value,
        buffer_high_value: data.buffer_high_value,
        reading_low: data.reading_low,
        reading_high: data.reading_high,
        pass_: data.pass,
        calibrated_by: user.user_id,
        notes: data.notes || undefined,
      };

      await api.calibrations.create(batchId, calibrationData);
      onSuccess();
      onClose();
    } catch (error: any) {
      console.error('Error creating calibration:', error);
      setApiError(error.response?.data?.detail || 'Failed to create calibration');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Add Calibration">
      <form onSubmit={handleSubmit(onSubmit)} className="modal-form">
        <div className="form-group">
          <label htmlFor="probe_type">
            Probe Type <span className="required">*</span>
          </label>
          <select id="probe_type" {...register('probe_type', { required: true })}>
            <option value="pH">pH</option>
            <option value="DO">Dissolved Oxygen (DO)</option>
            <option value="Temp">Temperature</option>
          </select>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="buffer_low_value">
              Buffer Low Value <span className="required">*</span>
            </label>
            <input
              id="buffer_low_value"
              type="number"
              step="0.01"
              {...register('buffer_low_value', {
                required: 'Required',
                valueAsNumber: true,
              })}
              placeholder={probeType === 'pH' ? '4.01' : '0'}
            />
            {errors.buffer_low_value && (
              <span className="error-text">{errors.buffer_low_value.message}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="reading_low">
              Reading Low <span className="required">*</span>
            </label>
            <input
              id="reading_low"
              type="number"
              step="0.01"
              {...register('reading_low', {
                required: 'Required',
                valueAsNumber: true,
              })}
              placeholder={probeType === 'pH' ? '4.02' : '0'}
            />
            {errors.reading_low && (
              <span className="error-text">{errors.reading_low.message}</span>
            )}
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="buffer_high_value">
              Buffer High Value <span className="required">*</span>
            </label>
            <input
              id="buffer_high_value"
              type="number"
              step="0.01"
              {...register('buffer_high_value', {
                required: 'Required',
                valueAsNumber: true,
              })}
              placeholder={probeType === 'pH' ? '7.00' : '100'}
            />
            {errors.buffer_high_value && (
              <span className="error-text">{errors.buffer_high_value.message}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="reading_high">
              Reading High <span className="required">*</span>
            </label>
            <input
              id="reading_high"
              type="number"
              step="0.01"
              {...register('reading_high', {
                required: 'Required',
                valueAsNumber: true,
              })}
              placeholder={probeType === 'pH' ? '6.98' : '100'}
            />
            {errors.reading_high && (
              <span className="error-text">{errors.reading_high.message}</span>
            )}
          </div>
        </div>

        <div className="form-group">
          <label className="checkbox-label">
            <input type="checkbox" {...register('pass')} />
            <span>Calibration Passed</span>
          </label>
          <p className="help-text">
            {probeType === 'pH' && 'pH calibrations must achieve ≥95% slope to pass'}
            {probeType === 'DO' && 'DO calibration must stabilize within acceptable range'}
            {probeType === 'Temp' && 'Temperature reading must be within ±0.5°C'}
          </p>
        </div>

        <div className="form-group">
          <label htmlFor="notes">Notes</label>
          <textarea
            id="notes"
            {...register('notes')}
            placeholder="Optional notes about this calibration..."
            rows={3}
          />
        </div>

        <div className="form-group">
          <label>Calibrated By</label>
          <input type="text" value={user?.full_name || ''} disabled className="disabled-input" />
        </div>

        {apiError && <div className="error-message">{apiError}</div>}

        <div className="form-actions">
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={submitting}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Saving...' : 'Save Calibration'}
          </button>
        </div>
      </form>
    </Modal>
  );
};
