"""
Monitoring and Alerting Module
Provides Prometheus metrics and MQTT alerts for pipeline health
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
import paho.mqtt.client as mqtt

from .config import settings

logger = logging.getLogger(__name__)


# Prometheus Metrics

# Counters
windows_processed_total = Counter(
    "pipeline_windows_processed_total", "Total number of 30s windows processed"
)

features_generated_total = Counter(
    "pipeline_features_generated_total", "Total number of features generated"
)

missing_data_total = Counter(
    "pipeline_missing_data_total", "Total missing data points detected", ["sensor"]
)

outliers_detected_total = Counter(
    "pipeline_outliers_detected_total", "Total outliers detected and clipped", ["sensor"]
)

bounds_violations_total = Counter(
    "pipeline_bounds_violations_total", "Total physical bounds violations", ["sensor"]
)

processing_errors_total = Counter(
    "pipeline_processing_errors_total", "Total processing errors", ["error_type"]
)

# Gauges
pipeline_running = Gauge("pipeline_running", "Pipeline running status (1=running, 0=stopped)")

window_completeness = Gauge(
    "pipeline_window_completeness_percent",
    "Data completeness percentage for last window",
    ["sensor"],
)

feature_values = Gauge(
    "pipeline_feature_value", "Current feature values", ["feature_name"]
)

# Histograms
processing_duration_seconds = Histogram(
    "pipeline_processing_duration_seconds", "Time to process a single window"
)

data_quality_score = Histogram(
    "pipeline_data_quality_score", "Overall data quality score (0-100)", ["sensor"]
)


class MonitoringService:
    """Service for monitoring pipeline health and sending alerts"""

    def __init__(self):
        self.mqtt_client: Optional[mqtt.Client] = None
        self.alerts_enabled = True
        self._setup_mqtt()

    def _setup_mqtt(self):
        """Initialize MQTT client for alerts"""
        try:
            self.mqtt_client = mqtt.Client(client_id="pipeline-monitor")

            # Set up authentication if configured
            if settings.mqtt_username and settings.mqtt_password:
                self.mqtt_client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

            # Connect to broker
            self.mqtt_client.connect(settings.mqtt_broker, settings.mqtt_port, keepalive=60)
            self.mqtt_client.loop_start()

            logger.info(f"MQTT client connected to {settings.mqtt_broker}:{settings.mqtt_port}")

        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            self.alerts_enabled = False

    def update_metrics(self, quality_reports: Dict[str, Dict], features: Dict[str, float]):
        """
        Update Prometheus metrics based on processing results

        Args:
            quality_reports: Data quality reports per sensor
            features: Engineered features
        """
        # Update counters
        windows_processed_total.inc()
        features_generated_total.inc(len(features))

        # Update quality metrics per sensor
        for tag, report in quality_reports.items():
            # Missing data
            missing_count = report.get("missing_count", 0)
            if missing_count > 0:
                missing_data_total.labels(sensor=tag).inc(missing_count)

            # Outliers
            outlier_count = report.get("outliers_detected", 0)
            if outlier_count > 0:
                outliers_detected_total.labels(sensor=tag).inc(outlier_count)

            # Bounds violations
            invalid_count = report.get("invalid_values", 0)
            if invalid_count > 0:
                bounds_violations_total.labels(sensor=tag).inc(invalid_count)

            # Window completeness
            completeness = report.get("completeness_percent", 100.0)
            window_completeness.labels(sensor=tag).set(completeness)

            # Data quality score (100 - penalties for issues)
            quality_score = 100.0
            quality_score -= missing_count * 2  # -2 per missing point
            quality_score -= outlier_count * 1  # -1 per outlier
            quality_score -= invalid_count * 5  # -5 per invalid value
            quality_score = max(0, quality_score)

            data_quality_score.labels(sensor=tag).observe(quality_score)

        # Update feature values
        for feature_name, value in features.items():
            if value is not None and not isinstance(value, str):
                try:
                    feature_values.labels(feature_name=feature_name).set(float(value))
                except (ValueError, TypeError):
                    pass

    def send_alert(
        self, level: str, category: str, message: str, metadata: Optional[Dict] = None
    ):
        """
        Send alert via MQTT

        Args:
            level: Alert level ('info', 'warning', 'error', 'critical')
            category: Alert category (e.g., 'data_quality', 'sensor_failure')
            message: Human-readable alert message
            metadata: Optional additional data
        """
        if not self.alerts_enabled or self.mqtt_client is None:
            logger.debug(f"Alert (MQTT disabled): [{level}] {message}")
            return

        alert_payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "category": category,
            "message": message,
            "vessel": settings.vessel_id,
            "metadata": metadata or {},
        }

        try:
            topic = f"bioprocess/pichia/{settings.vessel_id}/alarms/{category}"
            self.mqtt_client.publish(topic, str(alert_payload), qos=1)
            logger.info(f"Alert sent: [{level}] {message}")

        except Exception as e:
            logger.error(f"Failed to send alert: {e}")

    def check_quality_thresholds(self, quality_reports: Dict[str, Dict]):
        """
        Check quality reports against thresholds and send alerts

        Args:
            quality_reports: Data quality reports per sensor
        """
        for tag, report in quality_reports.items():
            # Check for alarms in report
            if report.get("alarm"):
                self.send_alert(
                    level="error",
                    category="data_quality",
                    message=f"Data quality alarm for {tag}: {report['alarm']}",
                    metadata=report,
                )

            # Check for excessive missing data
            missing_count = report.get("missing_count", 0)
            if missing_count > 15:  # >50% missing
                self.send_alert(
                    level="warning",
                    category="missing_data",
                    message=f"High missing data rate for {tag}: {missing_count}/30 samples",
                    metadata={"tag": tag, "missing_count": missing_count},
                )

            # Check for physical bounds violations
            invalid_count = report.get("invalid_values", 0)
            if invalid_count > 0:
                self.send_alert(
                    level="critical",
                    category="sensor_failure",
                    message=f"Physical bounds violation for {tag}: {invalid_count} invalid values",
                    metadata={"tag": tag, "invalid_count": invalid_count},
                )

    def check_feature_thresholds(self, features: Dict[str, float]):
        """
        Check engineered features for anomalies

        Args:
            features: Engineered features
        """
        # Check growth rate
        mu = features.get("mu")
        if mu is not None:
            if mu < 0:
                self.send_alert(
                    level="warning",
                    category="process_anomaly",
                    message=f"Negative growth rate detected: μ={mu:.4f} h⁻¹",
                    metadata={"mu": mu},
                )
            elif mu > 0.5:  # Unrealistically high for Pichia
                self.send_alert(
                    level="warning",
                    category="process_anomaly",
                    message=f"Unusually high growth rate: μ={mu:.4f} h⁻¹",
                    metadata={"mu": mu},
                )

        # Check RQ (should be ~1 for aerobic glycerol)
        rq = features.get("RQ")
        if rq is not None:
            if rq < 0.5 or rq > 1.5:
                self.send_alert(
                    level="info",
                    category="metabolic_shift",
                    message=f"Respiratory quotient outside normal range: RQ={rq:.3f}",
                    metadata={"RQ": rq},
                )

        # Check motor temperature
        motor_temp = features.get("motor_temp")
        if motor_temp is not None and motor_temp > 70:
            self.send_alert(
                level="warning",
                category="equipment_warning",
                message=f"High stirrer motor temperature: {motor_temp:.1f}°C",
                metadata={"motor_temp": motor_temp},
            )

    def get_metrics(self) -> bytes:
        """Get Prometheus metrics in text format"""
        return generate_latest()

    def close(self):
        """Close MQTT connection"""
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
