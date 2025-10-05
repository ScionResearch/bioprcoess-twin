# Documentation

This directory contains all planning documents, SOPs, architecture diagrams, and references for the Bioprocess Twin project.

## Document Hierarchy (Single Source of Truth)

When conflicts arise, always defer to the designated SSoT:

1. **Process & Experiments:** [batch-run-plan.md](batch-run-plan.md) - All experimental procedures, parameters, manual data requirements
2. **Technical Implementation:** [technical-plan.md](technical-plan.md) - Software, hardware, data pipeline, database schema
3. **Project Management:** [project-plan.md](project-plan.md) - Objectives, scope, timeline, risks, success criteria
4. **Manual Data Implementation:** [manual-data-development.md](manual-data-development.md) - Must align with Batch Run Plan requirements

## Core Planning Documents

### [Project Plan](project-plan.md)
**SSoT for:** Objectives, success criteria, timeline, budget, risk register

**Key Sections:**
- Success criteria: MRE ≤ 8% (adaptive ≤ 6% if Phase A CV <5%)
- 18-batch campaign timeline (20 weeks)
- Hardware requirements and costs
- Go-live gate checklist

### [Batch Run Plan](batch-run-plan.md)
**SSoT for:** Experimental procedures, batch execution, data quality

**Key Sections:**
- Phase A/B/C strategy (shakedown, data accumulation, validation)
- Standard Operating Procedure (SOP) for single batch run
- Controlled variation strategy (temperature, inoculum, stress testing)
- Calibration protocols (pH, DO, off-gas sensors, pressure)
- Data quality gates and deviation management
- Batch acceptance criteria

### [Technical Plan](technical-plan.md)
**SSoT for:** System architecture, sensor list, feature engineering, model development

**Key Sections:**
- Sensor list (20+ parameters including off-gas CO₂/O₂, pressure, temperatures)
- MQTT topic structure
- Feature engineering (CER/OUR/RQ/μ/qO₂/qCO₂/kLa with pressure correction)
- LightGBM model architecture
- Docker Compose edge stack

### [Manual Data Development](manual-data-development.md)
**SSoT for:** Tablet form system, Postgres schema, API design

**Key Sections:**
- Batch-centric data model (7 form types)
- Postgres schema (batches, calibrations, samples, failures, etc.)
- FastAPI endpoint specifications
- Quality validation rules

## References

### [Alignment Analysis: Gasset et al. 2024](references/alignment-analysis-gasset2024.md)
Comparative analysis showing 8.5/10 alignment with published research on AI-driven *P. pastoris* fermentation control.

**Key Findings:**
- Gasset et al. achieved MRE 3.5-4% on fed-batch RQ control (more complex process)
- Our Phase 1 target (MRE ≤ 8%) is realistic for first-time team
- Off-gas analysis (CER/OUR/RQ) critical for metabolic state inference
- Controlled variation strategy validated by their training approach

### Invitrogen Pichia Fermentation Guidelines
Reference manual for media recipes, cultivation parameters, and troubleshooting.

## Standard Operating Procedures (SOPs)

Located in [sops/](sops/) directory:

- **batch-execution-sop.md** - Step-by-step batch execution from media prep to harvest
- **sensor-calibration-sop.md** - Calibration protocols for pH, DO, off-gas sensors, pressure
- **tablet-form-guide.md** - User guide for manual data entry via tablet forms

## Architecture Diagrams

Located in [architecture/](architecture/) directory:

- **system-architecture.png** - High-level data flow diagram
- **data-flow.png** - Detailed sensor → MQTT → InfluxDB → prediction pipeline
- **mqtt-topic-structure.md** - Complete MQTT topic hierarchy

## Updating Documentation

**Important:** Documentation changes may require code updates to maintain alignment.

**Process:**
1. Update relevant SSoT document
2. Check for cross-references in other documents
3. Update dependent code (schemas, configs, etc.)
4. Update CHANGELOG.md
5. Commit with message: `docs: [section] - [brief description]`

**Example:**
```bash
# Updated sensor list in Technical Plan
# Must also update:
# - edge/services/telegraf/telegraf.conf
# - hardware/sensor-drivers/ (new drivers if needed)
# - database/init.sql (if manual data schema affected)
```

## Version History

See [../CHANGELOG.md](../CHANGELOG.md) for document version history.

---

**Last Updated:** 2025-10-05
