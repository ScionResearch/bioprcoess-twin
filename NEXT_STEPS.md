# Next Steps for Bioprocess Digital Twin Development

**Project Status:** Phase 1 - Digital Shadow Implementation
**Current Version:** v0.4.0
**Last Updated:** 2025-10-21

---

## ✅ Completed Components

### 1. Manual Data Collection System (v0.2.0 - v0.3.0)
- [x] PostgreSQL database schema with 9 tables
- [x] FastAPI backend with JWT auth and RBAC
- [x] React TypeScript frontend (tablet-optimized)
- [x] Complete batch workflow (calibration → inoculation → samples → closure)
- [x] Data export endpoints (CSV/Markdown/JSON)
- [x] Comprehensive testing (integration + unit tests)

### 2. Data Pipeline Service (v0.4.0)
- [x] Real-time data cleaning (interpolation, Kalman filter, outlier detection)
- [x] Feature engineering (60+ features: CER, OUR, RQ, μ, kLa, etc.)
- [x] InfluxDB integration with Telegraf and MQTT
- [x] FastAPI service with monitoring and alerting
- [x] 24 unit tests with 85% coverage

---

## 🚧 Critical Path Items (Phase 1 Completion)

### 3. Hardware Integration & ORC System Setup (Week 12-13)
**Reference:** `docs/technical-plan.md` Section 4.1

**IMPORTANT:** The Open Reactor Control System (ORC) handles ALL sensor reading and MQTT publishing. No separate sensor drivers needed in this project.

#### ORC System Architecture
- **Hardware:** RP2040 + SAMD51 dual microcontroller board (already built)
- **Sensors Handled by ORC:**
  - Temperature (broth, pH probe, DO probe, motor, exhaust)
  - pH (via Modbus or analog)
  - Dissolved Oxygen (DO)
  - Pressure (reactor headspace)
  - Gas flow (air, O₂ if enrichment)
  - Stirrer speed
  - Weight (if load cells installed)
  - Optical Density (OD, if inline sensor)
  - Power monitoring (voltage rails, PSU status)

- **MQTT Topics Published by ORC:**
  - `orcs/dev/<MAC>/sensors/temperature/0` (broth temp)
  - `orcs/dev/<MAC>/sensors/temperature/1` (pH probe temp)
  - `orcs/dev/<MAC>/sensors/ph/0`
  - `orcs/dev/<MAC>/sensors/do/0`
  - `orcs/dev/<MAC>/sensors/pressure/0`
  - `orcs/dev/<MAC>/sensors/gasflow/0`
  - `orcs/dev/<MAC>/sensors/stirrer/0`
  - And consolidated topic: `orcs/dev/<MAC>/sensors/all`

#### Integration Checklist

**1. ORC System Deployment:**
- [ ] Flash latest ORC firmware to RP2040 and SAMD51
- [ ] Configure ORC network settings (WiFi SSID, MQTT broker IP)
- [ ] Set MQTT broker to Jetson IP address (e.g., `10.10.37.118:1883`)
- [ ] Verify ORC publishes to MQTT (use `mosquitto_sub -h <jetson-ip> -t "orcs/dev/#" -v`)

**2. Jetson AGX Orin Setup:**
- [ ] Install Jetson on fermentation rig (ensure stable network connection)
- [ ] Deploy edge docker-compose stack: `cd edge && docker-compose up -d`
  - Services: mosquitto, influxdb, telegraf, data-pipeline, postgres, api, webapp
- [ ] Verify Mosquitto is running: `docker ps | grep mosquitto`
- [ ] Check MQTT broker accepts connections: `mosquitto_pub -h localhost -t test -m "hello"`

**3. Telegraf Configuration:**
- [ ] Update `edge/services/telegraf/telegraf.conf` to subscribe to ORC topics:
  ```toml
  [[inputs.mqtt_consumer]]
    servers = ["tcp://mosquitto:1883"]
    topics = ["orcs/dev/+/sensors/#"]
    data_format = "json"
    json_time_key = "timestamp"
    json_time_format = "2006-01-02T15:04:05Z"
  ```
- [ ] Map ORC sensor topics to InfluxDB tags/fields
- [ ] Verify data ingestion: query InfluxDB `raw_sensors` bucket

**4. Missing Sensors (If ORC Doesn't Have Them):**
- [ ] **CO₂ Sensor:** If ORC doesn't have CO₂, add external sensor with Python driver
  - Publish to `sensors/co2/ppm` (match ORC topic structure)
  - Use same JSON payload format: `{"timestamp": "...", "value": 450.2, "online": true}`
- [ ] **O₂ Sensor (Off-gas):** If not on ORC, add external sensor
  - Publish to `sensors/o2/percent`
  - Atmospheric calibration (20.9% reference)

**5. Sensor Validation:**
- [ ] All expected sensors appear in InfluxDB `raw_sensors` bucket
- [ ] Data publishing at expected rate (ORC default: configurable via `/api/mqtt`)
- [ ] No gaps or missing data over 1-hour test run
- [ ] Grafana dashboard shows live sensor data

**6. Data Pipeline Integration:**
- [ ] Data pipeline service queries InfluxDB successfully
- [ ] Feature engineering runs on ORC sensor data
- [ ] Engineered features written to `engineered_features` bucket
- [ ] No errors in data-pipeline logs: `docker logs data-pipeline`

**Documentation to Update:**
- `docs/technical-plan.md` Section 4.1 - Clarify ORC is the sensor interface (not separate drivers)
- `edge/services/telegraf/README.md` - Document ORC topic mapping
- `CHANGELOG.md` - Add ORC integration to v0.5.0

---

### 4. Digital Twin Model Development (Week 14-16)
**Reference:** `docs/technical-plan.md` Section 5.3

#### Model Training Pipeline
**Location:** `workstation/training/`

- [ ] **Feature Selection** (`feature_selection.py`)
  - Load engineered features from InfluxDB
  - Correlation analysis with OD600 target
  - Recursive feature elimination (RFE) or SHAP-based selection
  - Target: 20-30 most predictive features

- [ ] **LightGBM Baseline Model** (`train_lightgbm.py`)
  - Hyperparameter tuning (learning_rate, max_depth, num_leaves, min_data_in_leaf)
  - 5-fold cross-validation on Batches 1-15
  - Target: MRE ≤ 8% on validation set
  - Save model artifacts: `models/lightgbm_od_predictor_v1.txt`

- [ ] **Model Evaluation** (`evaluate.py`)
  - Hold-out test set: Batches 16-18 (Phase C)
  - Metrics: MRE, RMSE, MAE, R²
  - Residual plots, prediction vs actual scatter
  - Save evaluation report: `models/evaluation_report_v1.md`

- [ ] **Edge Deployment** (`deploy_to_edge.py`)
  - Convert model to ONNX or export LightGBM native format
  - Copy to Jetson: `edge/services/digital-twin/models/`
  - Update inference service to load model
  - Test inference latency < 100ms per prediction

#### Inference Service
**Location:** `edge/services/digital-twin/`

- [ ] **FastAPI Inference Endpoint** (`app/inference.py`)
  - `POST /predict` - Real-time OD prediction from latest features
  - `GET /predictions/{batch_id}` - Historical predictions with uncertainty
  - Model versioning support (v1, v2, etc.)
  - MQTT publish: `predictions/od600/value` topic

- [ ] **Real-Time Monitoring**
  - Grafana panel: predicted vs actual OD600
  - Prediction uncertainty bands (if model supports)
  - Alerting: if MRE exceeds 10% threshold

**Testing:**
- [ ] Offline inference on historical data (Batches 1-15)
- [ ] Real-time inference during live batch run
- [ ] Model drift detection (retrain if MRE degrades)

**Documentation to Update:**
- `docs/technical-plan.md` Section 5.3 (model architecture, hyperparameters)
- `models/README.md` (training procedure, deployment guide)
- `CHANGELOG.md` (add model training to v1.0.0)

---

### 5. Phase A Experimental Campaign (Week 16-18)
**Reference:** `docs/batch-run-plan.md`

#### Batch Execution
- [ ] **Batch 1** - Baseline conditions
  - Manual data entry via tablet UI
  - Sensor data collection (18 sensors at 1 Hz)
  - Export batch report after completion
  - Review data quality: any sensor failures, missing data?

- [ ] **Batch 2** - Repeat baseline (reproducibility check)
  - Compare OD trajectory to Batch 1
  - Calculate Phase A coefficient of variation (CV)
  - If CV < 5%, target MRE ≤ 6% (adaptive threshold)

- [ ] **Batch 3** - Baseline #3
  - Final reproducibility check
  - Complete Phase A dataset for initial model training

#### Data Quality Review
- [ ] Verify all 3 batches have ≥8 samples
- [ ] Check sensor uptime (target: >95%)
- [ ] Validate feature engineering pipeline (no NaN values)
- [ ] Export CSV for model training: `data/batches_1-3_training.csv`

**Success Criteria (Phase A):**
- 3 successful batch completions
- No Level 3 failures (critical deviations)
- CV < 10% for OD600 trajectories
- Data pipeline 100% operational

---

## 📋 Technical Debt & Improvements

### Frontend Enhancements
- [ ] Offline-first mode with IndexedDB queue (for unreliable network)
- [ ] QR code scanning for vessel/cryo-vial IDs (reduce manual entry errors)
- [ ] Real-time updates via WebSocket (show latest samples without refresh)
- [ ] Batch comparison analytics (overlay multiple OD curves)
- [ ] Media preparation form (currently not implemented)

### Backend Improvements
- [ ] Automated backups (PostgreSQL daily dumps to S3/NAS)
- [ ] Audit log dashboard (who changed what, when)
- [ ] Email notifications for Level 3 failures
- [ ] RESTful batch status webhooks (integrate with lab LIMS)

### Data Pipeline Optimizations
- [ ] Adaptive thresholds for outlier detection (learn from historical data)
- [ ] Advanced gap-filling: LSTM-based interpolation for gaps >30 min
- [ ] Real-time feature importance tracking (SHAP on streaming data)
- [ ] Anomaly detection: One-Class SVM for unusual sensor patterns

### Testing & Validation
- [ ] End-to-end Cypress tests for frontend workflows
- [ ] Load testing: 1000+ concurrent API requests (stress test)
- [ ] Sensor driver unit tests with mocked hardware
- [ ] Model robustness: test on batches with sensor failures

---

## 🎯 Milestones & Timeline

| Milestone | Target Date | Deliverables |
|-----------|-------------|--------------|
| **v0.5.0** Sensor Integration | Week 13 | All drivers deployed, 24h uptime test passed |
| **v0.6.0** Baseline Model | Week 16 | LightGBM model trained on simulated/Phase A data |
| **v1.0.0** Phase 1 Complete | Week 20 | 18 batches done, MRE ≤ 8% validated on Batches 16-18 |

---

## 📖 Documentation Priorities

### User-Facing Docs (DO Create)
- [ ] `docs/sops/sensor-calibration-procedure.md` - Technician guide for sensor calibration
- [ ] `docs/sops/batch-execution-checklist.md` - Step-by-step batch run guide
- [ ] `docs/sops/troubleshooting-guide.md` - Common errors and fixes
- [ ] `README.md` - Update with Phase 1 completion status

### Technical Docs (Update as You Go)
- [ ] `docs/technical-plan.md` - Mark completed sections (5.1 ✅, 5.2 ✅)
- [ ] `docs/manual-data-development.md` - Add frontend screenshots
- [ ] `CHANGELOG.md` - Keep updated with every version

### Do NOT Create (Unless Explicitly Requested)
- ❌ Architecture Decision Records (ADRs)
- ❌ Developer onboarding guides
- ❌ Meeting notes
- ❌ Design rationale documents

---

## 🚀 Immediate Next Actions (This Week)

1. **Review Project Status**
   - Re-read `docs/technical-plan.md` to understand full Phase 1 scope
   - Check `docs/batch-run-plan.md` for experimental timeline
   - Verify hardware procurement status (sensors ordered?)

2. **Start Sensor Driver Development**
   - Set up `hardware/sensor-drivers/` directory structure
   - Install required libraries (pyserial, smbus2, adafruit-circuitpython)
   - Write first driver (start with easiest: temperature or pressure)

3. **Test Data Pipeline with Mock Data**
   - Use `edge/services/data-pipeline/tests/` to generate synthetic sensor streams
   - Verify InfluxDB writes are working
   - Check Grafana dashboard shows engineered features

4. **Deploy Edge Stack on Jetson**
   - Copy `edge/docker-compose.yml` to Jetson
   - Run `docker-compose up -d` and verify all 7 services healthy
   - Test tablet UI on local network (http://jetson-ip/)

---

## 📞 Key Decisions Needed from User

Before proceeding, clarify:

1. **Hardware Status:**
   - Are sensors already connected? If so, what communication protocols (serial, I2C, analog)?
   - Is Jetson AGX Orin installed on rig? Network configured?

2. **Phase A Timeline:**
   - When is Batch 1 scheduled to run?
   - Are media prep and inoculum ready?

3. **Model Training Data:**
   - Do we have historical batch data to pre-train the model?
   - Or will Batches 1-3 be the first training data?

4. **Deployment Environment:**
   - Is the Jetson connected to lab network or isolated?
   - Do we need VPN/remote access for monitoring?

---

**Remember:** Per CLAUDE.md, always update docs when code changes. For sensor drivers, update `docs/technical-plan.md` Section 4.1 and `CHANGELOG.md` immediately.

**Next Session:** Start with sensor driver development or model training, depending on hardware availability and user priorities.
