"""
Data Cleaning and Validation Module (Section 5.1)

Implements:
- Missing data handling (linear interpolation, Kalman filter)
- Outlier detection and clipping (Z-score based)
- Physical bounds validation
- Data quality alerting
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
from scipy import interpolate
from pykalman import KalmanFilter

from .config import settings

logger = logging.getLogger(__name__)


class DataCleaner:
    """Real-time data cleaning and validation"""

    def __init__(self):
        self.settings = settings
        self.quality_stats = {
            "missing_count": 0,
            "outlier_count": 0,
            "invalid_count": 0,
            "interpolated_count": 0,
            "kalman_filtered_count": 0,
        }

    def clean_window(
        self, df: pd.DataFrame, tag: str
    ) -> Tuple[pd.DataFrame, Dict[str, any]]:
        """
        Clean a 30-second window of sensor data

        Args:
            df: DataFrame with columns ['_time', '_value']
            tag: Sensor tag name (e.g., 'pH', 'DO', 'Temp_Broth')

        Returns:
            Tuple of (cleaned_df, quality_report)
        """
        if df.empty:
            logger.warning(f"Empty dataframe for tag: {tag}")
            return df, {"status": "empty", "action": "none"}

        # Sort by time
        df = df.sort_values("_time").reset_index(drop=True)

        # Initialize quality report
        quality_report = {
            "tag": tag,
            "original_count": len(df),
            "missing_duration_seconds": 0,
            "outliers_detected": 0,
            "invalid_values": 0,
            "action": "none",
        }

        # 1. Handle missing data
        df, missing_report = self._handle_missing(df, tag)
        quality_report.update(missing_report)

        # 2. Detect and clip outliers
        df, outlier_report = self._handle_outliers(df, tag)
        quality_report.update(outlier_report)

        # 3. Validate physical bounds
        df, bounds_report = self._validate_bounds(df, tag)
        quality_report.update(bounds_report)

        # Update global stats
        self.quality_stats["missing_count"] += quality_report.get("missing_count", 0)
        self.quality_stats["outlier_count"] += quality_report.get("outliers_detected", 0)
        self.quality_stats["invalid_count"] += quality_report.get("invalid_values", 0)

        return df, quality_report

    def _handle_missing(
        self, df: pd.DataFrame, tag: str
    ) -> Tuple[pd.DataFrame, Dict]:
        """Handle missing data with interpolation or Kalman filter"""
        report = {"missing_count": 0, "interpolation_method": "none"}

        # Check for missing values
        missing_mask = df["_value"].isna()
        missing_count = missing_mask.sum()

        if missing_count == 0:
            return df, report

        report["missing_count"] = missing_count

        # Calculate missing duration
        if missing_count > 0:
            time_diff = (df["_time"].max() - df["_time"].min()).total_seconds()
            missing_duration_minutes = (missing_count / len(df)) * (time_diff / 60)

            report["missing_duration_minutes"] = missing_duration_minutes

            # Choose interpolation method based on duration
            if missing_duration_minutes < self.settings.max_missing_duration_interpolate_minutes:
                # Linear interpolation for short gaps
                df["_value"] = df["_value"].interpolate(method="linear", limit_direction="both")
                report["interpolation_method"] = "linear"
                self.quality_stats["interpolated_count"] += missing_count
                logger.debug(
                    f"{tag}: Applied linear interpolation for {missing_count} missing values"
                )

            elif missing_duration_minutes < self.settings.max_missing_duration_kalman_minutes:
                # Kalman filter for longer gaps
                df = self._apply_kalman_filter(df, tag)
                report["interpolation_method"] = "kalman"
                self.quality_stats["kalman_filtered_count"] += missing_count
                logger.warning(
                    f"{tag}: Applied Kalman filter for {missing_count} missing values "
                    f"({missing_duration_minutes:.1f} min gap)"
                )

            else:
                # Gap too large - mark as alarm
                report["interpolation_method"] = "failed"
                report["alarm"] = "missing_data_too_long"
                logger.error(
                    f"{tag}: Missing data duration ({missing_duration_minutes:.1f} min) "
                    f"exceeds threshold ({self.settings.max_missing_duration_kalman_minutes} min)"
                )

        return df, report

    def _apply_kalman_filter(self, df: pd.DataFrame, tag: str) -> pd.DataFrame:
        """Apply Kalman filter for missing data estimation"""
        try:
            # Get valid measurements
            valid_mask = ~df["_value"].isna()
            measurements = df.loc[valid_mask, "_value"].values

            if len(measurements) < 2:
                logger.warning(f"{tag}: Not enough valid data for Kalman filter, using forward fill")
                df["_value"] = df["_value"].fillna(method="ffill").fillna(method="bfill")
                return df

            # Initialize Kalman filter with simple dynamics
            kf = KalmanFilter(
                transition_matrices=[1],
                observation_matrices=[1],
                initial_state_mean=measurements[0],
                initial_state_covariance=1,
                observation_covariance=1,
                transition_covariance=0.1,
            )

            # Smooth the entire series
            state_means, _ = kf.smooth(df["_value"].values)
            df["_value"] = state_means.flatten()

        except Exception as e:
            logger.error(f"{tag}: Kalman filter failed: {e}, using forward fill")
            df["_value"] = df["_value"].fillna(method="ffill").fillna(method="bfill")

        return df

    def _handle_outliers(self, df: pd.DataFrame, tag: str) -> Tuple[pd.DataFrame, Dict]:
        """Detect and clip outliers using Z-score method"""
        report = {"outliers_detected": 0, "outlier_indices": []}

        if len(df) < 3:
            return df, report

        values = df["_value"].values
        mean = np.mean(values)
        std = np.std(values)

        if std == 0:
            return df, report

        # Calculate Z-scores
        z_scores = np.abs((values - mean) / std)
        outlier_mask = z_scores > self.settings.outlier_zscore_threshold

        outlier_count = outlier_mask.sum()
        if outlier_count > 0:
            report["outliers_detected"] = outlier_count
            report["outlier_indices"] = np.where(outlier_mask)[0].tolist()

            # Clip to 3-sigma range
            lower_bound = mean - 3 * std
            upper_bound = mean + 3 * std
            df["_value"] = np.clip(values, lower_bound, upper_bound)

            logger.debug(
                f"{tag}: Clipped {outlier_count} outliers to "
                f"[{lower_bound:.2f}, {upper_bound:.2f}]"
            )

        return df, report

    def _validate_bounds(self, df: pd.DataFrame, tag: str) -> Tuple[pd.DataFrame, Dict]:
        """Validate values against physical bounds"""
        report = {"invalid_values": 0, "alarm": None}

        # Get bounds for this tag
        bounds = self.settings.physical_bounds.get(tag)
        if bounds is None:
            # No bounds defined for this tag
            return df, report

        min_val = bounds["min"]
        max_val = bounds["max"]

        # Check for physically impossible values
        invalid_mask = (df["_value"] < min_val) | (df["_value"] > max_val)
        invalid_count = invalid_mask.sum()

        if invalid_count > 0:
            report["invalid_values"] = invalid_count
            report["alarm"] = "physical_bounds_violation"

            # Replace invalid values with NaN
            df.loc[invalid_mask, "_value"] = np.nan

            logger.error(
                f"{tag}: Found {invalid_count} values outside physical bounds "
                f"[{min_val}, {max_val}]. Values set to NaN."
            )

        return df, report

    def get_quality_stats(self) -> Dict[str, int]:
        """Get cumulative quality statistics"""
        return self.quality_stats.copy()

    def reset_stats(self):
        """Reset quality statistics counters"""
        for key in self.quality_stats:
            self.quality_stats[key] = 0


def validate_window_completeness(df: pd.DataFrame, expected_count: int = 30) -> Dict[str, any]:
    """
    Validate that a 30-second window has expected number of 1 Hz samples

    Args:
        df: DataFrame with time-series data
        expected_count: Expected number of samples (default 30 for 1 Hz over 30s)

    Returns:
        Dict with validation results
    """
    actual_count = len(df)
    completeness = (actual_count / expected_count) * 100

    return {
        "expected_count": expected_count,
        "actual_count": actual_count,
        "completeness_percent": completeness,
        "is_complete": completeness >= 90.0,  # 90% threshold
        "missing_samples": expected_count - actual_count,
    }
