# Data Pipeline Service

Real-time data cleaning, validation, and feature engineering for the Bioprocess Digital Twin.

## Overview

The Data Pipeline Service is a critical component of the Bioprocess Digital Twin system that:

1. **Cleans & Validates** sensor data in real-time (Section 5.1 of technical plan)
2. **Engineers Features** from 30-second windows including CER, OUR, RQ, μ, kLa (Section 5.2)
3. **Monitors Quality** and sends alerts for data anomalies
4. **Publishes Features** to InfluxDB for model consumption and Grafana visualization

## Architecture

```
Sensors (1 Hz) → MQTT → Telegraf → InfluxDB (pichia_raw)
                                         ↓
                                    Flux Task (30s aggregation)
                                         ↓
                                    InfluxDB (pichia_30s)
                                         ↓
                          Data Pipeline Service (Python/FastAPI)
                          ├── Data Cleaning & Validation
                          ├── Feature Engineering (CER/OUR/RQ/μ/kLa)
                          └── Monitoring & Alerting
                                         ↓
                              InfluxDB (pichia_pred) + MQTT Alerts
```

## Features

### Data Cleaning (data_cleaning.py)

- **Missing Data Handling**:
  - Linear interpolation for gaps < 5 minutes
  - Kalman filter for gaps 5-30 minutes
  - Alarm generation for gaps > 30 minutes

- **Outlier Detection**:
  - Z-score based detection (threshold: 3σ)
  - Automatic clipping to physical bounds

- **Physical Bounds Validation**:
  - Validates all sensor values against configured ranges
  - Sets invalid values to NaN and generates alarms

### Feature Engineering (feature_engineering.py)

#### Basic Features (all sensors)
- Mean, standard deviation, min, max, slope

#### Derived Rates (Off-Gas Balance)
- **CER** (Carbon Evolution Rate, mol CO₂/L/h)
- **OUR** (Oxygen Uptake Rate, mol O₂/L/h)
- **RQ** (Respiratory Quotient, CER/OUR)

#### Growth Metrics
- **μ** (Specific growth rate, h⁻¹) - Savitzky-Golay derivative of ln(OD)
- **qO₂** (Specific oxygen uptake rate, mol/gDCW/h)
- **qCO₂** (Specific CO₂ production rate, mol/gDCW/h)

#### Mass Transfer
- **kLa** (Volumetric mass transfer coefficient, h⁻¹)

#### Thermal Features
- Temperature gradients (broth vs. exhaust)
- Sensor agreement checks (pH probe, DO probe temperatures)
- Motor thermal state monitoring

#### Pressure Features
- Pressure deviation from atmospheric
- Pressure anomaly detection (foam, blockage)

#### Process State
- Phase detection: lag, exponential, stationary
- Cumulative sums: total CO₂, O₂, integrated OD

### Monitoring & Alerting (monitoring.py)

- **Prometheus Metrics**:
  - Window processing counters
  - Data quality scores per sensor
  - Feature value gauges
  - Processing duration histograms

- **MQTT Alerts**:
  - Data quality alarms
  - Sensor failure notifications
  - Process anomaly warnings
  - Metabolic shift detection

## API Endpoints

### Status & Control

- `GET /` - Health check
- `GET /health` - Detailed health status
- `GET /status` - Pipeline status and cycle count
- `POST /start` - Start continuous pipeline processing
- `POST /stop` - Stop pipeline
- `POST /reset` - Reset for new batch

### Processing

- `POST /process-window` - Manually trigger single window processing
- `GET /quality-stats` - Get cumulative data quality statistics
- `GET /config` - Get current pipeline configuration

### Monitoring

- `GET /metrics` - Prometheus metrics endpoint (via monitoring module)

## Configuration

Environment variables (configured in docker-compose.yml):

| Variable | Default | Description |
|----------|---------|-------------|
| `MQTT_BROKER` | `mosquitto` | MQTT broker hostname |
| `MQTT_PORT` | `1883` | MQTT broker port |
| `INFLUX_URL` | `http://influxdb:8086` | InfluxDB URL |
| `INFLUX_TOKEN` | - | InfluxDB authentication token |
| `INFLUX_ORG` | `bioprocess` | InfluxDB organization |
| `INFLUX_BUCKET_RAW` | `pichia_raw` | Raw 1 Hz data bucket |
| `INFLUX_BUCKET_30S` | `pichia_30s` | 30s aggregated bucket |
| `INFLUX_BUCKET_PRED` | `pichia_pred` | Predictions/features bucket |
| `WINDOW_SIZE_SECONDS` | `30` | Processing window size |
| `PROCESSING_INTERVAL_SECONDS` | `30` | Processing frequency |
| `VESSEL_ID` | `vessel1` | Vessel identifier |
| `LOG_LEVEL` | `INFO` | Logging level |

## Deployment

### Docker Compose (Recommended)

```bash
# From edge/ directory
docker-compose up -d data-pipeline

# View logs
docker-compose logs -f data-pipeline

# Check health
curl http://localhost:8001/health
```

### Standalone

```bash
# Install dependencies
pip install -r requirements.txt

# Run service
python -m app.main

# Or with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements.txt pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_feature_engineering.py -v
```

### Project Structure

```
data-pipeline/
├── app/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── data_cleaning.py       # Data cleaning & validation (Section 5.1)
│   ├── feature_engineering.py # Feature engineering (Section 5.2)
│   ├── influx_client.py       # InfluxDB client wrapper
│   ├── pipeline.py            # Main orchestrator
│   ├── monitoring.py          # Prometheus + MQTT monitoring
│   └── main.py                # FastAPI application
├── tests/
│   ├── conftest.py
│   ├── test_data_cleaning.py
│   └── test_feature_engineering.py
├── Dockerfile
├── requirements.txt
├── pytest.ini
└── README.md
```

## Usage Examples

### Starting the Pipeline via API

```bash
# Start continuous processing
curl -X POST http://localhost:8001/start

# Get status
curl http://localhost:8001/status

# Process single window manually
curl -X POST http://localhost:8001/process-window

# Stop pipeline
curl -X POST http://localhost:8001/stop
```

### Python Client Example

```python
import requests

# Start pipeline
response = requests.post("http://localhost:8001/start")
print(response.json())

# Check quality stats
stats = requests.get("http://localhost:8001/quality-stats").json()
print(f"Missing data: {stats['stats']['missing_count']}")
print(f"Outliers: {stats['stats']['outlier_count']}")
```

### Monitoring with Prometheus

The service exposes Prometheus metrics that can be scraped:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'data-pipeline'
    static_configs:
      - targets: ['data-pipeline:8001']
    metrics_path: '/metrics'
```

## Data Quality Thresholds

### Missing Data
- **< 5 min**: Linear interpolation applied
- **5-30 min**: Kalman filter applied
- **> 30 min**: Alarm generated, processing may fail

### Outliers
- Z-score threshold: **3σ**
- Action: Clip to mean ± 3σ

### Physical Bounds
See `config.py` for sensor-specific bounds. Examples:
- pH: 2.0 - 10.0
- DO: 0 - 100%
- Temperature (broth): 20 - 40°C

## Alerts

Alerts are published to MQTT topics:

```
bioprocess/pichia/{vessel_id}/alarms/data_quality
bioprocess/pichia/{vessel_id}/alarms/missing_data
bioprocess/pichia/{vessel_id}/alarms/sensor_failure
bioprocess/pichia/{vessel_id}/alarms/process_anomaly
bioprocess/pichia/{vessel_id}/alarms/metabolic_shift
bioprocess/pichia/{vessel_id}/alarms/equipment_warning
```

Alert payload format:
```json
{
  "timestamp": "2025-10-21T12:34:56.789Z",
  "level": "warning",
  "category": "data_quality",
  "message": "High missing data rate for pH: 18/30 samples",
  "vessel": "vessel1",
  "metadata": {
    "tag": "pH",
    "missing_count": 18
  }
}
```

## Performance

- **Processing Time**: ~100-500ms per 30s window (depends on sensor count)
- **Memory Usage**: ~200-300 MB
- **CPU Usage**: ~5-10% on Jetson AGX Orin

## Troubleshooting

### Pipeline not starting

Check InfluxDB connectivity:
```bash
curl http://localhost:8086/health
```

Check MQTT broker:
```bash
docker logs bioprocess-mosquitto
```

### No features being generated

Verify data is flowing into InfluxDB:
```bash
# Check raw bucket
influx query "from(bucket: \"pichia_raw\") |> range(start: -5m) |> limit(n: 10)"
```

### High missing data warnings

- Check sensor MQTT publishers are running
- Verify Telegraf is ingesting data: `docker logs bioprocess-telegraf`
- Check network connectivity

## Contributing

See main project [CONTRIBUTING.md](../../../CONTRIBUTING.md) for guidelines.

## License

MIT License - See [LICENSE](../../../LICENSE)

## References

- Technical Plan: `docs/technical-plan.md` (Sections 5.1, 5.2)
- InfluxDB Client Docs: https://docs.influxdata.com/influxdb/v2.7/
- FastAPI Docs: https://fastapi.tiangolo.com/
