// API Response Types
export interface User {
  user_id: string;
  username: string;
  full_name: string;
  role: 'admin' | 'engineer' | 'technician' | 'viewer';
  active: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Batch {
  batch_id: number;
  batch_number: number;
  phase: 'A' | 'B' | 'C';
  vessel_id: string;
  status: 'pending' | 'running' | 'complete' | 'failed';
  created_at: string;
  inoculated_at: string | null;
  closed_at: string | null;
  operator_id: string;
  notes: string | null;
  // Computed fields (optional, may not always be provided)
  current_timepoint_hours?: number | null;
  total_samples_count?: number;
  calibrations_count?: number;
  critical_failures_count?: number;
}

export interface BatchCreate {
  batch_number: number;
  phase: 'A' | 'B' | 'C';
  vessel_id: string;
  operator_id: string;
  notes?: string;
}

export interface Calibration {
  calibration_id: number;
  batch_id: number;
  probe_type: 'pH' | 'DO' | 'Temp';
  buffer_low_value: number;
  buffer_high_value: number;
  reading_low: number;
  reading_high: number;
  pass: boolean;
  calibrated_by: string;
  calibrated_at: string;
  notes: string | null;
  // Computed field for pH
  slope_percent: number | null;
}

export interface CalibrationCreate {
  probe_type: 'pH' | 'DO' | 'Temp';
  buffer_low_value: number;
  buffer_high_value: number;
  reading_low: number;
  reading_high: number;
  pass_: boolean; // Note: API uses pass_ to avoid Python keyword
  calibrated_by: string;
  notes?: string;
}

export interface Inoculation {
  inoculation_id: number;
  batch_id: number;
  cryo_vial_id: string;
  inoculum_od600: number;
  microscopy_observations: string;
  go_decision: boolean;
  inoculated_by: string;
  inoculated_at: string;
}

export interface InoculationCreate {
  cryo_vial_id: string;
  inoculum_od600: number;
  microscopy_observations: string;
  go_decision: boolean;
  inoculated_by: string;
}

export interface Sample {
  sample_id: number;
  batch_id: number;
  sampled_at: string;
  timepoint_hours: number;
  od600_raw: number;
  od600_dilution_factor: number;
  od600_corrected: number;
  dcw_g_l: number | null;
  contamination_detected: boolean;
  microscopy_notes: string | null;
  sampled_by: string;
}

export interface SampleCreate {
  od600_raw: number;
  od600_dilution_factor: number;
  dcw_g_l?: number;
  contamination_detected: boolean;
  microscopy_notes?: string;
  sampled_by: string;
}

export interface Failure {
  failure_id: number;
  batch_id: number;
  reported_at: string;
  severity: 1 | 2 | 3;
  description: string;
  root_cause: string | null;
  corrective_action: string | null;
  reported_by: string;
  reviewed: boolean;
  reviewed_by: string | null;
  reviewed_at: string | null;
}

export interface FailureCreate {
  severity: 1 | 2 | 3;
  description: string;
  root_cause?: string;
  corrective_action?: string;
  reported_by: string;
}

export interface BatchClosure {
  closure_id: number;
  batch_id: number;
  closed_at: string;
  final_od600: number;
  total_runtime_hours: number;
  glycerol_depletion_time_hours: number | null;
  outcome: 'Complete' | 'Partial' | 'Failed';
  closed_by: string;
  approved_by: string;
}

export interface BatchClosureCreate {
  final_od600: number;
  total_runtime_hours: number;
  glycerol_depletion_time_hours?: number;
  outcome: 'Complete' | 'Partial' | 'Failed';
  closed_by: string;
  approved_by: string;
}

// API Error Response
export interface APIError {
  detail: string;
}
