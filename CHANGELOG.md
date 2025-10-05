# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial repository structure
- Core planning documents (Project Plan, Batch Run Plan, Technical Plan)
- Documentation hierarchy (docs/, SOPs, architecture)
- Edge stack framework (Docker Compose configuration)
- API structure (FastAPI + Postgres schema)
- Webapp structure (React tablet forms)
- Hardware sensor driver templates
- Model versioning structure
- CI/CD workflows (.github/)

### Project Setup
- Repository created: 2025-10-05
- Based on Gasset et al. (2024) alignment analysis
- Target: MRE ≤ 8% (adaptive ≤ 6% if Phase A CV <5%)
- 18-batch experimental campaign (Phase A: 1-3, Phase B: 4-15, Phase C: 16-18)
- Off-gas analysis (custom CO₂/O₂ sensors with integrated analyzer fallback)
- Reactor pressure measurement for gas balance correction
- Multiple temperature sensors (broth, pH probe, DO probe, motor, exhaust)

## [0.1.0] - TBD

### Planned
- [ ] Docker Compose edge stack deployment
- [ ] MQTT broker configuration (Mosquitto)
- [ ] InfluxDB setup with bucket structure
- [ ] Telegraf configuration for sensor ingestion
- [ ] Grafana dashboard provisioning
- [ ] FastAPI manual data backend
- [ ] Postgres schema implementation
- [ ] React tablet form development
- [ ] Sensor driver implementation (CO₂, O₂, pressure, temperatures)
- [ ] Feature engineering pipeline (CER/OUR/RQ/μ/kLa)
- [ ] LightGBM baseline model training
- [ ] Phase A experimental campaign (Batches 1-3)

## Future Versions

### [1.0.0] - Phase 1 Completion (Target: Week 20)
- 18-batch campaign completed
- Model validation (MRE ≤ 8% on hold-out batches 16-18)
- Full documentation package
- Public release

### [2.0.0] - Phase 2 (Digital Twin with Control)
- RQ-based closed-loop control implementation
- Methanol fed-batch process modeling
- Recombinant protein expression prediction
- Multi-strain support

---

**Note:** This changelog will be updated with each significant change to the project.
