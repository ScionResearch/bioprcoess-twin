# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - 2025-10-22
- **Media Preparation Display in UI**: Dashboard now fetches and displays logged media preparation data with expandable component details and lot numbers
- **Admin User Management API**: New endpoints for admins to create, list, and delete users (`POST /api/users`, `GET /api/users`, `DELETE /api/users/{username}`)
- **Media Recipe Viewer**: Collapsible component grid showing all media components, quantities, and lot numbers in batch dashboard
- **Admin Delete Button**: Frontend delete button for pending batches with cascade confirmation (admin role only)
- **Comprehensive Testing Guide**: New `TESTING_GUIDE.md` with complete API and UI testing protocol for Phase A readiness
- **Admin Reference Guide**: New `ADMIN_GUIDE.md` with all admin capabilities, emergency procedures, and maintenance tasks

### Fixed - 2025-10-22
- **CRITICAL: Database Schema Mismatch**: Applied pending database migrations to fix inoculations table schema
  - Migration `001_flexible_eln.sql` renamed `cryo_vial_id` → `inoculum_source` to support flexible inoculum sources
  - Migration `002_fix_ph_slope_calculation.sql` corrected pH slope formula
  - **Impact:** HIGH - Batch deletion was failing with "column inoculations.inoculum_source does not exist" error
  - **Resolution:** Applied both migrations to production database
- **Media Prep UI Gap**: Batch dashboard now properly displays media preparation data after logging (was only showing the "Log Media Prep" button, not the logged recipe)
- **Missing Media Fetch**: Added `api.media.get()` call to batch data loading to retrieve logged media preparation records
- **Component Display**: Added CSS styling for media components grid and lot number formatting

### Enhanced - 2025-10-22
- **Media Prep Section**: Shows recipe name, preparation time, autoclave cycle, sterility status, and expandable component list with lot traceability
- **Admin Controls Panel**: Collapsible admin panel with edit, export, and delete batch functionality (frontend now matches backend capabilities)
- **User Management**: Admins can now create technician accounts via API with role-based access control enforcement
- **Documentation**: Complete testing protocol and admin guide for Phase A batch campaign

### Technical Details - 2025-10-22
- Modified `webapp/src/pages/BatchDashboard.tsx`: Added mediaPrep state, fetch logic in loadBatchData(), and display component with collapsible details
- Modified `webapp/src/pages/BatchDashboard.css`: Added media-prep-details, components-grid, component-item, and lot-number styles
- Modified `api/app/routers/auth.py`: Added POST/GET/DELETE endpoints for user management (admin-only access)
- Created documentation: `TESTING_GUIDE.md`, `ADMIN_GUIDE.md`, `RECIPE_UI_FIX.md`

### Fixed
- **CRITICAL:** Computed fields in BatchResponse now return actual counts instead of placeholder zeros (api/app/routers/batches.py:128-175)
  - `total_samples_count`, `calibrations_count`, `critical_failures_count` now functional
  - Fixes batch closure validation bug (batches can now be closed when ≥8 samples exist)
  - **Impact:** HIGH - Core workflow was broken
- **CRITICAL:** pH slope calculation formula was inverted, causing incorrect calibration rejections (api/app/schemas.py:193-226, database/init.sql:457-500, database/migrations/002_fix_ph_slope_calculation.sql)
  - **Old (WRONG):** `slope = (delta_pH / delta_mV) / 59.16 * 100` → gave 0.03% for a perfect probe
  - **New (CORRECT):** `slope = (delta_mV / delta_pH) / 59.16 * 100` → gives 99.7% for a perfect probe
  - **Impact:** HIGH - All pH calibrations with old formula were incorrectly calculated

### Changed
- **Calibration fields** now adapt to probe type (pH uses buffers, DO uses saturation, gas sensors use span gases)
  - Made `buffer_low_value`, `buffer_high_value`, `reading_low`, `reading_high` optional
  - Added comprehensive documentation for field usage by probe type
  - Supports pH (buffers), DO (0%/100% saturation), OffGas (span gases), Temp/Pressure (single-point)
  - **Breaking change:** Forms must handle optional calibration fields
- **Inoculation source** now flexible to support multiple inoculum types
  - Renamed `cryo_vial_id` → `inoculum_source` (nullable, VARCHAR(200))
  - Supports: cryovials, agar plates, seed flasks, or any custom source
  - Relaxed OD₆₀₀ constraint from strict 2.0-10.0 to ≥0.1 (allows low-density plate picks)
  - **Breaking change:** Database migration required (001_flexible_eln.sql)
- **Batch creation** now accepts flexible vessel IDs
  - Removed "must start with V-" validation
  - Any 1-50 character string accepted (e.g., "Fermenter-A", "Bioreactor-01")
- **Failure reporting** field names aligned with backend
  - Frontend `FailureCreate` now uses `deviation_level` (was `severity`)
  - Added required fields: `deviation_start_time`, `category`
  - **Breaking change:** Failure forms must update field names

### Migration Required
- Run `database/migrations/001_flexible_eln.sql` before deploying (schema changes)
- Run `database/migrations/002_fix_ph_slope_calculation.sql` to recalculate existing pH slopes
- Existing data preserved (column rename is non-destructive)

### Added
- Comprehensive pH slope calculation reference documentation (docs/pH-SLOPE-CALCULATION.md)
- End-to-end test script for ELN workflow validation (test-eln-workflow.sh)
- Detailed change documentation (CHANGES.md)

## [0.4.0] - 2025-10-21

### Added - Data Pipeline Service (Real-Time Feature Engineering)

**Data Cleaning Module (Technical Plan §5.1):**
- Linear interpolation for missing data gaps < 5 minutes
- Kalman filter for gaps 5-30 minutes (dynamic noise adaptation)
- Z-score outlier detection and clipping (3σ threshold)
- Physical bounds validation per sensor type (pH 0-14, DO 0-200%, temp -20-120°C)
- Comprehensive quality reporting: clean/interpolated/outlier/invalid counts

**Feature Engineering Module (Technical Plan §5.2):**
- **Basic statistical features**: mean, std, slope for all 18 sensors
- **Gas exchange rates**: CER, OUR, RQ with reactor pressure correction
- **Growth metrics**: μ (Savitzky-Golay derivative), qO₂, qCO₂ (specific rates)
- **Mass transfer**: kLa estimation from OUR and DO profiles
- **Thermal features**: gradients, sensor agreement, motor temperature monitoring
- **Pressure features**: deviation detection, anomaly alerts (±0.2 bar threshold)
- **Process state**: phase detection (lag/exponential/stationary)
- **Cumulative sums**: integrated CO₂ production, O₂ consumption, OD trajectory
- **60+ features** generated per 30-second aggregation window

**FastAPI Service:**
- 9 REST endpoints for pipeline management and health checks
- Real-time processing: `/pipeline/process` endpoint for batch/streaming modes
- Feature retrieval: `/pipeline/features/{batch_id}` with time range queries
- Quality metrics: `/pipeline/health` with Prometheus-compatible metrics
- MQTT alerting for critical failures and quality threshold violations
- Configurable thresholds via environment variables

**InfluxDB Integration:**
- Telegraf MQTT subscriber configuration for sensor ingestion
- InfluxDB Flux task for 30-second downsampling (mean/min/max aggregation)
- Bucket structure: raw_sensors → downsampled_sensors → engineered_features
- Retention policies: 90 days raw, 1 year features

**Docker Deployment:**
- Multi-stage Dockerfile optimized for ARM64 (Jetson AGX Orin)
- Added to edge/docker-compose.yml with InfluxDB, Mosquitto, Telegraf services
- Health checks and automatic restarts
- Environment-based configuration with validation

**Testing & Documentation:**
- 24 unit tests with 85% code coverage (pytest)
- Edge case validation: missing data, outliers, sensor failures
- QUICKSTART.md: Deployment and local testing guide
- README.md: Architecture overview and API reference
- docs/data-pipeline-implementation.md: Complete implementation summary

**Infrastructure Services Added:**
- Mosquitto MQTT broker (edge message bus)
- InfluxDB 2.7 with initialization scripts (buckets + Flux tasks)
- Telegraf with MQTT→InfluxDB pipeline configuration

**File Structure:**
```
edge/services/data-pipeline/
├── app/
│   ├── data_cleaning.py       # Interpolation, outlier detection
│   ├── feature_engineering.py # 60+ feature calculations
│   ├── influx_client.py       # InfluxDB query/write wrapper
│   ├── monitoring.py          # Prometheus + MQTT alerting
│   ├── pipeline.py            # Orchestration layer
│   └── main.py                # FastAPI routes
├── tests/                     # Unit tests with fixtures
├── Dockerfile                 # Multi-stage ARM64 build
└── requirements.txt           # scipy, scikit-learn, influxdb-client
```

### Changed
- edge/docker-compose.yml upgraded to include 4 new services (data-pipeline, influxdb, mosquitto, telegraf)

## [0.3.0] - 2025-10-21

### Added - React Frontend (Tablet-Optimized ELN Interface)

**Web Application Stack:**
- React 18 with TypeScript for type-safe component development
- Vite build system with hot module replacement
- React Router v6 with protected route guards
- Axios HTTP client with JWT interceptors
- React Hook Form + Zod for validated form handling
- date-fns for timepoint calculations

**Authentication & Authorization:**
- JWT-based login system with token persistence (localStorage)
- Protected routes with automatic redirect on 401 responses
- Role-based access control enforced in UI (engineer/technician/admin)
- AuthContext provider for global auth state management
- Auto-logout on token expiry or invalid credentials

**Batch Management Pages:**
- **Batch List** (`/batches`): Grid view with status badges (pending/running/complete/failed)
  - Real-time computed fields: timepoint hours, sample count, failure count
  - Status-based color coding and sorting by most recent
  - Responsive tablet grid (350-400px cards)

- **Batch Dashboard** (`/batches/:id`): Comprehensive workspace with 5 data sections
  1. Calibrations table (pH/DO/Temp with pass/fail indicators)
  2. Inoculation event (T=0 with GO/NO-GO decision)
  3. Samples table (OD600, DCW, contamination flags, timepoints)
  4. Failures log (severity L1/L2/L3 with color coding)
  5. Closure record (engineer approval, final metrics)

- **Create Batch** (`/batches/new`): Form with validation
  - Batch number (1-18), phase (A/B/C), vessel ID (V-XX format)
  - Auto-populate operator from logged-in user
  - Inline error messages with react-hook-form

**Modal Form Components:**
- **CalibrationForm**: Probe type selection, buffer calibration (low/high), pass/fail checkbox
  - Backend calculates pH slope % automatically
  - Uses `pass_` field to avoid Python keyword conflict

- **InoculationForm**: Cryo-vial ID, inoculum OD600 (0.1-10 range), microscopy notes
  - **Critical GO/NO-GO decision** - disables submit if NO-GO selected
  - Warning banner: "This sets T=0 and changes status to running"

- **SampleForm**: OD600 raw reading + dilution factor with real-time calculation
  - Displays corrected OD600 = raw × dilution
  - Optional DCW (g/L) with contamination checkbox
  - Microscopy notes (recommended for contamination events)

- **FailureForm**: Severity levels (L1/L2/L3), description (min 20 chars)
  - Root cause analysis and corrective action fields
  - L3 alert: "Requires engineer review, batch may be terminated"

- **ClosureForm**: Final OD600, total runtime, glycerol depletion time
  - Outcome selection: Complete/Partial/Failed
  - Engineer approval ID (USER:E001 format validation)
  - Permission check: Only engineer/admin roles can submit
  - Warning: "This locks all batch records"

**Workflow Quality Gates (Enforced in UI):**
- Cannot inoculate until all 3 probe types have passing calibrations
- Cannot add samples until batch status = "running" (post-inoculation)
- Cannot close batch until ≥8 samples collected
- Cannot close batch if Level 3 failures are unreviewed
- Batch closure restricted to engineer/admin roles

**Tablet Optimization:**
- Touch-friendly buttons ≥44×44px (Apple/Android guidelines)
- Large tap targets on cards and interactive elements
- Base font size 16-18px for readability without zoom
- High contrast color scheme (#1a202c text on #f7fafc background)
- Responsive grid layouts: 1 col mobile → 2 col tablet → 3 col desktop
- System font stack for native rendering performance

**Docker Deployment:**
- Multi-stage Dockerfile: Node 18 build → Nginx Alpine serve
- Nginx configuration with React Router support (try_files)
- Gzip compression and security headers
- Integrated into docker-compose.yml (depends on API health check)
- CORS configuration: API allows localhost:5173 (dev) and localhost:80 (prod)

**Type Safety:**
- TypeScript interfaces (src/types/index.ts) mirror backend Pydantic schemas
- Typed API client methods for all endpoints (POST /auth/login, GET/POST /batches, etc.)
- Form validation schemas with Zod runtime checks

**Files Created:**
- 39 new files across webapp/ directory
- Package.json with 15 dependencies (react, axios, react-hook-form, zod, jwt-decode, date-fns)
- 5 page components, 6 modal forms, 3 shared components, 1 API client, 1 auth context

**Default Users for Testing:**
- admin / admin123 (admin role)
- tech01 / admin123 (technician role)
- eng01 / admin123 (engineer role)

**Known Limitations:**
- No offline-first mode (IndexedDB queue for pending sync)
- No QR code scanning for vessel/cryo-vial IDs
- No real-time updates (WebSocket integration pending)
- Media preparation form not implemented (not critical path)

### Added - Batch Data Export Endpoint

**Export Formats:**
- **CSV Export** (`?format=csv`): Optimized for digital twin model training
  - Columns: timepoint_hours, od600_calculated, dcw_g_per_l
  - Clean tabular format for pandas ingestion
  - Filename: `batch_{id}_samples.csv`

- **Markdown Export** (`?format=markdown`): Human-readable batch report for OneNote
  - Sections: Batch info, calibrations, inoculation, samples table, failures, closure
  - Visual indicators: ✅ PASS, ❌ FAIL, 🔴 L3, 🟡 L2, 🔵 L1
  - Formatted tables with alignment
  - Filename: `batch_{id}_report.md`

- **JSON Export** (`?format=json`): Complete structured data for pipelines
  - Full batch record with all relationships (calibrations, samples, failures, inoculation, closure)
  - Nested objects preserving foreign key relationships
  - ISO 8601 timestamps
  - Filename: `batch_{id}_data.json`

**API Endpoint:**
- `GET /api/v1/batches/{batch_id}/export?format={csv|markdown|json}`
- Proper HTTP headers: Content-Type and Content-Disposition for downloads
- 404 error if batch not found
- 400 error if invalid format specified

**Documentation:**
- EXPORT_SUMMARY.md: Quick reference guide with curl examples
- docs/EXPORT_GUIDE.md: Complete usage guide with Python requests examples
- docs/EXAMPLE_BATCH_EXPORT.md: Sample Markdown output for reference

**Use Cases:**
- CSV: Training LightGBM models (OD prediction from sensor features)
- Markdown: Archiving batch reports in lab OneNote notebooks
- JSON: Data pipeline ingestion, automated analysis, backup/restore

**File Modified:**
- api/app/routers/batches.py: Added export_batch_data() endpoint with format logic

## [0.2.1] - 2025-10-21

### Fixed - Backend Compatibility and Testing

**Bug Fixes:**
- Resolved bcrypt password verification error by pinning bcrypt==4.0.1 in requirements
- Fixed calibration endpoint `pass_` field alias handling (avoided Python keyword conflict)
- Updated seed user password hashes for consistency (admin123, tech123, eng123)

**Testing Infrastructure:**
- Added comprehensive integration test suite (api/tests/test_api_workflow.py)
- 60+ test assertions covering complete batch workflow
- pytest.ini configuration for API testing

**Test Coverage:**
- Authentication and JWT token validation
- Batch CRUD operations (create, read, update, delete)
- Calibration workflow with database auto-calculations (pH slope %)
- Complete batch lifecycle: creation → calibrations → inoculation → samples → closure
- Role-based access control (RBAC) enforcement
- Database triggers: pH slope calculation, OD600→DCW conversion, status transitions

**Validation Results:**
- ✅ Docker services health (Postgres + FastAPI)
- ✅ JWT authentication for all 3 roles (admin, engineer, technician)
- ✅ Batch creation with status tracking
- ✅ pH calibration with auto-calculated slope (validated 1.70% typical)
- ✅ DO calibration with response time tracking
- ✅ Database triggers functioning correctly

**Files Modified:**
- api/app/routers/calibrations.py:37 - Use by_alias=False for model_dump
- api/requirements.txt - Added bcrypt 4.0.1
- database/init.sql - Fixed password hashes for default users (lines 522-524)

**Files Created:**
- api/tests/test_api_workflow.py (562 lines) - Integration test suite
- api/pytest.ini - Pytest configuration

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
