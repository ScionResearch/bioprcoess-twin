# Manual Data Development Guide
## Pichia pastoris Digital Shadow – Electronic Lab Notebook

**Version:** 2.1
**Purpose:** Define the batch-centric electronic lab notebook schema and API for manual data collection
**Last Updated:** October 20, 2025

**Change Log:**
- **v2.1 (Oct 20, 2025):** Added FastAPI implementation details, security specifications, React component interfaces, deployment configuration, and comprehensive error handling matrix
- **v2.0 (Oct 5, 2025):** Complete JSON schema specifications and workflow definitions
- **v1.0:** Initial draft

---

## **1. System Overview**

This document specifies the **electronic lab notebook** system for capturing all manual observations and quality control data during the 18-batch fermentation campaign. The system is designed around a **batch-centric workflow** where all data is organized hierarchically under a parent batch record.

### **Design Philosophy**

**Batch-Centric Workflow:**
- A technician creates a **Batch Record** at the start of each experiment
- All subsequent data entry (media prep, calibrations, samples, etc.) is added as **child records** linked to that batch
- The system enforces workflow logic (e.g., cannot inoculate until calibrations pass)
- Complete traceability: Every data point is timestamped and attributed to an operator

**Technology Stack:**
- **Frontend:** React SPA with `react-jsonschema-form` (RJSF) for auto-generated forms
- **Backend:** FastAPI with Pydantic validation
- **Database:** PostgreSQL (see Technical Plan Sec 4.4 for complete schema)
- **Deployment:** Nginx reverse proxy, offline-first with retry queue

---

## **2. User Workflow (Technician Perspective)**

### **Phase 1: Batch Setup (Day Before Run)**

**Step 1: Create Batch Record**
- Technician scans vessel QR code on tablet
- System prompts: "Create new batch for Vessel V-01?"
- Technician selects batch number (1-18) and phase (A/B/C)
- System creates batch record and displays **Batch Dashboard**

**Step 2: Log Media Preparation**
- From Batch Dashboard, technician selects "Add Media Prep"
- Fills in component weights and lot numbers
- Logs autoclave cycle and sterility verification
- System saves to `media_preparations` table

**Step 3: Perform Calibrations**
- From Batch Dashboard, technician selects "Add Calibration"
- Repeats for each probe type:
  - **pH:** 2-point buffer calibration (e.g., pH 4.01, 7.00) - system auto-calculates slope%
  - **DO:** 2-point air saturation (0% N₂ purge, 100% air) - records response time (<30s required)
  - **Off-Gas O₂/CO₂:** Span gas calibration (N₂ for 0%, certified span gas for high point)
  - **Temperature:** Single-point verification (ice bath or reference thermometer)
  - **Pressure:** Atmospheric reference or certified gauge
- **Quality Gate:** If pH slope <95% or DO response >30s, system warns technician
- **Notes field:** Use for span gas certificate numbers, reference equipment IDs, or temperature corrections

---

### **Phase 2: Inoculation (T=0)**

**Step 4: Quality Check Inoculum**
- Technician prepares inoculum from selected source (cryovial, agar plate, or seed flask)
- Measures final inoculum OD₆₀₀ and performs microscopy
- From Batch Dashboard, selects "Add Inoculation"
- Fills in:
  - **Inoculum Source** (optional): Description of source (e.g., "Cryo-2024-001", "YPD Plate Colony 3", "Seed Flask A")
  - **Inoculum OD₆₀₀:** Final measured OD (typical range 2-6, minimum 0.1)
  - **Microscopy Observations** (optional): Cell morphology, viability assessment, contamination check
- **GO/NO-GO Decision:** Technician must confirm "GO" to proceed with inoculation
- **Critical:** This step sets `batches.inoculated_at` timestamp → **T=0 starts**

---

### **Phase 3: In-Run Monitoring (T=0 to Glycerol Depletion)**

**Step 5: Add Sample Observations**
- At each timepoint (0h, 2h, 4h, 6h, 8h, 12h, 16h, endpoint)
- From Batch Dashboard, selects "Add Sample"
- System auto-calculates `timepoint_hours` from `inoculated_at` timestamp
- Fills in: OD₆₀₀, dilution factor, DCW measurements, microscopy
- **Contamination Flag:** Boolean field "Contamination Detected?"
  - If TRUE, system prompts "Log Failure Report"

**Step 6: Log Deviations (As Needed)**
- From Batch Dashboard, selects "Add Failure/Deviation"
- Classifies as Level 1/2/3
- Describes issue, root cause, corrective action

---

### **Phase 4: Batch Closure**

**Step 7: Close Batch**
- When glycerol depletion confirmed (DO spike)
- From Batch Dashboard, selects "Close Batch"
- Fills in: Final OD, runtime, glycerol depletion time, outcome
- Process Engineer must approve (sign-off)
- System sets `batches.status = 'complete'` and locks record

---

## **3. JSON Schemas (Frontend Form Generation)**

All forms are generated from JSON Schemas using `react-jsonschema-form`. The schemas below define the data structure and validation rules.

---

### **3.1 Create Batch**

**API Endpoint:** `POST /api/batches`

**Schema:** `create_batch_schema.json`
```json
{
  "title": "Create New Batch Record",
  "description": "Initialize a new batch for the fermentation campaign.",
  "type": "object",
  "required": ["batch_number", "phase", "vessel_id", "operator_id"],
  "properties": {
    "batch_number": {
      "type": "integer",
      "title": "Batch Number",
      "minimum": 1,
      "maximum": 18,
      "description": "Sequential batch number (1-18)"
    },
    "phase": {
      "type": "string",
      "title": "Campaign Phase",
      "enum": ["A", "B", "C"],
      "description": "A: Batches 1-3, B: Batches 4-15, C: Batches 16-18"
    },
    "vessel_id": {
      "type": "string",
      "title": "Vessel ID",
      "description": "Scan the QR code on the bioreactor vessel"
    },
    "operator_id": {
      "type": "string",
      "title": "Lead Operator",
      "description": "Scan your operator badge"
    },
    "notes": {
      "type": "string",
      "title": "Notes (optional)"
    }
  }
}
```

**UI Schema:** `create_batch_uischema.json`
```json
{
  "ui:order": ["vessel_id", "batch_number", "phase", "operator_id", "notes"],
  "vessel_id": {
    "ui:widget": "qr-scanner",
    "ui:placeholder": "Scan vessel QR code"
  },
  "operator_id": {
    "ui:widget": "qr-scanner",
    "ui:placeholder": "Scan operator badge"
  },
  "notes": {
    "ui:widget": "textarea",
    "ui:options": {"rows": 3}
  }
}
```

---

### **3.2 Media Preparation**

**API Endpoint:** `POST /api/batches/{batch_id}/media`

**Schema:** `media_schema.json`
```json
{
  "title": "Media Preparation Log",
  "description": "Record all components and preparation steps for fermentation media (per Batch Run Plan Sec 3.1.2).",
  "type": "object",
  "required": [
    "recipe_name",
    "phosphoric_acid_ml", "phosphoric_acid_lot",
    "calcium_sulfate_g", "calcium_sulfate_lot",
    "potassium_sulfate_g", "potassium_sulfate_lot",
    "magnesium_sulfate_g", "magnesium_sulfate_lot",
    "potassium_hydroxide_g", "potassium_hydroxide_lot",
    "glycerol_g", "glycerol_lot",
    "autoclave_cycle",
    "sterility_verified"
  ],
  "properties": {
    "recipe_name": {
      "type": "string",
      "title": "Media Recipe",
      "enum": ["Fermentation_Basal_Salts_4pct_Glycerol"],
      "default": "Fermentation_Basal_Salts_4pct_Glycerol"
    },
    "phosphoric_acid_ml": {"type": "number", "title": "Phosphoric Acid, 85% (ml)", "default": 26.7},
    "phosphoric_acid_lot": {"type": "string", "title": "Lot #"},
    "calcium_sulfate_g": {"type": "number", "title": "Calcium Sulfate (g)", "default": 0.93},
    "calcium_sulfate_lot": {"type": "string", "title": "Lot #"},
    "potassium_sulfate_g": {"type": "number", "title": "Potassium Sulfate (g)", "default": 18.2},
    "potassium_sulfate_lot": {"type": "string", "title": "Lot #"},
    "magnesium_sulfate_g": {"type": "number", "title": "Magnesium Sulfate·7H₂O (g)", "default": 14.9},
    "magnesium_sulfate_lot": {"type": "string", "title": "Lot #"},
    "potassium_hydroxide_g": {"type": "number", "title": "Potassium Hydroxide (g)", "default": 4.13},
    "potassium_hydroxide_lot": {"type": "string", "title": "Lot #"},
    "glycerol_g": {"type": "number", "title": "Glycerol, 99% (g)", "default": 40.0},
    "glycerol_lot": {"type": "string", "title": "Lot #"},
    "final_volume_l": {"type": "number", "title": "Final Volume (L)", "default": 0.9},
    "autoclave_cycle": {"type": "string", "title": "Autoclave Cycle Number"},
    "sterility_verified": {"type": "boolean", "title": "Sterility Indicator Passed?", "default": false},
    "prepared_by": {"type": "string", "title": "Prepared By (Operator ID)"},
    "notes": {"type": "string", "title": "Notes"}
  }
}
```

---

### **3.3 Calibration**

**API Endpoint:** `POST /api/batches/{batch_id}/calibrations` (call 3 times: pH, DO, Temp)

**Schema:** `calibration_schema.json`
```json
{
  "title": "Sensor Calibration Record",
  "description": "Log 2-point calibration for pH, DO, or temperature probe (per Batch Run Plan Sec 3.1.1).",
  "type": "object",
  "required": ["probe_type", "pass"],
  "properties": {
    "probe_type": {
      "type": "string",
      "title": "Probe Type",
      "enum": ["pH", "DO", "Temp"]
    },
    "buffer_low_value": {
      "type": "number",
      "title": "Low Buffer/Reference Value",
      "description": "e.g., pH 4.01 or 0% DO"
    },
    "buffer_low_lot": {
      "type": "string",
      "title": "Low Buffer Lot #"
    },
    "buffer_high_value": {
      "type": "number",
      "title": "High Buffer/Reference Value",
      "description": "e.g., pH 7.00 or 100% DO"
    },
    "buffer_high_lot": {
      "type": "string",
      "title": "High Buffer Lot #"
    },
    "reading_low": {
      "type": "number",
      "title": "Low Point Reading"
    },
    "reading_high": {
      "type": "number",
      "title": "High Point Reading"
    },
    "slope_percent": {
      "type": "number",
      "title": "Slope % (pH only, auto-calculated)",
      "readOnly": true
    },
    "response_time_sec": {
      "type": "integer",
      "title": "Response Time (seconds, DO only)",
      "description": "Time to reach 63% of step change. Must be <30s."
    },
    "pass": {
      "type": "boolean",
      "title": "Calibration PASSED?",
      "description": "pH: slope ≥95%. DO: response <30s."
    },
    "control_active": {
      "type": "boolean",
      "title": "Will control be active for this batch?",
      "description": "Batch 1: FALSE (monitoring only). Batches 2+: TRUE (automated control)",
      "default": true
    },
    "calibrated_by": {
      "type": "string",
      "title": "Calibrated By (Operator ID)"
    },
    "notes": {
      "type": "string",
      "title": "Notes"
    }
  }
}
```

**Validation Logic (API Layer):**
- If `probe_type == "pH"`, auto-calculate `slope_percent` from readings
- If `slope_percent < 95`, force `pass = FALSE`
- If `probe_type == "DO"` and `response_time_sec > 30`, force `pass = FALSE`

---

### **3.4 Inoculation**

**API Endpoint:** `POST /api/batches/{batch_id}/inoculation`

**Schema:** `inoculation_schema.json`
```json
{
  "title": "Inoculation Record (Sets T=0)",
  "description": "Record inoculum quality check and inoculation event. This starts the batch clock (per Batch Run Plan Sec 3.2.2 & 3.3.3).",
  "type": "object",
  "required": ["cryo_vial_id", "inoculum_od600", "go_decision"],
  "properties": {
    "cryo_vial_id": {
      "type": "string",
      "title": "Cryo-vial / Plate ID",
      "description": "Scan QR code on inoculum source"
    },
    "inoculum_od600": {
      "type": "number",
      "title": "Inoculum OD₆₀₀ (final)",
      "minimum": 2.0,
      "maximum": 10.0,
      "description": "Target range: 2.0-6.0 (up to 10 allowed with justification)"
    },
    "dilution_factor": {
      "type": "number",
      "title": "Dilution Factor (if OD>1.0 measured)",
      "default": 1.0,
      "description": "If you diluted 10×, enter 10. Final OD = reading × factor."
    },
    "inoculum_volume_ml": {
      "type": "number",
      "title": "Inoculum Volume (ml)",
      "default": 100
    },
    "microscopy_observations": {
      "type": "string",
      "title": "Microscopy Observations",
      "description": "Cell morphology, contaminants, viability estimate"
    },
    "go_decision": {
      "type": "boolean",
      "title": "GO Decision (Inoculate Vessel?)",
      "description": "Check this box only if OD is in range and microscopy is clean"
    },
    "inoculated_by": {
      "type": "string",
      "title": "Inoculated By (Operator ID)"
    }
  }
}
```

**Critical Validation (API Layer):**
- Cannot POST if ANY calibration has `pass = FALSE`
- If `go_decision = TRUE`, set `batches.inoculated_at = NOW()` and `batches.status = 'running'`
- If `go_decision = FALSE`, return error and prompt to log `FAILURE` record

---

### **3.5 Sample**

**API Endpoint:** `POST /api/batches/{batch_id}/samples`

**Schema:** `sample_schema.json`
```json
{
  "title": "In-Process Sample Observation",
  "description": "Record all measurements from a single sampling event (per Batch Run Plan Sec 3.4.2).",
  "type": "object",
  "required": ["od600_raw", "contamination_detected"],
  "properties": {
    "timepoint_hours": {
      "type": "number",
      "title": "Timepoint (hours post-inoculation)",
      "readOnly": true,
      "description": "Auto-calculated from current time and batches.inoculated_at"
    },
    "sample_volume_ml": {
      "type": "number",
      "title": "Sample Volume Taken (ml)",
      "default": 10
    },
    "od600_raw": {
      "type": "number",
      "title": "OD₆₀₀ Reading (from spectrophotometer)"
    },
    "od600_dilution_factor": {
      "type": "number",
      "title": "Dilution Factor",
      "default": 1.0,
      "description": "If undiluted, enter 1. If 10× diluted, enter 10."
    },
    "od600_calculated": {
      "type": "number",
      "title": "Calculated OD₆₀₀",
      "readOnly": true,
      "description": "Auto-calculated: raw × dilution_factor"
    },
    "dcw_filter_id": {
      "type": "string",
      "title": "DCW Filter ID (scan QR on filter tin)"
    },
    "dcw_sample_volume_ml": {
      "type": "number",
      "title": "Volume Filtered for DCW (ml)"
    },
    "dcw_filter_wet_weight_g": {
      "type": "number",
      "title": "Filter + Wet Cells Weight (g)"
    },
    "dcw_filter_dry_weight_g": {
      "type": "number",
      "title": "Filter + Dry Cells Weight (g, after 24h drying)"
    },
    "dcw_g_per_l": {
      "type": "number",
      "title": "DCW (g/L)",
      "readOnly": true,
      "description": "Auto-calculated from weights and volume"
    },
    "contamination_detected": {
      "type": "boolean",
      "title": "Contamination Detected?",
      "default": false,
      "description": "Check if microscopy shows contaminants"
    },
    "microscopy_observations": {
      "type": "string",
      "title": "Microscopy Observations",
      "description": "Cell morphology, budding, contaminants, notes"
    },
    "supernatant_cryovial_id": {
      "type": "string",
      "title": "Supernatant Cryovial ID (if archived)"
    },
    "pellet_cryovial_id": {
      "type": "string",
      "title": "Pellet Cryovial ID (if archived)"
    },
    "sampled_by": {
      "type": "string",
      "title": "Sampled By (Operator ID)"
    }
  }
}
```

**Validation Logic (API Layer):**
- Auto-calculate `timepoint_hours = (NOW() - batches.inoculated_at) / 3600`
- Auto-calculate `od600_calculated = od600_raw × od600_dilution_factor`
- Auto-calculate `dcw_g_per_l` from filter weights and volume
- If `contamination_detected = TRUE`, prompt operator to immediately log `FAILURE` record

---

### **3.6 Failure / Deviation**

**API Endpoint:** `POST /api/batches/{batch_id}/failures`

**Schema:** `failure_schema.json`
```json
{
  "title": "Failure / Deviation Log",
  "description": "Record any process deviation or failure event (per Batch Run Plan Sec 4.2).",
  "type": "object",
  "required": ["deviation_level", "category", "description"],
  "properties": {
    "deviation_level": {
      "type": "integer",
      "title": "Deviation Level",
      "enum": [1, 2, 3],
      "description": "1=Minor (Yellow), 2=Major (Orange), 3=Critical (Red)"
    },
    "deviation_start_time": {
      "type": "string",
      "format": "date-time",
      "title": "Deviation Start Time"
    },
    "deviation_end_time": {
      "type": "string",
      "format": "date-time",
      "title": "Deviation End Time (if resolved)"
    },
    "category": {
      "type": "string",
      "title": "Category",
      "enum": [
        "Contamination",
        "DO_Crash",
        "DO_Crash_No_Control",
        "pH_Excursion",
        "pH_Drift_No_Control",
        "Temp_Excursion",
        "Sensor_Failure",
        "Power_Outage",
        "Sampling_Missed",
        "O2_Enrichment_Used",
        "Other"
      ]
    },
    "description": {
      "type": "string",
      "title": "Description of Issue"
    },
    "root_cause": {
      "type": "string",
      "title": "Root Cause (if known)"
    },
    "corrective_action": {
      "type": "string",
      "title": "Corrective Action Taken"
    },
    "impact_assessment": {
      "type": "string",
      "title": "Impact on Data Quality / Batch Outcome"
    },
    "reported_by": {
      "type": "string",
      "title": "Reported By (Operator ID)"
    },
    "reviewed_by": {
      "type": "string",
      "title": "Reviewed By (Process Engineer or ML Engineer)"
    }
  }
}
```

---

### **3.7 Close Batch**

**API Endpoint:** `POST /api/batches/{batch_id}/close`

**Schema:** `batch_closure_schema.json`
```json
{
  "title": "Batch Closure & Sign-Off",
  "description": "Final batch record and Process Engineer approval (per Batch Run Plan Sec 3.5.3).",
  "type": "object",
  "required": ["final_od600", "total_runtime_hours", "outcome", "approved_by"],
  "properties": {
    "final_od600": {
      "type": "number",
      "title": "Final OD₆₀₀ (at glycerol depletion)"
    },
    "total_runtime_hours": {
      "type": "number",
      "title": "Total Batch Runtime (hours)",
      "description": "From inoculation to glycerol depletion"
    },
    "glycerol_depletion_time_hours": {
      "type": "number",
      "title": "Glycerol Depletion Time (hours)",
      "description": "Time when DO spike observed"
    },
    "do_spike_observed": {
      "type": "boolean",
      "title": "DO Spike Observed?",
      "default": true
    },
    "max_do_percent": {
      "type": "number",
      "title": "Maximum DO % (during spike)"
    },
    "cumulative_base_addition_ml": {
      "type": "number",
      "title": "Cumulative Base Addition (ml)",
      "description": "Total 28% NH₄OH consumed"
    },
    "outcome": {
      "type": "string",
      "title": "Batch Outcome",
      "enum": [
        "Complete",
        "Aborted_Contamination",
        "Aborted_Sensor_Failure",
        "Aborted_Other"
      ]
    },
    "harvest_method": {
      "type": "string",
      "title": "Harvest Method",
      "enum": ["Cell_Banking", "Disposal"]
    },
    "closed_by": {
      "type": "string",
      "title": "Closed By (Operator ID)"
    },
    "approved_by": {
      "type": "string",
      "title": "Approved By (Process Engineer - Scan Badge)",
      "description": "Process Engineer must sign off to close batch"
    },
    "notes": {
      "type": "string",
      "title": "Final Batch Notes"
    }
  }
}
```

**Validation Logic (API Layer):**
- Cannot close batch if <8 sample records exist
- Cannot close batch if any Level 3 deviation exists (must be reviewed first)
- Sets `batches.status = 'complete'` and `batches.completed_at = NOW()`
- Locks batch record (no further edits allowed)

---

## **4. Tablet UI Mockup (Batch Dashboard)**

When a technician opens the app and scans a vessel QR code, they see:

```
╔════════════════════════════════════════════════════════════╗
║  BATCH #5 - VESSEL V-01 - PHASE B - RUNNING               ║
║  Started: Oct 5, 2025 08:15 (T=2.3h)                       ║
╠════════════════════════════════════════════════════════════╣
║  PRE-RUN SETUP                                   [Status]  ║
║  ✅ Media Preparation (Oct 4, 14:30)               Complete ║
║  ✅ Calibration - pH (Slope: 98.2%)                Pass     ║
║  ✅ Calibration - DO (Response: 22s)               Pass     ║
║  ✅ Calibration - Temp                             Pass     ║
║  ✅ Inoculation (OD=4.2, GO)                       Complete ║
╠════════════════════════════════════════════════════════════╣
║  IN-RUN OBSERVATIONS                                       ║
║  ✅ Sample @ T=0h (OD=0.42)                                ║
║  ✅ Sample @ T=2h (OD=2.1)                                 ║
║  ⏳ Sample @ T=4h (DUE IN 1.7h)                  [ADD NOW] ║
║  ⏹️ Sample @ T=6h                                          ║
║  ⏹️ Sample @ T=8h                                          ║
╠════════════════════════════════════════════════════════════╣
║  ACTIONS                                                   ║
║  [+ Add Sample]  [+ Log Failure]  [+ Process Change]      ║
║                                            [Close Batch]   ║
╚════════════════════════════════════════════════════════════╝
```

---

## **5. API Response Examples**

### **Success Response**
```json
{
  "status": "success",
  "batch_id": "a3f2e9d1-4b7c-4f5a-9e1b-8d3c2a1f0e9d",
  "record_id": 42,
  "message": "Sample added to Batch #5 at T=2.3h. OD₆₀₀=2.1, DCW=0.52 g/L"
}
```

### **Validation Error Response**
```json
{
  "status": "error",
  "code": 422,
  "detail": [
    {
      "loc": ["body", "od600_raw"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### **Workflow Error Response**
```json
{
  "status": "error",
  "code": 400,
  "message": "Cannot add inoculation: pH calibration failed (slope 92.3% < 95%). Please recalibrate pH probe."
}
```

---

## **6. Implementation Notes for Developers**

### **Database Migration**
- Use Alembic for schema versioning
- Initialize database with SQL from Technical Plan Sec 4.4
- Seed with test data for Phase A batch simulation

### **Offline-First Strategy**
- Use IndexedDB on tablet to queue POST requests when offline
- Retry queue with exponential backoff (1s, 2s, 4s, 8s, 30s intervals)
- Display "Queued (will sync when online)" badge in UI

### **QR Code Scanner Integration**
- Use `html5-qrcode` library for camera access
- Validate QR format: `VESSEL:<ID>`, `USER:<ID>`, `CRYO:<ID>`, `FILTER:<ID>`
- Reject mismatched scans (e.g., scanning CRYO code when expecting VESSEL)

### **Auto-Calculation Fields**
- Frontend calculates and displays in real-time (instant feedback)
- Backend recalculates and validates (source of truth)
- If mismatch, backend value wins

### **Form State Persistence**
- Auto-save form draft to localStorage every 30 seconds
- Prompt "Resume draft from 5 minutes ago?" on form re-entry
- Clear draft on successful submission

---

## **7. Testing & Validation Plan**

### **Phase A Integration Testing (Batches 1-3)**

**Week 1 (Batch 1):**
- Mock batch with water (no cells)
- Full workflow test: Create batch → Media → Calibration → Inoculation → 3 samples → Close
- Measure time to complete all forms
- Target: <15 minutes for complete workflow

**Week 2 (Batch 2):**
- Real fermentation with live cells
- Test offline mode: Disconnect Wi-Fi during sample entry, verify retry queue works
- Test contamination workflow: Deliberately flag contamination, verify failure log workflow

**Week 3 (Batch 3):**
- Test dual-vessel scenario (2 batches running simultaneously)
- Verify no cross-contamination of batch contexts
- Test Process Engineer sign-off workflow for batch closure

### **Acceptance Criteria (from Project Plan Sec 8.0)**
1. Two technicians complete mock batch forms in <15 minutes ✅
2. Offline-submitted form syncs within 30 seconds of Wi-Fi restore ✅
3. Daily `pg_dump` backup successfully restores on test machine ✅

---

## **8. Future Enhancements (Phase 2 - Digital Twin)**

When control write-back is enabled in Phase 2:
- Add `process_changes` table integration with MQTT control topics
- Add "Recommended Action" alerts from model predictions
- Add closed-loop control approval workflow (Process Engineer must approve automated changes)

---

## **9. FastAPI Backend Implementation**

### **9.1 Technology Stack**

**Backend Framework:**
- **FastAPI** 0.103.0+ with **Uvicorn** ASGI server
- **SQLAlchemy** 2.0 ORM with async support
- **Alembic** for database migrations
- **Pydantic** v2 for request/response validation
- **PostgreSQL** 15 with psycopg3 driver

**Authentication:**
- JWT tokens with RS256 signing
- 15-minute access token lifetime
- 7-day refresh token lifetime
- Role-Based Access Control (RBAC)

**API Documentation:**
- Auto-generated OpenAPI 3.0 spec at `/docs` (Swagger UI)
- ReDoc at `/redoc`

### **9.2 Project Structure**

```
api/
├── Dockerfile
├── requirements.txt
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 001_initial_schema.py
├── app/
│   ├── main.py                    # FastAPI application entry
│   ├── config.py                  # Environment configuration
│   ├── database.py                # DB session management
│   ├── dependencies.py            # Dependency injection (auth, DB)
│   ├── models.py                  # SQLAlchemy ORM models
│   ├── schemas.py                 # Pydantic request/response schemas
│   ├── crud.py                    # Database operations
│   ├── auth.py                    # JWT authentication
│   ├── exceptions.py              # Custom exceptions
│   └── routers/
│       ├── __init__.py
│       ├── batches.py             # Batch CRUD endpoints
│       ├── calibrations.py        # Calibration endpoints
│       ├── inoculations.py        # Inoculation endpoints
│       ├── samples.py             # Sample endpoints
│       ├── failures.py            # Failure/deviation endpoints
│       └── auth.py                # Login/token endpoints
└── tests/
    ├── conftest.py                # Pytest fixtures
    ├── test_batches.py
    └── test_workflow.py           # End-to-end workflow tests
```

### **9.3 Complete API Endpoint Specification**

#### **Base URL:** `http://jetson-edge.local:8000/api/v1`

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/auth/login` | POST | No | Obtain JWT access + refresh tokens |
| `/auth/refresh` | POST | No | Refresh access token |
| `/batches` | GET | Yes | List all batches (with filtering) |
| `/batches` | POST | Yes | Create new batch record |
| `/batches/{batch_id}` | GET | Yes | Get batch details with all child records |
| `/batches/{batch_id}` | PATCH | Yes | Update batch metadata (limited fields) |
| `/batches/{batch_id}/media` | POST | Yes | Add media preparation record |
| `/batches/{batch_id}/calibrations` | POST | Yes | Add calibration record (call 3× for pH/DO/Temp) |
| `/batches/{batch_id}/inoculation` | POST | Yes | Set T=0 and start batch clock |
| `/batches/{batch_id}/samples` | POST | Yes | Add in-process sample observation |
| `/batches/{batch_id}/samples` | GET | Yes | List all samples for batch |
| `/batches/{batch_id}/failures` | POST | Yes | Log deviation/failure event |
| `/batches/{batch_id}/close` | POST | Yes | Close batch and lock record |
| `/batches/{batch_id}/export` | GET | Yes | Export batch as JSON/CSV |

### **9.4 Example Implementation: Create Batch Endpoint**

**File:** `app/routers/batches.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime, timezone

from ..database import get_db
from ..models import Batch, Calibration
from ..schemas import BatchCreate, BatchResponse
from ..auth import get_current_user, User
from ..exceptions import WorkflowError

router = APIRouter(prefix="/batches", tags=["batches"])

@router.post("/", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
async def create_batch(
    batch_in: BatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new batch record.

    **Validation:**
    - Batch number must be unique within phase
    - Vessel must not have another active (running) batch
    - Operator must have 'technician' or 'engineer' role
    """

    # Check for duplicate batch number
    stmt = select(Batch).where(
        Batch.batch_number == batch_in.batch_number,
        Batch.phase == batch_in.phase
    )
    result = await db.execute(stmt)
    existing_batch = result.scalar_one_or_none()

    if existing_batch:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Batch {batch_in.batch_number} already exists in Phase {batch_in.phase}"
        )

    # Check vessel availability
    stmt = select(Batch).where(
        Batch.vessel_id == batch_in.vessel_id,
        Batch.status.in_(["pending", "running"])
    )
    result = await db.execute(stmt)
    active_batch = result.scalar_one_or_none()

    if active_batch:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Vessel {batch_in.vessel_id} has active batch #{active_batch.batch_number}"
        )

    # Create batch record
    batch = Batch(
        batch_number=batch_in.batch_number,
        phase=batch_in.phase,
        vessel_id=batch_in.vessel_id,
        operator_id=batch_in.operator_id,
        notes=batch_in.notes,
        status="pending",
        created_at=datetime.now(timezone.utc),
        created_by=current_user.username
    )

    db.add(batch)
    await db.commit()
    await db.refresh(batch)

    return batch


@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get complete batch record with all child records."""

    stmt = select(Batch).where(Batch.id == batch_id)
    result = await db.execute(stmt)
    batch = result.scalar_one_or_none()

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found"
        )

    return batch
```

### **9.5 Pydantic Schemas**

**File:** `app/schemas.py`

```python
from pydantic import BaseModel, Field, field_validator, computed_field
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

class BatchCreate(BaseModel):
    batch_number: int = Field(..., ge=1, le=18, description="Batch number (1-18)")
    phase: Literal["A", "B", "C"] = Field(..., description="Campaign phase")
    vessel_id: str = Field(..., min_length=1, max_length=20)
    operator_id: str = Field(..., min_length=1, max_length=20)
    notes: Optional[str] = None

    @field_validator("vessel_id")
    @classmethod
    def validate_vessel_format(cls, v: str) -> str:
        if not v.startswith("V-"):
            raise ValueError("Vessel ID must start with 'V-'")
        return v

class BatchResponse(BaseModel):
    id: UUID
    batch_number: int
    phase: str
    vessel_id: str
    operator_id: str
    status: str
    created_at: datetime
    inoculated_at: Optional[datetime]
    completed_at: Optional[datetime]
    notes: Optional[str]

    # Computed field: runtime in hours
    @computed_field
    @property
    def runtime_hours(self) -> Optional[float]:
        if self.inoculated_at and self.completed_at:
            delta = self.completed_at - self.inoculated_at
            return round(delta.total_seconds() / 3600, 2)
        return None

    class Config:
        from_attributes = True  # Pydantic v2 (was orm_mode in v1)


class CalibrationCreate(BaseModel):
    probe_type: Literal["pH", "DO", "Temp"]
    buffer_low_value: float
    buffer_low_lot: Optional[str] = None
    buffer_high_value: float
    buffer_high_lot: Optional[str] = None
    reading_low: float
    reading_high: float
    response_time_sec: Optional[int] = Field(None, description="DO probe only")
    pass_: bool = Field(..., alias="pass")  # 'pass' is reserved in Python
    control_active: bool = True
    calibrated_by: str
    notes: Optional[str] = None

    @field_validator("pass_")
    @classmethod
    def validate_calibration_pass(cls, v: bool, info) -> bool:
        """Auto-fail if pH slope <95% or DO response >30s."""
        probe_type = info.data.get("probe_type")

        if probe_type == "pH":
            slope_pct = cls._calculate_ph_slope(
                info.data.get("buffer_low_value"),
                info.data.get("buffer_high_value"),
                info.data.get("reading_low"),
                info.data.get("reading_high")
            )
            if slope_pct < 95.0:
                return False

        elif probe_type == "DO":
            response_time = info.data.get("response_time_sec")
            if response_time and response_time > 30:
                return False

        return v

    @staticmethod
    def _calculate_ph_slope(low_ref: float, high_ref: float,
                           low_read: float, high_read: float) -> float:
        """Calculate pH probe slope percentage."""
        if not all([low_ref, high_ref, low_read, high_read]):
            return 0.0

        theoretical_slope = (high_ref - low_ref) / (high_read - low_read)
        # Nernst equation: 59.16 mV/pH at 25°C
        slope_pct = (abs(theoretical_slope) / 59.16) * 100
        return round(slope_pct, 1)

    class Config:
        populate_by_name = True  # Allow both 'pass' and 'pass_'


class InoculationCreate(BaseModel):
    cryo_vial_id: str
    inoculum_od600: float = Field(..., ge=2.0, le=10.0)
    dilution_factor: float = Field(1.0, ge=1.0)
    inoculum_volume_ml: float = 100.0
    microscopy_observations: str
    go_decision: bool
    inoculated_by: str

    @field_validator("go_decision")
    @classmethod
    def validate_go_decision(cls, v: bool, info) -> bool:
        """Enforce GO decision logic."""
        od = info.data.get("inoculum_od600")

        # Warn if OD is outside preferred range but allow with justification
        if v and od:
            if od < 2.0 or od > 6.0:
                # In production, this would log a warning
                pass

        return v


class SampleCreate(BaseModel):
    sample_volume_ml: float = 10.0
    od600_raw: float = Field(..., ge=0.0)
    od600_dilution_factor: float = Field(1.0, ge=1.0)
    dcw_filter_id: Optional[str] = None
    dcw_sample_volume_ml: Optional[float] = None
    dcw_filter_wet_weight_g: Optional[float] = None
    dcw_filter_dry_weight_g: Optional[float] = None
    contamination_detected: bool = False
    microscopy_observations: Optional[str] = None
    supernatant_cryovial_id: Optional[str] = None
    pellet_cryovial_id: Optional[str] = None
    sampled_by: str

    @computed_field
    @property
    def od600_calculated(self) -> float:
        return round(self.od600_raw * self.od600_dilution_factor, 3)

    @computed_field
    @property
    def dcw_g_per_l(self) -> Optional[float]:
        """Calculate DCW from filter weights."""
        if all([self.dcw_filter_dry_weight_g,
                self.dcw_filter_wet_weight_g,
                self.dcw_sample_volume_ml]):

            # Assuming filter tare weight is pre-subtracted or negligible
            dry_mass_g = self.dcw_filter_dry_weight_g - self.dcw_filter_wet_weight_g
            dcw = (dry_mass_g / self.dcw_sample_volume_ml) * 1000  # Convert to g/L
            return round(dcw, 2)

        return None
```

### **9.6 Database Models (SQLAlchemy)**

**File:** `app/models.py`

```python
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum

from .database import Base

class BatchStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    ABORTED = "aborted"

class Batch(Base):
    __tablename__ = "batches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_number = Column(Integer, nullable=False)
    phase = Column(String(1), nullable=False)  # A, B, or C
    vessel_id = Column(String(20), nullable=False)
    operator_id = Column(String(20), nullable=False)
    status = Column(Enum(BatchStatus), default=BatchStatus.PENDING)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_by = Column(String(50))
    inoculated_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    media_prep = relationship("MediaPreparation", back_populates="batch", uselist=False)
    calibrations = relationship("Calibration", back_populates="batch")
    inoculation = relationship("Inoculation", back_populates="batch", uselist=False)
    samples = relationship("Sample", back_populates="batch", order_by="Sample.timepoint_hours")
    failures = relationship("Failure", back_populates="batch")
    closure = relationship("BatchClosure", back_populates="batch", uselist=False)

    # Constraints
    __table_args__ = (
        # Unique constraint on batch_number within phase
        # Note: In PostgreSQL, use a unique index instead for better control
    )


class Calibration(Base):
    __tablename__ = "calibrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id", ondelete="CASCADE"), nullable=False)

    probe_type = Column(String(10), nullable=False)  # pH, DO, Temp
    buffer_low_value = Column(Float)
    buffer_low_lot = Column(String(50))
    buffer_high_value = Column(Float)
    buffer_high_lot = Column(String(50))
    reading_low = Column(Float)
    reading_high = Column(Float)
    slope_percent = Column(Float, nullable=True)  # pH only
    response_time_sec = Column(Integer, nullable=True)  # DO only
    pass_ = Column("pass", Boolean, nullable=False)
    control_active = Column(Boolean, default=True)

    calibrated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    calibrated_by = Column(String(50))
    notes = Column(Text)

    batch = relationship("Batch", back_populates="calibrations")


class Sample(Base):
    __tablename__ = "samples"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id", ondelete="CASCADE"), nullable=False)

    timepoint_hours = Column(Float)  # Auto-calculated from inoculated_at
    sample_volume_ml = Column(Float)

    od600_raw = Column(Float, nullable=False)
    od600_dilution_factor = Column(Float, default=1.0)
    od600_calculated = Column(Float)  # Auto-calculated

    dcw_filter_id = Column(String(50))
    dcw_sample_volume_ml = Column(Float)
    dcw_filter_wet_weight_g = Column(Float)
    dcw_filter_dry_weight_g = Column(Float)
    dcw_g_per_l = Column(Float)  # Auto-calculated

    contamination_detected = Column(Boolean, default=False)
    microscopy_observations = Column(Text)
    supernatant_cryovial_id = Column(String(50))
    pellet_cryovial_id = Column(String(50))

    sampled_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    sampled_by = Column(String(50))

    batch = relationship("Batch", back_populates="samples")
```

---

## **10. Security & Authentication**

### **10.1 Role-Based Access Control (RBAC)**

**User Roles:**

| Role | Permissions |
|------|-------------|
| **Technician** | Create batches, add all observations (media, calibrations, samples), view own batches |
| **Engineer** | All Technician permissions + close batches, approve closures, view all batches |
| **Admin** | All permissions + user management, system configuration |
| **Read-Only** | View batches and reports, export data (for Phase 2 analysis) |

**Implementation:**

```python
# app/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # Store in .env, rotate quarterly
ALGORITHM = "RS256"  # Use asymmetric signing for production
ACCESS_TOKEN_EXPIRE_MINUTES = 15

security = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")

        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

        return User(username=username, role=role)

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

def require_role(allowed_roles: list[str]):
    """Dependency to enforce role-based access."""
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {allowed_roles}"
            )
        return current_user
    return role_checker

# Usage in router:
@router.post("/batches/{batch_id}/close")
async def close_batch(
    batch_id: str,
    current_user: User = Depends(require_role(["engineer", "admin"]))
):
    # Only engineers and admins can close batches
    pass
```

### **10.2 Security Best Practices**

**Data Protection:**
- All passwords hashed with bcrypt (cost factor 12)
- JWTs signed with RS256 (private key on server only)
- Refresh tokens stored in HTTP-only cookies
- CORS restricted to tablet IP range and workstation
- Rate limiting: 100 requests/minute per IP

**Audit Trail:**
- Every POST/PATCH/DELETE logs: `username`, `timestamp`, `endpoint`, `batch_id`
- Stored in separate `audit_log` table (append-only, never delete)
- Weekly audit log export to MinIO

**Secrets Management:**
- Database password, JWT keys stored in `.env` file (gitignored)
- `.env.example` provided as template
- Production: Use Docker secrets or HashiCorp Vault

**Example `.env` file:**

```bash
# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=pichia_manual_data
POSTGRES_USER=pichia_api
POSTGRES_PASSWORD=<generate_strong_password>

# JWT Authentication
JWT_SECRET_KEY=<generate_rsa_key>
JWT_ALGORITHM=RS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
ALLOWED_ORIGINS=http://tablet-01.local,http://tablet-02.local,http://workstation.local

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
```

---

## **11. Error Handling & Validation Matrix**

### **11.1 HTTP Status Codes**

| Code | Meaning | Usage |
|------|---------|-------|
| **200** | OK | Successful GET request |
| **201** | Created | Successful POST (resource created) |
| **204** | No Content | Successful DELETE |
| **400** | Bad Request | Validation error (Pydantic) |
| **401** | Unauthorized | Missing or invalid JWT token |
| **403** | Forbidden | Insufficient permissions (RBAC) |
| **404** | Not Found | Batch/record does not exist |
| **409** | Conflict | Duplicate batch number, vessel in use |
| **422** | Unprocessable Entity | Workflow violation (e.g., inoculate before calibration) |
| **500** | Internal Server Error | Database error, unhandled exception |

### **11.2 Standard Error Response Format**

```json
{
  "status": "error",
  "code": 422,
  "message": "Cannot add inoculation: pH calibration failed",
  "detail": {
    "batch_id": "a3f2e9d1-4b7c-4f5a-9e1b-8d3c2a1f0e9d",
    "failed_calibrations": [
      {
        "probe_type": "pH",
        "slope_percent": 92.3,
        "threshold": 95.0,
        "calibrated_at": "2025-10-19T14:30:00Z"
      }
    ]
  },
  "timestamp": "2025-10-20T10:15:30Z",
  "path": "/api/v1/batches/a3f2e9d1-4b7c-4f5a-9e1b-8d3c2a1f0e9d/inoculation"
}
```

### **11.3 Workflow Validation Rules**

| Validation | Rule | Error Code | Error Message |
|------------|------|-----------|---------------|
| **Create Batch** | Batch number must be unique within phase | 409 | "Batch {N} already exists in Phase {A/B/C}" |
| **Create Batch** | Vessel must not have active batch | 409 | "Vessel {ID} has active batch #{N}" |
| **Add Media Prep** | Batch must be in 'pending' status | 422 | "Cannot add media prep: batch already started" |
| **Add Calibration** | Batch must be in 'pending' status | 422 | "Cannot add calibration: batch already started" |
| **Add Calibration** | pH slope must be ≥95% | 400 | "pH calibration failed: slope {X}% < 95%" |
| **Add Calibration** | DO response time must be <30s | 400 | "DO calibration failed: response time {X}s > 30s" |
| **Add Inoculation** | All calibrations must pass | 422 | "Cannot inoculate: {probe} calibration failed" |
| **Add Inoculation** | Media prep must exist | 422 | "Cannot inoculate: no media prep record" |
| **Add Inoculation** | GO decision must be TRUE | 422 | "Inoculation rejected by operator (GO=FALSE)" |
| **Add Sample** | Batch must be 'running' | 422 | "Cannot add sample: batch not yet inoculated" |
| **Add Sample** | If contamination=TRUE, must log failure | 422 | "Contamination detected: failure report required" |
| **Close Batch** | Batch must be 'running' | 422 | "Cannot close batch: not yet started" |
| **Close Batch** | Must have ≥8 sample records | 422 | "Cannot close: only {N} samples (minimum 8 required)" |
| **Close Batch** | All Level 3 failures must be reviewed | 422 | "Cannot close: {N} unreviewed critical failures" |
| **Close Batch** | Must have engineer role | 403 | "Insufficient permissions: engineer approval required" |

### **11.4 Custom Exception Classes**

```python
# app/exceptions.py
from fastapi import HTTPException, status

class WorkflowError(HTTPException):
    """Raised when workflow prerequisites are not met."""
    def __init__(self, message: str, detail: dict = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": message, "detail": detail}
        )

class CalibrationFailedError(WorkflowError):
    """Raised when calibration does not pass acceptance criteria."""
    pass

class BatchNotFoundError(HTTPException):
    """Raised when batch ID does not exist."""
    def __init__(self, batch_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found"
        )

class InsufficientPermissionsError(HTTPException):
    """Raised when user lacks required role."""
    def __init__(self, required_role: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required role: {required_role}"
        )
```

---

## **12. React Frontend Implementation**

### **12.1 Component Architecture**

**Technology Stack:**
- React 18 with TypeScript 5
- React Hook Form for form state management
- Zod for client-side validation
- TanStack Query (React Query) for API data fetching
- Tailwind CSS for styling
- `html5-qrcode` for QR scanner
- Zustand for global state (offline queue)

**Project Structure:**

```
webapp/
├── package.json
├── tsconfig.json
├── Dockerfile
├── public/
│   └── index.html
└── src/
    ├── App.tsx
    ├── main.tsx
    ├── api/
    │   ├── client.ts              # Axios instance with auth interceptor
    │   └── endpoints.ts           # API endpoint functions
    ├── components/
    │   ├── BatchDashboard.tsx     # Main batch view
    │   ├── BatchForm.tsx          # Create batch
    │   ├── CalibrationForm.tsx
    │   ├── InoculationForm.tsx
    │   ├── SampleForm.tsx
    │   ├── FailureForm.tsx
    │   ├── BatchClosureForm.tsx
    │   ├── QRScanner.tsx          # Reusable QR scanner component
    │   └── OfflineIndicator.tsx   # Shows offline status
    ├── hooks/
    │   ├── useOfflineQueue.ts     # IndexedDB queue management
    │   └── useAuth.ts             # JWT token management
    ├── stores/
    │   └── offlineStore.ts        # Zustand store for offline queue
    ├── types/
    │   └── api.ts                 # TypeScript interfaces for API
    └── utils/
        ├── validation.ts          # Zod schemas
        └── calculations.ts        # OD/DCW calculations
```

### **12.2 TypeScript Interfaces**

**File:** `src/types/api.ts`

```typescript
export interface Batch {
  id: string;
  batch_number: number;
  phase: "A" | "B" | "C";
  vessel_id: string;
  operator_id: string;
  status: "pending" | "running" | "complete" | "aborted";
  created_at: string;
  inoculated_at?: string;
  completed_at?: string;
  runtime_hours?: number;
  notes?: string;
}

export interface BatchCreate {
  batch_number: number;
  phase: "A" | "B" | "C";
  vessel_id: string;
  operator_id: string;
  notes?: string;
}

export interface Calibration {
  id: string;
  batch_id: string;
  probe_type: "pH" | "DO" | "Temp";
  buffer_low_value: number;
  buffer_low_lot?: string;
  buffer_high_value: number;
  buffer_high_lot?: string;
  reading_low: number;
  reading_high: number;
  slope_percent?: number;
  response_time_sec?: number;
  pass: boolean;
  control_active: boolean;
  calibrated_at: string;
  calibrated_by: string;
  notes?: string;
}

export interface Sample {
  id: string;
  batch_id: string;
  timepoint_hours: number;
  od600_raw: number;
  od600_dilution_factor: number;
  od600_calculated: number;
  dcw_g_per_l?: number;
  contamination_detected: boolean;
  microscopy_observations?: string;
  sampled_at: string;
  sampled_by: string;
}

export interface ApiError {
  status: "error";
  code: number;
  message: string;
  detail?: Record<string, any>;
  timestamp: string;
  path: string;
}
```

### **12.3 Example Component: Sample Form**

**File:** `src/components/SampleForm.tsx`

```typescript
import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { addSample } from '../api/endpoints';
import { QRScanner } from './QRScanner';
import { useOfflineQueue } from '../hooks/useOfflineQueue';

const sampleSchema = z.object({
  sample_volume_ml: z.number().positive().default(10),
  od600_raw: z.number().min(0),
  od600_dilution_factor: z.number().min(1).default(1),
  dcw_filter_id: z.string().optional(),
  dcw_sample_volume_ml: z.number().positive().optional(),
  contamination_detected: z.boolean().default(false),
  microscopy_observations: z.string().optional(),
  sampled_by: z.string().min(1),
});

type SampleFormData = z.infer<typeof sampleSchema>;

interface SampleFormProps {
  batchId: string;
  onSuccess: () => void;
}

export const SampleForm: React.FC<SampleFormProps> = ({ batchId, onSuccess }) => {
  const [showQRScanner, setShowQRScanner] = useState(false);
  const [scanTarget, setScanTarget] = useState<'operator' | 'filter' | null>(null);
  const { enqueue } = useOfflineQueue();
  const queryClient = useQueryClient();

  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<SampleFormData>({
    resolver: zodResolver(sampleSchema),
    defaultValues: {
      sample_volume_ml: 10,
      od600_dilution_factor: 1,
      contamination_detected: false,
    }
  });

  const mutation = useMutation({
    mutationFn: (data: SampleFormData) => addSample(batchId, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['batch', batchId]);
      onSuccess();
    },
    onError: (error: any) => {
      // If offline, add to queue
      if (!navigator.onLine) {
        enqueue({
          endpoint: `/batches/${batchId}/samples`,
          method: 'POST',
          data: mutation.variables,
        });
        alert('Offline: Sample will sync when connection restored');
        onSuccess();
      } else {
        alert(`Error: ${error.response?.data?.message || error.message}`);
      }
    }
  });

  const onSubmit = (data: SampleFormData) => {
    mutation.mutate(data);
  };

  const handleQRScan = (result: string) => {
    if (scanTarget === 'operator') {
      if (result.startsWith('USER:')) {
        setValue('sampled_by', result.replace('USER:', ''));
      } else {
        alert('Invalid operator QR code');
      }
    } else if (scanTarget === 'filter') {
      if (result.startsWith('FILTER:')) {
        setValue('dcw_filter_id', result.replace('FILTER:', ''));
      } else {
        alert('Invalid filter QR code');
      }
    }
    setShowQRScanner(false);
    setScanTarget(null);
  };

  // Auto-calculate OD600
  const od600Raw = watch('od600_raw');
  const dilutionFactor = watch('od600_dilution_factor');
  const od600Calculated = od600Raw * dilutionFactor;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 p-4">
      <h2 className="text-2xl font-bold">Add Sample Observation</h2>

      {/* Sample Volume */}
      <div>
        <label className="block font-medium">Sample Volume (ml)</label>
        <input
          type="number"
          step="0.1"
          {...register('sample_volume_ml', { valueAsNumber: true })}
          className="w-full p-2 border rounded"
        />
        {errors.sample_volume_ml && <p className="text-red-500">{errors.sample_volume_ml.message}</p>}
      </div>

      {/* OD600 */}
      <div>
        <label className="block font-medium">OD₆₀₀ Reading (raw)</label>
        <input
          type="number"
          step="0.001"
          {...register('od600_raw', { valueAsNumber: true })}
          className="w-full p-2 border rounded"
        />
        {errors.od600_raw && <p className="text-red-500">{errors.od600_raw.message}</p>}
      </div>

      {/* Dilution Factor */}
      <div>
        <label className="block font-medium">Dilution Factor</label>
        <input
          type="number"
          step="1"
          {...register('od600_dilution_factor', { valueAsNumber: true })}
          className="w-full p-2 border rounded"
        />
        <p className="text-sm text-gray-600">If undiluted, enter 1. If 10× diluted, enter 10.</p>
      </div>

      {/* Calculated OD */}
      <div className="bg-blue-50 p-3 rounded">
        <strong>Calculated OD₆₀₀:</strong> {od600Calculated.toFixed(3)}
      </div>

      {/* DCW Filter */}
      <div>
        <label className="block font-medium">DCW Filter ID (optional)</label>
        <div className="flex gap-2">
          <input
            type="text"
            {...register('dcw_filter_id')}
            className="flex-1 p-2 border rounded"
            readOnly
          />
          <button
            type="button"
            onClick={() => {
              setScanTarget('filter');
              setShowQRScanner(true);
            }}
            className="px-4 py-2 bg-blue-500 text-white rounded"
          >
            Scan QR
          </button>
        </div>
      </div>

      {/* Contamination */}
      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          {...register('contamination_detected')}
          className="w-5 h-5"
        />
        <label className="font-medium">Contamination Detected?</label>
      </div>

      {/* Microscopy */}
      <div>
        <label className="block font-medium">Microscopy Observations</label>
        <textarea
          {...register('microscopy_observations')}
          className="w-full p-2 border rounded"
          rows={3}
        />
      </div>

      {/* Sampled By */}
      <div>
        <label className="block font-medium">Sampled By</label>
        <div className="flex gap-2">
          <input
            type="text"
            {...register('sampled_by')}
            className="flex-1 p-2 border rounded"
            readOnly
          />
          <button
            type="button"
            onClick={() => {
              setScanTarget('operator');
              setShowQRScanner(true);
            }}
            className="px-4 py-2 bg-blue-500 text-white rounded"
          >
            Scan Badge
          </button>
        </div>
        {errors.sampled_by && <p className="text-red-500">{errors.sampled_by.message}</p>}
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={mutation.isLoading}
        className="w-full py-3 bg-green-500 text-white font-bold rounded disabled:bg-gray-300"
      >
        {mutation.isLoading ? 'Saving...' : 'Add Sample'}
      </button>

      {/* QR Scanner Modal */}
      {showQRScanner && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-white p-4 rounded">
            <QRScanner onScan={handleQRScan} onCancel={() => setShowQRScanner(false)} />
          </div>
        </div>
      )}
    </form>
  );
};
```

### **12.4 Offline Queue Implementation**

**File:** `src/hooks/useOfflineQueue.ts`

```typescript
import { useEffect } from 'react';
import { create } from 'zustand';
import axios from 'axios';

interface QueuedRequest {
  id: string;
  endpoint: string;
  method: 'POST' | 'PATCH' | 'DELETE';
  data: any;
  timestamp: number;
  retries: number;
}

interface OfflineStore {
  queue: QueuedRequest[];
  isOnline: boolean;
  enqueue: (req: Omit<QueuedRequest, 'id' | 'timestamp' | 'retries'>) => void;
  dequeue: (id: string) => void;
  processQueue: () => Promise<void>;
}

export const useOfflineStore = create<OfflineStore>((set, get) => ({
  queue: [],
  isOnline: navigator.onLine,

  enqueue: (req) => {
    const queuedReq: QueuedRequest = {
      ...req,
      id: crypto.randomUUID(),
      timestamp: Date.now(),
      retries: 0,
    };

    set((state) => ({
      queue: [...state.queue, queuedReq]
    }));

    // Persist to IndexedDB
    saveQueueToIndexedDB(get().queue);
  },

  dequeue: (id) => {
    set((state) => ({
      queue: state.queue.filter((req) => req.id !== id)
    }));
    saveQueueToIndexedDB(get().queue);
  },

  processQueue: async () => {
    const { queue, dequeue } = get();

    for (const req of queue) {
      try {
        await axios({
          method: req.method,
          url: `/api/v1${req.endpoint}`,
          data: req.data,
        });

        dequeue(req.id);
        console.log(`✅ Synced offline request: ${req.endpoint}`);
      } catch (error) {
        console.error(`❌ Failed to sync: ${req.endpoint}`, error);

        // Retry with exponential backoff (max 5 retries)
        if (req.retries < 5) {
          setTimeout(() => get().processQueue(), 2 ** req.retries * 1000);
        }
      }
    }
  }
}));

export const useOfflineQueue = () => {
  const { enqueue, processQueue, isOnline } = useOfflineStore();

  useEffect(() => {
    const handleOnline = () => {
      useOfflineStore.setState({ isOnline: true });
      processQueue();
    };

    const handleOffline = () => {
      useOfflineStore.setState({ isOnline: false });
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Process queue on mount if online
    if (navigator.onLine) {
      processQueue();
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [processQueue]);

  return { enqueue, isOnline };
};

// IndexedDB persistence
async function saveQueueToIndexedDB(queue: QueuedRequest[]) {
  const db = await openDB();
  const tx = db.transaction('queue', 'readwrite');
  await tx.objectStore('queue').put({ id: 'queue', data: queue });
  await tx.done;
}

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('PichiaOfflineDB', 1);

    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains('queue')) {
        db.createObjectStore('queue', { keyPath: 'id' });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}
```

---

## **13. Deployment & Configuration**

### **13.1 Docker Compose Configuration**

**File:** `docker-compose.yml` (add to edge stack)

```yaml
version: '3.8'

services:
  # PostgreSQL for manual data
  postgres:
    image: postgres:15-alpine
    container_name: pichia-postgres
    environment:
      POSTGRES_DB: pichia_manual_data
      POSTGRES_USER: pichia_api
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/01-schema.sql:ro
    ports:
      - "5432:5432"
    networks:
      - pichia-net
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pichia_api"]
      interval: 10s
      timeout: 5s
      retries: 5

  # FastAPI Backend
  api:
    build: ./api
    container_name: pichia-api
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_DB: pichia_manual_data
      POSTGRES_USER: pichia_api
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      ALLOWED_ORIGINS: ${ALLOWED_ORIGINS}
    ports:
      - "8000:8000"
    networks:
      - pichia-net
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # React Frontend (Nginx)
  webapp:
    build: ./webapp
    container_name: pichia-webapp
    ports:
      - "3000:80"
    networks:
      - pichia-net
    depends_on:
      - api
    restart: unless-stopped

networks:
  pichia-net:
    driver: bridge

volumes:
  postgres_data:
```

### **13.2 FastAPI Dockerfile**

**File:** `api/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Run database migrations on startup
CMD alembic upgrade head && \
    uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### **13.3 React Dockerfile (Production)**

**File:** `webapp/Dockerfile`

```dockerfile
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built React app to nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**File:** `webapp/nginx.conf`

```nginx
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # React SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to FastAPI
    location /api/ {
        proxy_pass http://api:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Enable gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
```

### **13.4 Database Initialization**

**File:** `database/init.sql` (already created, referenced in docker-compose)

This file should contain the complete schema from Technical Plan Sec 4.4.

### **13.5 Deployment Checklist**

**Pre-Deployment:**
- [ ] Copy `.env.example` to `.env` and fill in all secrets
- [ ] Generate strong JWT secret key: `openssl rand -base64 64`
- [ ] Generate strong Postgres password: `openssl rand -base64 32`
- [ ] Review CORS allowed origins (tablet IPs)
- [ ] Test all forms on development stack

**Initial Deployment:**
```bash
# On Jetson AGX Orin
cd bioprocess-twin/edge

# Load environment variables
source .env

# Build and start services
docker-compose up -d postgres api webapp

# Verify services are healthy
docker-compose ps
docker-compose logs -f api

# Test API health
curl http://localhost:8000/health

# Test web app
curl http://localhost:3000
```

**Post-Deployment:**
- [ ] Create initial admin user via API
- [ ] Test full workflow on tablet (mock batch)
- [ ] Configure daily Postgres backup cron job
- [ ] Set up Grafana alert for API downtime

---

## **14. Performance Requirements**

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **API Response Time** (GET) | < 200 ms (P95) | Prometheus histogram |
| **API Response Time** (POST) | < 500 ms (P95) | Prometheus histogram |
| **Form Submission Time** | < 2 s (user perception) | Frontend timing |
| **Offline Sync Time** | < 30 s after reconnect | Integration test |
| **Database Query Time** | < 100 ms (P95) | PostgreSQL slow query log |
| **Concurrent Users** | Support 5 simultaneous technicians | Load testing (Locust) |
| **Data Storage Growth** | ~500 MB per 18-batch campaign | Monitor disk usage |

**Monitoring Stack:**
- Prometheus for metrics collection
- Grafana dashboard for API performance
- PostgreSQL `pg_stat_statements` for query analysis

---

## **15. Testing Strategy**

### **15.1 Unit Tests (FastAPI)**

**File:** `api/tests/test_batches.py`

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_batch_success():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/batches",
            json={
                "batch_number": 1,
                "phase": "A",
                "vessel_id": "V-01",
                "operator_id": "USER:T001",
                "notes": "Test batch"
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

    assert response.status_code == 201
    data = response.json()
    assert data["batch_number"] == 1
    assert data["status"] == "pending"

@pytest.mark.asyncio
async def test_create_batch_duplicate():
    """Test that duplicate batch numbers are rejected."""
    # Create first batch
    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post("/api/v1/batches", json={...})

        # Try to create duplicate
        response = await client.post("/api/v1/batches", json={...})

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]
```

### **15.2 Integration Tests (Full Workflow)**

**File:** `api/tests/test_workflow.py`

```python
@pytest.mark.asyncio
async def test_full_batch_workflow():
    """Test complete batch lifecycle: create → media → calibration → inoculation → sample → close."""

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Step 1: Create batch
        batch_response = await client.post("/api/v1/batches", json={...})
        batch_id = batch_response.json()["id"]

        # Step 2: Add media prep
        await client.post(f"/api/v1/batches/{batch_id}/media", json={...})

        # Step 3: Add calibrations (pH, DO, Temp)
        for probe_type in ["pH", "DO", "Temp"]:
            await client.post(f"/api/v1/batches/{batch_id}/calibrations", json={
                "probe_type": probe_type,
                "pass": True,
                ...
            })

        # Step 4: Inoculate
        inoc_response = await client.post(f"/api/v1/batches/{batch_id}/inoculation", json={
            "go_decision": True,
            ...
        })
        assert inoc_response.status_code == 201

        # Step 5: Add 8 samples
        for i in range(8):
            await client.post(f"/api/v1/batches/{batch_id}/samples", json={...})

        # Step 6: Close batch
        close_response = await client.post(f"/api/v1/batches/{batch_id}/close", json={
            "outcome": "Complete",
            ...
        })
        assert close_response.status_code == 200

        # Verify batch is locked
        batch = await client.get(f"/api/v1/batches/{batch_id}")
        assert batch.json()["status"] == "complete"
```

### **15.3 Frontend Tests (React)**

**File:** `webapp/src/components/__tests__/SampleForm.test.tsx`

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { SampleForm } from '../SampleForm';

test('calculates OD600 correctly', () => {
  render(<SampleForm batchId="test-id" onSuccess={() => {}} />);

  const od600Input = screen.getByLabelText(/OD₆₀₀ Reading/i);
  const dilutionInput = screen.getByLabelText(/Dilution Factor/i);

  fireEvent.change(od600Input, { target: { value: '0.5' } });
  fireEvent.change(dilutionInput, { target: { value: '10' } });

  const calculatedOD = screen.getByText(/Calculated OD₆₀₀:/i);
  expect(calculatedOD).toHaveTextContent('5.000');
});

test('shows error when OD is negative', () => {
  render(<SampleForm batchId="test-id" onSuccess={() => {}} />);

  const od600Input = screen.getByLabelText(/OD₆₀₀ Reading/i);
  fireEvent.change(od600Input, { target: { value: '-1' } });

  const submitButton = screen.getByRole('button', { name: /Add Sample/i });
  fireEvent.click(submitButton);

  expect(screen.getByText(/must be greater than or equal to 0/i)).toBeInTheDocument();
});
```

### **15.4 Load Testing**

**File:** `tests/load_test.py` (using Locust)

```python
from locust import HttpUser, task, between

class PichiaAPIUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Login and get JWT token."""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "test_tech",
            "password": "test_pass"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def list_batches(self):
        self.client.get("/api/v1/batches", headers=self.headers)

    @task(1)
    def get_batch_detail(self):
        self.client.get("/api/v1/batches/test-batch-id", headers=self.headers)

    @task(2)
    def add_sample(self):
        self.client.post("/api/v1/batches/test-batch-id/samples", json={
            "od600_raw": 1.5,
            "od600_dilution_factor": 1.0,
            "contamination_detected": False,
            "sampled_by": "USER:T001"
        }, headers=self.headers)

# Run with: locust -f tests/load_test.py --host=http://localhost:8000
# Target: 5 concurrent users, 0% error rate, P95 < 500ms
```

---

## **16. Maintenance & Operations**

### **16.1 Backup Strategy**

**Daily Postgres Backup:**

```bash
#!/bin/bash
# File: scripts/backup_postgres.sh

BACKUP_DIR="/mnt/backup/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/pichia_manual_data_$TIMESTAMP.sql.gz"

# Create backup
docker exec pichia-postgres pg_dump -U pichia_api pichia_manual_data | gzip > $BACKUP_FILE

# Keep only last 30 days of backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

# Upload to MinIO (optional)
mc cp $BACKUP_FILE minio/pichia-backups/

echo "✅ Backup completed: $BACKUP_FILE"
```

**Cron Job:**

```bash
# Add to crontab on Jetson
# Run daily backup at 2 AM
0 2 * * * /home/admin/bioprocess-twin/scripts/backup_postgres.sh >> /var/log/postgres_backup.log 2>&1
```

### **16.2 Log Rotation**

**File:** `/etc/logrotate.d/pichia-api`

```
/var/log/pichia/api.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        docker exec pichia-api kill -USR1 1
    endscript
}
```

### **16.3 Health Check Endpoints**

**File:** `app/main.py`

```python
@app.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/health/db")
async def database_health(db: AsyncSession = Depends(get_db)):
    """Check database connectivity."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Kubernetes readiness probe."""
    try:
        # Check database
        await db.execute(text("SELECT 1"))

        # Check that migrations are up-to-date
        # (Implementation depends on Alembic)

        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Service not ready")
```

**Grafana Alert:**

```yaml
# Alert if API is down for >1 minute
alert: PichiaAPIDown
expr: up{job="pichia-api"} == 0
for: 1m
labels:
  severity: critical
annotations:
  summary: "Pichia API is down"
  description: "API has been unreachable for 1 minute"
```

---

**End of Manual Data Development Guide v2.1**
