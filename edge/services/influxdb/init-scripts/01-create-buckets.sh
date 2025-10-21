#!/bin/bash
# InfluxDB Initialization Script
# Creates additional buckets for 30s aggregated data and predictions

set -e

echo "Waiting for InfluxDB to be ready..."
sleep 10

# Get configuration from environment
INFLUX_HOST="${INFLUX_HOST:-http://localhost:8086}"
INFLUX_TOKEN="${INFLUX_TOKEN:-my-super-secret-auth-token}"
INFLUX_ORG="${INFLUX_ORG:-bioprocess}"

echo "Creating buckets..."

# Create pichia_30s bucket (30-second aggregated sensor data)
influx bucket create \
  --host "${INFLUX_HOST}" \
  --token "${INFLUX_TOKEN}" \
  --org "${INFLUX_ORG}" \
  --name pichia_30s \
  --retention 0 \
  || echo "Bucket pichia_30s already exists"

# Create pichia_pred bucket (model predictions)
influx bucket create \
  --host "${INFLUX_HOST}" \
  --token "${INFLUX_TOKEN}" \
  --org "${INFLUX_ORG}" \
  --name pichia_pred \
  --retention 0 \
  || echo "Bucket pichia_pred already exists"

echo "Buckets created successfully!"
echo "- pichia_raw: Raw 1 Hz sensor data (created by init)"
echo "- pichia_30s: 30-second aggregated data"
echo "- pichia_pred: Model predictions and derived features"
