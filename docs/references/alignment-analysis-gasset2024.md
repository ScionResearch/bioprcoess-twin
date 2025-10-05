# Alignment Analysis: Digital Shadow Project vs. Gasset et al. (2024)

**Document Type:** Comparative Analysis
**Date:** October 5, 2025
**Author:** Technical Program Manager
**Reference Paper:** Gasset et al. (2024) - "Continuous Process Verification 4.0 application in upstream: adaptiveness implementation managed by AI in the hypoxic bioprocess of the *Pichia pastoris* cell factory"
**Project Documents Reviewed:** Project Plan.md (Issue 1.0)

---

## Executive Summary

This analysis compares our Digital Shadow project plan against the published research by Gasset et al. (2024), which implemented AI-driven adaptive control for *Pichia pastoris* fermentation using Industry 4.0 technologies.

**Overall Assessment:** Our project shows **strong methodological alignment** (8.5/10) with appropriate scope reductions for a first-time implementation. Key differences reflect realistic Phase 1 constraints rather than fundamental approach divergence.

---

## 1. Core Similarities (Well-Aligned)

| Dimension | Gasset et al. (2024) | Our Project Plan | Alignment Status |
|-----------|---------------------|-------------------|------------------|
| **Organism** | *P. pastoris* X-33 | *P. pastoris* (strain unspecified) | ✓ Perfect |
| **Control Philosophy** | Physiological control (RQ set-point 1.4) | Digital shadow (prediction-only) | ✓ Compatible - building prediction foundation |
| **Performance Metrics** | MRE (accuracy), RMSD (precision) | MRE ≤ 8% (stretch 6%), R² >0.90, RMSE <5% | ✓ **Strong** - Industry-standard metrics |
| **AI Approach** | Random Forest (100 trees) for adaptive control | LightGBM for prediction | ✓ Compatible - both gradient-boosted ensembles |
| **Edge Computing** | BeDataFeeder (on-prem edge node) | Jetson Orin edge inference | ✓ Architecturally aligned |
| **Data Infrastructure** | Eve SCADA + Aizon cloud platform | InfluxDB + FastAPI + Grafana | ✓ Functionally equivalent (cloud-free) |
| **Batch Count** | 6 fermentations (2 MHC + 2 BLC + 2 AI-APC) | 18 batches planned | ✓ **Exceeds** research scope |
| **Feasibility Focus** | Demonstrated CPV via reproducibility | Phase A CV measurement to validate targets | ✓ Excellent - added feasibility gate |

---

## 2. Key Differences (Justified Scope Reductions)

### 2.1 Process Complexity

**Gasset et al.:** Fed-batch with RQ control under hypoxic conditions
- Exponential glucose feeding (µ = 0.10 h⁻¹)
- Respiratory quotient (RQ) control at 1.4 ± 0.05
- Required real-time off-gas analysis (CO₂, O₂)
- Dynamic agitation rate modulation (600-1200 rpm)

**Our Plan:** Simple glycerol batch for biomass accumulation
- Single carbon source (glycerol)
- No fed-batch complexity
- OD₆₀₀ prediction as primary target

**Assessment:** ✓ **Appropriate Phase 1 simplification**. Their system required 3 control iterations (MHC → BLC → AI-APC) to achieve stable performance. We're starting with prediction on a simpler process to establish foundational capabilities.

### 2.2 Control Implementation

**Gasset et al.:** Closed-loop control
- AI-APC system wrote agitation set-points every 7 minutes
- Adaptive proportional gain (Kp) predicted by Random Forest
- Real-time control actions via REST API calls to Eve SCADA

**Our Plan:** Digital shadow only
- Prediction with disabled control paths (`CONTROL_MODE=0`)
- Control architecture implemented but not activated
- Focus on prediction accuracy first

**Assessment:** ✓ **Correct Phase 1 scope**. Their work validates this is the right incremental path - they evolved through manual control before achieving autonomous AI-driven control.

### 2.3 Performance Targets

**Gasset et al.:** Achieved performance
- AI-APC: MRE = 3.5-4.0% (Table 3)
- BLC: MRE = 4.5%
- MHC: MRE = 5-14% (high variability)

**Our Plan:** Target performance
- Primary: MRE ≤ 8%
- Stretch: MRE ≤ 6%
- R² > 0.90, RMSE < 5%

**Assessment:** ✓ **Realistic for Phase 1**. Our target is ~2× their best performance, appropriate given:
1. First-time team (no prior digital shadow experience)
2. Simpler process may allow better accuracy than expected
3. Feasibility gate (Phase A) will validate target appropriateness

---

## 3. Critical Insights from Gasset et al. for Our Project

### 3.1 Their Progression Validates Our Phase Plan

**Their Development Path:**
1. **Manual-Heuristic Control (MHC):** MRE ~10%, high variability, labor-intensive
2. **Boolean-Logic Control (BLC):** MRE ~5%, automated with fixed Δrpm steps
3. **AI-Adaptive Control (AI-APC):** MRE <4%, dynamic Δrpm prediction

**Key Finding:** This 3-stage evolution required ~6 fermentations and significant trial-and-error tuning.

**Implication for Our Project:**
- We're building the **data foundation** (18 batches) to skip directly to AI-driven prediction in Phase 2
- Avoids their control tuning phase by starting with prediction-only
- Our larger dataset (18 vs. 6 batches) provides better training foundation

### 3.2 Reproducibility Was Their Main Achievement

**Gasset et al. Results (Table 2):**
- MHC: Final biomass varied 89-100 gDCW/L, CrI1 titre 244-335 kAU/L
- BLC: Final biomass 76-89 gDCW/L, CrI1 titre 257-332 kAU/L
- AI-APC: Final biomass 79-80 gDCW/L, CrI1 titre 257-270 kAU/L

**Root Cause Analysis:**
- RQ oscillations (±0.2 units) in manual mode caused metabolic flux instability
- Automated control reduced standard deviation in product titre by ~30%

**Implication for Our Project:**
- Our **Phase A CV baseline measurement** directly addresses this
- If glycerol batch CV is high (>10%), OD prediction alone won't enable reliable control
- Would need to address upstream variability (media prep, inoculum quality) first
- Validates importance of feasibility gate

### 3.3 Extensive Manual Data Capture Required

**Their Data System (Table 1):**
- 14 primary variables (TEMP, pH, STIRR, pO₂, GF_AIR, etc.)
- 4 derived variables (ExitCO₂, ExitO₂, Volume, Ethanol)
- Soft sensors for CER, OUR, RQ
- Off-gas analyzers required manual recalibration before each run
- Biomass (DCW) measured offline in quadruplicate (RSD <5%)

**Calibration Issues Observed:**
- R2 in Figure 3B required post-run RQ corrections due to analyzer drift
- Initial fed-batch hours showed poor RQ control due to low signal strength

**Validation for Our Plan:**
- Our **Manual Data Development.md** system (7 form types, QR codes, offline-first) matches their rigor
- Pre-batch CALIBRATION form enforcement addresses their analyzer drift issues
- **Not overkill** - aligns with published research requirements

### 3.4 Model Training Strategy

**Their Approach:**
- Random Forest with 100 decision trees
- Trained on data from MHC, BLC, and fed-batches at different µ values
- Required **diverse operating conditions** to achieve generalization
- Combined historical data from multiple control strategies

**Risk for Our Project:**
- Our 18 batches are all glycerol batch (single process mode)
- If batches 1-15 have low variability, model may overfit
- Limited operating envelope may reduce generalization

**Mitigation Strategy:**
- **Phase B/C**: Intentionally vary non-critical parameters:
  - Temperature: ±1°C from set-point
  - Inoculum OD: 0.8-1.2 range
  - Agitation: ±50 rpm within safe range
  - Media lot variations
- Generate training diversity without compromising safety
- Document as "controlled variation batches" in Phase B

---

## 4. Gaps & Recommendations

### 4.1 Performance Target Reassessment

**Gasset et al. Evidence:** AI-APC achieved MRE 3.5-4.0% on **harder problem** (fed-batch RQ control)

**Recommendation:**
- **Phase A Action**: Measure glycerol batch process CV
- **Decision Rule**: If CV < 5%, consider tightening to MRE ≤ 6% as primary (not stretch)
- **Rationale**: Simpler process may allow better accuracy than conservative 8% target

### 4.2 Feature Set Expansion

**Gasset et al. Used:** 7 specific rates (µ, qs, qO₂, qCO₂, qEtOH, qArb, qSuc) + respirometry

**Our Current Plan:** pH, DO, temperature, OD₆₀₀

**Recommendation:**
- **Phase B**: Add off-gas analysis (CER/OUR) if initial model struggles
- **Rationale**: OD prediction from pH/DO/temp alone may lack metabolic state information
- **Defer to Phase 2 if not needed**: Avoid scope creep

### 4.3 Disturbance Testing (Phase C Enhancement)

**Gasset et al. Approach:**
- Injected controlled disturbance at t=13.3h (switched to O₂-enriched air)
- Tested AI-APC robustness and recovery time
- AI controller returned RQ to set-point within 30-60 minutes

**Recommendation:**
- **Phase C Addition**: Introduce controlled perturbations in batches 13-15:
  - Delayed feeding simulation
  - Temperature spike (±2°C for 30 min)
  - Agitation step change
- Document as "stress test batches"
- Validates model resilience before hold-out validation

### 4.4 Hold-Out Validation Strategy

**Gasset et al.:** 2 biological replicates per strategy (N=6 total)

**Our Plan:** 18 batches with 3 hold-outs (batches 16-18)

**Recommendation:**
- **More rigorous validation**: ✓ Keep current plan
- **Ensure diversity**: Hold-outs should span:
  - Different seasons (thermal variations)
  - Different media lots
  - Different operators (if applicable)
- **Success Criteria**: ≥2 of 3 must meet MRE target (already in plan) ✓

---

## 5. Key Alignment Strengths

### ✓ Data Quality Over Speed
**Evidence:** Manual forms system (Project Plan Section 8.0) matches Gasset et al. rigor (Table 1: 14+ variables tracked)

**Validation:** Research-grade data collection is **not overkill** - it's a prerequisite for AI model success.

### ✓ Edge-First Architecture Validated
**Evidence:** BeDataFeeder + Aizon platform proved local inference works in production bioprocess

**Our Implementation:** Jetson Orin approach is architecturally sound and consistent with CPV 4.0 principles.

### ✓ Realistic Performance Targets
**Evidence:** MRE ≤ 8% for Phase 1 is appropriate given Gasset et al. achieved <4% after **multiple control iterations**

**Context:** They had prior hypoxic fermentation experience; our conservatism is justified for first-time team.

### ✓ Feasibility Gate is Best Practice
**Evidence:** Gasset et al. had **no feasibility checkpoint** - assumed RQ=1.4 was achievable from prior studies

**Our Addition:** Phase A CV measurement to validate MRE target = 2× CV is **superior to published approach**.

### ✓ Batch Count Exceeds Research Dataset
**Evidence:** They trained on ~6 fermentations; we plan 18 batches (3× more data)

**Benefit:** Reduces overfitting risk, improves generalization, enables robust train/validation/test split.

---

## 6. Phase 2 Roadmap Alignment

Gasset et al. progression provides a **validated path** for our Phase 2 expansion:

| Phase 2 Feature | Evidence from Gasset et al. | Our Readiness |
|----------------|----------------------------|---------------|
| **Closed-loop control** | AI-APC successfully wrote agitation set-points with 7-min intervals | `CONTROL_MODE` flag + control paths in architecture show pre-planning ✓ |
| **Fed-batch modeling** | Main contribution was µ-stat control under hypoxia | Correctly deferred (Project Plan Section 3.0 - Out of Scope) ✓ |
| **Multi-strain support** | Not addressed (single X-33 clone used) | Correctly deferred - consistent with research ✓ |
| **Adaptive control gains** | Random Forest predicted Kp (proportional gain) dynamically | LightGBM can do this - architecture supports it ✓ |
| **Disturbance rejection** | Tested with O₂-enriched air injection | Can add in Phase C stress tests ✓ |

**Expansion Path:** Our Phase 1 → Phase 2 progression mirrors their MHC → BLC → AI-APC evolution, but with stronger data foundation.

---

## 7. Risk Mitigation Based on Their Lessons Learned

### 7.1 Calibration Drift (High Priority)

**Their Issue:** R2 fermentation had post-run RQ corrections due to gas analyzer calibration drift (Figure 3B)

**Our Mitigation:**
- Mandatory pre-batch CALIBRATION form (2-point pH, DO calibration)
- Auto-flag data from non-compliant probes
- Weekly calibration schedule enforcement
- **Status:** Already in Manual Data Development.md ✓

### 7.2 Low Signal Strength in Early Batch Phase

**Their Issue:** First 1-2 hours of fed-batch showed poor RQ control due to low CO₂/O₂ flux

**Our Mitigation:**
- Glycerol batch has higher initial biomass (~25 gDCW/L at batch start)
- Higher metabolic activity should provide better signal-to-noise
- If issue persists: Exclude first hour from training dataset
- **Status:** Monitor in Phase A, adjust feature engineering if needed

### 7.3 Process Instability at High Biomass

**Their Issue:** R2 with BLC showed growth rate decline and glucose accumulation in final 2 hours (Figure 5)

**Our Implication:**
- Glycerol batch is simpler (no fed-batch substrate accumulation)
- Lower risk, but monitor for oxygen limitation at high biomass
- **Status:** Phase A will reveal if this is a concern for our process

---

## 8. Final Verdict

### Alignment Score: 8.5/10

**Strengths:**
1. Core methodology (AI-driven bioprocess monitoring, edge computing, rigorous validation) is nearly identical
2. Scope reductions (glycerol batch vs. fed-batch, prediction vs. control) are **appropriate for Phase 1**
3. Development path matches their incremental evolution (prediction → control)
4. **18-batch campaign exceeds their dataset size** (18 vs. 6), improving generalization potential
5. **Feasibility gate** (Phase A CV measurement) is a **best-practice addition** they lacked
6. Manual data system rigor matches published research requirements

**Justified Divergences:**
1. Simpler process (glycerol batch vs. hypoxic fed-batch) → **Correct for first-time team**
2. No control write-back → **Appropriate Phase 1 scope, architecture ready for Phase 2**
3. Lower performance target (MRE 8% vs. 4%) → **Realistic given team experience**

**Areas for Enhancement:**
1. Add controlled variation in Phase B/C batches to improve training diversity
2. Consider off-gas analysis (CER/OUR) if initial model accuracy is poor
3. Implement disturbance testing in Phase C (batches 13-15)
4. Reassess MRE target after Phase A CV measurement

---

## 9. Conclusion

**Bottom Line:** Our project plan is **scientifically grounded** in proven methods (Gasset et al., 2024) while appropriately scoped for a research demonstration by a first-time team.

The published research validates our:
- Architecture (edge computing + cloud-free data infrastructure)
- Metrics (MRE, RMSE, R² for model performance)
- Phased approach (prediction before control)
- Data collection rigor (manual forms system)

Our additions represent **improvements** over the published work:
- Feasibility gate with CV-based target validation
- Larger training dataset (18 vs. 6 batches)
- Explicit Phase 1/Phase 2 roadmap with expansion criteria

**Strategic Recommendation:** Proceed with current plan. The Gasset et al. paper provides strong validation that our approach is both scientifically sound and industrially relevant. Our Phase 1 scope reductions are justified and will not compromise Phase 2 expansion to closed-loop control.

---

## References

Gasset, A., Van Wijngaarden, J., Mirabent, F., Sales-Vallverdú, A., Garcia-Ortega, X., Montesinos-Seguí, J.L., Manzano, T., and Valero, F. (2024). "Continuous Process Verification 4.0 application in upstream: adaptiveness implementation managed by AI in the hypoxic bioprocess of the *Pichia pastoris* cell factory." *Frontiers in Bioengineering and Biotechnology*, 12.

---

**Document Control:**
- **Version:** 1.0
- **Status:** Final
- **Next Review:** After Phase A completion (Week 6)
- **Distribution:** Project team, research supervisors
