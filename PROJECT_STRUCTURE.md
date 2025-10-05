# Bioprocess Twin - Project Structure

**Repository Created:** 2025-10-05
**Location:** `bioprocess-twin/` (ready to copy to working location)

---

## Directory Tree

```
bioprocess-twin/
│
├── README.md                      ✅ Complete project overview
├── LICENSE                        ✅ MIT License
├── CHANGELOG.md                   ✅ Version history tracking
├── CONTRIBUTING.md                ✅ Contribution guidelines
├── .gitignore                     ✅ Python/Docker/Data exclusions
├── PROJECT_STRUCTURE.md           ✅ This file
│
├── docs/                          ✅ All planning documents
│   ├── README.md                  ✅ Documentation hierarchy guide
│   ├── project-plan.md            ✅ Copied from Project Plan.md
│   ├── batch-run-plan.md          ✅ Copied from Batch Run Plan.md
│   ├── technical-plan.md          ✅ Copied from Technical Plan.md
│   ├── manual-data-development.md ✅ Copied from Manual Data Development.md
│   ├── architecture/              📁 For diagrams (empty, ready for images)
│   ├── sops/                      📁 For SOPs (empty, ready for procedures)
│   └── references/
│       └── alignment-analysis-gasset2024.md ✅ Copied from references/
│
├── edge/                          ✅ Edge deployment (Jetson)
│   ├── docker-compose.yml         ✅ Full stack orchestration
│   ├── .env.example               ✅ Environment variable template
│   ├── services/
│   │   ├── digital-twin/          📁 Inference service (app/, models/)
│   │   ├── telegraf/              📁 Data ingestion
│   │   ├── influxdb/              📁 Time-series DB (init-scripts/)
│   │   ├── mosquitto/             📁 MQTT broker
│   │   └── grafana/               📁 Dashboards (provisioning/)
│   └── scripts/                   📁 Backup, deploy scripts
│
├── workstation/                   📁 Training workstation
│   ├── notebooks/                 📁 Jupyter notebooks (5 templates)
│   ├── training/                  📁 Training scripts
│   └── data-pipeline/             📁 ETL scripts
│
├── api/                           📁 FastAPI backend
│   ├── alembic/                   📁 Database migrations
│   ├── app/                       📁 main.py, models.py, routers/
│   └── tests/                     📁 API tests
│
├── webapp/                        📁 React tablet forms
│   ├── public/                    📁 Static assets
│   └── src/                       📁 components/, api/, schemas/
│
├── database/                      ✅ Postgres schema
│   ├── README.md                  ✅ Schema documentation
│   └── init.sql                   ✅ Complete schema (7 tables)
│
├── hardware/                      ✅ Hardware integration
│   ├── sensor-drivers/            📁 MQTT publishers (CO2, O2, pressure, temp)
│   ├── calibration-tools/         📁 Drift validation
│   └── datasheets/                📁 Sensor manuals
│
├── models/                        ✅ Model artifacts
│   └── README.md                  ✅ Model registry info
│
├── data/                          ✅ Local data (gitignored)
│   ├── raw/                       📁 Batch Parquet exports
│   └── processed/                 📁 Feature-engineered datasets
│
├── scripts/                       📁 Utility scripts
│   ├── setup/                     📁 Installation automation
│   ├── batch-management/          📁 CLI tools
│   └── monitoring/                📁 Health checks
│
├── tests/                         📁 Integration tests
│
└── .github/                       📁 CI/CD workflows
    └── workflows/                 📁 ci.yml, build-edge.yml, deploy.yml
```

**Legend:**
- ✅ = File/directory created with content
- 📁 = Directory created (empty, ready for development)

---

## Key Files Created

### Documentation (8 files)
1. `README.md` - Main project documentation (comprehensive)
2. `LICENSE` - MIT License
3. `CHANGELOG.md` - Version tracking
4. `CONTRIBUTING.md` - Contribution guidelines
5. `docs/README.md` - Documentation hierarchy
6. `docs/project-plan.md` - From your Project Plan.md
7. `docs/batch-run-plan.md` - From your Batch Run Plan.md
8. `docs/technical-plan.md` - From your Technical Plan.md
9. `docs/manual-data-development.md` - From your Manual Data Development.md
10. `docs/references/alignment-analysis-gasset2024.md` - From references/

### Configuration (4 files)
1. `.gitignore` - Excludes data, models, secrets, logs
2. `edge/docker-compose.yml` - 8-service stack (mosquitto, influxdb, telegraf, postgres, grafana, digital-twin, api, webapp)
3. `edge/.env.example` - Environment template
4. `database/init.sql` - Complete Postgres schema (batches + 7 child tables)

### Placeholder READMEs (5 files)
1. `models/README.md`
2. `database/README.md`
3. `edge/services/digital-twin/README.md`
4. `hardware/sensor-drivers/README.md`
5. `hardware/datasheets/README.md`

---

## Next Steps

### 1. Copy to Working Directory
```bash
# From current location (Obsidian folder):
cp -r bioprocess-twin /path/to/your/development/directory/
cd /path/to/your/development/directory/bioprocess-twin
```

### 2. Initialize Git Repository
```bash
git init
git add .
git commit -m "Initial commit: bioprocess-twin project structure

- Core planning documents from Digital Twin project
- Docker Compose edge stack (8 services)
- Postgres schema for manual data (batch-centric)
- Documentation hierarchy established
- 18-batch campaign framework (Phase A/B/C)
- Hardware integration structure (custom off-gas sensors)
- Model versioning structure
"
```

### 3. Create Remote Repository
```bash
# On GitHub/GitLab:
# 1. Create new repository named "bioprocess-twin"
# 2. Do NOT initialize with README (already have one)
# 3. Copy the remote URL

# Link local to remote:
git remote add origin https://github.com/yourorg/bioprocess-twin.git
git branch -M main
git push -u origin main
```

### 4. Set Up Development Environment
```bash
# Copy environment template
cp edge/.env.example edge/.env
# Edit edge/.env with your configuration

# Start edge stack (for testing)
cd edge
docker-compose up -d

# Verify services
docker-compose ps
```

---

## Development Priorities

### Immediate (Week 1-2)
- [ ] Implement sensor drivers in `hardware/sensor-drivers/`
  - `offgas_co2_mqtt.py`
  - `offgas_o2_mqtt.py`
  - `pressure_mqtt.py`
  - `temperature_multiplex_mqtt.py`
- [ ] Configure Telegraf (`edge/services/telegraf/telegraf.conf`)
- [ ] Create InfluxDB bucket initialization script
- [ ] Test MQTT → InfluxDB pipeline

### Short-term (Week 3-5)
- [ ] Build FastAPI backend (`api/app/`)
- [ ] Implement React tablet forms (`webapp/src/`)
- [ ] Create Grafana dashboards (`edge/services/grafana/provisioning/`)
- [ ] Develop feature engineering pipeline (`workstation/data-pipeline/`)

### Medium-term (Week 6-10)
- [ ] Execute Phase A batches (1-3)
- [ ] Validate sensor calibration procedures
- [ ] Establish OD-DCW correlation
- [ ] Measure process CV, set adaptive MRE target

### Long-term (Week 11-20)
- [ ] Train LightGBM model (Phase B data)
- [ ] Deploy model to Jetson edge
- [ ] Execute Phase C validation batches (16-18)
- [ ] Generate validation report (MRE ≤ 8%)
- [ ] Tag v1.0 release

---

## File Counts

- **Total directories created:** 45
- **Total files created:** 22
- **Planning documents:** 10 (all your key .md files)
- **Configuration files:** 4 (docker-compose, .env, .gitignore, init.sql)
- **Documentation files:** 8 (README, LICENSE, CHANGELOG, CONTRIBUTING, etc.)

---

## Repository Statistics (Estimated)

- **Lines of documentation:** ~8,000 (planning docs + SOPs)
- **Initial commit size:** ~500 KB (text only, no data/models)
- **Estimated final size:** ~2 GB (with models, data excluded from Git)

---

## Notes

1. **All planning documents preserved:** Your Project Plan, Batch Run Plan, Technical Plan, and Manual Data Development docs are now in `docs/` as the SSoT.

2. **Docker Compose ready:** The edge stack is configured for 8 services. Just need to add service-specific configs (Telegraf, Mosquitto, Grafana provisioning).

3. **Database schema complete:** The Postgres schema in `database/init.sql` matches your Technical Plan section 4.4 exactly (7 tables, all relationships).

4. **Git-friendly structure:** `.gitignore` excludes data, models, logs, and secrets. Models should use Git LFS or MinIO.

5. **Ready for collaboration:** README, CONTRIBUTING, and LICENSE files make this ready for open-source distribution.

---

**Repository is ready! Copy to your development directory and initialize Git.**
