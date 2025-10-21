"""
Configuration management for data pipeline service
"""
import os
from typing import Dict, Any
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Pipeline service configuration"""

    # MQTT Configuration
    mqtt_broker: str = os.getenv("MQTT_BROKER", "mosquitto")
    mqtt_port: int = int(os.getenv("MQTT_PORT", "1883"))
    mqtt_username: str = os.getenv("MQTT_USERNAME", "")
    mqtt_password: str = os.getenv("MQTT_PASSWORD", "")

    # InfluxDB Configuration
    influx_url: str = os.getenv("INFLUX_URL", "http://influxdb:8086")
    influx_token: str = os.getenv("INFLUX_TOKEN", "my-super-secret-auth-token")
    influx_org: str = os.getenv("INFLUX_ORG", "bioprocess")
    influx_bucket_raw: str = os.getenv("INFLUX_BUCKET_RAW", "pichia_raw")
    influx_bucket_30s: str = os.getenv("INFLUX_BUCKET_30S", "pichia_30s")
    influx_bucket_pred: str = os.getenv("INFLUX_BUCKET_PRED", "pichia_pred")

    # Pipeline Configuration
    window_size_seconds: int = int(os.getenv("WINDOW_SIZE_SECONDS", "30"))
    processing_interval_seconds: int = int(os.getenv("PROCESSING_INTERVAL_SECONDS", "30"))
    vessel_id: str = os.getenv("VESSEL_ID", "vessel1")

    # Data Quality Thresholds
    max_missing_duration_interpolate_minutes: int = 5  # Linear interpolation
    max_missing_duration_kalman_minutes: int = 30      # Kalman filter
    outlier_zscore_threshold: float = 3.0              # Z-score for outlier detection

    # Physical Bounds for Validation
    physical_bounds: Dict[str, Dict[str, float]] = {
        "pH": {"min": 2.0, "max": 10.0},
        "DO": {"min": 0.0, "max": 100.0},
        "OD": {"min": 0.0, "max": 100.0},
        "Temp_Broth": {"min": 20.0, "max": 40.0},
        "Temp_pH_Probe": {"min": 20.0, "max": 40.0},
        "Temp_DO_Probe": {"min": 20.0, "max": 40.0},
        "Temp_Stirrer_Motor": {"min": 15.0, "max": 100.0},
        "Temp_Exhaust": {"min": 20.0, "max": 50.0},
        "Gas_MFC_air": {"min": 0.0, "max": 3.0},
        "Stir_SP": {"min": 0.0, "max": 1200.0},
        "Stir_torque": {"min": 0.0, "max": 100.0},
        "Reactor_Pressure": {"min": 0.8, "max": 1.6},
        "Weight": {"min": 0.0, "max": 15.0},
        "Heater_PID_out": {"min": 0.0, "max": 100.0},
        "Base_Pump_Rate": {"min": 0.0, "max": 15.0},
        "Off_Gas_CO2": {"min": 0.0, "max": 10.0},
        "Off_Gas_O2": {"min": 15.0, "max": 25.0},
        "Gas_Flow_Inlet": {"min": 0.0, "max": 3.0},
        "Gas_Flow_Outlet": {"min": 0.0, "max": 3.5},
    }

    # Process Constants
    working_volume_l: float = 0.9
    standard_pressure_bar: float = 1.013
    air_o2_fraction: float = 0.21

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        case_sensitive = False


# Global settings instance
settings = Settings()
