"""
InfluxDB Client for reading sensor data windows
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from influxdb_client import InfluxDBClient
from influxdb_client.client.query_api import QueryApi

from .config import settings

logger = logging.getLogger(__name__)


class InfluxClient:
    """Client for querying InfluxDB sensor data"""

    def __init__(self):
        self.client = InfluxDBClient(
            url=settings.influx_url,
            token=settings.influx_token,
            org=settings.influx_org,
        )
        self.query_api: QueryApi = self.client.query_api()

    def get_sensor_window(
        self, tag: str, duration_seconds: int = 30, bucket: str = None
    ) -> pd.DataFrame:
        """
        Retrieve the last N seconds of data for a specific sensor

        Args:
            tag: Sensor tag name (e.g., 'pH', 'DO', 'Temp_Broth')
            duration_seconds: Window duration in seconds (default 30)
            bucket: InfluxDB bucket name (default: pichia_raw)

        Returns:
            DataFrame with columns ['_time', '_value']
        """
        if bucket is None:
            bucket = settings.influx_bucket_raw

        # Build Flux query
        query = f'''
        from(bucket: "{bucket}")
          |> range(start: -{duration_seconds}s)
          |> filter(fn: (r) => r._measurement == "{tag}")
          |> filter(fn: (r) => r._field == "_value" or r._field == "value")
          |> filter(fn: (r) => r.vessel == "{settings.vessel_id}")
          |> keep(columns: ["_time", "_value"])
          |> sort(columns: ["_time"])
        '''

        try:
            result = self.query_api.query_data_frame(query)

            if isinstance(result, list):
                if len(result) == 0:
                    return pd.DataFrame(columns=["_time", "_value"])
                result = pd.concat(result, ignore_index=True)

            if result.empty:
                logger.debug(f"No data found for {tag} in last {duration_seconds}s")
                return pd.DataFrame(columns=["_time", "_value"])

            # Ensure we have the required columns
            if "_time" not in result.columns or "_value" not in result.columns:
                logger.warning(f"Unexpected columns for {tag}: {result.columns.tolist()}")
                return pd.DataFrame(columns=["_time", "_value"])

            return result[["_time", "_value"]]

        except Exception as e:
            logger.error(f"Error querying {tag}: {e}")
            return pd.DataFrame(columns=["_time", "_value"])

    def get_all_sensor_windows(
        self, tags: List[str], duration_seconds: int = 30
    ) -> Dict[str, pd.DataFrame]:
        """
        Retrieve windows for multiple sensors

        Args:
            tags: List of sensor tag names
            duration_seconds: Window duration in seconds

        Returns:
            Dict mapping tag names to DataFrames
        """
        windows = {}

        for tag in tags:
            df = self.get_sensor_window(tag, duration_seconds)
            windows[tag] = df

        return windows

    def write_features(self, features: Dict[str, float], timestamp: Optional[datetime] = None):
        """
        Write engineered features to predictions bucket

        Args:
            features: Dict of feature name -> value
            timestamp: Timestamp for the features (default: now)
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        write_api = self.client.write_api()

        try:
            # Create line protocol entries
            lines = []
            for feature_name, value in features.items():
                if pd.notna(value):  # Skip NaN values
                    line = (
                        f"features,vessel={settings.vessel_id} "
                        f"{feature_name}={value} {int(timestamp.timestamp() * 1e9)}"
                    )
                    lines.append(line)

            if lines:
                write_api.write(
                    bucket=settings.influx_bucket_pred,
                    org=settings.influx_org,
                    record=lines,
                )
                logger.debug(f"Wrote {len(lines)} features to InfluxDB")

        except Exception as e:
            logger.error(f"Error writing features to InfluxDB: {e}")

        finally:
            write_api.close()

    def write_prediction(
        self, prediction: float, confidence_lower: float, confidence_upper: float, timestamp: Optional[datetime] = None
    ):
        """
        Write model prediction to InfluxDB

        Args:
            prediction: Predicted OD value
            confidence_lower: Lower confidence bound
            confidence_upper: Upper confidence bound
            timestamp: Prediction timestamp (default: now)
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        write_api = self.client.write_api()

        try:
            line = (
                f"prediction,vessel={settings.vessel_id} "
                f"od_predicted={prediction},"
                f"confidence_lower={confidence_lower},"
                f"confidence_upper={confidence_upper} "
                f"{int(timestamp.timestamp() * 1e9)}"
            )

            write_api.write(
                bucket=settings.influx_bucket_pred,
                org=settings.influx_org,
                record=line,
            )
            logger.debug(f"Wrote prediction: OD={prediction:.4f}")

        except Exception as e:
            logger.error(f"Error writing prediction to InfluxDB: {e}")

        finally:
            write_api.close()

    def close(self):
        """Close InfluxDB client connection"""
        self.client.close()


# Sensor tag list (based on technical plan Section 4.1)
ALL_SENSOR_TAGS = [
    "pH",
    "DO",
    "OD",
    "Gas_MFC_air",
    "Stir_SP",
    "Stir_torque",
    "Weight",
    "Heater_PID_out",
    "Base_Pump_Rate",
    "broth",  # Temp_Broth (mapped from MQTT topic)
    "ph_probe",  # Temp_pH_Probe
    "do_probe",  # Temp_DO_Probe
    "stirrer_motor",  # Temp_Stirrer_Motor
    "exhaust",  # Temp_Exhaust
    "headspace",  # Reactor_Pressure
    "co2",  # Off_Gas_CO2
    "o2",  # Off_Gas_O2
    "flow_in",  # Gas_Flow_Inlet
    "flow_out",  # Gas_Flow_Outlet
]
