import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Modal } from './Modal';
import { api } from '../api/client';
import type { InoculationCreate } from '../types';
import { useAuth } from '../contexts/AuthContext';
import './FormStyles.css';

interface InoculationFormProps {
  isOpen: boolean;
  onClose: () => void;
  batchId: string;
  onSuccess: () => void;
}

interface FormData {
  cryo_vial_id: string;
  inoculum_od600: number;
  dilution_factor: number;
  inoculum_volume_ml: number;
  microscopy_observations: string;
  go_decision: boolean;
}

export const InoculationForm: React.FC<InoculationFormProps> = ({
  isOpen,
  onClose,
  batchId,
  onSuccess,
}) => {
  const { register, handleSubmit, formState: { errors }, watch } = useForm<FormData>({
    defaultValues: {
      dilution_factor: 1.0,
      inoculum_volume_ml: 100.0,
      go_decision: false,
    },
  });
  const [submitting, setSubmitting] = useState(false);
  const [apiError, setApiError] = useState('');
  const { user } = useAuth();

  // Validate batchId
  const isValidBatchId = typeof batchId === 'string' && batchId.length > 0;

  const goDecision = watch('go_decision');

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
      const inoculationData: InoculationCreate = {
        cryo_vial_id: data.cryo_vial_id,
        inoculum_od600: data.inoculum_od600,
        dilution_factor: data.dilution_factor,
        inoculum_volume_ml: data.inoculum_volume_ml,
        microscopy_observations: data.microscopy_observations,
        go_decision: data.go_decision,
        inoculated_by: user.username,
      };

      await api.inoculation.create(batchId, inoculationData);
      onSuccess();
      onClose();
    } catch (error: any) {
      console.error('Error logging inoculation:', error);
      setApiError(error.response?.data?.detail || 'Failed to log inoculation');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Log Inoculation (T=0)">
      <form onSubmit={handleSubmit(onSubmit)} className="modal-form">
        <div className="alert alert-info">
          <strong>⚠️ Important:</strong> This action sets T=0 and changes batch status to "running".
          Ensure all pre-inoculation calibrations have passed.
        </div>

        <div className="form-group">
          <label htmlFor="cryo_vial_id">
            Cryo Vial ID <span className="required">*</span>
          </label>
          <input
            id="cryo_vial_id"
            type="text"
            {...register('cryo_vial_id', {
              required: 'Cryo vial ID is required',
              pattern: {
                value: /^CRYO-\d+$/,
                message: 'Format: CRYO-001, CRYO-002, etc.',
              },
            })}
            placeholder="CRYO-001"
          />
          {errors.cryo_vial_id && (
            <span className="error-text">{errors.cryo_vial_id.message}</span>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="inoculum_od600">
            Inoculum OD₆₀₀ <span className="required">*</span>
          </label>
          <input
            id="inoculum_od600"
            type="number"
            step="0.1"
            {...register('inoculum_od600', {
              required: 'OD600 is required',
              min: { value: 0.1, message: 'Must be at least 0.1' },
              max: { value: 10, message: 'Must be less than 10' },
              valueAsNumber: true,
            })}
            placeholder="4.5"
          />
          {errors.inoculum_od600 && (
            <span className="error-text">{errors.inoculum_od600.message}</span>
          )}
          <p className="help-text">Typical range: 3.0 - 6.0</p>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="dilution_factor">
              Dilution Factor
            </label>
            <input
              id="dilution_factor"
              type="number"
              step="0.1"
              {...register('dilution_factor', {
                min: { value: 1, message: 'Must be at least 1' },
                valueAsNumber: true,
              })}
              placeholder="1.0"
            />
            {errors.dilution_factor && (
              <span className="error-text">{errors.dilution_factor.message}</span>
            )}
            <p className="help-text">Inoculum dilution factor (default: 1.0)</p>
          </div>

          <div className="form-group">
            <label htmlFor="inoculum_volume_ml">
              Inoculum Volume (mL)
            </label>
            <input
              id="inoculum_volume_ml"
              type="number"
              step="0.1"
              {...register('inoculum_volume_ml', {
                min: { value: 0, message: 'Must be non-negative' },
                valueAsNumber: true,
              })}
              placeholder="100.0"
            />
            {errors.inoculum_volume_ml && (
              <span className="error-text">{errors.inoculum_volume_ml.message}</span>
            )}
            <p className="help-text">Volume of inoculum used (default: 100.0 mL)</p>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="microscopy_observations">
            Microscopy Observations <span className="required">*</span>
          </label>
          <textarea
            id="microscopy_observations"
            {...register('microscopy_observations', {
              required: 'Microscopy observations are required',
              minLength: { value: 10, message: 'Please provide detailed observations' },
            })}
            placeholder="Describe cell morphology, contamination check, viability..."
            rows={4}
          />
          {errors.microscopy_observations && (
            <span className="error-text">{errors.microscopy_observations.message}</span>
          )}
          <p className="help-text">
            Include: cell morphology, contamination status, estimated viability
          </p>
        </div>

        <div className="form-group">
          <label className="checkbox-label checkbox-go">
            <input type="checkbox" {...register('go_decision')} />
            <span>
              <strong>GO Decision - Proceed with Inoculation</strong>
            </span>
          </label>
          <p className="help-text">
            {goDecision ? (
              <span className="text-success">
                ✓ Cells are healthy, no contamination detected, proceeding with batch
              </span>
            ) : (
              <span className="text-warning">
                ⚠️ You must confirm GO decision to inoculate
              </span>
            )}
          </p>
        </div>

        <div className="form-group">
          <label>Inoculated By</label>
          <input type="text" value={user?.full_name || ''} disabled className="disabled-input" />
        </div>

        {apiError && <div className="error-message">{apiError}</div>}

        <div className="form-actions">
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={submitting}>
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={submitting || !goDecision}
          >
            {submitting ? 'Logging...' : 'Log Inoculation & Start T=0'}
          </button>
        </div>
      </form>
    </Modal>
  );
};
