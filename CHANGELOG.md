# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2025-10-20

### Added - Manual Data Collection System (Backend Complete)

**Database Layer:**
- Complete PostgreSQL schema with 9 tables (batches, media_preparations, calibrations, inoculations, samples, process_changes, failures, batch_closures, users)
- Database triggers for auto-calculations (OD600, DCW, timepoints, pH slope percentage)
- Batch status management triggers (inoculation → running, closure → complete)
- Audit log table for compliance tracking
- Batch summary view for dashboard queries
- Seed data with default admin, technician, and engineer users

**FastAPI Backend (v1.0):**
- Async SQLAlchemy ORM models with relationships and constraints
- Pydantic v2 schemas with validation and computed fields
- JWT authentication with HS256 signing
- Role-Based Access Control (RBAC) - 4 roles: technician, engineer, admin, read_only
- Password hashing with bcrypt (cost factor 12)
- CORS middleware configuration
- Comprehensive error handling (validation, integrity constraints, general exceptions)
- Health check endpoints for monitoring

**API Endpoints:**
- `POST /auth/login` - JWT token authentication
- `POST /batches` - Create batch with vessel availability validation
- `GET /batches` - List batches with filtering (phase, status, vessel)
- `GET /batches/{id}` - Get batch details
- `PATCH /batches/{id}` - Update batch metadata
- `DELETE /batches/{id}` - Delete batch (with safety checks)
- `POST /batches/{id}/calibrations` - Log sensor calibrations with pass/fail validation
- `POST /batches/{id}/inoculation` - Record inoculation (sets T=0, validates calibrations)
- `POST /batches/{id}/samples` - Log in-process samples (auto-calculates timepoint)
- `POST /batches/{id}/failures` - Log deviations/failures
- `POST /batches/{id}/close` - Close batch (engineer role required, validates sample count)

**Deployment Configuration:**
- Dockerfile for FastAPI application (Python 3.11-slim)
- Docker Compose with Postgres + API services
- Environment-based configuration with `.env.example`
- Health checks and automatic restarts
- Volume mounts for development hot-reload

**Documentation:**
- Enhanced manual-data-development.md (v2.1) with complete implementation details
- QUICKSTART.md guide for deployment and testing
- API endpoint examples with curl commands
- Default user credentials table

**Workflow Validation:**
- Cannot inoculate until all calibrations pass
- Cannot add samples until batch is running
- Cannot close batch without minimum 8 samples
- Cannot close batch with unreviewed Level 3 failures
- Engineer approval required for batch closure

### Project Setup (from v0.1.0)
- Repository created: 2025-10-05
- Based on Gasset et al. (2024) alignment analysis
- Target: MRE ≤ 8% (adaptive ≤ 6% if Phase A CV <5%)
- 18-batch experimental campaign (Phase A: 1-3, Phase B: 4-15, Phase C: 16-18)
- Off-gas analysis (custom CO₂/O₂ sensors with integrated analyzer fallback)
- Reactor pressure measurement for gas balance correction
- Multiple temperature sensors (broth, pH probe, DO probe, motor, exhaust)

### Changed
- Database schema upgraded to v2.0 with enhanced triggers and constraints
- All default passwords set to 'admin123' (must change in production)

### Technical Stack
- FastAPI 0.104.1 with Uvicorn
- SQLAlchemy 2.0.23 (async)
- PostgreSQL 15
- Pydantic 2.5.0
- python-jose for JWT
- passlib[bcrypt] for password hashing

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
