import React, { useState } from 'react';
import { Modal } from './Modal';
import { api } from '../api/client';
import type { Batch } from '../types';
import './FormStyles.css';

export interface EditBatchFormProps {
  isOpen: boolean;
  onClose: () => void;
  batch: Batch;
  onSuccess?: (data: Batch) => void;
}

export const EditBatchForm: React.FC<EditBatchFormProps> = ({
  isOpen,
  onClose,
  batch,
  onSuccess,
}) => {
  const [notes, setNotes] = useState(batch.notes || '');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const updatedBatch = await api.batches.update(batch.batch_id, notes);

      if (onSuccess) {
        onSuccess(updatedBatch);
      }
      onClose();
    } catch (err) {
      console.error('Error updating batch:', err);
      setError(err instanceof Error ? err.message : 'Failed to update batch');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Edit Batch">
      <form onSubmit={handleSubmit} className="form-container">
        {error && <div className="error-banner">{error}</div>}

        <div className="form-group">
          <label htmlFor="batch_number">Batch Number (read-only)</label>
          <input
            id="batch_number"
            type="text"
            value={`${batch.batch_number}-${batch.phase}`}
            disabled
          />
          <small>Cannot edit batch number after creation</small>
        </div>

        <div className="form-group">
          <label htmlFor="vessel_id">Vessel ID (read-only)</label>
          <input
            id="vessel_id"
            type="text"
            value={batch.vessel_id}
            disabled
          />
          <small>Cannot edit vessel after creation</small>
        </div>

        <div className="form-group">
          <label htmlFor="notes">Notes</label>
          <textarea
            id="notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add or update batch notes..."
            rows={6}
          />
          <small>Update batch notes, observations, or metadata</small>
        </div>

        <div className="form-actions">
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Saving...' : 'Save Notes'}
          </button>
        </div>
      </form>
    </Modal>
  );
};
