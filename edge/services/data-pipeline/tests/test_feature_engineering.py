"""
Unit tests for feature engineering module
"""
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from app.feature_engineering import FeatureEngineer


@pytest.fixture
def engineer():
    """Create a FeatureEngineer instance"""
    return FeatureEngineer()


@pytest.fixture
def mock_windows():
    """Create mock sensor windows for testing"""
    times = [datetime.utcnow() + timedelta(seconds=i) for i in range(30)]

    windows = {
        "pH": pd.DataFrame({"_time": times, "_value": np.random.normal(7.0, 0.05, 30)}),
        "DO": pd.DataFrame({"_time": times, "_value": np.random.normal(60.0, 2.0, 30)}),
        "OD": pd.DataFrame({"_time": times, "_value": np.linspace(2.0, 2.1, 30)}),
        "broth": pd.DataFrame({"_time": times, "_value": np.random.normal(30.0, 0.1, 30)}),
        "exhaust": pd.DataFrame({"_time": times, "_value": np.random.normal(28.0, 0.1, 30)}),
        "ph_probe": pd.DataFrame({"_time": times, "_value": np.random.normal(30.0, 0.1, 30)}),
        "do_probe": pd.DataFrame({"_time": times, "_value": np.random.normal(30.0, 0.1, 30)}),
        "stirrer_motor": pd.DataFrame({"_time": times, "_value": np.random.normal(45.0, 1.0, 30)}),
        "headspace": pd.DataFrame({"_time": times, "_value": np.random.normal(1.02, 0.01, 30)}),
        "co2": pd.DataFrame({"_time": times, "_value": np.random.normal(2.0, 0.1, 30)}),
        "o2": pd.DataFrame({"_time": times, "_value": np.random.normal(20.0, 0.2, 30)}),
        "flow_in": pd.DataFrame({"_time": times, "_value": np.random.normal(1.0, 0.05, 30)}),
        "flow_out": pd.DataFrame({"_time": times, "_value": np.random.normal(1.0, 0.05, 30)}),
        "Stir_SP": pd.DataFrame({"_time": times, "_value": np.random.normal(600.0, 10.0, 30)}),
        "Gas_MFC_air": pd.DataFrame({"_time": times, "_value": np.random.normal(1.0, 0.05, 30)}),
    }

    return windows


def test_basic_features_computation(engineer, mock_windows):
    """Test computation of basic statistical features"""
    features = engineer._compute_basic_features(mock_windows)

    # Check that mean, std, min, max, slope are computed for each sensor
    assert "pH_mean" in features
    assert "pH_std" in features
    assert "pH_min" in features
    assert "pH_max" in features
    assert "pH_slope" in features

    # Verify values are reasonable
    assert 6.5 < features["pH_mean"] < 7.5
    assert features["pH_std"] >= 0


def test_gas_balance_features(engineer, mock_windows):
    """Test CER, OUR, and RQ calculations"""
    features = engineer._compute_gas_balance_features(mock_windows)

    # Check that gas balance features are computed
    assert "CER" in features
    assert "OUR" in features
    assert "RQ" in features

    # Verify RQ is reasonable (should be ~1 for aerobic glycerol)
    if features["RQ"] is not None and not np.isnan(features["RQ"]):
        assert 0.5 < features["RQ"] < 1.5


def test_growth_rate_calculation(engineer, mock_windows):
    """Test specific growth rate (μ) calculation"""
    features = engineer._compute_growth_rate(mock_windows)

    assert "mu" in features
    # Growth rate should be positive for increasing OD
    if features["mu"] is not None:
        assert features["mu"] > 0


def test_specific_rates_calculation(engineer, mock_windows):
    """Test qO₂ and qCO₂ calculations"""
    # First compute basic features to get OD_mean
    basic_features = engineer._compute_basic_features(mock_windows)
    gas_features = engineer._compute_gas_balance_features(mock_windows)
    features = {**basic_features, **gas_features}

    specific_rates = engineer._compute_specific_rates(features, mock_windows)

    # Check for specific rate features
    if "qO2" in specific_rates:
        assert specific_rates["qO2"] > 0


def test_kla_estimation(engineer, mock_windows):
    """Test kLa (mass transfer coefficient) estimation"""
    basic_features = engineer._compute_basic_features(mock_windows)
    gas_features = engineer._compute_gas_balance_features(mock_windows)
    features = {**basic_features, **gas_features}

    kla_features = engineer._compute_kla(mock_windows, features)

    if "kLa" in kla_features:
        # kLa should be positive
        assert kla_features["kLa"] > 0


def test_thermal_features(engineer, mock_windows):
    """Test thermal feature calculations"""
    thermal_features = engineer._compute_thermal_features(mock_windows)

    # Check for temperature gradient
    assert "temp_gradient_broth_exhaust" in thermal_features
    assert "temp_deviation_ph_probe" in thermal_features
    assert "temp_deviation_do_probe" in thermal_features
    assert "motor_temp" in thermal_features

    # Temperature gradient should be positive (broth warmer than exhaust)
    if thermal_features["temp_gradient_broth_exhaust"] is not None:
        assert thermal_features["temp_gradient_broth_exhaust"] >= 0


def test_pressure_features(engineer, mock_windows):
    """Test pressure-related features"""
    pressure_features = engineer._compute_pressure_features(mock_windows)

    assert "pressure_deviation" in pressure_features
    assert "pressure_anomaly" in pressure_features

    # Pressure deviation should be small for normal operation
    if pressure_features["pressure_deviation"] is not None:
        assert abs(pressure_features["pressure_deviation"]) < 0.2


def test_process_state_detection(engineer, mock_windows):
    """Test process phase detection"""
    # Create mock features with known growth rate
    features = {"mu": 0.15}  # Exponential phase

    state_features = engineer._compute_process_state(features, mock_windows)

    assert "phase_lag" in state_features
    assert "phase_exp" in state_features
    assert "phase_stationary" in state_features

    # Should be in exponential phase
    assert state_features["phase_exp"] == 1.0
    assert state_features["phase_lag"] == 0.0


def test_cumulative_features(engineer):
    """Test cumulative feature tracking"""
    # Simulate multiple windows
    for i in range(5):
        features = {"CER": 0.1, "OUR": 0.1, "OD_mean": 2.0}
        cumulative = engineer._compute_cumulative_features(features)

    # Cumulative values should increase
    assert cumulative["cumulative_CO2"] > 0
    assert cumulative["cumulative_O2"] > 0
    assert cumulative["cumulative_OD"] > 0

    # Reset and verify
    engineer.reset_history()
    features = {"CER": 0.1, "OUR": 0.1, "OD_mean": 2.0}
    cumulative = engineer._compute_cumulative_features(features)

    # Should be close to zero after reset
    assert cumulative["cumulative_CO2"] < 0.01


def test_full_feature_engineering_pipeline(engineer, mock_windows):
    """Test the complete feature engineering pipeline"""
    features = engineer.engineer_features(mock_windows)

    # Verify we have a comprehensive feature set
    assert len(features) > 50  # Should have many features

    # Check for key feature categories
    feature_keys = features.keys()

    # Basic features
    assert any("_mean" in k for k in feature_keys)
    assert any("_std" in k for k in feature_keys)

    # Derived rates (may not all be present depending on data)
    # Just check that the function runs without errors


def test_empty_windows_handling(engineer):
    """Test handling of empty sensor windows"""
    empty_windows = {
        "pH": pd.DataFrame(columns=["_time", "_value"]),
        "DO": pd.DataFrame(columns=["_time", "_value"]),
    }

    features = engineer.engineer_features(empty_windows)

    # Should return empty or minimal features without crashing
    assert isinstance(features, dict)


def test_missing_sensor_handling(engineer, mock_windows):
    """Test handling when some sensors are missing"""
    # Remove some sensors
    partial_windows = {k: v for k, v in mock_windows.items() if k in ["pH", "DO", "OD"]}

    features = engineer.engineer_features(partial_windows)

    # Should still produce features for available sensors
    assert "pH_mean" in features
    assert "DO_mean" in features
    assert "OD_mean" in features
