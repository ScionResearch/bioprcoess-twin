import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import type { Batch } from '../types';
import { useAuth } from '../contexts/AuthContext';
import './BatchList.css';

export const BatchList: React.FC = () => {
  const [batches, setBatches] = useState<Batch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  useEffect(() => {
    loadBatches();
  }, []);

  const loadBatches = async () => {
    try {
      setLoading(true);
      const data = await api.batches.list();
      // Sort by most recent first
      setBatches(data.sort((a, b) => b.batch_id - a.batch_id));
    } catch (err) {
      setError('Failed to load batches');
      console.error('Error loading batches:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'pending':
        return 'status-badge status-pending';
      case 'running':
        return 'status-badge status-running';
      case 'complete':
        return 'status-badge status-complete';
      case 'failed':
        return 'status-badge status-failed';
      default:
        return 'status-badge';
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading">Loading batches...</div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>Batch Records</h1>
          <p className="user-info">Logged in as: {user?.full_name} ({user?.role})</p>
        </div>
        <div className="header-actions">
          <button
            className="btn btn-primary"
            onClick={() => navigate('/batches/new')}
          >
            + New Batch
          </button>
          <button
            className="btn btn-secondary"
            onClick={logout}
          >
            Logout
          </button>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          {error}
          <button onClick={loadBatches}>Retry</button>
        </div>
      )}

      {batches.length === 0 ? (
        <div className="empty-state">
          <h2>No batches yet</h2>
          <p>Create your first batch to get started</p>
          <button
            className="btn btn-primary"
            onClick={() => navigate('/batches/new')}
          >
            Create Batch
          </button>
        </div>
      ) : (
        <div className="batch-grid">
          {batches.map((batch) => (
            <div
              key={batch.batch_id}
              className="batch-card"
              onClick={() => navigate(`/batches/${batch.batch_id}`)}
            >
              <div className="batch-card-header">
                <div>
                  <h3>Batch {batch.batch_number}-{batch.phase}</h3>
                  <p className="vessel-id">{batch.vessel_id}</p>
                </div>
                <span className={getStatusBadgeClass(batch.status)}>
                  {batch.status}
                </span>
              </div>

              <div className="batch-card-body">
                <div className="batch-info-row">
                  <span className="label">Created:</span>
                  <span>{formatDate(batch.created_at)}</span>
                </div>

                {batch.inoculated_at && (
                  <div className="batch-info-row">
                    <span className="label">Inoculated:</span>
                    <span>{formatDate(batch.inoculated_at)}</span>
                  </div>
                )}

                {batch.current_timepoint_hours !== null && batch.current_timepoint_hours !== undefined && (
                  <div className="batch-info-row">
                    <span className="label">Timepoint:</span>
                    <span className="highlight">
                      {batch.current_timepoint_hours.toFixed(1)} hours
                    </span>
                  </div>
                )}

                <div className="batch-stats">
                  <div className="stat">
                    <span className="stat-value">{batch.total_samples_count ?? 0}</span>
                    <span className="stat-label">Samples</span>
                  </div>
                  <div className="stat">
                    <span className="stat-value">{batch.calibrations_count ?? 0}</span>
                    <span className="stat-label">Calibrations</span>
                  </div>
                  {(batch.critical_failures_count ?? 0) > 0 && (
                    <div className="stat stat-warning">
                      <span className="stat-value">{batch.critical_failures_count}</span>
                      <span className="stat-label">Failures</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
