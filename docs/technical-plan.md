# Bioprocess Digital Twin – Starter Research Edition
**(*Pichia pastoris*, glycerol batch, biomass-only, edge-first, cloud-free)**

---

## **Executive Summary**
End-to-end technical plan to build a research-grade **digital shadow** for *Pichia pastoris* biomass grown in a **glycerol-based simple batch** mode.
**Target:** ≤ 8% MRE (stretch: ≤ 6%) on OD₆₀₀ prediction within **18 batches** executed over **20 weeks**, using only on-prem hardware. The system features a **Dockerised** edge stack designed for easy deployment in research labs and biotechnology start-ups.
**Phase-1 Scope:** This plan covers the initial biomass accumulation phase. Control write-back for pH, DO, and future methanol feed is wired but **disabled** until model confidence is proven.

---

## **1. Objectives & Success Metrics**
| Metric | Research Target |
|---|---|
| **Primary:** MRE (30s OD prediction) | ≤ 8 % (Stretch: ≤ 6%) |
| **Secondary:** Model Robustness | R² >0.90, RMSE <5% (DO) |
| Process Variability Baseline | CV measured in Phase A to validate feasibility |
| Real-time latency | < 1 s (inference) |
| Batches to first model | 18 |
| System uptime | > 95 % (edge) |
| Drift trigger | MRE > 10 % **or** KL-div > 0.1 **or** operator flag |

---

## **2. Scope Boundary**
- **Organism**: *Pichia pastoris* (e.g., X-33, KM71H).
- **Process**: Simple batch on buffered glycerol medium (e.g., BMGY).
- **Hardware**: One vessel, expandable to two on the same Jetson.
- **Labels**: OD₆₀₀ (on-line), μ (derived), DCW (next-day manual).
- **Control Outputs**: Stirrer, Gas MFC, Heater PID, Base Pump (pH) → **MQTT wired, software-disabled**.
- **Retention**: Forever (InfluxDB + MinIO).
- **Compliance**: Research only. 21 CFR Part 11 not required in this phase.

---

## **3. Technical Architecture**

### **3.1 High-level Flow**
```
Sensors 1 Hz ──MQTT──► Telegraf ──► InfluxDB raw
                                    │
                                    ├─30-s Flux task──► InfluxDB agg
                                    │
                                    ▼
Jetson (Docker)  digital-twin service
 reads 30-s windows
 writes predictions back to Influx & MQTT
```

### **3.2 Hardware**
- **Edge**: NVIDIA Jetson AGX Orin 64 GB
- **Training Workstation**: On-prem GPU machine (RTX 4080 or better)
- **Network**: 1 Gbps switch, dedicated VLAN for process equipment
- **Off-Gas Analyzer**: Custom configuration (Phase 1)
  - **Primary**: Individual CO₂ sensor (0-5% v/v) + O₂ sensor (19-21% v/v)
  - Connection: Analog output (4-20mA or 0-10V) to data acquisition system
  - Calibration: Weekly 2-point (N₂ for 0% O₂, air for 20.9% O₂ and 0% CO₂)
  - **Fallback**: If custom sensor reliability issues arise (drift >0.2% between calibrations, RSD >5%), upgrade to integrated analyzer (e.g., BlueSens BlueInOne FERM, Servomex MiniMP5) - budget contingency required
  - **Note**: Gasset et al. (2024) used BlueSens analyzer with humidity correction and silica column for moisture removal - may be required if custom sensors show humidity interference

### **3.3 Software Stack (locked versions)**
| Component | Version / Image |
|---|---|
| JetPack | 5.1.2 |
| Docker | 24.0.5 (nvidia-docker runtime) |
| MQTT | eclipse-mosquitto:2.0.18 |
| InfluxDB | influxdb:2.7-arm64 |
| Telegraf | telegraf:1.28-arm64 |
| Python base | nvcr.io/nvidia/l4t-pytorch:r35.1.0-pth2.0-py3 |
| Core libs | pandas 1.5.3, numpy 1.24.3, scikit-learn 1.3.0, LightGBM 4.0.0, tsfresh 0.20.1 |
| API | FastAPI 0.103.0, uvicorn 0.23.2 |
| Monitoring | Prometheus client 0.17.1, Grafana 10.1-arm64 |

---

## **4. Data Infrastructure**

### **4.1 Sensor List (1 Hz unless noted)**
| Tag | Unit | Range | Notes |
|---|---|---|---|
| pH | — | 3.0 – 8.0 | Immersed probe with temperature compensation |
| DO | % sat | 0 – 100 | Immersed probe with temperature compensation |
| OD | AU @ 600 nm | 0 – 50+ (probe dependent) | In-situ optical density probe |
| Gas_MFC_air | L min⁻¹ | 0 – 2 | Mass flow controller (air inlet) |
| Stir_SP | RPM | 200 – 1000 | Stirrer speed setpoint |
| **Reactor_Pressure** | bar (or kPa) | 0.9 – 1.5 | **NEW**: Headspace pressure transducer |
| Temp_Broth | °C | 25 – 35 | Primary temperature (immersed RTD) |
| **Temp_pH_Probe** | °C | 25 – 35 | **NEW**: Integrated pH probe temperature sensor |
| **Temp_DO_Probe** | °C | 25 – 35 | **NEW**: Integrated DO probe temperature sensor |
| **Temp_Stirrer_Motor** | °C | 20 – 80 | **NEW**: Motor housing temperature (thermal monitoring) |
| **Temp_Exhaust** | °C | 25 – 40 | **NEW**: Off-gas line temperature (for gas density correction) |
| Base_Pump_Rate | mL min⁻¹ | 0 – 10 (0 in phase 1) | pH control pump |
| Weight | kg | 0 – 10 (10 s cadence) | Vessel mass (for evaporation tracking) |
| Heater_PID_out | % | 0 – 100 | Heating/cooling control output |
| Stir_torque | % | 0 – 100 (from VFD) | Stirrer motor torque (rheology proxy) |
| **Off-Gas_CO2** | % v/v | 0 – 5 | **Custom**: Individual CO₂ sensor (NDIR or electrochemical) |
| **Off-Gas_O2** | % v/v | 19 – 21 | **Custom**: Individual O₂ sensor (paramagnetic or zirconia) |
| **Gas_Flow_Inlet** | L min⁻¹ | 0 – 2 | Mass flow controller (air) |
| **Gas_Flow_Outlet** | L min⁻¹ | 0 – 2.5 | Optional: thermal mass flow meter for mass balance closure |

### **4.2 MQTT Topics**
```
bioprocess/pichia/vessel1/sensors/<tag>
bioprocess/pichia/vessel1/sensors/temperature/broth
bioprocess/pichia/vessel1/sensors/temperature/ph_probe
bioprocess/pichia/vessel1/sensors/temperature/do_probe
bioprocess/pichia/vessel1/sensors/temperature/stirrer_motor
bioprocess/pichia/vessel1/sensors/temperature/exhaust
bioprocess/pichia/vessel1/sensors/pressure/headspace
bioprocess/pichia/vessel1/sensors/offgas/co2     # % CO₂ in exhaust (custom sensor)
bioprocess/pichia/vessel1/sensors/offgas/o2      # % O₂ in exhaust (custom sensor)
bioprocess/pichia/vessel1/sensors/offgas/flow_in
bioprocess/pichia/vessel1/sensors/offgas/flow_out
bioprocess/pichia/vessel1/control/<actuator>     # (write-back disabled)
bioprocess/pichia/vessel1/telemetry/prediction
bioprocess/pichia/vessel1/telemetry/cer          # Calculated CER (mol/L/h)
bioprocess/pichia/vessel1/telemetry/our          # Calculated OUR (mol/L/h)
bioprocess/pichia/vessel1/telemetry/rq           # Calculated RQ (CER/OUR)
bioprocess/pichia/vessel1/telemetry/kla          # Estimated kLa from DO dynamics
bioprocess/pichia/vessel1/alarms/+
bioprocess/pichia/vessel1/alarms/offgas_sensor_drift   # Alert if calibration drift detected
bioprocess/pichia/vessel1/manual_events/<form_id>
```

### **4.3 Data Stores**
- **InfluxDB Buckets**: `pichia_raw`, `pichia_30s`, `pichia_pred`.
- **MinIO Bucket**: `pichia-lake` (`s3://pichia-lake/<batch_id>/...`).
- **Postgres Database**: `pichia_manual_data` (batch records and manual observations).

---

### **4.4 Manual Data Schema (Postgres)**

**Design Philosophy:** Batch-centric electronic lab notebook. All manual data is organized hierarchically under a parent `batch` record, enabling complete traceability and workflow-oriented data entry.

#### **Core Table: `batches`**
```sql
CREATE TABLE batches (
    batch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_number INTEGER NOT NULL,  -- 1-18
    phase CHAR(1) NOT NULL CHECK (phase IN ('A', 'B', 'C')),
    vessel_id VARCHAR(50) NOT NULL,
    operator_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('setup', 'running', 'complete', 'aborted')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    inoculated_at TIMESTAMPTZ,  -- T=0, set when inoculation record added
    completed_at TIMESTAMPTZ,
    notes TEXT,
    UNIQUE(batch_number)
);
```

#### **Child Tables (Foreign Key: `batch_id`)**

**1. Media Preparations** (`media_preparations`)
```sql
CREATE TABLE media_preparations (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES batches(batch_id) ON DELETE CASCADE,
    recipe_name VARCHAR(100) DEFAULT 'BMGY_Standard_4pc_Glycerol',
    phosphoric_acid_ml NUMERIC(5,2) DEFAULT 26.7,
    calcium_sulfate_g NUMERIC(5,2) DEFAULT 0.93,
    potassium_sulfate_g NUMERIC(5,2) DEFAULT 18.2,
    magnesium_sulfate_g NUMERIC(5,2) DEFAULT 14.9,
    potassium_hydroxide_g NUMERIC(5,2) DEFAULT 4.13,
    glycerol_g NUMERIC(5,2) DEFAULT 40.0,
    final_volume_l NUMERIC(4,2) DEFAULT 0.9,
    autoclave_cycle VARCHAR(50),
    sterility_verified BOOLEAN DEFAULT FALSE,
    prepared_by VARCHAR(50),
    prepared_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes TEXT
);
```

**2. Calibrations** (`calibrations`)
```sql
CREATE TABLE calibrations (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES batches(batch_id) ON DELETE CASCADE,
    probe_type VARCHAR(20) NOT NULL CHECK (probe_type IN ('pH', 'DO', 'Temp')),
    buffer_low_value NUMERIC(5,2),  -- e.g., pH 4.01
    buffer_high_value NUMERIC(5,2),  -- e.g., pH 7.00
    reading_low NUMERIC(5,2),
    reading_high NUMERIC(5,2),
    slope_percent NUMERIC(5,2),  -- For pH: must be ≥95%
    response_time_sec INTEGER,  -- For DO: must be <30s
    pass BOOLEAN NOT NULL,
    calibrated_by VARCHAR(50),
    calibrated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes TEXT
);
```

**3. Inoculations** (`inoculations`)
```sql
CREATE TABLE inoculations (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES batches(batch_id) ON DELETE CASCADE,
    cryo_vial_id VARCHAR(100) NOT NULL,
    inoculum_od600 NUMERIC(5,2) NOT NULL CHECK (inoculum_od600 BETWEEN 2.0 AND 10.0),
    inoculum_volume_ml NUMERIC(6,2) DEFAULT 100,
    dilution_factor NUMERIC(5,2) DEFAULT 1.0,
    microscopy_observations TEXT,
    go_decision BOOLEAN NOT NULL,  -- GO/NO-GO quality gate
    inoculated_by VARCHAR(50),
    inoculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(batch_id)  -- Only one inoculation per batch
);
```

**4. Samples** (`samples`)
```sql
CREATE TABLE samples (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES batches(batch_id) ON DELETE CASCADE,
    timepoint_hours NUMERIC(5,2) NOT NULL,  -- Hours post-inoculation
    sample_volume_ml NUMERIC(5,2) DEFAULT 10,
    od600_raw NUMERIC(8,4) NOT NULL,
    od600_dilution_factor NUMERIC(5,2) DEFAULT 1.0,
    od600_calculated NUMERIC(8,4) NOT NULL,  -- od600_raw × dilution_factor
    dcw_filter_id VARCHAR(100),
    dcw_sample_volume_ml NUMERIC(5,2),
    dcw_filter_wet_weight_g NUMERIC(8,4),
    dcw_filter_dry_weight_g NUMERIC(8,4),
    dcw_g_per_l NUMERIC(8,4),  -- Calculated from weights
    contamination_detected BOOLEAN DEFAULT FALSE,
    microscopy_observations TEXT,
    supernatant_cryovial_id VARCHAR(100),
    pellet_cryovial_id VARCHAR(100),
    sampled_by VARCHAR(50),
    sampled_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**5. Process Changes** (`process_changes`)
```sql
CREATE TABLE process_changes (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES batches(batch_id) ON DELETE CASCADE,
    timepoint_hours NUMERIC(5,2) NOT NULL,
    parameter VARCHAR(50) NOT NULL,  -- e.g., 'Agitation', 'Temperature'
    old_value NUMERIC(8,2),
    new_value NUMERIC(8,2),
    reason TEXT NOT NULL,
    supervisor_approval_id VARCHAR(50),
    changed_by VARCHAR(50),
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**6. Failures & Deviations** (`failures`)
```sql
CREATE TABLE failures (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES batches(batch_id) ON DELETE CASCADE,
    deviation_level INTEGER NOT NULL CHECK (deviation_level IN (1, 2, 3)),
    deviation_start_time TIMESTAMPTZ NOT NULL,
    deviation_end_time TIMESTAMPTZ,
    category VARCHAR(50) NOT NULL,  -- 'Contamination', 'DO_Crash', 'Sensor_Failure', etc.
    description TEXT NOT NULL,
    root_cause TEXT,
    corrective_action TEXT,
    impact_assessment TEXT,
    reported_by VARCHAR(50),
    reviewed_by VARCHAR(50),  -- ML Engineer for Level 2
    reported_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**7. Batch Closures** (`batch_closures`)
```sql
CREATE TABLE batch_closures (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES batches(batch_id) ON DELETE CASCADE,
    final_od600 NUMERIC(8,4),
    total_runtime_hours NUMERIC(6,2),
    glycerol_depletion_time_hours NUMERIC(6,2),
    do_spike_observed BOOLEAN,
    max_do_percent NUMERIC(5,2),
    cumulative_base_addition_ml NUMERIC(6,2),
    outcome VARCHAR(50) NOT NULL,  -- 'Complete', 'Aborted_Contamination', etc.
    harvest_method VARCHAR(50),  -- 'Cell_Banking', 'Disposal'
    closed_by VARCHAR(50),
    approved_by VARCHAR(50),  -- Process Engineer sign-off
    closed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(batch_id)  -- Only one closure per batch
);
```

---

### **4.5 API Endpoints (FastAPI)**

**Batch Management:**
- `POST /api/batches` - Create new batch record (returns `batch_id`)
- `GET /api/batches/{batch_id}` - Retrieve complete batch notebook (all child records)
- `GET /api/batches?status=running` - List batches by status
- `PATCH /api/batches/{batch_id}` - Update batch status or metadata

**Data Entry (Child Records):**
- `POST /api/batches/{batch_id}/media` - Add media preparation record
- `POST /api/batches/{batch_id}/calibrations` - Add calibration record
- `POST /api/batches/{batch_id}/inoculation` - Add inoculation record (sets `batches.inoculated_at`)
- `POST /api/batches/{batch_id}/samples` - Add sample observation
- `POST /api/batches/{batch_id}/process-changes` - Log process change
- `POST /api/batches/{batch_id}/failures` - Log deviation/failure
- `POST /api/batches/{batch_id}/close` - Add batch closure record (sets `batches.status='complete'`)

**Validation Rules (enforced at API layer):**
- Cannot add `inoculation` if calibrations not passing (`calibrations.pass = TRUE`)
- Cannot add `samples` until `inoculation` record exists
- Cannot `close` batch without at least 8 sample records
- `timepoint_hours` in samples must be relative to `batches.inoculated_at`

**Response Format:**
```json
{
  "status": "success",
  "batch_id": "uuid-here",
  "record_id": 123,
  "message": "Sample added to Batch 5 at T=2.0h"
}
```

---

## **5. Data Pipeline**

### **5.1 Cleaning & Validation (on edge, real-time)**
| Check | Action |
|---|---|
| Missing < 5 min | Linear interpolation |
| Missing 5 – 30 min | Kalman filter |
| Z-score > 3σ | Clip to physical bound |
| Physical impossible (pH < 2) | NaN + alarm |

### **5.2 Feature Engineering (30 s window)**
- **Basic**: mean, std, slope for every sensor tag.
- **Derived Rates (Off-Gas Balance with Pressure Correction)**:
    - **CER** (Carbon Evolution Rate, mol CO₂/L/h) = (F_in × y_CO2_out × P_reactor / P_std) / V_reactor
      - F_in = inlet gas flow (L/h at standard conditions)
      - y_CO2_out = mole fraction CO₂ in exhaust (from % / 100)
      - P_reactor = measured headspace pressure (bar)
      - P_std = 1.013 bar (standard pressure correction)
      - V_reactor = working volume (L)
    - **OUR** (Oxygen Uptake Rate, mol O₂/L/h) = (F_in × y_O2_in - F_out × y_O2_out) × (P_reactor / P_std) / V_reactor
      - y_O2_in = 0.21 (air composition)
      - y_O2_out = measured O₂ mole fraction in exhaust
      - **Note**: Pressure correction important if headspace pressure varies (e.g., due to foam, backpressure valve, high gas flow)
    - **RQ** (Respiratory Quotient, dimensionless) = CER / OUR
    - **μ** (Specific Growth Rate, h⁻¹) = d(ln OD)/dt (Savitzky-Golay 5-pt derivative)
    - **qO₂** (Specific Oxygen Uptake Rate, mol O₂/gDCW/h) = OUR / DCW_estimated
    - **qCO₂** (Specific CO₂ Production Rate, mol CO₂/gDCW/h) = CER / DCW_estimated
    - **kLa** (Volumetric Mass Transfer Coefficient, h⁻¹) = OUR / (C*_O2 - C_O2)
      - Estimated from dynamic DO response and oxygen uptake
      - C*_O2 = saturation oxygen concentration (pressure-corrected)
      - C_O2 = measured dissolved oxygen
- **Thermal Features**:
    - **Temperature gradients**: ΔT = Temp_Broth - Temp_Exhaust (indicates metabolic heat generation)
    - **Sensor agreement**: Temp_Broth vs. Temp_pH_Probe vs. Temp_DO_Probe (quality check for immersed sensors)
    - **Motor thermal state**: Temp_Stirrer_Motor (early warning for mechanical issues, correlates with viscosity changes)
- **Pressure Features**:
    - **Pressure deviation**: Reactor_Pressure - P_atmospheric (indicates foam accumulation, filter blockage, or gas flow imbalance)
    - **Pressure-compensated gas velocities**: Corrects gas flow measurements to actual reactor conditions
- **Process State**:
    - **Phase Flag**: lag (μ < 0.08 h⁻¹), exp (μ ≥ 0.08), stationary (μ < 0.02 after exp).
    - **Cumulative Sums**: ∫OD, ∫temp-deviation, ∫torque, ∫CER (total CO₂ produced), ∫OUR (total O₂ consumed).
- **Notes**:
  - **Reactor pressure** enables accurate gas balance closure and compensates for non-atmospheric conditions
  - **Multiple temperature sensors** provide redundancy and detect spatial gradients (poor mixing indicator)
  - Off-gas measurements (CER, OUR, RQ) provide **direct insight into cellular metabolism** independent of optical density
  - Based on Gasset et al. (2024): RQ-based physiological control achieved MRE <4% for P. pastoris fed-batch
  - **Custom sensor reliability monitoring**: Auto-flag batches where off-gas sensor drift >0.2% between calibrations; trigger upgrade to integrated analyzer if failure rate >20%

---

## **6. Model Development**

### **6.1 Candidate Pool**
LightGBM (baseline), XGBoost (accuracy), LSTM (long-range dynamics).

### **6.2 Champion (phase-1)**
**LightGBM Regressor**
- Hyperparameters: 500 trees, max_depth = 8, lr = 0.05, feature_fraction = 0.8.
- Training: 5-fold TimeSeriesSplit (gap = 1 batch), early stopping on RMSE.
- Tuning: Optuna (100 trials) on GPU workstation.

### **6.3 Training Workflow (nightly cron)**
1.  Export last 24h of completed batches to Parquet from InfluxDB.
2.  Join with DCW labels from Postgres (`samples` table: `od600_calculated`, `dcw_g_per_l`).
3.  Run Optuna tuning job on workstation.
4.  Evaluate best model on hold-out set (last 3 batches).
5.  If MRE improvement > 0.1% and MRE ≤ 8%, push model artefact (`.lgb`) and checksum to MinIO.
6.  Jetson pulls latest validated model on service restart.

### **6.4 Validation Report (auto-generated notebook)**
- MRE, RMSE, MAPE per batch.
- SHAP summary plot (top 15 features).
- Residual plots vs. time and process phase.
- KL-divergence check on feature distributions vs. training set.

---

## **7. Edge Deployment & CI/CD**

### **7.1 Container Layout**
Multi-stage Dockerfile building from `l4t-pytorch` base, creating a slim final image with a non-root user. Code structured into `app/`, `models/`, and `config/`.

### **7.2 CI/CD (GitHub Actions)**
- On PR to `main`: Run `pytest` unit tests and linter.
- On merge to `main`: Build `arm64` image, push to local container registry.
- Webhook triggers `docker-compose pull && docker-compose up -d` on Jetson.

---

## **8. Risk Register (Technical)**
| Risk | Mitigation |
|---|---|
| Sensor drifts (esp. pH) | Weekly 2-point calibration log; blacklist batch if pre/post cal offset > 0.2 pH. |
| Jetson SSD failure | Nightly `rsync` of critical data volumes (InfluxDB, Postgres, models) to workstation. |
| Model divergence | Auto-revert to previous model artefact if new model MRE exceeds threshold on live data. |
| Biological variation | Increase batch count for training (from 18 to 25); ensure consistent inoculum protocol. |
| Power outage | UPS for Jetson and network switch (30 min), enabling graceful shutdown script. |

---
