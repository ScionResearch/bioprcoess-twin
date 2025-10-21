import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { api } from '../api/client';
import { BatchCreate } from '../types';
import { useAuth } from '../contexts/AuthContext';
import './CreateBatch.css';

interface FormData {
  batch_number: number;
  phase: 'A' | 'B' | 'C';
  vessel_id: string;
  notes: string;
}

export const CreateBatch: React.FC = () => {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>();
  const [submitting, setSubmitting] = useState(false);
  const [apiError, setApiError] = useState('');
  const navigate = useNavigate();
  const { user } = useAuth();

  const onSubmit = async (data: FormData) => {
    if (!user) return;

    setSubmitting(true);
    setApiError('');

    try {
      const batchData: BatchCreate = {
        batch_number: data.batch_number,
        phase: data.phase,
        vessel_id: data.vessel_id,
        operator_id: user.user_id,
        notes: data.notes || undefined,
      };

      const batch = await api.batches.create(batchData);
      navigate(`/batches/${batch.batch_id}`);
    } catch (error: any) {
      console.error('Error creating batch:', error);
      setApiError(error.response?.data?.detail || 'Failed to create batch');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page-container">
      <div className="form-header">
        <button
          className="btn-back"
          onClick={() => navigate('/batches')}
        >
          ← Back to Batches
        </button>
        <h1>Create New Batch</h1>
      </div>

      <div className="form-container">
        <form onSubmit={handleSubmit(onSubmit)} className="batch-form">
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="batch_number">
                Batch Number <span className="required">*</span>
              </label>
              <input
                id="batch_number"
                type="number"
                min="1"
                max="18"
                {...register('batch_number', {
                  required: 'Batch number is required',
                  min: { value: 1, message: 'Must be between 1 and 18' },
                  max: { value: 18, message: 'Must be between 1 and 18' },
                  valueAsNumber: true,
                })}
                placeholder="1-18"
              />
              {errors.batch_number && (
                <span className="error-text">{errors.batch_number.message}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="phase">
                Phase <span className="required">*</span>
              </label>
              <select
                id="phase"
                {...register('phase', { required: 'Phase is required' })}
              >
                <option value="">Select phase</option>
                <option value="A">A</option>
                <option value="B">B</option>
                <option value="C">C</option>
              </select>
              {errors.phase && (
                <span className="error-text">{errors.phase.message}</span>
              )}
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="vessel_id">
              Vessel ID <span className="required">*</span>
            </label>
            <input
              id="vessel_id"
              type="text"
              {...register('vessel_id', {
                required: 'Vessel ID is required',
                pattern: {
                  value: /^V-\d{2}$/,
                  message: 'Format: V-01, V-02, etc.',
                },
              })}
              placeholder="V-01"
            />
            {errors.vessel_id && (
              <span className="error-text">{errors.vessel_id.message}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="notes">Notes</label>
            <textarea
              id="notes"
              {...register('notes')}
              placeholder="Optional notes about this batch..."
              rows={4}
            />
          </div>

          <div className="form-group">
            <label>Operator</label>
            <input
              type="text"
              value={user?.full_name || ''}
              disabled
              className="disabled-input"
            />
          </div>

          {apiError && (
            <div className="error-message">
              {apiError}
            </div>
          )}

          <div className="form-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => navigate('/batches')}
              disabled={submitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting}
            >
              {submitting ? 'Creating...' : 'Create Batch'}
            </button>
          </div>
        </form>

        <div className="info-panel">
          <h3>Batch Creation Guidelines</h3>
          <ul>
            <li>Batch numbers must be unique (1-18)</li>
            <li>Phase indicates experimental condition (A/B/C)</li>
            <li>Vessel format: V-01, V-02, etc.</li>
            <li>After creation, proceed with calibrations</li>
            <li>All calibrations must pass before inoculation</li>
          </ul>
        </div>
      </div>
    </div>
  );
};
