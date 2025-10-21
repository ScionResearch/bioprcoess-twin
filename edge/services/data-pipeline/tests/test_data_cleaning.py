"""
Unit tests for data cleaning module
"""
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from app.data_cleaning import DataCleaner, validate_window_completeness


@pytest.fixture
def cleaner():
    """Create a DataCleaner instance"""
    return DataCleaner()


@pytest.fixture
def sample_data():
    """Generate sample sensor data"""
    times = [datetime.utcnow() + timedelta(seconds=i) for i in range(30)]
    values = np.random.normal(7.0, 0.1, 30)  # pH data around 7.0
    return pd.DataFrame({"_time": times, "_value": values})


def test_clean_empty_dataframe(cleaner):
    """Test cleaning an empty dataframe"""
    df = pd.DataFrame(columns=["_time", "_value"])
    cleaned, report = cleaner.clean_window(df, "pH")

    assert cleaned.empty
    assert report["status"] == "empty"


def test_clean_valid_data(cleaner, sample_data):
    """Test cleaning valid data with no issues"""
    cleaned, report = cleaner.clean_window(sample_data, "pH")

    assert not cleaned.empty
    assert len(cleaned) == len(sample_data)
    assert report["missing_count"] == 0
    assert report["outliers_detected"] == 0


def test_missing_data_interpolation(cleaner):
    """Test linear interpolation for short missing gaps"""
    times = [datetime.utcnow() + timedelta(seconds=i) for i in range(30)]
    values = [7.0] * 10 + [np.nan] * 3 + [7.0] * 17  # 3 missing values

    df = pd.DataFrame({"_time": times, "_value": values})
    cleaned, report = cleaner.clean_window(df, "pH")

    assert report["missing_count"] == 3
    assert report["interpolation_method"] == "linear"
    assert cleaned["_value"].notna().all()  # All values should be filled


def test_outlier_detection(cleaner):
    """Test outlier detection and clipping"""
    times = [datetime.utcnow() + timedelta(seconds=i) for i in range(30)]
    values = [7.0] * 25 + [15.0, 16.0, 17.0, 18.0, 19.0]  # Last 5 are outliers

    df = pd.DataFrame({"_time": times, "_value": values})
    cleaned, report = cleaner.clean_window(df, "pH")

    assert report["outliers_detected"] > 0
    # Outliers should be clipped to 3-sigma range
    assert cleaned["_value"].max() < 15.0


def test_physical_bounds_validation(cleaner):
    """Test validation against physical bounds"""
    times = [datetime.utcnow() + timedelta(seconds=i) for i in range(30)]
    values = [7.0] * 25 + [1.0, 0.5, -1.0, 11.0, 12.0]  # Invalid pH values

    df = pd.DataFrame({"_time": times, "_value": values})
    cleaned, report = cleaner.clean_window(df, "pH")

    assert report["invalid_values"] > 0
    assert report["alarm"] == "physical_bounds_violation"
    # Invalid values should be set to NaN
    assert cleaned["_value"].isna().sum() == report["invalid_values"]


def test_window_completeness_full():
    """Test completeness validation with full window"""
    times = [datetime.utcnow() + timedelta(seconds=i) for i in range(30)]
    values = [7.0] * 30

    df = pd.DataFrame({"_time": times, "_value": values})
    result = validate_window_completeness(df, expected_count=30)

    assert result["completeness_percent"] == 100.0
    assert result["is_complete"] is True
    assert result["missing_samples"] == 0


def test_window_completeness_partial():
    """Test completeness validation with partial window"""
    times = [datetime.utcnow() + timedelta(seconds=i) for i in range(20)]
    values = [7.0] * 20

    df = pd.DataFrame({"_time": times, "_value": values})
    result = validate_window_completeness(df, expected_count=30)

    assert result["completeness_percent"] == pytest.approx(66.67, rel=0.1)
    assert result["is_complete"] is False
    assert result["missing_samples"] == 10


def test_quality_stats_accumulation(cleaner, sample_data):
    """Test that quality statistics accumulate correctly"""
    # Process multiple windows
    for _ in range(5):
        cleaner.clean_window(sample_data, "pH")

    stats = cleaner.get_quality_stats()
    assert "missing_count" in stats
    assert "outlier_count" in stats

    # Reset and verify
    cleaner.reset_stats()
    stats_after_reset = cleaner.get_quality_stats()
    assert stats_after_reset["missing_count"] == 0


def test_different_sensor_types(cleaner):
    """Test cleaning different sensor types with appropriate bounds"""
    sensors = [
        ("pH", 7.0, 0.1),
        ("DO", 50.0, 5.0),
        ("OD", 2.5, 0.2),
        ("Temp_Broth", 30.0, 0.5),
    ]

    for tag, mean, std in sensors:
        times = [datetime.utcnow() + timedelta(seconds=i) for i in range(30)]
        values = np.random.normal(mean, std, 30)
        df = pd.DataFrame({"_time": times, "_value": values})

        cleaned, report = cleaner.clean_window(df, tag)

        assert not cleaned.empty
        assert report["tag"] == tag
