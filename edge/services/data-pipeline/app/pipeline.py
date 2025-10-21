"""
Main Data Pipeline Orchestrator
Coordinates data cleaning, feature engineering, and prediction publishing
"""
import logging
import time
from datetime import datetime
from typing import Dict, Optional
import pandas as pd

from .config import settings
from .data_cleaning import DataCleaner
from .feature_engineering import FeatureEngineer
from .influx_client import InfluxClient, ALL_SENSOR_TAGS

logger = logging.getLogger(__name__)


class DataPipeline:
    """Main pipeline orchestrator for real-time data processing"""

    def __init__(self):
        self.influx = InfluxClient()
        self.cleaner = DataCleaner()
        self.engineer = FeatureEngineer()
        self.is_running = False
        self.cycle_count = 0

    def process_window(self) -> Optional[Dict[str, float]]:
        """
        Process a single 30-second window of sensor data

        Returns:
            Dict of engineered features, or None if processing failed
        """
        start_time = time.time()

        try:
            # 1. Fetch 30s windows for all sensors
            logger.debug("Fetching sensor windows from InfluxDB...")
            raw_windows = self.influx.get_all_sensor_windows(
                tags=ALL_SENSOR_TAGS, duration_seconds=settings.window_size_seconds
            )

            # 2. Clean and validate each sensor window
            logger.debug("Cleaning sensor data...")
            cleaned_windows = {}
            quality_reports = {}

            for tag, df in raw_windows.items():
                cleaned_df, report = self.cleaner.clean_window(df, tag)
                cleaned_windows[tag] = cleaned_df
                quality_reports[tag] = report

            # Log any critical quality issues
            self._log_quality_issues(quality_reports)

            # 3. Engineer features from cleaned windows
            logger.debug("Engineering features...")
            features = self.engineer.engineer_features(cleaned_windows)

            # 4. Write features to InfluxDB predictions bucket
            logger.debug("Writing features to InfluxDB...")
            self.influx.write_features(features)

            # Log processing time
            processing_time = time.time() - start_time
            logger.info(
                f"Window {self.cycle_count} processed in {processing_time:.3f}s "
                f"({len(features)} features)"
            )

            self.cycle_count += 1

            return features

        except Exception as e:
            logger.error(f"Error processing window: {e}", exc_info=True)
            return None

    def _log_quality_issues(self, quality_reports: Dict[str, Dict]):
        """Log any critical data quality issues"""
        for tag, report in quality_reports.items():
            # Check for alarms
            if report.get("alarm"):
                alarm_type = report["alarm"]
                logger.warning(f"DATA QUALITY ALARM - {tag}: {alarm_type}")

            # Check for high missing data
            if report.get("missing_count", 0) > 15:  # >50% missing in 30s window
                logger.warning(
                    f"HIGH MISSING DATA - {tag}: {report['missing_count']}/30 samples missing"
                )

            # Check for physical bounds violations
            if report.get("invalid_values", 0) > 0:
                logger.error(
                    f"PHYSICAL BOUNDS VIOLATION - {tag}: {report['invalid_values']} invalid values"
                )

    def run_continuous(self):
        """Run the pipeline continuously with configured interval"""
        self.is_running = True
        logger.info(
            f"Starting continuous pipeline (interval={settings.processing_interval_seconds}s)"
        )

        while self.is_running:
            try:
                # Process current window
                features = self.process_window()

                # Wait for next cycle
                time.sleep(settings.processing_interval_seconds)

            except KeyboardInterrupt:
                logger.info("Pipeline interrupted by user")
                self.stop()
                break
            except Exception as e:
                logger.error(f"Pipeline error: {e}", exc_info=True)
                time.sleep(5)  # Brief pause before retry

    def stop(self):
        """Stop the pipeline gracefully"""
        logger.info("Stopping pipeline...")
        self.is_running = False
        self.influx.close()

        # Log final statistics
        stats = self.cleaner.get_quality_stats()
        logger.info(f"Final quality stats: {stats}")
        logger.info(f"Total windows processed: {self.cycle_count}")

    def reset_batch(self):
        """Reset pipeline state for a new batch"""
        logger.info("Resetting pipeline for new batch")
        self.cleaner.reset_stats()
        self.engineer.reset_history()
        self.cycle_count = 0
