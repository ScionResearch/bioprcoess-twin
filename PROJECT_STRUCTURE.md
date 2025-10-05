# Bioprocess Twin - Project Structure

**Repository Created:** 2025-10-05
**Location:** `bioprocess-twin/` (ready to copy to working location)

---

## Directory Tree

```
bioprocess-twin/
│
├── README.md                          ✅ Project overview, quick start
├── LICENSE                            ✅ MIT License
├── CHANGELOG.md                       ✅ Version history tracking
├── CONTRIBUTING.md                    ✅ Contribution guidelines
├── .gitignore                         ✅ Python/Node/Docker/Data exclusions
├── PROJECT_STRUCTURE.md               ✅ This file
│
├── docs/                              ✅ 📖 Planning & reference docs
│   ├── README.md                      ✅ Documentation hierarchy guide
│   ├── project-plan.md                ✅ Project objectives, timeline, scope (SSoT: PM)
│   ├── batch-run-plan.md              ✅ Experimental procedures, parameters (SSoT: Process)
│   ├── technical-plan.md              ✅ Software, hardware, data pipeline (SSoT: Technical)
│   ├── manual-data-development.md     ✅ Tablet forms, data entry workflows
│   ├── architecture/                  📁 System diagrams
│   │   ├── system-architecture.png    📁 High-level system overview
│   │   ├── data-flow.png              📁 Sensor → Model → DB flow
│   │   └── mqtt-topic-structure.md    📁 MQTT topic hierarchy documentation
│   ├── sops/                          📁 Standard Operating Procedures
│   │   ├── batch-execution-sop.md     📁 Step-by-step batch execution guide
│   │   ├── sensor-calibration-sop.md  📁 pH/DO/Temp calibration procedures
│   │   └── tablet-form-guide.md       📁 Manual data entry instructions
│   └── references/                    ✅ Research references
│       ├── alignment-analysis-gasset2024.md ✅ Gasset et al. 2024 analysis
│       ├── gasset-et-al-2024.pdf      📁 Original research paper
│       └── invitrogen-pichia-guidelines.pdf 📁 Pichia culture guidelines
│
├── edge/                              ✅ 🖧 Edge deployment (Jetson stack)
│   ├── docker-compose.yml             ✅ 8-service orchestration (see Section 3)
│   ├── .env.example                   ✅ Environment variable template
│   ├── services/
│   │   ├── digital-twin/              📁 Inference service
│   │   │   ├── Dockerfile             📁 nvidia-docker ARM64 image
│   │   │   ├── requirements.txt       📁 LightGBM, tsfresh, pandas
│   │   │   ├── app/
│   │   │   │   ├── main.py            📁 FastAPI service entry
│   │   │   │   ├── inference.py       📁 30s prediction loop
│   │   │   │   └── feature_engineering.py 📁 Rolling aggregations
│   │   │   └── models/                📁 Pulled from MinIO (gitignored)
│   │   ├── telegraf/                  📁 Data ingestion
│   │   │   └── telegraf.conf          📁 MQTT → InfluxDB ingestion config
│   │   ├── influxdb/                  📁 Time-series DB
│   │   │   └── init-scripts/
│   │   │       └── 01-create-buckets.sh 📁 Create pichia_raw, pichia_30s, pichia_pred
│   │   ├── mosquitto/                 📁 MQTT broker
│   │   │   └── mosquitto.conf         📁 Anonymous auth, port 1883
│   │   └── grafana/                   📁 Dashboards
│   │       └── provisioning/
│   │           ├── dashboards/
│   │           │   └── pichia-dashboard.json 📁 Real-time batch monitoring
│   │           └── datasources/
│   │               └── influxdb.yml   📁 InfluxDB v2 datasource
│   └── scripts/                       📁 Operations scripts
│       ├── backup.sh                  📁 InfluxDB + Postgres backup automation
│       └── deploy.sh                  📁 Docker stack deployment script
│
├── workstation/                       📁 💻 Training workstation
│   ├── notebooks/                     📁 Jupyter notebooks
│   │   ├── 01-data-exploration.ipynb  📁 Initial data quality assessment
│   │   ├── 02-feature-engineering.ipynb 📁 Rolling stats, lag features
│   │   ├── 03-model-training.ipynb    📁 LightGBM hyperparameter tuning
│   │   ├── 04-model-validation.ipynb  📁 Hold-out batch validation (16-18)
│   │   └── 05-shap-analysis.ipynb     📁 Feature importance analysis
│   ├── training/                      📁 Python training scripts
│   │   ├── train_lightgbm.py          📁 Automated training pipeline
│   │   ├── hyperparameter_tuning.py   📁 Optuna-based tuning
│   │   └── validation_report.py       📁 MRE, R², RMSE reporting
│   ├── data-pipeline/                 📁 ETL scripts
│   │   ├── export_influx_to_parquet.py 📁 InfluxDB → Parquet export
│   │   ├── join_manual_data.py        📁 Merge Postgres manual data
│   │   └── feature_extraction.py      📁 tsfresh feature generation
│   └── requirements.txt               📁 Workstation Python dependencies
│
├── api/                               📁 ⚡ FastAPI backend (manual data)
│   ├── Dockerfile                     📁 Python 3.11 + FastAPI
│   ├── requirements.txt               📁 FastAPI, SQLAlchemy, Alembic
│   ├── alembic/                       📁 Database migrations
│   │   ├── env.py                     📁 Alembic environment
│   │   └── versions/                  📁 Migration version scripts
│   ├── app/
│   │   ├── main.py                    📁 FastAPI app entry
│   │   ├── models.py                  📁 SQLAlchemy ORM models (7 tables)
│   │   ├── schemas.py                 📁 Pydantic validation schemas
│   │   ├── crud.py                    📁 Database operations
│   │   └── routers/                   📁 API route modules
│   │       ├── batches.py             📁 Batch CRUD endpoints
│   │       ├── calibrations.py        📁 Probe calibration endpoints
│   │       ├── samples.py             📁 Sample/DCW endpoints
│   │       └── failures.py            📁 Deviation reporting endpoints
│   └── tests/                         📁 API tests
│       └── test_batch_api.py          📁 Batch lifecycle test suite
│
├── webapp/                            📁 📱 React tablet forms
│   ├── package.json                   📁 Node dependencies (React, TypeScript)
│   ├── Dockerfile                     📁 nginx-alpine for production
│   ├── public/
│   │   └── index.html                 📁 SPA entry point
│   └── src/
│       ├── App.tsx                    📁 Main React app
│       ├── components/                📁 Form components
│       │   ├── BatchForm.tsx          📁 Create/close batch form
│       │   ├── CalibrationForm.tsx    📁 pH/DO/Temp calibration entry
│       │   ├── SampleForm.tsx         📁 OD/DCW sample entry
│       │   └── QRScanner.tsx          📁 Barcode scanner for cryo vials
│       ├── api/
│       │   └── client.ts              📁 FastAPI client (axios)
│       └── schemas/
│           └── formSchemas.json       📁 JSON schema validation
│
├── database/                          ✅ 🗄️ Postgres schema
│   ├── README.md                      ✅ Schema documentation (batch-centric)
│   ├── init.sql                       ✅ Complete schema (1 parent + 7 child tables)
│   └── seed.sql                       📁 Test data for development
│
├── hardware/                          ✅ 🔧 Sensor integration
│   ├── sensor-drivers/                📁 MQTT publishers (Python)
│   │   ├── offgas_co2_mqtt.py         📁 CO₂ sensor → MQTT (4-20mA/0-10V input)
│   │   ├── offgas_o2_mqtt.py          📁 O₂ sensor → MQTT (paramagnetic/zirconia)
│   │   ├── pressure_mqtt.py           📁 Headspace pressure transducer
│   │   └── temperature_multiplex_mqtt.py 📁 5-channel temp readout (broth, probes, motor, exhaust)
│   ├── calibration-tools/             📁 Drift detection
│   │   └── sensor_cal_validator.py    📁 Weekly 2-point cal validation
│   └── datasheets/                    📁 Sensor documentation
│       └── README.md                  📁 Datasheet index
│
├── models/                            ✅ 🤖 Model artifacts
│   ├── README.md                      ✅ Model versioning strategy (Git LFS < 100MB, MinIO otherwise)
│   ├── lightgbm-v1.0/                 📁 First production model
│   │   ├── model.lgb                  📁 LightGBM binary
│   │   ├── metadata.json              📁 Training params, performance metrics
│   │   └── shap_values.pkl            📁 SHAP explainability artifacts
│   └── .gitignore                     📁 Exclude model binaries from Git
│
├── data/                              ✅ 📊 Local data (gitignored)
│   ├── raw/                           📁 Batch Parquet exports from InfluxDB
│   ├── processed/                     📁 Feature-engineered training datasets
│   └── .gitkeep                       📁 Preserve directory structure
│
├── scripts/                           📁 🛠️ Utility scripts
│   ├── setup/                         📁 System installation
│   │   ├── install_jetson.sh          📁 JetPack, Docker, nvidia-runtime setup
│   │   └── configure_network.sh       📁 VLAN, static IP configuration
│   ├── batch-management/              📁 CLI tools
│   │   ├── create_batch.py            📁 Initialize new batch in Postgres
│   │   └── close_batch.py             📁 Finalize batch, generate summary
│   └── monitoring/                    📁 Health checks
│       └── check_sensor_drift.py      📁 Automated calibration drift alerts
│
├── tests/                             📁 ✅ Integration tests
│   ├── test_end_to_end.py             📁 MQTT → Influx → Model → API test
│   ├── test_mqtt_pipeline.py          📁 Sensor data ingestion validation
│   └── test_feature_engineering.py    📁 Feature calculation unit tests
│
└── .github/                           📁 🚀 CI/CD workflows
    └── workflows/
        ├── ci.yml                     📁 Lint, test, build
        ├── build-edge.yml             📁 ARM64 Docker image builds
        └── deploy.yml                 📁 Automated Jetson deployment
```

**Legend:**
- ✅ = File/directory created with content
- 📁 = Directory created (empty, ready for development)

---

## 🔑 Key Design Decisions

### 1. Monorepo vs Multi-Repo
**Decision:** Monorepo
- ✅ Easier version coordination across stack (edge + workstation + API)
- ✅ Single CI/CD pipeline
- ✅ Atomic commits for full stack changes
- ❌ Repo grows larger (mitigated by `.gitignore` for data/models)

### 2. Documentation Strategy
- All `.md` docs live in `docs/` as **SSoT** (single source of truth)
- Documents versioned alongside code
- Three-tier hierarchy: Project Plan (PM) → Technical Plan (Technical) → Batch Run Plan (Process)

### 3. Hardware Integration Philosophy
- **Custom sensor drivers** in `hardware/sensor-drivers/` publish to MQTT independently
- Each sensor = separate Python process for isolation
- **Swappable design**: Easy upgrade path to integrated analyzers in Phase 2


### 4. Model Versioning
- Models stored under `models/` with semantic versioning subfolders (e.g., `lightgbm-v1.0/`)
- **Storage strategy:**
  - Git LFS for models <100MB
  - MinIO object storage for larger models
  - Edge pulls from MinIO at deployment time

### 5. Complete Sensor Suite
**Why ALL sensors are included in InfluxDB setup (not just off-gas and temp):**

The original document listing only off-gas and temp sensors was **incomplete**. Per Technical Plan Section 4.1, the full sensor suite includes:

**Core Process Sensors (1 Hz):**
- pH (immersed probe with temp compensation)
- DO (immersed probe with temp compensation)
- OD₆₀₀ (in-situ optical density probe) ← **Primary prediction target**
- Gas_MFC_air (mass flow controller)
- Stir_SP (stirrer speed setpoint)
- Stir_torque (motor torque from VFD) ← **Rheology proxy**
- Weight (vessel mass, 10s cadence) ← **Evaporation tracking**
- Heater_PID_out (heating/cooling control output)
- Base_Pump_Rate (pH control, 0 in Phase 1)

**Temperature Sensors (5 channels):**
- Temp_Broth (primary reactor temperature)
- Temp_pH_Probe (integrated probe sensor)
- Temp_DO_Probe (integrated probe sensor)
- Temp_Stirrer_Motor (thermal monitoring)
- Temp_Exhaust (for gas density correction)

**Off-Gas Sensors (Custom):**
- Off-Gas_CO₂ (0-5% v/v, NDIR or electrochemical)
- Off-Gas_O₂ (19-21% v/v, paramagnetic or zirconia)
- Gas_Flow_Inlet (L/min, mass flow controller)
- Gas_Flow_Outlet (L/min, optional thermal mass flow meter)

**Pressure:**
- Reactor_Pressure (0.9-1.5 bar, headspace transducer)

**Why the full suite matters:**
1. **Feature engineering requires all sensors** - LightGBM model uses rolling aggregations, lag features, and cross-correlations across ALL sensor channels
2. **Calculated telemetry depends on multiple inputs**:
   - CER/OUR calculation needs CO₂, O₂, flow rates, temp, pressure
   - kLa estimation needs DO dynamics + gas flows + agitation
   - RQ (CER/OUR ratio) is a critical metabolic indicator
3. **Phase 2 expansion** - Control write-back will need all actuator feedback signals
4. **Root cause analysis** - Failures correlate across multiple sensors (e.g., DO crash + stir torque spike = foaming)

The InfluxDB setup must ingest **all** sensor channels to support:
- Real-time Grafana dashboards showing complete process state
- Feature extraction for model training (tsfresh operates on full time-series matrix)
- Batch-to-batch comparison and process CV analysis
- Deviation detection and automated alerting

**Partial sensor ingestion would break the digital shadow's core functionality.**

---

## Technology Stack

### Edge Stack (Jetson AGX Orin)
- **MQTT Broker:** Eclipse Mosquitto 2.0.18
- **Time-Series DB:** InfluxDB 2.7 (ARM64)
- **Data Ingestion:** Telegraf 1.28 (ARM64)
- **Monitoring:** Grafana 10.1 (ARM64)
- **Inference Service:** Python 3.10 + LightGBM 4.0.0
- **Container Runtime:** Docker 24.0.5 (nvidia-docker)

### Backend Services
- **API Framework:** FastAPI 0.103.0 + Uvicorn 0.23.2
- **Database:** PostgreSQL 15 (batch-centric schema)
- **Migrations:** Alembic 1.12
- **ORM:** SQLAlchemy 2.0

### Frontend
- **Framework:** React 18 + TypeScript
- **Forms:** React Hook Form + Zod validation
- **API Client:** Axios
- **Production Server:** nginx-alpine

### Training Workstation
- **ML Framework:** LightGBM 4.0.0, scikit-learn 1.3.0
- **Feature Engineering:** tsfresh 0.20.1
- **Data Processing:** pandas 1.5.3, numpy 1.24.3
- **Hyperparameter Tuning:** Optuna
- **Explainability:** SHAP

### Hardware Integration
- **Sensor Communication:** Python MQTT clients (paho-mqtt)
- **Data Acquisition:** Custom drivers for analog sensors (4-20mA, 0-10V)
- **Off-Gas Analysis:** Custom CO₂/O₂ sensors (Phase 1), upgrade path to integrated analyzers

---

## Data Flow Architecture

```
Sensors (1 Hz) ──MQTT──► Mosquitto ──► Telegraf ──► InfluxDB
                                                        │
                                         ┌──────────────┼──────────────┐
                                         │              │              │
                                    pichia_raw    pichia_30s    pichia_pred
                                         │              │              │
                                         ▼              ▼              ▼
                                    Grafana      Digital Twin    Workstation
                                  (Real-time)    (Inference)   (Training/Export)
                                                       │
                                                       ▼
                                              PostgreSQL ◄──── FastAPI ◄──── React Tablet
                                           (Manual Data)      (Backend)         (Forms)
```

### InfluxDB Buckets
1. **pichia_raw** - Raw 1 Hz sensor data (all channels)
2. **pichia_30s** - Aggregated 30s windows (mean, std, min, max per sensor)
3. **pichia_pred** - Model predictions (OD₆₀₀, μ, confidence intervals)

### PostgreSQL Tables (Manual Data)
1. **batches** - Parent table (batch metadata, status tracking)
2. **media_preparations** - Recipe, autoclave validation
3. **calibrations** - pH/DO/Temp probe calibrations
4. **inoculations** - Cryo vial ID, OD, GO/NO-GO decision
5. **samples** - OD₆₀₀, DCW measurements (next-day)
6. **process_changes** - Deviation tracking (agitation, temp changes)
7. **failures** - Contamination, sensor failures, root cause analysis
8. **batch_closures** - Final metrics, outcome, engineer sign-off

---

## Repository Statistics

- **Total directories:** 45
- **Core planning documents:** 4 (project-plan, batch-run-plan, technical-plan, manual-data-development)
- **Configuration files:** 4 (docker-compose, .env.example, .gitignore, init.sql)
- **Estimated LOC at v1.0:** ~15,000 (excluding dependencies)
- **Model artifacts:** Excluded from Git (use Git LFS or MinIO)
- **Data retention:** Forever (InfluxDB + MinIO), Postgres backup daily
