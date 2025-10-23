import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Modal } from './Modal';
import { api } from '../api/client';
import type { BatchClosureCreate } from '../types';
import { useAuth } from '../contexts/AuthContext';
import './FormStyles.css';

interface ClosureFormProps {
  isOpen: boolean;
  onClose: () => void;
  batchId: string;
  onSuccess: () => void;
}

interface FormData {
  final_od600: number;
  total_runtime_hours: number;
  glycerol_depletion_time_hours: number;
  outcome: 'Complete' | 'Aborted_Contamination' | 'Aborted_Sensor_Failure' | 'Aborted_Other';
  approved_by: string;
  notes: string;
}

export const ClosureForm: React.FC<ClosureFormProps> = ({
  isOpen,
  onClose,
  batchId,
  onSuccess,
}) => {
  const { register, handleSubmit, formState: { errors }, watch } = useForm<FormData>({
    defaultValues: {
      outcome: 'Complete',
    },
  });
  const [submitting, setSubmitting] = useState(false);
  const [apiError, setApiError] = useState('');
  const { user } = useAuth();

  // Validate batchId
  const isValidBatchId = typeof batchId === 'string' && batchId.length > 0;

  const outcome = watch('outcome');

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
      const closureData: BatchClosureCreate = {
        final_od600: data.final_od600,
        total_runtime_hours: data.total_runtime_hours,
        glycerol_depletion_time_hours: data.glycerol_depletion_time_hours || undefined,
        outcome: data.outcome,
        closed_by: String(user.user_id),
        approved_by: data.approved_by,
        notes: data.notes || undefined,
      };

      await api.closure.close(batchId, closureData);
      onSuccess();
      onClose();
    } catch (error: any) {
      console.error('Error closing batch:', error);
      setApiError(error.response?.data?.detail || 'Failed to close batch');
    } finally {
      setSubmitting(false);
    }
  };

  const isEngineerOrAdmin = user?.role === 'engineer' || user?.role === 'admin';

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Close Batch">
      <form onSubmit={handleSubmit(onSubmit)} className="modal-form">
        <div className="alert alert-info">
          <strong>ℹ️ Batch Closure:</strong> This action will mark the batch as complete and lock
          all records. Ensure all data has been entered and verified.
        </div>

        <div className="form-group">
          <label htmlFor="final_od600">
            Final OD₆₀₀ <span className="required">*</span>
          </label>
          <input
            id="final_od600"
            type="number"
            step="0.1"
            {...register('final_od600', {
              required: 'Final OD600 is required',
              min: { value: 0, message: 'Must be non-negative' },
              valueAsNumber: true,
            })}
            placeholder="45.2"
          />
          {errors.final_od600 && (
            <span className="error-text">{errors.final_od600.message}</span>
          )}
          <p className="help-text">Final biomass concentration at batch termination</p>
        </div>

        <div className="form-group">
          <label htmlFor="total_runtime_hours">
            Total Runtime (hours) <span className="required">*</span>
          </label>
          <input
            id="total_runtime_hours"
            type="number"
            step="0.1"
            {...register('total_runtime_hours', {
              required: 'Total runtime is required',
              min: { value: 0, message: 'Must be non-negative' },
              valueAsNumber: true,
            })}
            placeholder="16.5"
          />
          {errors.total_runtime_hours && (
            <span className="error-text">{errors.total_runtime_hours.message}</span>
          )}
          <p className="help-text">Time from inoculation (T=0) to batch termination</p>
        </div>

        <div className="form-group">
          <label htmlFor="glycerol_depletion_time_hours">
            Glycerol Depletion Time (hours)
          </label>
          <input
            id="glycerol_depletion_time_hours"
            type="number"
            step="0.1"
            {...register('glycerol_depletion_time_hours', {
              min: { value: 0, message: 'Must be non-negative' },
              valueAsNumber: true,
            })}
            placeholder="14.2"
          />
          {errors.glycerol_depletion_time_hours && (
            <span className="error-text">{errors.glycerol_depletion_time_hours.message}</span>
          )}
          <p className="help-text">
            Time when DO spike indicated glycerol depletion (leave blank if not observed)
          </p>
        </div>

        <div className="form-group">
          <label htmlFor="outcome">
            Batch Outcome <span className="required">*</span>
          </label>
          <select id="outcome" {...register('outcome', { required: true })}>
            <option value="Complete">Complete - All objectives met</option>
            <option value="Aborted_Contamination">Aborted - Contamination detected</option>
            <option value="Aborted_Sensor_Failure">Aborted - Sensor failure</option>
            <option value="Aborted_Other">Aborted - Other reason</option>
          </select>
          <p className={`help-text outcome-description outcome-${outcome.toLowerCase()}`}>
            {outcome === 'Complete' && '✓ Batch completed successfully with all quality criteria met'}
            {outcome === 'Aborted_Contamination' && '✗ Batch aborted due to contamination'}
            {outcome === 'Aborted_Sensor_Failure' && '✗ Batch aborted due to sensor failure'}
            {outcome === 'Aborted_Other' && '✗ Batch aborted for other reason'}
          </p>
        </div>

        <div className="form-group">
          <label htmlFor="approved_by">
            Engineer Approval <span className="required">*</span>
          </label>
          <input
            id="approved_by"
            type="text"
            {...register('approved_by', {
              required: 'Engineer approval ID is required',
            })}
            placeholder="USER:E001"
          />
          {errors.approved_by && (
            <span className="error-text">{errors.approved_by.message}</span>
          )}
          <p className="help-text">User ID of approving engineer (must have engineer role)</p>
        </div>

        {!isEngineerOrAdmin && (
          <div className="alert alert-warning">
            <strong>⚠️ Permission Required:</strong> Only engineers and admins can close batches.
            Your current role: {user?.role}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="notes">Closure Notes</label>
          <textarea
            id="notes"
            {...register('notes')}
            placeholder="Final observations, harvest details, storage locations, conclusions..."
            rows={6}
          />
          <p className="help-text">
            Document final batch outcomes, cell banking details, key observations, or any deviations
          </p>
        </div>

        <div className="form-group">
          <label>Closed By</label>
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
            disabled={submitting || !isEngineerOrAdmin}
          >
            {submitting ? 'Closing Batch...' : 'Close Batch'}
          </button>
        </div>
      </form>
    </Modal>
  );
};
