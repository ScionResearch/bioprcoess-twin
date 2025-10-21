"""
Feature Engineering Module (Section 5.2)

Implements:
- Basic features: mean, std, slope for every sensor
- Derived rates: CER, OUR, RQ, μ, qO₂, qCO₂, kLa
- Thermal features: temperature gradients, sensor agreement
- Pressure features: pressure-compensated gas calculations
- Process state: phase detection, cumulative sums
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple
from scipy.signal import savgol_filter
from scipy.stats import linregress

from .config import settings

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Real-time feature engineering from 30-second windows"""

    def __init__(self):
        self.settings = settings
        self.history = {}  # Store historical values for cumulative features

    def engineer_features(self, windows: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """
        Engineer features from 30-second windows of all sensors

        Args:
            windows: Dict mapping sensor tags to DataFrames with '_time' and '_value' columns

        Returns:
            Dict of engineered features
        """
        features = {}

        # 1. Basic statistical features for all sensors
        basic_features = self._compute_basic_features(windows)
        features.update(basic_features)

        # 2. Derived rates (off-gas balance)
        gas_features = self._compute_gas_balance_features(windows)
        features.update(gas_features)

        # 3. Growth rate (μ) from OD
        growth_features = self._compute_growth_rate(windows)
        features.update(growth_features)

        # 4. Specific rates (qO₂, qCO₂)
        specific_rates = self._compute_specific_rates(features, windows)
        features.update(specific_rates)

        # 5. Mass transfer coefficient (kLa)
        kla_features = self._compute_kla(windows, features)
        features.update(kla_features)

        # 6. Thermal features
        thermal_features = self._compute_thermal_features(windows)
        features.update(thermal_features)

        # 7. Pressure features
        pressure_features = self._compute_pressure_features(windows)
        features.update(pressure_features)

        # 8. Process state features
        state_features = self._compute_process_state(features, windows)
        features.update(state_features)

        # 9. Cumulative features
        cumulative_features = self._compute_cumulative_features(features)
        features.update(cumulative_features)

        return features

    def _compute_basic_features(self, windows: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """Compute mean, std, slope for every sensor tag"""
        features = {}

        for tag, df in windows.items():
            if df.empty or len(df) < 2:
                continue

            values = df["_value"].values
            times = df["_time"].values

            # Statistical features
            features[f"{tag}_mean"] = np.mean(values)
            features[f"{tag}_std"] = np.std(values)
            features[f"{tag}_min"] = np.min(values)
            features[f"{tag}_max"] = np.max(values)

            # Temporal features
            if len(values) >= 2:
                # Compute slope using linear regression
                time_seconds = np.arange(len(values))
                slope, _, _, _, _ = linregress(time_seconds, values)
                features[f"{tag}_slope"] = slope

        return features

    def _compute_gas_balance_features(
        self, windows: Dict[str, pd.DataFrame]
    ) -> Dict[str, float]:
        """
        Compute CER, OUR, and RQ from off-gas measurements with pressure correction

        Based on technical plan Section 5.2:
        - CER = (F_in × y_CO2_out × P_reactor / P_std) / V_reactor
        - OUR = (F_in × y_O2_in - F_out × y_O2_out) × (P_reactor / P_std) / V_reactor
        - RQ = CER / OUR
        """
        features = {}

        try:
            # Extract mean values from windows
            F_in = windows.get("Gas_Flow_Inlet", pd.DataFrame()).get("_value", pd.Series()).mean()
            F_out = windows.get("Gas_Flow_Outlet", pd.DataFrame()).get("_value", pd.Series()).mean()
            y_CO2_out = (
                windows.get("Off_Gas_CO2", pd.DataFrame()).get("_value", pd.Series()).mean() / 100.0
            )  # % to fraction
            y_O2_out = (
                windows.get("Off_Gas_O2", pd.DataFrame()).get("_value", pd.Series()).mean() / 100.0
            )  # % to fraction
            P_reactor = (
                windows.get("Reactor_Pressure", pd.DataFrame()).get("_value", pd.Series()).mean()
            )

            # Check if we have all required measurements
            if any(pd.isna([F_in, y_CO2_out, y_O2_out, P_reactor])):
                logger.debug("Missing gas balance measurements, skipping CER/OUR calculation")
                return features

            # Constants
            P_std = self.settings.standard_pressure_bar
            V_reactor = self.settings.working_volume_l
            y_O2_in = self.settings.air_o2_fraction

            # If no outlet flow meter, assume outlet = inlet (simple assumption)
            if pd.isna(F_out):
                F_out = F_in

            # Convert L/min to L/h for hourly rates
            F_in_h = F_in * 60
            F_out_h = F_out * 60

            # Pressure correction factor
            pressure_correction = P_reactor / P_std

            # Carbon Evolution Rate (CER) - mol CO₂/L/h
            # Note: Simplified calculation, full stoichiometry would convert L to mol using ideal gas law
            # For now, using volumetric approximation (mol = L × pressure_correction / 22.4 at STP)
            CER = (F_in_h * y_CO2_out * pressure_correction) / V_reactor / 22.4
            features["CER"] = CER
            features["CER_volumetric"] = (F_in_h * y_CO2_out * pressure_correction) / V_reactor

            # Oxygen Uptake Rate (OUR) - mol O₂/L/h
            O2_consumed_h = (F_in_h * y_O2_in - F_out_h * y_O2_out) * pressure_correction
            OUR = O2_consumed_h / V_reactor / 22.4
            features["OUR"] = OUR
            features["OUR_volumetric"] = O2_consumed_h / V_reactor

            # Respiratory Quotient (RQ)
            if OUR > 0:
                features["RQ"] = CER / OUR
            else:
                features["RQ"] = np.nan

            logger.debug(
                f"Gas balance: CER={CER:.4f} mol/L/h, OUR={OUR:.4f} mol/L/h, RQ={features.get('RQ', np.nan):.3f}"
            )

        except Exception as e:
            logger.error(f"Error computing gas balance features: {e}")

        return features

    def _compute_growth_rate(self, windows: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """
        Compute specific growth rate μ (h⁻¹) from OD using Savitzky-Golay derivative

        μ = d(ln OD)/dt
        """
        features = {}

        try:
            od_df = windows.get("OD")
            if od_df is None or od_df.empty or len(od_df) < 5:
                return features

            od_values = od_df["_value"].values
            time_seconds = np.arange(len(od_values))

            # Avoid log of zero/negative
            od_values = np.maximum(od_values, 0.01)

            # Natural log of OD
            ln_od = np.log(od_values)

            # Savitzky-Golay filter for smooth derivative (5-point, 2nd order polynomial)
            if len(ln_od) >= 5:
                window_length = min(5, len(ln_od) if len(ln_od) % 2 == 1 else len(ln_od) - 1)
                deriv = savgol_filter(ln_od, window_length, polyorder=2, deriv=1, delta=1.0)

                # Convert from per-second to per-hour
                mu = deriv[-1] * 3600  # Use most recent derivative
                features["mu"] = mu
                features["mu_mean"] = np.mean(deriv) * 3600
                features["mu_std"] = np.std(deriv) * 3600

                logger.debug(f"Growth rate: μ={mu:.4f} h⁻¹")

        except Exception as e:
            logger.error(f"Error computing growth rate: {e}")

        return features

    def _compute_specific_rates(
        self, features: Dict[str, float], windows: Dict[str, pd.DataFrame]
    ) -> Dict[str, float]:
        """
        Compute specific rates: qO₂, qCO₂ (mol/gDCW/h)

        Requires DCW estimate (can be derived from OD or predicted)
        For now, using empirical OD-to-DCW conversion: DCW ≈ 0.4 × OD
        """
        specific_features = {}

        try:
            # Get OUR and CER
            OUR = features.get("OUR")
            CER = features.get("CER")

            # Get OD for DCW estimation
            od_mean = features.get("OD_mean")

            if OUR is not None and od_mean is not None:
                # Empirical conversion: DCW (g/L) ≈ 0.4 × OD₆₀₀
                # This should be calibrated from actual DCW measurements
                DCW_estimated = 0.4 * od_mean

                if DCW_estimated > 0.01:
                    specific_features["qO2"] = OUR / DCW_estimated  # mol O₂/gDCW/h
                    if CER is not None:
                        specific_features["qCO2"] = CER / DCW_estimated  # mol CO₂/gDCW/h

                    logger.debug(
                        f"Specific rates: qO₂={specific_features.get('qO2', np.nan):.4f}, "
                        f"qCO₂={specific_features.get('qCO2', np.nan):.4f} mol/gDCW/h"
                    )

        except Exception as e:
            logger.error(f"Error computing specific rates: {e}")

        return specific_features

    def _compute_kla(
        self, windows: Dict[str, pd.DataFrame], features: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Estimate volumetric mass transfer coefficient kLa (h⁻¹)

        kLa = OUR / (C*_O2 - C_O2)

        Where:
        - C*_O2 = saturation oxygen concentration (pressure-corrected)
        - C_O2 = measured dissolved oxygen
        """
        kla_features = {}

        try:
            OUR = features.get("OUR")
            DO_percent = features.get("DO_mean")
            P_reactor = features.get("Reactor_Pressure_mean", self.settings.standard_pressure_bar)

            if OUR is not None and DO_percent is not None:
                # Saturation concentration at standard conditions (assume 8 mg/L at 1 bar, 30°C)
                # Pressure correction: C* ∝ P
                C_star = 8.0 * (P_reactor / self.settings.standard_pressure_bar)  # mg O₂/L

                # Current DO concentration
                C_O2 = (DO_percent / 100.0) * C_star  # mg O₂/L

                # Driving force
                delta_C = C_star - C_O2

                if delta_C > 0.1:  # Avoid division by near-zero
                    # Convert OUR from mol/L/h to mg/L/h (MW O₂ = 32 g/mol = 32000 mg/mol)
                    OUR_mg = OUR * 32000

                    kla = OUR_mg / delta_C  # h⁻¹
                    kla_features["kLa"] = kla

                    logger.debug(f"Mass transfer: kLa={kla:.2f} h⁻¹")

        except Exception as e:
            logger.error(f"Error computing kLa: {e}")

        return kla_features

    def _compute_thermal_features(self, windows: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """
        Compute thermal features:
        - Temperature gradients (metabolic heat)
        - Sensor agreement (quality check)
        - Motor thermal state
        """
        thermal = {}

        try:
            T_broth = features.get("Temp_Broth_mean")
            T_exhaust = features.get("Temp_Exhaust_mean")
            T_ph = features.get("Temp_pH_Probe_mean")
            T_do = features.get("Temp_DO_Probe_mean")
            T_motor = features.get("Temp_Stirrer_Motor_mean")

            # Temperature gradient (indicates metabolic heat generation)
            if T_broth is not None and T_exhaust is not None:
                thermal["temp_gradient_broth_exhaust"] = T_broth - T_exhaust

            # Sensor agreement (should be within 1°C for immersed sensors)
            if T_broth is not None and T_ph is not None:
                thermal["temp_deviation_ph_probe"] = abs(T_broth - T_ph)

            if T_broth is not None and T_do is not None:
                thermal["temp_deviation_do_probe"] = abs(T_broth - T_do)

            # Motor thermal state
            if T_motor is not None:
                thermal["motor_temp"] = T_motor
                if T_motor > 60:  # Warning threshold
                    thermal["motor_temp_warning"] = 1.0
                else:
                    thermal["motor_temp_warning"] = 0.0

        except Exception as e:
            logger.error(f"Error computing thermal features: {e}")

        return thermal

    def _compute_pressure_features(self, windows: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """
        Compute pressure-related features:
        - Pressure deviation from atmospheric (foam, blockage indicator)
        """
        pressure = {}

        try:
            P_reactor = features.get("Reactor_Pressure_mean")
            P_atm = self.settings.standard_pressure_bar

            if P_reactor is not None:
                pressure["pressure_deviation"] = P_reactor - P_atm

                # Pressure anomaly detection
                if abs(pressure["pressure_deviation"]) > 0.1:  # ±0.1 bar threshold
                    pressure["pressure_anomaly"] = 1.0
                else:
                    pressure["pressure_anomaly"] = 0.0

        except Exception as e:
            logger.error(f"Error computing pressure features: {e}")

        return pressure

    def _compute_process_state(
        self, features: Dict[str, float], windows: Dict[str, pd.DataFrame]
    ) -> Dict[str, float]:
        """
        Detect process phase based on growth rate:
        - lag: μ < 0.08 h⁻¹
        - exp: μ ≥ 0.08 h⁻¹
        - stationary: μ < 0.02 h⁻¹ after exp phase
        """
        state = {}

        try:
            mu = features.get("mu")

            if mu is not None:
                # Simple phase detection (could be enhanced with state machine)
                if mu < 0.02:
                    state["phase_lag"] = 1.0
                    state["phase_exp"] = 0.0
                    state["phase_stationary"] = 0.0
                elif mu >= 0.08:
                    state["phase_lag"] = 0.0
                    state["phase_exp"] = 1.0
                    state["phase_stationary"] = 0.0
                else:  # 0.02 <= μ < 0.08
                    state["phase_lag"] = 0.0
                    state["phase_exp"] = 0.0
                    state["phase_stationary"] = 1.0

        except Exception as e:
            logger.error(f"Error computing process state: {e}")

        return state

    def _compute_cumulative_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """
        Compute cumulative sums over batch duration:
        - Total CO₂ produced
        - Total O₂ consumed
        - Integrated OD
        """
        cumulative = {}

        try:
            # Time step (30 seconds = 1/120 hour)
            dt = self.settings.window_size_seconds / 3600.0

            # Get current values
            CER = features.get("CER", 0)
            OUR = features.get("OUR", 0)
            OD = features.get("OD_mean", 0)

            # Update cumulative sums
            if "cumulative_CO2" not in self.history:
                self.history["cumulative_CO2"] = 0
                self.history["cumulative_O2"] = 0
                self.history["cumulative_OD"] = 0

            self.history["cumulative_CO2"] += CER * dt
            self.history["cumulative_O2"] += OUR * dt
            self.history["cumulative_OD"] += OD * dt

            cumulative["cumulative_CO2"] = self.history["cumulative_CO2"]
            cumulative["cumulative_O2"] = self.history["cumulative_O2"]
            cumulative["cumulative_OD"] = self.history["cumulative_OD"]

        except Exception as e:
            logger.error(f"Error computing cumulative features: {e}")

        return cumulative

    def reset_history(self):
        """Reset cumulative feature history (call at batch start)"""
        self.history = {}
        logger.info("Feature engineering history reset")


# Fix: Add missing 'features' variable in thermal and pressure functions
def _compute_thermal_features(self, windows: Dict[str, pd.DataFrame]) -> Dict[str, float]:
    """Compute thermal features with correct variable reference"""
    thermal = {}

    try:
        # Extract mean temperatures from windows
        T_broth = windows.get("Temp_Broth", pd.DataFrame()).get("_value", pd.Series()).mean()
        T_exhaust = windows.get("Temp_Exhaust", pd.DataFrame()).get("_value", pd.Series()).mean()
        T_ph = windows.get("Temp_pH_Probe", pd.DataFrame()).get("_value", pd.Series()).mean()
        T_do = windows.get("Temp_DO_Probe", pd.DataFrame()).get("_value", pd.Series()).mean()
        T_motor = (
            windows.get("Temp_Stirrer_Motor", pd.DataFrame()).get("_value", pd.Series()).mean()
        )

        # Temperature gradient
        if not pd.isna(T_broth) and not pd.isna(T_exhaust):
            thermal["temp_gradient_broth_exhaust"] = T_broth - T_exhaust

        # Sensor agreement
        if not pd.isna(T_broth) and not pd.isna(T_ph):
            thermal["temp_deviation_ph_probe"] = abs(T_broth - T_ph)

        if not pd.isna(T_broth) and not pd.isna(T_do):
            thermal["temp_deviation_do_probe"] = abs(T_broth - T_do)

        # Motor thermal state
        if not pd.isna(T_motor):
            thermal["motor_temp"] = T_motor
            thermal["motor_temp_warning"] = 1.0 if T_motor > 60 else 0.0

    except Exception as e:
        logger.error(f"Error computing thermal features: {e}")

    return thermal


def _compute_pressure_features(self, windows: Dict[str, pd.DataFrame]) -> Dict[str, float]:
    """Compute pressure features with correct variable reference"""
    pressure = {}

    try:
        P_reactor = (
            windows.get("Reactor_Pressure", pd.DataFrame()).get("_value", pd.Series()).mean()
        )
        P_atm = self.settings.standard_pressure_bar

        if not pd.isna(P_reactor):
            pressure["pressure_deviation"] = P_reactor - P_atm
            pressure["pressure_anomaly"] = 1.0 if abs(pressure["pressure_deviation"]) > 0.1 else 0.0

    except Exception as e:
        logger.error(f"Error computing pressure features: {e}")

    return pressure


# Patch the methods
FeatureEngineer._compute_thermal_features = _compute_thermal_features
FeatureEngineer._compute_pressure_features = _compute_pressure_features
