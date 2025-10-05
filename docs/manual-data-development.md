# Manual Data Development Guide
## Pichia pastoris Digital Shadow – Electronic Lab Notebook

**Version:** 2.0
**Purpose:** Define the batch-centric electronic lab notebook schema and API for manual data collection
**Last Updated:** October 5, 2025

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
- Repeats for each probe (pH, DO, Temp)
- System auto-calculates slope% for pH
- **Quality Gate:** If pH slope <95%, system blocks inoculation step

---

### **Phase 2: Inoculation (T=0)**

**Step 4: Quality Check Inoculum**
- Technician measures seed flask OD₆₀₀ and performs microscopy
- From Batch Dashboard, selects "Add Inoculation"
- Fills in: Cryo-vial ID, OD₆₀₀, microscopy observations
- **GO/NO-GO Decision:** Technician must check "GO" to proceed
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

**End of Manual Data Development Guide**
