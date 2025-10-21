# Batch Data Export Guide

This guide shows you how to export batch data from the manual data collection system.

## Quick Reference

The export endpoint supports three formats:
- **CSV** - For digital twin model training (samples data only)
- **Markdown** - For OneNote lab notebooks (complete batch report)
- **JSON** - For programmatic access (complete batch data)

---

## Usage

### Option 1: Using the API Directly

```bash
# Get your batch ID from the web interface or API
BATCH_ID="your-batch-uuid-here"
TOKEN="your-auth-token"

# Export as Markdown (for OneNote)
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/batches/$BATCH_ID/export?format=markdown" \
  -o batch_report.md

# Export as CSV (for model training)
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/batches/$BATCH_ID/export?format=csv" \
  -o batch_samples.csv

# Export as JSON (for data pipelines)
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/batches/$BATCH_ID/export?format=json" \
  -o batch_data.json
```

### Option 2: Using Python

```python
import requests
import pandas as pd

# Login and get token
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"username": "admin", "password": "admin123"}
)
token = response.json()["access_token"]

# Get batch ID (example: list all completed batches)
headers = {"Authorization": f"Bearer {token}"}
batches = requests.get(
    "http://localhost:8000/api/v1/batches?status=complete",
    headers=headers
).json()

batch_id = batches[0]["batch_id"]  # Use first completed batch

# Export as CSV for model training
csv_url = f"http://localhost:8000/api/v1/batches/{batch_id}/export?format=csv"
csv_data = requests.get(csv_url, headers=headers).text

# Load into pandas
from io import StringIO
df = pd.read_csv(StringIO(csv_data))

print(df.head())
# Output:
#   batch_id  batch_number phase  timepoint_hours  od600_raw  ...
#   uuid-123  1            A      0.0              0.42       ...
#   uuid-123  1            A      4.0              2.10       ...
```

---

## Export Formats

### 1. CSV Format (for Digital Twin Training)

**File:** `batch_{number}_phase_{phase}_samples.csv`

**Columns:**
- `batch_id` - UUID of the batch
- `batch_number` - Batch number (1-18)
- `phase` - Campaign phase (A/B/C)
- `timepoint_hours` - Hours post-inoculation
- `od600_raw` - Raw OD reading
- `od600_dilution_factor` - Dilution factor applied
- `od600_calculated` - Calculated OD (raw × dilution)
- `dcw_g_per_l` - Dry cell weight (g/L)
- `contamination_detected` - Boolean flag
- `sampled_at` - Timestamp (ISO 8601)

**Use Case:** Load this directly into your model training pipeline to join with InfluxDB sensor data.

**Example Training Script:**
```python
# Load manual DCW labels
manual_data = pd.read_csv("batch_1_phase_A_samples.csv")

# Load sensor data from InfluxDB
sensor_data = query_influx(
    f"SELECT * FROM sensors WHERE batch_id = '{batch_id}'"
)

# Join on timepoint_hours for model training
training_data = sensor_data.merge(
    manual_data[["timepoint_hours", "dcw_g_per_l"]],
    on="timepoint_hours",
    how="inner"
)

# Now you have features (sensor data) + labels (DCW)
X = training_data[["pH", "DO", "temp", "OD", "CER", "OUR"]]
y = training_data["dcw_g_per_l"]
```

---

### 2. Markdown Format (for OneNote Lab Notebook)

**File:** `batch_{number}_phase_{phase}_report.md`

**Contains:**
- Batch metadata (vessel, operator, timestamps)
- Calibration results table
- Inoculation details
- Sample observations table
- Failures/deviations (if any)
- Batch closure summary

**Use Case:** Copy/paste into OneNote, GitHub, or any Markdown-compatible lab notebook.

**Example Output:**
```markdown
# Batch #1 - Phase A

**Vessel:** V-FR-01
**Operator:** admin
**Status:** complete
**Created:** 2025-10-21 08:00
**Inoculated:** 2025-10-21 10:30
**Completed:** 2025-10-22 14:30 (28.0h runtime)

---

## Pre-Run Calibrations

| Probe | Buffer Low | Buffer High | Reading Low | Reading High | Slope % | Pass |
|-------|-----------|-------------|-------------|--------------|---------|------|
| pH | 4.01 | 7.00 | 4.03 | 6.98 | 98.5% | ✅ PASS |
| DO | 0.0 | 100.0 | 0.1 | 99.8 | - | ✅ PASS |

## Inoculation

- **Cryo Vial:** CRYO-001
- **Inoculum OD₆₀₀:** 4.20
- **Volume:** 100.0 mL
- **GO Decision:** ✅ GO
- **Inoculated by:** admin

## Sample Observations

| Time (h) | OD₆₀₀ (raw) | Dilution | OD₆₀₀ (calc) | DCW (g/L) | Contamination | Sampled By |
|----------|-------------|----------|--------------|-----------|---------------|------------|
| 0.0 | 0.420 | 1.0× | 0.42 | 0.14 | ✅ No | admin |
| 4.0 | 2.100 | 1.0× | 2.10 | 0.69 | ✅ No | admin |
| 8.0 | 5.300 | 1.0× | 5.30 | 1.75 | ✅ No | admin |
...

**Total samples:** 8

---

*Exported: 2025-10-21 15:00 UTC*
```

**Copy/Paste to OneNote:**
1. Open the Markdown file in any text editor
2. Select all (Ctrl+A) and copy (Ctrl+C)
3. Paste into OneNote - it will auto-format tables and headings!

---

### 3. JSON Format (for Data Pipelines)

**File:** Returns JSON directly (no file download)

**Contains:** Complete batch record with all child records as nested JSON.

**Use Case:** Integrate with automated data pipelines, send to data lakes, or process with scripts.

**Example:**
```json
{
  "batch": {
    "batch_id": "uuid-here",
    "batch_number": 1,
    "phase": "A",
    "vessel_id": "V-FR-01",
    "status": "complete",
    ...
  },
  "samples": [
    {
      "timepoint_hours": 0.0,
      "od600_calculated": 0.42,
      "dcw_g_per_l": 0.14,
      ...
    }
  ],
  ...
}
```

---

## Bulk Export (All Batches)

To export all completed batches for model training:

```python
import requests
import pandas as pd
from io import StringIO

# Login
token = get_auth_token()
headers = {"Authorization": f"Bearer {token}"}

# Get all completed batches
batches = requests.get(
    "http://localhost:8000/api/v1/batches?status=complete&limit=100",
    headers=headers
).json()

# Export each batch to CSV
all_samples = []

for batch in batches:
    batch_id = batch["batch_id"]
    csv_data = requests.get(
        f"http://localhost:8000/api/v1/batches/{batch_id}/export?format=csv",
        headers=headers
    ).text

    df = pd.read_csv(StringIO(csv_data))
    all_samples.append(df)

# Combine all batches
combined_df = pd.concat(all_samples, ignore_index=True)
combined_df.to_csv("all_batches_training_data.csv", index=False)

print(f"Exported {len(batches)} batches with {len(combined_df)} total samples")
```

---

## Tips

### For Model Training:
- Use CSV format - it's the fastest and easiest to load
- The `timepoint_hours` field is critical for joining with InfluxDB sensor data
- Filter out contaminated samples: `df[df["contamination_detected"] == False]`

### For Lab Notebooks:
- Use Markdown format - it renders beautifully in OneNote, GitHub, and Notion
- Keep the .md files in your lab notebook repo for version control
- The emoji indicators (✅/❌/🟡/🟠/🔴) make it easy to spot issues at a glance

### For Data Archival:
- Use JSON format - it's complete and structured
- Store in your data lake (MinIO/S3) alongside InfluxDB exports
- Easy to parse with jq or load into document databases

---

## Accessing from the Web Interface

*(Coming soon: Export button in the batch detail view)*

For now, use the API endpoints above or access via Swagger docs at:
`http://localhost:8000/api/v1/docs`

Search for "export_batch" endpoint and click "Try it out".

---

## Troubleshooting

**"Batch not found" error:**
- Check that the batch_id is correct (it's a UUID, not the batch number)
- Ensure you have permission to view the batch

**Empty CSV file:**
- The batch may not have any samples yet
- Check batch status - it should be "running" or "complete"

**Markdown formatting issues in OneNote:**
- OneNote may not support all Markdown features
- Tables should work fine, but nested formatting might get flattened
- Alternative: Use the Markdown preview in VS Code, then screenshot and paste

---

## Next Steps

1. **Test the export:** Create a test batch with mock data and export it
2. **Integrate with training:** Add CSV export to your model training pipeline
3. **Archive batches:** Set up a cron job to export completed batches to MinIO

For questions, see the main documentation or contact the development team.
