import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Modal } from './Modal';
import { api } from '../api/client';
import type { MediaPreparationCreate } from '../types';
import { useAuth } from '../contexts/AuthContext';
import './FormStyles.css';

interface MediaPreparationFormProps {
  isOpen: boolean;
  onClose: () => void;
  batchId: string;
  onSuccess: () => void;
}

interface FormData {
  recipe_name: string;
  phosphoric_acid_ml: number;
  phosphoric_acid_lot: string;
  calcium_sulfate_g: number;
  calcium_sulfate_lot: string;
  potassium_sulfate_g: number;
  potassium_sulfate_lot: string;
  magnesium_sulfate_g: number;
  magnesium_sulfate_lot: string;
  potassium_hydroxide_g: number;
  potassium_hydroxide_lot: string;
  glycerol_g: number;
  glycerol_lot: string;
  final_volume_l: number;
  autoclave_cycle: string;
  sterility_verified: boolean;
  notes: string;
}

export const MediaPreparationForm: React.FC<MediaPreparationFormProps> = ({
  isOpen,
  onClose,
  batchId,
  onSuccess,
}) => {
  const { register, handleSubmit, formState: { errors }, watch } = useForm<FormData>({
    defaultValues: {
      recipe_name: 'Fermentation_Basal_Salts_4pct_Glycerol',
      phosphoric_acid_ml: 26.7,
      calcium_sulfate_g: 0.93,
      potassium_sulfate_g: 18.2,
      magnesium_sulfate_g: 14.9,
      potassium_hydroxide_g: 4.13,
      glycerol_g: 40.0,
      final_volume_l: 0.9,
      sterility_verified: false,
    },
  });
  const [submitting, setSubmitting] = useState(false);
  const [apiError, setApiError] = useState('');
  const { user } = useAuth();

  const isValidBatchId = typeof batchId === 'string' && batchId.length > 0;
  const sterilityVerified = watch('sterility_verified');

  const onSubmit = async (data: FormData) => {
    if (!user) return;

    if (!isValidBatchId) {
      setApiError('Invalid batch ID');
      return;
    }

    setSubmitting(true);
    setApiError('');

    try {
      const mediaData: MediaPreparationCreate = {
        recipe_name: data.recipe_name,
        phosphoric_acid_ml: data.phosphoric_acid_ml,
        phosphoric_acid_lot: data.phosphoric_acid_lot || undefined,
        calcium_sulfate_g: data.calcium_sulfate_g,
        calcium_sulfate_lot: data.calcium_sulfate_lot || undefined,
        potassium_sulfate_g: data.potassium_sulfate_g,
        potassium_sulfate_lot: data.potassium_sulfate_lot || undefined,
        magnesium_sulfate_g: data.magnesium_sulfate_g,
        magnesium_sulfate_lot: data.magnesium_sulfate_lot || undefined,
        potassium_hydroxide_g: data.potassium_hydroxide_g,
        potassium_hydroxide_lot: data.potassium_hydroxide_lot || undefined,
        glycerol_g: data.glycerol_g,
        glycerol_lot: data.glycerol_lot || undefined,
        final_volume_l: data.final_volume_l,
        autoclave_cycle: data.autoclave_cycle,
        sterility_verified: data.sterility_verified,
        prepared_by: user.username,
        notes: data.notes || undefined,
      };

      await api.media.create(batchId, mediaData);
      onSuccess();
      onClose();
    } catch (error: any) {
      console.error('Error logging media preparation:', error);
      setApiError(error.response?.data?.detail || 'Failed to log media preparation');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Log Media Preparation">
      <form onSubmit={handleSubmit(onSubmit)} className="modal-form">
        <div className="alert alert-info">
          <strong>📋 Media Preparation:</strong> Log all components of the growth medium.
          This must be completed before inoculation.
        </div>

        <div className="form-group">
          <label htmlFor="recipe_name">
            Recipe Name <span className="required">*</span>
          </label>
          <select
            id="recipe_name"
            {...register('recipe_name', {
              required: 'Recipe name is required',
            })}
          >
            <option value="Fermentation_Basal_Salts_4pct_Glycerol">
              Fermentation Basal Salts + 4% Glycerol
            </option>
          </select>
          {errors.recipe_name && (
            <span className="error-text">{errors.recipe_name.message}</span>
          )}
        </div>

        <div className="form-section">
          <h3>Components</h3>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="phosphoric_acid_ml">
                Phosphoric Acid (mL) <span className="required">*</span>
              </label>
              <input
                id="phosphoric_acid_ml"
                type="number"
                step="0.1"
                {...register('phosphoric_acid_ml', {
                  required: 'Volume required',
                  min: { value: 0, message: 'Must be non-negative' },
                  valueAsNumber: true,
                })}
              />
              {errors.phosphoric_acid_ml && (
                <span className="error-text">{errors.phosphoric_acid_ml.message}</span>
              )}
              <p className="help-text">Typical: 26.7 mL</p>
            </div>

            <div className="form-group">
              <label htmlFor="phosphoric_acid_lot">Lot #</label>
              <input
                id="phosphoric_acid_lot"
                type="text"
                {...register('phosphoric_acid_lot')}
                placeholder="e.g., LOT-2025-001"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="calcium_sulfate_g">
                Calcium Sulfate (g) <span className="required">*</span>
              </label>
              <input
                id="calcium_sulfate_g"
                type="number"
                step="0.01"
                {...register('calcium_sulfate_g', {
                  required: 'Mass required',
                  min: { value: 0, message: 'Must be non-negative' },
                  valueAsNumber: true,
                })}
              />
              {errors.calcium_sulfate_g && (
                <span className="error-text">{errors.calcium_sulfate_g.message}</span>
              )}
              <p className="help-text">Typical: 0.93 g</p>
            </div>

            <div className="form-group">
              <label htmlFor="calcium_sulfate_lot">Lot #</label>
              <input
                id="calcium_sulfate_lot"
                type="text"
                {...register('calcium_sulfate_lot')}
                placeholder="e.g., LOT-2025-001"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="potassium_sulfate_g">
                Potassium Sulfate (g) <span className="required">*</span>
              </label>
              <input
                id="potassium_sulfate_g"
                type="number"
                step="0.01"
                {...register('potassium_sulfate_g', {
                  required: 'Mass required',
                  min: { value: 0, message: 'Must be non-negative' },
                  valueAsNumber: true,
                })}
              />
              {errors.potassium_sulfate_g && (
                <span className="error-text">{errors.potassium_sulfate_g.message}</span>
              )}
              <p className="help-text">Typical: 18.2 g</p>
            </div>

            <div className="form-group">
              <label htmlFor="potassium_sulfate_lot">Lot #</label>
              <input
                id="potassium_sulfate_lot"
                type="text"
                {...register('potassium_sulfate_lot')}
                placeholder="e.g., LOT-2025-001"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="magnesium_sulfate_g">
                Magnesium Sulfate (g) <span className="required">*</span>
              </label>
              <input
                id="magnesium_sulfate_g"
                type="number"
                step="0.01"
                {...register('magnesium_sulfate_g', {
                  required: 'Mass required',
                  min: { value: 0, message: 'Must be non-negative' },
                  valueAsNumber: true,
                })}
              />
              {errors.magnesium_sulfate_g && (
                <span className="error-text">{errors.magnesium_sulfate_g.message}</span>
              )}
              <p className="help-text">Typical: 14.9 g</p>
            </div>

            <div className="form-group">
              <label htmlFor="magnesium_sulfate_lot">Lot #</label>
              <input
                id="magnesium_sulfate_lot"
                type="text"
                {...register('magnesium_sulfate_lot')}
                placeholder="e.g., LOT-2025-001"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="potassium_hydroxide_g">
                Potassium Hydroxide (g) <span className="required">*</span>
              </label>
              <input
                id="potassium_hydroxide_g"
                type="number"
                step="0.01"
                {...register('potassium_hydroxide_g', {
                  required: 'Mass required',
                  min: { value: 0, message: 'Must be non-negative' },
                  valueAsNumber: true,
                })}
              />
              {errors.potassium_hydroxide_g && (
                <span className="error-text">{errors.potassium_hydroxide_g.message}</span>
              )}
              <p className="help-text">Typical: 4.13 g</p>
            </div>

            <div className="form-group">
              <label htmlFor="potassium_hydroxide_lot">Lot #</label>
              <input
                id="potassium_hydroxide_lot"
                type="text"
                {...register('potassium_hydroxide_lot')}
                placeholder="e.g., LOT-2025-001"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="glycerol_g">
                Glycerol (g) <span className="required">*</span>
              </label>
              <input
                id="glycerol_g"
                type="number"
                step="0.1"
                {...register('glycerol_g', {
                  required: 'Mass required',
                  min: { value: 0, message: 'Must be non-negative' },
                  valueAsNumber: true,
                })}
              />
              {errors.glycerol_g && (
                <span className="error-text">{errors.glycerol_g.message}</span>
              )}
              <p className="help-text">Typical: 40.0 g (4%)</p>
            </div>

            <div className="form-group">
              <label htmlFor="glycerol_lot">Lot #</label>
              <input
                id="glycerol_lot"
                type="text"
                {...register('glycerol_lot')}
                placeholder="e.g., LOT-2025-001"
              />
            </div>
          </div>
        </div>

        <div className="form-section">
          <h3>Preparation & Verification</h3>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="final_volume_l">
                Final Volume (L) <span className="required">*</span>
              </label>
              <input
                id="final_volume_l"
                type="number"
                step="0.01"
                {...register('final_volume_l', {
                  required: 'Volume required',
                  min: { value: 0, message: 'Must be non-negative' },
                  valueAsNumber: true,
                })}
              />
              {errors.final_volume_l && (
                <span className="error-text">{errors.final_volume_l.message}</span>
              )}
              <p className="help-text">Typical: 0.9 L (for 1L vessel with headspace)</p>
            </div>

            <div className="form-group">
              <label htmlFor="autoclave_cycle">
                Autoclave Cycle <span className="required">*</span>
              </label>
              <input
                id="autoclave_cycle"
                type="text"
                {...register('autoclave_cycle', {
                  required: 'Autoclave cycle required',
                })}
                placeholder="e.g., 121°C 30min or S-3"
              />
              {errors.autoclave_cycle && (
                <span className="error-text">{errors.autoclave_cycle.message}</span>
              )}
              <p className="help-text">Sterilization cycle used</p>
            </div>
          </div>

          <div className="form-group">
            <label className="checkbox-label">
              <input type="checkbox" {...register('sterility_verified')} />
              <span>
                <strong>Sterility Verified</strong>
              </span>
            </label>
            <p className="help-text">
              {sterilityVerified ? (
                <span className="text-success">✓ Medium confirmed sterile</span>
              ) : (
                <span className="text-warning">⚠️ Medium sterility status unconfirmed</span>
              )}
            </p>
          </div>

          <div className="form-group">
            <label htmlFor="notes">Additional Notes</label>
            <textarea
              id="notes"
              {...register('notes')}
              placeholder="Stock solution details, preparation deviations, filter sterilization details, pH adjustments, observations..."
              rows={6}
            />
            <p className="help-text">
              Document media preparation details, stock solutions used, pH adjustments, or any deviations from protocol
            </p>
          </div>
        </div>

        {apiError && <div className="error-message">{apiError}</div>}

        <div className="form-actions">
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={submitting}>
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={submitting}
          >
            {submitting ? 'Logging...' : 'Log Media Preparation'}
          </button>
        </div>
      </form>
    </Modal>
  );
};
