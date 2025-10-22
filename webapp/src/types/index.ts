// API Response Types
export interface User {
  user_id: number | string;
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
  batch_id: string; // UUID
  batch_number: number;
  phase: 'A' | 'B' | 'C';
  vessel_id: string;
  status: 'pending' | 'running' | 'complete' | 'failed' | 'aborted';
  created_at: string;
  created_by?: string;
  inoculated_at: string | null;
  completed_at: string | null;
  operator_id: string;
  notes: string | null;
  // Computed fields (optional, may not always be provided)
  current_timepoint_hours?: number | null;
  total_samples_count?: number;
  calibrations_count?: number;
  critical_failures_count?: number;
  runtime_hours?: number | null;
}

export interface BatchCreate {
  batch_number: number;
  phase: 'A' | 'B' | 'C';
  vessel_id: string;
  operator_id: string;
  notes?: string;
}

export interface Calibration {
  id: number;
  batch_id: string; // UUID
  probe_type: 'pH' | 'DO' | 'Temp';
  buffer_low_value: number | string;
  buffer_high_value: number | string;
  reading_low: number | string;
  reading_high: number | string;
  pass: boolean;
  calibrated_by: string;
  calibrated_at: string;
  notes: string | null;
  // Computed field for pH - can be string or number from API
  slope_percent: number | string | null;
}

export interface CalibrationCreate {
  probe_type: 'pH' | 'DO' | 'Temp' | 'OffGas_O2' | 'OffGas_CO2' | 'Pressure';
  buffer_low_value?: number; // Optional - not all probes use buffers
  buffer_low_lot?: string;
  buffer_high_value?: number; // Optional - not all probes use buffers
  buffer_high_lot?: string;
  reading_low?: number; // Optional
  reading_high?: number; // Optional
  response_time_sec?: number; // DO probe only, must be <30s
  pass_: boolean; // Note: API uses pass_ to avoid Python keyword
  control_active?: boolean;
  calibrated_by: string;
  notes?: string;
}

export interface Inoculation {
  id: number;
  batch_id: string; // UUID
  inoculum_source: string | null; // Flexible: cryo vial, plate, seed flask, etc.
  cryo_vial_id?: string; // Optional cryo vial ID
  inoculum_od600: number | string;
  microscopy_observations: string | null;
  go_decision: boolean;
  inoculated_by: string;
  inoculated_at: string;
}

export interface InoculationCreate {
  inoculum_source?: string; // Optional - can describe any inoculum source
  cryo_vial_id?: string; // Optional cryo vial ID
  inoculum_od600: number;
  dilution_factor?: number;
  inoculum_volume_ml?: number;
  microscopy_observations?: string;
  go_decision: boolean;
  inoculated_by: string;
}

export interface MediaPreparation {
  id: number;
  batch_id: string; // UUID
  recipe_name: string;
  phosphoric_acid_ml: number;
  phosphoric_acid_lot?: string;
  calcium_sulfate_g: number;
  calcium_sulfate_lot?: string;
  potassium_sulfate_g: number;
  potassium_sulfate_lot?: string;
  magnesium_sulfate_g: number;
  magnesium_sulfate_lot?: string;
  potassium_hydroxide_g: number;
  potassium_hydroxide_lot?: string;
  glycerol_g: number;
  glycerol_lot?: string;
  final_volume_l: number;
  autoclave_cycle: string;
  sterility_verified: boolean;
  prepared_at: string;
  prepared_by: string;
  notes?: string;
}

export interface MediaPreparationCreate {
  recipe_name: string;
  phosphoric_acid_ml: number;
  phosphoric_acid_lot?: string;
  calcium_sulfate_g: number;
  calcium_sulfate_lot?: string;
  potassium_sulfate_g: number;
  potassium_sulfate_lot?: string;
  magnesium_sulfate_g: number;
  magnesium_sulfate_lot?: string;
  potassium_hydroxide_g: number;
  potassium_hydroxide_lot?: string;
  glycerol_g: number;
  glycerol_lot?: string;
  final_volume_l: number;
  autoclave_cycle: string;
  sterility_verified: boolean;
  prepared_by: string;
  notes?: string;
}

export interface Sample {
  id: number;
  batch_id: string; // UUID
  sampled_at: string;
  timepoint_hours: number | string;
  od600_raw: number | string;
  od600_dilution_factor: number | string;
  od600_calculated: number | string;
  dcw_g_per_l: number | string | null;
  contamination_detected: boolean;
  microscopy_observations: string | null;
  sampled_by: string;
}

export interface SampleCreate {
  sample_volume_ml?: number;
  od600_raw: number;
  od600_dilution_factor?: number;
  dcw_filter_id?: string;
  dcw_sample_volume_ml?: number;
  dcw_filter_wet_weight_g?: number;
  dcw_filter_dry_weight_g?: number;
  contamination_detected: boolean;
  microscopy_observations?: string;
  supernatant_cryovial_id?: string;
  pellet_cryovial_id?: string;
  sampled_by: string;
}

export interface Failure {
  id: number;
  batch_id: string; // UUID
  reported_at: string;
  deviation_level: 1 | 2 | 3;
  description: string;
  root_cause: string | null;
  corrective_action: string | null;
  reported_by: string;
  reviewed: boolean;
  reviewed_by: string | null;
  reviewed_at: string | null;
}

export interface FailureCreate {
  deviation_level: 1 | 2 | 3; // Fixed: was 'severity', now matches backend
  deviation_start_time: string; // ISO datetime
  deviation_end_time?: string; // ISO datetime, optional
  category: 'Contamination' | 'DO_Crash' | 'DO_Crash_No_Control' | 'pH_Excursion' |
           'pH_Drift_No_Control' | 'Temp_Excursion' | 'Sensor_Failure' | 'Power_Outage' |
           'Sampling_Missed' | 'O2_Enrichment_Used' | 'Other';
  description: string;
  root_cause?: string;
  corrective_action?: string;
  impact_assessment?: string;
  reported_by: string;
  reviewed_by?: string;
}

export interface BatchClosure {
  id: number;
  batch_id: string; // UUID
  closed_at: string;
  final_od600: number | string;
  total_runtime_hours: number | string;
  glycerol_depletion_time_hours: number | string | null;
  outcome: 'Complete' | 'Aborted_Contamination' | 'Aborted_Sensor_Failure' | 'Aborted_Other';
  closed_by: string;
  approved_by: string;
}

export interface BatchClosureCreate {
  final_od600: number;
  total_runtime_hours: number;
  glycerol_depletion_time_hours?: number;
  outcome: 'Complete' | 'Aborted_Contamination' | 'Aborted_Sensor_Failure' | 'Aborted_Other';
  closed_by: string;
  approved_by: string;
}

// API Error Response
export interface APIError {
  detail: string;
}
