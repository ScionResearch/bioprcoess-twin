# Experimental Campaign Plan: 18-Batch Digital Shadow Training Series

## Document Control

**Organism:** _Pichia pastoris_ (Strain: TBD, e.g., X-33)  
**Process Type:** Glycerol Batch Phase for Biomass Accumulation  
**Document Version:** 1.0  
**Lead Process Engineer:** (Name)  
**Date Issued:** (Date)  
**Review Date:** (Date)

---

## 1.0 Campaign Objective

To execute a series of **18 highly consistent glycerol batch fermentations** of _Pichia pastoris_ for the purpose of generating a high-quality, comprehensive dataset suitable for training and validating a digital shadow model.

**Critical Success Factor:** Consistency in protocol execution is paramount to minimize process variance not attributable to biological factors. This plan operationalizes the parameters outlined in the Invitrogen _Pichia_ Fermentation Process Guidelines.

**Primary Deliverable:** A validated dataset capturing the complete glycerol batch phase dynamics including:

- High-resolution online process parameters (temperature, pH, DO, agitation, gas flow)
- Time-series offline measurements (OD₆₀₀, DCW, microscopy)
- Complete process metadata (calibrations, media composition, inoculum quality)

---

## 2.0 Campaign Structure & Phasing Strategy

The 18 batches will be executed in **three distinct phases** to allow for iterative learning, process optimization, and proper model validation.

### **Phase A: Shakedown, Correlation & Control Commissioning (Batches 1-3)**

**Primary Goals:**

- Validate all equipment functionality and sensor connections
- Establish robust data logging infrastructure
- Validate the manual data entry (tablet form) workflow
- **Commission and validate new control system (Batches 2-3)**
- **Establish a robust correlation between online OD₆₀₀ and offline Dry Cell Weight (DCW)**
- Identify and resolve any procedural ambiguities

**Execution Strategy:**

- Run batches **sequentially** in single 1L bioreactor
- Allow minimum 48-hour interval between batches for post-run analysis
- Conduct team debriefs after each batch to capture learnings
- Finalize and lock the SOP before proceeding to Phase B

**Batch 1 - Baseline (Set-Point Operation, No Control):**
- Temperature: Monitor only (manual heater adjustment if drift)
- pH: Set initial to 5.0, then monitor without control (natural drift expected)
- Agitation: Fixed at 500 rpm
- Aeration: Fixed at 1.0 vvm air
- DO: Monitor only
- **Purpose:** Establish baseline process behavior without automated control; validate workflow

**Batches 2-3 - Control System Validation:**
- **NEW control system commissioned** (base pump, temperature PID, DO cascade)
- Temperature: PID control to 30.0°C ± 0.3°C
- pH: PID control to 5.0 ± 0.1 via 28% NH₄OH addition
- DO: Cascade control (agitation 500-1000 rpm, O₂ enrichment if needed)
- **Purpose:** Validate control hardware/software, establish controlled process variability

**Key Deliverables:**

- Validated OD₆₀₀-to-DCW correlation curve (R² > 0.95 required)
- Confirmed sensor performance and calibration procedures
- **Control system validation report (Batches 2-3)**
- Process variability assessment (CV) with and without control
- Updated SOP with finalized control strategy

---

### **Phase B: Data Accumulation (Batches 4-15)**

**Primary Goal:** Generate the **core training dataset** for digital twin model development

**Execution Strategy:**

- Run batches **sequentially** in the same 1L bioreactor with validated control system
- Maintain **strict adherence** to the finalized and locked SOP with **controlled variation** (see below)
- Implement real-time quality checks at each sampling timepoint
- No protocol deviations permitted without formal approval
- **Control system must remain locked to Batch 2-3 validated configuration**

**Controlled Variation Strategy (NEW - Based on Gasset et al. 2024):**

To improve model generalization and avoid overfitting, **intentionally vary non-critical parameters** within safe operating ranges across Phase B batches:

**Batches 4-6: Baseline Consistency**
- Execute with nominal parameters (30.0°C, pH 5.0, 500 rpm initial agitation, inoculum OD 4.0)
- Establishes reference performance for controlled variation comparison

**Batches 7-9: Temperature Variation**
- Batch 7: 29.0°C (nominal - 1°C)
- Batch 8: 30.0°C (nominal)
- Batch 9: 31.0°C (nominal + 1°C)
- **Rationale**: Captures seasonal thermal variations; tests model robustness to temperature drift

**Batches 10-12: Inoculum Variation**
- Batch 10: Inoculum OD 2.5 (low end of acceptable range)
- Batch 11: Inoculum OD 4.0 (nominal)
- Batch 12: Inoculum OD 6.0 (high end of acceptable range)
- **Rationale**: Simulates batch-to-batch seed culture variability; improves prediction of different growth trajectories

**Batches 13-15: Stress Testing (Controlled Disturbances)**
- Batch 13: **Temperature spike test**: At T=8h, increase temperature to 32°C for 30 minutes, then return to 30°C
- Batch 14: **Agitation step test**: At T=6h, reduce agitation from 500 rpm to 400 rpm for 1 hour, then return
- Batch 15: **pH offset test**: Start batch at pH 5.3 (instead of 5.0), allow control to stabilize
- **Rationale**: Based on Gasset et al. disturbance testing (O₂-enriched air injection). Tests model recovery and robustness before final hold-out validation.

**Documentation Requirements:**
- All controlled variations must be logged in `PROCESS_CHANGE` tablet form
- Variation must be approved by Process Engineer before batch start
- Label batches with variation type in metadata (e.g., "Temp_Low", "Inoc_High", "Stress_TempSpike")

**Quality Assurance:**
- Controlled variations do NOT constitute deviations (they are planned experiments)
- All other quality gates (sterility, data completeness, sensor performance) remain enforced
- If a stress test batch results in Level 3 deviation (e.g., DO crash, contamination), **exclude from training set** and repeat the batch

**Data Quality Requirements:**

- All batches must complete the full glycerol depletion cycle
- No contamination events
- All mandatory tablet forms completed within 2 hours of sampling
- Sensor data continuity >99% (minimal dropouts)

**Expected Output:** 12 high-quality batch datasets spanning biological variability, technical replicates, and controlled process variations

**Phase A Feasibility Gate (CRITICAL):**

After completion of Batches 1-3, conduct statistical analysis to establish process capability:

- Calculate coefficient of variation (CV) for OD₆₀₀ and DCW across all timepoints
- Measure batch-to-batch variability in glycerol depletion time
- Assess sensor drift and calibration stability
- **Set realistic MRE target = 2× Process CV** (industry heuristic)
- **Adaptive Target Decision**: If CV < 5%, consider tightening MRE target from 8% to 6% as primary goal
- Document baseline variability in Phase A analysis report

**Rationale:** Gasset et al. (2024) achieved MRE 3.5-4.0% on a more complex fed-batch RQ control process. If our glycerol batch shows low inherent variability (CV <5%), the simpler process may allow better accuracy than the conservative 8% target.

**Go/No-Go Decision:** If CV >5%, consider extending Phase A with additional batches to improve process consistency before proceeding to Phase B.

---

### **Phase C: Validation & Hold-Out (Batches 16-18)**

**Primary Goal:** Generate a **clean hold-out dataset** for final model validation

**Critical Requirement:** These batches **must NOT be used** in any model training activities. They serve exclusively for independent model validation.

**Execution Strategy:**

- Run batches **sequentially** in the same 1L bioreactor with validated control system
- **Batches 16-18 return to nominal conditions** (30.0°C, pH 5.0, inoculum OD 4.0) to match baseline
- Independent operator verification of all manual measurements
- Duplicate sample analysis for critical timepoints (0h, 8h, endpoint)
- Real-time data review by Process Engineer and ML Engineer

**Diversity Requirements (for Robust Validation):**

To ensure hold-out batches test model generalization across realistic process variation:

- **Batch 16**: Run with fresh media lot (if available) and different cryovial from cell bank
- **Batch 17**: Run by alternate trained operator (if available) to capture operator variability
- **Batch 18**: Run after planned equipment maintenance (e.g., probe replacement, if scheduled)

**Rationale**: Hold-out validation should span realistic sources of variation (media lots, operators, seasonal effects) to test model robustness in production use. Based on Gasset et al. validation approach across biological replicates.

**Quality Gates:**

- Zero tolerance for protocol deviations
- Mandatory peer review of all data entry before batch closure
- Independent calibration verification before each run

---

## 3.0 Standard Operating Procedure (SOP) for a Single Batch Run

**CRITICAL:** This SOP is to be followed for **all 18 batches** unless a deviation is explicitly approved by the Lead Process Engineer and logged in the deviation management system.

---

### **3.1 Pre-Run: Vessel & Media Preparation**

#### **3.1.1 Bioreactor Vessel Preparation**

**Equipment:** 2L bioreactor vessel with associated sensors and controllers

1. **Cleaning Protocol:**
    
    - Disassemble all vessel components and inspect for residue or damage
    - Clean with alkaline detergent (e.g., 1% Alconox) at 60°C for 30 minutes
    - Rinse thoroughly with WFI (Water for Injection) - minimum 5 rinse cycles
    - Inspect all O-rings and replace if showing wear (>10 uses)
    - Reassemble vessel according to manufacturer specifications
2. **pH Probe Calibration (Two-Point Method):**

    - **Buffers Required:** pH 4.01 and pH 7.00 (NIST traceable)
    - Rinse probe with deionized water and blot dry (do not wipe)
    - Immerse in pH 7.00 buffer, allow 2 minutes for stabilization
    - Calibrate first point, record reading
    - Rinse and immerse in pH 4.01 buffer, allow 2 minutes for stabilization
    - Calibrate second point, record reading
    - **Calculate slope:** Must be **>95%** (typically 95-102%)
    - **Log in `CALIBRATION` tablet form:** Buffer lot numbers, readings, slope %, temperature, operator ID, timestamp
    - **Action if failed:** Replace probe or buffers and recalibrate. Do NOT proceed with batch if slope <95%
3. **Dissolved Oxygen (DO) Probe Calibration (Two-Point Method):**

    - Install probe in vessel
    - Set temperature to operating point (30°C) and agitation to operating speed (500 rpm)
    - **0% Calibration:** Sparge with Nitrogen gas for 15 minutes until stable, calibrate zero point
    - **100% Calibration:** Sparge with air at 1.0 vvm for 15 minutes until stable, calibrate span point
    - **Log in `CALIBRATION` tablet form:** Gas lot numbers, temperature, agitation, readings, operator ID, timestamp
    - Verify response time: Should reach 63% of step change in <30 seconds
4. **Off-Gas Sensor Calibration (Two-Point Method - Custom CO₂ and O₂ Sensors):**

    - **0% Calibration (O₂ zero, CO₂ zero):**
        - Bypass reactor and flow pure N₂ through off-gas sensor housing at 1.0 L/min for 10 minutes
        - Calibrate O₂ sensor zero point (should read 0.0% ± 0.1%)
        - Calibrate CO₂ sensor zero point (should read 0.0% ± 0.1%)
    - **Span Calibration:**
        - Flow room air through sensor housing at 1.0 L/min for 10 minutes
        - Calibrate O₂ sensor span point (should read 20.9% ± 0.2%)
        - Verify CO₂ sensor reads atmospheric CO₂ (~0.04%, typically <0.1%)
    - **Log in `CALIBRATION` tablet form:** Gas lot/source, pre-cal readings, post-cal readings, drift from previous calibration, operator ID, timestamp
    - **Pass Criteria:**
        - O₂ drift from previous calibration: <0.2%
        - CO₂ drift from previous calibration: <0.2%
        - Calibration stability: readings stable within ±0.05% for 5 minutes
    - **Action if failed:**
        - Clean sensors (remove dust, condensation)
        - Replace sensors if drift >0.2% for two consecutive calibrations
        - **Critical Flag:** If >20% of batches require sensor replacement or show RSD >5% on validation gas, activate contingency plan for integrated analyzer upgrade (BlueSens BlueInOne FERM, ~$5K)
5. **Reactor Pressure Transducer Verification:**

    - Zero transducer at atmospheric pressure (vessel open to atmosphere)
    - Verify reading: 0.000 ± 0.005 bar gauge pressure (or 1.013 bar absolute)
    - **Log in `CALIBRATION` tablet form:** Zero reading, atmospheric pressure (from weather station or barometer), operator ID
    - **Note:** Pressure transducer provides mass balance closure and gas density correction for CER/OUR calculations
4. **Final Vessel Check:**
    
    - Confirm all sensors are properly connected to control system
    - Verify data logging channels are active
    - Test all pumps (acid, base, antifoam) - run for 5 seconds each
    - Confirm vessel QR code is scannable and linked in system

---

#### **3.1.2 Fermentation Medium Preparation**

**Recipe:** Fermentation Basal Salts Medium (per Invitrogen guidelines, p. 11)  
**Target Volume:** 1L (final working volume after inoculation)  
**Preparation Volume:** 900 mL (leaving 100 mL headspace for inoculum and pH adjustments)

**Components (per 1L final volume):**

|Component|Amount|Notes|
|---|---|---|
|Phosphoric acid, 85%|26.7 mL|**CAUTION:** Add slowly, exothermic reaction|
|Calcium sulfate (CaSO₄·2H₂O)|0.93 g|Dissolves slowly, ensure complete dissolution|
|Potassium sulfate (K₂SO₄)|18.2 g||
|Magnesium sulfate heptahydrate (MgSO₄·7H₂O)|14.9 g||
|Potassium hydroxide (KOH)|4.13 g||
|Glycerol (99.5% pure)|40.0 g (~31.7 mL)|Primary carbon source|
|Deionized water (dH₂O)|To 900 mL||

**Preparation Procedure:**

1. **Weighing Protocol:**
    
    - Use calibrated analytical balance (±0.01 g accuracy)
    - Tare vessel before each component addition
    - **Log all weights and lot numbers** in the `MEDIA` tablet form
    - Scan vessel QR code to link media batch to reactor run
    - Have second operator verify weights for critical components (glycerol, salts)
2. **Mixing Sequence:**
    
    - Add approximately 600 mL dH₂O to mixing vessel
    - Add phosphoric acid **slowly** while stirring (exothermic!)
    - Add salts in order listed above, ensuring each dissolves before adding next
    - Add glycerol and mix thoroughly
    - Add dH₂O to bring volume to **900 mL** (measured with graduated cylinder ±10 mL)
3. **Quality Check:**
    
    - Final pH should be approximately 3.0-4.0 (will be adjusted to 5.0 after sterilization)
    - Medium should be clear with no visible precipitate
    - If precipitate present, dissolve by warming to 40°C with stirring
4. **Transfer to Vessel:**
    
    - Aseptically transfer medium to bioreactor vessel
    - Confirm final volume: 900 mL ±10 mL
    - Double-check all vessel ports are sealed
5. **Sterilization:**
    
    - Autoclave vessel with medium at **121°C for 30 minutes** (liquid cycle)
    - Allow to cool to room temperature (minimum 4 hours)
    - Verify sterility indicators (autoclave tape color change)
    - **Log autoclave cycle number** and verification in `MEDIA` form

---

### **3.2 Pre-Run: Inoculum Seed Flask Preparation**

**Timing:** Prepare **24-30 hours before** planned inoculation time

#### **3.2.1 Seed Culture Initiation**

**Flask Setup:**

- Use 1L baffled Erlenmeyer flask (sterile)
- Prepare 100 mL BMGY medium (Buffered Glycerol-complex Medium)
- BMGY composition per Invitrogen protocol:
    - 1% Yeast extract
    - 2% Peptone
    - 100 mM potassium phosphate buffer, pH 6.0
    - 1.34% YNB (Yeast Nitrogen Base)
    - 1% Glycerol

**Inoculation Source (select one):**

- **Option A:** Single colony from fresh YPD plate (streaked <7 days prior)
- **Option B:** 1 mL from frozen glycerol stock (stored at -80°C)

**Log in `INOCULATION` tablet form:**

- Source type and identifier (plate ID or cryovial ID)
- Inoculation date and time
- Operator name

**Incubation Conditions:**

- Temperature: **30°C ± 0.5°C**
- Shaking: **250-300 rpm** (orbital shaker)
- Duration: **18-24 hours**
- Target: Exponential phase culture with OD₆₀₀ = 2.0-6.0

---

#### **3.2.2 Inoculum Quality Check**

**Timing:** Perform **1 hour before** planned reactor inoculation

**Procedure:**

1. **Optical Density Measurement:**
    
    - Aseptically collect 1 mL sample from seed flask
    - Measure OD₆₀₀ using spectrophotometer (blanked with BMGY medium)
    - If OD₆₀₀ > 1.0, dilute sample **10-fold** in fresh BMGY for accurate reading (linear range 0.1-1.0)
    - Calculate actual OD₆₀₀ = reading × dilution factor
    - **Target Range: 2.0 - 6.0**
2. **Microscopic Examination:**
    
    - Prepare wet mount slide
    - Examine at 400× magnification
    - Confirm: Single-cell yeast morphology, no visible contaminants (bacteria, fungi)
    - Estimate viability: >90% of cells should appear turgid with clear cytoplasm
3. **Volume Verification:**
    
    - Confirm culture volume ≥100 mL (required for 10% v/v inoculation)
4. **Documentation:**
    
    - **Log in `INOCULATION` tablet form:**
        - Final measured OD₆₀₀
        - Dilution factor (if applicable)
        - Cryovial/plate ID
        - Microscopy observations
        - Operator name and timestamp
        - GO/NO-GO decision

**GO/NO-GO Criteria:**

- ✅ GO if: OD₆₀₀ = 2.0-6.0, microscopy clean, volume sufficient
- ❌ NO-GO if: OD₆₀₀ out of range, contamination visible, insufficient volume
    - Action: Use backup inoculum or postpone run
    - Log failure in `FAILURE` form

---

### **3.3 Batch Start-up & Inoculation**

#### **3.3.1 Fermenter Parameter Initialization**

**Temperature Control:**

- Reduce vessel temperature to **30.0°C ± 0.2°C**
- Confirm stable for ≥15 minutes before inoculation
- Verify heating/cooling control is responding properly

**Agitation:**

- Set initial agitation to **500 rpm**
- Confirm impeller rotation direction (check vessel manual)
- Verify no unusual vibration or noise

**Aeration:**

- Set air flow to **1.0 vvm** (volume of gas per volume of liquid per minute)
    - For 1L culture: 1.0 L/min
    - For 0.9L pre-inoculation volume: 0.9 L/min (adjust to 1.0 L/min after inoculation)
- Verify air is filtered through 0.22 μm sterile filter
- Confirm gas flow controller calibration is current (<30 days old)

---

#### **3.3.2 Aseptic Additions**

**PTM₁ Trace Salts Solution:**

- Volume: **4.35 mL per liter** of final culture volume
- For 1L culture: Add 4.35 mL
- Preparation: Filter-sterilize using 0.22 μm syringe filter
- Addition method: Aseptic syringe injection through septum port
- **Log lot number and volume** in `MEDIA` form

**pH Adjustment to 5.0:**

- Use **28% Ammonium hydroxide (NH₄OH)** - sterile filtered
- Add slowly via aseptic syringe or sterile base pump
- Target pH: **5.0 ± 0.1**
- Monitor pH continuously during addition
- This establishes the starting pH; automated control will maintain during run

**Final Pre-Inoculation Checks:**

- Confirm all additions logged
- Verify vessel temperature stable at 30°C
- Verify all control loops (pH, DO, temperature) are active
- Confirm data logging is ready

---

#### **3.3.3 Inoculation & Batch Initiation**

**Inoculation Procedure:**

1. **Transfer:**
    
    - Aseptically transfer **100 mL** of validated seed culture into fermenter
    - Inoculation ratio: **10% v/v** (100 mL into 900 mL = 1000 mL total)
    - Use sterile technique: flame transfer port, use sterile pipette/tubing
2. **Final Volume Confirmation:**
    
    - Total starting volume: **1.0 L ± 0.02 L**
    - Verify liquid level marking on vessel
3. **Batch Start:**
    
    - **Immediately** after inoculation completion:
        - Press "Start Batch" button in control system
        - Click "Start Batch" on master project dashboard
        - Record exact start time in `INOCULATION` form
    - Verify all sensors begin logging data
    - Confirm baseline readings are reasonable:
        - Temperature: 30.0°C
        - pH: 5.0
        - DO: ~100% (will drop as cells begin respiring)
        - Agitation: 500 rpm
4. **Initial Observation Period:**
    
    - Monitor for first 30 minutes post-inoculation
    - Expected: DO should begin declining within 15-30 minutes as cells begin consuming oxygen
    - pH should remain stable (base pump inactive initially)

**Time Zero (T=0) Sample:**

- Immediately after inoculation, collect **10 mL sample**
- Process as per Section 3.4.2 (manual sampling protocol)
- This establishes baseline OD₆₀₀ and DCW

---

### **3.4 In-Run Monitoring & Control (Glycerol Batch Phase)**

**Phase Duration:** Approximately **18-24 hours** (ends at glycerol depletion)

---

#### **3.4.1 Automated Control Setpoints**

**CRITICAL:** Control strategy differs between Batch 1 (baseline) and Batches 2-18 (controlled).

---

**BATCH 1 ONLY: Set-Point Operation (No Automated Control)**

All parameters are **set at batch start** and **monitored without feedback control**:

|Parameter|Setpoint|Control Method|Notes|
|---|---|---|---|
|**Temperature**|30.0°C|Manual heater setpoint|Monitor for drift; adjust manually if >±0.5°C|
|**pH**|5.0 (initial)|None - natural drift|Expect pH to rise as NH₃ assimilated; document drift profile|
|**Dissolved Oxygen**|N/A|None - monitoring only|Fixed aeration at 1.0 vvm; expect DO to drop during growth|
|**Agitation**|500 rpm|Fixed speed|No cascade adjustments|
|**Aeration**|1.0 vvm air|Fixed flow|No O₂ enrichment|

**Expected Behavior (Batch 1):**
- pH will drift upward (5.0 → 6.0-7.0 expected) as cells assimilate nitrogen
- DO will drop from ~100% to 20-40% during exponential growth
- If DO <20% observed, **log as deviation** but continue batch (this informs control strategy)
- **Document all excursions** - this establishes the need for control in Batches 2+

---

**BATCHES 2-18: Automated Control (Control System Validated)**

**These parameters are locked for Batches 2-18**. No adjustments permitted without formal deviation approval.

|Parameter|Setpoint|Control Method|Acceptable Range|
|---|---|---|---|
|**Temperature**|30.0°C|PID control via heating/cooling jacket|30.0 ± 0.3°C|
|**pH**|5.0|PID control via 28% NH₄OH addition|5.0 ± 0.1|
|**Dissolved Oxygen (DO)**|>20%|Cascade control (see below)|Must remain >20%|
|**Agitation**|500 rpm (initial)|Part of DO cascade|500-1000 rpm|
|**Aeration**|1.0 vvm air (initial)|Part of DO cascade|1.0 vvm air ± O₂ supplement|

---

**Dissolved Oxygen (DO) Cascade Control Strategy (Batches 2-18):**

The DO setpoint of **>20%** is the **primary control challenge**. A cascade control strategy is implemented:

**Stage 1: Agitation Control (Primary)**

- If DO drops below 20%, agitation automatically increases
- Agitation range: **500 → 1000 rpm**
- Step increment: 50 rpm
- Control algorithm: PID with anti-windup

**Stage 2: Oxygen Enrichment (Secondary - Avoid if Possible)**

- If DO remains <20% despite agitation at 1000 rpm
- Pure O₂ can be added to gas mix (air + O₂)
- Maximum O₂ addition: **0.3 vvm**
- **Important:** O₂ enrichment should be avoided to maintain consistency
- **Any O₂ usage must be logged as a process deviation** in `FAILURE` form

**DO Monitoring Requirements:**

- Log DO value every 60 seconds minimum
- Set alarm if DO <20% for >5 minutes
- Set critical alarm if DO <15% for >2 minutes

---

**pH Control Details (Batches 2-18):**

- Automated addition of **28% NH₄OH** (ammonium hydroxide)
- Pump: Peristaltic, calibrated flow rate
- Control mode: PID
- **Log cumulative base addition volume** in control system
- Expected behavior:
    - Minimal base addition in first 6-8 hours
    - Increased addition as ammonia assimilation increases
    - Total consumption typically 20-40 mL per batch

**Temperature Control (Batches 2-18):**

- Jacket temperature controlled via external circulator
- Heating and cooling capacity should be balanced
- Expected: Minimal heating required; fermentation is exothermic at high cell density

---

#### **3.4.2 Manual Data Collection & Sampling Protocol**

**Sampling Schedule (Mandatory Timepoints):**

|Timepoint|Sample Volume|Priority|Notes|
|---|---|---|---|
|**T = 0h**|10 mL|Critical|Immediately post-inoculation|
|**T = 2h**|10 mL|High|Early exponential phase|
|**T = 4h**|10 mL|High|Mid exponential phase|
|**T = 6h**|10 mL|High|Late exponential phase|
|**T = 8h**|10 mL|High|Transition phase|
|**T = 12h**|10 mL|Medium|Late batch phase|
|**T = 16h**|10 mL|Medium|Pre-depletion phase|
|**Glycerol Depletion**|10 mL|Critical|Triggered by DO spike|

**Sampling Tolerance:** ±15 minutes for scheduled timepoints

---

**Sample Collection Procedure:**

1. **Aseptic Sampling:**
    
    - Collect **10 mL** sample via sterile sampling port
    - Use sterile syringe or automated sampling system
    - Minimize air introduction to vessel
    - Collect sample into sterile 15 mL centrifuge tube
2. **Immediate Sample Processing (use `SAMPLE` tablet form):**
    
    **A. Optical Density Measurement:**
    
    - Measure **OD₆₀₀** within 5 minutes of sampling
    - If OD > 1.0, dilute sample (typically 10× or 100×) for accurate reading
    - Blank: Sterile fermentation medium
    - Record: OD₆₀₀ reading, dilution factor, calculated OD
    - **Target range for undiluted reading: 0.1-1.0 AU**
    
    **B. Microscopic Purity Check:**
    
    - Aliquot: **1 mL** for microscopy
    - Prepare wet mount slide
    - Examine at 400× magnification
    - Document:
        - Cell morphology (normal/abnormal)
        - Contaminants (present/absent)
        - Culture purity (clean/contaminated)
    - **Action if contaminated:** Immediately abort batch, log in `FAILURE` form
    
    **C. Dry Cell Weight (DCW) Analysis:**
    
    - Filter volume: **5 mL** (record exact volume)
    - Filter: Pre-weighed 0.22 μm cellulose membrane
    - Procedure:
        1. Filter sample under vacuum
        2. Wash filter with 10 mL deionized water (removes residual salts)
        3. Transfer filter to pre-labeled aluminum weighing dish
        4. Dry at **60°C for 24 hours** in drying oven
        5. Cool in desiccator for 30 minutes
        6. Weigh on analytical balance (±0.1 mg)
    - Calculation: DCW (g/L) = (final weight - initial weight) / filtered volume (L)
    - **Log in `SAMPLE` form:** Filter ID, sample volume, wet weight, dry weight, DCW
    
    **D. Sample Archival (for future analysis):**
    
    - Centrifuge remaining sample: **5000 × g, 10 minutes, 4°C**
    - Collect supernatant: Store in cryovial at **-80°C**
    - Collect cell pellet: Resuspend in 10% glycerol, store in cryovial at **-80°C**
    - Label with: Batch ID, timepoint, sample type, date
    - **Note:** These samples are out of scope for current campaign but valuable for future analysis

---

**Data Entry Requirements:**

- All measurements must be entered into `SAMPLE` tablet form **within 2 hours** of sampling
- Mandatory fields:
    - Batch ID (auto-populated from QR scan)
    - Timepoint (hours)
    - OD₆₀₀ (raw and calculated)
    - DCW (g/L)
    - Microscopy observations
    - Operator ID
    - Timestamp
- Photo documentation: Capture microscopy image if contamination suspected

---

### **3.5 Identifying End of Batch Phase & Batch Termination**

#### **3.5.1 Glycerol Depletion Detection**

**Primary Indicator: DO Spike**

The end of the glycerol batch phase is characterized by a **sharp and sustained rise in the dissolved oxygen (DO) signal**.

**Physiological Basis:**

- During active growth, cells consume oxygen rapidly → DO remains low (20-40%)
- When glycerol (carbon source) is exhausted, cell metabolism slows dramatically
- Oxygen consumption drops to near zero
- Since aeration continues, DO rapidly rises toward 100%

**DO Spike Signature:**

- DO increases from ~20-40% to >80% within **15-30 minutes**
- Rise is **monotonic** (continuous upward trend)
- DO stabilizes near **95-100%** and remains elevated

**Timing:**

- Typically occurs at **18-24 hours** post-inoculation
- Dependent on initial glycerol concentration and biomass yield
- May vary by ±2 hours between batches (biological variation)

---

#### **3.5.2 Endpoint Confirmation Protocol**

1. **Visual Confirmation:**
    
    - Observe real-time DO trend plot on control system
    - Confirm DO has risen >80% and is stable for >10 minutes
2. **Secondary Indicators (supportive evidence):**
    
    - Agitation: May have returned to lower setpoint (500-600 rpm) as DO control relaxes
    - pH: Base addition rate may have decreased
    - Culture appearance: May appear slightly clearer (reduced scattering)
3. **Final Sample Collection:**
    
    - **Immediately** upon confirming DO spike, collect final **10 mL sample**
    - Label as "Endpoint" or "Glycerol Depletion" sample
    - Process according to Section 3.4.2 (all analyses)
    - This is a **critical sample** - represents maximum biomass

---

#### **3.5.3 Batch Termination Procedure**

**Timing:** Within 30 minutes of confirmed glycerol depletion

1. **Stop Data Logging:**
    
    - Press "Stop Batch" in control system
    - Verify all data has been saved to database
    - Export raw data files to backup location
2. **Stop Fermenter Controls:**
    
    - Stop agitation (ramp down gradually from current speed to 0 over 2 minutes)
    - Stop aeration (close gas valves)
    - Stop all pumps (acid, base, antifoam)
    - Stop temperature control (allow vessel to equilibrate to room temperature)
3. **Culture Harvest:**
    
    - **Option A: Cell Banking**
        - Aseptically harvest full culture volume (1L)
        - Centrifuge: 5000 × g, 15 minutes, 4°C
        - Resuspend cell pellet in 20% glycerol (1:10 volume ratio)
        - Aliquot into cryovials (1 mL each)
        - Freeze at -80°C (slow freeze, -1°C/min ideal)
    - **Option B: Disposal**
        - Autoclave entire vessel with culture
        - Dispose as biological waste per institutional guidelines
4. **Documentation - `BATCH-END` Tablet Form:**
    
    - Final OD₆₀₀ (from endpoint sample)
    - Total batch duration (hours:minutes)
    - Cumulative base addition (mL)
    - Maximum DO observed
    - Final agitation speed
    - Any process deviations (reference deviation log IDs)
    - Harvest method (banking or disposal)
    - Operator sign-off
5. **Post-Run Vessel Cleaning:**
    
    - Disassemble vessel components
    - Clean immediately while residue is fresh (easier removal)
    - Follow cleaning protocol from Section 3.1.1
    - Store vessel in clean state, ready for next run

---

## 4.0 Data Quality & Deviation Management

**Fundamental Principle:** The value of this campaign is **entirely dependent on data quality**. A single batch with poor data quality can compromise model training.

---

### **4.1 Quality Gates & Decision Matrix**

|Quality Gate|Checkpoint|Acceptance Criteria|Action if Failed|Responsible Party|
|---|---|---|---|---|
|**Sensor Calibration**|Pre-run (Section 3.1)|pH slope ≥95%; DO response <30s|Replace probe/buffers and recalibrate. **Do NOT start batch** until passing.|Process Engineer|
|**Inoculum Quality**|Pre-run (Section 3.2.2)|OD₆₀₀ = 2.0-6.0; Microscopy clean|Discard flask. Use backup inoculum or **postpone run**. Log in `FAILURE` form.|Operator|
|**Sterility**|Each sampling point (Section 3.4.2)|No contamination visible on microscope|**Abort batch immediately**. Log in `FAILURE` form. **Blacklist batch data** from training set.|Operator + Process Engineer|
|**DO Control**|Continuous monitoring|DO >20% at all times|Log as "Process Deviation" if <20% for >15 minutes. Batch data **flagged for ML Engineer review**.|Control System + Process Engineer|
|**Data Completeness**|Batch end (Section 3.5.3)|All mandatory tablet forms filled within 2h of sampling|Batch data considered **incomplete**. **Excluded from training set**.|Data Manager|
|**Sampling Adherence**|Per schedule (Section 3.4.2)|All timepoints sampled within ±15 min|If >2 timepoints missed, **exclude batch** from training. Log in `FAILURE` form.|Operator + Process Engineer|
|**OD-DCW Correlation**|Phase A analysis|R² >0.95 for OD vs DCW|If correlation poor, investigate measurement technique. May require additional Phase A batches.|Process Engineer + ML Engineer|

---

### **4.2 Deviation Classification System**

**Level 1 - Minor Deviation (Yellow Flag):**

- Definition: Temporary excursion that self-corrects, minimal impact on data quality
- Examples:
    - DO <20% for 5-15 minutes, then recovers
    - Sampling delayed by 15-30 minutes (1 timepoint only)
    - Single missing microscopy observation (if OD and DCW available)
- Action: Log in control system notes, continue batch, flag data point for ML review
- Impact: Batch data usable with notation

**Level 2 - Major Deviation (Orange Flag):**

- Definition: Significant excursion requiring intervention, potential impact on model training
- Examples:
    - DO <20% for >15 minutes
    - pH excursion >0.3 units for >30 minutes
    - Use of O₂ enrichment
    - Temperature excursion >1°C for >15 minutes
    - > 2 sampling timepoints missed or delayed >30 minutes
        
- Action: Log in `FAILURE` form, notify Process Engineer and ML Engineer immediately, complete batch
- Impact: Batch data flagged for expert review before inclusion in training set

**Level 3 - Critical Deviation (Red Flag):**

- Definition: Batch integrity compromised, data unsuitable for model training
- Examples:
    - Confirmed contamination at any timepoint
    - DO crash <15% for >30 minutes (cell stress/death likely)
    - Sensor failure resulting in >1 hour data loss
    - pH excursion >0.5 units for >1 hour
    - Inoculum OD out of specification (not caught pre-run)
    - Power failure or control system failure
- Action: **Abort batch** (if possible), log in `FAILURE` form, **exclude all data** from training set
- Impact: Batch data blacklisted, batch does not count toward 18-batch campaign target

---

### **4.3 Deviation Logging Requirements**

**`FAILURE` Tablet Form Fields:**

- Batch ID
- Deviation timestamp (start and end)
- Deviation level (1/2/3)
- Deviation category (see classification above)
- Root cause (if known)
- Corrective action taken
- Impact assessment
- Operator and Process Engineer signatures
- ML Engineer review (for Level 2 deviations)

**Deviation Review Cycle:**

- Level 1: Reviewed weekly by Process Engineer
- Level 2: Reviewed within 24h by Process Engineer + ML Engineer
- Level 3: Reviewed immediately, root cause analysis within 48h

---

### **4.4 Data Traceability & Metadata Management**

Every batch must have complete traceability. The following metadata **must** be linked to each batch dataset:

**Pre-Run Metadata:**

- Media composition (all component lot numbers, weights, preparation date)
- Sensor calibration data (pH slope, DO response time, buffer lots, calibration timestamp)
- Vessel ID and configuration
- Inoculum source (cryovial ID or plate ID, passage number, OD₆₀₀)
- Operator ID and training status

**In-Run Metadata:**

- All process parameters at 1-minute intervals minimum (T, pH, DO, agitation, gas flow)
- All manual sample measurements (OD₆₀₀, DCW, microscopy notes)
- All control actions (base additions, agitation changes, O₂ enrichment events)
- All alarms and warnings
- Sampling timestamps (actual vs. scheduled)

**Post-Run Metadata:**

- Total batch duration
- Endpoint indicators (final OD, DO spike characteristics)
- Harvest method and cell bank IDs (if applicable)
- Quality gate pass/fail status for all checkpoints
- Deviation log references
- Data completeness score (% of expected data points captured)

**Data Storage Requirements:**

- Raw control system data: Stored in relational database with batch_id primary key
- Tablet form data: Exported to CSV and JSON formats, backed up daily
- All data backed up to secure server within 24 hours of batch completion
- Data retention: Minimum 7 years per GMP guidelines (even for research campaigns)

---

### **4.5 Batch Acceptance Criteria for Model Training**

Before a batch can be included in the digital twin training dataset, it must pass ALL of the following criteria:

✅ **Criterion 1: Process Completion**

- Batch reached glycerol depletion (DO spike observed)
- Total batch duration within 16-26 hours
- No early termination or aborts

✅ **Criterion 2: Data Completeness**

- All 8 sampling timepoints completed (0, 2, 4, 6, 8, 12, 16h, endpoint)
- All tablet forms completed within 2 hours of sampling
- Continuous sensor data with <1% dropout

✅ **Criterion 3: Process Stability**

- No Level 3 (Critical) deviations
- Maximum 1 Level 2 (Major) deviation per batch
- Level 2 deviation (if present) reviewed and approved by ML Engineer

✅ **Criterion 4: Sterility**

- All microscopy checks show clean culture
- No visible contamination at any timepoint

✅ **Criterion 5: Measurement Quality**

- OD₆₀₀ measurements follow expected exponential growth pattern
- DCW measurements correlate with OD₆₀₀ (within expected variance from Phase A correlation)
- No obvious measurement outliers (>3 standard deviations from model prediction after Phase A)

**Acceptance Decision Tree:**

1. Process Engineer reviews batch data within 48 hours of completion
2. Process Engineer assigns preliminary pass/fail status
3. ML Engineer reviews flagged batches (Level 2 deviations) within 72 hours
4. Final acceptance decision documented in batch record
5. Accepted batches added to training dataset registry
6. Rejected batches documented with rejection reason and lessons learned

---

## 5.0 Data Analysis & Model Development Strategy

### **5.1 Phase A Analysis (Batches 1-3)**

**Primary Objective:** Establish OD₆₀₀-to-DCW correlation curve

**Analysis Protocol:**

1. **Data Compilation:**

    - Pool all OD₆₀₀ and corresponding DCW measurements from Batches 1-3
    - Expected data points: 8 timepoints × 3 batches = 24 paired measurements
    - Include only measurements passing quality checks

2. **Correlation Analysis:**

    - Plot DCW (g/L) vs. OD₆₀₀ (linear scale)
    - Perform linear regression: DCW = m × OD₆₀₀ + b
    - Calculate correlation coefficient (R²)
    - **Acceptance Criteria:** R² ≥ 0.95
    - Calculate 95% confidence intervals for slope and intercept

3. **Process Variability Assessment (NEW - CRITICAL):**

    - Calculate coefficient of variation (CV) for OD₆₀₀ at each timepoint across the 3 batches
    - Calculate CV for DCW at each timepoint
    - Calculate CV for glycerol depletion time (batch duration)
    - **Target:** Overall process CV <5%
    - **Acceptable:** CV = 5-8% (proceed with caution)
    - **Unacceptable:** CV >8% (indicates poor process control or protocol inconsistency)
    - Document baseline variability - this sets the **lower bound** for achievable model MRE

4. **Expected Relationship:**
    
    - Typical conversion: 1.0 OD₆₀₀ ≈ 0.2-0.4 g/L DCW for _P. pastoris_
    - Relationship should be linear across OD range 0.1-100
    - Any non-linearity indicates measurement issues requiring investigation
4. **Deliverable:**
    
    - Validated OD₆₀₀-to-DCW correlation equation
    - Standard operating procedure addendum with conversion formula
    - Quality control chart for future batch comparisons

**Secondary Objectives:**

- Verify sensor calibration procedures are robust (check pH slope and DO response consistency across 3 batches)
- Identify any procedural bottlenecks or ambiguities in SOP
- Optimize tablet form workflow based on operator feedback
- Estimate typical batch duration and glycerol depletion time

**Go/No-Go Decision for Phase B:**

- **PASS:** If R² ≥ 0.95 for OD-DCW correlation AND process CV <5% AND all 3 batches completed without Critical deviations → Proceed to Phase B
- **CONDITIONAL:** If R² ≥ 0.95 but process CV = 5-8% → Proceed to Phase B but flag for enhanced process control focus
- **FAIL:** If R² < 0.95 or process CV >8% or >1 Critical deviation → Run additional Phase A batches (up to 6 total), investigate root causes, improve SOP consistency

---

### **5.2 Phase B Analysis (Batches 4-15)**

**Primary Objective:** Accumulate comprehensive training dataset

**Data Structure:** Each batch contributes a multivariate time-series dataset:

**Input Variables (Features):**

- Time (hours post-inoculation)
- Temperature (°C)
- pH
- Dissolved oxygen (% saturation)
- Agitation speed (rpm)
- Gas flow rate (vvm)
- Cumulative base addition (mL)
- Inoculum OD₆₀₀
- **Off-gas analysis** (if available):
  - Carbon dioxide evolution rate (CER, mol CO₂/L/h)
  - Oxygen uptake rate (OUR, mol O₂/L/h)
  - Respiratory quotient (RQ = CER/OUR)

**Output Variables (Targets):**

- OD₆₀₀ (measured)
- DCW (g/L, measured or calculated from OD correlation)
- Growth rate (calculated: μ = ln(DCW₂/DCW₁)/(t₂-t₁))
- Specific oxygen uptake rate (qO₂, calculated from OUR and biomass)

**Feature Expansion Strategy:**

- **Phase A-B baseline**: Train initial model using pH, DO, temperature, agitation, OD₆₀₀
- **If MRE >6% after Batch 12**: Add off-gas analysis (CER/OUR) to feature set for Batches 13-18
- **Rationale**: Gasset et al. (2024) used 7 specific rates including qO₂, qCO₂ for metabolic state inference. Off-gas data provides direct measurement of cellular respiration, improving prediction of growth phase transitions and glycerol depletion timing.

**Expected Dataset Size:**

- 12 batches × 8 timepoints = 96 high-quality measurement sets
- Plus continuous sensor data at 1-minute intervals = ~12 batches × 24 hours × 60 minutes = ~17,280 sensor data rows

**Interim Analysis (After Batch 9):**

- Conduct preliminary model training using first 6 accepted batches
- Validate against batches 7-9
- Assess if additional batches are needed beyond 15 to achieve target model performance
- Identify any systematic biases or drift in process conditions

**Quality Assurance:**

- Weekly review of batch acceptance rate (target: >80% acceptance)
- Monitor process capability (Cpk) for critical parameters (T, pH, DO)
- Track operator performance and provide feedback/retraining as needed

---

### **5.3 Phase C Analysis (Batches 16-18)**

**Primary Objective:** Independent model validation using hold-out dataset

**Critical Requirement:** Batches 16-18 must remain **completely unseen** by the model during training. This ensures unbiased validation.

**Validation Protocol:**

1. **Train Final Model:**
    
    - Use all accepted batches from Phase A (1-3) and Phase B (4-15)
    - Typical training set size: 10-14 batches (assuming 80% acceptance rate)
    - Hold out Batches 16-18 in separate database with restricted access
2. **Model Prediction:**
    
    - For each validation batch (16-18), use the trained model to predict:
        - OD₆₀₀ trajectory
        - DO trajectory
        - Glycerol depletion time
        - Final biomass concentration
    - Compare predictions to actual measured values
3. **Validation Metrics:**

    **Primary Success Criterion (Research Demonstration):**
    - **Mean Relative Error (MRE)** for 30s OD₆₀₀ predictions: **≤ 8%** (Stretch Goal: ≤ 6%)
    - Must include **uncertainty quantification**: Report MRE ± 95% confidence interval

    **Secondary Validation Metrics (Model Robustness):**
    - Root Mean Square Error (RMSE) for DO predictions: Target <5% saturation
    - Correlation coefficient for predicted vs. actual OD trajectories: Target R² >0.90
    - Glycerol depletion time prediction error: Target <30 minutes

4. **Success Criteria & Go-Live Decision Logic:**

    **PASS (Green Light for Research Deployment):**
    - Primary criterion: MRE ≤ 8% achieved on ≥2 of 3 validation batches (16-18)
      - **OR**, if Phase A showed CV <5%: MRE ≤ 6% achieved on ≥2 of 3 validation batches
    - AND: R² >0.90 on ≥2 of 3 batches
    - AND: Model uncertainty is quantified and documented

    **CONDITIONAL PASS (Yellow Light - Monitoring Mode):**
    - Primary criterion: MRE = 8-10% on ≥2 of 3 validation batches
      - **OR**, if Phase A target was tightened: MRE = 6-8% on ≥2 of 3 validation batches
    - Action: Deploy as monitoring tool only; gather 10 additional batches for retraining

    **FAIL (Red Light - Do Not Deploy):**
    - Primary criterion: MRE >10% on ≥2 of 3 validation batches
    - **ALSO FAIL if:** Model performance is worse than 2× Phase A process CV (indicates poor model, not just process variation)
    - Action: Root cause analysis required. Options:
      1. **Feature expansion**: Add off-gas analysis (CER/OUR) to feature set if not already included
      2. Extend training dataset to 25 batches with additional controlled variation
      3. Revise model architecture (try LSTM for temporal dynamics)
      4. Improve process control consistency (investigate root causes of high CV)

**Deliverable:**

- Validation report with performance metrics including:
  - MRE ± 95% confidence interval for each validation batch
  - Comparison plots (predicted vs. actual) for all validation batches
  - Residual analysis and uncertainty quantification
  - Performance relative to baseline process variability (from Phase A)
- Recommendations for deployment, monitoring, or additional training
- Documentation of model limitations and known failure modes

---

### **5.4 Digital Shadow Model Architecture (Preliminary)**

**Model Type:** Hybrid mechanistic-empirical model

**Mechanistic Components (Physics-Based):**

- Mass balance for biomass (dX/dt = μX)
- Mass balance for substrate (dS/dt = -μX/Y_{X/S})
- Oxygen mass transfer equation (OTR = kLa(C* - C))
- Heat balance (if temperature excursions occur)

**Empirical Components (Data-Driven):**

- Specific growth rate (μ) as function of substrate, pH, DO
    - Candidate models: Monod kinetics, neural network, Gaussian process
- Biomass yield coefficient (Y_{X/S})
- Oxygen uptake rate per unit biomass

**Input Features:**

- Initial conditions: Inoculum OD, media composition
- Controlled variables: T, pH setpoints
- Manipulated variables: Agitation, aeration

**Output Predictions:**

- Biomass trajectory (DCW vs. time)
- DO trajectory
- Substrate depletion time
- Base consumption

**Training Approach:**

- Parameter estimation using nonlinear least squares or maximum likelihood
- Hyperparameter tuning using cross-validation on Phase B batches
- Ensemble methods if multiple model forms perform similarly

**Software Tools:**

- Python (NumPy, SciPy, pandas, scikit-learn)
- PyTorch or TensorFlow (if using neural network components)
- Process modeling libraries (e.g., PyOMO, Cantera) for mechanistic equations

---

## 6.0 Operational Logistics & Resource Requirements

### **6.1 Timeline & Scheduling**

**Phase A: Shakedown, Correlation & Control Commissioning (Weeks 1-4)**

- Batch 1 (Baseline, No Control): Week 2 (Week 1 = setup/commissioning)
- Control system commissioning: Weeks 1-2
- Batch 2 (Control Validation): Week 3
- Batch 3 (Control Validation): Week 4
- Phase A analysis & SOP finalization: Week 4-5

**Phase B: Data Accumulation (Weeks 5-16)**

- Batches 4-15: 12 batches sequential in single 1L bioreactor
- Average cadence: **1 batch per week** (allows proper cleanup, analysis, and technician availability)
- 12 batches × 1 week/batch = 12 weeks
- Buffer time included for any repeated batches due to failures

**Phase C: Validation & Hold-Out (Weeks 17-19)**

- Batch 16: Week 17
- Batch 17: Week 18
- Batch 18: Week 19
- Final validation analysis: Week 19-20

**Total Campaign Duration: 20 weeks (5 months)**

---

### **6.2 Resource Requirements**

**Equipment:**

- 1× 1L benchtop bioreactor with automated control system (temperature PID, pH control via base pump, DO cascade)
- 1× Control system with data logging (e.g., BioFlo, Applikon, Sartorius)
- 1× Autoclave (minimum 50L capacity)
- 1× Spectrophotometer for OD₆₀₀ measurements
- 1× Analytical balance (±0.01 g accuracy) for media prep
- 1× Analytical balance (±0.1 mg accuracy) for DCW measurements
- 1× Vacuum filtration setup for DCW
- 1× Drying oven (60°C)
- 1× Microscope (phase contrast, 400× magnification)
- 1× Centrifuge (minimum 5000 × g)
- 1× Orbital shaker (for seed cultures)
- 1× -80°C freezer (for sample archival)

**Consumables (per batch):**

- Fermentation salts (K₂SO₄, MgSO₄, CaSO₄, KOH, H₃PO₄): ~50 g total
- Glycerol (40 g)
- PTM₁ trace salts (5 mL)
- Ammonium hydroxide 28% (50 mL)
- pH calibration buffers (20 mL each, pH 4 and 7)
- BMGY medium components (yeast extract, peptone, YNB): ~10 g total
- Sterile filters 0.22 μm for media/solutions (5 units)
- Cellulose membrane filters for DCW (10 units)
- Cryovials for sample storage (20 units)
- Sterile sampling syringes/pipettes (15 units)
- Gloves, lab coat, safety glasses (standard PPE)

**Estimated Consumable Cost per Batch:** $150-200 USD

**Personnel:**

**Core Team Roles:**
- **Project Lead:** 20 hours/week for 20 weeks (oversight, quality assurance, stakeholder communication)
- **Process Engineer (Lead):** 25 hours/week for 20 weeks (setup, SOP development, DevOps, batch execution oversight, deviation management)
- **ML Engineer / Data Scientist:** 10 hours/week for 20 weeks (model development, hyperparameter tuning, validation analysis)
- **Senior Process Engineer (Reviewer):** 5 hours/week for 20 weeks (plan review, data quality review, batch acceptance decisions)
- **Hardware Engineer / Data Pipeline:** 15 hours/week for Weeks 1-10 (control system design, sensor integration, pipeline development)
- **Software Engineer (Forms/API):** 40 hours/week for Weeks 2-5 (React SPA, FastAPI backend, PostgreSQL schema)
- **Lab Technician #1:** 20 hours/week for Weeks 2-19 (media prep, calibrations, sampling, analysis, data entry)
- **Lab Technician #2:** 15 hours/week for Weeks 5-19 (backup sampling, evening/weekend coverage, dual verification)

**Minimum Team Size:** 6-8 people (some roles combined depending on expertise)

**Critical Requirement:** At least **2 trained lab technicians** must be available throughout campaign to provide shift coverage and ensure continuity during vacations/illness.

**Total Person-Hours:** ~1,600 hours for complete campaign

---

### **6.3 Training Requirements**

All personnel must complete training before participating in campaign:

**Operator Training (8 hours):**

- Module 1: _P. pastoris_ biology and fermentation principles (1 hour)
- Module 2: Bioreactor operation and safety (2 hours)
- Module 3: Aseptic technique and sterility assurance (1 hour)
- Module 4: Sampling and analytical procedures (2 hours)
- Module 5: Tablet form data entry and SOP compliance (1 hour)
- Module 6: Practical hands-on training with supervised batch (1 hour)

**Assessment:** Written exam (80% pass required) + practical demonstration

**Process Engineer Training:**

- Sensor calibration certification
- Deviation management procedures
- Root cause analysis techniques
- Data review and batch acceptance workflows

**Retraining:** Required if technician has not run a batch in >30 days

**Note:** All roles listed use generic titles. Specific team members and responsibilities will be assigned during project initiation based on organizational structure and individual expertise.

---

### **6.4 Safety & Risk Management**

**Hazards:**

- **Chemical:** Phosphoric acid (corrosive), Ammonium hydroxide (corrosive, irritant)
- **Biological:** _P. pastoris_ (BSL-1, low risk but use aseptic technique)
- **Physical:** Autoclave burns, pressurized vessels, rotating equipment
- **Electrical:** Bioreactor control systems and heaters

**Mitigation:**

- All chemical handling in fume hood with appropriate PPE
- Autoclave operation only by trained personnel
- Emergency eyewash and safety shower within 10 meters of work area
- Lockout/tagout procedures for vessel maintenance
- Spill kits readily available

**Emergency Procedures:**

- Chemical spill: Evacuate, contain, neutralize (refer to SDS)
- Equipment failure: Stop batch, secure vessel, notify supervisor
- Contamination: Abort batch, autoclave vessel, investigate source
- Personnel injury: First aid, document incident, report to safety officer

---

## 7.0 Data Utilization & Digital Shadow Deployment

### **7.1 Digital Shadow Capabilities (Target)**

Upon successful completion of the campaign and model validation, the digital shadow will enable:

**Predictive Capabilities:**

- Forecast biomass trajectory from inoculation to glycerol depletion
- Predict glycerol depletion time (±30 min accuracy)
- Estimate final biomass concentration (±10% accuracy)
- Forecast DO and pH trends throughout batch

**Optimization Capabilities:**

- Recommend optimal inoculum density to achieve target batch time
- Suggest agitation/aeration strategies to maintain DO >20% with minimal O₂ enrichment
- Predict impact of temperature or pH setpoint changes on biomass yield

**Monitoring & Decision Support:**

- Real-time anomaly detection (flag batches deviating from expected trajectory)
- Soft-sensor for online DCW estimation (from OD₆₀₀ correlation + model prediction)
- Operator decision support (e.g., "DO may crash in 30 min - consider agitation increase")
- **Note:** Phase 1 is prediction-only. Control write-back capability reserved for Phase 2 (Digital Twin evolution)

**Scale-Up Support:**

- Predict behavior at different vessel scales (5L, 20L, 200L) using dimensionless numbers (Re, kLa)
- Guide process transfer to manufacturing facilities

---

### **7.2 Model Maintenance & Continuous Improvement**

**Model Versioning:**

- Version 1.0: Trained on Phase A + B data, validated on Phase C
- Version 1.1+: Updated as new batches are run post-campaign
- All model versions tracked in version control (Git) with training data snapshots

**Model Retraining Triggers:**

- New strain or media composition used
- Process conditions significantly changed (e.g., scale, temperature)
- Model prediction error exceeds threshold in production (MAPE >15%)
- Every 50 new batches run (to capture process drift)

**Performance Monitoring:**

- Track model prediction error for each production batch
- Monthly review of model performance metrics
- Quarterly re-validation using recent hold-out batches

---

### **7.3 Knowledge Transfer & Documentation**

**Campaign Deliverables:**

1. **Final Technical Report:**
    
    - Campaign summary and batch acceptance statistics
    - OD-DCW correlation study results
    - Digital twin model documentation (architecture, parameters, performance)
    - Validation results and uncertainty analysis
    - Lessons learned and recommendations
2. **Standard Operating Procedures:**
    
    - Finalized SOP for _P. pastoris_ glycerol batch fermentation
    - Sensor calibration procedures
    - Sampling and analytical methods
    - Data management and quality assurance protocols
3. **Training Materials:**
    
    - Operator training manual and assessment
    - Video tutorials for critical procedures (inoculation, sampling, data entry)
    - Troubleshooting guide for common issues
4. **Digital Shadow Software Package:**

    - Model code (Python scripts, Jupyter notebooks)
    - User interface for predictions and "what-if" scenarios
    - API for integration with monitoring dashboards (control write-back disabled)
    - Documentation and user guide
5. **Data Archive:**
    
    - Complete dataset (all 18 batches) in standardized format
    - Metadata dictionary
    - Database schema documentation
    - Data access and usage guidelines

**Knowledge Dissemination:**

- Internal presentation to R&D and manufacturing teams
- Publication in peer-reviewed journal (if applicable)
- Conference presentation at SIMB or ACS meeting
- Patent disclosure for novel process control strategies (if applicable)

---

## 8.0 Success Metrics & Campaign Evaluation

### **8.1 Quantitative Metrics**

|Metric|Target|Measurement Method|
|---|---|---|
|**Batch Acceptance Rate**|≥80%|(# accepted batches) / (# batches run) × 100%|
|**OD-DCW Correlation (Phase A)**|R² ≥0.95|Linear regression of pooled Phase A data|
|**Data Completeness**|≥95%|(# complete data points) / (# expected) × 100%|
|**Sterility Success Rate**|100%|(# sterile batches) / (# batches run) × 100%|
|**Sensor Calibration Pass Rate**|≥95%|(# successful calibrations) / (# attempts) × 100%|
|**Glycerol Depletion Detection**|100%|All batches show clear DO spike|
|**Model Prediction Accuracy (Phase C)**|MRE ≤8%|Compare predicted vs. actual OD trajectories|
|**Model Validation Success**|≥2 of 3 batches|Pass all validation metrics|
|**Campaign Duration**|≤20 weeks|Actual time from Batch 1 to final validation|
|**Safety Incidents**|0|# of recordable injuries or near-misses|

---

### **8.2 Qualitative Metrics**

**Process Understanding:**

- Team can articulate key physiological drivers of _P. pastoris_ growth kinetics
- Clear understanding of DO control challenges and mitigation strategies
- Documented lessons learned on protocol optimization

**Operational Excellence:**

- Streamlined workflows and minimal procedural bottlenecks
- High operator confidence and competency
- Robust data management and traceability systems

**Model Utility:**

- Digital shadow provides actionable insights for process optimization
- Model predictions are trusted by process engineers
- Model integrated into routine process monitoring

---

### **8.3 Go/No-Go Decision for Digital Shadow Deployment**

**DEPLOY (Green Light):**

- ✅ ≥12 accepted batches from Phases A+B
- ✅ Phase C validation successful (≥2 of 3 batches meet metrics)
- ✅ Model MAPE <10% on hold-out data
- ✅ No major safety incidents
- ✅ Complete documentation package delivered

**CONDITIONAL DEPLOY (Yellow Light):**

- ⚠️ 10-11 accepted batches (borderline dataset size)
- ⚠️ Phase C validation marginal (1 of 3 batches meets metrics OR metrics slightly exceed targets)
- ⚠️ Model MAPE 10-15%
- **Action:** Run additional validation batches (19-21) to build confidence

**DO NOT DEPLOY (Red Light):**

- ❌ <10 accepted batches (insufficient training data)
- ❌ Phase C validation failed (0 of 3 batches meet metrics OR major prediction errors)
- ❌ Model MAPE >15%
- ❌ Critical safety incident occurred
- **Action:** Conduct root cause analysis, revise approach, potentially re-run campaign

---

## 9.0 Appendices

### **Appendix A: Media Recipes**

**Fermentation Basal Salts Medium (per Invitrogen, 1L final volume)**

|Component|Amount|Supplier/Catalog #|Notes|
|---|---|---|---|
|Phosphoric acid, 85%|26.7 mL|Sigma P5811|Handle with care, corrosive|
|Calcium sulfate dihydrate|0.93 g|Sigma C3771|Slow to dissolve|
|Potassium sulfate|18.2 g|Sigma P9458||
|Magnesium sulfate heptahydrate|14.9 g|Sigma M1880||
|Potassium hydroxide|4.13 g|Sigma P1767||
|Glycerol, 99%|40.0 g (~31.7 mL)|Sigma G5516|Carbon source|

**PTM₁ Trace Salts (per Invitrogen, 1L stock solution)**

|Component|Amount|Notes|
|---|---|---|
|Cupric sulfate pentahydrate (CuSO₄·5H₂O)|6.0 g||
|Sodium iodide (NaI)|0.08 g||
|Manganese sulfate monohydrate (MnSO₄·H₂O)|3.0 g||
|Sodium molybdate dihydrate (Na₂MoO₄·2H₂O)|0.2 g||
|Boric acid (H₃BO₃)|0.02 g||
|Cobalt chloride hexahydrate (CoCl₂·6H₂O)|0.5 g||
|Zinc chloride (ZnCl₂)|20.0 g||
|Ferrous sulfate heptahydrate (FeSO₄·7H₂O)|65.0 g||
|Biotin|0.2 g||
|Sulfuric acid, concentrated|5.0 mL|Preservative|

_Store PTM₁ at 4°C. Filter-sterilize before use. Do not autoclave._

**BMGY Medium (Buffered Glycerol-complex Medium, 1L)**

|Component|Amount|Notes|
|---|---|---|
|Yeast extract|10 g||
|Peptone|20 g||
|Glycerol|10 mL||
|Yeast nitrogen base (YNB)|13.4 g|Without amino acids|
|Potassium phosphate buffer, 1M, pH 6.0|100 mL|Prepare separately|

_Autoclave at 121°C for 20 min. Cool before use._

---

### **Appendix B: Tablet Forms Checklist**

**Form 1: `CALIBRATION` (Pre-Run)**

- [ ] Batch ID (QR scan)
- [ ] Vessel ID
- [ ] Date/Time
- [ ] Operator ID
- [ ] pH probe: Buffer lot #s (pH 4 and 7), Readings, Slope %, Pass/Fail
- [ ] DO probe: 0% reading, 100% reading, Response time, Pass/Fail
- [ ] **Off-gas O₂ sensor: 0% reading (N₂), Span reading (air, 20.9%), Drift from previous cal, Pass/Fail**
- [ ] **Off-gas CO₂ sensor: 0% reading (N₂), Span reading (air, ~0.04%), Drift from previous cal, Pass/Fail**
- [ ] **Pressure transducer: Zero reading (atm pressure), Pass/Fail**
- [ ] Temperature probe (broth): Verification reading, Pass/Fail
- [ ] **Temperature probes (pH, DO, exhaust, motor): Verification readings, Agreement check**
- [ ] Comments/Notes

**Form 2: `MEDIA` (Pre-Run)**

- [ ] Batch ID (QR scan)
- [ ] Media prep date
- [ ] All component weights and lot numbers (9 components)
- [ ] Final volume
- [ ] Autoclave cycle number
- [ ] Sterility indicator pass
- [ ] Operator signature

**Form 3: `INOCULATION` (Pre-Run)**

- [ ] Batch ID
- [ ] Inoculum source (plate/cryo ID)
- [ ] Flask incubation start time
- [ ] Final OD₆₀₀ (raw and calculated)
- [ ] Microscopy observations
- [ ] Volume transferred (mL)
- [ ] Reactor inoculation timestamp
- [ ] GO/NO-GO decision
- [ ] Operator signature

**Form 4: `SAMPLE` (In-Run, repeat for each timepoint)**

- [ ] Batch ID
- [ ] Timepoint (hours)
- [ ] Sample collection timestamp
- [ ] OD₆₀₀ (raw reading, dilution factor, calculated OD)
- [ ] Microscopy: Morphology, Contamination Y/N
- [ ] DCW: Filter ID, Sample volume (mL), Wet weight (g), Dry weight (g), DCW (g/L)
- [ ] Supernatant archived: Cryovial ID
- [ ] Cell pellet archived: Cryovial ID
- [ ] Operator ID

**Form 5: `BATCH-END` (Post-Run)**

- [ ] Batch ID
- [ ] Batch end timestamp
- [ ] Total batch duration (hours)
- [ ] Final OD₆₀₀
- [ ] Glycerol depletion time (hours)
- [ ] DO spike observed: Y/N, Max DO %
- [ ] Cumulative base addition (mL)
- [ ] Harvest method (banking/disposal)
- [ ] Cell bank cryovial IDs (if applicable)
- [ ] Deviations logged: Y/N, Deviation IDs
- [ ] Operator signature
- [ ] Process Engineer review signature

**Form 6: `FAILURE` (As Needed)**

- [ ] Batch ID
- [ ] Deviation timestamp (start-end)
- [ ] Deviation level (1/2/3)
- [ ] Deviation category (dropdown: DO crash, contamination, sensor failure, etc.)
- [ ] Description of issue
- [ ] Root cause (if known)
- [ ] Corrective action taken
- [ ] Batch fate (continue/abort)
- [ ] Impact on data quality
- [ ] Operator signature
- [ ] Process Engineer signature
- [ ] ML Engineer review (for Level 2)

---

### **Appendix C: Troubleshooting Guide**

|Problem|Possible Cause|Solution|
|---|---|---|
|**pH slope <95%**|Probe fouled or aged|Clean probe with pepsin-HCl, recalibrate. If still failing, replace probe.|
||Old/contaminated buffers|Use fresh NIST-traceable buffers, store properly (4°C, sealed).|
|**DO probe slow response**|Membrane damaged|Replace membrane, recalibrate.|
||Electrolyte depleted|Refill electrolyte solution per manufacturer instructions.|
|**DO crash during batch**|Agitation insufficient|Increase agitation to max (1000 rpm). If still <20%, add O₂ (log deviation).|
||High cell density|Expected near glycerol depletion; confirm approaching endpoint.|
||Foam covering probe|Add antifoam (if not already in medium); verify probe position.|
|**pH drift upward**|NH₄OH pump failure|Check pump tubing, prime line, verify pump calibration.|
||Base reservoir empty|Refill 28% NH₄OH reservoir.|
|**pH drift downward**|Acid production|Unusual for glycerol batch; check for contamination.|
||Calibration drift|Recalibrate pH probe if drift >0.2 units.|
|**No DO spike observed**|Glycerol excess (weighing error)|Verify glycerol mass from media prep log; may take >24h.|
||Contamination (low OD)|Check microscopy for contaminants; abort if confirmed.|
||DO probe failure|Verify probe function; collect endpoint sample based on other indicators (agitation drop, pH change).|
|**Contamination visible**|Inoculum contaminated|Trace back to inoculum source; discard stock, re-streak fresh plate.|
||Breach of asepsis|Review sampling technique with operator; retrain if needed.|
||Autoclave failure|Verify autoclave cycle completion; check sterility indicators.|
|**OD reading erratic**|Sample clumping|Vortex sample vigorously before reading; dilute if needed.|
||Spectrophotometer dirty|Clean cuvette and spectrophotometer optics.|
||Bubbles in cuvette|Tap cuvette to remove bubbles before reading.|
|**DCW filter clogged**|High cell density|Use smaller sample volume (2-3 mL instead of 5 mL).|
||Cell lysis|Ensure gentle vacuum; avoid over-drying during filtration.|

---

### **Appendix D: Critical Contacts**

|Role|Name|Phone|Email|Escalation|
|---|---|---|---|---|
|Lead Process Engineer|(Name)|(Phone)|(Email)|Primary contact for all batch issues|
|ML Engineer|(Name)|(Phone)|(Email)|Data quality and model questions|
|Lab Manager|(Name)|(Phone)|(Email)|Equipment maintenance and supplies|
|Safety Officer|(Name)|(Phone)|(Email)|Incidents and hazard reporting|
|Data Manager|(Name)|(Phone)|(Email)|Database access and IT issues|
|Autoclave Technician|(Name)|(Phone)|(Email)|Sterilization troubleshooting|
|24/7 Emergency Line|-|(Phone)|-|After-hours critical issues|

---

### **Appendix E: References & Further Reading**

1. Invitrogen Corporation. "Pichia Fermentation Process Guidelines." Catalog no. K1750-01. 2002.
    
2. Macauley-Patrick S, et al. "Heterologous protein production using the _Pichia pastoris_ expression system." _Yeast_ 22.4 (2005): 249-270.
    
3. Cos O, et al. "Operational strategies, monitoring and control of heterologous protein production in the methylotrophic yeast _Pichia pastoris_ under different promoters: A review." _Microbial Cell Factories_ 5.1 (2006): 17.
    
4. Garcia-Ortega X, et al. "Physiological characterization and transcriptomic analysis of glycerol grown _Pichia pastoris_ cultures."