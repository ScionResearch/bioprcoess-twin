# **Bioprocess Digital Twin – COMPLETE PROJECT PLAN**
**Research Edition | *Pichia pastoris* | Glycerol Batch | Edge-First**

|                   |                                       |
| ----------------- | ------------------------------------- |
| **Project Name:** | Pichia pastoris Digital Twin v1.0     |
| **Author:**       | Tasman                                |
| **Date:**         | October 3, 2025                       |
| **Status:**       | **Issue 1.0 – Ready for Gate Review** |

---

## **1.0 EXECUTIVE SUMMARY**
This project will build an open-source, edge-based **digital shadow** for *Pichia pastoris* fermentations. The initial phase focuses on modeling the biomass accumulation (glycerol batch) phase. The system will predict optical density (OD₆₀₀) with a Mean Relative Error (MRE) of ≤ 8% (stretch goal: ≤ 6%) after a development campaign of 18 sequential batches executed over 20 weeks. The entire stack runs on-premise and is designed as a template for rapid adoption by biotechnology research labs and start-ups.

---

## **2.0 OBJECTIVES & SUCCESS CRITERIA**
| Metric | Target | Method of Verification |
|---|---|---|
| **Primary:** Predictive Accuracy | MRE ≤ 8 % (30s OD prediction), **Adaptive**: ≤ 6% if Phase A CV <5% | Validation report on hold-out data (Batches 16-18). |
| **Secondary:** Model Robustness | R² >0.90, RMSE <5% (DO) | Validation report on hold-out data (Batches 16-18). |
| Feasibility Gate | Process CV measured after Phase A (Batches 1-3) to set realistic MRE target = 2× CV | Phase A analysis report with Go/No-Go decision. |
| Real-time Performance | < 1 s inference latency | Grafana dashboard monitoring P99 latency. |
| Manual Data Integrity | < 1 % entry error rate | Achieved via dropdowns, QR scans, and schema validation. |
| System Reliability | ≥ 95 % system uptime | Prometheus uptime monitoring of all Docker containers. |
| Project Duration | 20 weeks | From project kick-off to v1.0 tag in Git. |

**Note on Adaptive Target:** Research by Gasset et al. (2024) achieved MRE 3.5-4.0% on fed-batch *P. pastoris* RQ control (more complex process). If Phase A reveals our glycerol batch process has CV <5%, we will tighten the MRE target to ≤6% as primary criterion, positioning this work competitively with published research.

---

## **3.0 SCOPE**

**IN SCOPE**
-   **Organism:** *Pichia pastoris*
-   **Process:** Simple glycerol batch phase for biomass accumulation.
-   **Hardware:** 1–2 lab-scale vessels, on-premise Jetson Orin and GPU workstation, custom off-gas sensors (CO₂ + O₂), reactor pressure transducer, multiple temperature probes (broth, probes, motor, exhaust).
-   **Data:** High-frequency sensor data (pH, DO, OD, pressure, off-gas CO₂/O₂, gas flows, temperatures) and all manual context data (media prep, sampling, calibration) via tablet forms.
-   **Derived Variables:** CER, OUR, RQ, μ, qO₂, qCO₂, kLa calculated from sensor data, gas balances, and pressure-corrected mass flows.
-   **Outcome:** A predictive digital shadow. Control system paths are implemented but disabled (`CONTROL_MODE=0`).
-   **Sensor Reliability Monitoring:** Automated drift detection for custom off-gas sensors; contingency budget for integrated analyzer upgrade if reliability issues arise.

**OUT OF SCOPE**
-   Methanol fed-batch process modeling and control (Phase 2).
-   Recombinant protein expression quantification and prediction (Phase 2).
-   RQ-based closed-loop control (Phase 2 - requires validation of prediction accuracy first).
-   GMP compliance and 21 CFR Part 11 electronic signatures (Phase 3).
-   Cloud computing or data storage.

---

## **4.0 HIGH-LEVEL ARCHITECTURE**
```
                                     ┌─────────────────────────┐
                                     │   Tablet / Manual Forms │
                                     └────────────┬────────────┘
                                                  │ (HTTPS)
Sensors (1Hz) ──MQTT──► Telegraf ──► InfluxDB ◄── FastAPI ──► Postgres
                                          │          (raw)         ▲ (SQL)       (audit)
                                          │ 30s agg                │
                                          ▼                        │
                                     ┌──────────────────┐          │ (MQTT)
                                     │ Jetson Inference │◄─────────┘
                                     └──────────────────┘
                                          │ (prediction)
                                          ▼
                                     MQTT & InfluxDB
                                          │ (pred)
                                          ▼
                                       Grafana
```

---

## **5.0 WORK BREAKDOWN STRUCTURE (WBS)**
| WBS | Task                        | Deliverable                            | Owner       | Week      |
| --- | --------------------------- | -------------------------------------- | ----------- | --------- |
| 1.0 | **Initiation & Setup**      |                                        |             | **0-2**   |
| 1.1 | Procure Hardware            | BOM, Receipts                          | PL          | 0         |
| 1.2 | Deploy Edge Stack           | `docker-compose.yml`, running services | DevOps      | 1-2       |
| 2.0 | **Data & Pipeline**         |                                        |             | **1-5**   |
| 2.1 | Integrate Sensors           | Live sensor data in Grafana            | Data Eng    | 1-2       |
| 2.2 | Develop Form Suite          | React SPA & FastAPI backend            | SW Eng      | 2-5       |
| 2.3 | Build Data Pipeline         | Feature engineering script             | Data Eng    | 3-5       |
| 3.0 | **Modeling & Fermentation** |                                        |             | **3-18**  |
| 3.1 | Develop Baseline Model      | Training notebook, LightGBM v0.1       | ML Eng      | 3-6       |
| 3.2 | Execute 18 Batches          | Labeled Parquet datasets in MinIO      | Process Eng | 3-18      |
| 3.3 | Tune & Validate Model       | MRE ≤ 8% report, SHAP plots            | ML Eng      | 12-18     |
| 4.0 | **Finalization**            |                                        |             | **18-20** |
| 4.1 | Document & Train Users      | SOPs, training video, quick-cards      | PL          | 18-19     |
| 4.2 | Go-Live Gate Review         | Signed checklist                       | All         | 20        |
| 4.3 | Tag v1.0 Release            | Public GitHub repo, Docker images      | DevOps      | 20        |

---

## **6.0 RESOURCE SUMMARY**

**Hardware & Equipment:**
- Jetson AGX Orin 64 GB (edge inference)
- GPU Workstation (RTX 4080) for model training
- Rugged tablets (2×) for manual data entry
- Sensors: pH, DO, OD probes; pressure transducer; RTDs
- Off-gas sensors (CO₂, O₂) with signal conditioning
  - **Fallback**: Integrated off-gas analyzer (BlueSens BlueInOne FERM or Servomex) if custom sensors show drift >0.2%, RSD >5%, or failure rate >20%
- Network infrastructure (switch, cables, QR labels, DAQ interface)

**Personnel:**
- 1.0 FTE internal research staff (funded by existing budget)

**Software:**
- All open-source stack (PostgreSQL, FastAPI, React, LightGBM)

---

## **7.0 RISK REGISTER**
| Risk | P | I | Mitigation Strategy | Owner |
|---|---|---|---|---|
| Techs reject tablet forms | M | H | Co-design UI with lab staff; use QR codes to minimize typing; provide 5-min video SOP. | PL |
| 18 batches delayed | M | M | Timeline assumes 1 batch/week with buffer time; maintain robust media/inoculum pipeline. | Process Eng |
| Model fails to converge (MRE >8%) | M | M | **Primary**: Off-gas analysis (CER/OUR/RQ) already included in sensor suite for metabolic state inference. **Secondary**: Increase batch count to 25 with controlled variation; try LSTM for temporal dynamics. | ML Eng |
| Insufficient features (pH/DO/temp only) | L | M | **Mitigated**: Off-gas analyzer (BlueSens) included in hardware spec for CER/OUR/RQ calculation. Provides direct metabolic measurements per Gasset et al. (2024). | ML Eng |
| High process variability (CV >8%) | M | H | Phase A feasibility gate will detect early. If CV >8%, extend Phase A to investigate root causes (media prep, inoculum quality, control tuning) before proceeding. | Process Eng |
| Sensor drift (pH/DO/off-gas) | M | H | Enforce weekly 2-point calibration for all probes (pH, DO, off-gas O₂/CO₂); auto-flag data from non-compliant probes; verify calibration slope >95% for pH. | Process Eng |
| Jetson hardware failure | L | H | Maintain nightly backups to workstation; keep spare SSD and power supply on-site. | DevOps |
| Technician availability | M | M | Cross-train 2+ technicians on all procedures; maintain documented SOPs for continuity. | Process Eng |
| Off-gas sensor calibration drift | M | M | Weekly 2-point calibration (N₂ for 0% O₂, air for 20.9% O₂ and 0% CO₂). **Custom sensors**: Auto-flag if drift >0.2% between calibrations. **Trigger upgrade** to integrated analyzer (BlueSens/Servomex) if failure rate >20% or RSD >5%. | Process Eng |
| Custom off-gas sensor unreliability | M | H | **Phase A evaluation**: If custom CO₂/O₂ sensors show drift >0.2%, RSD >5%, or require recalibration >weekly, activate $5K contingency budget for integrated analyzer (BlueSens BlueInOne FERM). Gasset et al. used integrated analyzer with humidity correction and silica column. | Process Eng |

---

## **8.0 MANUAL DATA & FORM SUB-SYSTEM**
This sub-system is critical for capturing the ground-truth context of each batch.
-   **Technology:** React SPA (with JSON-Schema forms) on Nginx, FastAPI backend, Postgres DB.
-   **Forms:** MEDIA, INOCULATION, CALIBRATION, SAMPLE, PROCESS-CHANGE, FAILURE, BATCH-END.
-   **UX Principles:** Glove-friendly, one-hand operation, offline-first (auto-retry queue), visual/haptic feedback on success.
-   **Quality Gates:**
    1.  Two technicians complete a full set of forms for a mock batch in under 15 minutes.
    2.  An offline-submitted form appears in Postgres within 30 seconds of Wi-Fi restoration.
    3.  A daily backup (`pg_dump`) to MinIO is successfully restored on a test machine.

---

## **9.0 GO-LIVE GATE CHECKLIST**
*Formal sign-off required to close the project and tag version 1.0.*

| Item                                                                                   | Sign-off     | Date |
| -------------------------------------------------------------------------------------- | ------------ | ---- |
| 1. All 18 batch datasets are complete and stored in MinIO.                             | Process Lead |      |
| 2. Final model MRE meets adaptive target (≤8% baseline, OR ≤6% if Phase A CV <5%) on hold-out test set. Report attached. | ML Eng Lead  |      |
| 3. Off-gas analyzer calibration records complete for all batches; CER/OUR/RQ data validated. | Process Lead |      |
| 4. All tablet forms have been used successfully in live runs; no critical bugs remain. | Project Lead |      |
| 5. System backup and restore procedure has been tested and documented.                 | DevOps       |      |
| 6. Risk register reviewed; all residual risks are formally accepted.                   | Project Lead |      |

**Gate Approval Action:** Tag repository as `v1.0`, publish documentation, and transition project to maintenance mode. The `CONTROL_MODE` environment variable remains `0` (disabled). Off-gas analysis system validated and ready for Phase 2 RQ-based control development.