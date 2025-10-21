import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { Batch, Calibration, Sample, Failure, Inoculation } from '../types';
import { useAuth } from '../contexts/AuthContext';
import { CalibrationForm } from '../components/CalibrationForm';
import { InoculationForm } from '../components/InoculationForm';
import { SampleForm } from '../components/SampleForm';
import { FailureForm } from '../components/FailureForm';
import { ClosureForm } from '../components/ClosureForm';
import './BatchDashboard.css';

export const BatchDashboard: React.FC = () => {
  const { batchId } = useParams<{ batchId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [batch, setBatch] = useState<Batch | null>(null);
  const [calibrations, setCalibrations] = useState<Calibration[]>([]);
  const [inoculation, setInoculation] = useState<Inoculation | null>(null);
  const [samples, setSamples] = useState<Sample[]>([]);
  const [failures, setFailures] = useState<Failure[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [activeModal, setActiveModal] = useState<
    'calibration' | 'inoculation' | 'sample' | 'failure' | 'closure' | null
  >(null);

  useEffect(() => {
    if (batchId) {
      loadBatchData();
    }
  }, [batchId]);

  const loadBatchData = async () => {
    if (!batchId) return;

    try {
      setLoading(true);
      const id = parseInt(batchId);

      const [batchData, calibrationsData, inoculationData, samplesData, failuresData] =
        await Promise.all([
          api.batches.get(id),
          api.calibrations.list(id),
          api.inoculation.get(id),
          api.samples.list(id),
          api.failures.list(id),
        ]);

      setBatch(batchData);
      setCalibrations(calibrationsData);
      setInoculation(inoculationData);
      setSamples(samplesData);
      setFailures(failuresData);
    } catch (err) {
      console.error('Error loading batch data:', err);
      setError('Failed to load batch data');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return '#f59e0b';
      case 'running':
        return '#3b82f6';
      case 'complete':
        return '#10b981';
      case 'failed':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  const canInoculate = () => {
    if (!batch || batch.status !== 'pending') return false;
    if (inoculation) return false;

    // Check if all probe types have passing calibrations
    const probeTypes = ['pH', 'DO', 'Temp'];
    return probeTypes.every((type) =>
      calibrations.some((cal) => cal.probe_type === type && cal.pass)
    );
  };

  const canAddSample = () => {
    return batch?.status === 'running' && inoculation !== null;
  };

  const canCloseBatch = () => {
    if (!batch || !user) return false;
    if (batch.status !== 'running') return false;
    if (batch.total_samples_count < 8) return false;
    return user.role === 'engineer' || user.role === 'admin';
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading">Loading batch data...</div>
      </div>
    );
  }

  if (error || !batch) {
    return (
      <div className="page-container">
        <div className="error-banner">
          {error || 'Batch not found'}
          <button onClick={() => navigate('/batches')}>Back to Batches</button>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="dashboard-header">
        <button className="btn-back" onClick={() => navigate('/batches')}>
          ← Back to Batches
        </button>
        <div className="batch-title">
          <h1>
            Batch {batch.batch_number}-{batch.phase}
          </h1>
          <span
            className="status-indicator"
            style={{ backgroundColor: getStatusColor(batch.status) }}
          >
            {batch.status.toUpperCase()}
          </span>
        </div>
        <div className="batch-meta">
          <span>Vessel: {batch.vessel_id}</span>
          <span>Created: {formatDate(batch.created_at)}</span>
          {batch.current_timepoint_hours !== null && (
            <span className="timepoint">
              T = {batch.current_timepoint_hours.toFixed(1)} hours
            </span>
          )}
        </div>
      </div>

      <div className="dashboard-grid">
        {/* Calibrations Section */}
        <div className="dashboard-card">
          <div className="card-header">
            <h2>Calibrations ({calibrations.length})</h2>
            {batch.status === 'pending' && (
              <button
                className="btn btn-small btn-primary"
                onClick={() => setActiveModal('calibration')}
              >
                + Add Calibration
              </button>
            )}
          </div>
          <div className="card-content">
            {calibrations.length === 0 ? (
              <p className="empty-message">No calibrations yet</p>
            ) : (
              <div className="calibrations-list">
                {calibrations.map((cal) => (
                  <div key={cal.calibration_id} className="calibration-item">
                    <div className="calibration-header">
                      <strong>{cal.probe_type}</strong>
                      <span className={cal.pass ? 'badge-pass' : 'badge-fail'}>
                        {cal.pass ? 'PASS' : 'FAIL'}
                      </span>
                    </div>
                    <div className="calibration-details">
                      <span>
                        Low: {cal.buffer_low_value} → {cal.reading_low}
                      </span>
                      <span>
                        High: {cal.buffer_high_value} → {cal.reading_high}
                      </span>
                      {cal.slope_percent !== null && (
                        <span>Slope: {cal.slope_percent.toFixed(2)}%</span>
                      )}
                    </div>
                    <div className="calibration-footer">
                      {formatDate(cal.calibrated_at)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Inoculation Section */}
        <div className="dashboard-card">
          <div className="card-header">
            <h2>Inoculation (T=0)</h2>
            {!inoculation && canInoculate() && (
              <button
                className="btn btn-small btn-primary"
                onClick={() => setActiveModal('inoculation')}
              >
                + Log Inoculation
              </button>
            )}
          </div>
          <div className="card-content">
            {!inoculation ? (
              <div>
                <p className="empty-message">Not inoculated yet</p>
                {!canInoculate() && batch.status === 'pending' && (
                  <p className="warning-message">
                    Complete calibrations (pH, DO, Temp) before inoculation
                  </p>
                )}
              </div>
            ) : (
              <div className="inoculation-details">
                <div className="detail-row">
                  <span className="label">Cryo Vial:</span>
                  <span>{inoculation.cryo_vial_id}</span>
                </div>
                <div className="detail-row">
                  <span className="label">OD600:</span>
                  <span>{inoculation.inoculum_od600}</span>
                </div>
                <div className="detail-row">
                  <span className="label">GO Decision:</span>
                  <span className={inoculation.go_decision ? 'badge-pass' : 'badge-fail'}>
                    {inoculation.go_decision ? 'GO' : 'NO-GO'}
                  </span>
                </div>
                <div className="detail-row">
                  <span className="label">Time:</span>
                  <span>{formatDate(inoculation.inoculated_at)}</span>
                </div>
                <div className="microscopy-notes">
                  <strong>Microscopy:</strong>
                  <p>{inoculation.microscopy_observations}</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Samples Section */}
        <div className="dashboard-card full-width">
          <div className="card-header">
            <h2>Samples ({samples.length})</h2>
            {canAddSample() && (
              <button
                className="btn btn-small btn-primary"
                onClick={() => setActiveModal('sample')}
              >
                + Add Sample
              </button>
            )}
          </div>
          <div className="card-content">
            {samples.length === 0 ? (
              <p className="empty-message">No samples yet</p>
            ) : (
              <div className="samples-table-wrapper">
                <table className="samples-table">
                  <thead>
                    <tr>
                      <th>Timepoint (h)</th>
                      <th>OD600 Raw</th>
                      <th>Dilution</th>
                      <th>OD600 Corrected</th>
                      <th>DCW (g/L)</th>
                      <th>Contamination</th>
                      <th>Sampled At</th>
                    </tr>
                  </thead>
                  <tbody>
                    {samples.map((sample) => (
                      <tr key={sample.sample_id}>
                        <td>{sample.timepoint_hours.toFixed(1)}</td>
                        <td>{sample.od600_raw.toFixed(2)}</td>
                        <td>{sample.od600_dilution_factor}x</td>
                        <td>{sample.od600_corrected.toFixed(2)}</td>
                        <td>{sample.dcw_g_l?.toFixed(2) || 'N/A'}</td>
                        <td>
                          {sample.contamination_detected ? (
                            <span className="badge-fail">YES</span>
                          ) : (
                            <span className="badge-pass">NO</span>
                          )}
                        </td>
                        <td>{formatDate(sample.sampled_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Failures Section */}
        <div className="dashboard-card full-width">
          <div className="card-header">
            <h2>Failures/Deviations ({failures.length})</h2>
            {batch.status !== 'complete' && (
              <button
                className="btn btn-small btn-secondary"
                onClick={() => setActiveModal('failure')}
              >
                + Report Failure
              </button>
            )}
          </div>
          <div className="card-content">
            {failures.length === 0 ? (
              <p className="empty-message">No failures reported</p>
            ) : (
              <div className="failures-list">
                {failures.map((failure) => (
                  <div key={failure.failure_id} className="failure-item">
                    <div className="failure-header">
                      <span className={`severity-badge severity-${failure.severity}`}>
                        Level {failure.severity}
                      </span>
                      <span>{formatDate(failure.reported_at)}</span>
                    </div>
                    <div className="failure-content">
                      <strong>Description:</strong>
                      <p>{failure.description}</p>
                      {failure.root_cause && (
                        <>
                          <strong>Root Cause:</strong>
                          <p>{failure.root_cause}</p>
                        </>
                      )}
                      {failure.corrective_action && (
                        <>
                          <strong>Corrective Action:</strong>
                          <p>{failure.corrective_action}</p>
                        </>
                      )}
                    </div>
                    {failure.reviewed && (
                      <div className="failure-footer">
                        Reviewed by {failure.reviewed_by} on{' '}
                        {formatDate(failure.reviewed_at)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Batch Closure Section */}
        {canCloseBatch() && (
          <div className="dashboard-card full-width closure-card">
            <div className="card-header">
              <h2>Batch Closure</h2>
            </div>
            <div className="card-content">
              <p>
                Ready to close batch. Minimum sample count met ({batch.total_samples_count}{' '}
                samples).
              </p>
              <button
                className="btn btn-primary"
                onClick={() => setActiveModal('closure')}
              >
                Close Batch
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      <CalibrationForm
        isOpen={activeModal === 'calibration'}
        onClose={() => setActiveModal(null)}
        batchId={batchId ? parseInt(batchId) : 0}
        onSuccess={loadBatchData}
      />
      <InoculationForm
        isOpen={activeModal === 'inoculation'}
        onClose={() => setActiveModal(null)}
        batchId={batchId ? parseInt(batchId) : 0}
        onSuccess={loadBatchData}
      />
      <SampleForm
        isOpen={activeModal === 'sample'}
        onClose={() => setActiveModal(null)}
        batchId={batchId ? parseInt(batchId) : 0}
        onSuccess={loadBatchData}
      />
      <FailureForm
        isOpen={activeModal === 'failure'}
        onClose={() => setActiveModal(null)}
        batchId={batchId ? parseInt(batchId) : 0}
        onSuccess={loadBatchData}
      />
      <ClosureForm
        isOpen={activeModal === 'closure'}
        onClose={() => setActiveModal(null)}
        batchId={batchId ? parseInt(batchId) : 0}
        onSuccess={loadBatchData}
      />
    </div>
  );
};
