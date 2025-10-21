"""
Pytest configuration and shared fixtures
"""
import pytest
import os


@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables"""
    os.environ["INFLUX_URL"] = "http://localhost:8086"
    os.environ["INFLUX_TOKEN"] = "test-token"
    os.environ["INFLUX_ORG"] = "test-org"
    os.environ["MQTT_BROKER"] = "localhost"
    os.environ["MQTT_PORT"] = "1883"
    os.environ["LOG_LEVEL"] = "DEBUG"


@pytest.fixture
def mock_influx_data():
    """Mock InfluxDB query results"""
    import pandas as pd
    from datetime import datetime, timedelta

    def _create_data(measurement, value, count=30):
        times = [datetime.utcnow() + timedelta(seconds=i) for i in range(count)]
        return pd.DataFrame({
            "_time": times,
            "_value": [value] * count,
            "_measurement": [measurement] * count,
        })

    return _create_data
