# Data Pipeline Quick Start Guide

Get the data pipeline up and running in 5 minutes.

## Prerequisites

- Docker and Docker Compose installed
- InfluxDB and MQTT broker running (via main docker-compose)
- Python 3.11+ (for local development)

## Option 1: Docker Compose (Recommended)

### 1. Start the Edge Stack

```bash
cd edge/
docker-compose up -d
```

This starts all services including:
- mosquitto (MQTT broker)
- influxdb (time-series database)
- telegraf (data ingestion)
- **data-pipeline** (cleaning + feature engineering)
- grafana (visualization)

### 2. Verify Pipeline is Running

```bash
# Check container status
docker-compose ps data-pipeline

# View logs
docker-compose logs -f data-pipeline

# Check health
curl http://localhost:8001/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-21T12:34:56.789Z",
  "service": "data-pipeline",
  "version": "0.1.0"
}
```

### 3. Start Processing

```bash
# Start continuous processing (30s intervals)
curl -X POST http://localhost:8001/start

# Check status
curl http://localhost:8001/status
```

### 4. Monitor Pipeline

```bash
# Get quality statistics
curl http://localhost:8001/quality-stats

# View Prometheus metrics
curl http://localhost:8001/metrics
```

## Option 2: Local Development

### 1. Install Dependencies

```bash
cd edge/services/data-pipeline/

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Set environment variables
export INFLUX_URL=http://localhost:8086
export INFLUX_TOKEN=my-super-secret-auth-token
export INFLUX_ORG=bioprocess
export MQTT_BROKER=localhost
export MQTT_PORT=1883
export LOG_LEVEL=DEBUG
```

Or create a `.env` file:
```bash
INFLUX_URL=http://localhost:8086
INFLUX_TOKEN=my-super-secret-auth-token
INFLUX_ORG=bioprocess
MQTT_BROKER=localhost
MQTT_PORT=1883
LOG_LEVEL=DEBUG
```

### 3. Run the Service

```bash
# Option A: Direct Python
python -m app.main

# Option B: Uvicorn with hot reload
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 4. Run Tests

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_data_cleaning.py::test_clean_valid_data -v
```

## Common Operations

### Process a Single Window

```bash
curl -X POST http://localhost:8001/process-window
```

Response:
```json
{
  "timestamp": "2025-10-21T12:34:56.789Z",
  "features": {
    "pH_mean": 7.02,
    "DO_mean": 58.3,
    "OD_mean": 2.45,
    "CER": 0.0142,
    "OUR": 0.0138,
    "RQ": 1.03,
    "mu": 0.152,
    ...
  },
  "feature_count": 68
}
```

### Get Pipeline Status

```bash
curl http://localhost:8001/status
```

Response:
```json
{
  "is_running": true,
  "cycle_count": 42,
  "quality_stats": {
    "missing_count": 5,
    "outlier_count": 18,
    "invalid_count": 0,
    "interpolated_count": 5,
    "kalman_filtered_count": 0
  }
}
```

### Reset for New Batch

```bash
curl -X POST http://localhost:8001/reset
```

### Stop Pipeline

```bash
curl -X POST http://localhost:8001/stop
```

## Monitoring

### View Logs

```bash
# Docker
docker-compose logs -f data-pipeline

# Local
# Logs are written to stdout by default
```

### Prometheus Metrics

Access metrics at: http://localhost:8001/metrics

Key metrics to watch:
- `pipeline_windows_processed_total` - Total windows processed
- `pipeline_data_quality_score` - Quality score per sensor
- `pipeline_processing_duration_seconds` - Processing time

### MQTT Alerts

Subscribe to alerts:

```bash
# Install mosquitto clients
sudo apt-get install mosquitto-clients

# Subscribe to all alerts
mosquitto_sub -h localhost -p 1883 -t "bioprocess/pichia/vessel1/alarms/#" -v
```

## Troubleshooting

### Pipeline Not Starting

**Problem:** `curl http://localhost:8001/health` fails

**Solutions:**
```bash
# Check if container is running
docker-compose ps data-pipeline

# Check logs for errors
docker-compose logs data-pipeline

# Restart service
docker-compose restart data-pipeline
```

### No Features Generated

**Problem:** Pipeline runs but no features appear in InfluxDB

**Solutions:**
```bash
# 1. Check if raw data exists
docker exec -it bioprocess-influxdb influx query \
  --org bioprocess \
  --token my-super-secret-auth-token \
  'from(bucket: "pichia_raw") |> range(start: -5m) |> limit(n: 10)'

# 2. Check Telegraf is running
docker-compose logs telegraf

# 3. Verify sensor data is publishing to MQTT
mosquitto_sub -h localhost -p 1883 -t "bioprocess/pichia/#" -v

# 4. Manually trigger processing
curl -X POST http://localhost:8001/process-window
```

### High Missing Data Warnings

**Problem:** Quality stats show high missing data counts

**Solutions:**
1. Check sensor publishers are running
2. Verify MQTT connectivity
3. Check InfluxDB write permissions
4. Review Telegraf configuration

### Processing Errors

**Problem:** Pipeline stops with errors

**Solutions:**
```bash
# Check detailed logs
docker-compose logs --tail=100 data-pipeline

# Common issues:
# - InfluxDB connection timeout → Check network/token
# - MQTT broker unreachable → Verify mosquitto is running
# - Out of memory → Increase Docker memory limit
```

## Next Steps

1. **Start Sensor Publishers** - Publish real sensor data to MQTT
2. **Configure Grafana** - Visualize features in real-time
3. **Set Up Alerting** - Configure alert handlers (email, Slack)
4. **Train Models** - Use generated features for model training

## API Reference

Full API documentation: http://localhost:8001/docs (FastAPI auto-generated docs)

## Support

- Main README: `README.md`
- Technical Plan: `../../../docs/technical-plan.md`
- Implementation Summary: `../../../docs/data-pipeline-implementation.md`
- Issues: https://github.com/your-org/bioprocess-twin/issues
