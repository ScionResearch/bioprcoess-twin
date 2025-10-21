# Export Feature - Quick Summary

## What I Just Added ✅

A comprehensive batch export endpoint with **3 formats** designed for different use cases:

### 1. **CSV Export** - For Your Digital Twin
```bash
GET /api/v1/batches/{batch_id}/export?format=csv
```

**Perfect for model training:**
- Contains: `timepoint_hours`, `od600_calculated`, `dcw_g_per_l`
- Clean, simple format
- Ready to join with InfluxDB sensor data
- One row per sample

**Example:**
```csv
batch_id,batch_number,phase,timepoint_hours,od600_raw,od600_dilution_factor,od600_calculated,dcw_g_per_l,contamination_detected,sampled_at
uuid-123,1,A,0.0,0.42,1.0,0.42,0.14,False,2025-10-21T10:30:00
uuid-123,1,A,4.0,2.10,1.0,2.10,0.69,False,2025-10-21T14:30:00
...
```

---

### 2. **Markdown Export** - For OneNote Lab Notebook
```bash
GET /api/v1/batches/{batch_id}/export?format=markdown
```

**Perfect for documentation:**
- Beautiful formatted tables
- Copy/paste directly into OneNote
- Includes everything: calibrations, samples, failures, closure
- Emoji indicators for quick visual scanning

**Example:**
```markdown
# Batch #1 - Phase A

**Vessel:** V-FR-01
**Status:** complete
**Runtime:** 28.0h

## Sample Observations

| Time (h) | OD₆₀₀ (calc) | DCW (g/L) | Contamination |
|----------|--------------|-----------|---------------|
| 0.0      | 0.42         | 0.14      | ✅ No          |
| 4.0      | 2.10         | 0.69      | ✅ No          |
```

Just open the .md file, copy all, paste into OneNote - done!

---

### 3. **JSON Export** - For Data Pipelines
```bash
GET /api/v1/batches/{batch_id}/export?format=json
```

**Perfect for automation:**
- Complete structured data
- Easy to parse with Python/scripts
- Includes all relationships
- Ready for data lakes/archives

---

## How to Use

### From Browser:
1. Go to: `http://localhost:8000/api/v1/docs`
2. Find `GET /batches/{batch_id}/export`
3. Click "Try it out"
4. Enter your batch ID and select format
5. Click "Execute" and download the file

### From Python:
```python
import requests
import pandas as pd
from io import StringIO

# Get CSV for model training
response = requests.get(
    f"http://localhost:8000/api/v1/batches/{batch_id}/export?format=csv",
    headers={"Authorization": f"Bearer {token}"}
)

df = pd.read_csv(StringIO(response.text))
```

### From Command Line:
```bash
# Export to file
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/batches/$BATCH_ID/export?format=markdown" \
  -o batch_report.md
```

---

## What This Solves

### ✅ For Digital Twin Training:
- Easy to extract DCW labels for model training
- Clean CSV format joins perfectly with InfluxDB data
- All timepoints aligned with `timepoint_hours` field

### ✅ For Lab Documentation:
- No more manual copy/paste of data into lab notebooks
- Beautiful, readable format for OneNote
- Complete batch record in one document

### ✅ For Data Archival:
- Export completed batches to backup storage
- Version control your batch records
- Share data with collaborators

---

## File Locations

- **Code:** `/home/tasman/projects/bioprocess-twin/api/app/routers/batches.py` (lines 218-538)
- **Documentation:** `/home/tasman/projects/bioprocess-twin/docs/EXPORT_GUIDE.md`

---

## Next Steps

1. **Test it:** Start the API and try exporting a batch
2. **Integrate:** Add CSV export to your model training script
3. **Document:** Paste a Markdown export into your lab notebook

See `EXPORT_GUIDE.md` for detailed examples and troubleshooting.
