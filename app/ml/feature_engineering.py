"""Feature Engineering and Preprocessing Pipeline for Semiconductor ML Engine.

Computes rolling process dynamics, sensor instability spikes, maintenance wear factors,
and executes time-aware dataset splitting without temporal data leakage.
"""

import logging
import os
from typing import Tuple, List, Dict, Any
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from app.config import settings

logger = logging.getLogger("semiconductor.features")


class FeaturePipeline:
    """Computes engineered features and manages feature preprocessing transformations."""

    CORE_FEATURE_COLS: List[str] = [
        "Temperature", "Vibration", "Pressure", "Power_Consumption",
        "Cycle_Time_Sec", "Wafer_Count", "Operating_Hours", "Machine_Efficiency_Pct",
        "Chemical_Flow_Rate", "Particle_Count", "Temperature_Uniformity", "Gas_Flow",
        "Days_Since_Maintenance", "Maintenance_Wear_Index", "Historical_Failure_Count",
        "Avg_Material_Quality_Pct", "Min_Days_of_Stock"
    ]

    def __init__(self, preprocessing_dir: str = "models/preprocessing"):
        self.preprocessing_dir = preprocessing_dir
        os.makedirs(self.preprocessing_dir, exist_ok=True)
        self.scaler_path = os.path.join(self.preprocessing_dir, "scaler.joblib")
        self.feature_meta_path = os.path.join(self.preprocessing_dir, "feature_names.joblib")
        self.scaler = None
        self.engineered_feature_cols: List[str] = []

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate temporal rolling statistics and sensor instability indicators."""
        data = df.copy()
        if "Timestamp" in data.columns:
            data = data.sort_values(by=["Machine_ID", "Timestamp"]).reset_index(drop=True)

        # 1. Rolling Window Statistics per Machine (6-hour window)
        for col in ["Temperature", "Vibration", "Pressure", "Power_Consumption"]:
            if col in data.columns:
                grouped = data.groupby("Machine_ID")[col]
                data[f"{col}_RollMean_6h"] = grouped.transform(lambda s: s.rolling(window=6, min_periods=1).mean())
                data[f"{col}_RollStd_6h"] = grouped.transform(lambda s: s.rolling(window=6, min_periods=1).std().fillna(0.01))
                
                # Z-score spike relative to recent moving baseline
                data[f"{col}_Spike_Z"] = (data[col] - data[f"{col}_RollMean_6h"]) / (data[f"{col}_RollStd_6h"] + 1e-4)

        # 2. Composite Interaction Terms
        data["Thermal_Instability_Index"] = np.clip(
            (data.get("Temperature_Spike_Z", 0) ** 2 + data.get("Vibration_Spike_Z", 0) ** 2) ** 0.5,
            0.0, 10.0
        )
        data["Power_Per_Wafer"] = data["Power_Consumption"] / (data["Wafer_Count"] + 1.0)
        data["Cycle_Efficiency_Ratio"] = (data["Machine_Efficiency_Pct"] / 100.0) / (data["Cycle_Time_Sec"] + 1e-3)
        
        # 3. Process Drift Deviation (Deviation from global median)
        temp_median = data["Temperature"].median()
        vib_median = data["Vibration"].median()
        data["Temp_Process_Drift"] = np.abs(data["Temperature"] - temp_median)
        data["Vib_Process_Drift"] = np.abs(data["Vibration"] - vib_median)

        return data

    def extract_feature_matrix(self, data: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        """Extract feature matrix from engineered dataframe."""
        candidate_cols = self.CORE_FEATURE_COLS + [
            "Temperature_RollMean_6h", "Temperature_RollStd_6h", "Temperature_Spike_Z",
            "Vibration_RollMean_6h", "Vibration_RollStd_6h", "Vibration_Spike_Z",
            "Pressure_RollMean_6h", "Pressure_RollStd_6h", "Pressure_Spike_Z",
            "Power_Consumption_RollMean_6h", "Power_Consumption_RollStd_6h", "Power_Consumption_Spike_Z",
            "Thermal_Instability_Index", "Power_Per_Wafer", "Cycle_Efficiency_Ratio",
            "Temp_Process_Drift", "Vib_Process_Drift"
        ]
        
        active_cols = [c for c in candidate_cols if c in data.columns]
        self.engineered_feature_cols = active_cols
        X = data[active_cols].fillna(0.0).values
        return X, active_cols

    def time_aware_split(
        self, data: pd.DataFrame, train_ratio: float = 0.75
    ) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Split data chronologically to prevent temporal data leakage."""
        engineered_df = self.engineer_features(data)
        
        # Chronological cutoff
        unique_timestamps = sorted(engineered_df["Timestamp"].unique())
        split_idx = int(len(unique_timestamps) * train_ratio)
        cutoff_time = unique_timestamps[split_idx]

        train_df = engineered_df[engineered_df["Timestamp"] < cutoff_time].copy()
        test_df = engineered_df[engineered_df["Timestamp"] >= cutoff_time].copy()

        logger.info(
            f"Time-aware split at {cutoff_time}: Train={len(train_df)} rows ({train_ratio*100:.0f}%), "
            f"Test={len(test_df)} rows ({(1-train_ratio)*100:.0f}%)"
        )

        X_train_raw, self.engineered_feature_cols = self.extract_feature_matrix(train_df)
        X_test_raw, _ = self.extract_feature_matrix(test_df)

        y_train = train_df["Breakdown_Risk_Label"].values
        y_test = test_df["Breakdown_Risk_Label"].values

        # Fit Scaler strictly on training set
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train_raw)
        X_test_scaled = self.scaler.transform(X_test_raw)

        # Persist Preprocessing Pipeline
        joblib.dump(self.scaler, self.scaler_path)
        joblib.dump(self.engineered_feature_cols, self.feature_meta_path)
        logger.info(f"Saved scaler and feature list ({len(self.engineered_feature_cols)} features) to {self.preprocessing_dir}")

        return train_df, test_df, X_train_scaled, X_test_scaled, y_train, y_test

    def transform_single(self, row_dict: Dict[str, Any]) -> np.ndarray:
        """Transform a single runtime row dictionary for live prediction."""
        if self.scaler is None and os.path.exists(self.scaler_path):
            self.scaler = joblib.load(self.scaler_path)
            self.engineered_feature_cols = joblib.load(self.feature_meta_path)

        df_single = pd.DataFrame([row_dict])
        df_single = self.engineer_features(df_single)
        X_raw, _ = self.extract_feature_matrix(df_single)
        return self.scaler.transform(X_raw)
