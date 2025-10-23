import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Modal } from './Modal';
import { api } from '../api/client';
import type { FailureCreate } from '../types';
import { useAuth } from '../contexts/AuthContext';
import './FormStyles.css';

interface FailureFormProps {
  isOpen: boolean;
  onClose: () => void;
  batchId: string;
  onSuccess: () => void;
}

interface FormData {
  deviation_level: 1 | 2 | 3;
  category: string;
  deviation_start_time: string;
  deviation_end_time: string;
  description: string;
  root_cause: string;
  corrective_action: string;
  impact_assessment: string;
}

export const FailureForm: React.FC<FailureFormProps> = ({
  isOpen,
  onClose,
  batchId,
  onSuccess,
}) => {
  const { register, handleSubmit, formState: { errors }, watch } = useForm<FormData>({
    defaultValues: {
      deviation_level: 1,
    },
  });
  const [submitting, setSubmitting] = useState(false);
  const [apiError, setApiError] = useState('');
  const { user } = useAuth();

  // Validate batchId
  const isValidBatchId = typeof batchId === 'string' && batchId.length > 0;

  const deviation_level = watch('deviation_level');

  const getSeverityDescription = (level: number) => {
    switch (level) {
      case 1:
        return 'Minor deviation - does not affect batch quality';
      case 2:
        return 'Moderate deviation - may affect batch quality, review required';
      case 3:
        return 'Critical failure - batch quality compromised, immediate action needed';
      default:
        return '';
    }
  };

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
      const failureData: FailureCreate = {
        deviation_level: data.deviation_level,
        category: data.category as any,
        deviation_start_time: data.deviation_start_time,
        deviation_end_time: data.deviation_end_time || undefined,
        description: data.description,
        root_cause: data.root_cause || undefined,
        corrective_action: data.corrective_action || undefined,
        impact_assessment: data.impact_assessment || undefined,
        reported_by: String(user.user_id),
      };

      await api.failures.create(batchId, failureData);
      onSuccess();
      onClose();
    } catch (error: any) {
      console.error('Error creating failure report:', error);
      setApiError(error.response?.data?.detail || 'Failed to create failure report');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Report Failure/Deviation">
      <form onSubmit={handleSubmit(onSubmit)} className="modal-form">
        <div className="form-group">
          <label htmlFor="deviation_level">
            Deviation Level <span className="required">*</span>
          </label>
          <select
            id="deviation_level"
            {...register('deviation_level', {
              required: true,
              valueAsNumber: true,
            })}
          >
            <option value={1}>Level 1 - Minor</option>
            <option value={2}>Level 2 - Moderate</option>
            <option value={3}>Level 3 - Critical</option>
          </select>
          <p className={`help-text severity-description severity-${deviation_level}`}>
            {getSeverityDescription(deviation_level)}
          </p>
        </div>

        <div className="form-group">
          <label htmlFor="description">
            Description <span className="required">*</span>
          </label>
          <textarea
            id="description"
            {...register('description', {
              required: 'Description is required',
            })}
            placeholder="Describe what happened, when it occurred, and immediate observations..."
            rows={4}
          />
          {errors.description && (
            <span className="error-text">{errors.description.message}</span>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="root_cause">Root Cause Analysis</label>
          <textarea
            id="root_cause"
            {...register('root_cause')}
            placeholder="What caused this issue? Include investigation findings..."
            rows={3}
          />
          <p className="help-text">Can be filled immediately or updated later after investigation</p>
        </div>

        <div className="form-group">
          <label htmlFor="corrective_action">Corrective Action</label>
          <textarea
            id="corrective_action"
            {...register('corrective_action')}
            placeholder="What actions were/will be taken to address this issue?"
            rows={3}
          />
          <p className="help-text">Document steps taken to resolve or mitigate the issue</p>
        </div>

        {deviation_level === 3 && (
          <div className="alert alert-danger">
            <strong>⚠️ Critical Failure:</strong> This report requires engineer review. The batch
            may need to be terminated or assessed for data integrity.
          </div>
        )}

        <div className="form-group">
          <label>Reported By</label>
          <input type="text" value={user?.full_name || ''} disabled className="disabled-input" />
        </div>

        {apiError && <div className="error-message">{apiError}</div>}

        <div className="form-actions">
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={submitting}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Submitting...' : 'Submit Report'}
          </button>
        </div>
      </form>
    </Modal>
  );
};
