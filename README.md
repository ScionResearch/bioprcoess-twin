# Bioprocess Twin

**Open-source digital shadow for *Pichia pastoris* fermentation | Edge-first | Research-grade**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-24.0+-blue.svg)](https://www.docker.com/)

---

## Overview

**Bioprocess Twin** is an end-to-end digital shadow platform for real-time prediction and monitoring of *Pichia pastoris* glycerol batch fermentations. Designed for research labs and biotech startups, it runs entirely on-premise using edge computing (NVIDIA Jetson) and open-source tools.

**Phase 1 Scope:**
- Predict OD₆₀₀ biomass trajectory with MRE ≤ 8% (stretch: ≤ 6%)
- Real-time inference (<1s latency) using LightGBM on edge
- Comprehensive manual data capture via tablet forms (electronic lab notebook)
- Off-gas analysis (CER/OUR/RQ) for metabolic state inference
- Control paths implemented but disabled (`CONTROL_MODE=0`)

**Phase 2 Roadmap:**
- Closed-loop RQ-based physiological control (based on Gasset et al. 2024)
- Methanol fed-batch process modeling
- Recombinant protein expression prediction
- Multi-strain support

---

## Key Features

✅ **Edge-First Architecture**: All processing on NVIDIA Jetson AGX Orin (no cloud dependency)
✅ **Research-Grade Data Quality**: Automated sensor calibration tracking, deviation management, batch acceptance criteria
✅ **Production-Ready Stack**: Docker Compose orchestration, MQTT pub/sub, InfluxDB time-series, Postgres relational DB
✅ **Comprehensive Monitoring**: Grafana dashboards, Prometheus metrics, automated alerts
✅ **Validated Approach**: Based on published research achieving MRE <4% (Gasset et al. 2024, *Frontiers in Bioengineering*)
✅ **Open Data Standards**: Parquet datasets, JSON-Schema forms, MQTT topic structure

---

## Quick Start

### Prerequisites
- **Hardware**: NVIDIA Jetson AGX Orin 64GB (or development on x86 workstation)
- **Software**: Docker 24.0+, Docker Compose, Git
- **Sensors**: pH, DO, OD probes; off-gas CO₂/O₂ sensors; pressure transducer

### Installation

```bash
# Clone repository
git clone https://github.com/yourorg/bioprocess-twin.git
cd bioprocess-twin

# Copy environment template
cp edge/.env.example edge/.env
# Edit edge/.env with your MQTT broker IP, InfluxDB credentials, etc.

# Start edge stack
cd edge
docker-compose up -d

# Verify services
docker-compose ps
# Expected: mosquitto, telegraf, influxdb, grafana, digital-twin all running

# Initialize database
psql -U pichia_api -d pichia_manual_data -f database/init.sql

# Run migrations (if updating existing installation)
psql -U pichia_api -d pichia_manual_data -f database/migrations/001_flexible_eln.sql
psql -U pichia_api -d pichia_manual_data -f database/migrations/002_fix_ph_slope_calculation.sql

# Access Grafana dashboard
# Navigate to http://<jetson-ip>:3000 (default login: admin/admin)
```

### Database Migrations

After pulling updates, run pending migrations:

```bash
# Migration 001: Flexible ELN fields (inoculum source, calibration fields)
psql -U pichia_api -d pichia_manual_data -f database/migrations/001_flexible_eln.sql

# Migration 002: Fix pH slope calculation formula
psql -U pichia_api -d pichia_manual_data -f database/migrations/002_fix_ph_slope_calculation.sql
```

**Migrations applied:**
- **001_flexible_eln.sql**: Makes ELN more flexible (optional calibration fields, flexible inoculum sources, relaxed constraints)
- **002_fix_ph_slope_calculation.sql**: Corrects pH probe slope % formula (was inverted, causing incorrect calibration rejections)
```

### First Batch Execution

1. **Prepare batch record** (via tablet or API):
   ```bash
   python scripts/batch-management/create_batch.py --batch-number 1 --phase A --operator "Your Name"
   ```

2. **Execute calibrations** (see [docs/sops/sensor-calibration-sop.md](docs/sops/sensor-calibration-sop.md))

3. **Start fermentation** following [docs/sops/batch-execution-sop.md](docs/sops/batch-execution-sop.md)

4. **Monitor in real-time** via Grafana dashboard

---

## Architecture

```
┌─────────────────────────┐
│  Tablet / Manual Forms  │
└────────────┬────────────┘
             │ (HTTPS)
Sensors ──MQTT──► Telegraf ──► InfluxDB ◄── FastAPI ──► Postgres
(1Hz)                 │          (raw)       (manual)     (audit)
                      │ 30s agg
                      ▼
                ┌──────────────────┐
                │ Jetson Inference │
                │   (LightGBM)     │
                └──────────────────┘
                      │ (prediction)
                      ▼
                MQTT & InfluxDB
                      │ (pred)
                      ▼
                   Grafana
```

**Data Flow:**
1. Sensors publish to MQTT at 1 Hz (pH, DO, OD, pressure, off-gas CO₂/O₂, temperatures)
2. Telegraf ingests to InfluxDB raw bucket
3. InfluxDB Flux task aggregates to 30s windows
4. Digital Twin service reads 30s windows, runs feature engineering (CER/OUR/RQ/μ/kLa), predicts OD₆₀₀
5. Predictions written back to MQTT + InfluxDB for visualization
6. Manual data (calibrations, samples, deviations) entered via tablet → FastAPI → Postgres

See [docs/architecture/system-architecture.png](docs/architecture/system-architecture.png) for detailed diagram.

---

## Project Structure

```
bioprocess-twin/
├── docs/                   # Planning documents, SOPs, references
├── edge/                   # Edge deployment (Jetson)
│   ├── docker-compose.yml
│   └── services/           # Microservices (digital-twin, telegraf, influxdb, etc.)
├── workstation/            # Model training on GPU workstation
│   ├── notebooks/          # Jupyter notebooks (data exploration, training, validation)
│   └── training/           # Training scripts (LightGBM, Optuna tuning)
├── api/                    # FastAPI backend for manual data
├── webapp/                 # React tablet forms (electronic lab notebook)
├── database/               # Postgres schema (batch-centric data model)
├── hardware/               # Sensor drivers (custom CO₂/O₂ → MQTT)
├── models/                 # Versioned model artifacts (LightGBM .lgb files)
├── scripts/                # Utility scripts (batch management, monitoring)
└── tests/                  # Integration tests
```

---

## Documentation

**Core Planning Documents:**
- [Project Plan](docs/project-plan.md) - Objectives, success criteria, timeline, budget
- [Batch Run Plan](docs/batch-run-plan.md) - 18-batch experimental campaign, SOPs, Phase A/B/C strategy
- [Technical Plan](docs/technical-plan.md) - System architecture, sensor list, feature engineering, model development
- [Manual Data Development](docs/manual-data-development.md) - Tablet form system, Postgres schema, API design

**Standard Operating Procedures:**
- [Batch Execution SOP](docs/sops/batch-execution-sop.md)
- [Sensor Calibration SOP](docs/sops/sensor-calibration-sop.md)
- [Tablet Form User Guide](docs/sops/tablet-form-guide.md)

**References:**
- [Alignment Analysis: Gasset et al. 2024](docs/references/alignment-analysis-gasset2024.md)
- [Invitrogen Pichia Fermentation Guidelines](docs/references/invitrogen-pichia-guidelines.pdf)

---

## Hardware Requirements

### Edge (Jetson)
- NVIDIA Jetson AGX Orin 64GB (~$2,000)
- Power supply + heatsink/fan
- 1TB NVMe SSD (for InfluxDB time-series data)
- Gigabit Ethernet connection

### Sensors & Instrumentation
- pH probe with 2-point calibration (slope ≥95%)
- Dissolved oxygen (DO) probe with 0%/100% calibration
- In-situ OD₆₀₀ optical density probe
- Reactor pressure transducer (0.9-1.5 bar)
- Off-gas CO₂ sensor (0-5% v/v, custom NDIR or electrochemical)
- Off-gas O₂ sensor (19-21% v/v, custom paramagnetic or zirconia)
- Temperature sensors: broth RTD, pH/DO integrated, stirrer motor, exhaust
- Mass flow controller (air inlet, 0-2 L/min)

**Total Sensor/Hardware Cost:** ~$8,200 (Phase 1 custom sensors) + $5,000 contingency (integrated off-gas analyzer if needed)

### Training Workstation
- NVIDIA RTX 4080 or better
- 32GB+ RAM
- Ubuntu 22.04 or Windows 10/11

---

## Software Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| **JetPack** | 5.1.2 | NVIDIA Jetson OS |
| **Docker** | 24.0.5 | Container runtime |
| **MQTT** | Eclipse Mosquitto 2.0.18 | Sensor data pub/sub |
| **InfluxDB** | 2.7 (ARM64) | Time-series database |
| **Telegraf** | 1.28 (ARM64) | Data ingestion |
| **Postgres** | 15 | Relational DB (manual data) |
| **FastAPI** | 0.103.0 | REST API backend |
| **React** | 18.2 | Tablet form frontend |
| **Grafana** | 10.1 (ARM64) | Dashboards |
| **Python** | 3.10+ | ML/data processing |
| **LightGBM** | 4.0.0 | Gradient boosting model |
| **Optuna** | 3.3.0 | Hyperparameter tuning |

All open-source, no license fees.

---

## Performance Targets

| Metric | Target | Validation Method |
|--------|--------|-------------------|
| **MRE** (30s OD prediction) | ≤ 8% (adaptive: ≤6% if Phase A CV <5%) | Hold-out batches 16-18 |
| **R²** (OD trajectory) | > 0.90 | Validation report |
| **RMSE** (DO prediction) | < 5% saturation | Validation report |
| **Inference Latency** | < 1 second | Grafana P99 monitoring |
| **System Uptime** | ≥ 95% | Prometheus container monitoring |
| **Batch Acceptance Rate** | ≥ 80% | Phase A-C campaign statistics |

**Success Criteria:** MRE target met on ≥2 of 3 hold-out batches (16-18).

---

## Development Roadmap

### Phase 1 (Current) - Digital Shadow
- [x] System architecture design
- [x] Planning documents (Project/Batch/Technical plans)
- [x] Alignment with published research (Gasset et al. 2024)
- [ ] Edge stack deployment (Docker Compose)
- [ ] Sensor driver development (custom CO₂/O₂ → MQTT)
- [ ] FastAPI + Postgres manual data system
- [ ] React tablet forms
- [ ] 18-batch experimental campaign (Phases A/B/C)
- [ ] LightGBM model training & validation
- [ ] v1.0 release

### Phase 2 - Digital Twin (Control)
- [ ] RQ-based closed-loop control (CONTROL_MODE=1)
- [ ] Methanol fed-batch process modeling
- [ ] Recombinant protein expression prediction
- [ ] Multi-strain support (KM71H, etc.)
- [ ] Advanced alerting & notifications

### Phase 3 - Production Scale
- [ ] GMP compliance features
- [ ] 21 CFR Part 11 electronic signatures
- [ ] Multi-vessel orchestration
- [ ] Cloud data replication (optional)

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Areas needing help:**
- Sensor driver development (Modbus, OPC-UA integrations)
- Grafana dashboard design
- Model architecture experiments (LSTM, Transformer for time-series)
- Documentation improvements
- Hardware integration guides for specific bioreactor models

---

## Citation

If you use this project in your research, please cite:

```bibtex
@software{bioprocess_twin_2025,
  author = {Your Name and Contributors},
  title = {Bioprocess Twin: Open-source digital shadow for Pichia pastoris fermentation},
  year = {2025},
  url = {https://github.com/yourorg/bioprocess-twin},
  version = {1.0.0}
}
```

**Related Publications:**
- Gasset et al. (2024). "Continuous Process Verification 4.0 application in upstream: adaptiveness implementation managed by AI in the hypoxic bioprocess of the Pichia pastoris cell factory." *Frontiers in Bioengineering and Biotechnology*, 12.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- Research methodology based on Gasset et al. (2024), Universitat Autònoma de Barcelona & Aizon
- Invitrogen *Pichia* Fermentation Process Guidelines (Catalog K1750-01)
- NVIDIA Jetson developer community
- Open-source bioprocess community

---

## Contact

- **Issues**: [GitHub Issues](https://github.com/yourorg/bioprocess-twin/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourorg/bioprocess-twin/discussions)
- **Email**: your.email@example.com

---

**Status:** 🚧 Active Development | Phase 1 Campaign In Progress

**Last Updated:** 2025-10-05
